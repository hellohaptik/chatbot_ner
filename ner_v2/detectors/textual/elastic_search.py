from __future__ import absolute_import

import json
import six

from itertools import chain
from elasticsearch import Elasticsearch

from lib.singleton import Singleton
from chatbot_ner.config import ner_logger, CHATBOT_NER_DATASTORE
from datastore import constants
from datastore.exceptions import DataStoreSettingsImproperlyConfiguredException, DataStoreRequestException
from language_utilities.constant import ENGLISH_LANG

from ner_v2.detectors.textual.queries import _generate_multi_entity_es_query, \
    _parse_multi_entity_es_results


class ElasticSearchDataStore(six.with_metaclass(Singleton, object)):
    """
    Class responsible for holding connections and performing search in
    ElasticSearch DB.
    Used as a singleton in this module.
    """

    def __init__(self):
        self._engine_name = constants.ELASTICSEARCH
        self._kwargs = {}
        self._conns = {}
        self._connection_settings = {}
        self._connection = None
        self._index_name = None

        self.query_data = []

        # configure variables and connection
        self._configure_store()

        # define doc type
        self.doc_type = self._connection_settings[
            constants.ELASTICSEARCH_DOC_TYPE]

    def _configure_store(self, **kwargs):
        """
        Configure self variables and connection.
        Also add default connection to registry with alias `default`
        """
        self._connection_settings = CHATBOT_NER_DATASTORE. \
            get(self._engine_name)

        if self._connection_settings is None:
            raise DataStoreSettingsImproperlyConfiguredException()

        self._index_name = self._connection_settings[constants.ELASTICSEARCH_ALIAS]
        self._connection = self.connect(**self._connection_settings)

        self._conns['default'] = self._connection

    def add_new_connection(self, alias, conn):
        """
        Add new connection object, which can be  directly passed through as-is to
        the connection registry.
        """
        self._conns[alias] = conn

    def get_or_create_new_connection(self, alias="default", **kwargs):
        """
        Retrieve a connection with given alias.
        Construct it if necessary (only when configuration was passed to us).

        If some non-string alias has been passed through it assume a client instance
        and will just return it as-is.

        Raises ``KeyError`` if no client (or its definition) is registered
        under the alias.
        """

        if not isinstance(alias, six.string_types):
            return alias

        # connection already established
        try:
            return self._conns[alias]
        except KeyError:
            pass

        # if not, try to create it a new connection
        try:
            conn = self.connect(**kwargs)
            self._conns[alias] = conn
        except KeyError:
            # no connection and no kwargs to set one up
            raise KeyError("There is no connection with alias %r." % alias)

    # check if this is necessary here
    def _check_doc_type_for_elasticsearch(self):
        """
        Checks if doc_type is present in connection settings, if not an exception is raised

        Raises:
             DataStoreSettingsImproperlyConfiguredException if doc_type was not found in
             connection settings
        """
        # TODO: This check should be during init or boot
        if constants.ELASTICSEARCH_DOC_TYPE not in self._connection_settings:
            ner_logger.debug("No doc type is present")
            raise DataStoreSettingsImproperlyConfiguredException(
                'Elasticsearch needs doc_type. Please configure ES_DOC_TYPE in your environment')

    def generate_query_data(self, entities, texts, fuzziness_threshold=1,
                            search_language_script=ENGLISH_LANG):

        # check if text is string
        if isinstance(texts, str):
            texts = [texts]

        index_header = json.dumps({'index': self._index_name, 'type': self.doc_type})

        data = list(chain.from_iterable([[index_header,
                                          json.dumps(_generate_multi_entity_es_query(
                                              entities=entities,
                                              text=each,
                                              fuzziness_threshold=fuzziness_threshold,
                                              language_script=search_language_script))]
                                         for each in texts]))

        return data

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

        self._check_doc_type_for_elasticsearch()
        request_timeout = self._connection_settings.get('request_timeout', 20)
        index_name = self._index_name

        data = []
        for entity_list, text_list in zip(entities, texts):
            data.extend(self.generate_query_data(entity_list, text_list, fuzziness_threshold,
                                                 search_language_script))

        # add `\n` for each index_header and query data text entry
        query_data = '\n'.join(data)

        kwargs = dict(body=query_data, doc_type=self.doc_type, index=index_name,
                      request_timeout=request_timeout)
        response = None
        try:
            response = self._run_es_search(self._connection, **kwargs)
            results = _parse_multi_entity_es_results(response.get("responses"))
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
            Elasticsearch client connection object

        """
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
                    or (constants.ELASTICSEARCH_VERSION_MAJOR == 6
                        and constants.ELASTICSEARCH_VERSION_MINOR >= 2):
                return fuzzy_setting
            return 'auto'

        return fuzzy_setting
