from __future__ import absolute_import

import logging.handlers
import os

import dotenv
from elasticsearch import RequestsHttpConnection
from requests_aws4auth import AWS4Auth

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_CONFIG_PATH = os.path.join(BASE_DIR, 'model_config')

LOG_PATH = os.path.join(BASE_DIR, 'logs')

# TODO: Set this up via Django LOGGING
# SET UP NER LOGGING
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)

LOG_LEVEL = os.environ.get('DJANGO_LOG_LEVEL', 'error').upper()

# Common formatter
formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s", "%Y-%m-%d %H:%M:%S")

# Handler for Docker stdout
handler_stdout = logging.StreamHandler()
handler_stdout.setLevel(LOG_LEVEL)
handler_stdout.setFormatter(formatter)

# SETUP NER LOGGING
NER_LOG_FILENAME = os.path.join(LOG_PATH, 'ner_log.log')
# Set up a specific logger with our desired output level
ner_logger = logging.getLogger('NERLogger')
ner_logger.setLevel(LOG_LEVEL)
# Add the log message handler to the logger
handler = logging.handlers.WatchedFileHandler(NER_LOG_FILENAME)
# handler = logging.handlers.RotatingFileHandler(NER_LOG_FILENAME, maxBytes=10 * 1024 * 1024, backupCount=5)
handler.setFormatter(formatter)
ner_logger.addHandler(handler)
ner_logger.addHandler(handler_stdout)

# SETUP NLP LIB LOGGING
NLP_LIB_LOG_FILENAME = os.path.join(LOG_PATH, 'nlp_log.log')
# Set up a specific logger with our desired output level
nlp_logger = logging.getLogger('NLPLibLogger')
nlp_logger.setLevel(LOG_LEVEL)
# Add the log message handler to the logger
handler = logging.handlers.WatchedFileHandler(NLP_LIB_LOG_FILENAME)
# handler = logging.handlers.RotatingFileHandler(NLP_LIB_LOG_FILENAME, maxBytes=10 * 1024 * 1024, backupCount=5)
handler.setFormatter(formatter)
nlp_logger.addHandler(handler)
nlp_logger.addHandler(handler_stdout)

ENGINE = os.environ.get('ENGINE')
# ES settings (Mandatory to use Text type entities)
ES_SCHEME = os.environ.get('ES_SCHEME', 'http')
ES_URL = os.environ.get('ES_URL')
ES_HOST = os.environ.get('ES_HOST')
ES_PORT = os.environ.get('ES_PORT')
ES_ALIAS = os.environ.get('ES_ALIAS')
ES_INDEX_1 = os.environ.get('ES_INDEX_1')
ES_DOC_TYPE = os.environ.get('ES_DOC_TYPE', 'data_dictionary')
ES_AUTH_NAME = os.environ.get('ES_AUTH_NAME')
ES_AUTH_PASSWORD = os.environ.get('ES_AUTH_PASSWORD')
ES_BULK_MSG_SIZE = os.environ.get('ES_BULK_MSG_SIZE', '10000')
ES_SEARCH_SIZE = os.environ.get('ES_SEARCH_SIZE', '10000')

try:
    ES_BULK_MSG_SIZE = int(ES_BULK_MSG_SIZE)
    ES_SEARCH_SIZE = int(ES_SEARCH_SIZE)
except ValueError:
    ES_BULK_MSG_SIZE = 1000
    ES_SEARCH_SIZE = 1000

ELASTICSEARCH_CRF_DATA_INDEX_NAME = os.environ.get('ELASTICSEARCH_CRF_DATA_INDEX_NAME')
ELASTICSEARCH_CRF_DATA_DOC_TYPE = os.environ.get('ELASTICSEARCH_CRF_DATA_DOC_TYPE')

# Optional Vars
ES_INDEX_2 = os.environ.get('ES_INDEX_2')
DESTINATION_ES_SCHEME = os.environ.get('DESTINATION_ES_SCHEME', 'http')
DESTINATION_HOST = os.environ.get('DESTINATION_HOST')
DESTINATION_PORT = os.environ.get('DESTINATION_PORT')
DESTINATION_URL = '{scheme}://{host}:{port}'.format(**{'scheme': DESTINATION_ES_SCHEME,
                                                       'host': DESTINATION_HOST,
                                                       'port': DESTINATION_PORT})

if ENGINE:
    ENGINE = ENGINE.lower()
    if ENGINE == 'elasticsearch':
        if not all(key is not None and key.strip() for key in (ES_ALIAS, ES_INDEX_1, ES_DOC_TYPE)):
            raise Exception(
                'Invalid configuration for datastore (engine=elasticsearch). One or more of following keys: '
                '`ES_ALIAS`, `ES_INDEX_1`, `ES_DOC_TYPE` is null in env')
else:
    ner_logger.warning("`ENGINE` variable is not set, Text type entities won't work without it")

CHATBOT_NER_DATASTORE = {
    'engine': ENGINE,
    'elasticsearch': {
        'connection_url': ES_URL,  # Elastic Search URL
        'es_scheme': ES_SCHEME,  # The scheme used in ES default value is http://
        'host': ES_HOST,  # Elastic Search Host
        'port': ES_PORT,  # Port of elastic search
        'user': ES_AUTH_NAME,
        'password': ES_AUTH_PASSWORD,
        'es_alias': ES_ALIAS,  # Elastic search alias used in transfer
        'es_index_1': ES_INDEX_1,
        'doc_type': ES_DOC_TYPE,  # Index's doc type
        'retry_on_timeout': False,
        'max_retries': 1,
        'timeout': 20,
        'request_timeout': 20,

        # Transfer Specific constants (ignore if only one elasticsearch is setup)
        # For detailed explanation datastore.elastic_search.transfer.py
        'es_index_2': ES_INDEX_2,  # Index 2 used for transfer
        'destination_url': DESTINATION_URL,  # Elastic search destination  URL

        # Training Data ES constants
        'elasticsearch_crf_data_index_name': ELASTICSEARCH_CRF_DATA_INDEX_NAME,
        'elasticsearch_crf_data_doc_type': ELASTICSEARCH_CRF_DATA_DOC_TYPE,
    }
}

ES_AWS_SERVICE = os.environ.get('ES_AWS_SERVICE')
ES_AWS_REGION = os.environ.get('ES_AWS_REGION')
ES_AWS_ACCESS_KEY_ID = os.environ.get('ES_AWS_ACCESS_KEY_ID')
ES_AWS_SECRET_ACCESS_KEY = os.environ.get('ES_AWS_SECRET_ACCESS_KEY')

if ES_AWS_SERVICE and ES_AWS_REGION:
    ner_logger.info('`ES_AWS_SERVICE` and `ES_AWS_REGION` are set. Using AWS Elasticsearch settings ')
    CHATBOT_NER_DATASTORE['elasticsearch']['use_ssl'] = True
    CHATBOT_NER_DATASTORE['elasticsearch']['verify_certs'] = True
    CHATBOT_NER_DATASTORE['elasticsearch']['connection_class'] = RequestsHttpConnection
    if ES_AWS_ACCESS_KEY_ID and ES_AWS_SECRET_ACCESS_KEY:
        CHATBOT_NER_DATASTORE['elasticsearch']['http_auth'] = AWS4Auth(ES_AWS_ACCESS_KEY_ID,
                                                                       ES_AWS_SECRET_ACCESS_KEY,
                                                                       ES_AWS_REGION, ES_AWS_SERVICE)
else:
    ner_logger.warning('`ES_AWS_SERVICE` and `ES_AWS_REGION` are not set. '
                       'This is not a problem if you are using self hosted ES')

# TODO: Remove non functional crf code and cleanup
# Model Vars
# Crf Model Specific (Mandatory to use CRF Model)
CRF_MODELS_PATH = os.environ.get('MODELS_PATH')
CRF_EMBEDDINGS_PATH_VOCAB = os.environ.get('EMBEDDINGS_PATH_VOCAB')
CRF_EMBEDDINGS_PATH_VECTORS = os.environ.get('EMBEDDINGS_PATH_VECTORS')

if os.path.exists(MODEL_CONFIG_PATH):
    dotenv.read_dotenv(MODEL_CONFIG_PATH)
else:
    ner_logger.warning('Warning: no file named "model_config" found at %s. This is not a problem if you '
                       'dont want to run NER with ML models', MODEL_CONFIG_PATH)

CITY_MODEL_TYPE = os.environ.get('CITY_MODEL_TYPE')
CITY_MODEL_PATH = os.environ.get('CITY_MODEL_PATH')
DATE_MODEL_TYPE = os.environ.get('DATE_MODEL_TYPE')
DATE_MODEL_PATH = os.environ.get('DATE_MODEL_PATH')
if not CITY_MODEL_PATH:
    CITY_MODEL_PATH = os.path.join(BASE_DIR, 'data', 'models', 'crf', 'city', 'model_13062017.crf')
if not DATE_MODEL_PATH:
    DATE_MODEL_PATH = os.path.join(BASE_DIR, 'data', 'models', 'crf', 'date', 'model_date.crf')

# Crf Model Specific with additional AWS storage (optional)
CRF_MODEL_S3_BUCKET_NAME = os.environ.get('CRF_MODEL_S3_BUCKET_NAME')
CRF_MODEL_S3_BUCKET_REGION = os.environ.get('CRF_MODEL_S3_BUCKET_REGION')
WORD_EMBEDDING_REMOTE_URL = os.environ.get('WORD_EMBEDDING_REMOTE_URL')
GOOGLE_TRANSLATE_API_KEY = os.environ.get('GOOGLE_TRANSLATE_API_KEY')

if not GOOGLE_TRANSLATE_API_KEY:
    ner_logger.warning('Google Translate API key is null or not set')
    GOOGLE_TRANSLATE_API_KEY = ''
