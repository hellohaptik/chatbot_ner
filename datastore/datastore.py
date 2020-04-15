from __future__ import absolute_import

import warnings

import six

from chatbot_ner.config import ner_logger, CHATBOT_NER_DATASTORE
from datastore import elastic_search
from datastore.constants import (ELASTICSEARCH, ENGINE, ELASTICSEARCH_ALIAS, ELASTICSEARCH_INDEX_1,
                                 ELASTICSEARCH_INDEX_2, ELASTICSEARCH_DOC_TYPE, ELASTICSEARCH_CRF_DATA_INDEX_NAME,
                                 ELASTICSEARCH_CRF_DATA_DOC_TYPE)
from datastore.elastic_search.transfer import ESTransfer
from datastore.exceptions import (DataStoreSettingsImproperlyConfiguredException, EngineNotImplementedException,
                                  EngineConnectionException, NonESEngineTransferException, IndexNotFoundException)
from lib.singleton import Singleton


class DataStore(six.with_metaclass(Singleton, object)):
    """
    Singleton class to connect to engine storing entity related data

    DataStore acts as a wrapper around storage/cache engines to store entity related data, query them with entity
    values to get dictionaries that contain similar words/phrases based on fuzzy searches and conditions. It reads the
    required configuration from environment variables.

    It provides a simple API to create, populate, delete and query the underlying storage of choice

    It supports the following storage/cache/database engines:

        NAME                                             USES
        --------------------------------------------------------------------------------------------------
        1. elasticsearch                                 https://github.com/elastic/elasticsearch-py

    Attributes:
        _engine: Engine name as read from the environment config
        _connection_settings: Connection settings compiled from variables in the environment config
        _store_name: Name of the database/index to query on the engine server
        _client_or_connection: Low level connection object to the engine, None at initialization
    """

    def __init__(self):
        """
        Initializes DataStore object with the config set in environment variables.

        Raises:
            DataStoreSettingsImproperlyConfiguredException if connection settings are invalid or missing
        """
        self._engine = CHATBOT_NER_DATASTORE.get(ENGINE)
        if self._engine is None:
            raise DataStoreSettingsImproperlyConfiguredException()
        self._connection_settings = CHATBOT_NER_DATASTORE.get(self._engine)
        if self._connection_settings is None:
            raise DataStoreSettingsImproperlyConfiguredException()
        # This can be index name for elastic search, table name for SQL,
        self._store_name = None
        self._client_or_connection = None
        self._connect()

    def _connect(self):
        """
        Connects to the configured engine using the appropriate drivers

        Raises:
            EngineNotImplementedException if the ENGINE for DataStore setting is not supported or has unexpected value
            EngineConnectionException if DataStore is unable to connect to ENGINE service
            All other exceptions raised by elasticsearch-py library
        """
        if self._engine == ELASTICSEARCH:
            self._store_name = self._connection_settings[ELASTICSEARCH_ALIAS]
            self._client_or_connection = elastic_search.connect.connect(**self._connection_settings)
        else:
            self._client_or_connection = None
            raise EngineNotImplementedException()

        if self._client_or_connection is None:
            raise EngineConnectionException(engine=self._engine)

    def create(self, ignore_if_exists=False, **kwargs):
        """
        Creates the schema/structure for the datastore depending on the engine configured in the environment.

        Args:
            ignore_if_exists (bool): if to ignore index already exists errors, default False
            kwargs:
                For Elasticsearch:
                    master_timeout: Specify timeout for connection to master
                    timeout: Explicit operation timeout
                    update_all_types: Whether to update the mapping for all fields with the same name across all types
                                      or not
                    wait_for_active_shards: Set the number of active shards to wait for before the operation returns.
                    doc_type: The name of the document type
                    allow_no_indices: Whether to ignore if a wildcard indices expression resolves into no concrete
                                      indices. (This includes _all string or when no indices have been specified)
                    expand_wildcards: Whether to expand wildcard expression to concrete indices that are open, closed
                                      or both., default 'open', valid choices are: 'open', 'closed', 'none', 'all'
                    ignore_unavailable: Whether specified concrete indices should be ignored when unavailable
                                        (missing or closed)

        Refer--
           https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.client.IndicesClient.create
           https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.client.IndicesClient.put_mapping

        Raises:
            DataStoreSettingsImproperlyConfiguredException if connection settings are invalid or missing
            All other exceptions raised by elasticsearch-py library
        """
        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            es_url = elastic_search.connect.get_es_url()
            es_object = ESTransfer(source=es_url, destination=None)
            self._check_doc_type_for_elasticsearch()
            elastic_search.create.create_entity_index(connection=self._client_or_connection,
                                                      index_name=self._connection_settings[ELASTICSEARCH_INDEX_1],
                                                      doc_type=self._connection_settings[ELASTICSEARCH_DOC_TYPE],
                                                      logger=ner_logger,
                                                      ignore_if_exists=ignore_if_exists,
                                                      **kwargs)
            es_object.point_an_alias_to_index(es_url=es_url, alias_name=self._store_name,
                                              index_name=self._connection_settings[ELASTICSEARCH_INDEX_1])

            if self._connection_settings.get(ELASTICSEARCH_INDEX_2):
                elastic_search.create.create_entity_index(connection=self._client_or_connection,
                                                          index_name=self._connection_settings[ELASTICSEARCH_INDEX_2],
                                                          doc_type=self._connection_settings[ELASTICSEARCH_DOC_TYPE],
                                                          logger=ner_logger,
                                                          ignore_if_exists=ignore_if_exists,
                                                          **kwargs)
                es_object.point_an_alias_to_index(es_url=es_url, alias_name=self._store_name,
                                                  index_name=self._connection_settings[ELASTICSEARCH_INDEX_2])

            if self._connection_settings.get(ELASTICSEARCH_CRF_DATA_INDEX_NAME):
                self._check_doc_type_for_crf_data_elasticsearch()
                elastic_search.create.create_crf_index(
                    connection=self._client_or_connection,
                    index_name=self._connection_settings.get[ELASTICSEARCH_CRF_DATA_INDEX_NAME],
                    doc_type=self._connection_settings[ELASTICSEARCH_CRF_DATA_DOC_TYPE],
                    logger=ner_logger,
                    ignore_if_exists=ignore_if_exists,
                    **kwargs
                )

    # FIXME: repopulate does not consider language of the variants
    def populate(self, entity_data_directory_path=None, csv_file_paths=None, **kwargs):
        """
        Populates the datastore from csv files stored in directory path indicated by entity_data_directory_path and
        from csv files at file paths in csv_file_paths list
        Args:
            entity_data_directory_path: Optional, Directory path containing CSV files to populate the datastore from.
                                        See the CSV file structure explanation in the datastore docs
            csv_file_paths: Optional, list of absolute file paths to csv files
            kwargs:
                For Elasticsearch:
                    Refer http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.bulk

        Raises:
            DataStoreSettingsImproperlyConfiguredException if connection settings are invalid or missing
            All other exceptions raised by elasticsearch-py library

        """
        if not (entity_data_directory_path or csv_file_paths):
            raise ValueError('Both `entity_data_directory_path` and `csv_file_paths` arguments cannot be None.'
                             'Either provide a path to directory containing csv files using '
                             '`entity_data_directory_path` or a list of paths to csv files '
                             'using `csv_file_paths`')
        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_elasticsearch()
            elastic_search.populate.create_all_dictionary_data(connection=self._client_or_connection,
                                                               index_name=self._store_name,
                                                               doc_type=self._connection_settings[
                                                                   ELASTICSEARCH_DOC_TYPE],
                                                               entity_data_directory_path=entity_data_directory_path,
                                                               csv_file_paths=csv_file_paths,
                                                               logger=ner_logger,
                                                               **kwargs)

    def delete(self, **kwargs):
        """
        Deletes all data including the structure of the datastore. Note that this is equivalent to DROP not TRUNCATE

        Args:
            kwargs:
                For Elasticsearch:
                    body: The configuration for the index (settings and mappings)
                    master_timeout: Specify timeout for connection to master
                    timeout: Explicit operation timeout
                    update_all_types: Whether to update the mapping for all fields with the same name across all types
                                      or not
                    wait_for_active_shards: Set the number of active shards to wait for before the operation returns.

            Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.client.IndicesClient.delete

        Raises:
            All exceptions raised by elasticsearch-py library

        """
        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            for index_key in [ELASTICSEARCH_INDEX_1, ELASTICSEARCH_INDEX_2, ELASTICSEARCH_CRF_DATA_INDEX_NAME]:
                if self._connection_settings.get(index_key):
                    elastic_search.create.delete_index(connection=self._client_or_connection,
                                                       index_name=self._store_name,
                                                       logger=ner_logger,
                                                       **kwargs)
            # TODO: cleanup aliases ?

    # FIXME: Deprecated, remove
    def get_entity_dictionary(self, entity_name, **kwargs):
        """
        Args:
            entity_name: the name of the entity to get the stored data for
            kwargs:
                For Elasticsearch:
                    Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search

        Returns:
            dictionary mapping entity values to list of their variants

        Raises:
            DataStoreSettingsImproperlyConfiguredException if connection settings are invalid or missing
            All other exceptions raised by elasticsearch-py library

        Example:
            db = DataStore()
            get_entity_dictionary(entity_name='city')

            Output:

                {u'Ahmednagar': [u'', u'Ahmednagar'],
                u'Alipurduar': [u'', u'Alipurduar'],
                u'Amreli': [u'', u'Amreli'],
                u'Baripada Town': [u'Baripada', u'Baripada Town', u''],
                u'Bettiah': [u'', u'Bettiah'],
                ...
                u'Rajgarh Alwar': [u'', u'Rajgarh', u'Alwar'],
                u'Rajgarh Churu': [u'Churu', u'', u'Rajgarh'],
                u'Rajsamand': [u'', u'Rajsamand'],
                ...
                u'koramangala': [u'koramangala']}
        """
        warnings.warn("get_entity_dictionary() is deprecated; Please use get_entity_data()", DeprecationWarning)
        if self._client_or_connection is None:
            self._connect()
        results_dictionary = {}
        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_elasticsearch()
            request_timeout = self._connection_settings.get('request_timeout', 20)
            results_dictionary = elastic_search.query.dictionary_query(connection=self._client_or_connection,
                                                                       index_name=self._store_name,
                                                                       doc_type=self._connection_settings[
                                                                           ELASTICSEARCH_DOC_TYPE],
                                                                       entity_name=entity_name,
                                                                       request_timeout=request_timeout,
                                                                       **kwargs)

        return results_dictionary

    def get_similar_dictionary(self, entity_name, texts, fuzziness_threshold="auto:4,7",
                               search_language_script=None, **kwargs):
        """
        Args:
            entity_name: the name of the entity to lookup in the datastore for getting entity values and their variants
            texts(list of strings): the text for which variants need to be find out
            fuzziness_threshold: fuzziness allowed for search results on entity value variants
            search_language_script: language of elasticsearch documents which are eligible for match
            kwargs:
                For Elasticsearch:
                    Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search

        Returns:
            list of collections.OrderedDict: dictionary mapping entity value variants to their entity value

        Example:
            db = DataStore()
            ngrams_list = ['Pune', 'Mumbai', 'Goa', 'Bangalore']
            db.get_similar_ngrams_dictionary(entity_name='city', ngrams_list=ngrams_list, fuzziness_threshold=2)

            Output:
                [
                    {u'Bangalore': u'Bangalore',
                     u'Mulbagal': u'Mulbagal',
                     u'Multai': u'Multai',
                     u'Mumbai': u'Mumbai',
                     u'Pune': u'Pune',
                     u'Puri': u'Puri',
                     u'bangalore': u'bengaluru',
                     u'goa': u'goa',
                     u'mumbai': u'mumbai',
                     u'pune': u'pune'}
                 ]
        """
        results_list = []
        if self._client_or_connection is None:
            self._connect()
        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_elasticsearch()
            request_timeout = self._connection_settings.get('request_timeout', 20)
            results_list = elastic_search.query.full_text_query(connection=self._client_or_connection,
                                                                index_name=self._store_name,
                                                                doc_type=self._connection_settings[
                                                                    ELASTICSEARCH_DOC_TYPE],
                                                                entity_name=entity_name,
                                                                sentences=texts,
                                                                fuzziness_threshold=fuzziness_threshold,
                                                                search_language_script=search_language_script,
                                                                request_timeout=request_timeout,
                                                                **kwargs)
        return results_list

    def delete_entity(self, entity_name, **kwargs):
        """
        Deletes the entity data for entity named entity_named from the datastore

        Args:
            entity_name: name of the entity, this is same as the file name of the csv used for this entity while
                         populating data for this entity
            kwargs:
                For Elasticsearch:
                    Refer http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.bulk

        """
        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_elasticsearch()
            elastic_search.populate.delete_entity_by_name(connection=self._client_or_connection,
                                                          index_name=self._store_name,
                                                          doc_type=self._connection_settings[
                                                              ELASTICSEARCH_DOC_TYPE],
                                                          entity_name=entity_name,
                                                          logger=ner_logger,
                                                          **kwargs)

    # FIXME: repopulate does not consider language of the variants
    def repopulate(self, entity_data_directory_path=None, csv_file_paths=None, **kwargs):
        """
        Deletes the existing data and repopulates it for entities from csv files stored in directory path indicated by
        entity_data_directory_path and from csv files at file paths in csv_file_paths list

        Args:
            entity_data_directory_path: Directory path containing CSV files to populate the datastore from.
                                        See the CSV file structure explanation in the datastore docs
            csv_file_paths: Optional, list of absolute file paths to csv files
            kwargs:
                For Elasticsearch:
                    Refer http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.bulk

        Raises:
            DataStoreSettingsImproperlyConfiguredException if connection settings are invalid or missing
            All other exceptions raised by elasticsearch-py library
        """
        if not (entity_data_directory_path or csv_file_paths):
            raise ValueError('Both `entity_data_directory_path` and `csv_file_paths` arguments cannot be None.'
                             'Either provide a path to directory containing csv files using '
                             '`entity_data_directory_path` or a list of paths to csv files '
                             'using `csv_file_paths`')

        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_elasticsearch()
            elastic_search.populate.recreate_all_dictionary_data(connection=self._client_or_connection,
                                                                 index_name=self._store_name,
                                                                 doc_type=self._connection_settings[
                                                                     ELASTICSEARCH_DOC_TYPE],
                                                                 entity_data_directory_path=entity_data_directory_path,
                                                                 csv_file_paths=csv_file_paths,
                                                                 logger=ner_logger,
                                                                 **kwargs)
            # TODO: repopulate code for crf index missing

    def _check_doc_type_for_elasticsearch(self):
        """
        Checks if doc_type is present in connection settings, if not an exception is raised

        Raises:
             DataStoreSettingsImproperlyConfiguredException if doc_type was not found in connection settings
        """
        if ELASTICSEARCH_DOC_TYPE not in self._connection_settings:
            raise DataStoreSettingsImproperlyConfiguredException(
                'Elasticsearch needs doc_type. Please configure ES_DOC_TYPE in your environment')

    def _check_doc_type_for_crf_data_elasticsearch(self):
        """
        Checks if doc_type is present in connection settings, if not an exception is raised

        Raises:
             DataStoreSettingsImproperlyConfiguredException if doc_type was not found in connection settings
        """
        if ELASTICSEARCH_CRF_DATA_DOC_TYPE not in self._connection_settings:
            raise DataStoreSettingsImproperlyConfiguredException(
                'Elasticsearch training data needs doc_type. Please configure '
                'ES_TRAINING_DATA_DOC_TYPE in your environment')

    def exists(self):
        """
        Checks if DataStore is already created
        Returns:
             boolean, True if DataStore structure exists, False otherwise
        """
        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            return elastic_search.create.exists(connection=self._client_or_connection, index_name=self._store_name)

        return False

    # FIXME: Deprecated, remove
    def update_entity_data(self, entity_name, entity_data, language_script, **kwargs):
        """
        This method is used to populate the the entity dictionary
        Args:
            entity_name (str): Name of the dictionary that needs to be populated
            entity_data (list): List of dicts consisting of value and variants
            language_script (str): Language code for the language script used.
            **kwargs:
                For Elasticsearch:
                Refer http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.bulk
        """
        warnings.warn("update_entity_data() is deprecated; Please use add_entity_data()", DeprecationWarning)
        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_elasticsearch()
            update_index = elastic_search.connect.get_current_live_index(self._store_name)
            elastic_search.populate.entity_data_update(connection=self._client_or_connection,
                                                       index_name=update_index,
                                                       doc_type=self._connection_settings[
                                                           ELASTICSEARCH_DOC_TYPE],
                                                       logger=ner_logger,
                                                       entity_data=entity_data,
                                                       entity_name=entity_name,
                                                       language_script=language_script,
                                                       **kwargs)

    def get_entity_supported_languages(self, entity_name, **kwargs):
        """
        Fetch supported language list for the entity
        Args:
            entity_name (str): Name of the entity for which the languages are to be fetched
        Returns:
            (list): List of str language codes
        """
        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_elasticsearch()
            request_timeout = self._connection_settings.get('request_timeout', 20)
            results_dictionary = elastic_search.query.get_entity_supported_languages(
                connection=self._client_or_connection,
                index_name=self._store_name,
                doc_type=self._connection_settings[ELASTICSEARCH_DOC_TYPE],
                entity_name=entity_name,
                request_timeout=request_timeout,
                **kwargs
            )

            return results_dictionary

    def get_entity_unique_values(self, entity_name, **kwargs):
        """
        Get list of unique values in this entity
        Args:
            entity_name (str): Name of the entity for which the unique values are to be fetched
        Returns:
            (list): list of values in this entity
        """
        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_elasticsearch()
            request_timeout = self._connection_settings.get('request_timeout', 20)
            results_dictionary = elastic_search.query.get_entity_unique_values(
                connection=self._client_or_connection,
                index_name=self._store_name,
                doc_type=self._connection_settings[ELASTICSEARCH_DOC_TYPE],
                entity_name=entity_name,
                request_timeout=request_timeout,
                **kwargs
            )

            return results_dictionary

    def delete_entity_data_by_values(self, entity_name, values=None, **kwargs):
        """
        Delete entity data which match the values
        Args:
            entity_name (str): Name of the entity for which the unique values are to be fetched
            values (list, optional): List of values for which records are to be deleted.
                If none, then all records are cleared
        Returns:
            None
        """
        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_elasticsearch()
            update_index = elastic_search.connect.get_current_live_index(self._store_name)
            request_timeout = self._connection_settings.get('request_timeout', 20)
            elastic_search.populate.delete_entity_data_by_values(
                connection=self._client_or_connection,
                index_name=update_index,
                doc_type=self._connection_settings[ELASTICSEARCH_DOC_TYPE],
                entity_name=entity_name,
                values=values,
                request_timeout=request_timeout,
                **kwargs
            )

    def add_entity_data(self, entity_name, value_variant_records, **kwargs):
        """
        Add the specified records under this entity
        Args:
            entity_name (str): Name of the entity for which the unique values are to be fetched
            value_variant_records (list): List of dicts with the value, variants and language script
                Sample Dict: {'value': 'value', 'language_script': 'en', variants': ['variant 1', 'variant 2']}
        Returns:
            None
        """
        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_elasticsearch()
            update_index = elastic_search.connect.get_current_live_index(self._store_name)
            elastic_search.populate.add_entity_data(
                connection=self._client_or_connection,
                index_name=update_index,
                doc_type=self._connection_settings[ELASTICSEARCH_DOC_TYPE],
                entity_name=entity_name,
                value_variant_records=value_variant_records,
                **kwargs
            )

    def get_entity_data(self, entity_name, values=None, **kwargs):
        """
        Fetch entity data for all languages for this entity filtered by the values provided

        Args:
            entity_name (str): Name of the entity for which the entity data is to be fetched
            values (list): List of values for which the entity data is to be fetched
        Returns:
            (list): List of records with entity data matching the filters
        """
        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_elasticsearch()
            request_timeout = self._connection_settings.get('request_timeout', 20)
            results_dictionary = elastic_search.query.get_entity_data(
                connection=self._client_or_connection,
                index_name=self._store_name,
                doc_type=self._connection_settings[ELASTICSEARCH_DOC_TYPE],
                entity_name=entity_name,
                values=values,
                request_timeout=request_timeout,
                **kwargs
            )

            return results_dictionary

    def transfer_entities_elastic_search(self, entity_list):
        """
        This method is used to transfer the entities from one environment to the other for elastic search engine
        only.
        Args:
            entity_list (list): List of entities that have to be transfered
        """
        if self._engine != ELASTICSEARCH:
            raise NonESEngineTransferException
        es_url = CHATBOT_NER_DATASTORE.get(self._engine).get('connection_url')
        if es_url is None:
            es_url = elastic_search.connect.get_es_url()
        if es_url is None:
            raise DataStoreSettingsImproperlyConfiguredException()
        destination = CHATBOT_NER_DATASTORE.get(self._engine).get('destination_url')
        es_object = elastic_search.transfer.ESTransfer(source=es_url, destination=destination)
        es_object.transfer_specific_entities(list_of_entities=entity_list)

    def get_crf_data_for_entity_name(self, entity_name, languages, **kwargs):
        """
        This method is used to obtain the sentences and entities from sentences given entity name

        Args:
            entity_name (str): Entity name for which training data needs to be obtained
            languages (List[str]): list of languges codes for which data is requested
            **kwargs: For Elasticsearch:
                Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search

        Returns:
            results_dictionary(dict): Dictionary consisting of the training data for the the given entity.

        Raises:
            IndexNotFoundException: Description
            IndexNotFoundException if es_training_index was not found in connection settings

        Example:
            db = Datastore()
            db.get_entity_training_data(entity_name, **kwargs):
            >> {
                'sentence_list': [
                        'My name is hardik',
                        'This is my friend Ajay'
                        ],
                'entity_list': [
                        [
                            'hardik'
                        ],
                        [
                            'Ajay'
                        ]
                    ]
                }
        """
        ner_logger.debug('Datastore, get_entity_training_data, entity_name %s' % entity_name)
        if self._client_or_connection is None:
            self._connect()
        results_dictionary = {}
        if self._engine == ELASTICSEARCH:
            es_training_index = self._connection_settings.get(ELASTICSEARCH_CRF_DATA_INDEX_NAME)
            if es_training_index is None:
                raise IndexNotFoundException('Index for ELASTICSEARCH_CRF_DATA_INDEX_NAME not found. '
                                             'Please configure the same')
            self._check_doc_type_for_crf_data_elasticsearch()
            request_timeout = self._connection_settings.get('request_timeout', 20)
            results_dictionary = elastic_search.query.get_crf_data_for_entity_name(
                connection=self._client_or_connection,
                index_name=es_training_index,
                doc_type=self._connection_settings[ELASTICSEARCH_CRF_DATA_DOC_TYPE],
                entity_name=entity_name,
                languages=languages,
                request_timeout=request_timeout,
                **kwargs)
            ner_logger.debug('Datastore, get_entity_training_data, results_dictionary %s' % str(entity_name))
        return results_dictionary

    def update_entity_crf_data(self, entity_name, sentences, **kwargs):
        """
        This method is used to populate the training data for a given entity

        Args:
            entity_name (str): Name of the entity for which the training data has to be populated
            sentences (Dict[str, List[Dict[str, str]]]: sentences mapped against their languages
            **kwargs: For Elasticsearch:
                Refer http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.bulk

        Raises:
            IndexNotFoundException: Description
            IndexNotFoundException if es_training_index was not found in connection settings
        """
        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_crf_data_elasticsearch()

            es_training_index = self._connection_settings.get(ELASTICSEARCH_CRF_DATA_INDEX_NAME)
            if es_training_index is None:
                raise IndexNotFoundException('Index for ELASTICSEARCH_CRF_DATA_INDEX_NAME not found. '
                                             'Please configure the same')

            elastic_search \
                .populate \
                .update_entity_crf_data_populate(connection=self._client_or_connection,
                                                 index_name=es_training_index,
                                                 doc_type=self._connection_settings[ELASTICSEARCH_CRF_DATA_DOC_TYPE],
                                                 logger=ner_logger,
                                                 sentences=sentences,
                                                 entity_name=entity_name,
                                                 **kwargs)
