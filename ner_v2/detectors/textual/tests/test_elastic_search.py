from __future__ import absolute_import

import json

import mock
from django.test import TestCase
from elasticsearch import Elasticsearch

from chatbot_ner.config import ES_SEARCH_SIZE, ES_ALIAS, ES_DOC_TYPE
from datastore.exceptions import EngineConnectionException
from ner_v2.detectors.textual.elastic_search import ElasticSearchDataStore


class TestESDataStore(TestCase):
    # Note: All ES networks calls should be properly mocked so that tests can also run without an actual instance
    # and also multiple success failure scenarios can be created
    # TODO: Lot of these tests have overlaps in what they test, needs a cleanup

    def setUp(self):
        self.elasticsearch_engine_settings = {
            'es_scheme': 'http://',
            'host': 'localhost',
            'port': 9200,
            'es_alias': 'test_alias',
            'es_index_1': 'test_index',
            'doc_type': 'test_doc_type',
        }
        self.esds = ElasticSearchDataStore()
        self.esds._clear_connections()  # Needed because `ElasticSearchDataStore` is a singleton instance

    @mock.patch('ner_v2.detectors.textual.elastic_search.Elasticsearch.ping')
    def test_elasticsearch_default_connection(self, mocked_es_ping):
        """Test default connection on `ElasticSearchDataStore`"""
        mocked_es_ping.return_value = True
        self.assertIsInstance(self.esds._default_connection, Elasticsearch)

    @mock.patch('ner_v2.detectors.textual.elastic_search.Elasticsearch.ping')
    def test_elasticsearch_reconnection(self, mocked_es_ping):
        """Test that `ElasticSearchDataStore` recovers connection after a ping fails"""
        mocked_es_ping.return_value = False
        with self.assertRaises(EngineConnectionException):
            _ = self.esds._default_connection

        mocked_es_ping.return_value = True
        self.assertIsInstance(self.esds._default_connection, Elasticsearch)

    @mock.patch('ner_v2.detectors.textual.elastic_search.Elasticsearch.ping')
    def test_elasticsearch_connect_ping_success(self, mocked_es_ping):
        """Test `ElasticSearchDataStore.connect` when ping succeeds"""
        mocked_es_ping.return_value = True
        connection = ElasticSearchDataStore.connect(**self.elasticsearch_engine_settings)
        self.assertIsInstance(connection, Elasticsearch)

    @mock.patch('ner_v2.detectors.textual.elastic_search.Elasticsearch.ping')
    def test_elasticsearch_connect_ping_fail(self, mocked_es_ping):
        """Test `ElasticSearchDataStore.connect` when ping fails"""
        mocked_es_ping.return_value = False
        connection = ElasticSearchDataStore.connect(**self.elasticsearch_engine_settings)
        self.assertIs(connection, None)

    @mock.patch('ner_v2.detectors.textual.elastic_search.Elasticsearch.ping')
    def test_elasticsearch_get_connection_ping_success(self, mocked_es_ping):
        """Test `ElasticSearchDataStore._get_or_create_new_connection` when ping succeeds"""
        mocked_es_ping.return_value = True
        connection = self.esds._get_or_create_new_connection(alias='test', **self.elasticsearch_engine_settings)
        self.assertIsInstance(connection, Elasticsearch)

    @mock.patch('ner_v2.detectors.textual.elastic_search.Elasticsearch.ping')
    def test_elasticsearch_get_connection_ping_fail(self, mocked_es_ping):
        """Test `ElasticSearchDataStore._get_or_create_new_connection` when ping fails"""
        mocked_es_ping.return_value = False
        with self.assertRaises(EngineConnectionException):
            self.esds._get_or_create_new_connection(alias='test', **self.elasticsearch_engine_settings)

    @mock.patch('ner_v2.detectors.textual.elastic_search.Elasticsearch.ping')
    def test_elasticsearch_add_connection(self, mocked_es_ping):
        """Test `ElasticSearchDataStore._get_or_create_new_connection` with multiple connections"""
        self.assertEqual(len(self.esds._conns), 0)

        mocked_es_ping.return_value = False
        with self.assertRaises(EngineConnectionException):
            self.esds._get_or_create_new_connection(alias='default', **self.elasticsearch_engine_settings)
        self.assertEqual(len(self.esds._conns), 0)

        mocked_es_ping.return_value = True
        self.esds._get_or_create_new_connection(alias='default', **self.elasticsearch_engine_settings)
        self.assertEqual(len(self.esds._conns), 1)

        self.esds._get_or_create_new_connection(alias='new', **self.elasticsearch_engine_settings)
        self.assertEqual(len(self.esds._conns), 2)

        self.esds._get_or_create_new_connection(alias='default', **self.elasticsearch_engine_settings)
        self.esds._get_or_create_new_connection(alias='new', **self.elasticsearch_engine_settings)
        self.assertEqual(len(self.esds._conns), 2)

        self.assertIn('default', self.esds._conns)
        self.assertIn('new', self.esds._conns)

    def test_elasticsearch_get_dynamic_fuzziness_threshold(self):
        fuzzy = 1
        fuzzy_threshold = ElasticSearchDataStore._get_dynamic_fuzziness_threshold(fuzzy)
        self.assertEqual(fuzzy_threshold, fuzzy)

        fuzzy = '1'
        fuzzy_threshold = ElasticSearchDataStore._get_dynamic_fuzziness_threshold(fuzzy)
        self.assertEqual(fuzzy_threshold, 'auto')

        fuzzy = 'some_string'
        fuzzy_threshold = ElasticSearchDataStore._get_dynamic_fuzziness_threshold(fuzzy)
        self.assertEqual(fuzzy_threshold, 'auto')

    def test_add_query(self):
        entity_list_1 = ['city', 'restaurant']
        text_1 = "I want to go to mumbai"

        query_data = self.esds.generate_query_data(entities=entity_list_1, texts=text_1)
        query_data = [json.loads(x) for x in query_data]

        assert_data = [
            {'index': ES_ALIAS, 'type': ES_DOC_TYPE},
            {
                '_source': ['value', 'entity_data'],
                'query': {
                    'bool': {
                        'filter': [
                            {'terms': {'entity_data': ['city', 'restaurant']}},
                            {'terms': {'language_script': ['en']}}
                        ],
                        'should': [{
                            'match': {
                                'variants': {
                                    'query': 'I want to go to mumbai',
                                    'fuzziness': 1,
                                    'prefix_length': 1
                                }
                            }
                        }],
                        'minimum_should_match': 1
                    }
                },
                'highlight': {
                    'fields': {
                        'variants': {'type': 'unified'}
                    },
                    'order': 'score',
                    'number_of_fragments': 20
                },
                'size': ES_SEARCH_SIZE
            }
        ]

        self.assertEqual(query_data, assert_data)
