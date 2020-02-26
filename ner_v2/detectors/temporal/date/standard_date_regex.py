# coding=utf-8
from __future__ import absolute_import
import datetime
import re
from dateutil.relativedelta import relativedelta

from ner_v2.detectors.temporal.constant import (DATE_CONSTANT_FILE, DATETIME_CONSTANT_FILE,
                                                RELATIVE_DATE, DATE_LITERAL_TYPE, MONTH_LITERAL_TYPE, WEEKDAY_TYPE,
                                                MONTH_TYPE, ADD_DIFF_DATETIME_TYPE, MONTH_DATE_REF_TYPE,
                                                NUMERALS_CONSTANT_FILE, TYPE_EXACT)
from ner_v2.detectors.temporal.utils import next_weekday, nth_weekday, get_tuple_dict, get_timezone


class BaseRegexDate(object):
    def __init__(self, entity_name, data_directory_path, locale=None, timezone='UTC', past_date_referenced=False):
        """
        Base Regex class which will be imported by language date class by giving their data folder path
        This will create standard regex and their parser to detect date for given language.
        Args:
            data_directory_path (str): path of data folder for given language
            timezone (Optional, str): user timezone default UTC
            past_date_referenced (boolean): if the date reference is in past, this is helpful for text like 'kal',
                                          'parso' to know if the reference is past or future.
            locale (Optional, str): user locale default None
        """
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.date = []
        self.original_date_text = []
        self.entity_name = entity_name
        self.tag = '__' + entity_name + '__'
        self.timezone = get_timezone(timezone)

        self.now_date = datetime.datetime.now(tz=self.timezone)
        self.bot_message = None

        self.past_date_referenced = past_date_referenced

        # dict to store words for date, numerals and words which comes in reference to some date
        self.date_constant_dict = {}
        self.datetime_constant_dict = {}
        self.numerals_constant_dict = {}

        # define dynamic created standard regex from language data files
        self.regex_relative_date = None
        self.regex_day_diff = None
        self.regex_date_month = None
        self.regex_date_ref_month_1 = None
        self.regex_date_ref_month_2 = None
        self.regex_date_ref_month_3 = None
        self.regex_after_days_ref = None
        self.regex_weekday_month_1 = None
        self.regex_weekday_month_2 = None
        self.regex_weekday_diff = None
        self.regex_weekday = None

        # Method to initialise value in regex
        self.init_regex_and_parser(data_directory_path)

        # Variable to define default order in which these regex will work
        self.detector_preferences = [self._gregorian_day_month_year_format,
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
                                     self._detect_weekday
                                     ]

    def detect_date(self, text):
        self.text = text
        self.processed_text = text
        self.tagged_text = text

        date_list, original_list = None, None
        for detector in self.detector_preferences:
            date_list, original_list = detector(date_list, original_list)
            self._update_processed_text(original_list)
        return date_list, original_list

    @staticmethod
    def _sort_choices_on_word_counts(choices_list):
        choices_list.sort(key=lambda s: len(s.split()), reverse=True)
        return choices_list

    def init_regex_and_parser(self, data_directory_path):
        """
        Initialise standard regex from data file
        Args:
            data_directory_path (str): path of data folder for given language
        Returns:
            None
        """
        self.date_constant_dict = get_tuple_dict(data_directory_path.rstrip('/') + '/' + DATE_CONSTANT_FILE)
        self.datetime_constant_dict = get_tuple_dict(data_directory_path.rstrip('/') + '/' + DATETIME_CONSTANT_FILE)
        self.numerals_constant_dict = get_tuple_dict(data_directory_path.rstrip('/') + '/' + NUMERALS_CONSTANT_FILE)

        relative_date_choices = "(" + "|".join(self._sort_choices_on_word_counts(
            [x.lower() for x in self.date_constant_dict if x.strip() != "" and
             self.date_constant_dict[x][1] == RELATIVE_DATE])) + ")"

        date_literal_choices = "(" + "|".join(self._sort_choices_on_word_counts(
            [x.lower() for x in self.date_constant_dict if x.strip() != "" and
             self.date_constant_dict[x][1] == DATE_LITERAL_TYPE])) + ")"

        month_ref_date_choices = "(" + "|".join(self._sort_choices_on_word_counts(
            [x.lower() for x in self.date_constant_dict if x.strip() != "" and
             self.date_constant_dict[x][1] == MONTH_DATE_REF_TYPE])) + ")"

        month_literal_choices = "(" + "|".join(self._sort_choices_on_word_counts(
            [x.lower() for x in self.date_constant_dict if x.strip() != "" and
             self.date_constant_dict[x][1] == MONTH_LITERAL_TYPE])) + ")"

        weekday_choices = "(" + "|".join(self._sort_choices_on_word_counts(
            [x.lower() for x in self.date_constant_dict if x.strip() != "" and
             self.date_constant_dict[x][1] == WEEKDAY_TYPE])) + ")"

        month_choices = "(" + "|".join(self._sort_choices_on_word_counts(
            [x.lower() for x in self.date_constant_dict if x.strip() != "" and
             self.date_constant_dict[x][1] == MONTH_TYPE])) + ")"

        datetime_diff_choices = "(" + "|".join(self._sort_choices_on_word_counts(
            [x.lower() for x in self.datetime_constant_dict if x.strip() != "" and
             self.datetime_constant_dict[x][2] == ADD_DIFF_DATETIME_TYPE])) + ")"

        numeral_variants = "|".join(self._sort_choices_on_word_counts(
            [x.lower() for x in self.numerals_constant_dict if x.strip() != ""]))

        # Date detector Regex
        self.regex_relative_date = re.compile((r'(' + relative_date_choices + r')'), flags=re.UNICODE)

        self.regex_day_diff = re.compile(r'(' + datetime_diff_choices + r'\s*' + date_literal_choices + r')',
                                         flags=re.UNICODE)

        self.regex_date_month = re.compile(r'((\d+|' + numeral_variants + r')\s*(st|nd|th|rd|)\s*' +
                                           month_choices + r')', flags=re.UNICODE)

        self.regex_date_ref_month_1 = \
            re.compile(r'((\d+|' + numeral_variants + r')\s*' + month_ref_date_choices + '\\s*' +
                       datetime_diff_choices + r'\s*' + month_literal_choices + r')', flags=re.UNICODE)

        self.regex_date_ref_month_2 = \
            re.compile(r'(' + datetime_diff_choices + r'\s*' + month_literal_choices + r'\s*[a-z]*\s*(\d+|' +
                       numeral_variants + r')\s+' + month_ref_date_choices + r')', flags=re.UNICODE)

        self.regex_date_ref_month_3 = \
            re.compile(r'((\d+|' + numeral_variants + r')\s*' + month_ref_date_choices + r')', flags=re.UNICODE)

        self.regex_after_days_ref = re.compile(r'((\d+|' + numeral_variants + r')\s*' + date_literal_choices + r'\s+' +
                                               datetime_diff_choices + r')', flags=re.UNICODE)

        self.regex_weekday_month_1 = re.compile(r'((\d+|' + numeral_variants + ')\s*' + weekday_choices + '\\s*' +
                                                datetime_diff_choices + r'\s+' + month_literal_choices + r')',
                                                flags=re.UNICODE)

        self.regex_weekday_month_2 = re.compile(r'(' + datetime_diff_choices + r'\s+' + month_literal_choices +
                                                r'\s*[a-z]*\s*(\d+|' + numeral_variants + ')\s+' +
                                                weekday_choices + r')', flags=re.UNICODE)

        self.regex_weekday_diff = re.compile(r'(' + datetime_diff_choices + r'\s+' + weekday_choices + r')',
                                             flags=re.UNICODE)

        self.regex_weekday = re.compile(r'(' + weekday_choices + r')', flags=re.UNICODE)

    def _get_int_from_numeral(self, numeral):
        """
        Convert string to float for given numeral text
        Args:
            numeral (str): numeral text

        Returns:
            (int): return float corresponding to given numeral
        """
        if numeral.replace('.', '').isdigit():
            return int(numeral)
        else:
            return int(self.numerals_constant_dict[numeral][0])

    def _detect_relative_date(self, date_list=None, original_list=None):
        """
        Parser to detect relative date  like 'kal'(hindi), 'parso'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected
        """
        date_list = date_list or []
        original_list = original_list or []

        date_rel_match = self.regex_relative_date.findall(self.processed_text)
        for date_match in date_rel_match:
            original = date_match[0]
            if not self.past_date_referenced:
                req_date = self.now_date + datetime.timedelta(days=self.date_constant_dict[date_match[1]][0])
            else:
                req_date = self.now_date - datetime.timedelta(days=self.date_constant_dict[date_match[1]][0])

            date = {
                'dd': req_date.day,
                'mm': req_date.month,
                'yy': req_date.year,
                'type': TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_month(self, date_list, original_list):
        """
        Parser to detect date containing specific date and month like '2 july'(hindi), 'pehli august'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected
        """
        date_list = date_list or []
        original_list = original_list or []

        date_month_match = self.regex_date_month.findall(self.processed_text)
        for date_match in date_month_match:
            original = date_match[0]
            dd = self._get_int_from_numeral(date_match[1])
            mm = self.date_constant_dict[date_match[3]][0]

            today_mmdd = "%d%02d" % (self.now_date.month, self.now_date.day)
            today_yymmdd = "%d%02d%02d" % (self.now_date.year, self.now_date.month, self.now_date.day)
            mmdd = "%02d%02d" % (mm, dd)

            if int(today_mmdd) < int(mmdd):
                yymmdd = str(self.now_date.year) + mmdd
                yy = self.now_date.year
            else:
                yymmdd = str(self.now_date.year + 1) + mmdd
                yy = self.now_date.year + 1

            if self.past_date_referenced:
                if int(today_yymmdd) < int(yymmdd):
                    yy -= 1
            date = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_ref_month_1(self, date_list, original_list):
        """
        Parser to detect date containing reference date and month like '2 tarikh is mahine ki'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected

        """
        date_list = date_list or []
        original_list = original_list or []

        date_ref_month_match = self.regex_date_ref_month_1.findall(self.processed_text)

        for date_match in date_ref_month_match:
            original = date_match[0]
            dd = self._get_int_from_numeral(date_match[1])
            if date_match[3] and date_match[4]:
                req_date = self.now_date + \
                           relativedelta(months=self.datetime_constant_dict[date_match[3]][1])
                mm = req_date.month
                yy = req_date.year
            else:
                mm = self.now_date.month
                yy = self.now_date.year

            date = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_ref_month_2(self, date_list, original_list):
        """
        Parser to detect date containing reference date and month like 'agle mahine ki 2 tarikh ko'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected

        """
        date_list = date_list or []
        original_list = original_list or []

        date_ref_month_match = self.regex_date_ref_month_2.findall(self.processed_text)
        for date_match in date_ref_month_match:
            original = date_match[0]
            dd = self._get_int_from_numeral(date_match[3])
            if date_match[1] and date_match[2]:
                req_date = self.now_date + \
                           relativedelta(months=self.datetime_constant_dict[date_match[1]][1])
                mm = req_date.month
                yy = req_date.year
            else:
                mm = self.now_date.month
                yy = self.now_date.year

            date = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_ref_month_3(self, date_list, original_list):
        """
        Parser to detect date containing reference date and month like '2 tarikh ko'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected

        """
        date_list = date_list or []
        original_list = original_list or []

        date_ref_month_match = self.regex_date_ref_month_3.findall(self.processed_text)
        for date_match in date_ref_month_match:
            original = date_match[0]
            dd = self._get_int_from_numeral(date_match[1])
            if (self.now_date.day > dd and self.past_date_referenced) or \
                    (self.now_date.day <= dd and not self.past_date_referenced):
                mm = self.now_date.month
                yy = self.now_date.year
            elif self.now_date.day <= dd and self.past_date_referenced:
                req_date = self.now_date - relativedelta(months=1)
                mm = req_date.month
                yy = req_date.year
            else:
                req_date = self.now_date + relativedelta(months=1)
                mm = req_date.month
                yy = req_date.year
            date = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_diff(self, date_list, original_list):
        """
        Parser to detect date containing reference with current date like 'pichhle din'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected

        """
        date_list = date_list or []
        original_list = original_list or []

        diff_day_match = self.regex_day_diff.findall(self.processed_text)
        for date_match in diff_day_match:
            original = date_match[0]
            req_date = self.now_date + datetime.timedelta(days=self.datetime_constant_dict[date_match[1]][1])
            date = {
                'dd': req_date.day,
                'mm': req_date.month,
                'yy': req_date.year,
                'type': TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_after_days(self, date_list, original_list):
        """
        Parser to detect date containing reference with current date like '2 din hua'(hindi), '2 din baad'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected

        """
        date_list = date_list or []
        original_list = original_list or []

        after_days_match = self.regex_after_days_ref.findall(self.processed_text)
        for date_match in after_days_match:
            original = date_match[0]
            day_diff = self._get_int_from_numeral(date_match[1])
            req_date = self.now_date + relativedelta(days=day_diff * self.datetime_constant_dict[date_match[3]][1])
            date = {
                'dd': req_date.day,
                'mm': req_date.month,
                'yy': req_date.year,
                'type': TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_weekday_ref_month_1(self, date_list, original_list):
        """
        Parser to detect date containing referenced week and month 'agle month ka pehla monday'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected
        """
        date_list = date_list or []
        original_list = original_list or []

        weekday_month_match = self.regex_weekday_month_1.findall(self.processed_text)
        for date_match in weekday_month_match:
            original = date_match[0]
            n_weekday = self._get_int_from_numeral(date_match[1])
            weekday = self.date_constant_dict[date_match[2]][0]
            ref_date = self.now_date + relativedelta(months=self.datetime_constant_dict[date_match[3]][1])
            req_date = nth_weekday(n_weekday, weekday, ref_date)
            date = {
                'dd': req_date.day,
                'mm': req_date.month,
                'yy': req_date.year,
                'type': TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_weekday_ref_month_2(self, date_list, original_list):
        """
        Parser to detect date containing referenced week and month like'pehla monday agle month ka'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected
        """
        date_list = date_list or []
        original_list = original_list or []

        weekday_month_match = self.regex_weekday_month_2.findall(self.processed_text)
        for date_match in weekday_month_match:
            original = date_match[0]
            n_weekday = self._get_int_from_numeral(date_match[3])
            weekday = self.date_constant_dict[date_match[4]][0]
            ref_date = self.now_date + relativedelta(months=self.datetime_constant_dict[date_match[1]][1])
            req_date = nth_weekday(weekday, n_weekday, ref_date)
            date = {
                'dd': req_date.day,
                'mm': req_date.month,
                'yy': req_date.year,
                'type': TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_weekday_diff(self, date_list, original_list):
        """
        Parser to detect date containing referenced weekday from present day like 'aane wala tuesday'(hindi),
            'agla somvar'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected
        """
        date_list = date_list or []
        original_list = original_list or []

        weekday_ref_match = self.regex_weekday_diff.findall(self.processed_text)
        for date_match in weekday_ref_match:
            original = date_match[0]
            n = self.datetime_constant_dict[date_match[1]][1]
            weekday = self.date_constant_dict[date_match[2]][0]
            req_date = next_weekday(current_date=self.now_date, n=n, weekday=weekday)
            date = {
                'dd': req_date.day,
                'mm': req_date.month,
                'yy': req_date.year,
                'type': TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_weekday(self, date_list, original_list):
        """
        Parser to detect date containing referenced weekday without referencing any particular day like
        'mangalvar'(hindi), 'ravivar'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected

        """
        date_list = date_list or []
        original_list = original_list or []

        weekday_ref_match = self.regex_weekday.findall(self.processed_text)
        for date_match in weekday_ref_match:
            original = date_match[0]
            weekday = self.date_constant_dict[date_match[1]][0]
            req_date = next_weekday(current_date=self.now_date, n=0, weekday=weekday)
            date = {
                'dd': req_date.day,
                'mm': req_date.month,
                'yy': req_date.year,
                'type': TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

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
        translate_number = self.convert_numbers(self.processed_text.lower())
        patterns = regex_pattern.findall(translate_number)
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
                return date_list, original_list

            date = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_EXACT
            }
            date_list.append(date)
            # original = self.regx_to_process.text_substitute(original)
            if translate_number != self.processed_text.lower():
                match = re.search(original, translate_number)
                original_list.append(self.processed_text[(match.span()[0]):(match.span()[1])])
            else:
                original_list.append(original)
        return date_list, original_list

    @staticmethod
    def convert_numbers(text):
        result = text
        digit = re.compile(r'(\d)', re.U)
        groups = digit.findall(result)
        for group in groups:
            result = result.replace(group, str(int(group)))
        return result

    def normalize_year(self, year):
        """
        Normalize two digit year to four digits by taking into consideration the bot message. Useful in cases like
        date of birth where past century is preferred than current. If no bot message is given it falls back to
        current century

        Args:[{"key":"message","value":"१/३/६६","description":""}]
            year (str): Year string to normalize

        Returns:
            str: year in four digits
        """
        # past_regex = re.compile(ur'birth|bday|dob|born|जन्म|जन्मदिन|పుట్టినరోజు|పుట్టిన', flags=re.UNICODE)
        past_regex = None
        # Todo: Add more language variations of birthday.
        present_regex = None
        future_regex = None
        this_century = int(str(self.now_date.year)[:2])
        if len(year) == 2:
            if (((self.bot_message and past_regex and past_regex.search(self.bot_message))
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

    def _update_processed_text(self, original_date_list):
        """
        Replaces detected date with tag generated from entity_name used to initialize the object with

        A final string with all dates replaced will be stored in object's tagged_text attribute
        A string with all dates removed will be stored in object's processed_text attribute

        Args:
            original_date_list (list): list of substrings of original text to be replaced with tag
                                       created from entity_name
        """
        for detected_text in original_date_list:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')


class DateDetector(BaseRegexDate):
    def __init__(self, entity_name, data_directory_path, timezone='UTC', past_date_referenced=False):
        super(DateDetector, self).__init__(entity_name=entity_name,
                                           data_directory_path=data_directory_path,
                                           timezone=timezone,
                                           past_date_referenced=past_date_referenced)
