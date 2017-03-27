import os
from chatbot_ner.settings import BASE_DIR
from chatbot_ner.config import ES_BULK_MSG_SIZE

DEFAULT_ENTITY_DATA_DIRECTORY = os.path.join(os.path.join(BASE_DIR, 'data'), 'entity_data')
ELASTICSEARCH = 'elasticsearch'
ELASTICSEARCH_SEARCH_SIZE = 100
ELASTICSEARCH_BULK_HELPER_MESSAGE_SIZE = ES_BULK_MSG_SIZE

# settings dictionary key constants
ENGINE = 'engine'
ELASTICSEARCH_INDEX_NAME = 'name'
ELASTICSEARCH_DOC_TYPE = 'doc_type'
