from datetime import datetime, timedelta
import re

from v1.entities.constant import TWELVE_HOUR, PM_MERIDIEM, AM_MERIDIEM
import pytz


class TimeDetector(object):
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
        timezone: Optional, pytz.timezone object used for getting current time, default is pytz.timezone('UTC')
        form_check: boolean, set to True at initialization, used when passed text is a form type message

    SUPPORTED FORMAT                                            METHOD NAME

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

    See respective methods for detail on structures of these formats

    Note:
        text and tagged_text will have a extra space prepended and appended after calling detect_entity(text)
    """

    def __init__(self, entity_name, timezone=pytz.timezone('UTC')):
        """Initializes a TimeDetector object with given entity_name and pytz timezone object

        Args:
            entity_name: A string by which the detected time stamp substrings would be replaced with on calling
                        detect_entity()
            timezone: Optional, pytz.timezone object used for getting current time, default is pytz.timezone('UTC')

        """
        self.entity_name = entity_name
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.time = []
        self.original_time_text = []
        self.tag = '__' + entity_name + '__'
        self.timezone = timezone
        # TODO form_check is Haptik specific ?
        self.form_check = True

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
        # print 'detection for default task'
        time_list = []
        original_list = []
        time_list, original_list = self._detect_12_hour_format(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_12_hour_without_min(time_list, original_list)
        self._update_processed_text(original_list)
        time_list, original_list = self._detect_time_with_difference(time_list, original_list)
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

        return time_list, original_list

    def detect_entity(self, text, form_check=False):
        """
        Detects all time strings in text and returns two lists of detected time entities and their corresponding
        original substrings in text respectively.

        Args:
            text: string to extract time entities from
            form_check: Optional, boolean set to False, used when passed text is a form type message

        Returns:
            Tuple containing two lists, first containing dictionaries, containing
            hour, minutes and meridiem/notation - either 'am', 'pm', 'hrs', 'df' ('df' denotes relative
            difference to current time) for each detected time, and second list containing corresponding original
            substrings in text

            Example:
                time_detector = TimeDetector("time")
                time_detector.detect_entity('John arrived at the bus stop at 13:50 hrs, expecting the bus to be there in
                                            15 mins.But the bus was scheduled for 12:30 pm')

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
        self.form_check = form_check
        self.text = ' ' + text + ' '
        self.processed_text = self.text.lower()
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
            original_time_strings: list of substrings of original text to be replaced with tag created from entity_name
        """
        for detected_text in original_time_strings:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')

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
            time_list: Optional, list to store dictionaries of detected time entities
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.

        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # print 'processed text : ', self.processed_text
        patterns = re.findall(
            r'\D(([0]?[2-9]|[0]?1[0-2]?)[\s-]*(?::|\.|\s)?[\s-]*?([0-5][0-9])[\s-]*?(pm|am|a.m|p.m))',
            self.processed_text.lower())
        # print 'pattern : ', patterns
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
            time_list: Optional, list to store dictionaries of detected time entities
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # print 'processed text: ', self.processed_text
        patterns = re.findall(r'\s(([0]?[2-9]|[0]?1[0-2]?)[\s-]*(am|pm))', self.processed_text.lower())
        # print 'pattern : ', patterns
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
            time_list: Optional, list to store dictionaries of detected time entities
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # print 'processed text: ', self.processed_text
        patterns = re.findall(r'\b((in\sabout|in|after)\s(\d+)\s?(min|mins|minutes|hour|hours|hrs|hr))\b',
                              self.processed_text.lower())
        # print 'pattern : ', patterns
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
            time = {}
            time[setter] = t1
            time[antisetter] = 0
            time['nn'] = 'df'
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
            time_list: Optional, list to store dictionaries of detected time entities
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # print 'processed text: ', self.processed_text
        patterns = re.findall(r'\D((00|[0]?[2-9]|[0]?1[0-9]?|2[0-3])[:.\s]([0-5][0-9])?)[^(am)|(pm)|(a.m)|(p.m)|\d]',
                              self.processed_text.lower())
        # print 'pattern : ', patterns
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
            time_list: Optional, list to store dictionaries of detected time entities
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # print 'processed text: ', self.processed_text
        patterns = re.findall(r'\D((00|1[3-9]?|2[0-3])[:.\s]([0-5][0-9]))[^(am)|(pm)|(a.m)|(p.m)|\d]',
                              self.processed_text.lower())
        # print 'pattern : ', patterns
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
            time_list: Optional, list to store dictionaries of detected time entities
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # print 'processed text: ', self.processed_text
        patterns = re.findall(r'\D(([0]?[1-9]|1[0-1])[:.\s]([0-5][0-9]))[^(am)|(pm)|(a.m)|(p.m)|\d]',
                              self.processed_text.lower())
        pattern_am = re.findall(r'\s(morning|early|subah|mrng|mrning|savere)', self.processed_text.lower())
        pattern_pm = re.findall(r'\s(noon|afternoon|evening|evng|evning|sham)', self.processed_text.lower())
        pattern_night = re.findall(r'\s(night|nite|tonight|latenight|tonit|nit|rat)', self.processed_text.lower())
        # print 'pattern : ', patterns
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
        time_list: Optional, list to store dictionaries of detected time entities
        original_list: Optional, list to store corresponding substrings of given text which were detected as
                        time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # print 'processed text: ', self.processed_text
        patterns = re.findall(r'((?:by|before|after|at|on|dot|exactly|exact)[\s-]*([1-9]|1[0-2]?))\D',
                              self.processed_text.lower())
        pattern_am = re.findall(r'\s(morning|early|subah|mrng|mrning|savere)', self.processed_text.lower())
        pattern_pm = re.findall(r'\s(noon|afternoon|evening|evng|evning|sham)', self.processed_text.lower())
        pattern_night = re.findall(r'\s(night|nite|tonight|latenight|tonit|nit|rat)', self.processed_text.lower())
        # print 'pattern : ', patterns
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
            time_list: Optional, list to store dictionaries of detected time entities
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # print 'processed text: ', self.processed_text
        patterns = re.findall(r'\D((00|[0]?[2-9]|[0]?1[0-9]?|2[0-3])[:.\s]([0-5][0-9]))[^(am)|(pm)|(a.m)|(p.m)|\d]',
                              self.processed_text.lower())
        # print 'pattern : ', patterns
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
            time_list: Optional, list to store dictionaries of detected time entities
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # print 'processed text: ', self.processed_text
        regex_string = r'((?:by|before|after|at|dot|exactly|exact)[\s-]*(([0]?[1-9]|1[0-2])[:.\s]*([0-5][0-9])?))\s'
        patterns = re.findall(regex_string, self.processed_text.lower())
        # print 'pattern : ', patterns
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
            time_list: Optional, list to store dictionaries of detected time entities
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            time entities

        Returns:
            A tuple of two lists with first list containing the detected time entities and second list containing their
            corresponding substrings in the given text.
        """
        if time_list is None:
            time_list = []
        if original_list is None:
            original_list = []
        # print 'processed text: ', self.processed_text
        regex_string = r'\s((([0]?[1-9]|1[0-2])[:.\s]*([0-5][0-9])?)[\s-]*' + \
                       r'(?:o\'clock|o\' clock|clock|oclock|o clock|hours))\s'
        patterns = re.findall(regex_string, self.processed_text.lower())
        # print 'pattern : ', patterns
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

        """
        if hours > TWELVE_HOUR:
            return 'hrs'
        else:
            right_now = datetime.now(self.timezone)
            after_twelve_hours = right_now + timedelta(hours=12)

            def check(hour_value):
                possible_datetime = right_now.replace(hour=hour_value, minute=mins)
                if possible_datetime < right_now:
                    possible_datetime = possible_datetime + timedelta(days=1)
                if right_now <= possible_datetime < after_twelve_hours:
                    if 0 <= possible_datetime.time().hour <= 11:
                        return AM_MERIDIEM
                    else:
                        return PM_MERIDIEM
                return None

            # Same day, hours and mins replaced
            meridiem = check(hour_value=hours)
            # Same day, hours and mins replaced but 12 hours shifted from above value
            if meridiem is None:
                meridiem = check(hour_value=(hours + 12) % 24)
            return meridiem
