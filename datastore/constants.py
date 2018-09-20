import elasticsearch
import os
from chatbot_ner.settings import BASE_DIR
from chatbot_ner.config import ES_BULK_MSG_SIZE, ES_SEARCH_SIZE

DEFAULT_ENTITY_DATA_DIRECTORY = os.path.join(os.path.join(BASE_DIR, 'data'), 'entity_data')
ELASTICSEARCH = 'elasticsearch'
ELASTICSEARCH_SEARCH_SIZE = ES_SEARCH_SIZE
ELASTICSEARCH_BULK_HELPER_MESSAGE_SIZE = ES_BULK_MSG_SIZE

# settings dictionary key constants
ENGINE = 'engine'
ELASTICSEARCH_INDEX_NAME = 'name'
ELASTICSEARCH_DOC_TYPE = 'doc_type'
ELASTICSEARCH_VERSION_MAJOR, ELASTICSEARCH_VERSION_MINOR, ELASTICSEARCH_VERSION_OTHER = elasticsearch.VERSION
ELASTICSEARCH_CRF_DATA_INDEX_NAME = 'elasticsearch_crf_data_index_name'
ELASTICSEARCH_CRF_DATA_DOC_TYPE = 'elasticsearch_crf_data_doc_type'
