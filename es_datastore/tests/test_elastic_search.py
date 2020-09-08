from __future__ import absolute_import

from es_datastore.elastic_search import ElasticSearchDataStore

from elasticsearch import Elasticsearch


def test_elasticsearch_connection():
    c = ElasticSearchDataStore()

    connection = c.get_or_create_new_connection('default')

    assert isinstance(connection, Elasticsearch)


# :TODO: configure parameters here
def test_elasticsearch_connect():

    kwargs = dict()

    connection = ElasticSearchDataStore.connect(**kwargs)

    assert isinstance(connection, Elasticsearch)