from elasticsearch import Elasticsearch

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
