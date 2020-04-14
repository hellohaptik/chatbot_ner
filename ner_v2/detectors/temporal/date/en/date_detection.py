from __future__ import absolute_import
import copy
import datetime
import re

from ner_v2.detectors.temporal.constant import (TYPE_EXACT, TYPE_EVERYDAY, TYPE_TODAY, TYPE_TOMORROW, TYPE_YESTERDAY,
                                                TYPE_DAY_AFTER, TYPE_DAY_BEFORE, TYPE_N_DAYS_AFTER, TYPE_NEXT_DAY,
                                                TYPE_THIS_DAY, TYPE_POSSIBLE_DAY, WEEKDAYS,
                                                REPEAT_WEEKDAYS, WEEKENDS, REPEAT_WEEKENDS, TYPE_REPEAT_DAY,
                                                MONTH_DICT, DAY_DICT, ORDINALS_MAP)
from ner_v2.detectors.temporal.utils import (get_weekdays_for_month, get_next_date_with_dd, get_previous_date_with_dd,
                                             get_timezone)
from six.moves import zip


class DateDetector(object):
    """
    Detects date in various formats from given text and tags them.

    Detects all date entities in given text and replaces them by entity_name.
    Additionally detect_entity() method returns detected date values in dictionary containing values for day (dd),
    month (mm), year (yy), type (exact, possible, everyday, weekend, range etc.)

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected date entities would be replaced with on calling detect_entity()
        tagged_text: string with date entities replaced with tag defined by entity name
        processed_text: string with detected date entities removed
        date: list of date entities detected
        original_date_text: list to store substrings of the text detected as date entities
        tag: entity_name prepended and appended with '__'
        timezone: Optional, pytz.timezone object used for getting current time, default is pytz.timezone('UTC')
        locale: Optional, locale of the user for getting country code
        now_date: datetime object holding timestamp while DateDetector instantiation
        month_dictionary: dictonary mapping month indexes to month spellings and
                          fuzzy variants(spell errors, abbreviations)
        day_dictionary: dictonary mapping day indexes to day of week spellings and
        fuzzy variants(spell errors, abbreviations)
        bot_message: str, set as the outgoing bot text/message

        SUPPORTED_FORMAT                                            METHOD_NAME
        ------------------------------------------------------------------------------------------------------------
        1. day/month/year                                           _gregorian_day_month_year_format
        2. month/day/year                                           _gregorian_month_day_year_format
        3. year/month/day                                           _gregorian_year_month_day_format
        4. day/month/year (Month in abbreviation or full)           _gregorian_advanced_day_month_year_format
        5. Xth month year (Month in abbreviation or full)           _gregorian_day_with_ordinals_month_year_format
        6. year month Xth (Month in abbreviation or full)           _gregorian_advanced_year_month_day_format
        7. year Xth month (Month in abbreviation or full)           _gregorian_year_day_month_format
        8. month Xth year (Month in abbreviation or full)           _gregorian_month_day_with_ordinals_year_format
        9. month Xth      (Month in abbreviation or full)           _gregorian_month_day_format
        10. Xth month      (Month in abbreviation or full)          _gregorian_day_month_format
        11."today" variants                                         _todays_date
        12."tomorrow" variants                                      _tomorrows_date
        13."yesterday" variants                                     _yesterdays_date
        14."_day_after_tomorrow" variants                           _day_after_tomorrow
        15."_day_before_yesterday" variants                         _day_before_yesterday
        16."next <day of week>" variants                            _day_in_next_week
        17."this <day of week>" variants                            _day_within_one_week
        18.probable date from only Xth                              _date_identification_given_day
        19.probable date from only Xth this month                   _date_identification_given_day_and_current_month
        20.probable date from only Xth next month                   _date_identification_given_day_and_next_month
        21."everyday" variants                                      _date_identification_everyday
        22."everyday except weekends" variants                      _date_identification_everyday_except_weekends
        23."everyday except weekdays" variants                       _date_identification_everyday_except_weekdays
        24."every monday" variants                                  _weeks_identification
        25."after n days" variants                                  _date_days_after
        26."n days later" variants                                  _date_days_later

        Not all separator are listed above. See respective methods for detail on structures of these formats

    Note:
        text and tagged_text will have a extra space prepended and appended after calling detect_entity(text)
    """

    def __init__(self, entity_name, locale=None, timezone='UTC', past_date_referenced=False):
        """Initializes a DateDetector object with given entity_name and pytz timezone object

        Args:
            entity_name: A string by which the detected date entity substrings would be replaced with on calling
                        detect_entity()
            timezone (Optional, str): timezone identifier string that is used to create a pytz timezone object
                                      default is UTC
            past_date_referenced (bool): to know if past or future date is referenced for date text like 'kal', 'parso'
            locale (Optional, str): user locale for getting the country code.

        """
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.date = []
        self.original_date_text = []
        self.month_dictionary = {}
        self.day_dictionary = {}
        self.entity_name = entity_name
        self.tag = '__' + entity_name + '__'
        self.timezone = get_timezone(timezone)
        self.now_date = datetime.datetime.now(tz=self.timezone)
        self.month_dictionary = MONTH_DICT
        self.day_dictionary = DAY_DICT
        self.bot_message = None
        self.locale = locale
        self.country_code = None
        self.past_date_referenced = past_date_referenced
        self.default_detector_preferences = [self._gregorian_day_month_year_format,
                                             self._gregorian_month_day_year_format,
                                             self._gregorian_year_month_day_format,
                                             self._gregorian_advanced_day_month_year_format,
                                             self._day_month_format_for_arrival_departure,
                                             self._date_range_ddth_of_mmm_to_ddth,
                                             self._date_range_ddth_to_ddth_of_next_month,
                                             self._gregorian_day_with_ordinals_month_year_format,
                                             self._gregorian_advanced_year_month_day_format,
                                             self._gregorian_year_day_month_format,
                                             self._gregorian_month_day_with_ordinals_year_format,
                                             self._gregorian_day_month_format,
                                             self._gregorian_month_day_format,
                                             self._day_after_tomorrow,
                                             self._date_days_after,
                                             self._date_days_later,
                                             self._day_before_yesterday,
                                             self._todays_date,
                                             self._tomorrows_date,
                                             self._yesterdays_date,
                                             self._day_in_next_week,
                                             self._day_range_for_nth_week_month
                                             ]
        """
        Rules to add new country code preferences:
        1. Create a new key with country code.
        2. Add all the methods which should be given higher preference in a list with the
           most preferred method first.
        3. Warning: Be careful about the order in which you set your preferences.
            For EX: If you set `self._gregorian_day_month_format` at a higher preference than
            `self._gregorian_advanced_day_month_year_format`, only `22nd MAR` will be detected in  `22nd MAR 2034`.
        """
        self.country_date_detector_preferences = {
            'US': [self._gregorian_month_day_year_format],
            'IN': [self._gregorian_day_month_year_format],
        }

    def get_country_code_from_locale(self):
        """
        Extracts locale from country code.
        Ex: locale:'en_us' sets,
            self.country_code = 'US'
        """
        regex_pattern = re.compile('[-_](.*$)', re.U)
        match = regex_pattern.findall(self.locale)
        if match:
            return match[0].upper()
        else:
            return None

    def detect_date(self, text):
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
        self.text = " " + text.strip().lower() + " "
        self.processed_text = self.text
        self.tagged_text = self.text
        if self.locale:
            self.country_code = self.get_country_code_from_locale()
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
        if self.country_code and self.country_code in self.country_date_detector_preferences:
            for preferred_detector in self.country_date_detector_preferences[self.country_code]:
                date_list, original_list = preferred_detector(date_list, original_list)
                self._update_processed_text(original_list)
            for detector in self.default_detector_preferences:
                if detector not in self.country_date_detector_preferences[self.country_code]:
                    date_list, original_list = detector(date_list, original_list)
                    self._update_processed_text(original_list)
        else:
            for detector in self.default_detector_preferences:
                date_list, original_list = detector(date_list, original_list)
                self._update_processed_text(original_list)

        return date_list, original_list

    def get_possible_date(self, date_list=None, original_list=None):
        """
        Detects possible dates for if there are missing parts of date - day, month, year assuming sensible defaults.
        Also detects "everyday","only weekdays", "only weekends","A to B" type ranges in days of week or months,
        and their variants/ synonyms and returns probable dates by using current year, month, week defaults for parts
        of dates that are missing or that include relative ranges. Type of dates returned by this method include
        TYPE_POSSIBLE_DAY, TYPE_REPEAT_DAY, TYPE_THIS_DAY, REPEAT_WEEKDAYS, REPEAT_WEEKENDS, START_RANGE, END_RANGE,
        REPEAT_START_RANGE, REPEAT_END_RANGE, DATE_START_RANGE, DATE_END_RANGE, WEEKDAYS, WEEKENDS .

        Args:
            date_list: Optional, list to store dictionaries of detected date entities
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities

        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        date_list, original_list = self._date_identification_given_day_and_current_month(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_identification_given_day_and_next_month(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_identification_given_day(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_identification_everyday_except_weekends(date_list, original_list,
                                                                                      n_days=15)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_identification_everyday_except_weekdays(date_list, original_list,
                                                                                      n_days=50)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_identification_everyday(date_list, original_list, n_days=15)
        self._update_processed_text(original_list)
        date_list, original_list = self._day_within_one_week(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._weeks_identification(date_list, original_list)
        self._update_processed_text(original_list)

        return date_list, original_list

    def _update_processed_text(self, original_date_strings):
        """
        Replaces detected date entities with tag generated from entity_name used to initialize the object with

        A final string with all date entities replaced will be stored in object's tagged_text attribute
        A string with all date entities removed will be stored in object's processed_text attribute

        Args:
            original_date_strings: list of substrings of original text to be replaced with tag created from entity_name
        """
        for detected_text in original_date_strings:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')

    def _gregorian_day_month_year_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <day><separator><month><separator><year>
        where each part is in of one of the formats given against them
            day: d, dd
            month: m, mm
            year: yy, yyyy
            separator: "/", "-", "."

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "6/2/39", "7/01/1997", "28-12-2096"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'[^/\-\.\w](([12][0-9]|3[01]|0?[1-9])\s?[/\-\.]\s?(1[0-2]|0?[1-9])'
                                   r'(?:\s?[/\-\.]\s?((?:20|19)?[0-9]{2}))?)\W')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd = int(pattern[1])
            mm = int(pattern[2])
            yy = int(self.normalize_year(pattern[3])) if pattern[3] else self.now_date.year
            try:
                # to catch dates which are not possible like "31/11" (october 31st)
                if not pattern[3] and self.timezone.localize(datetime.datetime(year=yy, month=mm, day=dd)) \
                        < self.now_date:
                    yy += 1
            except Exception:
                continue

            date = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_EXACT
            }
            date_list.append(date)
            # original = self.regx_to_process.text_substitute(original)
            original_list.append(original)
        return date_list, original_list

    def _gregorian_month_day_year_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <month><separator><day><separator><year>
        where each part is in of one of the formats given against them
            day: d, dd
            month: m, mm
            year: yy, yyyy
            separator: "/", "-", "."

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "6/2/39", "7/01/1997", "12-28-2096"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'[^/\-\.\w]((1[0-2]|0?[1-9])\s?[/\-\.]\s?([12][0-9]|3[01]|0?[1-9])'
                                   r'(?:\s?[/\-\.]\s?((?:20|19)?[0-9]{2}))?)\W')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[2]
            mm = pattern[1]
            yy = int(self.normalize_year(pattern[3])) if pattern[3] else self.now_date.year
            try:
                # to catch dates which are not possible like "11/31" (october 31st)
                if not pattern[3] and self.timezone.localize(datetime.datetime(year=yy, month=mm, day=dd)) \
                        < self.now_date:
                    yy += 1
            except Exception:
                continue

            date = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_EXACT
            }
            date_list.append(date)
            # original = self.regx_to_process.text_substitute(original)
            original_list.append(original)
        return date_list, original_list

    def _gregorian_year_month_day_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <year><separator><month><separator><day>
        where each part is in of one of the formats given against them
            day: d, dd
            month: m, mm
            year: yy, yyyy
            separator: "/", "-", "."

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "31/1/31", "97/2/21", "2017/12/01"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'\b(((?:20|19)[0-9]{2})\s?[/\-\.]\s?'
                                   r'(1[0-2]|0?[1-9])\s?[/\-\.]\s?([12][0-9]|3[01]|0?[1-9]))\W')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[3]
            mm = pattern[2]
            yy = self.normalize_year(pattern[1])

            date = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_EXACT
            }
            date_list.append(date)
            # original = self.regx_to_process.text_substitute(original)
            original_list.append(original)
        return date_list, original_list

    def _gregorian_advanced_day_month_year_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <day><separator><month><separator><year>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            year: yy, yyyy
            separator: "/", "-", ".", space

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "21 Nov 99", "02 january 1972", "9 November 2014", "09-Nov-2014", "09/Nov/2014"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'\b(([12][0-9]|3[01]|0?[1-9])\s?[\/\ \-\.\,]\s?([A-Za-z]+)\s?[\/\ \-\.\,]\s?'
                                   r'((?:20|19)?[0-9]{2}))\W')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0].strip()
            dd = pattern[1]
            probable_mm = pattern[2]
            yy = self.normalize_year(pattern[3])

            mm = self.__get_month_index(probable_mm)
            if mm:
                date = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT

                }
                date_list.append(date)
                # original = self.regx_to_process.text_substitute(original)
                original_list.append(original)
        return date_list, original_list

    def _gregorian_day_with_ordinals_month_year_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <day><Optional ordinal inidicator><Optional "of"><separator><month><separator><year>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            year: yy, yyyy
            ordinal indicator: "st", "nd", "rd", "th", space
            separator: ",", space

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "21st Nov 99", "02nd of,january, 1972", "9 th November 2014", "09th Nov, 2014", "09 Nov 2014"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        regex_pattern = re.compile(r'\b(([12][0-9]|3[01]|0?[1-9])\s?(?:nd|st|rd|th)?\s?(?:of)?[\s\,\-]\s?'
                                   r'([A-Za-z]+)[\s\,\-]\s?((?:20|19)?[0-9]{2}))\W')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0].strip()
            dd = pattern[1]
            probable_mm = pattern[2]
            yy = self.normalize_year(pattern[3])

            mm = self.__get_month_index(probable_mm)
            if mm:
                date = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_list.append(date)
                original_list.append(original)
        return date_list, original_list

    def _gregorian_advanced_year_month_day_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <year><separator><month><separator><day>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            year: yy, yyyy
            separator: "/", "-", space

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "2099 Nov 21", "1972 january 2", "2014 November 6", "2014-Nov-09", "2015/Nov/94"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'\b(((?:20|19)[0-9]{2})\s?[\/\ \,\-]\s?([A-Za-z]+)\s?'
                                   r'[\/\ \,\-]\s?([12][0-9]|3[01]|0?[1-9]))\W')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[3]
            probable_mm = pattern[2]
            yy = self.normalize_year(pattern[1])
            mm = self.__get_month_index(probable_mm)
            if mm:
                date = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_list.append(date)
                # original = self.regx_to_process.text_substitute(original)
                original_list.append(original)
        return date_list, original_list

    def _gregorian_year_day_month_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <year><separator><day><Optional ordinal indicator><separator><month>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            year: yy, yyyy
            separator: ",", space
            ordinal indicator: "st", "nd", "rd", "th", space

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "2099 21st Nov", "1972, 2 january", "14,November,6"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'\b(((?:20|19)[0-9]{2})[\ \,]\s?([12][0-9]|3[01]|0?[1-9])\s?'
                                   r'(?:nd|st|rd|th)?[\ \,]([A-Za-z]+))\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[2]
            probable_mm = pattern[3]
            yy = self.normalize_year(pattern[1])
            mm = self.__get_month_index(probable_mm)
            if mm:
                date = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_list.append(date)
                original_list.append(original)
        return date_list, original_list

    def _gregorian_month_day_with_ordinals_year_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <month><separator><day><Optional ordinal indicator><separator><year>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            year: yy, yyyy
            separator: ",", space
            ordinal indicator: "st", "nd", "rd", "th", space

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "Nov 21st 2099", "january, 2 1972", "12,November,13"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'\b(((?:20|19)?[0-9]{2})?\s?([A-Za-z]+)[\ \,\-]\s?([12][0-9]'
                                   r'|3[01]|0?[1-9])\s?(?:nd|st|rd|th)?'
                                   r'(?:[\ \,\-]\s?((?:20|19)?[0-9]{2}))?)\W')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            yy1 = pattern[1]
            yy2 = pattern[4]
            dd = pattern[3]
            yy = int(self.normalize_year(yy1 or yy2 or str(self.now_date.year)))
            probable_mm = pattern[2]
            mm = self.__get_month_index(probable_mm)

            if mm:
                try:
                    # to catch dates which are not possible like "31/11" (october 31st)
                    if not yy1 and not yy2 and self.timezone.localize(datetime.datetime(year=yy, month=mm, day=dd)) \
                            < self.now_date:
                        yy += 1
                except Exception:
                    continue

                date = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_list.append(date)
                original_list.append(original)
        return date_list, original_list

    def _gregorian_month_day_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <month><separator><day><Optional ordinal indicator>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            separator: ",", space
            ordinal indicator: "st", "nd", "rd", "th", space

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "Feb 21st", "january, 2", "November 12"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'\b(([A-Za-z]+)[\ \,]\s?([12][0-9]|3[01]|0?[1-9])\s?(?:nd|st|rd|th)?)\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[2]
            probable_mm = pattern[1]
            mm = self.__get_month_index(probable_mm)
            if dd and mm:
                dd = int(dd)
                mm = int(mm)
                if self.now_date.month > mm:
                    yy = self.now_date.year + 1
                elif self.now_date.day > dd and self.now_date.month == mm:
                    yy = self.now_date.year + 1
                else:
                    yy = self.now_date.year

                date_dict = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_list.append(date_dict)
                original_list.append(original)
        return date_list, original_list

    def _gregorian_day_month_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <day><Optional ordinal indicator><separator><month>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            separator: ",", space
            ordinal indicator: "st", "nd", "rd", "th", space

        Optional "of" is allowed after ordinal indicator, example "dd th of this current month"

        Few valid examples:
            "21st Nov", "2, of january ", "12th of November"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'\b(([12][0-9]|3[01]|0?[1-9])\s?(?:nd|st|rd|th)?[\ \,]\s?(?:of)?\s?([A-Za-z]+))\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[1]
            probable_mm = pattern[2]
            mm = self.__get_month_index(probable_mm)
            if dd and mm:
                dd = int(dd)
                mm = int(mm)
                if self.now_date.month > mm:
                    yy = self.now_date.year + 1
                elif self.now_date.day > dd and self.now_date.month == mm:
                    yy = self.now_date.year + 1
                else:
                    yy = self.now_date.year
                date_dict = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_list.append(date_dict)
                original_list.append(original)
        return date_list, original_list

    def _todays_date(self, date_list=None, original_list=None):
        """
        Detects "today" and its variants and returns the date today
        Matches "today", "2dy", "2day", "tody", "aaj", "aj", "tonight"
        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        regex_pattern = re.compile(r'\b(today|2dy|2day|tody|aaj|aj|tonight)\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern
            dd = self.now_date.day
            mm = self.now_date.month
            yy = self.now_date.year
            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_TODAY

            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _tomorrows_date(self, date_list=None, original_list=None):
        """
        Detects "tommorow" and its variants and returns the date value for tommorow
        Matches "tomorrow", "2morow", "2mrw", "2mrow", "next day", "tommorrow", "tommorow", "tomorow", "tommorow"
        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.
        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        regex_pattern = re.compile(r'\b((tomorrow|2morow|2mrw|2mrow|next day|tommorr?ow|tomm?orow|'
                                   r'tmrw|tmrrw|tomorw|tomro|tomorow|afte?r\s+1\s+da?y))\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            tomorrow = self.now_date + datetime.timedelta(days=1)
            dd = tomorrow.day
            mm = tomorrow.month
            yy = tomorrow.year
            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_TOMORROW
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _yesterdays_date(self, date_list=None, original_list=None):
        """
        Detects "yesterday" and "previous day" and its variants and returns the date value for yesterday

        Matches "yesterday", "sterday", "yesterdy", "yestrdy", "yestrday", "previous day", "prev day", "prevday"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(
            r'\b((yesterday|sterday|yesterdy|yestrdy|yestrday|previous day|prev day|prevday))\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            yesterday = self.now_date - datetime.timedelta(days=1)
            dd = yesterday.day
            mm = yesterday.month
            yy = yesterday.year
            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_YESTERDAY
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _day_after_tomorrow(self, date_list=None, original_list=None):
        """
        Detects "day after tomorrow" and its variants and returns the date on day after tomorrow
        Matches "day" or "dy" followed by "after" or "aftr" followed by one of
        "tomorrow", "2morow", "2mrw", "2mrow", "kal", "2mrrw"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        regex_pattern = re.compile(r'\b((da?y afte?r)\s+(tomorrow|2morow|2mrw|2mrow|kal|2mrrw))\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            day_after = self.now_date + datetime.timedelta(days=2)
            dd = day_after.day
            mm = day_after.month
            yy = day_after.year
            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_DAY_AFTER
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _date_days_after(self, date_list=None, original_list=None):
        """
        Detects "date after n number of days" and returns the date after n days
        Matches "after" followed by the number of days provided
        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                               date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and type followed by the
            second list containing their corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        regex_pattern = re.compile(r'\b(afte?r\s+(\d+)\s+(da?y|da?ys))\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            days = int(pattern[1])
            day_after = self.now_date + datetime.timedelta(days=days)
            dd = day_after.day
            mm = day_after.month
            yy = day_after.year
            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_N_DAYS_AFTER
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _date_days_later(self, date_list=None, original_list=None):
        """
        Detects "date n days later" and returns the date for n days later
        Matches "digit" followed by "days" and iterations of "later"
        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                           date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and type followed by the
            second list containing their corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        regex_pattern = re.compile(r'\b((\d+)\s+(da?y|da?ys)\s?(later|ltr|latr|lter)s?)\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            days = int(pattern[1])
            day_after = self.now_date + datetime.timedelta(days=days)
            dd = day_after.day
            mm = day_after.month
            yy = day_after.year
            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_N_DAYS_AFTER
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _day_before_yesterday(self, date_list=None, original_list=None):
        """
        Detects "day before yesterday" and its variants and returns the date on day after tomorrow

        Matches "day" or "dy" followed by "before" or "befre" followed by one of
        "yesterday", "sterday", "yesterdy", "yestrdy", "yestrday"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'\b((da?y befo?re)\s+(yesterday|sterday|yesterdy|yestrdy|yestrday))\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            day_before = self.now_date - datetime.timedelta(days=2)
            dd = day_before.day
            mm = day_before.month
            yy = day_before.year
            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_DAY_BEFORE

            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _day_in_next_week(self, date_list=None, original_list=None):
        """
        Detects "next <day of the week>" and its variants and returns the date on that day in the next week.
        Week starts with Sunday and ends with Saturday

        Matches "next" or "nxt" followed by day of the week - Sunday/Monday/Tuesday/Wednesday/Thursday/Friday/Saturday
        or their abbreviations. NOTE: Day of the week and their variants are fetched from the data store

        Example:
            If it is 7th February 2017, Tuesday while invoking this function,
            "next Sunday" would return [{'dd': 12, 'mm': 2, 'type': 'day_in_next_week', 'yy': 2017}]
            "next Saturday" would return [{'dd': 18, 'mm': 2, 'type': 'day_in_next_week', 'yy': 2017}]
            and other days would return dates between these dates

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'\b((ne?xt)\s+([A-Za-z]+))\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            probable_day = pattern[2]
            day = self.__get_day_index(probable_day)
            current_day = self.__get_day_index(self.now_date.strftime("%A"))
            if day and current_day:
                day, current_day = int(day), int(current_day)
                date_after_days = day - current_day + 7
                day_to_set = self.now_date + datetime.timedelta(days=date_after_days)
                dd = day_to_set.day
                mm = day_to_set.month
                yy = day_to_set.year
                date_dict = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_NEXT_DAY
                }
                date_list.append(date_dict)
                original_list.append(original)
        return date_list, original_list

    def _day_within_one_week(self, date_list=None, original_list=None):
        """
        Detects "this <day of the week>" and its variants and returns the date on that day within one week from
        current date.

        Matches one of "this", "dis", "coming", "on", "for", "fr" followed by
        day of the week - Sunday/Monday/Tuesday/Wednesday/Thursday/Friday/Saturday or their abbreviations.
        NOTE: Day of the week and their variants are fetched from the data store

        Example:
            If it is 7th February 2017, Tuesday while invoking this function,
            "this Tuesday" would return [{'dd': 7, 'mm': 2, 'type': 'day_within_one_week', 'yy': 2017}]
            "for Monday" would return [{'dd': 13, 'mm': 2, 'type': 'day_within_one_week', 'yy': 2017}]
            and other days would return dates between these dates

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'\b((this|dis|coming|on|for)*[\s\-]*([A-Za-z]+))\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0].strip()
            probable_day = pattern[2]
            day = self.__get_day_index(probable_day)
            current_day = self.__get_day_index(self.now_date.strftime("%A"))
            if day and current_day:
                day, current_day = int(day), int(current_day)
                if current_day <= day:
                    date_after_days = day - current_day
                else:
                    date_after_days = day - current_day + 7
                day_to_set = self.now_date + datetime.timedelta(days=date_after_days)
                dd = day_to_set.day
                mm = day_to_set.month
                yy = day_to_set.year
                date_dict = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_THIS_DAY
                }
                date_list.append(date_dict)
                original_list.append(original)
        return date_list, original_list

    def _date_identification_given_day(self, date_list=None, original_list=None):
        """
        Detects probable date given only day part. The month and year are assumed to be current month and current year
        respectively. Consider checking if the returned detected date is valid.

        format: <day><Optional space><ordinal indicator>
        where each part is in of one of the formats given against them
            day: d, dd
            ordinal indicator: "st", "nd", "rd", "th"

        Example:
            If it is 7th February 2017, Tuesday while invoking this function,
            "2nd" would return [{'dd': 2, 'mm': 2, 'type': 'possible_day', 'yy': 2017}]
            "29th" would return [{'dd': 29, 'mm': 2, 'type': 'possible_day', 'yy': 2017}]
            Please note that 29/2/2017 is not a valid date on calendar but would be returned anyway as a probable date

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'\b(([12][0-9]|3[01]|0?[1-9])\s*(?:nd|st|rd|th))\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]

            dd = int(pattern[1])
            mm = self.now_date.month
            yy = self.now_date.year

            date = datetime.date(year=yy, month=mm, day=dd)
            if date < self.now_date.date():
                mm += 1
                if mm > 12:
                    mm = 1
                    yy += 1

            date_dict = {
                'dd': dd,
                'mm': mm,
                'yy': yy,
                'type': TYPE_POSSIBLE_DAY
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _date_identification_given_day_and_current_month(self, date_list=None, original_list=None):
        """
        Detects probable date given day part and . The year is assumed to be current year
        Consider checking if the returned detected date is valid.

        Matches <day><Optional ordinal indicator><"this" or "dis"><Optional "current" or "curent"><"mnth" or "month">
        where each part is in of one of the formats given against them
            day: d, dd
            ordinal indicator: "st", "nd", "rd", "th"

        Optional "of" is allowed after ordinal indicator, example "dd th of this current month"

        Few valid examples:
            "3rd this month", "2 of this month", "05 of this current month"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.
        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'\b(([12][0-9]|3[01]|0?[1-9])\s*(?:nd|st|rd|th)?\s*(?:of)?'
                                   r'\s*(?:this|dis)\s*(?:curr?ent)?\s*(month|mnth))\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]

            dd = pattern[1]
            mm = self.now_date.month
            yy = self.now_date.year

            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_POSSIBLE_DAY
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _date_identification_given_day_and_next_month(self, date_list=None, original_list=None):
        """
        Detects probable date given day part and "next month" synonyms. The year is assumed to be current year
        Consider checking if the returned detected date is valid.

        Matches <day><Optional ordinal indicator><"this" or "dis"><"next" variants><"mnth" or "month">
        where each part is in of one of the formats given against them
            day: d, dd
            ordinal indicator: "st", "nd", "rd", "th"
            "next" variants: "next", "nxt", "comming", "coming", "commin", "following", "folowin", "followin",
                             "folowing"

        Optional "of" is allowed after ordinal indicator, example "dd th of this next month"

        Few valid examples:
            "3rd of next month", "2 of next month", "05 of next month"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        regex_pattern = re.compile(r'\b(([12][0-9]|3[01]|0?[1-9])\s*(?:nd|st|rd|th)?\s*(?:of)?'
                                   r'\s*(?:next|nxt|comm?ing?|foll?owing?|)\s*(mo?nth))\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]

            dd = int(pattern[1])
            previous_mm = self.now_date.month
            yy = self.now_date.year
            mm = previous_mm + 1
            if mm > 12:
                mm = 1
                yy += 1

            date_dict = {
                'dd': dd,
                'mm': mm,
                'yy': yy,
                'type': TYPE_POSSIBLE_DAY
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _date_identification_everyday(self, date_list=None, original_list=None, n_days=30):
        """
        Detects "everyday" and its variants and returns all the dates of the next n_days from current date.
        Matches "everyday", "daily", "every day", "all day", "all days"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                           date entities
            n_days: Optional, number of days from current date to return dates for if everyday is detected as a time
                    entity, default value is 30

        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        now = self.now_date
        end = now + datetime.timedelta(days=n_days)
        regex_pattern = re.compile(r'\b\s*((everyday|daily|every\s{0,3}day|all\sday|all\sdays))\s*\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        if patterns:
            pattern = patterns[0]
            original = pattern[0]
            date_dict = {
                'dd': now.day,
                'mm': now.month,
                'yy': now.year,
                'type': TYPE_EVERYDAY
            }

            while now < end:
                date_list.append(copy.deepcopy(date_dict))
                now += datetime.timedelta(days=1)
                date_dict = {
                    'dd': now.day,
                    'mm': now.month,
                    'yy': now.year,
                    'type': TYPE_EVERYDAY
                }
                original_list.append(original)
        return date_list, original_list

    def _date_identification_everyday_except_weekends(self, date_list=None, original_list=None, n_days=30):
        """
        First this method tries to detect "everday except weekends" and its variants. If that fails, it tries to detect
        "weekdays" and its variants and returns all the dates within the next n_days from
        current date except those that occur on Saturdays and Sundays.

        Matches <"everyday", "daily", "all days"><space><"except"><space><"weekend", "weekends">
        Matches <"weekday", "weekdays", "week days", "week day", "all weekdays">

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                           date entities
            n_days: Optional, number of days from current date, to return all dates of weekdays in the interval from
                    current date to date after n_days, default value is 30

        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        now = self.now_date
        end = now + datetime.timedelta(days=n_days)
        regex_pattern = re.compile(r'\b((every\s?day|daily|all\s?days)\s+except\s+weekends?)\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        is_everyday_result = []
        if not patterns:
            weekday_regex_pattern = re.compile(r'\b((week\s?days?|all\sweekdays))\b')
            patterns = weekday_regex_pattern.findall(self.processed_text.lower())
            every_weekday_pattern = re.compile(r'\b((every|daily|recur|always|continue|every\s*day|all)\s+'
                                               r'(week\s?days?|all\sweekdays))\b', re.IGNORECASE)
            is_everyday_result = every_weekday_pattern.findall(self.text)
        constant_type = WEEKDAYS
        if is_everyday_result:
            constant_type = REPEAT_WEEKDAYS
            patterns = is_everyday_result
        # checks if phrase of the form everyday except weekdays is present in the sentence.
        regex_pattern = re.compile(r'\b((every\s?day|daily|all\s?days)\s+except\s+weekdays?)\b')
        check_patterns_for_except_weekdays = regex_pattern.findall(self.processed_text.lower())
        if check_patterns_for_except_weekdays:
            patterns = []
        today = now.weekday()
        count = 0
        weekend = []
        date_day = self.now_date
        while count < 15:
            if today > 6:
                today = 0
            if today == 5 or today == 6:
                weekend.append(copy.deepcopy(date_day))
            count += 1
            today += 1
            date_day = date_day + datetime.timedelta(days=1)
        i = 0
        weekend_digit = []
        while i <= (len(weekend) - 1):
            weekend_date = weekend[i].day
            weekend_digit.append(copy.deepcopy(weekend_date))
            i += 1
        for pattern in patterns:
            original = pattern[0]
            date_dict = {
                'dd': now.day,
                'mm': now.month,
                'yy': now.year,
                'type': constant_type
            }
            current_date = date_dict['dd']
            while now < end:
                if current_date not in weekend_digit:
                    date_list.append(copy.deepcopy(date_dict))
                now += datetime.timedelta(days=1)
                date_dict = {
                    'dd': now.day,
                    'mm': now.month,
                    'yy': now.year,
                    'type': constant_type
                }
                current_date = now.day
                original_list.append(original)
        return date_list, original_list

    def _date_identification_everyday_except_weekdays(self, date_list=None, original_list=None, n_days=30):
        """
        First this method tries to detect "everday except weekdays" and its variants. If that fails, it tries to detect
        "weekends" and its variants and returns all the dates within the next n_days from
        current date that occur on Saturdays and Sundays.

        Matches <"everyday", "daily", "all days"><space><"except"><space><"weekday", "weekdays">
        Matches <"weekend", "weekends", "week end", "week ends", "all weekends">


        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                           date entities
            n_days: Optional, number of days from current date, to return all dates of weekends in the interval from
                    current date to date after n_days, default value is 30

        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        now = self.now_date
        end = now + datetime.timedelta(days=n_days)
        regex_pattern = re.compile(r'\b((every\s?day|daily|all\s?days)\s+except\s+weekdays?)\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        is_everyday_result = []
        if not patterns:
            weekend_regex_pattern = re.compile(r'\b((week\s?ends?|all\sweekends))\b')
            patterns = weekend_regex_pattern.findall(self.processed_text.lower())
            every_weekend_pattern = re.compile(r'\b((every|daily|recur|always|continue|every\s*day|all)'
                                               r'\s+(week\s?ends?|all\sweekends))\b', re.IGNORECASE)
            is_everyday_result = every_weekend_pattern.findall(self.text)

        constant_type = WEEKENDS
        if is_everyday_result:
            constant_type = REPEAT_WEEKENDS
            patterns = is_everyday_result
        today = now.weekday()
        count = 0
        weekend = []
        date_day = self.now_date
        while count < 50:
            if today > 6:
                today = 0
            if today == 5 or today == 6:
                weekend.append(copy.deepcopy(date_day))
            count += 1
            today += 1
            date_day = date_day + datetime.timedelta(days=1)
        i = 0
        weekend_digit = []
        while i <= (len(weekend) - 1):
            weekend_date = weekend[i].isocalendar()
            weekend_digit.append(copy.deepcopy(weekend_date))
            i += 1
        for pattern in patterns:
            original = pattern[0]
            date_dict = {
                'dd': now.day,
                'mm': now.month,
                'yy': now.year,
                'type': constant_type
            }
            current_date = now.isocalendar()
            while now < end:
                if current_date in weekend_digit:
                    date_list.append(copy.deepcopy(date_dict))
                now += datetime.timedelta(days=1)
                date_dict = {
                    'dd': now.day,
                    'mm': now.month,
                    'yy': now.year,
                    'type': constant_type
                }
                current_date = now.isocalendar()
                original_list.append(original)
        return date_list, original_list

    def _day_month_format_for_arrival_departure(self, date_list=None, original_list=None):
        """
        Detects probable "start_date to/till/- end_date of month" format and its variants and returns both start date
        and end date
        format: <day><ordinal indicator><range separator><day><ordinal indicator><separator><Optional "of"><month>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            separator: ",", space
            range separator: "to", "-", "till"

        Few valid examples:
            "21st to 30th of Jan", "2 till 15 Nov", "10 - 15 of february"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        # FIXME: This ignores any mentioned year
        regex_pattern = re.compile(r'\b(([12][0-9]|3[01]|0?[1-9])\s*(?:nd|st|rd|th)?'
                                   r'(?:(?:\s*\-\s*)|\s+(?:to|till|se)\s+)'
                                   r'([12][0-9]|3[01]|0?[1-9])\s?(?:nd|st|rd|th)?[\s\,]+(?:of\s+)?([A-Za-z]+))\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd1, mm1, yy1 = int(pattern[1]), None, None
            dd2, mm2, yy2 = int(pattern[2]), self.__get_month_index(pattern[3]), self.now_date.year

            if mm2:
                mm2 = int(mm2)
                dt2 = self.timezone.localize(datetime.datetime(year=yy2, month=mm2, day=dd2))
                dd1, mm1, yy1 = get_previous_date_with_dd(dd=dd1, before_datetime=dt2)
                if dd1 and mm1 and yy1:
                    dt1 = self.timezone.localize(datetime.datetime(year=yy1, month=mm1, day=dd1))
                    if dt1 < self.now_date:
                        yy1 = yy2 = yy2 + 1

            if all(part for part in [dd1, mm1, yy1, dd2, mm2, yy2]):
                date_dict_1 = {
                    'dd': int(dd1),
                    'mm': int(mm1),
                    'yy': int(yy1),
                    'type': TYPE_EXACT
                }
                date_dict_2 = {
                    'dd': int(dd2),
                    'mm': int(mm2),
                    'yy': int(yy2),
                    'type': TYPE_EXACT
                }
                date_list.append(date_dict_1)
                date_list.append(date_dict_2)

                original_list.append(original)
                original_list.append(original)

        return date_list, original_list

    def _day_range_for_nth_week_month(self, date_list=None, original_list=None):
        """
        Detects probable "first week of month" format and its variants and returns list of dates in those week
        and end date
        format: <ordinal><separator><week><separator><Optional "of"><month>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            separator: ",", space
            range separator: "to", "-", "till"

        Few valid examples:
            "first week of Jan", "second week of coming month", "last week of december"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        ordinal_choices = "|".join(list(ORDINALS_MAP.keys()))
        regex_pattern = re.compile(r'((' + ordinal_choices + r')\s+week\s+(of\s+)?([A-Za-z]+)(?:\s+month)?)\s+')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            probable_mm = pattern[3]
            mm = self.__get_month_index(probable_mm)
            yy = self.now_date.year
            if mm:
                mm = int(mm)
                if self.now_date.month > mm:
                    yy += 1
            elif probable_mm in ['coming', 'comming', 'next', 'nxt', 'following', 'folowing']:
                mm = self.now_date.month + 1
                if mm > 12:
                    mm = 1
                    yy += 1
            if mm:
                weeknumber = ORDINALS_MAP[pattern[1]]
                weekdays = get_weekdays_for_month(weeknumber, mm, yy)
                for day in weekdays:
                    date_dict = {
                        'dd': int(day),
                        'mm': int(mm),
                        'yy': int(yy),
                        'type': TYPE_EXACT
                    }
                    date_list.append(date_dict)
                    original_list.append(original)

        return date_list, original_list

    def _date_range_ddth_of_mmm_to_ddth(self, date_list=None, original_list=None):
        """
        Detects probable "start_date month to/till/- end_date" format and its variants and returns both start date
        and end date
        format: <day><ordinal indicator><Optional "of"><month><range separator><day><ordinal indicator><separator>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            separator: ",", space
            range separator: "to", "-", "till"

        Few valid examples:
            "21st jan to 30th", "2 nov till 15", "10 february - 15"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        # FIXME: This ignores any mentioned year
        regex_pattern = re.compile(r'\b(([12][0-9]|3[01]|0?[1-9])\s?(?:nd|st|rd|th)?[\s\,]+(?:of\s+)?([A-Za-z]+)'
                                   r'(?:(?:\s*\-\s*)|\s+(?:to|till|se)\s+)'
                                   r'([12][0-9]|3[01]|0?[1-9])\s?(?:nd|st|rd|th)?'
                                   r'(?:[\s\,]+(?:of\s+)?([A-Za-z]+))?)\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd1, mm1, yy1 = int(pattern[1]), self.__get_month_index(pattern[2]), self.now_date.year
            dd2, mm2, yy2 = int(pattern[3]), self.__get_month_index(pattern[4]), self.now_date.year
            if mm1:
                mm1 = int(mm1)
                dt1 = self.timezone.localize(datetime.datetime(year=yy1, month=mm1, day=dd1))
                if dt1 < self.now_date:
                    yy2 = yy1 = yy1 + 1
                    dt1 = self.timezone.localize(datetime.datetime(year=yy1, month=mm1, day=dd1))

                if mm2:
                    # find the correct yy2 such that dd2/mm2/yy2 >= dd1/mm1/yy1
                    mm2 = int(mm2)
                    dt2 = self.timezone.localize(datetime.datetime(year=yy2, month=mm2, day=dd2))
                    yy2 = yy2 + 1 if dt2 < dt1 else yy2
                else:
                    # find the closest dd2 after dt1
                    dd2, mm2, yy2 = get_next_date_with_dd(dd=dd2, after_datetime=dt1)

            if all(part for part in [dd1, mm1, yy1, dd2, mm2, yy2]):
                date_dict_1 = {
                    'dd': int(dd1),
                    'mm': int(mm1),
                    'yy': int(yy1),
                    'type': TYPE_EXACT
                }
                date_dict_2 = {
                    'dd': int(dd2),
                    'mm': int(mm2),
                    'yy': int(yy2),
                    'type': TYPE_EXACT
                }
                date_list.append(date_dict_1)
                date_list.append(date_dict_2)

                original_list.append(original)
                original_list.append(original)

        return date_list, original_list

    def _date_range_ddth_to_ddth_of_next_month(self, date_list=None, original_list=None):
        """
        Detects probable "start_date to/till/- end_date of coming/next month" format and its variants and returns both
        start date and end date
        format: <day><ordinal indicator><range separator><day><ordinal indicator><separator><Optional "of">
        (coming/next)<month>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            separator: ",", space
            range separator: "to", "-", "till"

        Few valid examples:
            "21st to 30th of coming month", "2 till 15 next month", "10 - 15 of next month"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = re.compile(r'\b(([12][0-9]|3[01]|0?[1-9])\s?(?:nd|st|rd|th)?'
                                   r'(?:(?:\s*\-\s*)|\s+(?:to|till|se)\s+)'
                                   r'([12][0-9]|3[01]|0?[1-9])\s?(?:nd|st|rd|th)?[\s\,]+(?:of\s+)?'
                                   r'(?:next|nxt|comm?ing?|foll?owing?)\s+(?:mo?nth))\b')
        patterns = regex_pattern.findall(self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd1 = pattern[1]
            dd2 = pattern[2]
            previous_mm = self.now_date.month
            yy = self.now_date.year
            mm = previous_mm + 1
            if mm > 12:
                mm = 1
                yy += 1

            date_dict_1 = {
                'dd': int(dd1),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_EXACT
            }
            date_dict_2 = {
                'dd': int(dd2),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_EXACT
            }
            date_list.append(date_dict_1)
            date_list.append(date_dict_2)

            original_list.append(original)
            original_list.append(original)

        return date_list, original_list

    @staticmethod
    def _is_everyday_present(text):
        """
        Detects if there is one of following words in text:
            "every", "daily", "recur", "always", "continue", "every day", "all"

        Args:
            text: string to recognize date entities from

        Returns:
            Boolean, True if any one of the above listed words are found , False otherwise

        """
        pattern = re.compile(r'\b(every|daily|recur|always|continue|every\s*day|all)\b', re.IGNORECASE)
        result = pattern.findall(text)
        if result:
            return True
        else:
            return False

    @staticmethod
    def _check_current_day(date_list):
        """
        Checks if TYPE_THIS_DAY or TYPE_REPEAT_DAY type of date is present in the date_list consisting of detected
        date dictionaries by checking "type" of each date

        Args:
            date_list: list of dictionaries of detected dates

        Returns:
            Boolean, True if any date in list has "type" either TYPE_THIS_DAY or TYPE_REPEAT_DAY , False otherwise

        """
        for index in date_list:
            if index['type'] in [TYPE_THIS_DAY, TYPE_REPEAT_DAY]:
                return True
        else:
            return False

    @staticmethod
    def _check_date_presence(date_list):
        """
        Checks if TYPE_NORMAL type of date is present in the date_list consisting of detected date dictionaries by
        checking "type" of each date

        Args:
            date_list: list of dictionaries of detected dates

        Returns:
            Boolean, True if any date in list has "type" TYPE_NORMAL , False otherwise

        """
        for i in date_list:
            if i['type'] == TYPE_EXACT:
                return True
        else:
            return False

    def _weeks_identification(self, date_list=None, original_list=None):
        """
        Checks for repeating days and will replace the type to TYPE_REPEAT_DAY
        Few valid examples:
            "every monday", "every friday", "every thursday"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities

        Returns:
            tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        new_date_list = []
        new_text = self.text.lower().replace(',', '')
        is_everyday = self._is_everyday_present(new_text)

        if self._check_current_day(date_list) and is_everyday:
            for index, val in enumerate(date_list):
                if val['type'] == TYPE_THIS_DAY:
                    val['type'] = TYPE_REPEAT_DAY
                    new_date_list.append(val)
        if new_date_list:
            date_list = new_date_list
            original_list = original_list[:len(date_list)]
        return date_list, original_list

    def __get_month_index(self, value):
        # type: (str) -> Optional[int]
        """
        Gets the index of month by comparing the value with month names and their variants from the data store

        Args:
            value: string of the month detected in the text

        Returns:
            integer between 1 to 12 inclusive if value matches one of the month or its variants
            None if value doesn't match any of the month or its variants
        """
        for month in self.month_dictionary:
            if value.lower() in self.month_dictionary[month]:
                return month
        return None

    def __get_day_index(self, value):
        # type: (str) -> Optional[int]
        """
        Gets the index of month by comparing the value with day names and their variants from the data store

        Args:
            value: string of the month detected in the text

        Returns:
            integer between 1 to 7 inclusive if value matches one of the day or its variants
            None if value doesn't match any of the day or its variants
        """
        for day in self.day_dictionary:
            if value.lower() in self.day_dictionary[day]:
                return day
        return None

    @staticmethod
    def to_date_dict(datetime_object, date_type=TYPE_EXACT):
        """
        Convert the given datetime object to a dictionary containing dd, mm, yy

        Args:
            datetime_object (datetime.datetime): datetime object
            date_type (str, optional, default TYPE_EXACT): 'type' metdata for this detected date

        Returns:
            dict: dictionary containing day, month, year in keys dd, mm, yy respectively with date type as additional
            metadata.
        """
        return {
            'dd': datetime_object.day,
            'mm': datetime_object.month,
            'yy': datetime_object.year,
            'type': date_type,
        }

    def to_datetime_object(self, base_date_value_dict):
        """
        Convert the given date value dict to a timezone localised datetime object

        Args:
            base_date_value_dict (dict): dict containing dd, mm, yy

        Returns:
            datetime object: datetime object localised with the timezone given on initialisation
        """
        datetime_object = datetime.datetime(year=base_date_value_dict['yy'],
                                            month=base_date_value_dict['mm'],
                                            day=base_date_value_dict['dd'], )
        return self.timezone.localize(datetime_object)

    def normalize_year(self, year):
        """
        Normalize two digit year to four digits by taking into consideration the bot message. Useful in cases like
        date of birth where past century is preferred than current. If no bot message is given it falls back to
        current century

        Args:
            year (str): Year string to normalize

        Returns:
            str: year in four digits
        """
        past_regex = re.compile(r'birth|bday|dob|born')
        present_regex = None
        future_regex = None
        this_century = int(str(self.now_date.year)[:2])
        if len(year) == 2:
            if (((self.bot_message and past_regex.search(self.bot_message))
                 or (self.past_date_referenced is True)) and (int(year) > int(str(self.now_date.year)[2:]))):
                return str(this_century - 1) + year
            elif present_regex and present_regex.search(self.bot_message):
                return str(this_century) + year
            elif future_regex and future_regex.search(self.bot_message):
                return str(this_century + 1) + year

        # if patterns didn't match or no bot message set, fallback to current century
        if len(year) == 2:
            return str(this_century) + year

        return year

    def set_bot_message(self, bot_message):
        """
        Sets the object's bot_message attribute

        Args:
            bot_message: is the previous message that is sent by the bot
        """
        self.bot_message = bot_message
