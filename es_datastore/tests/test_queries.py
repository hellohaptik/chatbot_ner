from __future__ import absolute_import

import json
from django.test import TestCase

from es_datastore.queries import _parse_multi_entity_es_results, \
    _generate_multi_entity_es_query


class TestESDataStoreQueries(TestCase):

    def test_parse_multi_entity_es_results(self):
        # get input data from file `query_parse_input_data.json`
        with open('query_parse_input_data.json', 'r') as f:
            input_data = json.load(f)

        result = _parse_multi_entity_es_results(input_data)

        # get output data from file `query_parse_output_data.json`
        with open('query_parse_output_data.json', 'r') as f:
            output_data = json.load(f)

        # set max diff to None
        self.maxDiff = None

        self.assertDictEqual(result, output_data)

    def test_generate_multi_entity_es_query_list(self):

        entity_list = ['city', 'restaurant']
        text = "I want to go to mumbai"

        result = _generate_multi_entity_es_query(entity_list, text)

        with open("query_generate_output_entity_list_data.json", "r") as f:
            output_data = json.load(f)

        # set max diff to None
        self.maxDiff = None

        self.assertDictEqual(result, output_data)

    def test_generate_multi_entity_es_query_string(self):

        entity_string = "city"
        text = "I want to go to mumbai"

        result = _generate_multi_entity_es_query(entity_string, text)

        with open("query_generate_output_entity_string_data.json.json", "r") as f:
            output_data = json.load(f)

        # set max diff to None
        self.maxDiff = None

        self.assertDictEqual(result, output_data)
