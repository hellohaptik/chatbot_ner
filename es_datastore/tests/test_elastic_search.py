from __future__ import absolute_import

from django.test import TestCase
from elasticsearch import Elasticsearch

from es_datastore.elastic_search import ElasticSearchDataStore
from chatbot_ner.config import CHATBOT_NER_DATASTORE


class TestESDataStore(TestCase):
    def test_elasticsearch_connection(self):
        c = ElasticSearchDataStore()

        connection = c.get_or_create_new_connection('default')

        self.assertIsInstance(connection, Elasticsearch)

    # :TODO: configure parameters here
    def test_elasticsearch_connect(self):
        kwargs = CHATBOT_NER_DATASTORE.get('elasticsearch')

        connection = ElasticSearchDataStore.connect(**kwargs)

        self.assertIsInstance(connection, Elasticsearch)

    def test_elasticsearch_get_connection(self):
        c = ElasticSearchDataStore()

        conn = c.get_or_create_new_connection()
        self.assertIsInstance(conn, Elasticsearch)

    def test_elasticsearch_add_connection(self):
        kwargs = CHATBOT_NER_DATASTORE.get('elasticsearch')
        c = Elasticsearch(**kwargs)

        es = ElasticSearchDataStore()
        es.add_new_connection('new', c)

        conn = es.get_or_create_new_connection()
        new_conn = es.get_or_create_new_connection('new')

        self.assertIsInstance(new_conn, Elasticsearch)
        self.assertIsInstance(c, Elasticsearch)
        self.assertIsInstance(conn, Elasticsearch)

    def test_elasticsearch_get_dynamic_fuzziness_threshold(self):
        fuzzy = 1

        fuzzy_threshold = ElasticSearchDataStore._get_dynamic_fuzziness_threshold(fuzzy)

        self.assertEqual(fuzzy_threshold, fuzzy)

        fuzzy = '1'

        fuzzy_threshold = ElasticSearchDataStore._get_dynamic_fuzziness_threshold(fuzzy)

        self.assertEqual(fuzzy_threshold, 'auto')

        # :TODO: Check if below is expected
        fuzzy = 'some_string'

        fuzzy_threshold = ElasticSearchDataStore._get_dynamic_fuzziness_threshold(fuzzy)

        self.assertEqual(fuzzy_threshold, 'auto')
