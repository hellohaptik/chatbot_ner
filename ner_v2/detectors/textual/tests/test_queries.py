from __future__ import absolute_import

import json
import os
from django.test import TestCase

from ner_v2.detectors.textual.queries import _parse_multi_entity_es_results, \
    _generate_multi_entity_es_query
from chatbot_ner.config import ES_SEARCH_SIZE


es_tests_directory = os.path.dirname(os.path.abspath(__file__))


class TestESDataStoreQueries(TestCase):

    def test_parse_multi_entity_es_results(self):
        # get input data from file `query_parse_input_data.json`

        input_test_file = os.path.join(es_tests_directory, 'query_parse_input_data.json')
        output_test_file = os.path.join(es_tests_directory, 'query_parse_output_data.json')

        with open(input_test_file, 'r') as f:
            input_data = json.load(f)

        result = _parse_multi_entity_es_results(input_data)

        # get output data from file `query_parse_output_data.json`
        with open(output_test_file, 'r') as f:
            output_data = json.load(f)

        # set max diff to None
        self.maxDiff = None

        self.assertDictEqual(result[1], output_data[1])

    def test_generate_multi_entity_es_query_list(self):

        entity_list = ['city', 'restaurant']
        text = "I want to go to mumbai"
        output_test_file = os.path.join(es_tests_directory,
                                        'query_generate_output_entity_list_data.json')

        result = _generate_multi_entity_es_query(entity_list, text)

        with open(output_test_file, "r") as f:
            output_data = json.load(f)
            output_data['size'] = ES_SEARCH_SIZE

        # set max diff to None
        self.maxDiff = None

        self.assertDictEqual(result, output_data)

    def test_generate_multi_entity_es_query_string(self):

        entity_string = "city"
        text = "I want to go to mumbai"
        output_test_file = os.path.join(es_tests_directory,
                                        'query_generate_output_entity_string_data.json')

        result = _generate_multi_entity_es_query(entity_string, text)

        with open(output_test_file, "r") as f:
            output_data = json.load(f)
            output_data['size'] = ES_SEARCH_SIZE

        # set max diff to None
        self.maxDiff = None

        self.assertDictEqual(result, output_data)
