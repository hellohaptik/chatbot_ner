from __future__ import absolute_import
import re
import os

from ner_v2.detectors.temporal.constant import TYPE_EXACT
from ner_v2.detectors.temporal.date.standard_date_regex import BaseRegexDate
from ner_v2.constant import LANGUAGE_DATA_DIRECTORY


class DateDetector(BaseRegexDate):
    data_directory_path = os.path.join((os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep)),
                                       LANGUAGE_DATA_DIRECTORY)

    def __init__(self, entity_name, locale=None, timezone='UTC', past_date_referenced=False):
        super(DateDetector, self).__init__(entity_name,
                                           data_directory_path=DateDetector.data_directory_path,
                                           timezone=timezone,
                                           past_date_referenced=past_date_referenced)
        self.detector_preferences = [
            self._gregorian_day_month_year_format,
            self._detect_relative_date,
            self._detect_date_month,
            self._detect_date_ref_month_1,
            self._detect_date_ref_month_2,
            self._detect_date_ref_month_3,
            self._detect_date_diff,
            self._detect_after_days,
            self._detect_weekday_ref_month_1,
            self._detect_weekday_ref_month_2,
            self._detect_weekday_diff,
            self._detect_weekday,
            self.custom_christmas_date_detector
        ]

    def custom_christmas_date_detector(self, date_list=None, original_list=None):
        """
        Method to detect chritmast
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected
        Examples:
            >> self.processed_text = 'christmas'
            >> self.custom_christmas_date_detector()
            >> [{'dd': 25, 'mm': 12, 'yy': 2018, 'type': 'exact_date'}], ['christmas']
        """
        date_list = date_list or []
        original_list = original_list or []

        christmas_regex = re.compile(r'((christmas|xmas|x-mas|chistmas))')
        day_match = christmas_regex.findall(self.processed_text)
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
