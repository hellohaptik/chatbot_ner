import elastic_search
from chatbot_ner.config import ner_logger, HAPTIK_NER_DATASTORE
from .constants import ELASTICSEARCH, ENGINE, ELASTICSEARCH_INDEX_NAME, DEFAULT_ENTITY_DATA_DIRECTORY, \
    ELASTICSEARCH_DOC_TYPE
from .exceptions import DataStoreSettingsImproperlyConfiguredException, EngineNotImplementedException


class DataStore(object):
    def __init__(self):
        self._engine = HAPTIK_NER_DATASTORE.get(ENGINE)
        if self._engine is None:
            raise DataStoreSettingsImproperlyConfiguredException()
        self._connection_settings = HAPTIK_NER_DATASTORE.get(self._engine)
        if self._connection_settings is None:
            raise DataStoreSettingsImproperlyConfiguredException()
        # This can be index name for elastic search, table name for SQL,
        self._store_name = None
        self._connection = None
        self._connect()

    def _connect(self):
        if self._engine == ELASTICSEARCH:
            self._store_name = self._connection_settings.get(ELASTICSEARCH_INDEX_NAME, '_all')
            self._connection = elastic_search.connect.connect(**self._connection_settings)
        else:
            self._connection = None
            raise EngineNotImplementedException()

    def create(self, **kwargs):
        if self._engine == ELASTICSEARCH:
            if ELASTICSEARCH_DOC_TYPE not in self._connection_settings:
                raise DataStoreSettingsImproperlyConfiguredException(
                    'Elasticsearch needs doc_type. Please configure ES_DOC_TYPE in your environment')
            elastic_search.create.create_index(connection=self._connection,
                                               index_name=self._store_name,
                                               doc_type=self._connection_settings[ELASTICSEARCH_DOC_TYPE],
                                               logger=ner_logger,
                                               ignore=[400, 404],
                                               **kwargs)

    def populate(self, entity_data_directory_path=DEFAULT_ENTITY_DATA_DIRECTORY, **kwargs):
        if self._engine == ELASTICSEARCH:
            if ELASTICSEARCH_DOC_TYPE not in self._connection_settings:
                raise DataStoreSettingsImproperlyConfiguredException(
                    'Elasticsearch needs doc_type. Please configure ES_DOC_TYPE in your environment')
            elastic_search.populate.create_all_dictionary_data(connection=self._connection,
                                                               index_name=self._store_name,
                                                               doc_type=self._connection_settings[
                                                                   ELASTICSEARCH_DOC_TYPE],
                                                               entity_data_directory_path=entity_data_directory_path,
                                                               logger=ner_logger,
                                                               **kwargs)

    def delete(self, **kwargs):
        if self._engine == ELASTICSEARCH:
            elastic_search.create.delete_index(connection=self._connection,
                                               index_name=self._store_name,
                                               logger=ner_logger,
                                               ignore=[400, 404],
                                               **kwargs)

    def get_entity_dictionary(self, entity_name, **kwargs):
        results_dictionary = {}
        if self._engine == ELASTICSEARCH:
            results_dictionary = elastic_search.query.dictionary_query(connection=self._connection,
                                                                       index_name=self._store_name,
                                                                       entity_list_name=entity_name,
                                                                       **kwargs)

        return results_dictionary

    def get_similar_ngrams_dictionary(self, entity_name, ngrams_list, fuzziness_threshold=1, **kwargs):
        results_dictionary = {}
        if self._engine == ELASTICSEARCH:
            if ngrams_list:
                ngrams_length = len(ngrams_list[0].strip().split())
                results_dictionary = elastic_search.query.ngrams_query(connection=self._connection,
                                                                       index_name=self._store_name,
                                                                       entity_list_name=entity_name,
                                                                       ngrams_list=ngrams_list,
                                                                       ngrams_length=ngrams_length,
                                                                       fuzziness_threshold=fuzziness_threshold,
                                                                       **kwargs)

        return results_dictionary
