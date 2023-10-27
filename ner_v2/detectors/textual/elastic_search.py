from __future__ import absolute_import

import json

import six
from elasticsearch import Elasticsearch
from elasticsearch import exceptions as es_exceptions

from chatbot_ner.config import ner_logger, CHATBOT_NER_DATASTORE
from datastore import constants
from datastore.exceptions import (EngineConnectionException, DataStoreSettingsImproperlyConfiguredException,
                                  DataStoreRequestException)
from language_utilities.constant import ENGLISH_LANG
from lib.singleton import Singleton
from ner_v2.detectors.textual.queries import _generate_multi_entity_es_query, _parse_multi_entity_es_results


# NOTE: connection is a misleading term for this implementation, rather what we have are clients that manage
# any real connections on their own
class ElasticSearchDataStore(six.with_metaclass(Singleton, object)):
    """
    Instance responsible for holding connections and performing search in ElasticSearch DB.
    Used as a singleton in this module.
    """

    def __init__(self):
        self._engine_name = constants.ELASTICSEARCH
        self._conns = {}
        self._connection_settings = {}
        self._index_name = None
        self._doc_type = None
        self._configure_store()

    def _clear_connections(self):
        self._conns = {}

    def _configure_store(self):
        """
        Configure self variables and connection settings.
        """
        self._connection_settings = CHATBOT_NER_DATASTORE.get(self._engine_name)
        if self._connection_settings is None:
            raise DataStoreSettingsImproperlyConfiguredException()
        self._check_doc_type_for_elasticsearch()
        self._index_name = self._connection_settings[constants.ELASTICSEARCH_ALIAS]
        self._doc_type = self._connection_settings[constants.ELASTICSEARCH_DOC_TYPE]

    @property
    def _default_connection(self):
        return self._get_or_create_new_connection(alias='default', **self._connection_settings)

    def _get_or_create_new_connection(self, alias='default', **kwargs):
        """
        Retrieve a connection with given alias.
        Construct it if necessary (only when configuration was passed to us).

        Raises ``KeyError`` if no client (or its definition) is registered
        under the alias.
        """
        if alias not in self._conns:
            conn = self.connect(**kwargs)
            if not conn:
                raise EngineConnectionException(engine=self._engine_name)
            self._conns[alias] = conn

        return self._conns[alias]

    def _check_doc_type_for_elasticsearch(self):
        """
        Checks if doc_type is present in connection settings, if not an exception is raised

        Raises:
             DataStoreSettingsImproperlyConfiguredException if doc_type was not found in
             connection settings
        """
        if constants.ELASTICSEARCH_DOC_TYPE not in self._connection_settings:
            ner_logger.debug("No doc type is present in chatbot_ner.config.CHATBOT_NER_DATASTORE")
            raise DataStoreSettingsImproperlyConfiguredException(
                'Elasticsearch needs doc_type. Please configure ES_DOC_TYPE in your environment')

    def generate_query_data(self, entities, texts, fuzziness_threshold=1, search_language_script=ENGLISH_LANG):
        if isinstance(texts, str):
            texts = [texts]

        index_header = json.dumps({'index': self._index_name, 'type': self._doc_type})
        query_parts = []
        for text in texts:
            query_parts.append(index_header)
            text_query = _generate_multi_entity_es_query(entities=entities, text=text,
                                                         fuzziness_threshold=fuzziness_threshold,
                                                         language_script=search_language_script)
            query_parts.append(json.dumps(text_query))

        return query_parts

    def get_multi_entity_results(self, entities, texts, fuzziness_threshold=1,
                                 search_language_script=ENGLISH_LANG, **kwargs):
        """
        Returns:
            list of collections.OrderedDict: dictionary mapping each entity for each text
            with their value variants to entity value

        Example:
            db = ElasticSearchDataStore()
            entities = ['city', 'restaurant']
            texts = ['I want to go to mumbai and eat at dominoes pizza',
             ' I want to go Jabalpur']

            get_multi_entity_results(entities, texts)

            Output:
            [
               {
                'restaurant': OrderedDict([
                    ("Domino's Pizza", "Domino's Pizza"),
                    ('Domino', "Domino's Pizza"),
                    ('Dominos', "Domino's Pizza"),
                    ('Pizza Pizza Pizza', 'Pizza Pizza Pizza'),
                    ('Pizza', 'U S  Pizza')]),
                'city': OrderedDict([
                     ('Mumbai', 'Mumbai'),
                     ('mumbai', 'mumbai')])},
                {
                 'city': OrderedDict([
                    ('Jabalpur', 'Jabalpur'),
                    ('Jamalpur', 'Jamalpur'),
                    ('goa', 'goa')]),
                'restaurant': OrderedDict([
                    ('TMOS', 'TMOS'), ('G.', 'G  Pulla Reddy Sweets')])}
            ]
        """
        # entities for which es results need to be logged for debugging purposes
        log_results_for_entities = ['nsdc_language_select',
                                    'nsdc_choose_topik',
                                    'test_giftcard_user_amount',
                                    'pvr_giftcard_user_amount']
        # this boolean will determine if the es result needs to be logged
        # this will be set to true only if one of or all names mentioned in log_results_for_entities list
        # are present in the entities list
        log_es_result = False
        for entity_name in log_results_for_entities:
            if entity_name in entities:
                # if we find at least one entity name for which the es results need to be logged
                # we set the value for the boolean and break the loop
                log_es_result = True
                break
        request_timeout = self._connection_settings.get('request_timeout', 20)
        index_name = self._index_name

        data = []
        for entity_list, text_list in zip(entities, texts):
            data.extend(self.generate_query_data(entity_list, text_list, fuzziness_threshold, search_language_script))

        # add `\n` for each index_header and query data text entry
        query_data = '\n'.join(data)
        kwargs = dict(body=query_data, doc_type=self._doc_type, index=index_name, request_timeout=request_timeout)
        response = None
        try:
            response = self._run_es_search(self._default_connection, **kwargs)
            results = _parse_multi_entity_es_results(response.get("responses"))
            if log_es_result:
                ner_logger.info(f'[ES Result for Entities] result: {results}')
        except es_exceptions.NotFoundError as e:
            raise DataStoreRequestException(f'NotFoundError in datastore query on index: {index_name}',
                                            engine='elasticsearch', request=json.dumps(data),
                                            response=json.dumps(response)) from e
        except es_exceptions.ConnectionError as e:
            raise e
        except Exception as e:
            raise DataStoreRequestException(f'Error in datastore query on index: {index_name}', engine='elasticsearch',
                                            request=json.dumps(data), response=json.dumps(response)) from e

        return results

    @staticmethod
    def connect(connection_url=None, host=None, port=None, user=None, password=None, **kwargs):
        """
        Establishes connection to a single Elasticsearch Instance.
        if connection_url is not None, then host, port, user, password are not used
        Args:
            connection_url: Elasticsearch connection url of the format https://user:secret@host:port/abc .
                            Optional if other parameters are provided.
            host: nodes to connect to . e.g. localhost. Optional if connection_url is provided
            port: port for elasticsearch connection. Optional if connection_url is provided
            user: Optional, username for elasticsearch authentication
            password: Optional, password for elasticsearch authentication
            kwargs: any additional arguments will be passed on to the Transport class and, subsequently,
                    to the Connection instances.
        Returns:
            Elasticsearch client connection object or None

        """
        # TODO: This does not account for ES_SCHEME unless the connection is being made via `connection_url`
        connection = None
        if user and password:
            kwargs = dict(kwargs, http_auth=(user, password))

        if connection_url:
            connection = Elasticsearch(hosts=[connection_url], **kwargs)
        elif host and port:
            connection = Elasticsearch(hosts=[{'host': host, 'port': int(port)}], **kwargs)

        if connection and not connection.ping():
            connection = None

        return connection

    @staticmethod
    def _run_es_search(connection, **kwargs):
        """
        Execute the elasticsearch.ElasticSearch.msearch() method and return all results
        Args:
            connection: Elasticsearch client object
            kwargs:
                Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search
        Returns:
            dictionary, search results from elasticsearch.ElasticSearch.msearch
        """
        return connection.msearch(**kwargs)

    @staticmethod
    def _get_dynamic_fuzziness_threshold(fuzzy_setting):
        """
        Approximately emulate AUTO:[low],[high] functionality of elasticsearch 6.2+ on older versions

        Args:
            fuzzy_setting (int or str): Can be int or "auto" or "auto:<int>,<int>"

        Returns:
             int or str: fuzziness as int when ES version < 6.2
                         otherwise the input is returned as it is
        """
        if isinstance(fuzzy_setting, six.string_types):
            if constants.ELASTICSEARCH_VERSION_MAJOR > 6 \
                    or (constants.ELASTICSEARCH_VERSION_MAJOR == 6 and constants.ELASTICSEARCH_VERSION_MINOR >= 2):
                return fuzzy_setting
            return 'auto'

        return fuzzy_setting
