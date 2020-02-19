from __future__ import absolute_import
from elasticsearch import Elasticsearch
from chatbot_ner.config import CHATBOT_NER_DATASTORE
from datastore.elastic_search.transfer import ESTransfer
log_prefix = 'datastore.elastic_search.connect'


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

        Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch

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


class FetchIndexForAliasException(Exception):
    """
    This exception is raised if fetch for indices for an alias fails
    """
    pass


def get_current_live_index(alias_name):
    """
    This method is used to get the index the alias is currently pointing to.
    Args:
        alias_name (str): The alias which is pointing tothe indices.

    Returns:
        current_live_index (str): The index to which the alias is pointing.
    """
    es_url = get_es_url()
    es_object = ESTransfer(source=es_url, destination=None)
    current_live_index = es_object.fetch_index_alias_points_to(es_url, alias_name)
    return current_live_index


def get_es_url():
    """
    This method is used to obtain the es_url
    Returns:
        es_url (str): returns es_url currently pointed at
    """
    engine = CHATBOT_NER_DATASTORE.get('engine')
    es_url = (CHATBOT_NER_DATASTORE.get(engine).get('es_scheme', 'http')
              + '://'
              + CHATBOT_NER_DATASTORE.get(engine).get('host') + ":" +
              CHATBOT_NER_DATASTORE.get(engine).get('port'))
    return es_url
