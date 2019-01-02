# coding=utf-8
import pandas as pd
import collections
import os
import re

from ner_v2.detectors.numeral.constant import NUMBER_RANGE_KEYWORD_FILE_NAME, NUMBER_RANGE_FILE_VARIANTS_COLUMN_NAME, \
    NUMBER_RANGE_FILE_POSITION_COLUMN_NAME, NUMBER_RANGE_FILE_RANGE_TYPE_COLUMN_NAME, NUMBER_RANGE_MIN_TYPE, \
    NUMBER_RANGE_MAX_TYPE, NUMBER_RANGE_MIN_MAX_TYPE, NUMBER_REPLACE_TEXT, NUMBER_RANGE_MIN_VALUE, \
    NUMBER_DETECTION_RETURN_DICT_VALUE, NUMBER_RANGE_MAX_VALUE, NUMBER_RANGE_VALUE_UNIT, \
    NUMBER_DETECTION_RETURN_DICT_UNIT
from ner_v2.detectors.numeral.utils import get_list_from_pipe_sep_string
from ner_v2.detectors.numeral.number.number_detection import NumberDetector

NumberRangeVariant = collections.namedtuple('NumberRangeVariant', ['position', 'range_type'])


class BaseNumberRangeDetector(object):
    def __init__(self, entity_name, language, data_directory_path, unit_type=None):
        """
        Standard Number detection class, read data from language data path and help to detect number ranges like min
        and max value from given number range text for given languages.
        Args:
            entity_name (str): entity_name: string by which the detected number would be replaced
            language (str): language code of text
            data_directory_path (str): path of data folder for given language
            unit_type (str): number unit types like weight, currency, temperature, used to detect number with
                               specific unit type.

        """
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.number_tagged_processed_text = ''
        self.date = []
        self.original_date_text = []
        self.entity_name = entity_name
        self.tag = '__' + entity_name + '__'
        self.range_variants_map = {}
        self.unit_type = unit_type

        self.min_range_start_variants = None
        self.min_range_end_variants = None
        self.max_range_start_variants = None
        self.max_range_end_variants = None
        self.min_max_range_variants = None
        self.number_detected_map = None

        self.language_number_detector = NumberDetector(entity_name=entity_name, language=language, unit_type=unit_type)
        self.language_number_detector.set_min_max_digits(1, 100)

        # Method to initialise regex params
        self.init_regex_for_range(data_directory_path)

        # Variable to define default order in which detector will work
        self.detector_preferences = [self._detect_min_num_range_with_start_variant,
                                     self._detect_min_num_range_with_end_variant,
                                     self._detect_max_num_range_with_start_variant,
                                     self._detect_max_num_range_with_end_variant,
                                     self._detect_min_max_num_range
                                     ]

    def init_regex_for_range(self, data_directory_path):
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
        number_range_df = pd.read_csv(os.path.join(data_directory_path, NUMBER_RANGE_KEYWORD_FILE_NAME),
                                      encoding='utf-8')
        for index, row in number_range_df.iterrows():
            range_variants = get_list_from_pipe_sep_string(row[NUMBER_RANGE_FILE_VARIANTS_COLUMN_NAME])
            for variant in range_variants:
                self.range_variants_map[variant] = \
                    NumberRangeVariant(position=row[NUMBER_RANGE_FILE_POSITION_COLUMN_NAME],
                                       range_type=row[NUMBER_RANGE_FILE_RANGE_TYPE_COLUMN_NAME])

        self.min_range_start_variants = [variant for variant, value in self.range_variants_map.items()
                                         if(value.position == -1 and value.range_type == NUMBER_RANGE_MIN_TYPE)]

        self.min_range_end_variants = [variant for variant, value in self.range_variants_map.items()
                                       if(value.position == 1 and value.range_type == NUMBER_RANGE_MIN_TYPE)]

        self.max_range_start_variants = [variant for variant, value in self.range_variants_map.items()
                                         if (value.position == -1 and value.range_type == NUMBER_RANGE_MAX_TYPE)]

        self.max_range_end_variants = [variant for variant, value in self.range_variants_map.items()
                                       if (value.position == 1 and value.range_type == NUMBER_RANGE_MAX_TYPE)]

        self.min_max_range_variants = [variant for variant, value in self.range_variants_map.items()
                                       if (value.position == 0 and value.range_type == NUMBER_RANGE_MIN_MAX_TYPE)]

    def _tag_number_in_text(self, processed_text):
        """
        replace number in text with number tag from number_detected_map
        Args:
            processed_text (str): processed text
        Returns:
            tagged_number_text(str): text with number replaced with tag
        Examples:
            [In]  >>  text = 'i want to buy 3 apples and more than two bananas'
            [In]  >>  number_detected_map = {'__number__1': ({'value': '3', 'unit': None}, '3'),
                                             '__number__2': ({'value': '2', 'unit': None}, 'two')}
            [In]  >> _tag_number_in_text(text)
            [Out] >> 'i want to buy __number__1 apples and more than __number__2 bananas'
        """
        tagged_number_text = processed_text
        sorted_number_detected_map = sorted(self.number_detected_map.items(), key=lambda kv: len(kv[1][1]),
                                            reverse=True)
        for number_tag in sorted_number_detected_map:
            tagged_number_text = tagged_number_text.replace(number_tag[1][1], number_tag[0], 1)
        return tagged_number_text

    def _get_number_tag_dict(self):
        """
        Method to create number tag dict. Its run number detection on text and create a dict having number tag as key
        and value as tuple of entity value and original text.
        Returns:
            detected_number_dict(dict): dict containing number tag and their corresponding value and original text
        Examples:
            [In]  >> text = 'I want 12 dozen banana'
            [In]  >> _get_number_tag_dict()
            [Out] >> {'__number_1': ({'value': 12, 'unit': None}, '12')}
        """
        detected_number_dict = {}
        entity_value_list, original_text_list = self.language_number_detector.detect_entity(self.processed_text)
        index = 1
        for entity_value, original_text in zip(entity_value_list, original_text_list):
            detected_number_dict[NUMBER_REPLACE_TEXT + str(index)] = (entity_value, original_text)
            index = index + 1
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
            original = original.replace(number_tag, self.number_detected_map[number_tag][1])
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
            number_list (list): list containing detected numeric text
            original_list (list): list containing original numeral text

        """
        self.text = text
        self.processed_text = text
        self.tagged_text = text
        self.number_detected_map = self._get_number_tag_dict()

        number_list, original_list = None, None
        for detector in self.detector_preferences:
            self.number_tagged_processed_text = self._tag_number_in_text(self.processed_text)
            number_list, original_list = detector(number_list, original_list)
            self._update_processed_text(original_list)
        return number_list, original_list

    def _update_number_range_and_original_list(self, number_tag_min, number_tag_max, matched_text,
                                               number_range_list=None, original_list=None):
        """
        Update number_range_list and original_list by finding entity value of number tag and original text from
        number_detected_map
        Args:
            number_tag_min (str or None): tagged min number
            number_tag_max (str or None): tagged max number
            matched_text (str): text matching regex
            number_range_list (list): list containing all number range detected
            original_list (list): list containing original text of values detected
        Returns:
            number_range_list (list)
            original_list (list)
        """
        number_range_list = number_range_list or []
        original_list = original_list or []

        entity_value_min, entity_value_max, entity_unit = None, None, None

        if number_tag_min and number_tag_min in self.number_detected_map:
            entity_dict = self.number_detected_map[number_tag_min][0]
            entity_value_min = entity_dict[NUMBER_DETECTION_RETURN_DICT_VALUE]
            entity_unit = entity_dict[NUMBER_DETECTION_RETURN_DICT_UNIT]

        if number_tag_max and number_tag_max in self.number_detected_map:
            entity_dict = self.number_detected_map[number_tag_max][0]
            entity_value_max = entity_dict[NUMBER_DETECTION_RETURN_DICT_VALUE]
            entity_unit = entity_dict[NUMBER_DETECTION_RETURN_DICT_UNIT]

        original_text = self._get_original_text_from_tagged_text(matched_text)
        if entity_value_min or entity_value_max and original_text:
            original_list.append(original_text.strip())
            number_range_list.append({
                NUMBER_RANGE_MIN_VALUE: entity_value_min,
                NUMBER_RANGE_MAX_VALUE: entity_value_max,
                NUMBER_RANGE_VALUE_UNIT: entity_unit
            })
        return number_range_list, original_list

    def _detect_min_num_range_with_start_variant(self, number_range_list=None, original_list=None):
        """
        Method to detect number range containing only min value and keywords which identify value as min present
        before them. Example - More than 2 {'more than' => keyword, '2' => min value},
                               At least seven hundred rupees {'At least' => keyword, 'seven hundred rupees'=>min value}
        Args:
            number_range_list (list):
            original_list (list):
        Returns:
            number_range_list (list):
            original_list (list):
        """
        number_range_list = number_range_list or []
        original_list = original_list or []

        if self.min_range_start_variants:
            min_start_choices = "|".join(self.min_range_start_variants)
            min_range_start_regex = re.compile(r'((?:' + min_start_choices + r')\s+(' + NUMBER_REPLACE_TEXT +
                                               r'[\d+])' + r')', re.UNICODE)
            number_range_matches = min_range_start_regex.findall(self.number_tagged_processed_text)
            for match in number_range_matches:
                number_range_list, original_list = \
                    self._update_number_range_and_original_list(number_tag_min=match[1], number_tag_max=None,
                                                                matched_text=match[0],
                                                                number_range_list=number_range_list,
                                                                original_list=original_list)
        return number_range_list, original_list

    def _detect_min_num_range_with_end_variant(self, number_range_list=None, original_list=None):
        """
        Method to detect number range containing only min value and keywords which identify value as min present
        after them.
        Args:
            number_range_list (list):
            original_list (list):
        Returns:
            number_range_list (list):
            original_list (list):
        """
        number_range_list = number_range_list or []
        original_list = original_list or []

        if self.min_range_end_variants:
            min_end_choices = "|".join(self.min_range_end_variants)
            min_range_end_regex = re.compile(r'((' + NUMBER_REPLACE_TEXT + r'[\d+])\s+(?:' + min_end_choices + r'))',
                                             re.UNICODE)
            number_range_matches = min_range_end_regex.findall(self.number_tagged_processed_text)
            for match in number_range_matches:
                number_range_list, original_list = \
                    self._update_number_range_and_original_list(number_tag_min=match[1], number_tag_max=None,
                                                                matched_text=match[0],
                                                                number_range_list=number_range_list,
                                                                original_list=original_list)
        return number_range_list, original_list

    def _detect_max_num_range_with_start_variant(self, number_range_list=None, original_list=None):
        """
        Method to detect number range containing only max value and keywords which identify value as min present
        before them. Example - less than 2 {'less than' => keyword, '2' => max value},
                               At most seven hundred rupees {'At most' => keyword, 'seven hundred rupees'=>min value}
        Args:
            number_range_list (list):
            original_list (list):
        Returns:
            number_range_list (list):
            original_list (list):
        """
        number_range_list = number_range_list or []
        original_list = original_list or []

        if self.max_range_start_variants:
            max_start_choices = "|".join(self.max_range_start_variants)
            max_range_start_regex = re.compile(r'((?:' + max_start_choices + r')\s+(' + NUMBER_REPLACE_TEXT + r'[\d+])'
                                               + r')', re.UNICODE)
            number_range_matches = max_range_start_regex.findall(self.number_tagged_processed_text)
            for match in number_range_matches:
                number_range_list, original_list = \
                    self._update_number_range_and_original_list(number_tag_min=None, number_tag_max=match[1],
                                                                matched_text=match[0],
                                                                number_range_list=number_range_list,
                                                                original_list=original_list)
        return number_range_list, original_list

    def _detect_max_num_range_with_end_variant(self, number_range_list=None, original_list=None):
        """
        Method to detect number range containing only max value and keywords which identify value as min present
        after them.
        Args:
            number_range_list (list):
            original_list (list):
        Returns:
            number_range_list (list):
            original_list (list):
        """
        number_range_list = number_range_list or []
        original_list = original_list or []

        if self.max_range_end_variants:
            max_end_choices = "|".join(self.max_range_end_variants)
            max_range_end_regex = re.compile(r'((' + NUMBER_REPLACE_TEXT + r'[\d+])\s+(?:' + max_end_choices + r'))',
                                             re.UNICODE)
            number_range_matches = max_range_end_regex.findall(self.number_tagged_processed_text)
            for match in number_range_matches:
                number_range_list, original_list = \
                    self._update_number_range_and_original_list(number_tag_min=None, number_tag_max=match[1],
                                                                matched_text=match[0],
                                                                number_range_list=number_range_list,
                                                                original_list=original_list)
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
            number_range_list (list):
            original_list (list):
        """
        number_range_list = number_range_list or []
        original_list = original_list or []

        if self.min_max_range_variants:
            min_max_choices = "|".join(self.min_max_range_variants)
            min_max_range_regex = re.compile(r'((' + NUMBER_REPLACE_TEXT + r'[\d+])\s*(?:' + min_max_choices + r')\s*('
                                             + NUMBER_REPLACE_TEXT + r'[\d+]))', re.UNICODE)
            number_range_matches = min_max_range_regex.findall(self.number_tagged_processed_text)
            for match in number_range_matches:
                number_range_list, original_list = \
                    self._update_number_range_and_original_list(number_tag_min=match[1], number_tag_max=match[2],
                                                                matched_text=match[0],
                                                                number_range_list=number_range_list,
                                                                original_list=original_list)
        return number_range_list, original_list

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


class NumberRangeDetector(BaseNumberRangeDetector):
    def __init__(self, entity_name, language, data_directory_path, unit_type=None):
        super(NumberRangeDetector, self).__init__(entity_name=entity_name,
                                                  language=language,
                                                  data_directory_path=data_directory_path,
                                                  unit_type=unit_type)
