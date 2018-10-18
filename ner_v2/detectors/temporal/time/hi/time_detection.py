from chatbot_ner.config import ner_logger
from ner_v2.detectors.temporal.constant import LANGUAGE_DATA_DIRECTORY
import datetime
import pytz
import os

from ner_v2.detectors.temporal.time.standard_time_regex import BaseRegexTime


class TimeDetector(BaseRegexTime):
    def __init__(self, entity_name, timezone='UTC'):

        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.entity_name = entity_name
        self.tag = '__' + entity_name + '__'
        try:
            self.timezone = pytz.timezone(timezone)
        except Exception as e:
            ner_logger.debug('Timezone error: %s ' % e)
            self.timezone = pytz.timezone('UTC')
            ner_logger.debug('Default timezone passed as "UTC"')
        self.now_date = datetime.datetime.now(tz=self.timezone)
        self.bot_message = None
        data_directory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep),
                                           LANGUAGE_DATA_DIRECTORY)

        super(TimeDetector, self).__init__(data_directory_path=data_directory_path)

    def detect_time(self, text):
        """
        Detects exact date for complete date information - day, month, year are available in text
        and possible dates for if there are missing parts of date - day, month, year assuming sensible defaults. Also
        detects "today", "tomorrow", "yesterday", "everyday", "day after tomorrow", "day before yesterday",
        "only weekdays", "only weekends", "day in next week", "day A to day B", "month A to month B" ranges
        and their variants/synonyms

        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.
        """

        self.text = text
        self.processed_text = self.text
        self.tagged_text = self.text

        time_list, original_text_list = self._detect_time_from_standard_regex()

        return time_list, original_text_list
