from __future__ import absolute_import

from django.test import TestCase
import pandas as pd
import os

from ner_v2.detectors.numeral.number_range.number_range_detection import NumberRangeDetector
from chatbot_ner.config import ner_logger


def get_value_list(val):
    val = val.lower().strip()
    val_list = []
    for v in val.split('|'):
        if v == 'na':
            val_list.append(None)
        else:
            val_list.append(v.strip())
    return val_list


class NumberRangeDetectorTest(TestCase):
    def setUp(self):
        self.csv_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'number_range_detection_test.csv')

    def _make_expected_output(self, min_values, max_values, units, original_texts):
        entity_values_list = []
        original_texts_list = []

        if original_texts == 'NA':
            return entity_values_list, original_texts_list

        min_values = get_value_list(min_values)
        max_values = get_value_list(max_values)
        units = get_value_list(units)
        original_texts = get_value_list(original_texts)

        for min_value, max_value, unit, original_text in zip(min_values, max_values, units, original_texts):
            entity_values_list.append({'min_value': min_value, 'max_value': max_value, 'unit': unit})
            original_texts_list.append(original_text)

        return entity_values_list, original_texts_list

    def test_number_range_detection_from_csv(self):
        df = pd.read_csv(self.csv_path, encoding='utf-8', keep_default_na=False)

        for language, language_tests_df in df.groupby(by=['language']):
            ner_logger.debug('Running tests for language {}'.format(language))
            for index, row in language_tests_df.iterrows():
                message = row['message']
                unit_type = None if row['unit_type'] == 'NA' else row['unit_type']
                number_range_detector = NumberRangeDetector(entity_name='number_range', language=language,
                                                            unit_type=unit_type)
                expected_entity_values_list, expected_original_texts_list = \
                    self._make_expected_output(row['min_value'], row['max_value'], row['unit'], row['original_text'])

                expected_zipped = list(zip(expected_entity_values_list, expected_original_texts_list))

                detected_entities_values_list, detected_original_texts_list = \
                    number_range_detector.detect_entity(message)

                for detected_number_range in zip(detected_entities_values_list, detected_original_texts_list):
                    self.assertIn(detected_number_range, expected_zipped)
