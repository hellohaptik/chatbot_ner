from __future__ import absolute_import

from django.test import TestCase
from elasticsearch import Elasticsearch
import json

from ner_v2.detectors.textual.elastic_search import ElasticSearchDataStore
from chatbot_ner.config import CHATBOT_NER_DATASTORE, ES_SEARCH_SIZE, ES_ALIAS, ES_DOC_TYPE


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

    def test_add_query(self):
        es = ElasticSearchDataStore()

        entity_list_1 = ['city', 'restaurant']
        text_1 = "I want to go to mumbai"

        query_data = es.generate_query_data(entities=entity_list_1, texts=text_1)

        query_data = [json.loads(x) for x in query_data]

        assert_data = [{'index': ES_ALIAS, 'type': ES_DOC_TYPE},
                       {'_source': ['value', 'entity_data'],
                        'query': {'bool': {'filter': [{'terms': {'entity_data': ['city',
                                                                                 'restaurant']}},
                                                      {'terms': {'language_script': ['en']}}],
                                           'should': [{'match': {'variants': {'query': 'I want to go to mumbai',
                                                                              'fuzziness': 1,
                                                                              'prefix_length': 1}}}],
                                           'minimum_should_match': 1}},
                        'highlight': {'fields': {'variants': {'type': 'unified'}},
                                      'order': 'score',
                                      'number_of_fragments': 20},
                        'size': ES_SEARCH_SIZE}]

        self.assertEqual(query_data, assert_data)
