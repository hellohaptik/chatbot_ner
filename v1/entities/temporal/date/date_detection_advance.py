import re
import pytz
from lib.nlp.regex import Regex
from v1.entities.temporal.date.date_detection import DateDetector


class DateAdvanceDetector(object):
    """
    Detects dates subject to conditions like "departure date" and "return date". These dates are returned in a
    dictionary with keys 'date_departure' and 'date_return'. This class uses DateDetector to detect the date values.

    This class can be used to detect dates specific to scenarios involving a departure and arrival dates for example in
    travel related text

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected date entities would be replaced with on calling detect_entity()
        tagged_text: string with date entities replaced with tag defined by entity name
        processed_text: string with detected date entities removed
        date: list of date entities detected
        original_date_text: list to store substrings of the text detected as date entities
        tag: entity_name prepended and appended with '__'
        date_detector_object: DateDetector object used to detect dates in the given text
        bot_message: boolean, set as the outgoing bot text/message
    """

    def __init__(self, entity_name, timezone=pytz.timezone('UTC')):
        """
        Initializes the DateAdvanceDetector object with given entity_name and pytz timezone object

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
        self.regx_to_process = Regex([(r'[\/]', r'')])
        self.regx_to_process_text = Regex([(r'[\,]', r'')])
        self.entity_name = entity_name
        self.tag = '__' + entity_name + '__'
        self.date_detector_object = DateDetector(entity_name=self.entity_name, timezone=timezone)
        self.bot_message = None

    def detect_entity(self, text):
        """
        Detects all date strings in text and returns two lists of detected date entities and their corresponding
        original substrings in text respectively.

        Args:
            text: string to extract date entities from

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'date_return'
            and 'date_departure' keys and dictionaries returned form DateDetector as their values,
            for each detected date, and second list containing corresponding original substrings in text

        Examples:
            date_adv_detector = DateAdvanceDetector("date_advance")
            text = 'find me a flight departing on 20/2/17 and one returning on 21/2/17'
            date_adv_detector.detect_entity(text)

                Output:
                    ([
                        {
                            'date_departure': {'dd': 20, 'mm': 2, 'type': 'date', 'yy': 2017},
                            'date_return': None
                        },
                        {
                            'date_departure': None,
                            'date_return': {'dd': 21, 'mm': 2, 'type': 'date', 'yy': 2017}
                        }
                    ],
                    ['departing on 20/2/17', 'returning on 21/2/17'])

            dd.tagged_text

                Output:
                    ' find me a flight __date_adv__ and one __date_adv__ '


            text = 'I am not available from 3rd April, 2017 to 9/05/17'
            date_adv_detector.detect_entity(text)

                Output:
                    ([
                        {
                            'date_departure': {'dd': 3, 'mm': 4, 'type': 'date', 'yy': 2017},
                            'date_return': {'dd': 9, 'mm': 5, 'type': 'date', 'yy': 2017}
                        }
                    ],
                    ['3rd april 2017', '9/05/17'])

            dd.tagged_text

                Output:
                    ' find me a flight __date_adv__ and one __date_adv__ '


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
        Detects "departure" and "return" from the object's text attribute

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'date_return'
            and 'date_departure' keys and dictionaries returned form DateDetector as their values,
            for each detected date, and second list containing corresponding original substrings in text

        """
        # print 'detection for default task'
        date_list = []
        original_list = []

        date_list, original_list = self._detect_departure_return_date(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._detect_departure_date(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._detect_return_date(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._detect_any_date(date_list, original_list)
        self._update_processed_text(original_list)

        return date_list, original_list

    def _detect_departure_return_date(self, date_list=None, original_list=None):
        """
        Finds <any text><space(s)><'-' or 'to' or '2'><space(s)><any text> in the given text.
        It  splits the text into two parts on '-' or 'to' or '2'
        and detects the departure date in the first (left) part and detects return date in the second (right) part

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding original substrings of text which were detected as
                            departure and return type date entities

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'date_return'
            and 'date_departure' keys and dictionaries returned form DateDetector as their values,
            for each detected date, and second list containing corresponding original substrings in text
        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\b((.+)\s*(\-|to|2)\s*(.+))\b', self.processed_text.lower())

        for pattern in patterns:
            date = {
                'date_departure': None,
                'date_return': None
            }
            date_departure = None
            date_return = None
            date_detect = self.date_detector_object.detect_entity(pattern[1])
            if date_detect[0]:
                date_departure = date_detect[0][0]
                original = date_detect[1][0] if date_detect[1] else None
                original_list.append(original)

            date_detect = self.date_detector_object.detect_entity(pattern[3])
            if date_detect[0]:
                date_return = date_detect[0][0]
                original = date_detect[1][0] if date_detect[1] else None
                original_list.append(original)

            if date_departure and date_return:
                date['date_departure'] = date_departure
                date['date_return'] = date_return

                date_list.append(date)
                # original = self.regx_to_process.text_substitute(original)

        return date_list, original_list

    def _detect_departure_date(self, date_list=None, original_list=None):
        """
        Finds departure type dates in the given text by matching few keywords like 'onward date', 'departure date',
        'leaving on', 'starting from', 'departing', 'going on' . It detects dates in the part of text right to these
        keywords.

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding original substrings of text which were detected as
                            departure type date entities

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'date_return'
            and 'date_departure' keys and dictionaries returned form DateDetector as their values,
            for each detected date, and second list containing corresponding original substrings in text
        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        regex_string = r'\b((onward date\:|onward date -|on|departure date|leaving on|starting from|' + \
                       r'departing on|departing|going on|for|departs on)\s+(.+))\b'
        patterns = re.findall(regex_string, self.processed_text.lower())

        for pattern in patterns:
            date_departure = None
            date = {
                'date_departure': None,
                'date_return': None
            }

            date_detect = self.date_detector_object.detect_entity(pattern[2])
            if date_detect[0]:
                date_departure = date_detect[0][0]

            if date_departure:
                if date_detect[1] and date_detect[1][0] in pattern[0]:
                    end_idx = pattern[0].find(date_detect[1][0]) + len(date_detect[1][0])
                    original = pattern[0][:end_idx]
                else:
                    original = date_detect[1][0] if date_detect[1] else None
                date['date_departure'] = date_departure

                date_list.append(date)
                # original = self.regx_to_process.text_substitute(original)
                original_list.append(original)

        return date_list, original_list

    def _detect_return_date(self, date_list=None, original_list=None):
        """
        Finds return type dates in the given text by matching few keywords like 'coming back', 'return date',
        'leaving on', 'returning on', 'returning at', 'arriving', 'arrive' . It detects dates in the part of text right
        to these keywords.

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding original substrings of text which were detected as
                            return type date entities

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'date_return'
            and 'date_departure' keys and dictionaries returned form DateDetector as their values,
            for each detected date, and second list containing corresponding original substrings in text
        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        regex_string = r'\b((coming back|back|return date\:?|return date -|returning on|' + \
                       r'arriving|arrive|return|returning|returns on|at)\s+(.+))\b'
        patterns = re.findall(regex_string, self.processed_text.lower())

        for pattern in patterns:
            date_return = None
            original = None
            date = {
                'date_departure': None,
                'date_return': None
            }

            date_detect = self.date_detector_object.detect_entity(pattern[2])
            if date_detect[0]:
                date_return = date_detect[0][0]

            if date_return:
                if date_detect[1] and date_detect[1][0] in pattern[0]:
                    end_idx = pattern[0].find(date_detect[1][0]) + len(date_detect[1][0])
                    original = pattern[0][:end_idx]
                else:
                    original = date_detect[1][0] if date_detect[1] else None
                date['date_return'] = date_return

                date_list.append(date)
                original_list.append(original)

        return date_list, original_list

    def _detect_any_date(self, date_list=None, original_list=None):
        """
        Finds departure and return type dates in the given text. It detects 'departure' and 'return' and their synonyms
        and tags all the detected dates in the text accordingly. If both type synonyms are found, and more than one
        dates are detected, first date is marked as departure type and last as return type. If only one date is found,
        it is marked as departure if 'departure' or both type synonyms are found and marked as 'return' type if 'return'
        type synonyms were found in the given text


        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding original substrings of text which were detected as
                            return type date entities

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'date_return'
            and 'date_departure' keys and dictionaries returned form DateDetector as their values,
            for each detected date, and second list containing corresponding original substrings in text
        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        departure_date_flag = False
        return_date_flag = False
        if self.bot_message:
            departure_regex_string = r'traveling on|going on|starting on|departure date|date of travel|' + \
                                     r'check in date|check-in date|date of check-in|date of departure\.'
            arrival_regex_string = r'traveling back|coming back|returning back|returning on|return date' + \
                                   r'|arrival date|check out date|check-out date|date of check-out|check out'
            departure_regexp = re.compile(departure_regex_string)
            arrival_regexp = re.compile(arrival_regex_string)
            if departure_regexp.search(self.bot_message) is not None:
                departure_date_flag = True
            elif arrival_regexp.search(self.bot_message) is not None:
                return_date_flag = True

        patterns = re.findall(r'\s((.+))\.?\b', self.processed_text.lower())

        for pattern in patterns:
            pattern = list(pattern)
            date = {
                'date_departure': None,
                'date_return': None
            }
            date_detect = self.date_detector_object.detect_entity(pattern[1])
            if date_detect[0]:
                original = date_detect[1][0]
                if len(date_detect[0]) > 1:
                    sort_date_detect = self._sort_date_list(date_list=date_detect[0], original_list=date_detect[1])
                    date['date_departure'] = sort_date_detect[0][0]
                    date['date_return'] = sort_date_detect[0][-1]
                else:
                    if departure_date_flag and not return_date_flag:
                        date['date_departure'] = date_detect[0][0]
                        date['date_return'] = None
                    elif not departure_date_flag and return_date_flag:
                        date['date_departure'] = None
                        date['date_return'] = date_detect[0][0]
                    else:
                        date['date_departure'] = date_detect[0][0]
                        date['date_return'] = None

                date_list.append(date)
                # original = self.regx_to_process.text_substitute(original)
                original_list.append(original)

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
            if detected_text:
                self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
                self.processed_text = self.processed_text.replace(detected_text, '')

    def set_bot_message(self, bot_message):
        """
        Sets the object's bot_message attribute

        Args:
            bot_message: string
        """
        self.bot_message = bot_message

    def _sort_date_list(self, date_list, original_list):
        """
        Sorts the date_list and original_list according to date value in chronological order

        Args:
            date_list: List of dictionaries of date values for detected dates in the text
            original_list: List of substrings of the given text to DateAdvanceDetector that correspond to the
                            detected dates in the date_list

        Returns:
            Tuple containing two lists, first containing dictionaries of detected dates sorted in chronological order
            and second list containing their corresponding substrings of text

        Example:


        """
        sorted_original_list = []
        if len(date_list) > 1:
            dates_zip = zip(date_list, original_list)
            sorted_dates_zip = sorted(dates_zip, key=lambda d: d[0].values())
            sorted_date_list, sorted_original_list = map(list, zip(*sorted_dates_zip))
        else:
            sorted_date_list = date_list
            sorted_original_list = original_list
        return sorted_date_list, sorted_original_list
