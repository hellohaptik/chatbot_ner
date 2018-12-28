from __future__ import absolute_import

import os

import pandas as pd
import six
from django.test import TestCase

from ner_constants import FROM_MESSAGE
from ner_v2.detectors.temporal.time.time_detection import TimeDetector


class TimeDetectorTest(TestCase):
    def setUp(self):
        self.csv_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'time_detection_tests.csv')

    @staticmethod
    def _make_expected_output(hh, mm, nn, range=None, time_type=None, drop_na=True):
        # TODO: built-in range is being shadowed here. fix this
        # TODO: This function should be a part of time detection package
        output = {
            'hh': hh,
            'mm': mm,
            'nn': nn,
            'range': range,
            'time_type': time_type
        }
        if drop_na:
            output = {k: output[k] for k in output if output[k] not in ['NA', 'na', None]}
        return output

    def test_time_detection_from_csv(self):
        """
        Run time detection tests defined in the csv
        """
        # columns = ['language', 'text', 'bot_message', 'hh', 'mm', 'nn', 'range', 'time_type', 'original_text']
        dtype = {
            'language': six.text_type,
            'text': six.text_type,
            'bot_message': six.text_type,
            'hh': int,
            'mm': int,
            'range': six.text_type,
            'time_type': six.text_type,
            'original_text': six.text_type
        }
        df = pd.read_csv(self.csv_path, encoding='utf-8', dtype=dtype, keep_default_na=False)

        for language, language_tests_df in df.groupby(by=['language']):
            print('Running tests for language {}'.format(language))
            time_detector = TimeDetector(language=language)
            for index, row in language_tests_df.iterrows():
                if row['bot_message'] != 'NA':
                    time_detector.set_bot_message(bot_message=row['bot_message'])
                    range_enabled = (row['range'] != 'NA')
                    # TODO: handling multiple detections in a single message has not been handled here
                    expected_time = self._make_expected_output(hh=row['hh'],
                                                               mm=row['mm'],
                                                               nn=row['nn'],
                                                               range=row['range'],
                                                               time_type=row['time_type'])
                    expected_output = time_detector.output_entity_dict_list(entity_value_list=[expected_time],
                                                                            original_text_list=[row['original_text']],
                                                                            detection_method_list=[FROM_MESSAGE],
                                                                            detection_language=language)

                    detected_output = time_detector.detect(message=row['text'], range_enabled=range_enabled)
                    self.assertEqual(detected_output, expected_output)
