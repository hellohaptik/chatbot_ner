import re
import copy
import datetime
import pytz
from lib.nlp.regex import Regex
from v1.entities.constant import TYPE_EXACT, TYPE_EVERYDAY, TYPE_TODAY, \
    TYPE_TOMORROW, TYPE_YESTERDAY, TYPE_DAY_AFTER, TYPE_DAY_BEFORE, TYPE_NEXT_DAY, TYPE_THIS_DAY, \
    TYPE_POSSIBLE_DAY, TYPE_REPEAT_DAY, START_RANGE, END_RANGE, REPEAT_START_RANGE, REPEAT_END_RANGE, \
    DATE_START_RANGE, DATE_END_RANGE, WEEKDAYS, WEEKENDS, REPEAT_WEEKDAYS, REPEAT_WEEKENDS, MONTH_DICT, DAY_DICT


# TODO add code examples
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
        regx_to_process: regex to remove forward slash while updating list that stores  text
        regx_to_process_text: regex to remove forward slash while before detecting entities
        date_object: datetime object holding timestamp while DateDetector instantiation
        month_dictionary: dictonary mapping month indexes to month spellings and 
                            fuzzy variants(spell errors, abbreviations)
        day_dictionary: dictonary mapping day indexes to day of week spellings and 
                            fuzzy variants(spell errors, abbreviations)

        SUPPORTED_FORMAT                                            METHOD_NAME
        ------------------------------------------------------------------------------------------------------------
        1. day/month/year                                           _gregorian_day_month_year_format
        2. year/month/day                                           _gregorian_year_month_day_format
        3. day/month/year (Month in abbreviation or full)           _gregorian_advanced_day_month_year_format
        4. Xth month year (Month in abbreviation or full)           _gregorian_day_with_ordinals_month_year_format
        5. year month Xth (Month in abbreviation or full)           _gregorian_advanced_year_month_day_format
        6. year Xth month (Month in abbreviation or full)           _gregorian_year_day_month_format
        7. month Xth year (Month in abbreviation or full)           _gregorian_month_day_year_format
        8. month Xth      (Month in abbreviation or full)           _gregorian_month_day_format
        9. Xth month      (Month in abbreviation or full)           _gregorian_day_month_format
        10. "today" variants                                        _todays_date
        11. "tomorrow" variants                                     _tomorrows_date
        12. "yesterday" variants                                    _yesterdays_date
        13. "_day_after_tomorrow" variants                           _day_after_tomorrow
        14. "_day_before_yesterday" variants                         _day_before_yesterday
        15. "next <day of week>" variants                           _day_in_next_week
        16. "this <day of week>" variants                           _day_within_one_week
        17. probable date from only Xth                             _date_identification_given_day
        18. probable date from only Xth this month                  _date_identification_given_day_and_current_month
        19. probable date from only Xth next month                  _date_identification_given_day_and_next_month
        20. "everyday" variants                                     _date_identification_everyday
        21. "everyday except weekends" variants                     _date_identification_everyday_except_weekends
        22. "everday except weekdays" variants                      _date_identification_everyday_except_weekdays
        23.                                                         _weeks_identification
        24.                                                         _weeks_range_identification
        25.                                                         _dates_range_identification
        
        Not all separator are lsited above. See respective methods for detail on structures of these formats

    Note:
        text and tagged_text will have a extra space prepended and appended after calling detect_entity(text)
    """

    def __init__(self, entity_name, timezone=pytz.timezone('UTC')):
        """Initializes a DateDetector object with given entity_name and pytz timezone object

        Args:
            entity_name: A string by which the detected date entity substrings would be replaced with on calling
                        detect_entity()
            timezone: Optional, pytz.timezone object used for getting current time, default is pytz.timezone('UTC')

        """
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.date = []
        self.original_date_text = []
        self.month_dictionary = {}
        self.day_dictionary = {}
        self.entity_name = entity_name
        self.regx_to_process = Regex([(r'[\/]', r'')])
        self.regx_to_process_text = Regex([(r'[\,]', r'')])
        self.tag = '__' + entity_name + '__'
        self.timezone = timezone
        self.date_object = datetime.datetime.now(self.timezone)
        self.month_dictionary = MONTH_DICT
        self.day_dictionary = DAY_DICT

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
        self.text = self.regx_to_process_text.text_substitute(self.text)
        self.processed_text = self.text
        self.tagged_text = self.text
        date_data = self._detect_date()
        self.date = date_data[0]
        self.original_date_text = date_data[1]
        return date_data

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
        # print 'detection for default task'
        date_list = []
        original_list = []
        date_list, original_list = self.get_exact_date(date_list, original_list)
        date_list, original_list = self.get_possible_date(date_list, original_list)
        return date_list, original_list

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
        date_list, original_list = self._gregorian_year_month_day_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_advanced_day_month_year_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_day_with_ordinals_month_year_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_advanced_year_month_day_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_year_day_month_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_month_day_year_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_day_month_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_month_day_format(date_list, original_list)
        self._update_processed_text(original_list)

        date_list, original_list = self._day_after_tomorrow(date_list, original_list)
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

    def get_possible_date(self, date_list=None, original_list=None):
        """
        Detects possible dates for if there are missing parts of date - day, month, year assuming sensible defaults.
        Also detects "everyday","only weekdays", "only weekends","A to B" type ranges in days of week or months,
        and their variants/ synonyms and returns probable dates by using current year, month, week defaults for parts of
        dates that are missing or that include relative ranges. Type of dates returned by this method include
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
        date_list, original_list = self._date_identification_everyday(date_list, original_list, n_days=15)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_identification_everyday_except_weekends(date_list, original_list,
                                                                                      n_days=15)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_identification_everyday_except_weekdays(date_list, original_list,
                                                                                      n_days=50)
        self._update_processed_text(original_list)
        date_list, original_list = self._day_within_one_week(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._weeks_identification(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._weeks_range_identification(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._dates_range_identification(date_list, original_list)
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
        patterns = re.findall(
            r'\b((0?[1-9]|[12][0-9]|3[01])\s?[/\-\.]\s?(0?[1-9]|1[0-2])\s?[/\-\.]\s?((?:20|19)?[0-9]{2}))\b',
            self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[1]
            mm = pattern[2]
            yy = pattern[3]

            if len(yy) == 2:
                yy = '20' + yy

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
            "31/1/31", "97/2/21", "2517/12/01"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        # print '-- calling _gregorian_year_month_day_format() ---'
        # print 'processed text : ', self.processed_text
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        patterns = re.findall(
            r'\b(((?:20|19)[0-9]{2})\s?[/\-\.]\s?(0?[1-9]|1[0-2])\s?[/\-\.]\s?(0?[1-9]|[12][0-9]|3[01]))\b',
            self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[1]
            mm = pattern[2]
            yy = pattern[3]

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
        # print '-- calling _gregorian_advanced_day_month_year_format() ---'

        # print 'processed text : ', self.processed_text
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        patterns = re.findall(
            r'\b((0?[1-9]|[12][0-9]|3[01])\s?[/ -\.]\s?([A-Za-z]+)\s?[/ -\.]\s?((?:20|19)?[0-9]{2}))\b',
            self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[1]
            probable_mm = pattern[2]
            yy = pattern[3]

            if len(yy) == 2:
                yy = '20' + yy

            mm = self.__get_month_index(probable_mm)
            # print 'mm: ', mm
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
            oridinal indicator: "st", "nd", "rd", "th", space
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
        # print '-- calling _gregorian_day_with_ordinals_month_year_format() ---'
        # print 'processed text : ', self.processed_text
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        regex_pattern = r'\b((0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?\s?(?:of)?[\s\,]\s?([A-Za-z]+)[\s\,]\s?' + \
                        r'((?:20|19)?[0-9]{2}))\b'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[1]
            probable_mm = pattern[2]
            yy = pattern[3]

            if len(yy) == 2:
                yy = '20' + yy

            mm = self.__get_month_index(probable_mm)
            # print 'mm: ', mm
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
            "2199 Nov 21", "1972 january 2", "2014 November 6", "2014-Nov-09", "2015/Nov/94"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        # print '-- calling _gregorian_advanced_year_month_day_format() ---'
        # print 'processed text : ', self.processed_text
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        patterns = re.findall(r'\b(((?:20|19)[0-9]{2})\s?[/ \-]\s?([A-Za-z]+)\s?[/ \-]\s?(0?[1-9]|[12][0-9]|3[01]))\b',
                              self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[3]
            probable_mm = pattern[2]
            yy = pattern[1]
            mm = self.__get_month_index(probable_mm)
            # print 'mm: ', mm
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

        format: <year><separator><day><Optional oridinal indicator><separator><month>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            year: yy, yyyy
            separator: ",", space
            oridinal indicator: "st", "nd", "rd", "th", space

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "2199 21st Nov", "1972, 2 january", "14,November,6"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        # print '-- calling _gregorian_year_day_month_format() ---'

        # print 'processed text : ', self.processed_text
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        patterns = re.findall(
            r'\b(((?:20|19)[0-9]{2})[\ \,]\s?(0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?[\ \,]([A-Za-z]+))\b',
            self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[2]
            probable_mm = pattern[3]
            yy = pattern[1]
            mm = self.__get_month_index(probable_mm)
            # print 'mm: ', mm
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

    def _gregorian_month_day_year_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <month><separator><day><Optional oridinal indicator><separator><year>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            year: yy, yyyy
            separator: ",", space
            oridinal indicator: "st", "nd", "rd", "th", space

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "Nov 21st 2199", "january, 2 1972", "12,November,13"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        # print '-- calling _gregorian_month_day_year_format() ---'
        # print 'processed text : ', self.processed_text
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        patterns = re.findall(
            r'\b(([A-Za-z]+)[\ \,]\s?(0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?[\ \,]\s?((?:20|19)?[0-9]{2}))\b',
            self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[2]
            probable_mm = pattern[1]
            yy = pattern[3]
            mm = self.__get_month_index(probable_mm)

            if len(yy) == 2:
                yy = '20' + yy
            # print 'mm: ', mm
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

    def _gregorian_month_day_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <month><separator><day><Optional oridinal indicator>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            separator: ",", space
            oridinal indicator: "st", "nd", "rd", "th", space

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
        # print '-- calling _gregorian_month_day_format() ---'

        # print 'processed text : ', self.processed_text
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        patterns = re.findall(r'\b(([A-Za-z]+)[\ \,]\s?(0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?)\b',
                              self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[2]
            probable_mm = pattern[1]
            mm = self.__get_month_index(probable_mm)
            if dd:
                dd = int(dd)
            if mm:
                mm = int(mm)
            if self.date_object.month > mm:
                yy = self.date_object.year + 1
            elif self.date_object.day > dd and self.date_object.month == mm:
                yy = self.date_object.year + 1
            else:
                yy = self.date_object.year

            # print 'mm: ', mm
            if mm:
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

        format: <day><Optional oridinal indicator><separator><month>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            separator: ",", space
            oridinal indicator: "st", "nd", "rd", "th", space

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
        # print '-- calling _gregorian_day_month_format() ---'

        # print 'processed text : ', self.processed_text
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        patterns = re.findall(r'\b((0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?[\ \,]\s?(?:of)?\s?([A-Za-z]+))\b',
                              self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[1]
            probable_mm = pattern[2]
            mm = self.__get_month_index(probable_mm)
            if dd:
                dd = int(dd)
            if mm:
                mm = int(mm)
            if self.date_object.month > mm:
                yy = self.date_object.year + 1
            elif self.date_object.day > dd and self.date_object.month == mm:
                yy = self.date_object.year + 1
            else:
                yy = self.date_object.year
            # print 'mm: ', mm
            if mm:
                date_dict = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_list.append(date_dict)
                original_list.append(original)
        return date_list, original_list

    # TODO this method has hinglish words
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
        # print '-- calling _todays_date() ---'
        # print 'processed text : ', self.processed_text
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\b(today|2dy|2day|tody|aaj|aj|tonight)\b',
                              self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern
            dd = self.date_object.day
            mm = self.date_object.month
            yy = self.date_object.year
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
        # print '-- calling tommorows_date() ---'
        # print 'processed text : ', self.processed_text
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\b(tomorrow|2morow|2mrw|2mrow|next day|tommorr?ow|tomm?orow)\b',
                              self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern
            tommorow = self.date_object + datetime.timedelta(days=1)
            dd = tommorow.day
            mm = tommorow.month
            yy = tommorow.year
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
        # print '-- calling _yesterdays_date() ---'
        # print 'processed text : ', self.processed_text
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        patterns = re.findall(r'\b(yesterday|sterday|yesterdy|yestrdy|yestrday|previous day|prev day|prevday)\b',
                              self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]
            yesterday = self.date_object - datetime.timedelta(days=1)
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
        # print '-- calling _day_after_tomorrow() ---'
        # print 'processed text : ', self.processed_text
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\b((da?y afte?r)\s+(tomorrow|2morow|2mrw|2mrow|kal|2mrrw))\b',
                              self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]
            day_after = self.date_object + datetime.timedelta(days=2)
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
        # print '-- calling _day_before_yesterday() ---'
        # print 'processed text : ', self.processed_text
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        patterns = re.findall(r'\b((da?y befo?re)\s+(yesterday|sterday|yesterdy|yestrdy|yestrday))\b',
                              self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]
            day_before = self.date_object - datetime.timedelta(days=2)
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
        Detects "next <day of the week>" and its variants and returns the date on that day in the next week. Week starts
        with Sunday and ends with Saturday

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
        # print '-- calling _day_in_next_week() ---'
        # print 'processed text : ', self.processed_text
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        patterns = re.findall(r'\b((ne?xt)\s+([A-Za-z]+))\b', self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]
            probable_day = pattern[2]
            day = self.__get_day_index(probable_day)
            current_day = self.__get_day_index(self.date_object.strftime("%A"))
            if day and current_day:
                date_after_days = int(day) - int(current_day) + 7
                day_to_set = self.date_object + datetime.timedelta(days=date_after_days)
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
        # print '-- calling _day_within_one_week() ---'
        # print 'processed text : ', self.processed_text
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        patterns = re.findall(r'\b((this|dis|coming|on|for|fr)*[\s\-]+([A-Za-z]+))\b', self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0].strip()
            probable_day = pattern[2]
            day = self.__get_day_index(probable_day)
            current_day = self.__get_day_index(self.date_object.strftime("%A"))
            if day and current_day:
                if int(current_day) <= int(day):
                    date_after_days = int(day) - int(current_day)
                else:
                    date_after_days = int(day) - int(current_day) + 7
                day_to_set = self.date_object + datetime.timedelta(days=date_after_days)
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

        format: <day><Optional space><oridnal indicator>
        where each part is in of one of the formats given against them
            day: d, dd
            oridinal indicator: "st", "nd", "rd", "th"

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
        # print '-- calling day_of_current_month() ---'
        # print 'processed text : ', self.processed_text
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        patterns = re.findall(r'\b((0?[1-9]|[12][0-9]|3[01])\s*(?:nd|st|rd|th))\b', self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]

            dd = pattern[1]
            mm = self.date_object.month
            yy = self.date_object.year

            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_POSSIBLE_DAY
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _date_identification_given_day_and_current_month(self, date_list=None, original_list=None):
        """
        Detects probable date given day part and . The year is assumed to be current year
        Consider checking if the returned detected date is valid.

        Matches <day><Optional oridnal indicator><"this" or "dis"><Optional "current" or "curent"><"mnth" or "month">
        where each part is in of one of the formats given against them
            day: d, dd
            oridinal indicator: "st", "nd", "rd", "th"
        
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
        # print '-- calling day_of_current_month() ---'
        # print 'processed text : ', self.processed_text
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = r'\b((0?[1-9]|[12][0-9]|3[01])\s*(?:nd|st|rd|th)?\s*(?:of)?\s*(?:this|dis)\s*(?:curr?ent)?' + \
                        r'\s*(month|mnth))\b'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]

            dd = pattern[1]
            mm = self.date_object.month
            yy = self.date_object.year

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

        Matches <day><Optional oridnal indicator><"this" or "dis"><"next" variants><"mnth" or "month">
        where each part is in of one of the formats given against them
            day: d, dd
            oridinal indicator: "st", "nd", "rd", "th"
            "next" variants: "next", "nxt", "comming", "coming", "commin", "following", "folowin", "followin",
                             "folowing"
        
        Optional "of" is allowed after ordinal indicator, example "dd th of this next month"

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
        # print '-- calling day_of_next_month() ---'
        # print 'processed text : ', self.processed_text
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        regex_pattern = r'\b((0?[1-9]|[12][0-9]|3[01])\s*(?:nd|st|rd|th)?\s*(?:of)?\s*' + \
                        r'(?:next|nxt|comm?ing?|foll?owing?|)\s*(mo?nth))\b'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]

            dd = pattern[1]
            previous_mm = self.date_object.month
            yy = self.date_object.year
            mm = int(previous_mm) + 1
            if mm > 12:
                mm = 1

            date_dict = {
                'dd': int(dd),
                'mm': mm,
                'yy': int(yy),
                'type': TYPE_POSSIBLE_DAY
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _date_identification_everyday(self, date_list=None, original_list=None, n_days=30):
        """
        Detects "everday" and its variants and returns all the dates of the next n_days from current date.
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
        # print '-- calling everyday() ---'
        # print 'processed text : ', self.processed_text
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        now = datetime.datetime.now()
        end = now + datetime.timedelta(days=n_days)
        patterns = re.findall(r'\b((everyday|daily|every\s{0,3}day|all\sdays?))\b', self.processed_text.lower())
        # print 'pattern : ', patterns
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
        now = datetime.datetime.now()
        end = now + datetime.timedelta(days=n_days)
        patterns = re.findall(r'\b(([eE]veryday|[dD]aily)|all\sdays[\s]?except[\s]?([wW]eekend|[wW]eekends))\b',
                              self.processed_text.lower())

        if not patterns:
            patterns = re.findall(r'\b(weekdays|weekday|week day|week days| all weekdays)\b',
                                  self.processed_text.lower())
        constant_type = WEEKDAYS
        if self._is_everyday_present(self.text):
            constant_type = REPEAT_WEEKDAYS
        today = now.weekday()
        count = 0
        weekend = []
        date_day = datetime.datetime.now()
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
        now = datetime.datetime.now()
        end = now + datetime.timedelta(days=n_days)
        patterns = re.findall(r'\b(([eE]veryday|[dD]aily)|[eE]very\s*day|all[\s]?except[\s]?([wW]eekday|[wW]eekdays))\b'
                              , self.processed_text.lower())

        if not patterns:
            patterns = re.findall(r'\b((weekends|weekend|week end|week ends | all weekends))\b',
                                  self.processed_text.lower())
        constant_type = WEEKENDS
        if self._is_everyday_present(self.text):
            constant_type = REPEAT_WEEKENDS

        today = now.weekday()
        count = 0
        weekend = []
        date_day = datetime.datetime.now()
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
        format: <day><ordinal inidicator><range separator><day><ordinal inidicator><separator><Optional "of"><month>
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
        # print '-- calling _gregorian_day_month_format() ---'

        # print 'processed text : ', self.processed_text
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_pattern = r'\b((0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?\s?(?:-|to|-|till)\s?' + \
                        r'(0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?[\ \,]\s?(?:of)?\s?([A-Za-z]+))\b'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        # print 'pattern : ', patterns
        for pattern in patterns:
            original = pattern[0]
            dd1 = pattern[1]
            dd2 = pattern[2]
            probable_mm = pattern[3]
            mm = self.__get_month_index(probable_mm)
            yy = self.date_object.year
            # print 'mm: ', mm
            if mm:
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

    def _is_everyday_present(self, text):
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

    def _is_range_present(self, text):
        """
        Detects if there is a "A to B" type range present in the text
        Detects format: <day of week><separator><day of week> OR <month><separator><month>
        where each part is in of one of the formats given against them
            day of week: seven days of the week, in abbreviation or spelled out in full
            month: mmm, mmmm (abbreviation or spelled out in full)
            separator: "to", "-", " - "

        Args:
            text: string to recognize date entities from

        Few valid examples:
            "Jan to Sep", "February to Nov", "December to January", "Mon to Wed", "Sat to Friday"

        Returns:
            Boolean, True if any range is matched according to the format above, False otherwise

        """
        pattern = re.compile(
            r'([a-z]{3,9}\s* to\s* [a-z]{3,9}\s* |\s* [a-z]{3,9}\s* \-\s* [a-z]{3,9} | [a-z]{3,9}-[a-z]{3,9})')
        data = pattern.findall(text)
        if data:
            return True
        else:
            return False

    def _check_current_day(self, date_list):
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

    def _check_date_presence(self, date_list):
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

    # TODO Doc
    def _weeks_identification(self, date_list=None, original_list=None):
        """
        :param date_list:
        :param original_list:
        :return:

        checks for weeks in query
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
            date_list.extend(new_date_list)
            original_list = original_list[:len(date_list)]
        return date_list, original_list

    # TODO Doc
    def _weeks_range_identification(self, date_list=None, original_list=None):
        """
        :param date_list:
        :param original_list:
        :return:

        identify a week range
        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        new_text = self.text.lower().replace(',', '')
        is_everyday = self._is_everyday_present(new_text)
        is_range = self._is_range_present(new_text)
        if is_range and is_everyday and len(date_list) <= 4 and self._check_current_day(date_list):
            date_list = date_list[:2]
            if len(date_list) == 2:
                date_list.sort()
                date_list[0]['type'] = REPEAT_START_RANGE
                date_list[1]['type'] = REPEAT_END_RANGE
        elif is_range and len(date_list) <= 4 and self._check_current_day(date_list):
            date_list = date_list[:2]
            date_list.sort()
            if len(date_list) == 2:
                date_list[0]['type'] = START_RANGE
                date_list[1]['type'] = END_RANGE
            original_list = original_list[:len(date_list)]
        return date_list, original_list

    # TODO Doc
    def _dates_range_identification(self, date_list=None, original_list=None):
        """
        :param date_list:
        :param original_list:
        :return:
        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        new_text = self.text.lower().replace(',', '')
        # Changed to single function because of removal of duplicate function
        is_range = self._is_range_present(new_text)
        if is_range and self._check_date_presence(date_list):
            date_list = date_list[:2]
            date_list.sort()
            if len(date_list) == 2:
                date_list[0]['type'] = DATE_START_RANGE
                date_list[1]['type'] = DATE_END_RANGE
            original_list = original_list[:len(date_list)]
        return date_list, original_list

    def __get_month_index(self, value):
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
