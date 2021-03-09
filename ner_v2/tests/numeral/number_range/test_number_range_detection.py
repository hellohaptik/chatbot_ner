from __future__ import absolute_import
import io
import os
import six
import yaml
from django.test import TestCase

from ner_v2.detectors.numeral.number_range.number_range_detection import NumberRangeDetector


class NumberRangeDetectorTestMeta(type):
    yaml_test_files = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "number_range_ner_tests.yaml")
    ]

    def __new__(cls, name, bases, attrs):
        for test_name, test_fn in cls.yaml_testsuite_generator():
            if test_name in attrs:
                raise ValueError('Got duplicate test name {test_name}, please make sure all tests have unique "id"'
                                 .format(test_name=test_name))
            attrs[test_name] = test_fn

        return super(NumberRangeDetectorTestMeta, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def yaml_testsuite_generator(cls):
        for filepath in cls.yaml_test_files:
            test_data = yaml.load(io.open(filepath, "r", encoding="utf-8"), Loader=yaml.SafeLoader)
            for language in test_data["tests"]:
                for i, testcase in enumerate(test_data["tests"][language]):
                    yield (
                        "test_yaml_{}".format(testcase["id"]),
                        cls.get_yaml_test(testcase=testcase,
                                          language=language,)
                    )

    @classmethod
    def get_yaml_test(cls, testcase, language, **kwargs):
        def parse_expected_outputs(expected_outputs):
            num_range_dicts, original_texts = [], []
            for expected_output in expected_outputs:
                num_range_dict = {
                    "min_value": str(expected_output["min_value"]) if expected_output["min_value"] else None,
                    "unit": str(expected_output["unit"]) if expected_output["unit"] else None,
                    "max_value": str(expected_output["max_value"]) if expected_output["max_value"] else None,
                    "abs_value": str(expected_output["abs_value"]) if expected_output["abs_value"] else None
                }
                original_text = \
                    expected_output["original_text"].lower().strip() if expected_output["original_text"] else None
                if original_text:
                    num_range_dicts.append(num_range_dict)
                    original_texts.append(original_text)
            return num_range_dicts, original_texts

        failure_string_prefix = u"Test failed for\nText = {message}\nLanguage = {language}\n"

        def run_test(self):
            message = testcase["message"]
            unit_type = testcase.get("unit_type")
            range_detector = NumberRangeDetector(entity_name='number_range', language=language,
                                                 unit_type=unit_type)

            range_dicts, spans = range_detector.detect_entity(message)
            expected_range_dicts, expected_spans = parse_expected_outputs(testcase["outputs"])
            expected_outputs = list(six.moves.zip(expected_range_dicts, expected_spans))

            prefix = failure_string_prefix.format(message=message, language=language)

            self.assertEqual(len(range_dicts), len(spans),
                             prefix + u"Returned number ranges and original_texts have different lengths")
            self.assertEqual(len(spans), len(expected_outputs),
                             prefix + u"Returned number ranges and expected_outputs have different lengths")

            for output in six.moves.zip(range_dicts, spans):

                self.assertIn(output, expected_outputs,
                              prefix + u"{got} not in {expected_outputs}".format(got=output,
                                                                                 expected_outputs=expected_outputs))

        return run_test


class NumberRangeDetectorTest(six.with_metaclass(NumberRangeDetectorTestMeta, TestCase)):
    pass
