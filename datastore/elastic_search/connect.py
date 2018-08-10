from elasticsearch import Elasticsearch
import requests
from chatbot_ner.config import CHATBOT_NER_DATASTORE
import json
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


def _get_current_live_index(alias_name):
    es_scheme = ''
    es_url = (es_scheme + "://" +
                          CHATBOT_NER_DATASTORE.get('host') + ":" +
                          CHATBOT_NER_DATASTORE.get('port'))
    current_live_index = fetch_index_alias_points_to(es_url, alias_name)
    return current_live_index


def fetch_index_alias_points_to(es_url, alias_name):
    """
    This function fetches the current live index, ie the index the alias points to

    Args
        es_url (str): The elasticsearch URL
        alias_name (str):  The name of alias for which the list of indices has to be fetched

    Returns
        current_live_index (str): The current live index
    """
    response = requests.get(es_url + '/*/_alias/' + alias_name)
    if response.status_code == 200:
        json_obj = json.loads(response.content)
        indices = json_obj.keys()
        if '' in indices:
            return ''
        elif '' in indices:
            return ''
        else:
            raise FetchIndexForAliasException(alias_name)
    raise FetchIndexForAliasException('fetch index for ' + alias_name + ' failed')

