from __future__ import absolute_import
import importlib
import math
import os

from language_utilities.constant import ENGLISH_LANG
from ner_v2.detectors.base_detector import BaseDetector
from ner_v2.detectors.numeral.constant import NUMBER_DETECTION_RETURN_DICT_VALUE, NUMBER_DETECTION_RETURN_DICT_UNIT
from ner_v2.detectors.utils import get_lang_data_path
from six.moves import zip


class NumberDetector(BaseDetector):
    """Detects number from the text  and tags them.

    Detects all numbers in given text for all supported languages and replaces them by entity_name

    For Example:

        number_detector = NumberDetector("number_of_units")
        message = "I want to purchase 30 units of mobile and 40 units of Television"
        numbers, original_numbers = number_detector.detect_entity(message)
        tagged_text = number_detector.tagged_text
        print numbers, ' -- ', original_numbers
        print 'Tagged text: ', tagged_text

         >> [{'value': '30', 'unit': None}, {'value': 40, 'unit': None}] -- ['30', '40']
            Tagged text: I want to purchase __number_of_units__ units of mobile and __number)of_units__
            units of Television'


        number_detector = NumberDetector("number_of_people")
        message = "Can you please help me to book tickets for 3 people"
        numbers, original_numbers = number_detector.detect_entity(message)
        tagged_text = number_detector.tagged_text

        print numbers, ' -- ', original_numbers
        print 'Tagged text: ', tagged_text

         >> [{'value': '3', 'unit': 'people'}] -- ['3 people']
            Tagged text: Can you please help me to book tickets __number_of_people__

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected number would be replaced with on calling detect_entity()

        tagged_text: string with numbers replaced with tag defined by entity name
        processed_text: string with numbers detected removed
        number: list of numbers detected
        original_number_text: list to store substrings of the text detected as numbers
        tag: entity_name prepended and appended with '__'
        min_digit: minimum digit that a number can take
        max_digit: maximum digit that a number can take

    """

    @staticmethod
    def get_supported_languages():
        """
        Return list of supported languages
        Returns:
            (list): supported languages
        """
        supported_languages = []
        cwd = os.path.dirname(os.path.abspath(__file__))
        cwd_dirs = [x for x in os.listdir(cwd) if os.path.isdir(os.path.join(cwd, x))]
        for _dir in cwd_dirs:
            if len(_dir.rstrip(os.sep)) == 2:
                supported_languages.append(_dir)
        return supported_languages

    def __init__(self, entity_name, language=ENGLISH_LANG, unit_type=None, detect_without_unit=False):
        """Initializes a NumberDetector object

        Args:
            entity_name: A string by which the detected numbers would be replaced with on calling detect_entity()
            language (str, optional): language code of number text, defaults to 'en'
            unit_type (str): number unit types like weight, currency, temperature, used to detect number with
                               specific unit type.
        """
        # assigning values to superclass attributes
        self._supported_languages = self.get_supported_languages()
        super(NumberDetector, self).__init__(language)
        self.entity_name = entity_name
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.number = []
        self.original_number_text = []
        self.tag = '__' + self.entity_name + '__'
        self.min_digit = 1
        self.max_digit = 6
        self.language = language
        self.unit_type = unit_type
        self.detect_without_unit = detect_without_unit
        try:
            number_detector_module = importlib.import_module(
                'ner_v2.detectors.numeral.number.{0}.number_detection'.format(self.language))
            self.language_number_detector = number_detector_module.NumberDetector(entity_name=self.entity_name,
                                                                                  unit_type=self.unit_type)

        except ImportError:
            standard_number_regex = importlib.import_module(
                'ner_v2.detectors.numeral.number.standard_number_detector'
            )
            self.language_number_detector = standard_number_regex.NumberDetector(
                entity_name=self.entity_name,
                unit_type=self.unit_type,
                data_directory_path=get_lang_data_path(detector_path=os.path.abspath(__file__),
                                                       lang_code=self.language)
            )

    @property
    def supported_languages(self):
        return self._supported_languages

    def detect_entity(self, text, **kwargs):
        """Detects numbers in the text string

        Args:
            text: string to extract entities from
            **kwargs: it can be used to send specific arguments in future.

        Returns:
            A tuple of two lists with first list containing the detected numbers and second list containing their
            corresponding substrings in the original message.

            For example:

                ([{'value': '3', 'unit': 'people'}], ['3 people'])

            Additionally this function assigns these lists to self.number and self.original_number_text attributes
            respectively.

        """
        self.text = ' ' + text.lower() + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        number_data = self.language_number_detector.detect_number(self.processed_text)
        validated_number, validated_number_text = [], []
        for number_value_dict, original_text in zip(number_data[0], number_data[1]):
            number_value = number_value_dict[NUMBER_DETECTION_RETURN_DICT_VALUE]
            number_unit = number_value_dict[NUMBER_DETECTION_RETURN_DICT_UNIT]
            if self.min_digit <= self._num_digits(number_value) <= self.max_digit:
                if self.unit_type and (number_unit is None or
                                       self.language_number_detector.units_map[number_unit].type != self.unit_type)\
                        and not self.detect_without_unit:
                    continue
                validated_number.append(number_value_dict)
                validated_number_text.append(original_text)

        self.number = validated_number
        self.original_number_text = validated_number_text
        self.processed_text = self.language_number_detector.processed_text
        self.tagged_text = self.language_number_detector.tagged_text

        return validated_number, validated_number_text

    def get_unit_type(self, detected_unit):
        unit = self.language_number_detector.units_map.get(detected_unit)
        unit_type = unit.type if unit else None
        return unit_type

    def set_min_max_digits(self, min_digit, max_digit):
        """
        Update min max digit

        Args:
            min_digit (int): min digit
            max_digit (int): max digit
        """
        self.min_digit = min_digit
        self.max_digit = max_digit

    @staticmethod
    def _num_digits(value):
        """
        Calculate the number of digits in given number

        Args:
            value (str or float or int):

        Returns:
            int: number of digits in given number

        Raises:
            ValueError: if the given string cannot be cast to float
        """
        v = abs(float(value))
        return 1 if int(v) == 0 else (1 + int(math.log10(v)))