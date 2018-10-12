from chatbot_ner.config import ner_logger
from ner_v2.detectors.temporal.date.BaseRegexDate import BaseRegexDate
import pytz


class DateDetector(BaseRegexDate):
    def __init__(self):
        super(DateDetector, self).__init__()
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.date = []
        self.original_date_text = []
        self.month_dictionary = {}
        self.day_dictionary = {}
        self.entity_name = entity_name
        self.tag = '__' + entity_name + '__'
        try:
            self.timezone = pytz.timezone(timezone)
        except Exception as e:
            ner_logger.debug('Timezone error: %s ' % e)
            self.timezone = pytz.timezone('UTC')
            ner_logger.debug('Default timezone passed as "UTC"')
        self.now_date = datetime.datetime.now(tz=self.timezone)
        self.month_dictionary = MONTH_DICT
        self.day_dictionary = DAY_DICT
        self.bot_message = None

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
        date_list, original_list = self.get_exact_date(date_list, original_list)
        date_list, original_list = self.get_possible_date(date_list, original_list)
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

    def get_exact_date(self, date_list, original_list):
        """
        Detects exact date if complete date information - day, month, year are available in text.
        Also detects "today", "tomorrow", "yesterday", "day after tomorrow", "day before yesterday",
        "day in next week" and their variants/ synonyms and returns their dates as these can have exactly one date
        they refer to. Type of dates returned by this method include TYPE_NORMAL, TYPE_TODAY, TYPE_TOMORROW,
        TYPE_DAY_AFTER, TYPE_DAY_BEFORE, TYPE_YESTERDAY, TYPE_NEXT_DAY

        Args:
            date_list: Optional, list to store dictionaries of detected date entities
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities

        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        date_list, original_list = self._gregorian_day_month_year_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_month_day_year_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_year_month_day_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_advanced_day_month_year_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._day_month_format_for_arrival_departure(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_day_with_ordinals_month_year_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_advanced_year_month_day_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_year_day_month_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_month_day_with_ordinals_year_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_day_month_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_month_day_format(date_list, original_list)
        self._update_processed_text(original_list)

        date_list, original_list = self._day_after_tomorrow(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_days_after(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_days_later(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._day_before_yesterday(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._todays_date(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._tomorrows_date(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._yesterdays_date(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._day_in_next_week(date_list, original_list)
        self._update_processed_text(original_list)

        return date_list, original_list