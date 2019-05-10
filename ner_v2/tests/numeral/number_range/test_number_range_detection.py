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


from __future__ import absolute_import

import io
import os

import pytz
import six
import yaml
from django.test import TestCase

from ner_v2.detectors.numeral.number_range.number_range_detection import NumberRangeDetector


class TimeDetectionTestsMeta(type):
    yaml_test_files = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "number_range_ner_tests.yaml")
    ]

    def __new__(cls, name, bases, attrs):
        for test_name, test_fn in cls.yaml_testsuite_generator():
            attrs[test_name] = test_fn

        return super(TimeDetectionTestsMeta, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def yaml_testsuite_generator(cls):
        for filepath in cls.yaml_test_files:
            test_data = yaml.load(io.open(filepath, "r", encoding="utf-8"))
            for language in test_data["tests"]:
                for i, testcase in enumerate(test_data["tests"][language]):
                    yield (
                        "test_yaml_{}_{}".format(language, i),
                        cls.get_yaml_test(testcase=testcase,
                                          language=language,)
                    )

    @classmethod
    def get_yaml_test(cls, testcase, language, timezone, **kwargs):
        def parse_expected_outputs(expected_outputs):
            time_dicts, original_texts = [], []
            for expected_output in expected_outputs:
                time_dict = {
                        "unit_type": expected_output["hh"],
                        "max_value": expected_output["mm"],
                        "unit": expected_output["nn"],
                        "max_value": expected_output["range"],
                        "time_type": expected_output["time_type"]
                }
                original_text = expected_output["original_text"].lower() if expected_output["original_text"] else None
                if original_text:
                    time_dicts.append(time_dict)
                    original_texts.append(original_text)
            return time_dicts, original_texts

        failure_string_prefix = u"Test failed for\nText = {message}\nLanguage = {language}\n"

        def run_test(self):
            message = testcase["message"]
            range_enabled = testcase.get("range_enabled")
            time_detector = TimeDetector(entity_name='time', language=language, timezone=timezone)

            time_dicts, spans = time_detector.detect_entity(text=message, range_enabled=range_enabled, **kwargs)

            for time_dict in time_dicts:
                if "range" not in time_dict:
                    time_dict.update({"range": None})
                if "time_type" not in time_dict:
                    time_dict.update({"time_type": None})

            expected_date_dicts, expected_spans = parse_expected_outputs(testcase["outputs"])
            expected_outputs = list(six.moves.zip(expected_date_dicts, expected_spans))

            prefix = failure_string_prefix.format(message=message, language=language)

            self.assertEqual(len(time_dicts), len(spans),
                             prefix + u"Returned dates and original_texts have different lengths")
            self.assertEqual(len(spans), len(expected_outputs),
                             prefix + u"Returned dates and expected_outputs have different lengths")

            for output in six.moves.zip(time_dicts, spans):

                self.assertIn(output, expected_outputs,
                              prefix + u"{got} not in {expected_outputs}".format(got=output,
                                                                                 expected_outputs=expected_outputs))

        return run_test


class TimeDetectionTests(six.with_metaclass(TimeDetectionTestsMeta, TestCase)):
    pass
