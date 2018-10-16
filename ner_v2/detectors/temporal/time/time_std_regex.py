from chatbot_ner.config import ner_logger
from ner_v2.detectors.constant import TYPE_EXACT
from ner_v2.detectors.temporal.constant import DATETIME_CONSTANT_FILE, ADD_DIFF_DATETIME_TYPE, NUMERALS_CONSTANT_FILE, \
    TIME_CONSTANT_FILE, REF_DATETIME_TYPE, HOUR_TIME_TYPE, MINUTE_TIME_TYPE
import pytz
import re
import datetime

from ner_v2.detectors.temporal.utils import get_tuple_dict


class BaseRegexTime(object):
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

        # dict to store words for time, numerals and words which comes in reference to some date
        self.time_constant_dict = {}
        self.datetime_constant_dict = {}
        self.numerals_constant_dict = {}

        # define dynamic created standard regex from language data files
        self.regex_hour = None
        self.regex_minute = None

        # Method to initialise value in regex
        self.init_regex_and_parser(data_directory_path)

        # Variable to define default order in which these regex will work
        self.detector_preferences = [self._detect_hour_minute
                                     ]

    def init_regex_and_parser(self, data_directory_path):
        """
        Initialise standard regex from data file
        Args:
            data_directory_path (str): path of data folder for given language
        Returns:
            None
        """
        self.time_constant_dict = get_tuple_dict(data_directory_path.rstrip('/') + '/' + TIME_CONSTANT_FILE)
        self.datetime_constant_dict = get_tuple_dict(data_directory_path.rstrip('/') + '/' + DATETIME_CONSTANT_FILE)
        self.numerals_constant_dict = get_tuple_dict(data_directory_path.rstrip('/') + '/' + NUMERALS_CONSTANT_FILE)

        datetime_diff_choices = "(" + "|".join([x for x in self.datetime_constant_dict
                                        if self.datetime_constant_dict[x][2] == ADD_DIFF_DATETIME_TYPE]) + "|)"
        datetime_add_ref_choices = "(" + "|".join([x for x in self.datetime_constant_dict
                                       if self.datetime_constant_dict[x][2] == REF_DATETIME_TYPE]) + "|)"

        hour_variants = "(" + "|".join([x for x in self.time_constant_dict if
                                        self.time_constant_dict[x][1] == HOUR_TIME_TYPE]) + ")"
        minute_variants = "(" + "|".join([x for x in self.time_constant_dict if
                                          self.time_constant_dict[x][1] == MINUTE_TIME_TYPE]) + ")"

        self.regex_hour = re.compile(r'(' + datetime_add_ref_choices + r"\s*([\d.]+)\s*" + hour_variants + r"\s+" +
                                     datetime_diff_choices + r')')
        self.regex_minute = re.compile(r'(' + datetime_add_ref_choices + r"\s*([\d+.])\s*" + minute_variants + r"\s+" +
                                       datetime_diff_choices + r')')

    def _detect_hour_minute(self, time_list, original_list):
        """

        Returns:

        """
        time_list = time_list or []
        original_list = original_list or []

        regex_hour_match = self.regex_hour.findall(self.processed_text)
        for time_match in regex_hour_match:
        if regex_hour_match:
            print regex_hour_match
            regex_hour_match = regex_hour_match[0]
            hh = float(regex_hour_match[1])
            if regex_hour_match[0]:
                val_add = self.datetime_constant_dict[regex_hour_match[0]][1]
                print val_add
                hh = hh + val_add
            if regex_hour_match[3] and regex_hour_match[2] not in IGNORE_DIFF_HOUR_LIST:
                ref_date = self.now_date + datetime_dict[regex_hour_match[3]][1] * timedelta(hours=hh)
                return get_hour_min_diff(today, ref_date)

        # regex to match text like '30 minutes', '12 minute pehle'
        regex_minute_match = REGEX_MINUTE_TIME_1.findall(text)
        if regex_minute_match:
            regex_minute_match = regex_minute_match[0]
            mm = float(regex_minute_match[1])
            if regex_minute_match[3]:
                ref_date = self.now_date + self,datetime_constant_dict[regex_minute_match[3]][1] * \
                           timedelta(hours=hh, minutes=mm)
                return get_hour_min_diff(today, ref_date)

        print hh, mm
        for each in DAYTIME_MERIDIAN:
            if each in text:
                nn = DAYTIME_MERIDIAN[each]

        if type(hh) == float:
            mm = int((hh - int(hh)) * 60)
            hh = int(hh)
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

    def _detect_time_from_standard_regex(self, text, tag):
        """
        Method which will detect date from given text by running the parser in order defined in
        self.detector_preferences
        Args:
            text (str): text from which date has to be detected
            tag (str): tag by which entity in text will be replaced

        Returns:
            (dict): containing detected day, month, year if detected else empty dict
        """
        time_list, original_list = None, None
        self.text = text
        self.processed_text = self.text
        self.tag = tag
        for detector in self.detector_preferences:
            time_list, original_list = detector(time_list, original_list)
            self._update_processed_text(original_list)

        return time_list, original_list
