from __future__ import absolute_import

import datetime
import io
import os

import pytz
import six
import yaml
from django.test import TestCase

from ner_v2.detectors.temporal.date.date_detection import DateDetector


class DateDetectionTestsMeta(type):
    yaml_test_files = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "testcases.yaml")
    ]

    def __new__(cls, name, bases, attrs):
        for test_name, test_fn in cls.yaml_testsuite_generator():
            attrs[test_name] = test_fn

        return super(DateDetectionTestsMeta, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def yaml_testsuite_generator(cls):
        for filepath in cls.yaml_test_files:
            test_data = yaml.load(io.open(filepath, "r", encoding="utf-8"))
            reference_date = test_data["args"]["today"]
            timezone = pytz.timezone(reference_date.get("timezone", "UTC"))
            now_date = timezone.localize(datetime.datetime(year=int(reference_date["yy"]),
                                                           month=int(reference_date["mm"]),
                                                           day=int(reference_date["dd"])))
            for language in test_data["tests"]:
                for i, testcase in enumerate(test_data["tests"][language]):
                    yield (
                        "test_yaml_{}_{}".format(language, i),
                        cls.get_yaml_test(testcase=testcase,
                                          language=language,
                                          timezone=timezone,
                                          now_date=now_date)
                    )

    @classmethod
    def get_yaml_test(cls, testcase, language, timezone, now_date, **kwargs):
        def parse_expected_outputs(expected_outputs):
            date_dicts, original_texts = [], []
            for expected_output in expected_outputs:
                date_dict = {
                    "value": {
                        "dd": expected_output["dd"],
                        "mm": expected_output["mm"],
                        "yy": expected_output["yy"],
                    },
                    "range": expected_output["range"],
                    "repeat": expected_output["repeat"],
                    "property": expected_output["property"]
                }
                original_text = expected_output["original_text"].lower()
                date_dicts.append(date_dict)
                original_texts.append(original_text)
            return date_dicts, original_texts

        failure_string_prefix = u"Test failed for\nText = {message}\nLanguage = {language}\n"

        def run_test(self):
            message = testcase["message"]
            bot_message = testcase.get("bot_message")
            date_detector = DateDetector(entity_name='date', language=language, timezone=timezone)

            if bot_message:
                date_detector.set_bot_message(bot_message=bot_message)

            date_detector.set_now_datetime(now_datetime=now_date)
            date_dicts, spans = date_detector.detect_entity(text=message, **kwargs)

            for date_dict in date_dicts:
                if "type" in date_dict["value"]:
                    date_dict["value"].pop("type")

            expected_date_dicts, expected_spans = parse_expected_outputs(testcase["outputs"])
            expected_outputs = list(six.moves.zip(expected_date_dicts, expected_spans))

            prefix = failure_string_prefix.format(message=message, language=language)

            self.assertEqual(len(date_dicts), len(spans),
                             prefix + u"Returned dates and original_texts have different lengths")
            self.assertEqual(len(spans), len(expected_outputs),
                             prefix + u"Returned dates and expected_outputs have different lengths")

            for output in six.moves.zip(date_dicts, spans):

                self.assertIn(output, expected_outputs,
                              prefix + u"{got} not in {expected_outputs}".format(got=output,
                                                                                 expected_outputs=expected_outputs))

        return run_test


class DateDetectionTests(six.with_metaclass(DateDetectionTestsMeta, TestCase)):
    pass
