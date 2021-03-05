from __future__ import absolute_import
import io
import os
import six
import yaml
from django.test import TestCase

from ner_v2.detectors.pattern.phone_number.phone_number_detection import PhoneDetector


class PhoneNumberDetectorTestMeta(type):
    yaml_test_files = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone_number_ner_tests.yaml")
    ]

    def __new__(cls, name, bases, attrs):
        for test_name, test_fn in cls.yaml_testsuite_generator():
            if test_name in attrs:
                raise ValueError('Got duplicate test name {test_name}, please make sure all tests have unique "id"'
                                 .format(test_name=test_name))
            attrs[test_name] = test_fn

        return super(PhoneNumberDetectorTestMeta, cls).__new__(cls, name, bases, attrs)

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
            phone_num_list, original_texts = [], []
            for expected_output in expected_outputs:
                original_text = \
                    expected_output["original_text"].lower().strip() if expected_output["original_text"] else None
                if original_text:
                    phone_num_dict = {
                        'value': str(expected_output["value"]),
                        'country_calling_code': str(expected_output["country_calling_code"])
                    }
                    phone_num_list.append(phone_num_dict)
                    original_texts.append(original_text)
            return phone_num_list, original_texts

        failure_string_prefix = u"Test failed for\nText = {message}\nLanguage = {language}\n"

        def run_test(self):
            message = testcase["message"]
            locale = testcase["locale"]
            number_detector_object = PhoneDetector(entity_name='phone_number', language=language, locale=locale)
            phone_number_list, spans = number_detector_object.detect_entity(message)

            expected_phone_number_list, expected_spans = parse_expected_outputs(testcase["outputs"])

            expected_outputs = list(six.moves.zip(expected_phone_number_list, expected_spans))

            prefix = failure_string_prefix.format(message=message, language=language)

            self.assertEqual(len(phone_number_list), len(spans),
                             prefix + u"Returned phone numbers and original_texts have different lengths")
            self.assertEqual(len(spans), len(expected_outputs),
                             prefix + u"Returned phone numbers and expected_outputs have different lengths")

            for output in six.moves.zip(phone_number_list, spans):

                self.assertIn(output, expected_outputs,
                              prefix + u"{got} not in {expected_outputs}".format(got=output,
                                                                                 expected_outputs=expected_outputs))

        return run_test


class PhoneNumberDetectorTest(six.with_metaclass(PhoneNumberDetectorTestMeta, TestCase)):
    pass
