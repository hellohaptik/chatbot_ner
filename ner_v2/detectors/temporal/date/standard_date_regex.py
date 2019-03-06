# -*- coding: UTF-8 -*-
from __future__ import unicode_literals  # All strings in this file are by default unicode literals

import collections
import datetime
import os
import re

import dateutil.relativedelta as relativedelta
import pytz

import ner_v2.detectors.temporal.constant as temporal_constants
import ner_v2.detectors.temporal.utils as temporal_utils


# TODO: Some detectors don't return proper date types
# NOTE: This detector ignores year mentions

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
        self.timezone = ner_v2.detectors.temporal.utils.get_timezone(pytz.timezone(timezone))
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
            self._detect_weekday
        ]

    def detect_date(self, text, **kwargs):
        self.text = text
        self.processed_text = text
        self.tagged_text = text

        date_list, original_list = None, None
        for detector in self.detector_preferences:
            # FIXME: this just overwrites the results from successive detectors, is this correct ?
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
        Intialize

        Args:
            data_directory_path (str): path of data folder for given language
        Returns:
            None
        """
        data_directory_path = data_directory_path.rstrip(os.sep)
        date_constants_path = os.path.join(data_directory_path, temporal_constants.DATE_CONSTANT_FILE)
        datetime_constants_path = os.path.join(data_directory_path, temporal_constants.DATETIME_CONSTANT_FILE)
        numeral_constans_path = os.path.join(data_directory_path, temporal_constants.NUMERALS_CONSTANT_FILE)

        self._date_constants_dict = temporal_utils.read_variants_data(date_constants_path)
        self._datetime_constants_dict = temporal_utils.read_variants_data(datetime_constants_path)
        self._numerals_constants_dict = temporal_utils.read_variants_data(numeral_constans_path)

        date_part_choices = collections.defaultdict(list)

        # TODO: Make this more pythonic and readable by using namedtuple or some other datatype instead of 1 and 2
        # TODO: indices
        for variant in self._date_constants_dict:
            date_part_choices[self._date_constants_dict[variant][1]].append(variant)

        # Relative date mentions. In en -> today, tomorrow, yesterday, day after tomorrow
        relative_date_choices = date_part_choices[temporal_constants.RELATIVE_DATE]

        # literals that mean "day". In en -> 2 "days", hi -> 3 "din"
        day_literal_choices = date_part_choices[temporal_constants.DATE_LITERAL_TYPE]

        # Literals that mean "date". Used when referring to some date wrt to month.
        # In hi -> agle mahine ki 3 "tareekh", etc
        month_ref_date_choices = date_part_choices[temporal_constants.MONTH_DATE_REF_TYPE]

        # Literals that mean "month". In hi -> mahina, mahine, etc
        month_literal_choices = date_part_choices[temporal_constants.MONTH_LITERAL_TYPE]

        # Days of the week. In en -> Monday, Tuesday, Wednesday, ...
        weekday_choices = date_part_choices[temporal_constants.WEEKDAY_TYPE]

        # Months of the year. In en -> January, February, ...
        month_choices = date_part_choices[temporal_constants.MONTH_TYPE]

        # prefixes and suffixes that indicate the sign of relative delta. Also contains time prepositions
        # like previous, next, this, ago, last, etc
        # In en -> 2 days "later", 2 days "ago"
        # In hi -> 2 din "baad", 3 din "pehle"
        # FIXME: We are not using the prefix/suffix information provided in the data, resulting in detection of
        # FIXME: weird constructs like '2 din pichla', '2 din agla', 'pehle ravivar', 'baad mangalvaar'
        datetime_diff_choices = [x for x in self._datetime_constants_dict
                                 if self._datetime_constants_dict[x][2] == temporal_constants.ADD_DIFF_DATETIME_TYPE]

        # word and digit representations of numbers in the target language
        # In en -> 1, 2, 3, 4, 5, ...(upto thirty one), one, two, three, ... (upto thirty one)
        numeral_variants = [x for x in self._numerals_constants_dict]

        format_args = {
            "relative_date_choices": "({})".format(self._decode_sort_escape_join(relative_date_choices)),
            "day_literal_choices": "({})".format(self._decode_sort_escape_join(day_literal_choices)),
            "month_ref_date_choices": "({})".format(self._decode_sort_escape_join(month_ref_date_choices)),
            "month_literal_choices": "({})".format(self._decode_sort_escape_join(month_literal_choices)),
            "weekday_choices": "({})".format(self._decode_sort_escape_join(weekday_choices)),
            "month_choices": "({})".format(self._decode_sort_escape_join(month_choices)),
            "datetime_diff_choices": "({})".format(self._decode_sort_escape_join(datetime_diff_choices)),
            "numeral_variants": r"(\d+|{})".format(self._decode_sort_escape_join(numeral_variants)),
        }

        _patterns = {
            "regex_relative_date": r"({relative_date_choices})",

            "regex_date_month": r"({numeral_variants}\s*(st|nd|th|rd)?\s*{month_choices})",

            "regex_date_ref_month_1": r"({numeral_variants}\s*{month_ref_date_choices}\s*"
                                      r"{datetime_diff_choices}\s*{month_literal_choices})",

            "regex_date_ref_month_2": r"({datetime_diff_choices}\s*{month_literal_choices}\s*"
                                      r"[a-z]*\s*{numeral_variants}\s+{month_ref_date_choices})",

            "regex_date_ref_month_3": r"({numeral_variants}\s*{month_ref_date_choices})",

            "regex_date_diff": r"({datetime_diff_choices}\s*{day_literal_choices})",

            "regex_after_days_ref": r"({numeral_variants}\s*{day_literal_choices}\s+{datetime_diff_choices})",

            "regex_weekday_month_1": r"({numeral_variants}\s*{weekday_choices}\s*"
                                     r"{datetime_diff_choices}\s+{month_literal_choices})",

            "regex_weekday_month_2": r"({datetime_diff_choices}\s+{month_literal_choices}\s*[a-z]*\s*"
                                     r"{numeral_variants}\s+{weekday_choices})",

            "regex_weekday": r"((?:{datetime_diff_choices}\s+)?{weekday_choices})",
        }

        for pattern_key in _patterns:
            self._patterns[pattern_key] = re.compile(_patterns[pattern_key].format(**format_args), flags=re.UNICODE)

    def _get_int_from_numeral(self, numeral):
        """
        Cast a numeral str to int. It does so by directing casting it if the strinng contains only digits.
        Otherwise it looks up in the numerals data read from language data folder (numbers_constant.csv)

        Args:
            numeral (str): numeral text to cast to int

        Returns:
            int: integer value for given numeral

        Raises:
            ValueError: if the given string contains decimal points in addition to digits
            KeyError: if the numeral string is not present in the data read from numbers_constant.csv
        """
        if numeral.replace('.', '').isdigit():
            # FIXME: This fails for any floating point string
            return int(numeral)
        else:
            # FIXME: possible lossy conversion for dedh, dhai, etc that have floats in numbers_constant.csv
            return int(self._numerals_constants_dict[numeral][0])

    def _detect_relative_date(self, date_list=None, original_list=None):
        """
        Detect dates in relative mentions
            en -> today, tomorrow, yesterday, day after tomorrow, ...
            hi -> aaj, kal, parson, ...

        Args:
            date_list (list, optional): list of date values detected so far
            original_list (list, optional): list of same length as date_list, which has corresponding substrings from
                                            the text that were detected as dates.

        Returns:
            tuple containing
                list: list of date values detected so far
                list: list of same length as date_list, which has corresponding substrings from
                      the text that were detected as dates.
        """

        def get_type(delta):
            relative_types = [temporal_constants.TYPE_DAY_BEFORE,
                              temporal_constants.TYPE_YESTERDAY,
                              temporal_constants.TYPE_TODAY,
                              temporal_constants.TYPE_TOMORROW,
                              temporal_constants.TYPE_DAY_AFTER]
            if 0 <= delta + 2 < len(delta):
                return relative_types[delta + 2]

            return temporal_constants.TYPE_EXACT

        date_list = date_list or []
        original_list = original_list or []

        relative_date_matches = self._patterns["regex_relative_date"].findall(self.processed_text)
        for date_match in relative_date_matches:
            original = date_match[0]
            if not self.is_past_referenced:
                req_date = self.now_date + datetime.timedelta(days=self._date_constants_dict[date_match[1]][0])
            else:
                req_date = self.now_date - datetime.timedelta(days=self._date_constants_dict[date_match[1]][0])

            date = {
                "dd": req_date.day,
                "mm": req_date.month,
                "yy": req_date.year,
                "type": get_type(self._date_constants_dict[date_match[1]][0]),
                "dinfo": {
                    "dd": "detected",
                    "mm": "detected",
                    "yy": "detected",
                },
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_month(self, date_list=None, original_list=None):
        """
        Detect dates in <number><optional ordinal><month word> format
            en -> 2nd July, 3rd Feb
            hi -> 2 janvary, 3 september

        Args:
            date_list (list, optional): list of date values detected so far
            original_list (list, optional): list of same length as date_list, which has corresponding substrings from
                                            the text that were detected as dates.

        Returns:
            tuple containing
                list: list of date values detected so far
                list: list of same length as date_list, which has corresponding substrings from
                      the text that were detected as dates.
        """
        date_list = date_list or []
        original_list = original_list or []

        date_month_matches = self._patterns["regex_date_month"].findall(self.processed_text)
        for date_month_match in date_month_matches:
            original, number_variant, _, month_variant = date_month_match
            dd = int(self._get_int_from_numeral(number_variant))
            mm = int(self._date_constants_dict[month_variant][0])
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
                "type": temporal_constants.TYPE_EXACT,
                "dinfo": {
                    "dd": "detected",
                    "mm": "detected",
                    "yy": "inferred",
                },
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_ref_month_1(self, date_list=None, original_list=None):
        """
        Detect dates in <number><date literals><next/previous/this/relative delta prepositions><month literals> format
            en -> 2nd of this month
            hi -> 2 tarikh iss mahine ki, 2 tarikh pichle mahine ki

        Args:
            date_list (list, optional): list of date values detected so far
            original_list (list, optional): list of same length as date_list, which has corresponding substrings from
                                            the text that were detected as dates.

        Returns:
            tuple containing
                list: list of date values detected so far
                list: list of same length as date_list, which has corresponding substrings from
                      the text that were detected as dates.
        """
        date_list = date_list or []
        original_list = original_list or []

        date_ref_month_matches = self._patterns["regex_date_ref_month_1"].findall(self.processed_text)

        for date_match in date_ref_month_matches:
            original, day_variant, _, month_delta, month_literal = date_match
            dd = self._get_int_from_numeral(day_variant)
            if month_delta and month_literal:
                months_delta_value = self._datetime_constants_dict[month_delta][1]
                req_date = self.now_date + relativedelta.relativedelta(months=months_delta_value)
                mm = req_date.month
                yy = req_date.year
            else:
                mm = self.now_date.month
                yy = self.now_date.year

            date = {
                "dd": int(dd),
                "mm": int(mm),
                "yy": int(yy),
                "type": temporal_constants.TYPE_EXACT,
                "dinfo": {
                    "dd": "detected",
                    "mm": "detected",
                    "yy": "detected",
                },
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_ref_month_2(self, date_list=None, original_list=None):
        """
        Detect dates in <next/previous/this/relative delta prepositions><month literals><number><date literals> format
            hi -> alge mahine ki 2 tareekh, pichle mahine ki 30 tareekh
            en -> next month's 2nd day

        Args:
            date_list (list, optional): list of date values detected so far
            original_list (list, optional): list of same length as date_list, which has corresponding substrings from
                                            the text that were detected as dates.

        Returns:
            tuple containing
                list: list of date values detected so far
                list: list of same length as date_list, which has corresponding substrings from
                      the text that were detected as dates.
        """
        date_list = date_list or []
        original_list = original_list or []

        date_ref_month_match = self._patterns["regex_date_ref_month_2"].findall(self.processed_text)
        for date_match in date_ref_month_match:
            original, month_delta, month_literal, day_variant, _ = date_match
            dd = self._get_int_from_numeral(day_variant)
            if month_delta and month_literal:
                months_delta_value = self._datetime_constants_dict[month_delta][1]
                req_date = self.now_date + relativedelta.relativedelta(months=months_delta_value)
                mm = req_date.month
                yy = req_date.year
            else:
                mm = self.now_date.month
                yy = self.now_date.year

            date = {
                "dd": int(dd),
                "mm": int(mm),
                "yy": int(yy),
                "type": temporal_constants.TYPE_EXACT,
                "dinfo": {
                    "dd": "detected",
                    "mm": "detected",
                    "yy": "detected",
                },
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_ref_month_3(self, date_list=None, original_list=None):
        """
        Detect dates in <number><date literals> format
            en -> 2nd day
            hi -> 2 tarikh , 30 tareekh

        Args:
            date_list (list, optional): list of date values detected so far
            original_list (list, optional): list of same length as date_list, which has corresponding substrings from
                                            the text that were detected as dates.

        Returns:
            tuple containing
                list: list of date values detected so far
                list: list of same length as date_list, which has corresponding substrings from
                      the text that were detected as dates.
        """
        date_list = date_list or []
        original_list = original_list or []

        date_ref_month_match = self._patterns["regex_date_ref_month_3"].findall(self.processed_text)
        for date_match in date_ref_month_match:
            original, day_variant, date_literal = date_match
            dd = self._get_int_from_numeral(day_variant)
            if ((self.now_date.day > dd and self.is_past_referenced) or
                    (self.now_date.day <= dd and not self.is_past_referenced)):
                mm = self.now_date.month
                yy = self.now_date.year
            elif self.now_date.day < dd and self.is_past_referenced:
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
                "type": temporal_constants.TYPE_POSSIBLE_DAY,
                "dinfo": {
                    "dd": "detected",
                    "mm": "inferred",
                    "yy": "inferred",
                },
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_date_diff(self, date_list=None, original_list=None):
        """
        Detect date using format <previous/next/this><day literals>
            hi -> agle din, pichle din
            en -> previous day, next day, this day

        Args:
            date_list (list, optional): list of date values detected so far
            original_list (list, optional): list of same length as date_list, which has corresponding substrings from
                                            the text that were detected as dates.

        Returns:
            list: list of date values detected so far
            list: list of same length as date_list, which has corresponding substrings from
                  the text that were detected as dates.
        """
        date_list = date_list or []
        original_list = original_list or []

        diff_day_match = self._patterns["regex_date_diff"].findall(self.processed_text)
        for date_match in diff_day_match:
            original, day_delta, _ = date_match
            req_date = self.now_date + datetime.timedelta(days=self._datetime_constants_dict[day_delta][1])
            date = {
                'dd': req_date.day,
                'mm': req_date.month,
                'yy': req_date.year,
                'type': temporal_constants.TYPE_EXACT,
                "dinfo": {
                    "dd": "detected",
                    "mm": "detected",
                    "yy": "detected",
                }
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_after_days(self, date_list=None, original_list=None):
        """
        Detect date using format <number><day literals><ago/later/relative delta prepositions>
            hi -> 2 din bad, 30 din pehle
            en -> two days later, one day ago

        Args:
            date_list (list, optional): list of date values detected so far
            original_list (list, optional): list of same length as date_list, which has corresponding substrings from
                                            the text that were detected as dates.

        Returns:
            list: list of date values detected so far
            list: list of same length as date_list, which has corresponding substrings from
                  the text that were detected as dates.
        """
        date_list = date_list or []
        original_list = original_list or []

        after_days_match = self._patterns["regex_after_days_ref"].findall(self.processed_text)
        for date_match in after_days_match:
            original, number_variant, _, day_delta = date_match
            day_diff = self._get_int_from_numeral(number_variant)
            req_date = self.now_date + relativedelta.relativedelta(
                days=day_diff * self._datetime_constants_dict[day_delta][1])
            date = {
                "dd": req_date.day,
                "mm": req_date.month,
                "yy": req_date.year,
                "type": temporal_constants.TYPE_EXACT,
                "dinfo": {
                    "dd": "detected",
                    "mm": "detected",
                    "yy": "detected",
                }
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_weekday_ref_month_1(self, date_list=None, original_list=None):
        """
        Detect date using format <number><day of week><next/previous/this/relative delta prepositions>?<month literals>
            hi -> doosra somwaar agle mahine ka, teesra somwar pichle mahine ka 
            en -> 2nd Monday of next month

        Args:
            date_list (list, optional): list of date values detected so far
            original_list (list, optional): list of same length as date_list, which has corresponding substrings from
                                            the text that were detected as dates.

        Returns:
            list: list of date values detected so far
            list: list of same length as date_list, which has corresponding substrings from
                  the text that were detected as dates.
        """
        date_list = date_list or []
        original_list = original_list or []

        weekday_month_matches = self._patterns["regex_weekday_month_1"].findall(self.processed_text)
        for date_match in weekday_month_matches:
            original, number_variant, day_of_week, months_delta, _ = date_match
            n_weekday = self._get_int_from_numeral(number_variant)
            weekday = self._date_constants_dict[day_of_week][0]
            ref_date = self.now_date + relativedelta.relativedelta(
                months=self._datetime_constants_dict[months_delta][1])
            req_date = temporal_utils.nth_weekday_of_month(weekday=weekday, n=n_weekday, reference_datetime=ref_date)
            date = {
                "dd": req_date.day,
                "mm": req_date.month,
                "yy": req_date.year,
                "type": temporal_constants.TYPE_EXACT,
                "dinfo": {
                    "dd": "detected",
                    "mm": "detected",
                    "yy": "detected",
                }
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_weekday_ref_month_2(self, date_list=None, original_list=None):
        """
        Detect date using format <next/previous/this/relative delta prepositions><month literals><number><day of week>
            hi -> agle mahine ka doosra somwaar, pichle mahine ka teesra somwar
            en -> next month's 2nd Monday

        Args:
            date_list (list, optional): list of date values detected so far
            original_list (list, optional): list of same length as date_list, which has corresponding substrings from
                                            the text that were detected as dates.

        Returns:
            list: list of date values detected so far
            list: list of same length as date_list, which has corresponding substrings from
                  the text that were detected as dates.
        """
        date_list = date_list or []
        original_list = original_list or []

        weekday_month_matches = self._patterns["regex_weekday_month_2"].findall(self.processed_text)
        for date_match in weekday_month_matches:
            original, months_delta, _, number_variant, day_of_week = date_match
            n_weekday = self._get_int_from_numeral(number_variant)
            weekday = self._date_constants_dict[day_of_week][0]
            ref_date = self.now_date + relativedelta.relativedelta(
                months=self._datetime_constants_dict[months_delta][1])
            req_date = temporal_utils.nth_weekday_of_month(weekday=weekday, n=n_weekday, reference_datetime=ref_date)
            date = {
                "dd": req_date.day,
                "mm": req_date.month,
                "yy": req_date.year,
                "type": temporal_constants.TYPE_EXACT,
                "dinfo": {
                    "dd": "detected",
                    "mm": "detected",
                    "yy": "detected",
                }
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list

    def _detect_weekday(self, date_list=None, original_list=None):
        """
        Detect date using format <next/previous/this/relative delta prepositions>?<day of week>
            en -> previous monday, next tuesday, etc
            hi -> pichla somwar, agla ravivar, etc

        Args:
            date_list (list, optional): list of date values detected so far
            original_list (list, optional): list of same length as date_list, which has corresponding substrings from
                                            the text that were detected as dates.

        Returns:
            list: list of date values detected so far
            list: list of same length as date_list, which has corresponding substrings from
                  the text that were detected as dates.
        """

        def get_type(delta):
            relative_types = [temporal_constants.TYPE_THIS_DAY, temporal_constants.TYPE_NEXT_DAY]
            if 0 <= delta < len(relative_types):
                return relative_types[delta]
            return temporal_constants.TYPE_EXACT

        date_list = date_list or []
        original_list = original_list or []

        weekday_ref_matches = self._patterns["regex_weekday"].findall(self.processed_text)
        for date_match in weekday_ref_matches:
            original, delta_variant, day_of_week = date_match
            n = 0
            if delta_variant:
                n = self._datetime_constants_dict[delta_variant][1]
            weekday = self._date_constants_dict[day_of_week][0]
            req_date = temporal_utils.nth_weekday(weekday=weekday, n=n, from_datetime=self.now_date)
            date = {
                "dd": req_date.day,
                "mm": req_date.month,
                "yy": req_date.year,
                "type": get_type(delta=n),
                "dinfo": {
                    "dd": "detected",
                    "mm": "detected",
                    "yy": "detected",
                },
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
