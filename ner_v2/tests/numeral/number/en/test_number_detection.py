from __future__ import absolute_import
import io
import os
import six
import yaml
from django.test import TestCase

from ner_v2.detectors.numeral.number.number_detection import NumberDetector
from ner_v2.detectors.numeral.number.standard_number_detector import NumberVariant
from ner_v2.detectors.numeral.utils import get_number_from_number_word
from six.moves import zip


class NumberFromWordsTest(TestCase):
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
        zipped = list(zip(detect_texts, original_texts))
        self.assertEqual(len(zipped), 1)
        self.assertIn((1, 'one'), zipped)

    def test_get_number_with_only_scale_in_number_word(self):
        """
        Number detection from word with only scale like - 'hundred', 'thousand'
        """
        message = 'need hundred change'
        detect_texts, original_texts = get_number_from_number_word(message, self.number_words_map)
        zipped = list(zip(detect_texts, original_texts))
        self.assertEqual(len(zipped), 1)
        self.assertIn((100, 'hundred'), zipped)

    def test_get_number_with_scale_and_unit_in_number_word(self):
        """
        Number detection from word with scale and unit like - 'one hundred', 'one thousand two hundred five'
        """
        message = 'haptik get one thousand two hundred five messages daily'
        detect_texts, original_texts = get_number_from_number_word(message, self.number_words_map)
        zipped = list(zip(detect_texts, original_texts))
        self.assertEqual(len(zipped), 1)
        self.assertIn((1205, 'one thousand two hundred five'), zipped)

    def test_get_number_with_multiple_unit_number_word(self):
        """
        Number detection from word with multiple unit numbers like 'one two three twenty one'
        """
        message = 'one two three'
        detect_texts, original_texts = get_number_from_number_word(message, self.number_words_map)
        zipped = list(zip(detect_texts, original_texts))
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
        zipped = list(zip(detect_texts, original_texts))
        self.assertEqual(len(zipped), 2)
        self.assertIn((1000, 'one thousand'), zipped)
        self.assertIn((102, 'one hundred two'), zipped)

    def test_get_number_with_combination_of_unit_scale_and_unit_number_word(self):
        """
        Number detection from word with combination of unit scale and unit number like 'one thousand one two three'
        """
        message = 'one thousand one two three'
        detect_texts, original_texts = get_number_from_number_word(message, self.number_words_map)
        zipped = list(zip(detect_texts, original_texts))
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
        zipped = list(zip(detect_texts, original_texts))
        self.assertEqual(len(zipped), 1)
        self.assertIn((1102, 'one thousand   one   hundred two'), zipped)


class NumberDetectorTestMeta(type):
    yaml_test_files = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "number_ner_tests.yaml")
    ]

    def __new__(cls, name, bases, attrs):
        for test_name, test_fn in cls.yaml_testsuite_generator():
            if test_name in attrs:
                raise ValueError('Got duplicate test name {test_name}, please make sure all tests have unique "id"'
                                 .format(test_name=test_name))
            attrs[test_name] = test_fn

        return super(NumberDetectorTestMeta, cls).__new__(cls, name, bases, attrs)

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
            num_dicts, original_texts = [], []
            for expected_output in expected_outputs:
                if "detected_number" in expected_output:
                    num_dict = {
                        "detected_number": expected_output["detected_number"]
                    }

                else:
                    num_dict = {
                        "value": str(expected_output["value"]) if expected_output["value"] else None,
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
            number_detector_object.set_min_max_digits(
                min_digit=testcase.get('min_digit', number_detector_object.min_digit),
                max_digit=testcase.get('max_digit', number_detector_object.max_digit))
            number_dicts, spans = number_detector_object.detect_entity(message)

            expected_number_dicts, expected_spans = parse_expected_outputs(testcase["outputs"])
            expected_outputs = list(six.moves.zip(expected_number_dicts, expected_spans))

            prefix = failure_string_prefix.format(message=message, language=language)

            self.assertEqual(len(number_dicts), len(spans),
                             prefix + u"Returned numbers and original_texts have different lengths")
            self.assertEqual(len(spans), len(expected_outputs),
                             prefix + u"Returned numbers and expected_outputs have different lengths")

            for output in six.moves.zip(number_dicts, spans):

                self.assertIn(output, expected_outputs,
                              prefix + u"{got} not in {expected_outputs}".format(got=output,
                                                                                 expected_outputs=expected_outputs))

        return run_test


class NumberDetectorTest(six.with_metaclass(NumberDetectorTestMeta, TestCase)):
    pass
