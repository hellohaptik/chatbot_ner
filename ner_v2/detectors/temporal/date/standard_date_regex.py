# -*- coding: UTF-8 -*-
from __future__ import unicode_literals  # All strings in this file are by default unicode literals

import datetime
import os
import re

import dateutil.relativedelta as relativedelta
import pytz

import ner_v2.detectors.temporal.constant as temporal_constants
import ner_v2.detectors.temporal.utils as temporal_utils
import ner_v2.detectors.utils as detector_utils

# TODO: For now all date types return TYPE_EXACT. Either drop the type or return proper types


class BaseRegexDate(object):
    def __init__(self, entity_name, data_directory_path, timezone='UTC', past_date_referenced=False):
        """
        Base Regex class which will be imported by language date class by giving their data folder path
        This will create standard regex and their parser to detect date for given language.
        Args:
            data_directory_path (str): path of data folder for given language
            timezone (str): user timezone default UTC
            past_date_referenced (boolean): if the date reference is in past, this is helpful for text like 'kal',
                                          'parso' to know if the reference is past or future.
        """
        self.text = ""
        self.tagged_text = ""
        self.processed_text = ""
        self.date = []
        self.original_date_text = []
        self.entity_name = entity_name
        self.tag = "__" + entity_name + "__"
        self.timezone = detector_utils.get_timezone(pytz.timezone(timezone))
        self.now_date = datetime.datetime.now(tz=self.timezone)
        self.bot_message = None

        self.is_past_referenced = past_date_referenced

        # dict to store words for date, numerals and words which comes in reference to some date
        self._date_constants_dict = {}
        self._datetime_constants_dict = {}
        self._numerals_constants_dict = {}

        # define dynamic created standard regex from language data files
        self._patterns = {}

        # Method to initialise value in regex
        self._generate_date_patterns(data_directory_path)

        # Variable to define default order in which these regex will work
        self.detector_preferences = [
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
            date_list, original_list = detector(date_list=None, original_list=None)
            self._update_processed_text(original_list)
        return date_list, original_list

    def _decode_sort_escape_join(self, choices, delimiter='|', lower=True, re_escape=True):
        choices = [choice.decode('utf-8') if isinstance(choice, bytes) else choice for choice in choices]
        choices = [choice.strip() for choice in choices if choice.strip()]
        if lower:
            choices = [choice.lower() for choice in choices]
        choices = sorted(choices, key=lambda s: len(s.split()), reverse=True)
        if re_escape:
            choices = [re.escape(choice) for choice in choices]
        joined = delimiter.join(choices)
        return joined

    def _generate_date_patterns(self, data_directory_path):
        """
        Initialise standard regex from data file
        Args:
            data_directory_path (str): path of data folder for given language
        Returns:
            None
        """
        data_directory_path = data_directory_path.rstrip(os.sep)
        date_constants_path = os.path.join(data_directory_path, temporal_constants.DATE_CONSTANT_FILE)
        datetime_constants_path = os.path.join(data_directory_path, temporal_constants.DATETIME_CONSTANT_FILE)
        numeral_constans_path = os.path.join(data_directory_path, temporal_constants.NUMERALS_CONSTANT_FILE)

        self._date_constants_dict = temporal_utils.get_tuple_dict(date_constants_path)
        self._datetime_constants_dict = temporal_utils.get_tuple_dict(datetime_constants_path)
        self._numerals_constants_dict = temporal_utils.get_tuple_dict(numeral_constans_path)

        relative_date_choices = [x for x in self._date_constants_dict
                                 if self._date_constants_dict[x][1] == temporal_constants.RELATIVE_DATE]

        date_literal_choices = [x for x in self._date_constants_dict
                                if self._date_constants_dict[x][1] == temporal_constants.DATE_LITERAL_TYPE]

        month_ref_date_choices = [x for x in self._date_constants_dict
                                  if self._date_constants_dict[x][1] == temporal_constants.MONTH_DATE_REF_TYPE]

        month_literal_choices = [x for x in self._date_constants_dict
                                 if self._date_constants_dict[x][1] == temporal_constants.MONTH_LITERAL_TYPE]

        weekday_choices = [x for x in self._date_constants_dict
                           if self._date_constants_dict[x][1] == temporal_constants.WEEKDAY_TYPE]

        month_choices = [x for x in self._date_constants_dict
                         if self._date_constants_dict[x][1] == temporal_constants.MONTH_TYPE]

        datetime_diff_choices = [x for x in self._datetime_constants_dict
                                 if self._datetime_constants_dict[x][2] == temporal_constants.ADD_DIFF_DATETIME_TYPE]

        numeral_variants = [x for x in self._numerals_constants_dict]

        format_args = {
            "relative_date_choices": "({})".format(self._decode_sort_escape_join(relative_date_choices)),
            "date_literal_choices": "({})".format(self._decode_sort_escape_join(date_literal_choices)),
            "month_ref_date_choices": "({})".format(self._decode_sort_escape_join(month_ref_date_choices)),
            "month_literal_choices": "({})".format(self._decode_sort_escape_join(month_literal_choices)),
            "weekday_choices": "({})".format(self._decode_sort_escape_join(weekday_choices)),
            "month_choices": "({})".format(self._decode_sort_escape_join(month_choices)),
            "datetime_diff_choices": "({})".format(self._decode_sort_escape_join(datetime_diff_choices)),
            "numeral_variants": "({})".format(self._decode_sort_escape_join(numeral_variants)),
        }

        _patterns = {
            "regex_relative_date": r"({relative_date_choices})",
            "regex_day_diff": r"({datetime_diff_choices}\s*{date_literal_choices})",
            "regex_date_month": r"((\d+|{numeral_variants})\s*(st|nd|th|rd)\s*{month_choices})",
            "regex_date_ref_month_1": r"((\d+|{numeral_variants})\s*{month_ref_date_choices}\s*"
                                      r"{datetime_diff_choices}\s*{month_literal_choices})",
            "regex_date_ref_month_2": r"({datetime_diff_choices}\s*{month_literal_choices}\s*"
                                      r"[a-z]*\s*(\d+|{numeral_variants})\s+{month_ref_date_choices})",
            "regex_date_ref_month_3": r"((\d+|{numeral_variants})\s*{month_ref_date_choices})",
            "regex_after_days_ref": r"((\d+|{numeral_variants})\s*{date_literal_choices}\s+{datetime_diff_choices})",
            "regex_weekday_month_1": r"((\d+|{numeral_variants})\s*{weekday_choices}\s*"
                                     r"{datetime_diff_choices}\s+{month_literal_choices})",
            "regex_weekday_month_2": r"({datetime_diff_choices}\s+{month_literal_choices}\s*[a-z]*\s*"
                                     r"(\d+|{numeral_variants})\s+{weekday_choices})",
            "regex_weekday_diff": r"({datetime_diff_choices}\s+{weekday_choices})",
            "regex_weekday": r"({weekday_choices})",
        }

        for pattern_key in _patterns:
            self._patterns[pattern_key] = re.compile(_patterns[pattern_key].format(**format_args), flags=re.UNICODE)

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
            return int(self._numerals_constants_dict[numeral][0])

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

        date_rel_match = self._patterns["regex_relative_date"].findall(self.processed_text)
        for date_match in date_rel_match:
            original = date_match[0]
            if not self.is_past_referenced:
                req_date = self.now_date + datetime.timedelta(days=self._date_constants_dict[date_match[1]][0])
            else:
                req_date = self.now_date - datetime.timedelta(days=self._date_constants_dict[date_match[1]][0])

            date = {
                "dd": req_date.day,
                "mm": req_date.month,
                "yy": req_date.year,
                "type": temporal_constants.TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_month(self, date_list=None, original_list=None):
        """
        Parser to detect date containing specific date and month like '2 july'(hindi), 'pehli august'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected
        """
        date_list = date_list or []
        original_list = original_list or []

        date_month_matches = self._patterns["regex_date_month"].findall(self.processed_text)
        for date_month_match in date_month_matches:
            original = date_month_match[0]
            dd = int(self._get_int_from_numeral(date_month_match[1]))
            mm = int(self._date_constants_dict[date_month_match[3]][0])
            yy = self.now_date.year

            current_date = self.now_date.date()
            detected_date = datetime.date(year=self.now_date.month, month=mm, day=dd)

            if current_date < detected_date:
                yy += 1

            if self.is_past_referenced:
                yy -= 1

            date = {
                "dd": dd,
                "mm": mm,
                "yy": yy,
                "type": temporal_constants.TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_ref_month_1(self, date_list=None, original_list=None):
        """
        Parser to detect date containing reference date and month like '2 tarikh is mahine ki'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected

        """
        date_list = date_list or []
        original_list = original_list or []

        date_ref_month_match = self._patterns["regex_date_ref_month_1"].findall(self.processed_text)

        for date_match in date_ref_month_match:
            original = date_match[0]
            dd = self._get_int_from_numeral(date_match[1])
            if date_match[3] and date_match[4]:
                req_date = self.now_date + relativedelta.relativedelta(
                    months=self._datetime_constants_dict[date_match[3]][1])
                mm = req_date.month
                yy = req_date.year
            else:
                mm = self.now_date.month
                yy = self.now_date.year

            date = {
                "dd": int(dd),
                "mm": int(mm),
                "yy": int(yy),
                "type": temporal_constants.TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_ref_month_2(self, date_list=None, original_list=None):
        """
        Parser to detect date containing reference date and month like 'agle mahine ki 2 tarikh ko'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected

        """
        date_list = date_list or []
        original_list = original_list or []

        date_ref_month_match = self._patterns["regex_date_ref_month_2"].findall(self.processed_text)
        for date_match in date_ref_month_match:
            original = date_match[0]
            dd = self._get_int_from_numeral(date_match[3])
            if date_match[1] and date_match[2]:
                req_date = self.now_date + relativedelta.relativedelta(
                    months=self._datetime_constants_dict[date_match[1]][1])
                mm = req_date.month
                yy = req_date.year
            else:
                mm = self.now_date.month
                yy = self.now_date.year

            date = {
                "dd": int(dd),
                "mm": int(mm),
                "yy": int(yy),
                "type": temporal_constants.TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_ref_month_3(self, date_list=None, original_list=None):
        """
        Parser to detect date containing reference date and month like '2 tarikh ko'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected

        """
        date_list = date_list or []
        original_list = original_list or []

        date_ref_month_match = self._patterns["regex_date_ref_month_3"].findall(self.processed_text)
        for date_match in date_ref_month_match:
            original = date_match[0]
            dd = self._get_int_from_numeral(date_match[1])
            if ((self.now_date.day > dd and self.is_past_referenced) or
                    (self.now_date.day <= dd and not self.is_past_referenced)):
                mm = self.now_date.month
                yy = self.now_date.year
            elif self.now_date.day <= dd and self.is_past_referenced:
                req_date = self.now_date - relativedelta.relativedelta(months=1)
                mm = req_date.month
                yy = req_date.year
            else:
                req_date = self.now_date + relativedelta.relativedelta(months=1)
                mm = req_date.month
                yy = req_date.year
            date = {
                "dd": int(dd),
                "mm": int(mm),
                "yy": int(yy),
                "type": temporal_constants.TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_diff(self, date_list=None, original_list=None):
        """
        Parser to detect date containing reference with current date like 'pichhle din'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected

        """
        date_list = date_list or []
        original_list = original_list or []

        diff_day_match = self._patterns["regex_day_diff"].findall(self.processed_text)
        for date_match in diff_day_match:
            original = date_match[0]
            req_date = self.now_date + datetime.timedelta(days=self._datetime_constants_dict[date_match[1]][1])
            date = {
                'dd': req_date.day,
                'mm': req_date.month,
                'yy': req_date.year,
                'type': temporal_constants.TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_after_days(self, date_list=None, original_list=None):
        """
        Parser to detect date containing reference with current date like '2 din hua'(hindi), '2 din baad'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected

        """
        date_list = date_list or []
        original_list = original_list or []

        after_days_match = self._patterns["regex_after_days_ref"].findall(self.processed_text)
        for date_match in after_days_match:
            original = date_match[0]
            day_diff = self._get_int_from_numeral(date_match[1])
            req_date = self.now_date + relativedelta.relativedelta(
                days=day_diff * self._datetime_constants_dict[date_match[3]][1])
            date = {
                "dd": req_date.day,
                "mm": req_date.month,
                "yy": req_date.year,
                "type": temporal_constants.TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_weekday_ref_month_1(self, date_list=None, original_list=None):
        """
        Parser to detect date containing referenced week and month 'agle month ka pehla monday'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected
        """
        date_list = date_list or []
        original_list = original_list or []

        weekday_month_match = self._patterns["regex_weekday_month_1"].findall(self.processed_text)
        for date_match in weekday_month_match:
            original = date_match[0]
            n_weekday = self._get_int_from_numeral(date_match[1])
            weekday = self._date_constants_dict[date_match[2]][0]
            ref_date = self.now_date + relativedelta.relativedelta(
                months=self._datetime_constants_dict[date_match[3]][1])
            req_date = temporal_utils.nth_weekday(n_weekday, weekday, ref_date)
            date = {
                "dd": req_date.day,
                "mm": req_date.month,
                "yy": req_date.year,
                "type": temporal_constants.TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_weekday_ref_month_2(self, date_list=None, original_list=None):
        """
        Parser to detect date containing referenced week and month like'pehla monday agle month ka'(hindi)
        Args:

        Returns:
            date_list (list): list of dict containing day, month, year from detected text
            original_list (list): list of original text corresponding to values detected
        """
        date_list = date_list or []
        original_list = original_list or []

        weekday_month_match = self._patterns["regex_weekday_month_2"].findall(self.processed_text)
        for date_match in weekday_month_match:
            original = date_match[0]
            n_weekday = self._get_int_from_numeral(date_match[3])
            weekday = self._date_constants_dict[date_match[4]][0]
            ref_date = self.now_date + relativedelta.relativedelta(
                months=self._datetime_constants_dict[date_match[1]][1])
            req_date = temporal_utils.nth_weekday(weekday, n_weekday, ref_date)
            date = {
                "dd": req_date.day,
                "mm": req_date.month,
                "yy": req_date.year,
                "type": temporal_constants.TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_weekday_diff(self, date_list=None, original_list=None):
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

        weekday_ref_match = self._patterns["regex_weekday_diff"].findall(self.processed_text)
        for date_match in weekday_ref_match:
            original = date_match[0]
            n = self._datetime_constants_dict[date_match[1]][1]
            weekday = self._date_constants_dict[date_match[2]][0]
            req_date = temporal_utils.next_weekday(current_date=self.now_date, n=n, weekday=weekday)
            date = {
                "dd": req_date.day,
                "mm": req_date.month,
                "yy": req_date.year,
                "type": temporal_constants.TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_weekday(self, date_list=None, original_list=None):
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

        weekday_ref_match = self._patterns["regex_weekday"].findall(self.processed_text)
        for date_match in weekday_ref_match:
            original = date_match[0]
            weekday = self._date_constants_dict[date_match[1]][0]
            req_date = temporal_utils.next_weekday(current_date=self.now_date, n=0, weekday=weekday)
            date = {
                "dd": req_date.day,
                "mm": req_date.month,
                "yy": req_date.year,
                "type": temporal_constants.TYPE_EXACT
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


class DateDetector(BaseRegexDate):
    def __init__(self, entity_name, data_directory_path, timezone='UTC', past_date_referenced=False):
        super(DateDetector, self).__init__(entity_name=entity_name,
                                           data_directory_path=data_directory_path,
                                           timezone=timezone,
                                           past_date_referenced=past_date_referenced)
