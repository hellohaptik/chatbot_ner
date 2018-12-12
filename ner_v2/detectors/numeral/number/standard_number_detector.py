# coding=utf-8
import pandas as pd
import os
import re

from ner_v2.detectors.numeral.constant import NUMBER_DATA_FILE_NAME_VARIANTS, \
    NUMBER_DATA_FILE_VALUE, NUMBER_DATA_FILE_TYPE, NUMBER_TYPE_UNIT, NUMBER_NUMERAL_CONSTANT_FILE, NUMBER_DETECT_VALUE, \
    NUMBER_DETECT_UNIT, NUMBER_UNITS_FILE, NUMBER_UNIT_VARIANTS, NUMBER_UNIT_VALUE
from ner_v2.detectors.numeral.utils import get_number_from_numerals


class BaseNumberDetector(object):
    def __init__(self, entity_name, data_directory_path):
        """
        Standard Number detection class, read data from language data path and help to detect number and numbers words
        for given languages.
        Args:
            data_directory_path (str): path of data folder for given language
        """
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.date = []
        self.original_date_text = []
        self.entity_name = entity_name
        self.tag = '__' + entity_name + '__'

        self.numbers_word = {}
        self.language_scale_map = {}
        self.units_map = {}

        # Method to initialise value in regex
        self.init_regex_and_parser(data_directory_path)

        self.regex_numeric_patterns = re.compile(r'(([\d,]+[.]?[\d]*)\s?(' + "|".join(self.language_scale_map.keys())
                                                 + r')?)\s*', re.UNICODE)

        # Variable to define default order in which detector will work
        self.detector_preferences = [self._detect_number_from_digit,
                                     self._detect_number_from_numerals
                                     ]

    def detect_number(self, text):
        self.text = text
        self.processed_text = text
        self.tagged_text = text

        number_list, original_list = None, None
        for detector in self.detector_preferences:
            number_list, original_list = detector(number_list, original_list)
            self._update_processed_text(original_list)
        return number_list, original_list

    @staticmethod
    def _get_list_from_pipe_sep_string(numerals_text):
        """
        Split numerals
        Args:
            numerals_text (str): numerals text
        Returns:
            (list) : list containing numeral after split
        """
        numerals_list = numerals_text.split("|")
        return [num.lower().strip() for num in numerals_list if num.strip()]

    def init_regex_and_parser(self, data_directory_path):
        """
        Initialise numbers word from from data file
        Args:
            data_directory_path (str): path of data folder for given language
        Returns:
            None
        """
        # create number_words dict having number variants and their corresponding scale and increment value
        # create language_scale_map dict having scale variants and their corresponding value
        numeral_df = pd.read_csv(os.path.join(data_directory_path, NUMBER_NUMERAL_CONSTANT_FILE), encoding='utf-8')
        for index, row in numeral_df.iterrows():
            name_variants = self._get_list_from_pipe_sep_string(row[NUMBER_DATA_FILE_NAME_VARIANTS])
            value = row[NUMBER_DATA_FILE_VALUE]
            if float(value).is_integer():
                value = int(row[NUMBER_DATA_FILE_VALUE])
            number_type = row[NUMBER_DATA_FILE_TYPE]

            if number_type == NUMBER_TYPE_UNIT:
                for numeral in name_variants:
                    self.numbers_word[numeral] = (1, value)
            else:
                for numeral in name_variants:
                    self.numbers_word[numeral] = (value, 0)
                    self.language_scale_map[numeral] = value

        # create units_dict having unit variants and their corresponding value
        unit_file_path = os.path.join(data_directory_path, NUMBER_UNITS_FILE)
        if os.path.exists(unit_file_path):
            units_df = pd.read_csv(unit_file_path, encoding='utf-8')
            for index, row in units_df.iterrows():
                unit_variants = self._get_list_from_pipe_sep_string(row[NUMBER_UNIT_VARIANTS])
                unit_value = row[NUMBER_UNIT_VALUE]
                for unit in unit_variants:
                    self.units_map[unit] = unit_value

    def _get_unit_from_text(self, detected_original, processed_text):
        """
        Method to detect unit from detected original text.
        Args:
            detected_original (str): detected number text from processed text
            processed_text (str): processed text
        Returns:
            unit(str|<None>): unit detected
            original_text(str): original text adding unit text if detected
        """
        unit = None
        original_text = detected_original
        if not self.units_map:
            return unit, original_text

        unit_choices = "|".join(self.units_map)
        unit_matches = re.findall(r'((' + unit_choices + r')?[\.\,\s]*?' + detected_original + r'\s*(' + unit_choices +
                                  r')?)', processed_text, re.UNICODE)
        if unit_matches:
            original_text = original_text[0][0].strip()
            unit_pre = unit_matches[0][1].strip()
            unit_suc = unit_matches[0][2].strip()
            if unit_pre:
                unit = self.units_map[unit_pre]
            elif unit_suc:
                unit = self.units_map[unit_suc]
        return unit, original_text

    def _detect_number_from_numerals(self, number_list=None, original_list=None):
        """
        Detect number from numeral text like "two thousand", "One hundred twenty two"
        Args:
            number_list (list): list containing detected numeric text
            original_list (list): list containing original numeral text
        Returns:
            number_list (list): list containing updated detected numeric text
            original_list (list): list containing updated original numeral text

        Examples:
            [In]  >>  self.processed_text = "One hundred two"
            [In]  >>  _detect_number_from_numerals()
            [Out] >> ([{'value': '102', 'unit': None}], ['one hundred two two'])

            [In]  >>  self.processed_text = "two hundred - three hundred"
            [In]  >>  _detect_number_from_numerals()
            [Out] >> ([{'value': '200', 'unit': None}, {'value': '300', 'unit': None}],
                      ['two hundred', 'three hundred'])

            [In]  >>  self.processed_text = "one two three"
            [In]  >>  _detect_number_from_numerals()
            [Out] >> ([{'value': '2', 'unit': None}, {'value': '2', 'unit': None}, {'value': '3', 'unit': None}],
                      ['one', 'two', 'three'])
        """
        number_list = number_list or []
        original_list = original_list or []

        numeral_text_list = re.split(r'[\-\:]', self.processed_text)
        for numeral_text in numeral_text_list:
            number_data = get_number_from_numerals(numeral_text, self.numbers_word)
            for number, original_text in zip(number_data[0], number_data[1]):
                unit, original_text = self._get_unit_from_text(original_text, numeral_text)
                number_list.append({
                    NUMBER_DETECT_VALUE: str(number),
                    NUMBER_DETECT_UNIT: unit
                })
                original_list.append(original_text)
        return number_list, original_list

    def _detect_number_from_digit(self, number_list=None, original_list=None):
        """
        Detect number from numeric text like 200 , 2.2k , 300.12
        Args:
            number_list (list): list containing detected numeric text
            original_list (list): list containing original numeral text
        Returns:
            number_list (list): list containing updated detected numeric text
            original_list (list): list containing updated original numeral text

        Examples:
            [In]  >>  self.processed_text = "200"
            [In]  >>  _detect_number_from_digit()
            [Out] >> ([{'value': '200', 'unit': None}], ['200'])

            [In]  >>  self.processed_text = "200-300"
            [In]  >>  _detect_number_from_digit()
            [Out] >> ([{'value': '200', 'unit': None}, {'value': '300', 'unit': None}],
                      ['200', '300'])

            [In]  >>  self.processed_text = "1 2 3"
            [In]  >>  _detect_number_from_digit()
            [Out] >> ([{'value': '2', 'unit': None}, {'value': '2', 'unit': None}, {'value': '3', 'unit': None}],
                      ['1', '2', '3'])

            [In]  >>  self.processed_text = "12.23"
            [In]  >>  _detect_number_from_digit()
            [Out] >> ([{'value': '12.23', 'unit': None}], ['12.23'])

            [In]  >>  self.processed_text = "2k"
            [In]  >>  _detect_number_from_digit()
            [Out] >> ([{'value': '2000', 'unit': None}], ['2k'])

            [In]  >>  self.processed_text = "2.2k"
            [In]  >>  _detect_number_from_digit()
            [Out] >> ([{'value': '2200', 'unit': None}], ['2.2k'])

        """
        number_list = number_list or []
        original_list = original_list or []

        patterns = self.regex_numeric_patterns.findall(self.processed_text)
        for pattern in patterns:
            original_text = pattern[0].strip()
            number = pattern[1].replace(",", "")
            scale = pattern[2].strip()
            scale = self.language_scale_map[scale] if scale else 1
            number = float(number) * scale
            number = int(number) if number.is_integer() else number
            unit, original_text = self._get_unit_from_text(original_text, self.processed_text)
            number_list.append({
                NUMBER_DETECT_VALUE: str(number),
                NUMBER_DETECT_UNIT: unit
            })
            original_list.append(original_text)

        return number_list, original_list

    def _update_processed_text(self, original_number_list):
        """
        Replaces detected date with tag generated from entity_name used to initialize the object with

        A final string with all dates replaced will be stored in object's tagged_text attribute
        A string with all dates removed will be stored in object's processed_text attribute

        Args:
            original_number_list (list): list of substrings of original text to be replaced with tag
                                       created from entity_name
        """
        for detected_text in original_number_list:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')


class NumberDetector(BaseNumberDetector):
    def __init__(self, entity_name, data_directory_path):
        super(NumberDetector, self).__init__(entity_name=entity_name, data_directory_path=data_directory_path)
