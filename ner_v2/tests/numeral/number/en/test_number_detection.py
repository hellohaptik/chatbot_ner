from __future__ import absolute_import
import io
import os
import six
import yaml
from django.test import TestCase

from ner_v2.detectors.numeral.number.number_detection import NumberDetector


class NumberDetectorTestsMeta(type):
    yaml_test_files = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "number_ner_tests.yaml")
    ]

    def __new__(cls, name, bases, attrs):
        for test_name, test_fn in cls.yaml_testsuite_generator():
            attrs[test_name] = test_fn

        return super(NumberDetectorTestsMeta, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def yaml_testsuite_generator(cls):
        for filepath in cls.yaml_test_files:
            test_data = yaml.load(io.open(filepath, "r", encoding="utf-8"))
            for language in test_data["tests"]:
                for i, testcase in enumerate(test_data["tests"][language]):
                    yield (
                        "test_yaml_{}".format(testcase["_id_"]),
                        cls.get_yaml_test(testcase=testcase,
                                          language=language,)
                    )

    @classmethod
    def get_yaml_test(cls, testcase, language, **kwargs):
        def parse_expected_outputs(expected_outputs):
            num_dicts, original_texts = [], []
            for expected_output in expected_outputs:
                if "detected_number" in expected_output:
                    num_dict = {
                        "detected_number": expected_output["detected_number"]
                    }

                else:
                    num_dict = {
                        "value": expected_output["value"],
                        "unit": expected_output["unit"],
                    }
                original_text = \
                    expected_output["original_text"].lower().strip() if expected_output["original_text"] else None
                if original_text:
                    num_dicts.append(num_dict)
                    original_texts.append(original_text)
            return num_dicts, original_texts

        failure_string_prefix = u"Test failed for\nText = {message}\nLanguage = {language}\n"

        def run_test(self):
            message = testcase["message"]
            unit_type = testcase.get("unit_type", None)
            number_detector_object = NumberDetector(entity_name="number", language=language, unit_type=unit_type)
            number_dicts, spans = number_detector_object.detect_entity(message)

            expected_number_dicts, expected_spans = parse_expected_outputs(testcase["outputs"])
            expected_outputs = list(six.moves.zip(expected_number_dicts, expected_spans))

            prefix = failure_string_prefix.format(message=message, language=language)

            self.assertEqual(len(number_dicts), len(spans),
                             prefix + u"Returned dates and original_texts have different lengths")
            self.assertEqual(len(spans), len(expected_outputs),
                             prefix + u"Returned dates and expected_outputs have different lengths")

            for output in six.moves.zip(number_dicts, spans):

                self.assertIn(output, expected_outputs,
                              prefix + u"{got} not in {expected_outputs}".format(got=output,
                                                                                 expected_outputs=expected_outputs))

        return run_test


class NumberDetectorTests(six.with_metaclass(NumberDetectorTestsMeta, TestCase)):
    pass
