from __future__ import absolute_import

import structlog
import os

from elasticsearch import RequestsHttpConnection
from requests_aws4auth import AWS4Auth

ner_logger = structlog.getLogger('chatbot_ner')

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
ES_BULK_MSG_SIZE = int((os.environ.get('ES_BULK_MSG_SIZE') or '').strip() or '1000')
ES_SEARCH_SIZE = int((os.environ.get('ES_SEARCH_SIZE') or '').strip() or '1000')
ES_REQUEST_TIMEOUT = int((os.environ.get('ES_REQUEST_TIMEOUT') or '').strip() or '20')

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

DISABLE_REPLICAS_WHILE_TRANFERRING = os.environ.get('DISABLE_REPLICAS_WHILE_TRANFERRING', False)

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
        'request_timeout': ES_REQUEST_TIMEOUT,

        # Transfer Specific constants (ignore if only one elasticsearch is setup)
        # For detailed explanation datastore.elastic_search.transfer.py
        'es_index_2': ES_INDEX_2,  # Index 2 used for transfer
        'destination_url': DESTINATION_URL,  # Elastic search destination  URL
        # flag to disable replicas and re-enable once transfer is done
        'disable_replicas_while_transferring': DISABLE_REPLICAS_WHILE_TRANFERRING,

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

GOOGLE_TRANSLATE_API_KEY = os.environ.get('GOOGLE_TRANSLATE_API_KEY')
if not GOOGLE_TRANSLATE_API_KEY:
    ner_logger.warning('Google Translate API key is null or not set')
    GOOGLE_TRANSLATE_API_KEY = ''
