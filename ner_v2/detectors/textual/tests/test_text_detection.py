from __future__ import absolute_import

import os

from collections import OrderedDict
from mock import patch

from django.test import TestCase

from ner_v2.detectors.textual.text_detection import TextDetector

tests_directory = os.path.dirname(os.path.abspath(__file__))


class TestTextualUtils(TestCase):

    def test_text_detector_intialization(self):
        entity_dict = {'city': {'structured_value': None,
                                'fallback_value': None,
                                'predetected_values': None,
                                'fuzziness': 4,
                                'min_token_len_fuzziness': 4,
                                'use_fallback': None},
                       'restaurant': {'structured_value': None,
                                      'fallback_value': None,
                                      'predetected_values': None,
                                      'fuzziness': 4,
                                      'min_token_len_fuzziness': 4,
                                      'use_fallback': None}
                       }

        language = 'en'
        target_language_script = 'en'

        text_detector = TextDetector(entity_dict=entity_dict, source_language_script=language,
                                     target_language_script=target_language_script)

        self.assertIsInstance(text_detector, TextDetector)

        self.assertEqual(language, text_detector._source_language_script)
        self.assertEqual(target_language_script, text_detector._target_language_script)

        self.assertDictEqual(entity_dict, text_detector.entities_dict)

    @patch('ner_v2.detectors.textual.elastic_search.'
           'ElasticSearchDataStore.get_multi_entity_results')
    def test_text_detection_detect_single_message(self, mock_es_query):
        entity_dict = {'city': {'structured_value': None,
                                'fallback_value': None,
                                'predetected_values': None,
                                'fuzziness': 4,
                                'min_token_len_fuzziness': 4,
                                'use_fallback': None},
                       'restaurant': {'structured_value': None,
                                      'fallback_value': None,
                                      'predetected_values': None,
                                      'fuzziness': 4,
                                      'min_token_len_fuzziness': 4,
                                      'use_fallback': None}
                       }

        language = 'en'
        target_language_script = 'en'

        message = "I want to go to Mumbai to order Dominoes"

        mock_es_query.return_value = [{
            'restaurant': OrderedDict([('Domino', "Domino's Pizza"),
                                       ('Dominos', "Domino's Pizza"), ('TMOS', 'TMOS'),
                                       ('G.', 'G  Pulla Reddy Sweets')]),
            'city': OrderedDict([('Wani', 'Wani'), ('mumbai', 'mumbai'),
                                 ('Mumbai', 'Mumbai'), ('goa', 'goa')])}]

        text_detector = TextDetector(entity_dict=entity_dict, source_language_script=language,
                                     target_language_script=target_language_script)

        result = text_detector.detect(message=message)

        assert_output = [{'city': [{
            'entity_value': {'value': 'Mumbai',
                             'datastore_verified': True, 'model_verified': False},
            'detection': 'message', 'original_text': 'mumbai', 'language': 'en'}],
            'restaurant': [
                {'entity_value': {'value': "Domino's Pizza", 'datastore_verified': True, 'model_verified': False},
                 'detection': 'message', 'original_text': 'dominoes', 'language': 'en'}]}]

        self.maxDiff = None
        self.assertListEqual(result, assert_output)

    @patch('ner_v2.detectors.textual.elastic_search.'
           'ElasticSearchDataStore.get_multi_entity_results')
    def test_text_detection_detect_bulk_message(self, mock_es_query):
        entity_dict = {'city': {'structured_value': None,
                                'fallback_value': None,
                                'predetected_values': None,
                                'fuzziness': 4,
                                'min_token_len_fuzziness': 4,
                                'use_fallback': None},
                       'restaurant': {'structured_value': None,
                                      'fallback_value': None,
                                      'predetected_values': None,
                                      'fuzziness': 4,
                                      'min_token_len_fuzziness': 4,
                                      'use_fallback': None}
                       }

        language = 'en'
        target_language_script = 'en'

        message = ['I want to go to Mumbai to order Dominoes',
                   'I want to go to Delhi']

        mock_es_query.return_value = [{
            'restaurant': OrderedDict([('Domino', "Domino's Pizza"),
                                       ('Dominos', "Domino's Pizza"),
                                       ('TMOS', 'TMOS'), ('G.', 'G  Pulla Reddy Sweets')]),
            'city': OrderedDict([('Wani', 'Wani'), ('mumbai', 'mumbai'),
                                 ('Mumbai', 'Mumbai'), ('goa', 'goa')])},
            {'restaurant': OrderedDict([('TMOS', 'TMOS'),
                                        ('Deli', 'Deli'),
                                        ('G.', 'G  Pulla Reddy Sweets')]),
             'city': OrderedDict([('Delhi', 'New Delhi'), ('Wani', 'Wani'),
                                  ('goa', 'goa')])}]

        text_detector = TextDetector(entity_dict=entity_dict, source_language_script=language,
                                     target_language_script=target_language_script)

        result = text_detector.detect_bulk(messages=message)

        assert_output = [{
            'city': [{'entity_value': {'value': 'Mumbai', 'datastore_verified': True, 'model_verified': False},
                      'detection': 'message', 'original_text': 'mumbai', 'language': 'en'}],
            'restaurant': [{'entity_value': {'value': "Domino's Pizza", 'datastore_verified': True,
                                             'model_verified': False},
                            'detection': 'message', 'original_text': 'dominoes', 'language': 'en'}]},
            {'city': [{'entity_value': {'value': 'New Delhi', 'datastore_verified': True,
                                        'model_verified': False},
                       'detection': 'message', 'original_text': 'delhi', 'language': 'en'}], 'restaurant': []}]

        self.maxDiff = None
        self.assertListEqual(result, assert_output)
