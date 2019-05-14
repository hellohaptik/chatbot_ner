from __future__ import absolute_import

import io
import os

import pytz
import six
import yaml
from django.test import TestCase

from ner_v2.detectors.temporal.time.time_detection import TimeDetector
from ner_v2.detectors.numeral.number.standard_number_detector import NumberVariant
from ner_v2.detectors.numeral.utils import get_number_from_number_word


class TestNumberFromWords(TestCase):
    def setUp(self):
        self.entity_name = 'number'
        self.number_words_map = {
            u'c': NumberVariant(scale=10000000, increment=0),
            u'cr': NumberVariant(scale=10000000, increment=0),
            u'crore': NumberVariant(scale=10000000, increment=0),
            u'crores': NumberVariant(scale=10000000, increment=0),
            u'eight': NumberVariant(scale=1, increment=8),
            u'eighteen': NumberVariant(scale=1, increment=18),
            u'eighty': NumberVariant(scale=1, increment=80),
            u'eleven': NumberVariant(scale=1, increment=11),
            u'fifteen': NumberVariant(scale=1, increment=15),
            u'fifty': NumberVariant(scale=1, increment=50),
            u'five': NumberVariant(scale=1, increment=5),
            u'forty': NumberVariant(scale=1, increment=40),
            u'four': NumberVariant(scale=1, increment=4),
            u'fourteen': NumberVariant(scale=1, increment=14),
            u'fourty': NumberVariant(scale=1, increment=40),
            u'hundred': NumberVariant(scale=100, increment=0),
            u'k': NumberVariant(scale=1000, increment=0),
            u'l': NumberVariant(scale=100000, increment=0),
            u'lac': NumberVariant(scale=100000, increment=0),
            u'lacs': NumberVariant(scale=100000, increment=0),
            u'lakh': NumberVariant(scale=100000, increment=0),
            u'lakhs': NumberVariant(scale=100000, increment=0),
            u'm': NumberVariant(scale=1000000, increment=0),
            u'mil': NumberVariant(scale=1000000, increment=0),
            u'million': NumberVariant(scale=1000000, increment=0),
            u'nine': NumberVariant(scale=1, increment=9),
            u'nineteen': NumberVariant(scale=1, increment=19),
            u'ninety': NumberVariant(scale=1, increment=90),
            u'ninty': NumberVariant(scale=1, increment=90),
            u'one': NumberVariant(scale=1, increment=1),
            u'seven': NumberVariant(scale=1, increment=7),
            u'seventeen': NumberVariant(scale=1, increment=17),
            u'seventy': NumberVariant(scale=1, increment=70),
            u'six': NumberVariant(scale=1, increment=6),
            u'sixteen': NumberVariant(scale=1, increment=16),
            u'sixty': NumberVariant(scale=1, increment=60),
            u'ten': NumberVariant(scale=1, increment=10),
            u'thirteen': NumberVariant(scale=1, increment=13),
            u'thirty': NumberVariant(scale=1, increment=30),
            u'thousand': NumberVariant(scale=1000, increment=0),
            u'thousands': NumberVariant(scale=1000, increment=0),
            u'three': NumberVariant(scale=1, increment=3),
            u'tweleve': NumberVariant(scale=1, increment=12),
            u'twelve': NumberVariant(scale=1, increment=12),
            u'twenty': NumberVariant(scale=1, increment=20),
            u'two': NumberVariant(scale=1, increment=2),
            u'zero': NumberVariant(scale=1, increment=0)
        }

    def test_get_number_with_only_unit_in_number_word(self):
        """
        Number detection from word with only unit ex - 'one', 'two', 'twenty'
        """
        message = 'I want to book for one passenger'
        detect_texts, original_texts = get_number_from_number_word(message, self.number_words_map)
        zipped = zip(detect_texts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn((1, 'one'), zipped)

    def test_get_number_with_only_scale_in_number_word(self):
        """
        Number detection from word with only scale like - 'hundred', 'thousand'
        """
        message = 'need hundred change'
        detect_texts, original_texts = get_number_from_number_word(message, self.number_words_map)
        zipped = zip(detect_texts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn((100, 'hundred'), zipped)

    def test_get_number_with_scale_and_unit_in_number_word(self):
        """
        Number detection from word with scale and unit like - 'one hundred', 'one thousand two hundred five'
        """
        message = 'haptik get one thousand two hundred five messages daily'
        detect_texts, original_texts = get_number_from_number_word(message, self.number_words_map)
        zipped = zip(detect_texts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn((1205, 'one thousand two hundred five'), zipped)

    def test_get_number_with_multiple_unit_number_word(self):
        """
        Number detection from word with multiple unit numbers like 'one two three twenty one'
        """
        message = 'one two three'
        detect_texts, original_texts = get_number_from_number_word(message, self.number_words_map)
        zipped = zip(detect_texts, original_texts)
        self.assertEqual(len(zipped), 3)
        self.assertIn((1, 'one'), zipped)
        self.assertIn((2, 'two'), zipped)
        self.assertIn((3, 'three'), zipped)

    def test_get_number_with_multiple_unit_scale_number_word(self):
        """
        Number detection from word with multiple unit scale numbers like 'one thousand to one hundred two'
        """
        message = 'one thousand to one hundred two'
        detect_texts, original_texts = get_number_from_number_word(message, self.number_words_map)
        zipped = zip(detect_texts, original_texts)
        self.assertEqual(len(zipped), 2)
        self.assertIn((1000, 'one thousand'), zipped)
        self.assertIn((102, 'one hundred two'), zipped)

    def test_get_number_with_combination_of_unit_scale_and_unit_number_word(self):
        """
        Number detection from word with combination of unit scale and unit number like 'one thousand one two three'
        """
        message = 'one thousand one two three'
        detect_texts, original_texts = get_number_from_number_word(message, self.number_words_map)
        zipped = zip(detect_texts, original_texts)
        self.assertEqual(len(zipped), 3)
        self.assertIn((1001, 'one thousand one'), zipped)
        self.assertIn((2, 'two'), zipped)
        self.assertIn((3, 'three'), zipped)

    def test_get_number_with_multiple_spaces_in_unit_scale_number_word(self):
        """
        Number detection from word with multiple spaces in unit scale number like 'one thousand   one   hundred two'
        """
        message = 'there are one thousand   one   hundred two students attending placement drive'
        detect_texts, original_texts = get_number_from_number_word(message, self.number_words_map)
        zipped = zip(detect_texts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn((1102, 'one thousand   one   hundred two'), zipped)


class TestTimeDetectionTestsMeta(type):
    yaml_test_files = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "time_ner_tests.yaml")
    ]

    def __new__(cls, name, bases, attrs):
        for test_name, test_fn in cls.yaml_testsuite_generator():
            attrs[test_name] = test_fn

        return super(TestTimeDetectionTestsMeta, cls).__new__(cls, name, bases, attrs)

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
                    "range": expected_output["range"],
                    "time_type": expected_output["time_type"]
                }
                original_text = str(expected_output["original_text"]).lower().strip() if expected_output[
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


class TestTimeDetectionTests(six.with_metaclass(TestTimeDetectionTestsMeta, TestCase)):
    pass
