# coding=utf-8
from __future__ import absolute_import

import collections
import os

import pandas as pd
from six.moves import zip

import ner_v2.detectors.numeral.constant as numeral_constant
from ner_v2.detectors.numeral.number.number_detection import NumberDetector
from ner_v2.detectors.numeral.utils import get_list_from_pipe_sep_string

try:
    import regex as re

    _re_flags = re.UNICODE | re.V1 | re.WORD

except ImportError:

    import re

    _re_flags = re.UNICODE

NumberRangeVariant = collections.namedtuple('NumberRangeVariant', ['position', 'range_type'])
ValueTextPair = collections.namedtuple('ValueTextPair', ['entity_value', 'original_text'])


class BaseNumberRangeDetector(object):
    def __init__(self, entity_name, language, data_directory_path, unit_type=None):
        """
        Standard Number detection class, read data from language data path and help to detect number ranges like min
        and max value from given number range text for given languages.
        Args:
            entity_name (str): entity_name: string by which the detected number would be replaced
            language (str): language code of text
            data_directory_path (str): path of data folder for given language
            unit_type (str, optional): number unit types like weight, currency, temperature, used to detect number with
                                       specific unit type only. If None, it will detect all number ranges irrespective
                                       of units. You can see all unit types supported inside number detection
                                       language data with filename unit.csv.

        """
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.entity_name = entity_name
        self.tag = '__' + entity_name + '__'
        self.range_variants_map = {}
        self.unit_type = unit_type
        self.language = language
        self.min_range_prefix_variants = None
        self.min_range_suffix_variants = None
        self.max_range_prefix_variants = None
        self.max_range_suffix_variants = None
        self.min_max_range_variants = None
        self.number_detected_map = {}

        self.number_detector = NumberDetector(entity_name=entity_name, language=language, unit_type=unit_type,
                                              detect_without_unit=True)
        self.number_detector.set_min_max_digits(1, 100)

        # Method to initialise regex params
        self._init_regex_for_range(data_directory_path)

        # Variable to define default order in which detector will work
        self.detector_preferences = [self._detect_min_max_num_range,
                                     self._detect_min_num_range_with_prefix_variants,
                                     self._detect_min_num_range_with_suffix_variants,
                                     self._detect_max_num_range_with_prefix_variants,
                                     self._detect_max_num_range_with_suffix_variants,
                                     self._detect_absolute_number]

    def _init_regex_for_range(self, data_directory_path):
        """
        Initialise params which hold variants of keywords defining whether a given number range in text contains
        min value, max value or both.

        Params:
             min_range_start_variants (list): List of keywords which occur before min value in text
             min_range_end_variants (list): List of keywords which occur after min value in text
             max_range_start_variants (list): List of keywords which occur before max value in text
             max_range_end_variants (list): List of keywords which occur after max value in text
             min_max_range_variants (list): List of keywords which occur in between min and max value in text
        Args:
            data_directory_path (str): Data directory path
        Returns:
            None
        """
        number_range_df = pd.read_csv(os.path.join(data_directory_path,
                                                   numeral_constant.NUMBER_RANGE_KEYWORD_FILE_NAME), encoding='utf-8')
        for index, row in number_range_df.iterrows():
            range_variants = get_list_from_pipe_sep_string(row[numeral_constant.COLUMN_NUMBER_RANGE_VARIANTS])
            for variant in range_variants:
                self.range_variants_map[variant] = \
                    NumberRangeVariant(position=row[numeral_constant.COLUMN_NUMBER_RANGE_POSITION],
                                       range_type=row[numeral_constant.COLUMN_NUMBER_RANGE_RANGE_TYPE])

        self.min_range_prefix_variants = [re.escape(variant) for variant, value in self.range_variants_map.items()
                                          if (value.position == -1 and
                                              value.range_type == numeral_constant.NUMBER_RANGE_MIN_TYPE)]

        self.min_range_suffix_variants = [re.escape(variant) for variant, value in self.range_variants_map.items()
                                          if (value.position == 1 and
                                              value.range_type == numeral_constant.NUMBER_RANGE_MIN_TYPE)]

        self.max_range_prefix_variants = [re.escape(variant) for variant, value in self.range_variants_map.items()
                                          if (value.position == -1 and
                                              value.range_type == numeral_constant.NUMBER_RANGE_MAX_TYPE)]

        self.max_range_suffix_variants = [re.escape(variant) for variant, value in self.range_variants_map.items()
                                          if (value.position == 1 and
                                              value.range_type == numeral_constant.NUMBER_RANGE_MAX_TYPE)]

        self.min_max_range_variants = [re.escape(variant) for variant, value in self.range_variants_map.items()
                                       if (value.position == 0 and
                                           value.range_type == numeral_constant.NUMBER_RANGE_MIN_MAX_TYPE)]

    def _tag_number_in_text(self, processed_text):
        """
        replace number in text with number tag from number_detected_map
        Args:
            processed_text (str): processed text
        Returns:
            (str): text with number replaced with tag
        Examples:
            >>> text = 'i want to buy 3 apples and more than two bananas'
            >>> number_detected_map = {'__number__0': ({'value': '2', 'unit': None}, 'two'),
                                       '__number__1': ({'value': '3', 'unit': None}, '3')}
            >>> self._tag_number_in_text(text)
            i want to buy __number__1 apples and more than __number__0 bananas
        """
        tagged_number_text = processed_text
        sorted_number_detected_map = sorted(list(self.number_detected_map.items()),
                                            key=lambda kv: len(kv[1].original_text), reverse=True)
        span_template = self.number_detector.language_number_detector._SPAN_BOUNDARY_TEMPLATE
        for number_tag, value_text_pair in sorted_number_detected_map:
            tagged_number_text = re.sub(span_template.format(re.escape(value_text_pair.original_text)), number_tag,
                                        tagged_number_text, count=1, flags=_re_flags)
        return tagged_number_text

    def _get_number_tag_dict(self):
        """
        Method to create number tag dict. Its run number detection on text and create a dict having number tag as key
        and value as tuple of entity value and original text.
        Returns:
            (dict): dict containing number tag and their corresponding value and original text
        Examples:
            >>> text = 'I want 12 dozen banana'
            >>> self._get_number_tag_dict()
            {'__dnumber_1': ({'value': 12, 'unit': None}, '12')}
        """
        detected_number_dict = {}
        entity_value_list, original_text_list = self.number_detector.detect_entity(self.processed_text)
        for index, (entity_value, original_text) in enumerate(zip(entity_value_list, original_text_list)):
            key = '{number}{index}__'.format(number=numeral_constant.NUMBER_REPLACE_TEXT, index=index)
            detected_number_dict[key] = ValueTextPair(entity_value=entity_value, original_text=original_text)
        return detected_number_dict

    def _get_original_text_from_tagged_text(self, number_tag_text):
        """
        Return original text value of number tag from number detected map
        Args:
            number_tag_text (str): tagged number
        Returns:
            (str or None): Original value of tagged number if found else None
        """
        original = number_tag_text
        for number_tag in self.number_detected_map:
            original = original.replace(number_tag, self.number_detected_map[number_tag].original_text)
        if original == number_tag_text:
            return None
        return original

    def detect_number_range(self, text):
        """
        Detect number-range from number range text. Run through list of detectors defined in detector_preferences in
        the preferences.
        Args:
            text(str): text string
        Returns:
            (tuple): a tuple containing
                (list): list containing detected numeric text
                (list): list containing original numeral text

        """
        self.text = text
        self.tagged_text = text
        self.processed_text = text
        self.number_detected_map = self._get_number_tag_dict()
        self.processed_text = self._tag_number_in_text(text)

        number_list, original_list = None, None
        for detector in self.detector_preferences:
            number_list, original_list = detector(number_list, original_list)
            self._update_tagged_text(original_list)
        return number_list, original_list

    def _detect_absolute_number(self, number_list, original_list):
        number_list = number_list or []
        original_list = original_list or []
        abs_number_pattern = re.compile(r'({number}\d+__)'.format(number=numeral_constant.NUMBER_REPLACE_TEXT),
                                        re.UNICODE)
        abs_number_matches = abs_number_pattern.findall(self.processed_text)
        for match in abs_number_matches:
            entity_unit = self.number_detected_map[match].entity_value[
                numeral_constant.NUMBER_DETECTION_RETURN_DICT_UNIT]
            if (self.unit_type and entity_unit) or not self.unit_type:
                number_list.append({numeral_constant.NUMBER_RANGE_MAX_VALUE: None,
                                    numeral_constant.NUMBER_RANGE_MIN_VALUE: None,
                                    numeral_constant.NUMBER_RANGE_VALUE_UNIT: entity_unit,
                                    numeral_constant.NUMBER_RANGE_ABS_VALUE: self.
                                   number_detected_map[match].
                                   entity_value[numeral_constant.NUMBER_DETECTION_RETURN_DICT_VALUE]})
                original_list.append(self.number_detected_map[match].original_text)
        return number_list, original_list

    def _get_number_range(self, min_part_match, max_part_match, full_match):
        """
        Update number_range_list and original_list by finding entity value of number tag and original text from
        number_detected_map
        Args:
            min_part_match (str or None): tagged min number
            max_part_match (str or None): tagged max number
            full_match (str): text matching regex
        Returns:
            (tuple): a tuple containing
                (list): list containing detected numeric text
                (list): list containing original numeral text
        """
        number_range = None
        original_text = None

        if full_match not in self.processed_text:
            return number_range, original_text

        entity_value_min, entity_value_max, entity_unit = None, None, None

        if min_part_match and min_part_match in self.number_detected_map:
            entity_dict = self.number_detected_map[min_part_match].entity_value
            entity_value_min = entity_dict[numeral_constant.NUMBER_DETECTION_RETURN_DICT_VALUE]
            entity_unit = entity_dict[numeral_constant.NUMBER_DETECTION_RETURN_DICT_UNIT]

        if max_part_match and max_part_match in self.number_detected_map:
            entity_dict = self.number_detected_map[max_part_match].entity_value
            entity_value_max = entity_dict[numeral_constant.NUMBER_DETECTION_RETURN_DICT_VALUE]
            if not entity_unit:
                entity_unit = entity_dict[numeral_constant.NUMBER_DETECTION_RETURN_DICT_UNIT]

        if self.unit_type and (
                entity_unit is None or self.number_detector.get_unit_type(entity_unit) != self.unit_type):
            return number_range, original_text

        if min_part_match and max_part_match:
            if float(entity_value_min) > float(entity_value_max):
                temp = entity_value_max
                entity_value_max = entity_value_min
                entity_value_min = temp

        original_text = self._get_original_text_from_tagged_text(full_match)
        if (entity_value_min or entity_value_max) and original_text:
            self.processed_text = self.processed_text.replace(full_match.strip(), '', 1)
            original_text = original_text.strip()
            number_range = {
                numeral_constant.NUMBER_RANGE_MIN_VALUE: entity_value_min,
                numeral_constant.NUMBER_RANGE_MAX_VALUE: entity_value_max,
                numeral_constant.NUMBER_RANGE_ABS_VALUE: None,
                numeral_constant.NUMBER_RANGE_VALUE_UNIT: entity_unit
            }
        return number_range, original_text

    def _detect_min_num_range_with_prefix_variants(self, number_range_list=None, original_list=None):
        """
        Method to detect number range containing only min value and keywords which identify value as min present
        before them. Example - More than 2 {'more than' => keyword, '2' => min value},
                               At least seven hundred rupees {'At least' => keyword, 'seven hundred rupees'=>min value}
        Args:
            number_range_list (list):
            original_list (list):
        Returns:
            (tuple): a tuple containing
                (list): list containing detected numeric text
                (list): list containing original numeral text
        """
        number_range_list = number_range_list or []
        original_list = original_list or []

        if self.min_range_prefix_variants:
            min_prefix_choices = '|'.join(self.min_range_prefix_variants)
            min_range_start_pattern = re.compile(r'((?:{min_prefix_choices})\s+({number}\d+__))'.format(
                number=numeral_constant.NUMBER_REPLACE_TEXT, min_prefix_choices=min_prefix_choices), re.UNICODE)
            number_range_matches = min_range_start_pattern.findall(self.processed_text)
            for match in number_range_matches:
                number_range, original_text = self._get_number_range(min_part_match=match[1], max_part_match=None,
                                                                     full_match=match[0])
                if number_range and original_text:
                    number_range_list.append(number_range)
                    original_list.append(original_text)
        return number_range_list, original_list

    def _detect_min_num_range_with_suffix_variants(self, number_range_list=None, original_list=None):
        """
        Method to detect number range containing only min value and keywords which identify value as min present
        after them.
        Args:
            number_range_list (list):
            original_list (list):
        Returns:
           (tuple): a tuple containing
                (list): list containing detected numeric text
                (list): list containing original numeral text
        """
        number_range_list = number_range_list or []
        original_list = original_list or []

        if self.min_range_suffix_variants:
            min_suffix_choices = '|'.join(self.min_range_suffix_variants)
            min_range_end_pattern = re.compile(r'(({number}\d+__)\s+(?:{min_suffix_choices}))'.format(
                number=numeral_constant.NUMBER_REPLACE_TEXT, min_suffix_choices=min_suffix_choices), re.UNICODE)
            number_range_matches = min_range_end_pattern.findall(self.processed_text)
            for match in number_range_matches:
                number_range, original_text = self._get_number_range(min_part_match=match[1], max_part_match=None,
                                                                     full_match=match[0])
                if number_range and original_text:
                    number_range_list.append(number_range)
                    original_list.append(original_text)

        return number_range_list, original_list

    def _detect_max_num_range_with_prefix_variants(self, number_range_list=None, original_list=None):
        """
        Method to detect number range containing only max value and keywords which identify value as min present
        before them. Example - less than 2 {'less than' => keyword, '2' => max value},
                               At most seven hundred rupees {'At most' => keyword, 'seven hundred rupees'=>min value}
        Args:
            number_range_list (list):
            original_list (list):
        Returns:
            (tuple): a tuple containing
                (list): list containing detected numeric text
                (list): list containing original numeral text
        """
        number_range_list = number_range_list or []
        original_list = original_list or []

        if self.max_range_prefix_variants:
            max_prefix_choices = '|'.join(self.max_range_prefix_variants)
            max_range_start_pattern = re.compile(r'((?:{max_prefix_choices})\s+({number}\d+__))'.format(
                number=numeral_constant.NUMBER_REPLACE_TEXT, max_prefix_choices=max_prefix_choices), re.UNICODE)
            number_range_matches = max_range_start_pattern.findall(self.processed_text)
            for match in number_range_matches:
                number_range, original_text = self._get_number_range(min_part_match=None, max_part_match=match[1],
                                                                     full_match=match[0])
                if number_range and original_text:
                    number_range_list.append(number_range)
                    original_list.append(original_text)

        return number_range_list, original_list

    def _detect_max_num_range_with_suffix_variants(self, number_range_list=None, original_list=None):
        """
        Method to detect number range containing only max value and keywords which identify value as min present
        after them.
        Args:
            number_range_list (list):
            original_list (list):
        Returns:
            (tuple): a tuple containing
                (list): list containing detected numeric text
                (list): list containing original numeral text
        """
        number_range_list = number_range_list or []
        original_list = original_list or []

        if self.max_range_suffix_variants:
            max_suffix_choices = '|'.join(self.max_range_suffix_variants)
            max_range_end_pattern = re.compile(r'(({number}\d+__)\s+(?:{max_suffix_choices}))'.format(
                number=numeral_constant.NUMBER_REPLACE_TEXT, max_suffix_choices=max_suffix_choices), re.UNICODE)
            number_range_matches = max_range_end_pattern.findall(self.processed_text)
            for match in number_range_matches:
                number_range, original_text = self._get_number_range(min_part_match=None, max_part_match=match[1],
                                                                     full_match=match[0])
                if number_range and original_text:
                    number_range_list.append(number_range)
                    original_list.append(original_text)

        return number_range_list, original_list

    def _detect_min_max_num_range(self, number_range_list=None, original_list=None):
        """
        Method to detect number range containing both min and max value and keywords them present in between
        Example - 2000 to 30000 {'to' => keyword, '2000' => min value, '30000' => ,max_value},
                 2k-3k hundred rupees {'-' => keyword, '2k' => min value, '3k' => ,max_value}
        Args:
            number_range_list (list):
            original_list (list):
        Returns:
            (tuple): a tuple containing
                (list): list containing detected numeric text
                (list): list containing original numeral text
        """
        number_range_list = number_range_list or []
        original_list = original_list or []

        if self.min_max_range_variants:
            min_max_choices = '|'.join(self.min_max_range_variants)
            min_max_range_pattern = re.compile(r'(({number}\d+__)\s*(?:{min_max_choices})\s*'
                                               r'({number}\d+__))'.format(number=numeral_constant.NUMBER_REPLACE_TEXT,
                                                                          min_max_choices=min_max_choices), re.UNICODE)
            number_range_matches = min_max_range_pattern.findall(self.processed_text)
            for match in number_range_matches:
                number_range, original_text = self._get_number_range(min_part_match=match[1], max_part_match=match[2],
                                                                     full_match=match[0])
                if number_range and original_text:
                    number_range_list.append(number_range)
                    original_list.append(original_text)

        return number_range_list, original_list

    def _update_tagged_text(self, original_number_list):
        """
        Replaces detected date with tag generated from entity_name used to initialize the object with
        A final string with all dates replaced will be stored in object's tagged_text attribute
        A string with all dates removed will be stored in object's processed_text attribute

        Args:
            original_number_list (list): list of substrings of original text to be replaced with tag
                                       created from entity_name
        """
        for detected_text in original_number_list:
            _pattern = re.compile(r'\b%s\b' % re.escape(detected_text), flags=_re_flags)
            self.tagged_text = _pattern.sub(self.tag, self.tagged_text)


class NumberRangeDetector(BaseNumberRangeDetector):
    def __init__(self, entity_name, language, data_directory_path, unit_type=None):
        super(NumberRangeDetector, self).__init__(entity_name=entity_name,
                                                  language=language,
                                                  data_directory_path=data_directory_path,
                                                  unit_type=unit_type)
