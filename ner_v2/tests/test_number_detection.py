from __future__ import absolute_import

from django.test import TestCase
import collections
import datetime
import pytz

from ner_v2.detectors.numeral.utils import get_number_from_number_word
from ner_v2.detectors.numeral.number.number_detection import NumberDetector

NumberVariant = collections.namedtuple('NumberVariant', ['scale', 'increment'])


class NumberDetectionTest(TestCase):
    def setUp(self):
        self.entity_name = 'number'
        self.timezone = pytz.timezone('UTC')
        self.now_date = datetime.datetime.now(tz=self.timezone)

    def test_get_number_with_only_unit_in_number_word(self):
        """
        Number detection from word with only unit ex - 'one', 'two', 'twenty'
        """
        message = 'I want to book for one passenger'
        number_word_map = {
            'one': NumberVariant(scale=1, increment=1)
        }
        detect_texts, original_texts = get_number_from_number_word(message, number_word_map)
        zipped = zip(detect_texts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn((1, 'one'), zipped)

    def test_get_number_with_only_scale_in_number_word(self):
        """
        Number detection from word with only scale like - 'hundred', 'thousand'
        """
        message = 'need hundred change'
        number_word_map = {
            'hundred': NumberVariant(scale=100, increment=0)
        }
        detect_texts, original_texts = get_number_from_number_word(message, number_word_map)
        zipped = zip(detect_texts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn((100, 'hundred'), zipped)

    def test_get_number_with_scale_and_unit_in_number_word(self):
        """
        Number detection from word with scale and unit like - 'one hundred', 'one thousand two hundred five'
        """
        message = 'haptik get one thousand two hundred five messages daily'
        number_word_map = {
            'one': NumberVariant(scale=1, increment=1),
            'two': NumberVariant(scale=1, increment=2),
            'five': NumberVariant(scale=1, increment=5),
            'hundred': NumberVariant(scale=100, increment=0),
            'thousand': NumberVariant(scale=1000, increment=0)
        }
        detect_texts, original_texts = get_number_from_number_word(message, number_word_map)
        zipped = zip(detect_texts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn((1205, 'one thousand two hundred five'), zipped)

    def test_get_number_with_multiple_unit_number_word(self):
        """
        Number detection from word with multiple unit numbers like 'one two three twenty one'
        """
        message = 'one two three'
        number_word_map = {
            'one': NumberVariant(scale=1, increment=1),
            'two': NumberVariant(scale=1, increment=2),
            'three': NumberVariant(scale=1, increment=3)
        }
        detect_texts, original_texts = get_number_from_number_word(message, number_word_map)
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
        number_word_map = {
            'one': NumberVariant(scale=1, increment=1),
            'two': NumberVariant(scale=1, increment=2),
            'hundred': NumberVariant(scale=100, increment=0),
            'thousand': NumberVariant(scale=1000, increment=0)
        }
        detect_texts, original_texts = get_number_from_number_word(message, number_word_map)
        zipped = zip(detect_texts, original_texts)
        self.assertEqual(len(zipped), 2)
        self.assertIn((1000, 'one thousand'), zipped)
        self.assertIn((102, 'one hundred two'), zipped)

    def test_get_number_with_combination_of_unit_scale_and_unit_number_word(self):
        """
        Number detection from word with combination of unit scale and unit number like 'one thousand one two three'
        """
        message = 'one thousand one two three'
        number_word_map = {
            'one': NumberVariant(scale=1, increment=1),
            'two': NumberVariant(scale=1, increment=2),
            'three': NumberVariant(scale=1, increment=3),
            'thousand': NumberVariant(scale=1000, increment=0)
        }
        detect_texts, original_texts = get_number_from_number_word(message, number_word_map)
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
        number_word_map = {
            'one': NumberVariant(scale=1, increment=1),
            'two': NumberVariant(scale=1, increment=2),
            'hundred': NumberVariant(scale=100, increment=0),
            'thousand': NumberVariant(scale=1000, increment=0)
        }
        detect_texts, original_texts = get_number_from_number_word(message, number_word_map)
        zipped = zip(detect_texts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn((1102, 'one thousand   one   hundred two'), zipped)

    def test_en_number_detection_for_integer_number(self):
        """
        Number detection for english language for integer number like '100', '2'
        """
        message = u'100 men got selected for interview'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en')
        number_dicts, original_texts = number_detector_object.detect_entity(message)
        zipped = zip(number_dicts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn(({'value': '100', 'unit': None}, u'100'), zipped)

    def test_en_number_detection_for_integer_number_with_unit(self):
        """
        Number detection for english language for integer number with units like 'Rs100', '2Rs'
        """
        message = u'rs.100 is the application charger'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en')
        number_dicts, original_texts = number_detector_object.detect_entity(message)
        zipped = zip(number_dicts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn(({'value': '100', 'unit': 'rupees'}, 'rs.100'), zipped)

    def test_en_number_detection_for_decimal_number(self):
        """
        Number detection for english language for decimal number like '100.2'
        """
        message = u'Todays temperature is 11.2 degree celsius'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en')
        number_dicts, original_texts = number_detector_object.detect_entity(message)

        zipped = zip(number_dicts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn(({'value': '11.2', 'unit': None}, u'11.2'), zipped)

    def test_en_number_detection_for_decimal_number_with_unit(self):
        """
        Number detection for english language for decimal number with unit like '10.2k rupees'
        """
        message = u'my monthly salary is 10.12k rupees'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en')
        number_dicts, original_texts = number_detector_object.detect_entity(message)

        zipped = zip(number_dicts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn(({'value': '10120', 'unit': 'rupees'}, u'10.12k rupees'), zipped)

    def test_en_number_detection_for_integer_number_with_scale(self):
        """
        Number detection for english language for integer number with scale like '1 thousand', '1k', '1m'
        """
        message = '1 thousand men were killed in war'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en')
        number_dicts, original_texts = number_detector_object.detect_entity(message)

        zipped = zip(number_dicts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn(({'value': '1000', 'unit': None}, u'1 thousand'), zipped)

    def test_en_number_detection_for_integer_number_with_scale_and_unit(self):
        """
        Number detection for english language for integer number with scale and unit like 'Rs 1 thousand', '1k Rs'
        """
        message = 'i need 1 thousand rupees'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en')
        number_dicts, original_texts = number_detector_object.detect_entity(message)

        zipped = zip(number_dicts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn(({'value': '1000', 'unit': 'rupees'}, u'1 thousand rupees'), zipped)

    def test_en_number_detection_for_decimal_number_with_scale(self):
        """
        Number detection for english language for decimal number with scale like '1.2 thousand', '2.2k', '1.4m'
        """
        message = 'my monthly salary is 2.2k'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en')
        number_dicts, original_texts = number_detector_object.detect_entity(message)

        zipped = zip(number_dicts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn(({'value': '2200', 'unit': None}, u'2.2k'), zipped)

    def test_en_number_detection_for_decimal_number_with_scale_and_unit(self):
        """
        Number detection for english language for decimal number with scale like '1.2 thousand rupees', 'Rupees 2.2k'
        """
        message = 'I bought a car toy for 2.3k rupees'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en')
        number_dicts, original_texts = number_detector_object.detect_entity(message)

        zipped = zip(number_dicts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn(({'value': '2300', 'unit': 'rupees'}, u'2.3k rupees'), zipped)
