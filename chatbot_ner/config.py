import os
import dotenv
import logging.handlers
from requests_aws4auth import AWS4Auth
from elasticsearch import RequestsHttpConnection

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config')

LOG_PATH = BASE_DIR + '/logs/'
# SET UP NER LOGGING
NER_LOG_FILENAME = LOG_PATH + 'ner_log.log'
# Set up a specific logger with our desired output level
ner_logger = logging.getLogger('NERLogger')
ner_logger.setLevel(logging.DEBUG)
# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(NER_LOG_FILENAME, maxBytes=10 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
ner_logger.addHandler(handler)

# SET UP NLP LIB LOGGING
NLP_LIB_LOG_FILENAME = LOG_PATH + 'nlp_log.log'
# Set up a specific logger with our desired output level
nlp_logger = logging.getLogger('NLPLibLogger')
nlp_logger.setLevel(logging.DEBUG)
# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(NLP_LIB_LOG_FILENAME, maxBytes=10 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
nlp_logger.addHandler(handler)

if os.path.exists(CONFIG_PATH):
    dotenv.read_dotenv(CONFIG_PATH)
else:
    ner_logger.debug('Warning: no file named "config" found at %s. This is not a problem if your '
                     'datastore(elasticsearch) connection settings are already available in the environment',
                     CONFIG_PATH)

# TODO Consider prefixing everything config with HAPTIK_NER_ because these names are in the environment and so are
# TODO lot of others too which may conflict in name. Example user is already using some another instance of
# TODO Elasticsearch for other purposes
ENGINE = os.environ.get('ENGINE')
if ENGINE:
    ENGINE = ENGINE.lower()
ES_URL = os.environ.get('ES_URL')
ES_HOST = os.environ.get('ES_HOST')
ES_PORT = os.environ.get('ES_PORT')
ES_INDEX_NAME = os.environ.get('ES_INDEX_NAME')
ES_DOC_TYPE = os.environ.get('ES_DOC_TYPE')
ES_AUTH_NAME = os.environ.get('ES_AUTH_NAME')
ES_AUTH_PASSWORD = os.environ.get('ES_AUTH_PASSWORD')
ES_BULK_MSG_SIZE = os.environ.get('ES_BULK_MSG_SIZE', '10000')

try:
    ES_BULK_MSG_SIZE = int(ES_BULK_MSG_SIZE)
except ValueError:
    ES_BULK_MSG_SIZE = 10000

ES_AWS_SECRET_ACCESS_KEY = os.environ.get('ES_AWS_SECRET_ACCESS_KEY')
ES_AWS_ACCESS_KEY_ID = os.environ.get('ES_AWS_ACCESS_KEY_ID')
ES_AWS_REGION = os.environ.get('ES_AWS_REGION')
ES_AWS_SERVICE = os.environ.get('ES_AWS_SERVICE')

CHATBOT_NER_DATASTORE = {
    'engine': ENGINE,
    'elasticsearch': {
        'connection_url': ES_URL,
        'name': ES_INDEX_NAME,
        'host': ES_HOST,
        'port': ES_PORT,
        'user': ES_AUTH_NAME,
        'password': ES_AUTH_PASSWORD,
    }
}

if ES_DOC_TYPE:
    CHATBOT_NER_DATASTORE['elasticsearch']['doc_type'] = ES_DOC_TYPE
else:
    CHATBOT_NER_DATASTORE['elasticsearch']['doc_type'] = 'data_dictionary'

if not ES_AWS_SERVICE:
    ES_AWS_SERVICE = 'es'

if ES_AWS_ACCESS_KEY_ID and ES_AWS_SECRET_ACCESS_KEY and ES_AWS_REGION and ES_AWS_SERVICE:
    CHATBOT_NER_DATASTORE['elasticsearch']['http_auth'] = AWS4Auth(ES_AWS_ACCESS_KEY_ID, ES_AWS_SECRET_ACCESS_KEY,
                                                                   ES_AWS_REGION, ES_AWS_SERVICE)
    CHATBOT_NER_DATASTORE['elasticsearch']['use_ssl'] = True
    CHATBOT_NER_DATASTORE['elasticsearch']['verify_certs'] = True
    CHATBOT_NER_DATASTORE['elasticsearch']['connection_class'] = RequestsHttpConnection
else:
    ner_logger.debug('Elasticsearch: Some or all AWS settings missing from environment, this will skip AWS auth!')
