import elastic_search
from chatbot_ner.config import ner_logger, CHATBOT_NER_DATASTORE
from lib.singleton import Singleton
from .constants import (ELASTICSEARCH, ENGINE, ELASTICSEARCH_INDEX_NAME, DEFAULT_ENTITY_DATA_DIRECTORY,
                        ELASTICSEARCH_DOC_TYPE)
from .exceptions import (DataStoreSettingsImproperlyConfiguredException, EngineNotImplementedException,
                         EngineConnectionException)
from external_api.es_transfer import ESTransfer


class DataStore(object):
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
    __metaclass__ = Singleton

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
        alias_config = CHATBOT_NER_DATASTORE.get(self._engine).get('es_alias_config')
        if self._engine == ELASTICSEARCH:
            self._store_name = self._connection_settings.get(ELASTICSEARCH_INDEX_NAME, '_all')
            if alias_config:
                self._store_name = elastic_search.connect.get_current_live_index(self._store_name)

            self._client_or_connection = elastic_search.connect.connect(**self._connection_settings)
        else:
            self._client_or_connection = None
            raise EngineNotImplementedException()

        if self._client_or_connection is None:
            raise EngineConnectionException(engine=self._engine)

    def create(self, **kwargs):
        """
        Creates the schema/structure for the datastore depending on the engine configured in the environment.

        Args:
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

                    Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.client.IndicesClient.create
                    Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.client.IndicesClient.put_mapping

        Raises:
            DataStoreSettingsImproperlyConfiguredException if connection settings are invalid or missing
            All other exceptions raised by elasticsearch-py library
        """
        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_elasticsearch()
            elastic_search.create.create_index(connection=self._client_or_connection,
                                               index_name=self._store_name,
                                               doc_type=self._connection_settings[ELASTICSEARCH_DOC_TYPE],
                                               logger=ner_logger,
                                               ignore=[400, 404],
                                               **kwargs)

    def populate(self, entity_data_directory_path=DEFAULT_ENTITY_DATA_DIRECTORY, csv_file_paths=None, **kwargs):
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
            elastic_search.create.delete_index(connection=self._client_or_connection,
                                               index_name=self._store_name,
                                               logger=ner_logger,
                                               ignore=[400, 404],
                                               **kwargs)

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

    def get_similar_dictionary(self, entity_name, text, fuzziness_threshold="auto:4,7",
                               search_language_script=None, **kwargs):
        """
        Args:
            entity_name: the name of the entity to lookup in the datastore for getting entity values and their variants
            text: the text for which variants need to be find out
            fuzziness_threshold: fuzziness allowed for search results on entity value variants
            search_language_script: language of elasticsearch documents which are eligible for match
            kwargs:
                For Elasticsearch:
                    Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search

        Returns:
            dictionary mapping entity value variants to their entity value

        Example:
            db = DataStore()
            ngrams_list = ['Pune', 'Mumbai', 'Goa', 'Bangalore']
            db.get_similar_ngrams_dictionary(entity_name='city', ngrams_list=ngrams_list, fuzziness_threshold=2)

            Output:
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
        """
        if self._client_or_connection is None:
            self._connect()
        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_elasticsearch()
            request_timeout = self._connection_settings.get('request_timeout', 20)
            results_dictionary = elastic_search.query.full_text_query(connection=self._client_or_connection,
                                                                      index_name=self._store_name,
                                                                      doc_type=self._connection_settings[
                                                                          ELASTICSEARCH_DOC_TYPE],
                                                                      entity_name=entity_name,
                                                                      sentence=text,
                                                                      fuzziness_threshold=fuzziness_threshold,
                                                                      search_language_script=search_language_script,
                                                                      request_timeout=request_timeout,
                                                                      **kwargs)
        return results_dictionary

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
                                                          ignore=[400, 404],
                                                          **kwargs)

    def repopulate(self, entity_data_directory_path=DEFAULT_ENTITY_DATA_DIRECTORY, csv_file_paths=None, **kwargs):
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
                                                                 ignore=[400, 404],
                                                                 **kwargs)

    def _check_doc_type_for_elasticsearch(self):
        """
        Checks if doc_type is present in connection settings, if not an exception is raised

        Raises:
             DataStoreSettingsImproperlyConfiguredException if doc_type was not found in connection settings
        """
        if ELASTICSEARCH_DOC_TYPE not in self._connection_settings:
            raise DataStoreSettingsImproperlyConfiguredException(
                'Elasticsearch needs doc_type. Please configure ES_DOC_TYPE in your environment')

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

    def external_api_update_entity(self, dictionary_name, dictionary_data, language_script, **kwargs):
        """
        This method is used to populate the the entity dictionary
        Args:
            dictionary_name (str): Name of the dictionary that needs to be populated
            dictionary_data (list): List of dicts consisting of value and variants
            language_script (str): Language code for the language script used.
            **kwargs:
                For Elasticsearch:
                Refer http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.bulk
        """
        if self._client_or_connection is None:
            self._connect()

        if self._engine == ELASTICSEARCH:
            self._check_doc_type_for_elasticsearch()
            elastic_search.populate.external_api_entity_update(connection=self._client_or_connection,
                                                               index_name=self._store_name,
                                                               doc_type=self._connection_settings[
                                                                    ELASTICSEARCH_DOC_TYPE],
                                                               logger=ner_logger,
                                                               dictionary_data=dictionary_data,
                                                               dictionary_name=dictionary_name,
                                                               language_script=language_script,
                                                               **kwargs)

    def transfer_entities(self, entity_list):
        """
        This method is used to transfer the entities from one environment to the other.
        Args:
            entity_list (list): List of entities that have to be transfered
        """
        es_url = CHATBOT_NER_DATASTORE.get(self._engine).get('connection_url')
        if es_url is None:
            es_url = elastic_search.connect.get_es_url()
        if es_url is None:
            raise DataStoreSettingsImproperlyConfiguredException()
        destination = CHATBOT_NER_DATASTORE.get(self._engine).get('destination_url')
        es_object = ESTransfer(source=es_url, destination=destination)
        es_object.transfer_specific_entities(list_of_entities=entity_list)
