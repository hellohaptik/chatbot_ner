from __future__ import absolute_import
from datetime import datetime
import re
import pytz
from ner_v1.constant import TWELVE_HOUR, PM_MERIDIEM, AM_MERIDIEM, EVERY_TIME_TYPE
from ner_v1.detectors.base_detector import BaseDetector
from language_utilities.constant import ENGLISH_LANG


class TimeDetector(BaseDetector):
    """Detects time in various formats from given text and tags them.

    Detects all time entities in given text and replaces them by entity_name.
    Additionally there are methods to get detected time values in dictionary containing values for hour (hh),
    minutes (mm), notation/meridiem (nn = one of {'hrs', 'am', 'pm', 'df'}, df stands for difference)

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected time entities would be replaced with on calling detect_entity()
        tagged_text: string with time entities replaced with tag defined by entity_name
        processed_text: string with detected time entities removed
        time: list of time entities detected
        original_time_text: list to store substrings of the text detected as time entities
        tag: entity_name prepended and appended with '__'
        timezone: Optional, timezone identifier string that is used to create a pytz timezone object
        form_check: boolean, set to True at initialization, used when passed text is a form type message
        bot_message: str, set as the outgoing bot text/message
        departure_flag: bool, whether departure time is being detected
        return_flag: bool, whether return time is being detected
        range_enabled: bool, whether time range needs to be detected

    SUPPORTED FORMAT                                            METHOD NAME
    ------------------------------------------------------------------------------------------------------------
    1. 12 hour format                                           _detect_12_hour_format
    2. 12 hour format without minutes                           _detect_12_hour_without_min
    3. In X hours / minutes difference format                   _detect_time_with_difference
    4. 24 hour format                                           _detect_24_hour_format
    5. Restricted 24 hour format                                _detect_restricted_24_hour_format
    6. 12 hour word format                                      _detect_12_hour_word_format
    7. 12 hour word format (hour only version)                  _detect_12_hour_word_format2
    8. 24 hour without format                                   _detect_24_hour_without_format
    9. Before / After / By / At / Exactly hhmm 12 hour format   _detect_time_without_format
    10. o'clock 12 hour format                                  _detect_time_without_format_preceeding
    11. 12 hour range format                                    _detect_range_12_hour_format
    12. 12 hour range format without minutes                    _detect_range_12_hour_format_without_min
    13. 12 hour start range format                              _detect_start_range_12_hour_format
    14. 12 hour end range format time                           _detect_end_range_12_hour_format
    15. 12 hour start range format without minutes              _detect_start_range_12_hour_format_without_min
    16. 12 hour end range format without minutes                _detect_end_range_12_hour_format_without_min
    17. X hour/mins later format                                _detect_time_with_difference_later
    18. every x hour, every x mins format                       _detect_time_with_every_x_hour
    19. once in x day format                                    _detect_time_with_once_in_x_day
    20. morning time range format                               _get_morning_time_range
    21. afternoon time range format                             _get_afternoon_time_range
    22. evening time range format                               _get_evening_time_range
    23. night time range format                                 _get_night_time_range
    24. No time preference format                               _get_default_time_range

    See respective methods for detail on structures of these formats

    Note:
        text and tagged_text will have a extra space prepended and appended after calling detect_entity(text)
    """

    def __init__(self, entity_name, timezone='UTC', range_enabled=False, form_check=False,
                 source_language_script=ENGLISH_LANG,
                 translation_enabled=False):
        """Initializes a TimeDetector object with given entity_name and timezone

        Args:
            entity_name (str): A string by which the detected time stamp substrings would be replaced with on calling
                        detect_entity()
            timezone (str): timezone identifier string that is used to create a pytz timezone object
                            default is UTC
            range_enabled (bool): whether time range needs to be detected
            form_check (bool): Optional, boolean set to False, used when passed text is a form type message
            source_language_script (str): ISO 639 code for language of entities to be detected by the instance of this
                                          class
            translation_enabled (bool): True if messages needs to be translated in case detector does not support a
                                        particular language, else False

        """
        # assigning values to superclass attributes
        self._supported_languages = [ENGLISH_LANG]
        super(TimeDetector, self).__init__(source_language_script, translation_enabled)
        self.entity_name = entity_name
        self.text = ''
        self.departure_flag = False
        self.return_flag = False
        self.tagged_text = ''
        self.processed_text = ''
        self.time = []
        self.original_time_text = []
        self.form_check = form_check
        self.tag = '__' + entity_name + '__'
        self.bot_message = None
        self.timezone = timezone or 'UTC'
        self.range_enabled = range_enabled

    @property
    def supported_languages(self):
        return self._supported_languages

    def _detect_time(self):
        """
        Detects all time strings in text and returns list of detected time entities and their corresponding original
        substrings in text

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing
            containing hour, minutes and meridiem/notation - either 'am', 'pm', 'hrs', 'df' ('df' denotes relative
            difference to current time) for each detected time, and second list containing corresponding original
            substrings in text

        """
        time_list = []
        original_list = []
        time_list, original_list = self._detect_range_12_hour_format(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_range_12_hour_format_without_min(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_start_range_12_hour_format(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_start_range_12_hour_format_without_min(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_end_range_12_hour_format(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_end_range_12_hour_format_without_min(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_12_hour_format(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_12_hour_without_min(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_time_with_difference(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_time_with_difference_later(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_time_with_every_x_hour(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_time_with_once_in_x_day(time_list, original_list)
        self._update_processed_text(original_list)
        if self.form_check:
            time_list, original_list = self._detect_24_hour_format(time_list, original_list)
            self._update_processed_text(original_list)
        time_list, original_list = self._detect_restricted_24_hour_format(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_12_hour_word_format(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_12_hour_word_format2(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_24_hour_without_format(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_time_without_format(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_time_without_format_preceeding(time_list, original_list)
        self._update_processed_text(original_list)
        if not time_list:
            time_list, original_list = self._get_morning_time_range(time_list, original_list)
            self._update_processed_text(original_list)
            time_list, original_list = self._get_afternoon_time_range(time_list, original_list)
            self._update_processed_text(original_list)
            time_list, original_list = self._get_evening_time_range(time_list, original_list)
            self._update_processed_text(original_list)
            time_list, original_list = self._get_night_time_range(time_list, original_list)
            self._update_processed_text(original_list)
            time_list, original_list = self._get_default_time_range(time_list, original_list)
            self._update_processed_text(original_list)
        if not self.range_enabled and time_list:
            time_list, original_list = self._remove_time_range_entities(time_list=time_list,
                                                                        original_list=original_list)
        return time_list, original_list

    def detect_entity(self, text, **kwargs):
        """
        Detects all time strings in text and returns two lists of detected time entities and their corresponding
        original substrings in text respectively.

        Args:
            text (str): string to extract time entities from
            **kwargs: it can be used to send specific arguments in future.

        Returns:
            Tuple containing two lists, first containing dictionaries, containing
            hour, minutes and meridiem/notation - either 'am', 'pm', 'hrs', 'df' ('df' denotes relative
            difference to current time) for each detected time, and second list containing corresponding original
            substrings in text

            Example:
                time_detector = TimeDetector("time")
                time_detector.detect_entity('John arrived at the bus stop at 13:50 hrs, expecting the bus to be
                                            there in 15 mins. But the bus was scheduled for 12:30 pm')

                    ([{'hh': 13, 'mm': 50, 'nn': 'hrs'},
                      {'hh': 0, 'mm': '15', 'nn': 'df'},
                      {'hh': 11, 'mm': 50, 'nn': 'pm'}],
                     ['12:30 pm', 'in 15 mins', '13:50'])

                time_detector.tagged_text

                    ' john arrived at the bus stop at __time__ hrs, expecting the bus to be there __time__.
                    but the bus was scheduled for __time__ '

        Additionally this function assigns these lists to self.time and self.original_time_text attributes
        respectively.

        """
        self.text = ' ' + text + ' '
        self.processed_text = self.text.lower()
        self.departure_flag = True if re.search(r'depart', self.text.lower()) else False
        self.return_flag = True if re.search(r'return', self.text.lower()) else False
        self.tagged_text = self.text.lower()
        time_data = self._detect_time()
        self.time = time_data[0]
        self.original_time_text = time_data[1]
        return time_data

    def _update_processed_text(self, original_time_strings):
        """
        Replaces detected time entities with tag generated from entity_name used to initialize the object with

        A final string with all time entities replaced will be stored in object's tagged_text attribute
        A string with all time entities removed will be stored in object's processed_text attribute

        Args:
            original_time_strings (list): list of substrings of original text to be replaced with tag created
                                          from entity_name
        """
        for detected_text in original_time_strings:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')

    def _detect_range_12_hour_format(self, time_list=None, original_list=None):
        """
        Finds 12 hour range format time from text
        CURRENTLY IT IS LIMITED ONLY TO ONE RANGE PER TEXT

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(
            r'\s(([0]?[2-9]|[0]?1[0-2]?)[\s-]*(?::|\.|\s)?[\s-]*?([0-5][0-9])[\s-]*?(pm|am|a.m|p.m)[\s-]*?[t][o][\s-]'
            r'*?([0]?[2-9]|[0]?1[0-2]?)[\s-]*(?::|\.|\s)?[\s-]*?([0-5][0-9])[\s-]*?(pm|am|a.m|p.m))',
            self.processed_text.lower())
        for pattern in patterns:
            original1 = pattern[0]
            original2 = pattern[0]
            if self.departure_flag:
                time_type = 'departure'
            elif self.return_flag:
                time_type = 'return'
            else:
                time_type = None
            t1 = pattern[1]
            t2 = pattern[2]
            ap1 = pattern[3]
            time1 = {
                'hh': int(t1),
                'mm': int(t2),
                'nn': str(ap1).lower().strip('.'),
                'range': 'start',
                'time_type': time_type
            }
            time1['nn'] = 'am' if 'a' in time1['nn'] else time1['nn']
            time1['nn'] = 'pm' if 'p' in time1['nn'] else time1['nn']

            t3 = pattern[4]
            t4 = pattern[5]
            ap2 = pattern[6]
            time2 = {
                'hh': int(t3),
                'mm': int(t4),
                'nn': str(ap2).lower().strip('.'),
                'range': 'end',
                'time_type': time_type
            }
            time2['nn'] = 'am' if 'a' in time2['nn'] else time2['nn']
            time2['nn'] = 'pm' if 'p' in time2['nn'] else time2['nn']

            time_list.append(time1)
            original_list.append(original1)
            time_list.append(time2)
            original_list.append(original2)
            break
        return time_list, original_list

    def _detect_range_12_hour_format_without_min(self, time_list=None, original_list=None):
        """
        Finds 12 hour range format time from text without minutes
        CURRENTLY IT IS LIMITED ONLY TO ONE RANGE PER TEXT

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(
            r'\s(([0]?[2-9]|[0]?1[0-2]?)[\s-]*(am|pm|a.m|p.m)[\s-]*?[t][o][\s-]*?([0]?[2-9]|[0]?1[0-2]?)[\s-]*'
            r'(am|pm|a.m|p.m))',
            self.processed_text.lower())
        for pattern in patterns:
            original1 = pattern[0]
            original2 = pattern[0]
            if self.departure_flag:
                time_type = 'departure'
            elif self.return_flag:
                time_type = 'return'
            else:
                time_type = None
            t1 = pattern[1]
            ap1 = pattern[2]
            time1 = {
                'hh': int(t1),
                'mm': 0,
                'nn': str(ap1).lower().strip('.'),
                'range': 'start',
                'time_type': time_type
            }
            time1['nn'] = 'am' if 'a' in time1['nn'] else time1['nn']
            time1['nn'] = 'pm' if 'p' in time1['nn'] else time1['nn']

            t2 = pattern[3]
            ap2 = pattern[4]
            time2 = {
                'hh': int(t2),
                'mm': 0,
                'nn': str(ap2).lower().strip('.'),
                'range': 'end',
                'time_type': time_type
            }
            time2['nn'] = 'am' if 'a' in time2['nn'] else time2['nn']
            time2['nn'] = 'pm' if 'p' in time2['nn'] else time2['nn']

            time_list.append(time1)
            original_list.append(original1)
            time_list.append(time2)
            original_list.append(original2)
            break
        return time_list, original_list

    def _detect_start_range_12_hour_format(self, time_list=None, original_list=None):
        """
        Finds 12 hour start range format time from text - after 3.30 pm
        CURRENTLY IT IS LIMITED ONLY TO ONE RANGE PER TEXT

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\s((after|aftr)[\s-]*([0]?[2-9]|[0]?1[0-2]?)[\s-]*(?::|\.|\s)?[\s-]*?'
                              r'([0-5][0-9])[\s-]*?(pm|am|a.m|p.m))',
                              self.processed_text.lower())
        for pattern in patterns:
            original1 = pattern[0]
            if self.departure_flag:
                time_type = 'departure'
            elif self.return_flag:
                time_type = 'return'
            else:
                time_type = None
            t1 = pattern[2]
            t2 = pattern[3]
            ap1 = pattern[4]
            time1 = {
                'hh': int(t1),
                'mm': int(t2),
                'nn': str(ap1).lower().strip('.'),
                'range': 'start',
                'time_type': time_type
            }
            time1['nn'] = 'am' if 'a' in time1['nn'] else time1['nn']
            time1['nn'] = 'pm' if 'p' in time1['nn'] else time1['nn']

            time_list.append(time1)
            original_list.append(original1)
            break
        return time_list, original_list

    def _detect_end_range_12_hour_format(self, time_list=None, original_list=None):
        """
        Finds 12 hour end range format time from text - 'before 3.30 pm'
        CURRENTLY IT IS LIMITED ONLY TO ONE RANGE PER TEXT

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\s((before|bfre)[\s-]*([0]?[2-9]|[0]?1[0-2]?)[\s-]*'
                              r'(?::|\.|\s)?[\s-]*?([0-5][0-9])[\s-]*?(pm|am|a.m|p.m))',
                              self.processed_text.lower())
        for pattern in patterns:
            original1 = pattern[0]
            if self.departure_flag:
                time_type = 'departure'
            elif self.return_flag:
                time_type = 'return'
            else:
                time_type = None
            t1 = pattern[2]
            t2 = pattern[3]
            ap1 = pattern[4]
            time1 = {
                'hh': int(t1),
                'mm': int(t2),
                'nn': str(ap1).lower().strip('.'),
                'range': 'end',
                'time_type': time_type
            }
            time1['nn'] = 'am' if 'a' in time1['nn'] else time1['nn']
            time1['nn'] = 'pm' if 'p' in time1['nn'] else time1['nn']
            time_list.append(time1)
            original_list.append(original1)
            break
        return time_list, original_list

    def _detect_start_range_12_hour_format_without_min(self, time_list=None, original_list=None):
        """
        Finds start 12 hour format time from text without mins mentioned - 'after 5 pm'
        CURRENTLY IT IS LIMITED ONLY TO ONE RANGE PER TEXT

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\s((after|aftr)[\s-]*([0]?[2-9]|[0]?1[0-2]?)[\s-]*(am|pm|a.m|p.m))',
                              self.processed_text.lower())
        for pattern in patterns:
            original1 = pattern[0]
            if self.departure_flag:
                time_type = 'departure'
            elif self.return_flag:
                time_type = 'return'
            else:
                time_type = None
            t1 = pattern[2]
            ap1 = pattern[3]
            time1 = {
                'hh': int(t1),
                'mm': 0,
                'nn': str(ap1).lower().strip('.'),
                'range': 'start',
                'time_type': time_type
            }
            time1['nn'] = 'am' if 'a' in time1['nn'] else time1['nn']
            time1['nn'] = 'pm' if 'p' in time1['nn'] else time1['nn']

            time_list.append(time1)
            original_list.append(original1)
            break
        return time_list, original_list

    def _detect_end_range_12_hour_format_without_min(self, time_list=None, original_list=None):
        """
        Finds end range 12 hour format without mins mentioned time from text - ' before 9 pm'
        CURRENTLY IT IS LIMITED ONLY TO ONE RANGE PER TEXT

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\s((before|bfore)[\s-]*([0]?[2-9]|[0]?1[0-2]?)[\s-]*(am|pm|a.m|p.m))',
                              self.processed_text.lower())
        for pattern in patterns:
            original1 = pattern[0]
            if self.departure_flag:
                time_type = 'departure'
            elif self.return_flag:
                time_type = 'return'
            else:
                time_type = None
            t1 = pattern[2]
            ap1 = pattern[3]
            time1 = {
                'hh': int(t1),
                'mm': 0,
                'nn': str(ap1).lower().strip('.'),
                'range': 'end',
                'time_type': time_type
            }
            time1['nn'] = 'am' if 'a' in time1['nn'] else time1['nn']
            time1['nn'] = 'pm' if 'p' in time1['nn'] else time1['nn']
            time_list.append(time1)
            original_list.append(original1)
            break
        return time_list, original_list

    def _detect_12_hour_format(self, time_list=None, original_list=None):
        """
        Detects time in the following format

        format: <hour><Optional extra separator><Optional separator><minutes><Optional extra separator><meridiem>
        where each part is in of one of the formats given against them
            hour: h, hh
            minute: m, mm
            meridiem: "am", "pm", "a.m", "p.m"
            separator:  ":", "."
            extra separator: "-", space(s)


        Few valid examples:
            "10:33 pm", "1033pm",
            "02 33 p.m", "2-33-a.m",
            "012 - 59 am", "012 59 am", "12.59-am", "012:59 am"

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\D(([0]?[2-9]|[0]?1[0-2]?)[\s-]*(?::|\.|\s)?[\s-]*?'
                              r'([0-5][0-9])[\s-]*?(pm|am|a.m|p.m))',
                              self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            t1 = pattern[1]
            t2 = pattern[2]
            ap = pattern[3]
            time = {
                'hh': int(t1),
                'mm': int(t2),
                'nn': str(ap).lower().strip('.')
            }

            time['nn'] = 'am' if 'a' in time['nn'] else time['nn']
            time['nn'] = 'pm' if 'p' in time['nn'] else time['nn']
            time_list.append(time)
            original_list.append(original)
        return time_list, original_list

    def _detect_12_hour_without_min(self, time_list=None, original_list=None):
        """
        Detects time in the following format

        format: <hour><Optional extra separator><meridiem>
        where each part is in of one of the formats given against them
            hour: h, hh
            meridiem: "am", "pm", "a.m", "p.m"
            extra separator: "-", space(s)


        Few valid examples:
            "10 pm", "10-pm",
            "02 pm", "2-am",
            "012 - am"

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\s(([0]?[2-9]|[0]?1[0-2]?)[\s-]*(am|pm|a.m|p.m))', self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            t1 = pattern[1]
            ap = pattern[2]
            time = {
                'hh': int(t1),
                'mm': 0,
                'nn': str(ap).lower().strip('.')
            }
            time['nn'] = 'am' if 'a' in time['nn'] else time['nn']
            time['nn'] = 'pm' if 'p' in time['nn'] else time['nn']
            time_list.append(time)
            original_list.append(original)
        return time_list, original_list

    def _detect_time_with_difference(self, time_list=None, original_list=None):
        """
        Detects time in the following format

        format: <prefix><space><integer><Optional space><minute or hour suffix>
        where each part is in of one of the formats given against them
            prefix: "in about", "in", "after"
            minute or hour suffix: "min", "mins", "minutes", "hour", "hours", "hrs", "hr"
            integer: integer of any length

        The notation nn returned from this method is 'df' denoting relative difference from current time

        Few valid examples:
            "in 30mins", "in  about 40000000hours"

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\b((in\sabout|in|after)\s(\d+)\s?(min|mins|minutes|hour|hours|hrs|hr))\b',
                              self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            t1 = pattern[2]
            td = pattern[3]
            hours = ['hour', 'hours', 'hrs', 'hr']
            mins = ['min', 'mins', 'minutes']
            setter = ""
            antisetter = ""
            if td in hours:
                setter = "hh"
                antisetter = "mm"
            elif td in mins:
                setter = "mm"
                antisetter = "hh"
            time = dict()
            time[setter] = int(t1)
            time[antisetter] = 0
            time['nn'] = 'df'
            time_list.append(time)
            original_list.append(original)
        return time_list, original_list

    def _detect_time_with_difference_later(self, time_list=None, original_list=None):
        """
        Get time for phrases like X hour/mins later

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\b((\d+)\s?(min|mins|minutes|hour|hours|hrs|hr)\s?(later|ltr|latr|lter)s?)\b',
                              self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            t1 = pattern[1]
            td = pattern[2]
            hours = ['hour', 'hours', 'hrs', 'hr']
            mins = ['min', 'mins', 'minutes']
            setter = ""
            antisetter = ""
            if td in hours:
                setter = "hh"
                antisetter = "mm"
            elif td in mins:
                setter = "mm"
                antisetter = "hh"
            time = dict()
            time[setter] = int(t1)
            time[antisetter] = 0
            time['nn'] = 'df'
            time_list.append(time)
            original_list.append(original)
        return time_list, original_list

    def _detect_time_with_every_x_hour(self, time_list=None, original_list=None):
        """
        Get time for phrases every 6 hour, every 30 mins

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\b((every|evry|evy|evri)\s*(\d+)\s*(min|mins|minutes|hour|hours|hrs|hr))\b',
                              self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            t1 = int(pattern[2])
            td = pattern[3]
            hours = ['hour', 'hours', 'hrs', 'hr']
            mins = ['min', 'mins', 'minutes']
            setter = ""
            antisetter = ""
            if td in hours:
                setter = "hh"
                antisetter = "mm"
            elif td in mins:
                setter = "mm"
                antisetter = "hh"
            time = dict()
            time[setter] = int(t1)
            time[antisetter] = 0
            time['nn'] = EVERY_TIME_TYPE
            time_list.append(time)
            original_list.append(original)
        return time_list, original_list

    def _detect_time_with_once_in_x_day(self, time_list=None, original_list=None):
        """
        Get time for phrases like once in 1 day (treated it as no of hours, once in 1 day means every 24 hours)

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\b((once|onc|1se)\s*(in)?\s*(\d+)\s?(day|days))\b',
                              self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            t1 = 24 * int(pattern[3])
            setter = "hh"
            antisetter = "mm"
            time = dict()
            time[setter] = int(t1)
            time[antisetter] = 0
            time['nn'] = EVERY_TIME_TYPE
            time_list.append(time)
            original_list.append(original)
        return time_list, original_list

    def _detect_24_hour_format(self, time_list=None, original_list=None):
        """
        Detects time in the following format

        format: <hour><separator><Optional minutes><any character except digits and meridiems>
        where each part is in of one of the formats given against them
            hour: h, hh (24 hour)
            minute: m, mm
            separator:  ":", ".", space

        Few valid examples:
            "02:59h", "14:33 ",
            "14: ", "00.45", "013 41"

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\D((00|[0]?[2-9]|[0]?1[0-9]?|2[0-3])[:.\s]([0-5][0-9])?)[^am|pm|a.m|p.m|\d]',
                              self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            t2 = 0
            t1 = pattern[1]
            if pattern[2]:
                t2 = pattern[2]

            time = {
                'hh': int(t1),
                'mm': int(t2),
                'nn': 'hrs'
            }
            time_list.append(time)
            original_list.append(original)
        return time_list, original_list

    def _detect_restricted_24_hour_format(self, time_list=None, original_list=None):
        """
        Detects time in the following format

        format: <hour><separator><minutes><any character except digits and meridiems>
        where each part is in of one of the formats given against them
            hour: hh (24 hour; 13 - 23, or 00)
            minute: m, mm
            separator:  ":", ".", space

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\D((00|1[3-9]?|2[0-3])[:.\s]([0-5][0-9]))[^am|pm|a.m|p.m|\d]',
                              self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            t1 = pattern[1]
            t2 = pattern[2]
            meridiem = self._get_meridiem(int(t1), int(t2))

            time = {
                'hh': int(t1),
                'mm': int(t2),
                'nn': meridiem
            }
            time_list.append(time)
            original_list.append(original)
        return time_list, original_list

    def _detect_12_hour_word_format(self, time_list=None, original_list=None):
        """
        First it looks for following pattern

        <hour><separator><minutes><any character except digits and meridiems>
        where each part is in of one of the formats given against them
            hour: h, hh
            minute: m, mm
            separator:  ":", ".", space

        Then to decide the meridiem (AM or PM), it looks for one of the following words in following order

        a.m. if any of ["morning", "early", "subah", "mrng", "mrning", "savere"]
        p.m. if any of ["noon", "afternoon", "evening", "evng", "evning", "sham"]
        a.m. if any of ["night", "nite", "tonight", "latenight", "tonit", "nit", "rat"] and hh is less than 5,
             otherwise p.m.

        Few valid examples:

        "02:59 morning", "14:33 early",
        "evening 14: ", "00.45 noon", "tonight 013 41z "

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\D(([0]?[1-9]|1[0-1])[:.\s]([0-5][0-9]))[^am|pm|a.m|p.m|\d]',
                              self.processed_text.lower())
        pattern_am = re.findall(r'\s(morning|early|subah|mrng|mrning|savere)\s', self.processed_text.lower())
        pattern_pm = re.findall(r'\s(noon|afternoon|evening|evng|evning|sham)\s', self.processed_text.lower())
        pattern_night = re.findall(r'\s(night|nite|tonight|latenight|tonit|nit|rat)\s', self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            t1 = pattern[1]
            t2 = pattern[2]
            time = {
                'hh': int(t1),
                'mm': int(t2),
            }
            if len(pattern_am) > 0:
                time['nn'] = 'am'
            elif len(pattern_pm) > 0:
                time['nn'] = 'pm'
            elif len(pattern_night) > 0:
                time['nn'] = 'am' if int(t1) < 5 else 'pm'
            else:
                return time_list, original_list
            time_list.append(time)
            original_list.append(original)
        return time_list, original_list

    def _detect_12_hour_word_format2(self, time_list=None, original_list=None):
        """
        First it looks for following pattern:

        <prefix><Optional separator><hour>
        where each part is in of one of the formats given against them
            prefix:  "by", "before", "after", "at", "on", "dot", "exactly", "exact"
            hour: h, hh
            minute: m, mm
            separator: "-", space

        Then to decide the meridiem (AM or PM), it looks for one of the following words in following order

        a.m. if any of ["morning", "early", "subah", "mrng", "mrning", "savere"]
        p.m. if any of ["noon", "afternoon", "evening", "evng", "evning", "sham"]
        a.m. if any of ["night", "nite", "tonight", "latenight", "tonit", "nit", "rat"] and hh is less than 5,
             otherwise p.m.

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'((?:by|before|after|at|on|dot|exactly|exact)[\s-]*([1-9]|1[0-2]?))\D',
                              self.processed_text.lower())
        pattern_am = re.findall(r'\s(morning|early|subah|mrng|mrning|savere)', self.processed_text.lower())
        pattern_pm = re.findall(r'\s(noon|afternoon|evening|evng|evning|sham)', self.processed_text.lower())
        pattern_night = re.findall(r'\s(night|nite|tonight|latenight|tonit|nit|rat)', self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            t1 = pattern[1]
            time = {
                'hh': int(t1),
                'mm': 0,
            }
            if len(pattern_am) > 0:
                time['nn'] = 'am'
            elif len(pattern_pm) > 0:
                time['nn'] = 'pm'
            elif len(pattern_night) > 0:
                time['nn'] = 'am' if int(t1) < 5 else 'pm'
            else:
                return time_list, original_list
            time_list.append(time)
            original_list.append(original)
        return time_list, original_list

    def _detect_24_hour_without_format(self, time_list=None, original_list=None):
        """
        Detects time in the following format

        format: <hour><separator><minutes><any character except digits and meridiems>
        where each part is in of one of the formats given against them
            hour: h, hh (24 hour)
            minute: m, mm
            separator:  ":", ".", space

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\D((00|[0]?[2-9]|[0]?1[0-9]?|2[0-3])[:.\s]([0-5][0-9]))[^am|pm|a.m|p.m|\d]',
                              self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            t1 = pattern[1]
            t2 = pattern[2]
            meridiem = self._get_meridiem(int(t1), int(t2))
            time = {
                'hh': int(t1),
                'mm': int(t2),
                'nn': meridiem
            }
            time_list.append(time)
            original_list.append(original)
        return time_list, original_list

    def _detect_time_without_format(self, time_list=None, original_list=None):
        """
        Detects time in the following format

        format: <prefix><Optional extra separator><hour><Optional separator><minutes>
        where each part is in of one of the formats given against them
            prefix:  "by", "before", "after", "at", "on", "dot", "exactly", "exact"
            hour: h, hh
            minute: m, mm
            extra separator: "-", space
            separator:  ":", ".", space

        The meridiem is given assuming the time detected to be in within 12 hour span from the current timestamp.

        For example,
            If it is 5:33 AM at the moment of invoking this method, 6:20 would be assigned 'AM'
            as 5:33 AM <= 6:20 AM < 5:33 PM and 4:30 would be assigned 'PM' as 5:33 AM <= 4:30 PM < 5:33 PM

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'((?:by|before|after|at|dot|exactly|exact)[\s-]*'
                              r'(([0]?[1-9]|1[0-2])[:.\s]*([0-5][0-9])?))\s',
                              self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            t1 = pattern[2]
            t2 = 0
            if pattern[3]:
                t2 = pattern[3]
            meridiem = self._get_meridiem(int(t1), int(t2))
            time = {
                'hh': int(t1),
                'mm': int(t2),
                'nn': meridiem
            }
            time_list.append(time)
            original_list.append(original)
        return time_list, original_list

    def _detect_time_without_format_preceeding(self, time_list=None, original_list=None):
        """
        Detects time in the following format

        format: <hour><Optional separator><minutes><suffix>
        where each part is in of one of the formats given against them
            hour: h, hh
            minute: m, mm
            separator:  ":", ".", space
            suffix: "o'clock", "o' clock", "clock", "oclock", "o clock", "hours"

        The meridiem is given assuming the time detected to be in within 12 hour span from the current timestamp.
        The meridiem is given assuming the time detected to be in within 12 hour span from the current timestamp.

        For example,
            If it is 12:30 PM at the moment of invoking this method, 1:45 would be assigned 'PM'
            as 12:30 PM <= 1:45 PM < 12:30 AM and 12:10 would be assigned 'AM' as 12:30 PM <= 12:10 AM < 12:30 AM

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\s((([0]?[1-9]|1[0-2])[:.\s]*([0-5][0-9])?)[\s-]*'
                              r'(?:o\'clock|o\' clock|clock|oclock|o clock|hours))\s',
                              self.processed_text.lower())

        if not patterns and self.bot_message:
            if re.findall(r"Time|time", self.bot_message.lower()):
                patterns = re.findall(r'\s*((([0-2]?[0-9])()))\s*', self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            t1 = pattern[2]
            t2 = 0
            if pattern[3]:
                t2 = pattern[3]
            meridiem = self._get_meridiem(int(t1), int(t2))
            time = {
                'hh': int(t1),
                'mm': int(t2),
                'nn': meridiem
            }
            time_list.append(time)
            original_list.append(original)
        return time_list, original_list

    def _get_meridiem(self, hours, mins):
        """
        Returns the meridiem(am/pm) for which the given hours:mins time is in within 12 hour span from the current
        timestamp.
        If hours value is greater than 12, 'hrs' is returned instead

        For example,
            If it is 12:30 PM at the moment of invoking this method, 1:45 would be assigned 'PM'
            as 12:30 PM <= 1:45 PM < 12:30 AM and 12:10 would be assigned 'AM' as 12:30 PM <= 12:10 AM < 12:30 AM

        Args:
            hours (int): hours in integer
            mins (int): mins in integer

        Returns
            meridiem type (str): returns the meridiem type whether its am and pm
        """
        current_datetime = datetime.now(pytz.timezone(self.timezone))
        current_hour = current_datetime.hour
        current_min = current_datetime.minute
        if hours == 0 or hours >= TWELVE_HOUR:
            return 'hrs'
        if current_hour >= TWELVE_HOUR:
            current_hour -= 12
            if current_hour < hours:
                return PM_MERIDIEM
            elif current_hour == hours and current_min < mins:
                return PM_MERIDIEM
        else:
            if current_hour > hours:
                return PM_MERIDIEM
            elif current_hour == hours and current_min > mins:
                return PM_MERIDIEM
        return AM_MERIDIEM

    def _get_morning_time_range(self, time_list=None, original_list=None):
        """
        This function returns time range for queries related to Morning without time_list

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # pattern to detect morning
        patterns = re.findall(r'\s(morning|early|subah|mrng|mrning|savere)', self.processed_text.lower())

        if patterns:
            original1 = patterns[0]
            if self.departure_flag:
                time_type = 'departure'
            elif self.return_flag:
                time_type = 'return'
            else:
                time_type = None
            time1 = {
                'hh': 12,
                'mm': 0,
                'nn': 'am',
                'range': 'start',
                'time_type': time_type
            }

            time2 = {
                'hh': 11,
                'mm': 0,
                'nn': 'am',
                'range': 'end',
                'time_type': time_type
            }

            time_list.append(time1)
            original_list.append(original1)
            time_list.append(time2)
            original_list.append(original1)

        return time_list, original_list

    def _get_afternoon_time_range(self, time_list=None, original_list=None):
        """
        This function returns time range for queries related to Afternoon without time_list

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # patterns
        patterns = re.findall(r'\s(noon|afternoon)', self.processed_text.lower())

        if patterns:
            original1 = patterns[0]
            if self.departure_flag:
                time_type = 'departure'
            elif self.return_flag:
                time_type = 'return'
            else:
                time_type = None
            time1 = {
                'hh': 11,
                'mm': 0,
                'nn': 'am',
                'range': 'start',
                'time_type': time_type
            }

            time2 = {
                'hh': 5,
                'mm': 0,
                'nn': 'pm',
                'range': 'end',
                'time_type': time_type
            }

            time_list.append(time1)
            original_list.append(original1)
            time_list.append(time2)
            original_list.append(original1)

        return time_list, original_list

    def _get_evening_time_range(self, time_list=None, original_list=None):
        """
        This function returns time range for queries related to Evening without time_list

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # patterns
        patterns = re.findall(r'\s(evening|evng|evning|sham)', self.processed_text.lower())

        if patterns:
            original1 = patterns[0]
            if self.departure_flag:
                time_type = 'departure'
            elif self.return_flag:
                time_type = 'return'
            else:
                time_type = None
            time1 = {
                'hh': 5,
                'mm': 0,
                'nn': 'pm',
                'range': 'start',
                'time_type': time_type
            }

            time2 = {
                'hh': 9,
                'mm': 0,
                'nn': 'pm',
                'range': 'end',
                'time_type': time_type
            }

            time_list.append(time1)
            original_list.append(original1)
            time_list.append(time2)
            original_list.append(original1)

        return time_list, original_list

    def _get_night_time_range(self, time_list=None, original_list=None):
        """
        This function returns time range for queries related to Night without time_list

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # patterns
        patterns = re.findall(r'\s(night|nite|tonight|latenight|tonit|nit|rat)', self.processed_text.lower())

        if patterns:
            original1 = patterns[0]
            if self.departure_flag:
                time_type = 'departure'
            elif self.return_flag:
                time_type = 'return'
            else:
                time_type = None
            time1 = {
                'hh': 9,
                'mm': 0,
                'nn': 'pm',
                'range': 'start',
                'time_type': time_type
            }

            time2 = {
                'hh': 12,
                'mm': 0,
                'nn': 'am',
                'range': 'end',
                'time_type': time_type
            }

            time_list.append(time1)
            original_list.append(original1)
            time_list.append(time2)
            original_list.append(original1)

        return time_list, original_list

    def _get_default_time_range(self, time_list=None, original_list=None):
        """
        This function returns time range for queries related to No time preference without time_list

        Args:
            time_list (list): Optional, list to store dictionaries of detected time entities
            original_list (list): Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # patterns
        preference = re.compile(r'\s(No particular preference|No preference|No particular time|No time|'
                                r'anytime|any time|all day|full day|entire day|entireday)')
        patterns = preference.findall(self.processed_text.lower())

        if patterns:
            original1 = patterns[0]
            if self.departure_flag:
                time_type = 'departure'
            elif self.return_flag:
                time_type = 'return'
            else:
                time_type = None
            time1 = {
                'hh': 12,
                'mm': 0,
                'nn': 'am',
                'range': 'start',
                'time_type': time_type
            }

            time2 = {
                'hh': 11,
                'mm': 59,
                'nn': 'pm',
                'range': 'end',
                'time_type': time_type
            }

            time_list.append(time1)
            original_list.append(original1)
            time_list.append(time2)
            original_list.append(original1)

        return time_list, original_list

    def set_bot_message(self, bot_message):
        """
        Sets the object's bot_message attribute

        Args:
            bot_message (str): previous message that is sent by the bot
        """
        self.bot_message = bot_message

    def _remove_time_range_entities(self, time_list, original_list):
        """
        This function removes time ranges from the time list and keeps only absolute time
        for example - it will keep patterns like 'at 8 pm' but remove patterns like 'anytime after 8pm'

        Args:
            time_list (list): list of detected time entities dict
            original_list (list): list of corresponding substrings of given text which were detected as
                                  time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        time_list_final = []
        original_list_final = []
        for i, entity in enumerate(time_list):
            if 'range' not in entity:
                time_list_final.append(entity)
                original_list_final.append(original_list[i])
            elif not entity['range']:
                time_list_final.append(entity)
                original_list_final.append(original_list[i])
        return time_list_final, original_list_final
