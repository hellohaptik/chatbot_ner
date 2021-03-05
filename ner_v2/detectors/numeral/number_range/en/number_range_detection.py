from __future__ import absolute_import

import re
import os

from ner_v2.constant import LANGUAGE_DATA_DIRECTORY
from ner_v2.detectors.numeral.constant import NUMBER_REPLACE_TEXT
from ner_v2.detectors.numeral.number_range.standard_number_range_detector import BaseNumberRangeDetector


class NumberRangeDetector(BaseNumberRangeDetector):
    data_directory_path = os.path.join((os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep)),
                                       LANGUAGE_DATA_DIRECTORY)

    def __init__(self, entity_name, language, unit_type=None):
        super(NumberRangeDetector, self).__init__(entity_name=entity_name,
                                                  language=language,
                                                  data_directory_path=NumberRangeDetector.data_directory_path,
                                                  unit_type=unit_type)

        self.detector_preferences = [self._detect_min_max_num_range,
                                     self._custom_num_range_between_num_and_num,
                                     self._detect_min_num_range_with_prefix_variants,
                                     self._detect_min_num_range_with_suffix_variants,
                                     self._detect_max_num_range_with_prefix_variants,
                                     self._detect_max_num_range_with_suffix_variants,
                                     self._detect_absolute_number]

    def _custom_num_range_between_num_and_num(self, number_range_list=None, original_list=None):
        """Detects number range of text of pattern between number1 to number2
        This is a custom created patterns which will be called after all the standard detector will ran.

        Returns:
            A tuple of two lists with first list containing the detected number ranges and second list
            containing their corresponding substrings in the original message.

            For example:
                input text: "my salary range is between 2000 to 3000"
                output: ([{'min_value': '2000', 'max_value': '3000', 'unit': None}], ['between 2000 to 3000'])

        """
        number_range_list = number_range_list or []
        original_list = original_list or []
        between_range_pattern = re.compile(r'(between\s+({number}\d+__)\s+(?:and|-)'
                                           r'\s+({number}\d+__))'.format(number=NUMBER_REPLACE_TEXT), re.UNICODE)
        number_range_matches = between_range_pattern.findall(self.processed_text)
        for match in number_range_matches:
            number_range, original_text = self._get_number_range(min_part_match=match[1], max_part_match=match[2],
                                                                 full_match=match[0])
            if number_range and original_text:
                number_range_list.append(number_range)
                original_list.append(original_text)

        return number_range_list, original_list
