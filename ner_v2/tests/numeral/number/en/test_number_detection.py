from __future__ import absolute_import

from django.test import TestCase


from ner_v2.detectors.numeral.utils import get_number_from_number_word
from ner_v2.detectors.numeral.number.number_detection import NumberDetector
from ner_v2.detectors.numeral.number.standard_number_detector import NumberVariant


class NumberDetectionTest(TestCase):
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
            u'ml': NumberVariant(scale=1000000, increment=0),
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

    def test_en_number_detection_for_integer_number(self):
        """
        Number detection for english language for integer number like '100', '2'
        """
        message = u'100 got selected for interview'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en')
        number_dicts, original_texts = number_detector_object.detect_entity(message)
        zipped = zip(number_dicts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn(({'value': '100', 'unit': None}, u'100'), zipped)

    def test_en_number_detection_for_integer_number_with_unit_and_unit_type_given(self):
        """
        Number detection for english language for integer number with units like 'Rs100', '2Rs'
        """
        message = u'rs.100 is the application charger'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en', unit_type='currency')
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

    def test_en_number_detection_for_decimal_number_with_unit_and_unit_type_given(self):
        """
        Number detection for english language for decimal number with unit like '10.2k rupees'
        """
        message = u'my monthly salary is 10.12k rupees'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en', unit_type='currency')
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

    def test_en_number_detection_for_integer_number_with_scale_and_unit_and_unit_type_given(self):
        """
        Number detection for english language for integer number with scale and unit like 'Rs 1 thousand', '1k Rs'
        """
        message = 'i need 1 thousand rupees'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en', unit_type='currency')
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
        Number detection for english language for decimal number with scale like '1.2 thousand', '2.2k' excluding unit
        """
        message = 'I bought a car toy for 2.3k rupees'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en')
        number_dicts, original_texts = number_detector_object.detect_entity(message)

        zipped = list(zip(number_dicts, original_texts))
        self.assertEqual(len(zipped), 1)
        self.assertIn(({'value': '2300', 'unit': None}, u'2.3k'), zipped)

    def test_en_number_detection_for_decimal_number_with_scale_and_unit_and_unit_type_given(self):
        """
        Number detection for english language for decimal number with scale like '1.2 thousand rupees', 'Rupees 2.2k'
        """
        message = 'I bought a car toy for 2.3k rupees'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en', unit_type='currency')
        number_dicts, original_texts = number_detector_object.detect_entity(message)

        zipped = zip(number_dicts, original_texts)
        self.assertEqual(len(zipped), 1)
        self.assertIn(({'value': '2300', 'unit': 'rupees'}, u'2.3k rupees'), zipped)

    def test_en_number_detection_for_decimal_number_with_scale_and_unit_and_different_unit_type_given(self):
        """
        Number detection for english language for decimal number with scale like '1.2 thousand rupees', 'Rupees 2.2k'
        """
        message = 'I buys 2.3k kg mango'
        number_detector_object = NumberDetector(entity_name=self.entity_name, language='en', unit_type='currency')
        number_dicts, original_texts = number_detector_object.detect_entity(message)

        zipped = list(zip(number_dicts, original_texts))
        self.assertEqual(len(zipped), 0)
