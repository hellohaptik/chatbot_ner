from __future__ import absolute_import
import re
import os

from ner_v2.constant import LANGUAGE_DATA_DIRECTORY
from ner_v2.detectors.numeral.constant import NUMBER_DETECTION_RETURN_DICT_UNIT, NUMBER_DETECTION_RETURN_DICT_VALUE
from ner_v2.detectors.numeral.number.standard_number_detector import BaseNumberDetector


class NumberDetector(BaseNumberDetector):
    data_directory_path = os.path.join((os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep)),
                                       LANGUAGE_DATA_DIRECTORY)

    def __init__(self, entity_name='number', unit_type=None):
        super(NumberDetector, self).__init__(entity_name=entity_name,
                                             data_directory_path=NumberDetector.data_directory_path,
                                             unit_type=unit_type)

        if entity_name in ['number_of_people', 'number_of_ticket', 'no_of_guests', 'no_of_adults',
                           'travel_no_of_people']:
            self.detector_preferences = [
                self._custom_detect_number_of_people_format,
                self._detect_number_from_digit,
                self._detect_number_from_words
            ]

    def _custom_detect_number_of_people_format(self, number_list=None, original_list=None):
        """Detects any numbers from text
        This is a function which will be called when we want to detect the number of persons from the text

        Returns:
            A tuple of two lists with first list containing the detected numbers and second list containing their
            corresponding substrings in the original message.

            For example:
                input text: "Can you please help me to book tickets for 3 people"
                output: (['3'], ['for 3 people'])

        Note: Currently, we can detect numbers from 1 digit to 3 digit. This function will be enabled only
        if entity_name is set to  'number_of_people'
        """
        number_list = number_list or []
        original_list = original_list or []
        patterns = re.findall(r'\s((fo?r\s+)?([0-9]+)\s*(ppl|people|passengers?|travellers?|persons?|pax|adults?))\s',
                              self.processed_text.lower())
        for pattern in patterns:
            number_list.append({
                NUMBER_DETECTION_RETURN_DICT_VALUE: pattern[2],
                NUMBER_DETECTION_RETURN_DICT_UNIT: 'people'
            })
            original_list.append(pattern[0])

        return number_list, original_list
