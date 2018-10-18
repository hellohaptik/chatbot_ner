from chatbot_ner.config import ner_logger
from ner_v2.detectors.constant import TYPE_EXACT, TWELVE_HOUR
from ner_v2.detectors.temporal.constant import DATETIME_CONSTANT_FILE, ADD_DIFF_DATETIME_TYPE, NUMERALS_CONSTANT_FILE, \
    TIME_CONSTANT_FILE, REF_DATETIME_TYPE, HOUR_TIME_TYPE, MINUTE_TIME_TYPE, DAYTIME_MERIDIAN
import pytz
import re
import datetime

from ner_v2.detectors.temporal.utils import get_tuple_dict, get_hour_min_diff


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

        # define dynamic created standard regex for time from language data files
        self.regex_time = None

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
                                        self.time_constant_dict[x][0] == HOUR_TIME_TYPE]) + "|)"
        minute_variants = "(" + "|".join([x for x in self.time_constant_dict if
                                          self.time_constant_dict[x][0] == MINUTE_TIME_TYPE]) + "|)"
        daytime_meridian = "(" + "|".join([x for x in self.time_constant_dict if
                                           self.time_constant_dict[x][0] == DAYTIME_MERIDIAN]) + "|)"

        self.regex_time = re.compile(r'(' + daytime_meridian + r'\s*[a-z]*\s*' + datetime_add_ref_choices +
                                     r'\s*([\d.]+)\s*' + hour_variants + r'\s*([\d]*)\s*' + minute_variants + r'\s+'
                                     + datetime_diff_choices + r'\s*' + daytime_meridian + r')')

    def _detect_hour_minute(self, time_list, original_list):
        """
        Parser to detect time for following text:
            i) 2 baje
            ii) 2 ghante baad
            iii) 2 bajkar 30 minute
            iv) dhaai baje
            v) shaam me 5 baje
            vi) subah me paune 9 baje
            v) 30 minute baad
            vi) 5 baje shaam me
        Returns:
            time_list (list): list of dict containing hour, minute, time type from detected text
            original_list (list): list of original text corresponding to values detected

        """
        time_list = time_list or []
        original_list = original_list or []

        regex_hour_match = self.regex_time.findall(self.processed_text)
        for time_match in regex_hour_match:
            hh = 0
            mm = 0
            nn = None
            original = time_match[0].strip()
            val = float(time_match[3])

            if time_match[2]:
                val_add = self.datetime_constant_dict[time_match[2]][1]
                val = val + val_add

            if time_match[4]:
                hh = val
            else:
                mm = val

            if time_match[5]:
                mm = float(time_match[5])

            if time_match[7]:
                ref_date = self.now_date + int(self.datetime_constant_dict[time_match[7]][1]) * \
                           datetime.timedelta(hours=hh, minutes=mm)

                hh, mm, nn = get_hour_min_diff(self.now_date, ref_date)

            if int(hh) != hh:
                mm = int((hh - int(hh)) * 60)
                hh = int(hh)

            if hh > 12:
                nn = TWELVE_HOUR

            if not nn:
                for key, values in self.time_constant_dict.items():
                    if values[0] == DAYTIME_MERIDIAN and key in original:
                        nn = values[1]

            time = {
                'hh': int(hh),
                'mm': int(mm),
                'nn': nn
            }

            time_list.append(time)
            original_list.append(original)

        return time_list, original_list

    def _update_processed_text(self, original_time_list):
        """
        Replaces detected time with tag generated from entity_name used to initialize the object with

        A final string with all time replaced will be stored in object's tagged_text attribute
        A string with all time removed will be stored in object's processed_text attribute

        Args:
            original_time_list (list): list of substrings of original text to be replaced with tag
                                       created from entity_name
        """
        for detected_text in original_time_list:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')

    def _detect_time_from_standard_regex(self):
        """
        Method which will detect time from given text by running the parser in order defined in
        self.detector_preferences
        Args:

        Returns:
            time_list (list): list of dict containing hour, minute, time type from detected text
            original_list (list): list of original text corresponding to values detected
        """
        time_list, original_list = None, None
        for detector in self.detector_preferences:
            time_list, original_list = detector(time_list, original_list)
            self._update_processed_text(original_list)

        return time_list, original_list
