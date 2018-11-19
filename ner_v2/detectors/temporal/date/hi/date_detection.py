import re

import os

from ner_v2.constant import TYPE_EXACT
from ner_v2.detectors.temporal.date.date_detection import get_lang_data_path
from ner_v2.detectors.temporal.date.standard_date_regex import BaseRegexDate


class DateDetector(BaseRegexDate):
    data_directory_path = get_lang_data_path(os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep))

    def __init__(self, entity_name, timezone='UTC', past_date_referenced=False):
        super(DateDetector, self).__init__(entity_name,
                                           data_directory_path=DateDetector.data_directory_path,
                                           timezone=timezone,
                                           past_date_referenced=past_date_referenced)
        self.detector_preferences = [
            self._detect_relative_date,
            self._detect_date_month,
            self._detect_date_ref_month_1,
            self._detect_date_ref_month_2,
            self._detect_date_ref_month_3,
            self.custom_christmas_date_detector,
            self._detect_date_diff,
            self._detect_after_days,
            self._detect_weekday_ref_month_1,
            self._detect_weekday_ref_month_2,
            self._detect_weekday_diff,
            self._detect_weekday
        ]

    def custom_christmas_date_detector(self, date_list=None, original_list=None):
        """
        Method to detect chritmast
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected

        """
        date_list = date_list or []
        original_list = original_list or []

        chritmas_regex = re.compile(r'((christmas|xmas|x-mas|chistmas))')
        day_match = chritmas_regex.findall(self.processed_text)
        for match in day_match:
            original = match[0]
            date = {
                'dd': 25,
                'mm': 12,
                'yy': self.now_date.year,
                'type': TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list
