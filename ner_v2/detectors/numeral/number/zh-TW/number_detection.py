from __future__ import absolute_import
import os

try:
    import regex as re

    _re_flags = re.UNICODE | re.V1 | re.WORD
except ImportError:
    import re

    _re_flags = re.UNICODE

from ner_v2.constant import LANGUAGE_DATA_DIRECTORY
from ner_v2.detectors.numeral.constant import NUMBER_DETECTION_RETURN_DICT_SPAN, NUMBER_DETECTION_RETURN_DICT_UNIT, NUMBER_DETECTION_RETURN_DICT_VALUE
from ner_v2.detectors.numeral.number.standard_number_detector import BaseNumberDetector

from chatbot_ner.config import ner_logger

class NumberDetector(BaseNumberDetector):
    data_directory_path = os.path.join((os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep)),
                                       LANGUAGE_DATA_DIRECTORY)

    def __init__(self, entity_name='number', unit_type=None):
        super(NumberDetector, self).__init__(entity_name=entity_name,
                                             data_directory_path=NumberDetector.data_directory_path,
                                             unit_type=unit_type)

        ner_logger.debug(f'>>> Chinese Number Detector : Here <<<')
        ner_logger.debug(f'>>> Units map : {self.units_map}')
        
        self._filter_base_numbers_map()

        sorted_len_base_number_keys = sorted(list(self.base_numbers_map.keys()))
        self.base_numbers_map_choices = "|".join([re.escape(x) for x in sorted_len_base_number_keys])
        
        ner_logger.debug(f' base number choices : {self.base_numbers_map_choices}')
        self.detector_preferences = [
            self._detect_number_digit_by_digit,
            self._detect_number_from_digit,
            # self._detect_number_from_words
        ]


    def _filter_base_numbers_map(self):
        new_base_numbers_map = {}
        for k,v in self.base_numbers_map.items():
            if 0 <= v <= 9:
                new_base_numbers_map[k] = v
        self.base_numbers_map = new_base_numbers_map
    
    def _detect_number_digit_by_digit(self,number_list=None, original_list=None):
        number_list = number_list or []
        original_list = original_list or []
        start_span = 0
        end_span = -1
        spanned_text = self.processed_text
        processed_text = self.processed_text

        regex_digit_patterns = re.compile(r'([' + self.base_numbers_map_choices + r']+\s?)')

        patterns = regex_digit_patterns.findall(self.processed_text)
        for pattern in patterns:
            non_latin, latin_number, original_text = None, None, None

            if pattern:
                original_text = pattern.strip().strip(',.').strip()
                span = re.search(original_text, spanned_text).span()
                start_span = end_span + span[0]
                end_span += span[1]
                spanned_text = spanned_text[span[1]:]
                non_latin = original_text
                number  = ''.join([str(self.base_numbers_map.get(_t,_t)) for _t in pattern ])
                
                if number.isnumeric():
                    latin_number = number
            
            if latin_number:
                _pattern = re.compile(self._SPAN_BOUNDARY_TEMPLATE.format(re.escape(original_text)), flags=_re_flags)
                if _pattern.search(processed_text):
                    processed_text = _pattern.sub(self.tag, processed_text, 1)
                    number_list.append({
                        NUMBER_DETECTION_RETURN_DICT_VALUE: str(latin_number),
                        NUMBER_DETECTION_RETURN_DICT_UNIT: None,
                        NUMBER_DETECTION_RETURN_DICT_SPAN: (start_span, end_span)
                    })
                    original_list.append(original_text)

        return number_list, original_list



    
