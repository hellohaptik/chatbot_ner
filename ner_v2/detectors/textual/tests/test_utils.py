from __future__ import absolute_import

import json
import os

from collections import OrderedDict
from mock import patch

from django.test import TestCase
from django.http import HttpRequest

from ner_v2.detectors.textual.utils import get_text_entity_detection_data, validate_text_request, \
    get_output_for_fallback_entities, get_detection, InvalidTextRequest

tests_directory = os.path.dirname(os.path.abspath(__file__))


class TestTextualUtils(TestCase):

    def test_get_output_for_fallback_entities(self):
        input_data = {'city': {'fallback_value': 'Mumbai', 'ignore_message': True},
                      'restaurant': {'fallback_value': None, 'ignore_message': True}}

        assert_output_data = {'city': [{'entity_value': {'value': 'Mumbai',
                                                         'datastore_verified': False,
                                                         'model_verified': False},
                                        'detection': 'fallback_value',
                                        'original_text': 'Mumbai', 'language': 'en'}],
                              'restaurant': []}

        result = get_output_for_fallback_entities(input_data)

        self.assertDictEqual(result, assert_output_data)

    def test_validate_text_request_ok(self):
        request = HttpRequest()

        # test if everything is ok
        request._body = b'{"messages":["something"], "entities":{"something":""}}'
        validate_text_request(request)

    def test_validate_text_request_exceptions(self):
        request = HttpRequest()

        # test if no message
        request._body = b'{}'
        self.assertRaises(InvalidTextRequest, validate_text_request, request=request)

        # test if no entities
        request._body = b'{"messages": "something"}'
        self.assertRaises(InvalidTextRequest, validate_text_request, request=request)

        # test if message not in proper format
        request._body = b'{"messages":"something", "entities":"something"}'
        self.assertRaises(InvalidTextRequest, validate_text_request, request=request)

        # test if entities not in proper format
        request._body = b'{"messages":["something"], "entities":"something"}'
        self.assertRaises(InvalidTextRequest, validate_text_request, request=request)

    @patch('ner_v2.detectors.textual.utils.get_detection')
    def test_get_text_entity_detection_data(self, mock_get_detection):
        input_data = {
            "messages": ["I want to go to Mumbai"],
            "bot_message": None,
            "language_script": "en",
            "source_language": "en",
            "entities": {
                "city": {
                    "structured_value": None,
                    "fallback_value": None,
                    "predetected_values": None,
                    "fuzziness": 4,
                    "min_token_len_fuzziness": 4,
                    "ignore_message": None
                },

                "restaurant": {
                    "structured_value": None,
                    "fallback_value": None,
                    "predetected_values": None,
                    "fuzziness": None,
                    "min_token_len_fuzziness": None,
                    "ignore_message": True
                },
            }

        }

        request = HttpRequest()

        request._body = json.dumps(input_data)

        mock_get_detection.return_value = [{'entities': {'city': [
            {'entity_value': {'value': 'Mumbai', 'datastore_verified': True,
                              'model_verified': False},
             'detection': 'message', 'original_text': 'mumbai',
             'language': 'en'}], 'restaurant': []},
            'language': 'en'}]

        output = get_text_entity_detection_data(request)

        assert_output = [{
            'entities': {'entities': {'city': [
                {'entity_value': {'value': 'Mumbai',
                                  'datastore_verified': True,
                                  'model_verified': False},
                 'detection': 'message', 'original_text': 'mumbai',
                 'language': 'en'}], 'restaurant': []},
                'language': 'en', 'restaurant': []}, 'language': 'en'}]

        self.assertListEqual(output, assert_output)

    @patch('ner_v2.detectors.textual.utils.get_detection')
    def test_get_text_entity_detection_data_structured(self, mock_get_detection):
        input_data = {
            "messages": ["I want to go to Mumbai"],
            "bot_message": None,
            "language_script": "en",
            "source_language": "en",
            "entities": {
                "city": {
                    "structured_value": None,
                    "fallback_value": None,
                    "predetected_values": None,
                    "fuzziness": 4,
                    "min_token_len_fuzziness": 4,
                    "ignore_message": None
                },

                "restaurant": {
                    "structured_value": None,
                    "fallback_value": None,
                    "predetected_values": None,
                    "fuzziness": None,
                    "min_token_len_fuzziness": None,
                    "ignore_message": True
                },
            }

        }

        request = HttpRequest()

        request._body = json.dumps(input_data)

        mock_get_detection.return_value = [{'city': [
            {'entity_value': {'value': 'New Delhi', 'datastore_verified': True, 'model_verified': False},
             'detection': 'structure_value_verified', 'original_text': 'delhi', 'language': 'en'}]}]

        output = get_text_entity_detection_data(request)

        assert_output = [{'entities': {'city': [
            {'entity_value': {'value': 'New Delhi', 'datastore_verified': True, 'model_verified': False},
             'detection': 'structure_value_verified', 'original_text': 'delhi', 'language': 'en'}], 'restaurant': []},
            'language': 'en'}]

        self.assertListEqual(output, assert_output)

    @patch('ner_v2.detectors.textual.elastic_search.'
           'ElasticSearchDataStore.get_multi_entity_results')
    def test_get_text_detection_string_message(self, mock_es_query):
        entity_dict = {'city': {'structured_value': None,
                                'fallback_value': None,
                                'predetected_values': None,
                                'fuzziness': "4,7",
                                'min_token_len_fuzziness': 4,
                                'ignore_message': None}}

        message = "I want to go to Mumbai"

        mock_es_query.return_value = [
            {'city': OrderedDict([('Wani', 'Wani'),
                                  ('mumbai', 'mumbai'),
                                  ('Mumbai', 'Mumbai'),
                                  ('goa', 'goa')])
             }]

        output = get_detection(message, entity_dict)
        assert_output = [
            {'city': [{'entity_value': {'value': 'Mumbai', 'datastore_verified': True,
                                        'model_verified': False}, 'detection': 'message',
                       'original_text': 'mumbai',
                       'language': 'en'}]}]

        self.assertDictEqual(assert_output[0], output[0])

    @patch('ner_v2.detectors.textual.elastic_search.'
           'ElasticSearchDataStore.get_multi_entity_results')
    def test_get_text_detection_list_message(self, mock_es_query):
        entity_dict = {'city': {'structured_value': None,
                                'fallback_value': None,
                                'predetected_values': None,
                                'fuzziness': "4,7",
                                'min_token_len_fuzziness': 4,
                                'ignore_message': None}}

        message = ["I want to go to Mumbai", "I want to go to Delhi"]

        mock_es_query.return_value = [
            {'city': OrderedDict([('Wani', 'Wani'),
                                  ('mumbai', 'mumbai'),
                                  ('Mumbai', 'Mumbai'), (
                                      'goa', 'goa')])},
            {'city': OrderedDict([('Delhi', 'New Delhi'),
                                  ('Wani', 'Wani'),
                                  ('goa', 'goa')])}]

        output = get_detection(message, entity_dict)
        assert_output = [{'city': [
            {'entity_value': {'value': 'Mumbai',
                              'datastore_verified': True,
                              'model_verified': False},
             'detection': 'message',
             'original_text': 'mumbai',
             'language': 'en'}]},
            {'city': [
                {'entity_value': {'value': 'New Delhi',
                                  'datastore_verified': True,
                                  'model_verified': False},
                 'detection': 'message',
                 'original_text': 'delhi',
                 'language': 'en'}]}]

        self.assertListEqual(assert_output, output)
