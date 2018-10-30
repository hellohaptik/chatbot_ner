from ner_v2.detectors.temporal.constant import LANGUAGE_DATA_DIRECTORY
from ner_v2.detectors.temporal.date.standard_regex_date import BaseRegexDate
import os
import re


class DateDetector(BaseRegexDate):
    def __init__(self, entity_name, timezone='UTC'):

        data_directory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep),
                                           LANGUAGE_DATA_DIRECTORY)
        super(DateDetector, self).__init__(entity_name=entity_name, timezone=timezone,
                                           data_directory_path=data_directory_path)

        self.custom_detectors = [self.custom_chritmast_date_detector]

    def custom_chritmast_date_detector(self, date_list=None, original_list=None):
        """
        Method to detect chritmast
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected

        """
        date_list = date_list or []
        original_list = original_list or []

        chritmas_regex = re.compile(r'((chritmas|xmas|x-mas|chistmas))')
        day_match = chritmas_regex.findall(self.processed_text)
        for match in day_match:
            original = match[0]
            date = {
                'dd': 25,
                'mm': 12,
                'yy': self.now_date.year
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def detect_date(self, text):
        """
        Detects exact date for complete date information - day, month, year are available in text
        and possible dates for if there are missing parts of date - day, month, year assuming sensible defaults.

        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.
        """

        self.text = text
        self.processed_text = self.text
        self.tagged_text = self.text

        date_list, original_list  = self._detect_date_from_standard_regex()

        # run custom date detectors
        for detector in self.custom_detectors:
            date_list, original_list = detector(date_list, original_list)
            self._update_processed_text(original_list)

        return date_list, original_list
