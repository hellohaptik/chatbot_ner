from chatbot_ner.config import ner_logger
from ner_v1.detectors.constant import TYPE_EXACT
from ner_v1.detectors.temporal.constant import DATE_CONSTANT_FILE, DATETIME_CONSTANT_FILE, CONSTANT_FILE_KEY, \
    RELATIVE_DATE, DATE_LITERAL_TYPE, MONTH_LITERAL_TYPE, WEEKDAY_TYPE, \
    MONTH_TYPE, ADD_DIFF_DATETIME_TYPE, MONTH_DATE_REF_TYPE, NUMERALS_CONSTANT_FILE
import pytz
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from ner_v1.detectors.temporal.utils import next_weekday, nth_weekday, get_tuple_list


class BaseRegexDate(object):
    def __init__(self, data_directory_path, timezone='UTC', is_past_referenced=False):

        self.text = ''
        try:
            self.timezone = pytz.timezone(timezone)
        except Exception as e:
            ner_logger.debug('Timezone error: %s ' % e)
            self.timezone = pytz.timezone('UTC')
            ner_logger.debug('Default timezone passed as "UTC"')

        self.now_date = datetime.now(tz=self.timezone)
        self.is_past_referenced = is_past_referenced

        self.date_constant_dict = {}
        self.datetime_constant_dict = {}
        self.numerals_constant_dict = {}

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

        self.init_regex_and_parser(data_directory_path)

        self.detector_preferences = [self._detect_relative_date,
                                     self._detect_date_month,
                                     self._detect_date_ref_month_1,
                                     self._detect_date_ref_month_2(),
                                     self._detect_date_ref_month_3(),
                                     self._detect_date_diff(),
                                     self._detect_after_days(),
                                     self._detect_weekday_ref_month_1(),
                                     self._detect_weekday_ref_month_2(),
                                     self._detect_weekday_diff(),
                                     self._detect_weekday()
                                     ]

    def init_regex_and_parser(self, data_directory_path):
        self.date_constant_dict = get_tuple_list(data_directory_path.rstrip('/') + '/' + DATE_CONSTANT_FILE)
        self.datetime_constant_dict = get_tuple_list(data_directory_path.rstrip('/') + '/' + DATETIME_CONSTANT_FILE)
        self.numerals_constant_dict = get_tuple_list(data_directory_path.rstrip('/') + '/' + NUMERALS_CONSTANT_FILE)

        relative_date_or_condition = "(" + " | ".join([x for x in self.date_constant_dict if
                                                       self.date_constant_dict[x][1] == RELATIVE_DATE]) + ")"
        date_literal_or_condition = "(" + " | ".join([x for x in self.date_constant_dict if
                                                      self.date_constant_dict[x][1] == DATE_LITERAL_TYPE]) + ")"
        month_date_or_condition = "(" + " | ".join([x for x in self.date_constant_dict
                                                    if self.date_constant_dict[x][1] == MONTH_DATE_REF_TYPE]) + ")"
        month_literal_or_condition = "(" + " | ".join([x for x in self.date_constant_dict
                                                       if self.date_constant_dict[x][1] == MONTH_LITERAL_TYPE]) + ")"
        weekday_or_condition = "(" + " | ".join([x for x in self.date_constant_dict
                                                 if self.date_constant_dict[x][1] == WEEKDAY_TYPE]) + ")"
        month_or_condition = "(" + " | ".join([x for x in self.date_constant_dict
                                               if self.date_constant_dict[x][1] == MONTH_TYPE]) + ")"
        datetime_diff_or_condition = "(" + " | ".join([x for x in self.datetime_constant_dict
                                                       if self.datetime_constant_dict[x][2] == ADD_DIFF_DATETIME_TYPE]) + ")"

        # Date detector Regex
        self.regex_relative_date = re.compile(r'\b' + relative_date_or_condition + r'\b')
        self.regex_day_diff = re.compile(datetime_diff_or_condition + r'\s*' + date_literal_or_condition)
        self.regex_date_month = re.compile(r'(\d+)\s*' + month_or_condition)
        self.regex_date_ref_month_1 = re.compile(
            r'(\d+)\s*' + month_date_or_condition + '\\s*' + datetime_diff_or_condition + r'\s*' + month_literal_or_condition)
        self.regex_date_ref_month_2 = re.compile(
            datetime_diff_or_condition + r'\s*' + month_literal_or_condition + r'\s*(\d+)\s+' + month_date_or_condition)
        self.regex_date_ref_month_3 = re.compile(r'(\d+)\s*' + month_date_or_condition)
        self.regex_after_days_ref = re.compile(r'(\d+)\s*' + date_literal_or_condition + r'\s+' + datetime_diff_or_condition)
        self.regex_weekday_month_1 = re.compile(
            r'(\d+)\s*' + weekday_or_condition + '\\s*' + datetime_diff_or_condition + r'\s+' + month_literal_or_condition)
        self.regex_weekday_month_2 = re.compile(
            datetime_diff_or_condition + r'\s+' + month_literal_or_condition + r'\s*(\d+)\s*' + weekday_or_condition)
        self.regex_weekday_diff = re.compile(datetime_diff_or_condition + r'\s*' + weekday_or_condition)
        self.regex_weekday = re.compile(weekday_or_condition)

    @staticmethod
    def _return_date_ner_format(day, month, year):
        if day and month and year:
            return {
                'dd': day,
                'mm': month,
                'yy': year,
                'type': TYPE_EXACT
            }
        else:
            return None

    def _detect_relative_date(self):
        """
        Regex for date like kal, aaj, parso
        Args:

        Returns:

        """
        dd, mm, yy = None, None, None
        date_rel_match = self.regex_relative_date.findall(self.text)
        if date_rel_match:
            if not self.is_past_referenced:
                req_date = self.now_date + timedelta(days=self.date_constant_dict[date_rel_match[0]][0])
            else:
                req_date = self.now_date - timedelta(days=self.date_constant_dict[date_rel_match[0]][0])
            dd, mm, yy = req_date.day, req_date.month, req_date.year
            self.date_detected = True
        return self._return_date_ner_format(dd, mm, yy)

    def _detect_date_month(self):
        """
        Regex for date like '2 july', 'pehli august'
        Args:

        Returns:

        """
        dd, mm, yy = None, None, None
        date_month_match = self.regex_date_month.findall(self.text)
        if date_month_match:
            date_month_match = date_month_match[0]
            dd = int(date_month_match[0])
            mm = self.date_constant_dict[date_month_match[1]][0]

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
        return self._return_date_ner_format(dd, mm, yy)

    def _detect_date_ref_month_1(self):
        """
        Regex for date like '2 tarikh is mahine ki
        Args:
            message:

        Returns:

        """
        dd, mm, yy = None, None, None
        date_ref_month_match = self.regex_date_ref_month_1.findall(self.text)
        if date_ref_month_match:
            date_ref_month_match = date_ref_month_match[0]
            dd = int(date_ref_month_match[0])
            if date_ref_month_match[2] and date_ref_month_match[3]:
                req_date = self.now_date + relativedelta(months=self.datetime_constant_dict[date_ref_month_match[2]][1])
                mm = req_date.month
                yy = req_date.year
            else:
                mm = self.now_date.month
                yy = self.now_date.year
        return self._return_date_ner_format(dd, mm, yy)

    def _detect_date_ref_month_2(self):
        """
        Regex for date like 'agle mahine ki 10 tarikh ko
        Args:

        Returns:

        """
        dd, mm, yy = None, None, None
        date_ref_month_match = self.regex_date_ref_month_2.findall(self.text)
        if date_ref_month_match:
            date_ref_month_match = date_ref_month_match[0]
            dd = int(date_ref_month_match[2])
            if date_ref_month_match[0] and date_ref_month_match[1]:
                req_date = self.now_date + relativedelta(months=self.datetime_constant_dict[date_ref_month_match[0]][1])
                mm = req_date.month
                yy = req_date.year
            else:
                mm = self.now_date.month
                yy = self.now_date.year
        return self._return_date_ner_format(dd, mm, yy)

    def _detect_date_ref_month_3(self):
        """
        Regex for date like '2 tarikh ko'
        Args:

        Returns:

        """
        dd, mm, yy = None, None, None
        date_ref_month_match = self.regex_date_ref_month_3.findall(self.text)
        if date_ref_month_match:
            date_ref_month_match = date_ref_month_match[0]
            dd = int(date_ref_month_match[0])
            if self.now_date.day < dd:
                mm = self.now_date.month
                yy = self.now_date.year
            else:
                req_date = self.now_date + relativedelta(months=1)
                mm = req_date.month
                yy = req_date.year
        return self._return_date_ner_format(dd, mm, yy)

    def _detect_date_diff(self):
        """
        Regex for date like 'pichhle din'
        Args:

        Returns:

        """
        dd, mm, yy = None, None, None
        diff_day_match = self.regex_day_diff.findall(self.text)
        if diff_day_match:
            diff_day_match = diff_day_match[0]
            print diff_day_match
            req_date = self.now_date + timedelta(days=self.datetime_constant_dict[diff_day_match[0]][1])
            dd, mm, yy = req_date.day, req_date.month, req_date.year
        return self._return_date_ner_format(dd, mm, yy)

    def _detect_after_days(self):
        """
        Regex for date like '2 din hua', '2 din baad'
        Args:

        Returns:

        """
        dd, mm, yy = None, None, None
        after_days_match = self.regex_after_days_ref.findall(self.text)
        if after_days_match:
            after_days_match = after_days_match[0]
            req_date = self.now_date + relativedelta(days=self.datetime_constant_dict[after_days_match[2]][1])
            dd, mm, yy = req_date.day, req_date.month, req_date.year
        return self._return_date_ner_format(dd, mm, yy)

    def _detect_weekday_ref_month_1(self):
        """
        Regex for date like 'agle month ka pehla monday', 'pichle month ki 3 shanivar
        Returns:
        """
        dd, mm, yy = None, None, None
        weekday_month_match = self.regex_weekday_month_1.findall(self.text)
        if weekday_month_match:
            weekday_month_match = weekday_month_match[0]
            n_weekday = int(weekday_month_match[0])
            weekday = self.date_constant_dict[weekday_month_match[1]][0]
            ref_date = self.now_date + relativedelta(months=self.datetime_constant_dict[weekday_month_match[2]][1])
            req_date = nth_weekday(n_weekday, weekday, ref_date)
            dd, mm, yy = req_date.day, req_date.month, req_date.year
        return dd, mm, yy

    def _detect_weekday_ref_month_2(self):
        """
        Regex for date like 'agle month ka pehla monday', 'pichle month ki 3 shanivar
        Returns:
        """
        dd, mm, yy = None, None, None
        weekday_month_match = self.regex_weekday_month_2.findall(self.text)
        if weekday_month_match:
            weekday_month_match = weekday_month_match[0]
            n_weekday = int(weekday_month_match[2])
            weekday = self.date_constant_dict[weekday_month_match[3]][0]
            ref_date = self.now_date + relativedelta(months=self.datetime_constant_dict[weekday_month_match[0]][1])
            req_date = nth_weekday(weekday, n_weekday, ref_date)
            dd, mm, yy = req_date.day, req_date.month, req_date.year
        return dd, mm, yy

    def _detect_weekday_diff(self):
        """
        Regex for date like 'aane wala tuesday', 'is mangalvar'
        Args:
        Returns:

        """
        dd, mm, yy = None, None, None
        weekday_ref_match = self.regex_weekday_diff.findall(self.text)
        if weekday_ref_match:
            weekday_ref_match = weekday_ref_match[0]
            n = self.datetime_constant_dict[weekday_ref_match[0]][1]
            weekday = self.date_constant_dict[weekday_ref_match[1]][0]
            req_date = next_weekday(current_date=self.now_date, n=n, weekday=weekday)
            dd, mm, yy = req_date.day, req_date.month, req_date.year
        return self._return_date_ner_format(dd, mm, yy)

    def _detect_weekday(self):
        """
        Regex for date like 'monday', 'somvar'
        Args:
        Returns:

        """
        dd, mm, yy = None, None, None
        weekday_ref_match = self.regex_weekday.findall(self.text)
        if weekday_ref_match:
            weekday = self.date_constant_dict[weekday_ref_match[0]][0]
            req_date = next_weekday(current_date=self.now_date, n=0, weekday=weekday)
            dd, mm, yy = req_date.day, req_date.month, req_date.year
            return dd, mm, yy
        return self._return_date_ner_format(dd, mm, yy)

    def _detect_date(self, text):
        date_detected = {}
        self.text = ' ' + text.lower().strip() + ' '
        for detector in self.detector_preferences:
            date_detected = detector()
            if date_detected:
                break
        return date_detected
