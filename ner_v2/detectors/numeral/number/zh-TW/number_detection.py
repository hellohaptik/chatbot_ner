from __future__ import absolute_import
import os

try:
    import regex as re

    _re_flags = re.UNICODE | re.V1 | re.WORD
except ImportError:
    import re

    _re_flags = re.UNICODE

from ner_v2.constant import LANGUAGE_DATA_DIRECTORY
from ner_v2.detectors.numeral.constant import NUMBER_DETECTION_RETURN_DICT_SPAN, \
    NUMBER_DETECTION_RETURN_DICT_UNIT, NUMBER_DETECTION_RETURN_DICT_VALUE
from ner_v2.detectors.numeral.number.standard_number_detector import BaseNumberDetector

class NumberDetector(BaseNumberDetector):
    """
    Number detector to detect numbers in chinese text
    It map the chinese to latin character as per data file and extract the numeric values
    """

    data_directory_path = os.path.join((os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep)),
                                       LANGUAGE_DATA_DIRECTORY)

    def __init__(self, entity_name='number', unit_type=None):
        super(NumberDetector, self).__init__(entity_name=entity_name,
                                             data_directory_path=NumberDetector.data_directory_path,
                                             unit_type=unit_type)

        self.base_numbers_map_full = self.base_numbers_map.copy()
        self.base_numbers_map_choices_full = self._get_base_map_choices(self.base_numbers_map_full)

        self._filter_base_numbers_map()
        self.base_numbers_map_choices = self._get_base_map_choices(self.base_numbers_map)

        self.detector_preferences = [
            self._detect_number_from_text
        ]

        self.special_chars_mapping = {
            ',': '、',
            '.': '點',
            '+': '加'
        }

        self.power_of_10 = { 10 ** i for i in range(1,17)}

    def _get_base_map_choices(self, base_map):
        number_set = set()
        for key, val in base_map.items():
            number_set.add(str(key))
            number_set.add(str(val))

        sorted_len_base_number_key_vals = sorted(list(number_set))
        return "|".join([re.escape(x) for x in sorted_len_base_number_key_vals])

    def _filter_base_numbers_map(self):
        """
        Only require the chinese digits mapping for digit from 0 to 9
        """
        new_base_numbers_map = {}
        for k, v in self.base_numbers_map.items():
            if 0 <= v <= 9:
                new_base_numbers_map[k] = v
        self.base_numbers_map = new_base_numbers_map

    def _have_digits_only(self, text=None, scale_map=None):
        text = text or ''
        scale_map = scale_map or {}

        scaling_digits = set(list(scale_map.keys()))
        only_digits = True
        for _digit in text:
            if _digit in scaling_digits:
                only_digits = False
                break
        return only_digits

    def replace_special_chars(self, text=None):
        text = text or ''
        for _char, _native_char in self.special_chars_mapping.items():
            text = text.replace(_native_char, _char)
        return text

    def _detect_number_from_text(self, number_list=None, original_list=None):
        """
        extract out the numbers from chinese text ( roman as well as chinese )
        """
        number_list = number_list or []
        original_list = original_list or []
        start_span = 0
        end_span = -1

        # removing hyphen
        self.processed_text = re.sub(r'[-]+', '', self.processed_text)

        spanned_text = self.processed_text
        processed_text = self.processed_text

        # need to handle decimal points as well
        rgx_pattern = r'([{}]+)({}?([{}]*))'.format(
            self.base_numbers_map_full,
            self.special_chars_mapping.get('.', '.'),
            self.base_numbers_map_full
        )
        regex_digit_patterns = re.compile(rgx_pattern)
        patterns = regex_digit_patterns.findall(self.processed_text)
        for pattern in patterns:
            full_number, number, original_text = None, None, None
            if pattern[0].strip():
                original_text = pattern[0].strip()
                span = re.search(original_text, spanned_text).span()
                start_span = end_span + span[0]
                end_span += span[1]
                spanned_text = spanned_text[span[1]:]
                number = self.get_number(original_text)
                if number.isnumeric():
                    full_number = number

            if full_number:
                _pattern = re.compile(re.escape(original_text), flags=_re_flags)
                if _pattern.search(processed_text):
                    processed_text = _pattern.sub(self.tag, processed_text, 1)
                    number_list.append({
                        NUMBER_DETECTION_RETURN_DICT_VALUE: int(full_number),
                        NUMBER_DETECTION_RETURN_DICT_UNIT: None,
                        NUMBER_DETECTION_RETURN_DICT_SPAN: (start_span, end_span)
                    })
                    original_list.append(original_text)
        return number_list, original_list

    def get_number(self, original_text):
        original_text = original_text.strip()
        if self._have_digits_only(original_text, self.scale_map):
            return self.get_number_digit_by_digit(original_text)
        return self.get_number_with_digit_scaling(original_text)

    def extract_digits_only(self, text, rgx_pattern=None, with_special_chars=False, with_scale=False):
        text = text or ''
        rgx_pattern = rgx_pattern or r'[-,.+\s{}]+'
        digit_choices = self.base_numbers_map_choices_full if with_scale else self.base_numbers_map_choices
        if with_special_chars:
            digit_choices += '|'.join(self.special_chars_mapping.values())
        rgx_pattern = re.compile(rgx_pattern.format(digit_choices))
        return rgx_pattern.findall(text)

    def get_number_digit_by_digit(self, text=''):
        return ''.join([str(self.base_numbers_map.get(_t, _t)) for _t in text])

    def get_number_with_digit_scaling(self, text=''):
        # change the below logic to work with scaling
        result = ''
        if not text:
            return result

        # extract the digits and scales from the text
        digit_list = []

        pwr_index_map = {}
        for t in text:
            digit_val = self.base_numbers_map_full.get(t)
            if digit_val == None:
                return result
            else:
                digit_list.append(digit_val)
                if digit_val in self.power_of_10:
                    pwr_index_map[digit_val] = len(digit_list) - 1
        if len(digit_list) == 0:
            return result

        pwr_index_map[1] = len(digit_list)

        # starting from highest power aggregate digit and scales
        pwr_index_list = sorted(pwr_index_map.items(), key= lambda kv : kv[0], reverse=True)

        st = 0
        final_val = 0
        for pwr, indx in pwr_index_list:
            value = self.combine_digit_and_scale(digit_list[ st : indx])
            st = indx + 1
            if value != None:
                value = value * pwr
                final_val += value

        result = str(final_val)
        return result

    def combine_digit_and_scale(self, num_list: None):
        """
        params : list of numbers either digit or scale
        return : int
        example :
            [ 2, 1000, 5, 100, 3, 10, 8 ]
            output : 2538
        """
        value = None
        num_list = num_list or []

        if len(num_list) == 0:
            return value

        digit_scaled_list = [1]
        start_index = 0
        if num_list[0] not in self.power_of_10:
            start_index = 1
            digit_scaled_list[0] = num_list[0]

        zero_found = False
        for i in range(start_index, len(num_list)):
            x = num_list[i]
            if x == 0:
                zero_found = True
                continue
            if x in self.power_of_10:
                digit_scaled_list[-1] = digit_scaled_list[-1] * x
            else:
                digit_scaled_list.append(x)
        value = sum(digit_scaled_list)
        if (value == 0) and ( zero_found == False):
            value = None
        return value