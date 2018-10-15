from chatbot_ner.config import ner_logger
from ner_v2.detectors.constant import TYPE_EXACT
from ner_v2.detectors.temporal.constant import DATE_CONSTANT_FILE, DATETIME_CONSTANT_FILE, CONSTANT_FILE_KEY, \
    RELATIVE_DATE, DATE_LITERAL_TYPE, MONTH_LITERAL_TYPE, WEEKDAY_TYPE, \
    MONTH_TYPE, ADD_DIFF_DATETIME_TYPE, MONTH_DATE_REF_TYPE, NUMERALS_CONSTANT_FILE
import pytz
import re
import datetime
from dateutil.relativedelta import relativedelta

from ner_v2.detectors.temporal.utils import next_weekday, nth_weekday, get_tuple_list


class BaseRegexDate(object):
    def __init__(self, data_directory_path, timezone='UTC', is_past_referenced=False):
        """
        Base Regex class which will be imported by language date class by giving their data folder path
        This will create standard regex and their parser to detect date for given language.
        Args:
            data_directory_path (str): path of data folder for given language
            timezone (str): user timezone default UTC
            is_past_referenced (boolean): if the date reference is in past, this is helpful for text like 'kal',
                                          'parso' to know if the reference is past or future.
        """
        self.text = ''
        self.processed_text = ''
        self.tag = ''

        try:
            self.timezone = pytz.timezone(timezone)
        except Exception as e:
            ner_logger.debug('Timezone error: %s ' % e)
            self.timezone = pytz.timezone('UTC')
            ner_logger.debug('Default timezone passed as "UTC"')

        self.now_date = datetime.datetime.now(tz=self.timezone)
        self.is_past_referenced = is_past_referenced

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
        self.detector_preferences = [self._detect_relative_date,
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

    def init_regex_and_parser(self, data_directory_path):
        """
        Initialise standard regex from data file
        Args:
            data_directory_path (str): path of data folder for given language
        Returns:
            None
        """
        self.date_constant_dict = get_tuple_list(data_directory_path.rstrip('/') + '/' + DATE_CONSTANT_FILE)
        self.datetime_constant_dict = get_tuple_list(data_directory_path.rstrip('/') + '/' + DATETIME_CONSTANT_FILE)
        self.numerals_constant_dict = get_tuple_list(data_directory_path.rstrip('/') + '/' + NUMERALS_CONSTANT_FILE)

        relative_date_choices = "(" + " | ".join([x for x in self.date_constant_dict if
                                                  self.date_constant_dict[x][1] == RELATIVE_DATE]) + ")"
        date_literal_choices = "(" + " | ".join([x for x in self.date_constant_dict if
                                                 self.date_constant_dict[x][1] == DATE_LITERAL_TYPE]) + ")"
        month_ref_date_choices = "(" + " | ".join([x for x in self.date_constant_dict
                                                   if self.date_constant_dict[x][1] == MONTH_DATE_REF_TYPE]) + ")"
        month_literal_choices = "(" + " | ".join([x for x in self.date_constant_dict
                                                  if self.date_constant_dict[x][1] == MONTH_LITERAL_TYPE]) + ")"
        weekday_choices = "(" + " | ".join([x for x in self.date_constant_dict
                                            if self.date_constant_dict[x][1] == WEEKDAY_TYPE]) + ")"
        month_choices = "(" + " | ".join([x for x in self.date_constant_dict
                                          if self.date_constant_dict[x][1] == MONTH_TYPE]) + ")"
        datetime_diff_choices = "(" + " | ".join([x for x in self.datetime_constant_dict if
                                                  self.datetime_constant_dict[x][2] == ADD_DIFF_DATETIME_TYPE]) + ")"

        # Date detector Regex
        self.regex_relative_date = re.compile((r'(\b' + relative_date_choices + r'\b)'))
        self.regex_day_diff = re.compile(r'(' + datetime_diff_choices + r'\s*' + date_literal_choices + r')')
        self.regex_date_month = re.compile(r'((\d+)\s*' + month_choices + r')')
        self.regex_date_ref_month_1 = re.compile(r'((\d+)\s*' + month_ref_date_choices + '\\s*' +
                                                 datetime_diff_choices + r'\s*' + month_literal_choices + r')')
        self.regex_date_ref_month_2 = re.compile(r'(' + datetime_diff_choices + r'\s*' + month_literal_choices +
                                                 r'\s*[a-z]*\s*(\d+)\s+' + month_ref_date_choices + r')')
        self.regex_date_ref_month_3 = re.compile(r'((\d+)\s*' + month_ref_date_choices + r')')
        self.regex_after_days_ref = re.compile(r'((\d+)\s*' + date_literal_choices + r'\s+' +
                                               datetime_diff_choices + r')')
        self.regex_weekday_month_1 = re.compile(r'((\d+)\s*' + weekday_choices + '\\s*' +
                                                datetime_diff_choices + r'\s+' + month_literal_choices + r')')
        self.regex_weekday_month_2 = re.compile(r'(' + datetime_diff_choices + r'\s+' + month_literal_choices +
                                                r'\s*[a-z]*\s*(\d+)\s*' + weekday_choices + r')')
        self.regex_weekday_diff = re.compile(r'(' + datetime_diff_choices + r'\s*' + weekday_choices + r')')
        self.regex_weekday = re.compile(r'(' + weekday_choices + r')')

    def _detect_relative_date(self, date_list=None, original_list=None):
        """
        Parser to detect relative date  like 'kal'(hindi), 'parso'(hindi)
        Args:

        Returns:
            (dict): containing detected day, month, year if detected else empty dict
        """
        date_list = date_list or []
        original_list = original_list or []

        date_rel_match = self.regex_relative_date.findall(self.processed_text)
        for date_match in date_rel_match:
            original = date_match[0]
            if not self.is_past_referenced:
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
            (dict): containing detected day, month, year if detected else empty dict
        """
        date_list = date_list or []
        original_list = original_list or []

        date_month_match = self.regex_date_month.findall(self.processed_text)
        for date_match in date_month_match:
            original = date_match[0]
            dd = int(date_match[1])
            mm = self.date_constant_dict[date_match[2]][0]

            today_mmdd = "%d%02d" % (self.now_date.month, self.now_date.day)
            today_yymmdd = "%d%02d%02d" % (self.now_date.year, self.now_date.month, self.now_date.day)
            mmdd = "%02d%02d" % (mm, dd)

            if int(today_mmdd) < int(mmdd):
                yymmdd = str(self.now_date.year) + mmdd
                yy = self.now_date.year
            else:
                yymmdd = str(self.now_date.year + 1) + mmdd
                yy = self.now_date.year + 1

            if self.is_past_referenced:
                if int(today_yymmdd) < int(yymmdd):
                    yy -= 1
            date = {
                'dd': dd,
                'mm': mm,
                'yy': yy,
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
            (dict): containing detected day, month, year if detected else empty dict
        """
        date_list = date_list or []
        original_list = original_list or []

        date_ref_month_match = self.regex_date_ref_month_1.findall(self.processed_text)

        for date_match in date_ref_month_match:
            original = date_match[0]
            dd = int(date_match[1])
            if date_match[3] and date_match[4]:
                req_date = self.now_date + \
                           relativedelta(months=self.datetime_constant_dict[date_match[3]][1])
                mm = req_date.month
                yy = req_date.year
            else:
                mm = self.now_date.month
                yy = self.now_date.year

            date = {
                'dd': dd,
                'mm': mm,
                'yy': yy,
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
            (dict): containing detected day, month, year if detected else empty dict
        """
        date_list = date_list or []
        original_list = original_list or []

        date_ref_month_match = self.regex_date_ref_month_2.findall(self.processed_text)
        for date_match in date_ref_month_match:
            original = date_match[0]
            dd = int(date_match[3])
            if date_match[1] and date_match[2]:
                req_date = self.now_date + \
                           relativedelta(months=self.datetime_constant_dict[date_match[1]][1])
                mm = req_date.month
                yy = req_date.year
            else:
                mm = self.now_date.month
                yy = self.now_date.year

            date = {
                'dd': dd,
                'mm': mm,
                'yy': yy,
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
            (dict): containing detected day, month, year if detected else empty dict
        """
        date_list = date_list or []
        original_list = original_list or []

        date_ref_month_match = self.regex_date_ref_month_3.findall(self.processed_text)
        for date_match in date_ref_month_match:
            original = date_match[0]
            dd = int(date_match[1])
            if self.now_date.day < dd:
                mm = self.now_date.month
                yy = self.now_date.year
            else:
                req_date = self.now_date + relativedelta(months=1)
                mm = req_date.month
                yy = req_date.year
            date = {
                'dd': dd,
                'mm': mm,
                'yy': yy,
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
            (dict): containing detected day, month, year if detected else empty dict
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
            (dict): containing detected day, month, year if detected else empty dict
        """
        date_list = date_list or []
        original_list = original_list or []

        after_days_match = self.regex_after_days_ref.findall(self.processed_text)
        for date_match in after_days_match:
            original = date_match[0]
            day_diff = int(date_match[1])
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
            (dict): containing detected day, month, year if detected else empty dict
        """
        date_list = date_list or []
        original_list = original_list or []

        weekday_month_match = self.regex_weekday_month_1.findall(self.processed_text)
        for date_match in weekday_month_match:
            original = date_match[0]
            n_weekday = int(date_match[1])
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
            (dict): containing detected day, month, year if detected else empty dict
        """
        date_list = date_list or []
        original_list = original_list or []

        weekday_month_match = self.regex_weekday_month_2.findall(self.processed_text)
        for date_match in weekday_month_match:
            original = date_match[0]
            n_weekday = int(date_match[3])
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
            (dict): containing detected day, month, year if detected else empty dict
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

    def _detect_weekday(self,date_list, original_list):
        """
        Parser to detect date containing referenced weekday without referencing any particular day like
        'mangalvar'(hindi), 'ravivar'(hindi)
        Args:

        Returns:
            (dict): containing detected day, month, year if detected else empty dict
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

    def _detect_date_from_standard_regex(self, text, tag):
        """
        Method which will detect date from given text by running the parser in order defined in
        self.detector_preferences
        Args:
            text (str): text from which date has to be detected
            tag (str): tag by which entity in text will be replaced

        Returns:
            (dict): containing detected day, month, year if detected else empty dict
        """
        date_list, original_list = None, None
        self.text = text
        self.processed_text = self.text
        self.tag = tag
        for detector in self.detector_preferences:
            date_list, original_list = detector(date_list, original_list)
            self._update_processed_text(original_list)

        return date_list, original_list
