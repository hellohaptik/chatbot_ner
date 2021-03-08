# coding=utf-8
from __future__ import absolute_import

import collections
import os

import pandas as pd
from six.moves import zip

try:
    import regex as re

    _re_flags = re.UNICODE | re.V1 | re.WORD

except ImportError:

    import re

    _re_flags = re.UNICODE

from ner_v2.detectors.numeral.constant import NUMBER_NUMERAL_FILE_VARIANTS_COLUMN_NAME, \
    NUMBER_NUMERAL_FILE_VALUE_COLUMN_NAME, NUMBER_NUMERAL_FILE_TYPE_COLUMN_NAME, NUMBER_TYPE_UNIT, \
    NUMBER_NUMERAL_CONSTANT_FILE_NAME, NUMBER_DETECTION_RETURN_DICT_VALUE, \
    NUMBER_DETECTION_RETURN_DICT_UNIT, NUMBER_UNITS_FILE_NAME, NUMBER_DATA_FILE_UNIT_VARIANTS_COLUMN_NAME, \
    NUMBER_DATA_FILE_UNIT_VALUE_COLUMN_NAME, NUMBER_TYPE_SCALE, NUMBER_DATA_FILE_UNIT_TYPE_COLUMN_NAME
from ner_v2.detectors.numeral.utils import get_number_from_number_word, get_list_from_pipe_sep_string

NumberVariant = collections.namedtuple('NumberVariant', ['scale', 'increment'])
NumberUnit = collections.namedtuple('NumberUnit', ['value', 'type'])


class BaseNumberDetector(object):
    _SPAN_BOUNDARY_TEMPLATE = r'(?:^|(?<=[\s\"\'\,\-\?])){}(?=[\s\!\"\%\'\,\?\.\-]|$)'

    def __init__(self, entity_name, data_directory_path, unit_type=None):
        """
        Standard Number detection class, read data from language data path and help to detect number and numbers words
        for given languages.
        Args:
            entity_name (str): entity_name: string by which the detected number would be replaced
            data_directory_path (str): path of data folder for given language
            unit_type (str): number unit types like weight, currency, temperature, used to detect number with
                               specific unit type.

        """
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.entity_name = entity_name
        self.tag = '__' + entity_name + '__'

        self.numbers_word_map = {}
        self.scale_map = {}
        self.units_map = {}
        self.unit_type = unit_type

        # Method to initialise value in regex
        self.init_regex_and_parser(data_directory_path)

        sorted_len_units_keys = sorted(list(self.units_map.keys()), key=len, reverse=True)
        self.unit_choices = "|".join([re.escape(x) for x in sorted_len_units_keys])

        sorted_len_scale_map = sorted(list(self.scale_map.keys()), key=len, reverse=True)
        # using re.escape for strict matches in case pattern comes with '.' or '*', which should be escaped
        self.scale_map_choices = "|".join([re.escape(x) for x in sorted_len_scale_map])

        # Variable to define default order in which detector will work
        self.detector_preferences = [self._detect_number_from_digit,
                                     self._detect_number_from_words]

    def detect_number(self, text):
        """
        Detect number from numeric and number word. Run through list of detectors defined in detector_preferences in
        the preferences.
        Args:
            text(str): text string
        Returns:
            number_list (list): list containing detected numeric text
            original_list (list): list containing original numeral text

        """
        self.text = text
        self.processed_text = text
        self.tagged_text = text

        number_list, original_list = None, None
        for detector in self.detector_preferences:
            number_list, original_list = detector(number_list, original_list)
            self._update_processed_text(original_list)
        return number_list, original_list

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
        numeral_df = pd.read_csv(os.path.join(data_directory_path, NUMBER_NUMERAL_CONSTANT_FILE_NAME),
                                 encoding='utf-8')
        for index, row in numeral_df.iterrows():
            name_variants = get_list_from_pipe_sep_string(row[NUMBER_NUMERAL_FILE_VARIANTS_COLUMN_NAME])
            value = row[NUMBER_NUMERAL_FILE_VALUE_COLUMN_NAME]
            if float(value).is_integer():
                value = int(row[NUMBER_NUMERAL_FILE_VALUE_COLUMN_NAME])
            number_type = row[NUMBER_NUMERAL_FILE_TYPE_COLUMN_NAME]

            if number_type == NUMBER_TYPE_UNIT:
                for numeral in name_variants:
                    # tuple values to corresponds to (scale, increment), for unit type, scale will always be 1.
                    self.numbers_word_map[numeral] = NumberVariant(scale=1, increment=value)

            elif number_type == NUMBER_TYPE_SCALE:
                for numeral in name_variants:
                    # tuple values to corresponds to (scale, increment), for scale type, increment will always be 0.
                    self.numbers_word_map[numeral] = NumberVariant(scale=value, increment=0)
                    # Dict map to store scale and their values
                    self.scale_map[numeral] = value

        # create units_dict having unit variants and their corresponding value
        unit_file_path = os.path.join(data_directory_path, NUMBER_UNITS_FILE_NAME)
        if os.path.exists(unit_file_path):
            units_df = pd.read_csv(unit_file_path, encoding='utf-8')
            if self.unit_type:
                units_df = units_df[units_df[NUMBER_DATA_FILE_UNIT_TYPE_COLUMN_NAME] == self.unit_type]
            for index, row in units_df.iterrows():
                unit_variants = get_list_from_pipe_sep_string(row[NUMBER_DATA_FILE_UNIT_VARIANTS_COLUMN_NAME])
                unit_value = row[NUMBER_DATA_FILE_UNIT_VALUE_COLUMN_NAME]
                unit_type = row[NUMBER_DATA_FILE_UNIT_TYPE_COLUMN_NAME]
                for unit in unit_variants:
                    self.units_map[unit] = NumberUnit(value=unit_value, type=unit_type)

    def _get_unit_from_text(self, detected_original, processed_text):
        """
        Method to detect units present in prefix or suffix of number from detected original string. It will also return
        updated original text with units included if found.
            Example - For number 'one hundred rupees', our number detector will detect "one hundred" as 100.
                      To detect unit we pass original string "one hundred" and processed text "one hundred rupees" to
                      this method, which will apply regex to find if any unit text (here rupees) is present in
                      prefix or suffix of original string and return corresponding value if found.
        Args:
            detected_original (str): detected number text from processed text
            processed_text (str): processed text
        Returns:
            unit(str|<None>): unit detected
            original_text(str): original text adding unit text if detected

        Examples:
            [In]  >> _get_unit_from_text('100', '100 Rs')
            [Out] >> ('rupees', '100 Rs')

            [In]  >> _get_unit_from_text('one hundred', 'rupees one hundred')
            [Out] >> ('rupees', 'rupees one hundred')

        """
        unit = None
        original_text = detected_original

        if not self.units_map:
            return unit, original_text

        processed_text = " " + processed_text.strip() + " "

        # add re.escape to handle decimal cases in detected original
        detected_original = re.escape(detected_original)
        unit_matches = re.search(r'\W+((' + self.unit_choices + r')[.,\s]*' + detected_original + r')\W+|\W+(' +
                                 detected_original + r'\s*(' +
                                 self.unit_choices + r'))\W+',
                                 processed_text,
                                 re.UNICODE)
        if unit_matches:
            original_text_prefix, unit_prefix, original_text_suffix, unit_suffix = unit_matches.groups()
            if unit_suffix:
                unit = self.units_map[unit_suffix.strip()].value
                original_text = original_text_suffix.strip()
            elif unit_prefix:
                unit = self.units_map[unit_prefix.strip()].value
                original_text = original_text_prefix.strip()
        return unit, original_text

    def _detect_number_from_words(self, number_list=None, original_list=None):
        """
        Detect numbers from number words, for example - "two thousand", "One hundred twenty two".
        How it works?
            First it splits the text checking if any of '-' or ':' is present in text, and pass the split text
            to number word detector, which return the number value and original word from which it is being detected.
            Further we check for unit in suffix and prefix of original string and update that if any units are found.
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

            *Notes*
                Some Limitations:
                i) Cannot detect decimals without the integer part. E.g. .25, .5, etc
                ii) Cannot detect one with "a/an". E.g. I want an apple
                iii) Detects wrong for multiple scales mentioned consecutively E.g. three hundred thousand,
                     hundred thousand
        """
        number_list = number_list or []
        original_list = original_list or []

        # Splitting text based on "-" and ":",  as in case of text "two thousand-three thousand", simple splitting
        # will give list as [two, thousand-three, thousand], result in number word detector giving wrong result,
        # hence we need to separate them into [two thousand, three thousand] using '-' or ':' as split char
        numeral_text_list = re.split(r'[\-\:]', self.processed_text)
        for numeral_text in numeral_text_list:
            numbers, original_texts = get_number_from_number_word(numeral_text, self.numbers_word_map)
            full_list = list(zip(numbers, original_texts))
            sorted_full_list = sorted(full_list, key=lambda kv: len(kv[1]), reverse=True)
            for number, original_text in sorted_full_list:
                unit = None
                if self.unit_type:
                    unit, original_text = self._get_unit_from_text(original_text, numeral_text)
                _pattern = re.compile(self._SPAN_BOUNDARY_TEMPLATE.format(re.escape(original_text)), flags=_re_flags)
                if _pattern.search(numeral_text):
                    numeral_text = _pattern.sub(self.tag, numeral_text, 1)
                    number_list.append({
                        NUMBER_DETECTION_RETURN_DICT_VALUE: str(number),
                        NUMBER_DETECTION_RETURN_DICT_UNIT: unit
                    })
                    original_list.append(original_text)
        return number_list, original_list

    def _detect_number_from_digit(self, number_list=None, original_list=None):
        """
        Detect number from numeric(digit) text considering integer and float both. It also check for cases where
        scales are also present in suffix of digit like '200 thousand' or '2.2k'.

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
        processed_text = self.processed_text

        regex_numeric_patterns = re.compile(r'(([\d,]+\.?[\d]*)\s?(' + self.scale_map_choices + r'))[\s\-\:]' +
                                            r'|([\d,]+\.?[\d]*)', re.UNICODE)
        patterns = regex_numeric_patterns.findall(processed_text)
        for pattern in patterns:
            number, scale, original_text = None, None, None
            if pattern[1] and pattern[1].replace(',', '').replace('.', '').isdigit():
                number = pattern[1].replace(',', '')
                original_text = pattern[0].strip().strip(',.').strip()
                scale = self.scale_map[pattern[2].strip()]

            elif pattern[3] and pattern[3].replace(',', '').replace('.', '').isdigit():
                number = pattern[3].replace(',', '')
                original_text = pattern[3].strip().strip(',.').strip()
                scale = 1

            if number:
                if '.' not in number:
                    number = int(number) * scale
                else:
                    number = float(number) * scale
                    # FIXME: this conversion from float -> int is lossy, consider using Decimal class
                    number = int(number) if number.is_integer() else number
                unit = None
                if self.unit_type:
                    unit, original_text = self._get_unit_from_text(original_text, processed_text)
                _pattern = re.compile(self._SPAN_BOUNDARY_TEMPLATE.format(re.escape(original_text)), flags=_re_flags)
                if _pattern.search(processed_text):
                    processed_text = _pattern.sub(self.tag, processed_text, 1)
                    number_list.append({
                        NUMBER_DETECTION_RETURN_DICT_VALUE: str(number),
                        NUMBER_DETECTION_RETURN_DICT_UNIT: unit
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
            _pattern = re.compile(self._SPAN_BOUNDARY_TEMPLATE.format(re.escape(detected_text)), flags=_re_flags)
            self.tagged_text = _pattern.sub(self.tag, self.tagged_text, 1)
            self.processed_text = _pattern.sub('', self.processed_text, 1)


class NumberDetector(BaseNumberDetector):
    def __init__(self, entity_name, data_directory_path, unit_type=None):
        super(NumberDetector, self).__init__(entity_name=entity_name,
                                             data_directory_path=data_directory_path,
                                             unit_type=unit_type)
