from chatbot_ner.config import ner_logger
from ner_v2.detectors.temporal.constant import TAGGED_DATE, ORIGINAL_DATE_TEXT
from ner_v2.detectors.temporal.date.BaseRegexDate import BaseRegexDate
import datetime
import pytz
from chatbot_ner.config import BASE_DIR
from ner_v2.detectors.temporal.datetime_tagger import HindiDateTimeTagger


class DateDetector(BaseRegexDate):
    def __init__(self, entity_name, timezone='UTC'):

        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.date = []
        self.original_date_text = []
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
        data_directory_path = BASE_DIR.rstrip('/') + '/' + 'ner_v2/detector/temporal/date/hi/data/'

        self.date_tagger = HindiDateTimeTagger(data_directory_path)
        super(DateDetector, self).__init__(data_directory_path=data_directory_path)

    def detect_entity(self, text):
        """
        Detects all date strings in text and returns two lists of detected date entities and their corresponding
        original substrings in text respectively.

        Args:
            text: string to extract date entities from

        Returns:
            Tuple containing two lists, first containing dictionaries, containing
            date values as 'dd', 'mm', 'type', 'yy' for each detected date, and second list containing corresponding
            substrings in given for entity detection

            Examples:
                date_detector = DateDetector("date")
                date_detector.detect_entity('Remind me everyday')

                date_detector.tagged_text


        Additionally this function assigns these lists to self.date and self.original_date_text attributes
        respectively.

        """

        self.text = ' ' + text.lower() + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        self.date, self.original_date_text = self._detect_date()
        return self.date, self.original_date_text

    def _detect_date(self):
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
        date_list = []
        original_list = []
        date_tagged_dict = self.date_tagger.get_datetime_tagged(self.processed_text)
        if not date_tagged_dict.get(TAGGED_DATE):
            return date_list, original_list

        tagged_text_list = date_tagged_dict.get(TAGGED_DATE)
        original_text_list = date_tagged_dict.get(ORIGINAL_DATE_TEXT)

        date_list, original_list = self.get_exact_date(tagged_text_list, original_text_list)
        validated_date_list, validated_original_list = [], []

        # Note: Following leaves tagged text incorrect but avoids returning invalid dates like 30th Feb
        for date, original_text in zip(date_list, original_list):
            try:
                datetime.date(year=date['yy'], month=date['mm'], day=date['dd'])
                validated_date_list.append(date)
                validated_original_list.append(original_text)
            except ValueError:
                pass

        return validated_date_list, validated_original_list

    def get_exact_date(self, tagged_text_list, original_text_list):
        """
        Detects exact date if complete date information - day, month, year are available in text.
        Also detects "today", "tomorrow", "yesterday", "day after tomorrow", "day before yesterday",
        "day in next week" and their variants/ synonyms and returns their dates as these can have exactly one date
        they refer to. Type of dates returned by this method include TYPE_NORMAL, TYPE_TODAY, TYPE_TOMORROW,
        TYPE_DAY_AFTER, TYPE_DAY_BEFORE, TYPE_YESTERDAY, TYPE_NEXT_DAY

        Args:
            tagged_text_list: Optional, list to store dictionaries of detected date entities
            original_text_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities

        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        date_list, original_list = [], []
        for tagged_text, original_text in zip(tagged_text_list, original_text_list):
            detect_date = self._detect_date_from_standard_regex(tagged_text)
            if detect_date:
                date_list.append(detect_date)
                original_list.append(original_text)
        return date_list, original_list
