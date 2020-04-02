from __future__ import absolute_import

import io
import os

import pytz
import six
import yaml
from django.test import TestCase

from ner_v2.detectors.temporal.time.time_detection import TimeDetector


class TimeDetectionTestMeta(type):
    yaml_test_files = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "time_ner_tests.yaml")
    ]

    def __new__(cls, name, bases, attrs):
        for test_name, test_fn in cls.yaml_testsuite_generator():
            attrs[test_name] = test_fn

        return super(TimeDetectionTestMeta, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def yaml_testsuite_generator(cls):
        for filepath in cls.yaml_test_files:
            test_data = yaml.load(io.open(filepath, "r", encoding="utf-8"))
            timezone = pytz.timezone(test_data["args"].get("timezone", "UTC"))
            for language in test_data["tests"]:
                for i, testcase in enumerate(test_data["tests"][language]):
                    yield (
                        "test_yaml_{}".format(testcase["id"]),
                        cls.get_yaml_test(testcase=testcase,
                                          language=language,
                                          timezone=timezone)
                    )

    @classmethod
    def get_yaml_test(cls, testcase, language, timezone, **kwargs):
        def parse_expected_outputs(expected_outputs):
            time_dicts, original_texts = [], []
            for expected_output in expected_outputs:
                time_dict = {
                    "hh": expected_output["hh"],
                    "mm": expected_output["mm"],
                    "nn": expected_output["nn"],
                    'tz': expected_output["tz"],
                    "range": expected_output["range"],
                    "time_type": expected_output["time_type"]
                }
                original_text = expected_output["original_text"].lower().strip() if expected_output[
                    "original_text"] else None
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
                # TODO: This is not correct! actual output should not modified instead expected output should be
                if "range" not in time_dict:
                    time_dict.update({"range": None})
                if "time_type" not in time_dict:
                    time_dict.update({"time_type": None})

            expected_time_dicts, expected_spans = parse_expected_outputs(testcase["outputs"])
            expected_outputs = list(six.moves.zip(expected_time_dicts, expected_spans))

            prefix = failure_string_prefix.format(message=message, language=language)

            self.assertEqual(len(time_dicts), len(spans),
                             prefix + u"Returned times and original_texts have different lengths")
            self.assertEqual(len(spans), len(expected_outputs),
                             prefix + u"Returned times and expected_outputs have different lengths")

            for output in six.moves.zip(time_dicts, spans):

                self.assertIn(output, expected_outputs,
                              prefix + u"{got} not in {expected_outputs}".format(got=output,
                                                                                 expected_outputs=expected_outputs))

        return run_test


class TimeDetectionTest(six.with_metaclass(TimeDetectionTestMeta, TestCase)):
    pass
