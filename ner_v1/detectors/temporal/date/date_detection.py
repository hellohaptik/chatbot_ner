import re
import copy
import datetime
import pytz

from chatbot_ner.config import ner_logger
from lib.nlp.regex import Regex
from models.models import Models
import models.constant as model_constant
from ner_v1.constant import FROM_MESSAGE, FROM_MODEL_VERIFIED, FROM_MODEL_NOT_VERIFIED
import ner_v1.detectors.constant as detector_constant
from ner_v1.detectors.constant import TYPE_EXACT, TYPE_EVERYDAY, TYPE_TODAY, \
    TYPE_TOMORROW, TYPE_YESTERDAY, TYPE_DAY_AFTER, TYPE_DAY_BEFORE, TYPE_NEXT_DAY, TYPE_THIS_DAY, \
    TYPE_POSSIBLE_DAY, TYPE_REPEAT_DAY, WEEKDAYS, WEEKENDS, REPEAT_WEEKDAYS, REPEAT_WEEKENDS, MONTH_DICT, DAY_DICT, \
    TYPE_N_DAYS_AFTER


class DateAdvanceDetector(object):
    """
    DateAdvanceDetector detects dates from the text. It Detects date with the properties like "from", "to","start_range"
    ,"end_range"and "normal". These dates are returned in a dictionary form that contains relevant text, 
    its actual value and its attribute in boolean field i.e. "from", "to", "start_range", "end_range" and "normal".
    This class uses DateDetector to detect the entity values. It also has model integrated to it that can be used to
    extract relevant dates from the text

    Attributes:
        text: string to extract entities from
        tagged_text: string with date entities replaced with tag defined by entity name
        processed_text: string with detected date entities removed
        date: list of date entities detected
        original_date_text: list to store substrings of the date detected as date entities
        regex_to_process_text: Replaces ',' with empty strings ''
        entity_name: string by which the detected date entities would be replaced with on calling detect_entity()
        tag: entity_name prepended and appended with '__'
        date_detector_object: DateDetector object used to detect dates in the given text
        bot_message: boolean, set as the outgoing bot text/message
    """

    def __init__(self, entity_name, timezone=pytz.timezone('UTC')):
        """
        Initializes the DateDetector object with given entity_name and pytz timezone object

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
        self.regex_to_process_text = Regex([(r'[\,]', r'')])
        self.entity_name = entity_name
        self.tag = '__' + entity_name + '__'
        self.date_detector_object = DateDetector(entity_name=entity_name, timezone=timezone)
        self.bot_message = None

    def detect_entity(self, text, run_model=False):
        """
        Detects all date strings in text and returns two lists of detected date entities and their corresponding
        original substrings in text respectively.

        Args:
            text: string to extract date entities from
            run_model: if set true will run the crf model otherwise default value is set to False

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'date_return'
            and 'date_departure' keys and dictionaries returned form DateDetector as their values,
            for each detected date, and second list containing corresponding original substrings in text

        Examples:
            obj = DateDetector('date')
            text = '16th august to 27th august'
            obj.detect_entity(text)

                Output:
                    [{'detection_method': 'message',
                          'from': True,
                          'normal': False,
                          'start_range': False,
                          'end_range': False
                          'text': '16th august',
                          'to': False,
                          'value': {'dd': 16, 'mm': 8, 'type': 'date', 'yy': 2017}},

                    {'detection_method': 'message',
                          'from': False,
                          'normal': False,
                          'start_range': False,
                          'end_range': False
                          'text': '27th august',
                          'to': True,
                          'value': {'dd': 27, 'mm': 8, 'type': 'date', 'yy': 2017}}]

        Additionally this function assigns these lists to self.date and self.original_date_text attributes
        respectively. 
        """
        self.text = ' ' + text.lower() + ' '
        self.text = self.regex_to_process_text.text_substitute(self.text)
        self.processed_text = self.text
        self.tagged_text = self.text
        date_data = []
        if run_model:
            date_data = self._date_model_detection()
        if not run_model or not date_data:
            date_data = self._detect_date()
        return date_data

    def _detect_date(self):
        """
        Detects a date and categorises it into "from", "to", "start_range", "end_range" and "normal" attributes

        Returns:
            It returns the list of dictionary containing the fields like detection_method, from, normal, to,
            text, value, start_range, end_range
        """
        final_date_dict_list = []
        date_dict_list = self._detect_range()
        final_date_dict_list.extend(date_dict_list)
        self._update_processed_text(date_dict_list)
        date_dict_list = self._detect_return_date()
        final_date_dict_list.extend(date_dict_list)
        self._update_processed_text(date_dict_list)
        date_dict_list = self._detect_departure_date()
        final_date_dict_list.extend(date_dict_list)
        self._update_processed_text(date_dict_list)
        date_dict_list = self._detect_any_date()
        final_date_dict_list.extend(date_dict_list)
        self._update_processed_text(date_dict_list)

        return final_date_dict_list

    def _detect_range(self):
        """
        Finds <any text><space(s)><'-' or 'to'><space(s)><any text> in the given text.
        It  splits the text into two parts on '-' or 'to'
        and detects the start range in the first (left) part and detects end range in the second (right) part

        Returns:
            The list of dictionary containing the dictionary for date which is detected as start_range and date
            that got detected as end_range. For start range the key "start_range" will be set to True.
            Whereas for end range the key "end_range" will be set to True.
        """
        date_dict_list = []
        regex_pattern = r'\b((0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?\s?(?:-|to|-|till)\s?' + \
                        r'(0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?[\ \,]\s?(?:of)?\s?([A-Za-z]+))\b'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        if patterns:
            for pattern in patterns:
                date_dict_list.extend(
                    self._date_dict_from_text(text=pattern[0])
                )
            date_dict_list[0][detector_constant.DATE_START_RANGE_PROPERTY] = True
            date_dict_list[-1][detector_constant.DATE_END_RANGE_PROPERTY] = True

        else:
            patterns = re.findall(r'\b(([A-Za-z]+)\s*(\-|to)\s*([A-Za-z]+))\b', self.processed_text.lower())
            for pattern in patterns:
                start_date_list = self._date_dict_from_text(text=pattern[1], start_range_property=True)
                end_date_list = self._date_dict_from_text(text=pattern[3], end_range_property=True)
                if start_date_list and end_date_list:
                    date_dict_list.extend(start_date_list)
                    date_dict_list.extend(end_date_list)
        return date_dict_list

    def _detect_departure_date(self):
        """
        Finds departure type dates in the given text by matching few keywords like 'onward date', 'departure date',
        'leaving on', 'starting from', 'departing', 'going on' . It detects dates in the part of text right to these
        keywords.

        Returns:
            The list of dictionary containing the dictionary for date which is detected as departure date.
            For departure date the key "From" will be set to True.
        """
        date_dict_list = []
        regex_string = r'\b((onward date\:|onward date -|departure date|leaving on|starting from|' + \
                       r'departing on|departing|going on|for|departs on)\s+(.+))\b'
        patterns = re.findall(regex_string, self.processed_text.lower())

        for pattern in patterns:
            date_dict_list.extend(
                self._date_dict_from_text(text=pattern[2], from_property=True)
            )
        return date_dict_list

    def _detect_return_date(self):
        """
        Finds return type dates in the given text by matching few keywords like 'coming back', 'return date',
        'leaving on', 'returning on', 'returning at', 'arriving', 'arrive' . It detects dates in the part of text right
        to these keywords.

        Args:

        Returns:
            The list of dictionary containing the dictionary for date which is detected as return date.
            For departure date the key "to" will be set to True.
        """

        date_dict_list = []
        regex_string = r'\s?((coming back|back|return date\:?|return date -|returning on|' \
                       r'arriving|arrive|return|returning at)\s+(.+))\.?\s?'
        patterns = re.findall(regex_string, self.processed_text.lower())
        for pattern in patterns:
            date_dict_list.extend(
                self._date_dict_from_text(text=pattern[2], to_property=True)
            )
        return date_dict_list

    def _detect_any_date(self):
        """
        Finds departure and return type dates in the given text. It detects 'departure' and 'return' and their synonyms
        and tags all the detected dates in the text accordingly. If both type synonyms are found, and more than one
        dates are detected, first date is marked as departure type and last as return type. If only one date is found,
        it is marked as departure if 'departure' or both type synonyms are found and marked as 'return' type if 'return'
        type synonyms were found in the given text


        Args:

        Returns:
            The list of dictionary containing the dictionary for date which is detected as departure date and date
            that got detected as arrival date or the date that got detected as normal date. For departure date
            the key "from" will be set to True.
            Whereas for arrival date the key "to" will be set to True.
            Otherwise the normal date with the key 'normal' will be set to True
        """
        date_dict_list = []
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
            date_dict_list = self._date_dict_from_text(text=pattern[1])
            if date_dict_list:
                if len(date_dict_list) > 1:
                    for i in xrange(len(date_dict_list)):
                        date_dict_list[i][detector_constant.DATE_NORMAL_PROPERTY] = True
                else:
                    if departure_date_flag:
                        date_dict_list[0][detector_constant.DATE_FROM_PROPERTY] = True
                    elif return_date_flag:
                        date_dict_list[0][detector_constant.DATE_TO_PROPERTY] = True
                    else:
                        date_dict_list[0][detector_constant.DATE_NORMAL_PROPERTY] = True
        return date_dict_list

    def _update_processed_text(self, date_dict_list):
        """
        Replaces detected date with tag generated from entity_name used to initialize the object with

        A final string with all dates replaced will be stored in object's tagged_text attribute
        A string with all dates removed will be stored in object's processed_text attribute

        Args:
            date_dict_list: list of substrings of original text to be replaced with tag created from entity_name
        """
        for date_dict in date_dict_list:
            self.tagged_text = self.tagged_text.replace(date_dict[detector_constant.ORIGINAL_DATE_TEXT], self.tag)
            self.processed_text = self.processed_text.replace(date_dict[detector_constant.ORIGINAL_DATE_TEXT], '')

    def set_bot_message(self, bot_message):
        """
        Sets the object's bot_message attribute

        Args:
            bot_message: is the previous message that is sent by the bot
        """
        self.bot_message = bot_message

    def _date_dict_from_text(self, text, from_property=False, to_property=False, start_range_property=False,
                             end_range_property=False, normal_property=False, detection_method=FROM_MESSAGE):
        """
        Takes the text and the property values and creates a list of dictionaries based on number of dates detected

        Attributes:
            text: Text on which TextDetection needs to run on
            from_property: True if the text is belonging to "from" property". for example, From monday
            to_property: True if the text is belonging to "to" property". for example, To monday
            start_range_property: True if the text is belonging to "start_range" property". for example, starting from monday
            end_range_property: True if the text is belonging to "end_range" property". for example, to monday
            normal_property: True if the text is belonging to "normal" property". for example, every monday
            detection_method: method through which it got detected whether its through message or model

        Returns:

            It returns the list of dictionary containing the fields like detection_method, from, normal, to,
            text, value, range

            Examples:

                Output:
                    [{'detection_method': 'message',
                          'from': True,
                          'normal': False,
                          'start_range': False,
                          'end_range': False
                          'text': '16th august',
                          'to': False,
                          'value': {'dd': 16, 'mm': 8, 'type': 'date', 'yy': 2017}},

                    {'detection_method': 'message',
                          'from': False,
                          'normal': False,
                          'start_range': False,
                          'end_range': False
                          'text': '27th august',
                          'to': True,
                          'value': {'dd': 27, 'mm': 8, 'type': 'date', 'yy': 2017}}]

        """
        date_dict_list = []
        date_list, original_list = self._date_value(text=text)
        index = 0
        for date in date_list:
            date_dict_list.append(
                {
                    detector_constant.DATE_VALUE: date,
                    detector_constant.ORIGINAL_DATE_TEXT: original_list[index],
                    detector_constant.DATE_FROM_PROPERTY: from_property,
                    detector_constant.DATE_TO_PROPERTY: to_property,
                    detector_constant.DATE_START_RANGE_PROPERTY: start_range_property,
                    detector_constant.DATE_END_RANGE_PROPERTY: end_range_property,
                    detector_constant.DATE_NORMAL_PROPERTY: normal_property,
                    detector_constant.DATE_DETECTION_METHOD: detection_method
                }
            )
            index += 1
        return date_dict_list

    def _date_value(self, text):
        """
        Detects date from text by running DateDetector class.

        Args:
            text: date to process

        Returns:
            A tuple of two lists with first list containing the detected dates and second list containing their
            corresponding substrings in the given date. For example:

            For example:

                (['friday'], ['friday'])
        """
        date_list, original_list = self.date_detector_object.detect_entity(text)
        return date_list, original_list

    def convert_date_dict_in_tuple(self, entity_dict_list):
        """
        This function takes the input as a list of dictionary and converts it into tuple which is
        for now the standard format  of individual detector function

        Returns:
            Returns the tuple containing list of entity_values, original_text and detection method

            For example:

                (['friday'], ['friday'], ['message'])

        """
        entity_list, original_list, detection_list = [], [], []
        for entity_dict in entity_dict_list:
            entity_list.append(
                {
                    detector_constant.DATE_VALUE: entity_dict[detector_constant.DATE_VALUE],
                    detector_constant.DATE_FROM_PROPERTY: entity_dict[detector_constant.DATE_FROM_PROPERTY],
                    detector_constant.DATE_TO_PROPERTY: entity_dict[detector_constant.DATE_TO_PROPERTY],
                    detector_constant.DATE_START_RANGE_PROPERTY: entity_dict[
                        detector_constant.DATE_START_RANGE_PROPERTY],
                    detector_constant.DATE_END_RANGE_PROPERTY: entity_dict[detector_constant.DATE_END_RANGE_PROPERTY],
                    detector_constant.DATE_NORMAL_PROPERTY: entity_dict[detector_constant.DATE_NORMAL_PROPERTY],

                }
            )
            original_list.append(entity_dict[detector_constant.ORIGINAL_DATE_TEXT])
            detection_list.append(entity_dict[detector_constant.DATE_DETECTION_METHOD])
        return entity_list, original_list, detection_list

    def _date_model_detection(self):
        """
        This function calls run_model functionality from class Models() and verifies the values returned by it through
        datastore.
        If the dates provided by the model are present in the datastore, it sets the value to FROM_MODEL_VERIFIED
        else FROM_MODEL_NOT_VERFIED is set.

        For Example:
            Note:  before calling this method you need to call set_bot_message() to set a bot message.

            self.bot_message = 'Please help me with your departure date?'
            self.text = '26th november'

            Output:
               [
                 {

                  'detection_method': 'message',
                  'end_range': False,
                  'from': False,
                  'normal': True,
                  'start_range': False,
                  'text': '26th november',
                  'to': False,
                  'value': {'dd': 26, 'mm': 11, 'type': 'date', 'yy': 2017}
                  'detection_method': model_verified

                  }
               ]



        For Example:

            self.bot_message = 'Please help me with your departure date?'
            self.text = 'monday'

            Output:
                 [
                    {

                      'detection_method': 'message',
                      'end_range': False,
                      'from': False,
                      'normal': True,
                      'start_range': False,
                      'text': 'monday',
                      'to': False,
                      'value': {'dd': 21, 'mm': 8, 'type': 'day_within_one_week', 'yy': 2017}
                      'detection_method': model_not_verified

                    }
                 ]

        """
        date_dict_list = []
        model_object = Models()
        model_output = model_object.run_model(entity_type=model_constant.DATE_ENTITY_TYPE,
                                              bot_message=self.bot_message, user_message=self.text)
        for output in model_output:
            entity_value_list, original_text_list = self._date_value(text=output[model_constant.MODEL_DATE_VALUE])
            if entity_value_list:
                date_value = entity_value_list[0]
                detection_method = FROM_MODEL_VERIFIED
            else:
                date_value = output[model_constant.MODEL_DATE_VALUE]
                detection_method = FROM_MODEL_NOT_VERIFIED

            date_dict_list.append(
                {
                    detector_constant.DATE_VALUE: date_value,
                    detector_constant.ORIGINAL_DATE_TEXT: output[model_constant.MODEL_DATE_VALUE],
                    detector_constant.DATE_FROM_PROPERTY: output[model_constant.MODEL_DATE_FROM],
                    detector_constant.DATE_TO_PROPERTY: output[model_constant.MODEL_DATE_TO],
                    detector_constant.DATE_START_RANGE_PROPERTY: output[model_constant.MODEL_START_DATE_RANGE],
                    detector_constant.DATE_END_RANGE_PROPERTY: output[model_constant.MODEL_END_DATE_RANGE],
                    detector_constant.DATE_NORMAL_PROPERTY: output[model_constant.MODEL_DATE_NORMAL],
                    detector_constant.DATE_DETECTION_METHOD: detection_method
                }

            )
        return date_dict_list


class DateDetector(object):
    """
    Detects date in various formats from given text and tags them.

    Detects all date entities in given text and replaces them by entity_name.
    Additionally detect_entity() method returns detected date values in dictionary containing values for day (dd),
    month (mm), year (yy), type (exact, possible, everyday, weekend, range etc.)

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected date entities would be replaced with on calling detect_entity()
        tagged_text: string with date entities replaced with tag defined by entity name
        processed_text: string with detected date entities removed
        date: list of date entities detected
        original_date_text: list to store substrings of the text detected as date entities
        tag: entity_name prepended and appended with '__'
        timezone: Optional, pytz.timezone object used for getting current time, default is pytz.timezone('UTC')
        regx_to_process: regex to remove forward slash while updating list that stores  text
        regx_to_process_text: regex to remove forward slash while before detecting entities
        date_object: datetime object holding timestamp while DateDetector instantiation
        month_dictionary: dictonary mapping month indexes to month spellings and 
                            fuzzy variants(spell errors, abbreviations)
        day_dictionary: dictonary mapping day indexes to day of week spellings and 
                            fuzzy variants(spell errors, abbreviations)

        SUPPORTED_FORMAT                                            METHOD_NAME
        ------------------------------------------------------------------------------------------------------------
        1. day/month/year                                           _gregorian_day_month_year_format
        2. year/month/day                                           _gregorian_year_month_day_format
        3. day/month/year (Month in abbreviation or full)           _gregorian_advanced_day_month_year_format
        4. Xth month year (Month in abbreviation or full)           _gregorian_day_with_ordinals_month_year_format
        5. year month Xth (Month in abbreviation or full)           _gregorian_advanced_year_month_day_format
        6. year Xth month (Month in abbreviation or full)           _gregorian_year_day_month_format
        7. month Xth year (Month in abbreviation or full)           _gregorian_month_day_year_format
        8. month Xth      (Month in abbreviation or full)           _gregorian_month_day_format
        9. Xth month      (Month in abbreviation or full)           _gregorian_day_month_format
        10."today" variants                                         _todays_date
        11."tomorrow" variants                                      _tomorrows_date
        12."yesterday" variants                                     _yesterdays_date
        13."_day_after_tomorrow" variants                           _day_after_tomorrow
        14."_day_before_yesterday" variants                         _day_before_yesterday
        15."next <day of week>" variants                            _day_in_next_week
        16."this <day of week>" variants                            _day_within_one_week
        17.probable date from only Xth                              _date_identification_given_day
        18.probable date from only Xth this month                   _date_identification_given_day_and_current_month
        19.probable date from only Xth next month                   _date_identification_given_day_and_next_month
        20."everyday" variants                                      _date_identification_everyday
        21."everyday except weekends" variants                      _date_identification_everyday_except_weekends
        22."everyday except weekdays" variants                       _date_identification_everyday_except_weekdays
        23."every monday" variants                                  _weeks_identification
        24."after n days" variants                                  _date_days_after
        25."n days later" variants                                  _date_days_later
        
        Not all separator are listed above. See respective methods for detail on structures of these formats

    Note:
        text and tagged_text will have a extra space prepended and appended after calling detect_entity(text)
    """

    def __init__(self, entity_name, timezone=pytz.timezone('UTC')):
        """Initializes a DateDetector object with given entity_name and pytz timezone object

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
        self.month_dictionary = {}
        self.day_dictionary = {}
        self.entity_name = entity_name
        self.regx_to_process = Regex([(r'[\/]', r'')])
        self.regx_to_process_text = Regex([(r'[\,]', r'')])
        self.tag = '__' + entity_name + '__'
        self.timezone = timezone
        try:
                self.date_object = datetime.datetime.now(pytz.timezone(timezone))
        except Exception, e:
                ner_logger.debug('Timezone error: %s ' % e)
                self.date_object = datetime.datetime.now(pytz.timezone('UTC'))
                ner_logger.debug('Default timezone passed as "UTC"')
        self.month_dictionary = MONTH_DICT
        self.day_dictionary = DAY_DICT

    def detect_entity(self, text):
        """
        Detects all date strings in text and returns two lists of detected date entities and their corresponding
        original substrings in text respectively.

        Args:
            text: string to extract date entities from

        Returns:
            Tuple containing two lists, first containing dictionaries, containing
            date values as 'dd', 'mm', 'type', 'yy' for each detected date, and second list containing corresponding
            substrings in given for entity detection

            Examples:
                date_detector = DateDetector("date")
                date_detector.detect_entity('Remind me everyday')

                date_detector.tagged_text


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
        Detects exact date for complete date information - day, month, year are available in text
        and possible dates for if there are missing parts of date - day, month, year assuming sensible defaults. Also
        detects "today", "tomorrow", "yesterday", "everyday", "day after tomorrow", "day before yesterday",
        "only weekdays", "only weekends", "day in next week", "day A to day B", "month A to month B" ranges
        and their variants/synonyms

        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.
        """
        date_list = []
        original_list = []
        date_list, original_list = self.get_exact_date(date_list, original_list)
        date_list, original_list = self.get_possible_date(date_list, original_list)
        return date_list, original_list

    def get_exact_date(self, date_list, original_list):
        """
        Detects exact date if complete date information - day, month, year are available in text.
        Also detects "today", "tomorrow", "yesterday", "day after tomorrow", "day before yesterday",
        "day in next week" and their variants/ synonyms and returns their dates as these can have exactly one date
        they refer to. Type of dates returned by this method include TYPE_NORMAL, TYPE_TODAY, TYPE_TOMORROW,
        TYPE_DAY_AFTER, TYPE_DAY_BEFORE, TYPE_YESTERDAY, TYPE_NEXT_DAY

        Args:
            date_list: Optional, list to store dictionaries of detected date entities
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities

        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        date_list, original_list = self._gregorian_day_month_year_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_year_month_day_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_advanced_day_month_year_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._day_month_format_for_arrival_departure(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_day_with_ordinals_month_year_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_advanced_year_month_day_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_year_day_month_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_month_day_year_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_day_month_format(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._gregorian_month_day_format(date_list, original_list)
        self._update_processed_text(original_list)

        date_list, original_list = self._day_after_tomorrow(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_days_after(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_days_later(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._day_before_yesterday(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._todays_date(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._tomorrows_date(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._yesterdays_date(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._day_in_next_week(date_list, original_list)
        self._update_processed_text(original_list)

        return date_list, original_list

    def get_possible_date(self, date_list=None, original_list=None):
        """
        Detects possible dates for if there are missing parts of date - day, month, year assuming sensible defaults.
        Also detects "everyday","only weekdays", "only weekends","A to B" type ranges in days of week or months,
        and their variants/ synonyms and returns probable dates by using current year, month, week defaults for parts of
        dates that are missing or that include relative ranges. Type of dates returned by this method include
        TYPE_POSSIBLE_DAY, TYPE_REPEAT_DAY, TYPE_THIS_DAY, REPEAT_WEEKDAYS, REPEAT_WEEKENDS, START_RANGE, END_RANGE,
        REPEAT_START_RANGE, REPEAT_END_RANGE, DATE_START_RANGE, DATE_END_RANGE, WEEKDAYS, WEEKENDS .

        Args:
            date_list: Optional, list to store dictionaries of detected date entities
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
        date_list, original_list = self._date_identification_given_day_and_current_month(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_identification_given_day_and_next_month(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_identification_given_day(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_identification_everyday(date_list, original_list, n_days=15)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_identification_everyday_except_weekends(date_list, original_list,
                                                                                      n_days=15)
        self._update_processed_text(original_list)
        date_list, original_list = self._date_identification_everyday_except_weekdays(date_list, original_list,
                                                                                      n_days=50)
        self._update_processed_text(original_list)
        date_list, original_list = self._day_within_one_week(date_list, original_list)
        self._update_processed_text(original_list)
        date_list, original_list = self._weeks_identification(date_list, original_list)
        self._update_processed_text(original_list)

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
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')

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
        regex_pattern = r'\b((0?[1-9]|[12][0-9]|3[01])\s?[/\-\.]\s?(0?[1-9]|1[0-2])\s?[/\-\.]' \
                        r'\s?((?:20|19)?[0-9]{2}))(\s|$)'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[1]
            mm = pattern[2]
            yy = pattern[3]

            if len(yy) == 2:
                yy = '20' + yy

            date = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_EXACT
            }
            date_list.append(date)
            # original = self.regx_to_process.text_substitute(original)
            original_list.append(original)
        return date_list, original_list

    def _gregorian_year_month_day_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <year><separator><month><separator><day>
        where each part is in of one of the formats given against them
            day: d, dd
            month: m, mm
            year: yy, yyyy
            separator: "/", "-", "."

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "31/1/31", "97/2/21", "2017/12/01"

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
        regex_pattern = r'\b(((?:20|19)[0-9]{2})\s?[/\-\.]\s?(0?[1-9]|1' \
                        r'[0-2])\s?[/\-\.]\s?(0?[1-9]|[12][0-9]|3[01]))(\s|$)'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[3]
            mm = pattern[2]
            yy = pattern[1]

            date = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_EXACT
            }
            date_list.append(date)
            # original = self.regx_to_process.text_substitute(original)
            original_list.append(original)
        return date_list, original_list

    def _gregorian_advanced_day_month_year_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <day><separator><month><separator><year>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            year: yy, yyyy
            separator: "/", "-", ".", space

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "21 Nov 99", "02 january 1972", "9 November 2014", "09-Nov-2014", "09/Nov/2014"

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
        regex_pattern = r'\b((0?[1-9]|[12][0-9]|3[01])\s?[/ -\.]\s?([A-Za-z]+)\s?[/ -\.]\s?((?:20|19)?[0-9]{2}))(\s|$)'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0].strip()
            dd = pattern[1]
            probable_mm = pattern[2]
            yy = pattern[3]

            if len(yy) == 2:
                yy = '20' + yy

            mm = self.__get_month_index(probable_mm)
            if mm:
                date = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT

                }
                date_list.append(date)
                # original = self.regx_to_process.text_substitute(original)
                original_list.append(original)
        return date_list, original_list

    def _gregorian_day_with_ordinals_month_year_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <day><Optional ordinal inidicator><Optional "of"><separator><month><separator><year>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            year: yy, yyyy
            ordinal indicator: "st", "nd", "rd", "th", space
            separator: ",", space

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "21st Nov 99", "02nd of,january, 1972", "9 th November 2014", "09th Nov, 2014", "09 Nov 2014"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        regex_pattern = r'\b((0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?\s?(?:of)?[\s\,]\s?' \
                        r'([A-Za-z]+)[\s\,]\s?((?:20|19)?[0-9]{2}))(\s|$)'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0].strip()
            dd = pattern[1]
            probable_mm = pattern[2]
            yy = pattern[3]

            if len(yy) == 2:
                yy = '20' + yy

            mm = self.__get_month_index(probable_mm)
            if mm:
                date = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_list.append(date)
                original_list.append(original)
        return date_list, original_list

    def _gregorian_advanced_year_month_day_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <year><separator><month><separator><day>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            year: yy, yyyy
            separator: "/", "-", space

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "2099 Nov 21", "1972 january 2", "2014 November 6", "2014-Nov-09", "2015/Nov/94"

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
        patterns = re.findall(
            r'\b(((?:20|19)[0-9]{2})\s?[/ \-]\s?([A-Za-z]+)\s?[/ \-]\s?(0?[1-9]|[12][0-9]|3[01]))(\s|$)',
            self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[3]
            probable_mm = pattern[2]
            yy = pattern[1]
            mm = self.__get_month_index(probable_mm)
            if mm:
                date = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_list.append(date)
                # original = self.regx_to_process.text_substitute(original)
                original_list.append(original)
        return date_list, original_list

    def _gregorian_year_day_month_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <year><separator><day><Optional ordinal indicator><separator><month>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            year: yy, yyyy
            separator: ",", space
            ordinal indicator: "st", "nd", "rd", "th", space

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "2099 21st Nov", "1972, 2 january", "14,November,6"

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
        regex_pattern = r'\b(((?:20|19)[0-9]{2})[\ \,]\s?(0?[1-9]|[12][0-9]|3[01])\s?(?:' \
                        r'nd|st|rd|th)?[\ \,]([A-Za-z]+))\b'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[2]
            probable_mm = pattern[3]
            yy = pattern[1]
            mm = self.__get_month_index(probable_mm)
            if mm:
                date = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_list.append(date)
                original_list.append(original)
        return date_list, original_list

    def _gregorian_month_day_year_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <month><separator><day><Optional ordinal indicator><separator><year>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            year: yy, yyyy
            separator: ",", space
            ordinal indicator: "st", "nd", "rd", "th", space

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "Nov 21st 2099", "january, 2 1972", "12,November,13"

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
        regex_pattern = r'\b(([A-Za-z]+)[\ \,]\s?(0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?[\ \
        ,]\s?((?:20|19)?[0-9]{2}))(\s|$)'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[2]
            probable_mm = pattern[1]
            yy = pattern[3]
            mm = self.__get_month_index(probable_mm)

            if len(yy) == 2:
                yy = '20' + yy
            if mm:
                date = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_list.append(date)
                original_list.append(original)
        return date_list, original_list

    def _gregorian_month_day_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <month><separator><day><Optional ordinal indicator>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            separator: ",", space
            ordinal indicator: "st", "nd", "rd", "th", space

        Two character years are assumed to be belong to 21st century - 20xx.
        Only years between 1900 to 2099 are detected

        Few valid examples:
            "Feb 21st", "january, 2", "November 12"

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
        regex_pattern = r'\b(([A-Za-z]+)[\ \,]\s?(0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?)\b'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[2]
            probable_mm = pattern[1]
            mm = self.__get_month_index(probable_mm)
            if dd:
                dd = int(dd)
            if mm:
                mm = int(mm)
            if self.date_object.month > mm:
                yy = self.date_object.year + 1
            elif self.date_object.day > dd and self.date_object.month == mm:
                yy = self.date_object.year + 1
            else:
                yy = self.date_object.year
            if mm:
                date_dict = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_list.append(date_dict)
                original_list.append(original)
        return date_list, original_list

    def _gregorian_day_month_format(self, date_list=None, original_list=None):
        """
        Detects date in the following format

        format: <day><Optional ordinal indicator><separator><month>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            separator: ",", space
            ordinal indicator: "st", "nd", "rd", "th", space

        Optional "of" is allowed after ordinal indicator, example "dd th of this current month"

        Few valid examples:
            "21st Nov", "2, of january ", "12th of November"

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
        regex_pattern = r'\b((0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?[\ \,]\s?(?:of)?\s?([A-Za-z]+))\b'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd = pattern[1]
            probable_mm = pattern[2]
            mm = self.__get_month_index(probable_mm)
            if dd:
                dd = int(dd)
            if mm:
                mm = int(mm)
            if self.date_object.month > mm:
                yy = self.date_object.year + 1
            elif self.date_object.day > dd and self.date_object.month == mm:
                yy = self.date_object.year + 1
            else:
                yy = self.date_object.year
            if mm:
                date_dict = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_list.append(date_dict)
                original_list.append(original)
        return date_list, original_list

    def _todays_date(self, date_list=None, original_list=None):
        """
        Detects "today" and its variants and returns the date today

        Matches "today", "2dy", "2day", "tody", "aaj", "aj", "tonight"
        
        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\b(today|2dy|2day|tody|aaj|aj|tonight)\b',
                              self.processed_text.lower())
        for pattern in patterns:
            original = pattern
            dd = self.date_object.day
            mm = self.date_object.month
            yy = self.date_object.year
            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_TODAY

            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _tomorrows_date(self, date_list=None, original_list=None):
        """
        Detects "tommorow" and its variants and returns the date value for tommorow

        Matches "tomorrow", "2morow", "2mrw", "2mrow", "next day", "tommorrow", "tommorow", "tomorow", "tommorow"
        
        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        regex_pattern = r'\b((tomorrow|2morow|2mrw|2mrow|next day|tommorr?ow|tomm?orow|tmrw|' \
                        r'tmrrw|tomorw|tomro|tomorow|afte?r\s+1\s+da?y))\b'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            tomorrow = self.date_object + datetime.timedelta(days=1)
            dd = tomorrow.day
            mm = tomorrow.month
            yy = tomorrow.year
            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_TOMORROW
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _yesterdays_date(self, date_list=None, original_list=None):
        """
        Detects "yesterday" and "previous day" and its variants and returns the date value for yesterday

        Matches "yesterday", "sterday", "yesterdy", "yestrdy", "yestrday", "previous day", "prev day", "prevday"

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
        patterns = re.findall(r'\b(yesterday|sterday|yesterdy|yestrdy|yestrday|previous day|prev day|prevday)\b',
                              self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            yesterday = self.date_object - datetime.timedelta(days=1)
            dd = yesterday.day
            mm = yesterday.month
            yy = yesterday.year
            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_YESTERDAY
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _day_after_tomorrow(self, date_list=None, original_list=None):
        """
        Detects "day after tomorrow" and its variants and returns the date on day after tomorrow

        Matches "day" or "dy" followed by "after" or "aftr" followed by one of 
        "tomorrow", "2morow", "2mrw", "2mrow", "kal", "2mrrw"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(r'\b((da?y afte?r)\s+(tomorrow|2morow|2mrw|2mrow|kal|2mrrw))\b',
                              self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            day_after = self.date_object + datetime.timedelta(days=2)
            dd = day_after.day
            mm = day_after.month
            yy = day_after.year
            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_DAY_AFTER
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _date_days_after(self, date_list=None, original_list=None):
        """
        Detects "date after n number of days" and returns the date after n days
    
        Matches "after" followed by the number of days provided
        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                               date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and type followed by the 
            second list containing their corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(
            r'\b(afte?r\s+(\d+)\s+(da?y|da?ys))\b',
            self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            days = int(pattern[1])
            day_after = self.date_object + datetime.timedelta(days=days)
            dd = day_after.day
            mm = day_after.month
            yy = day_after.year
            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_N_DAYS_AFTER
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _date_days_later(self, date_list=None, original_list=None):
        """
        Detects "date n days later" and returns the date for n days later
    
        Matches "digit" followed by "days" and iterations of "later"
        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                               date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and type followed by the 
            second list containing their corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        patterns = re.findall(
            r'\b((\d+)\s+(da?y|da?ys)\s?(later|ltr|latr|lter)s?)\b',
            self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            days = int(pattern[1])
            day_after = self.date_object + datetime.timedelta(days=days)
            dd = day_after.day
            mm = day_after.month
            yy = day_after.year
            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_N_DAYS_AFTER
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _day_before_yesterday(self, date_list=None, original_list=None):
        """
        Detects "day before yesterday" and its variants and returns the date on day after tomorrow

        Matches "day" or "dy" followed by "before" or "befre" followed by one of 
        "yesterday", "sterday", "yesterdy", "yestrdy", "yestrday"

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
        patterns = re.findall(r'\b((da?y befo?re)\s+(yesterday|sterday|yesterdy|yestrdy|yestrday))\b',
                              self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            day_before = self.date_object - datetime.timedelta(days=2)
            dd = day_before.day
            mm = day_before.month
            yy = day_before.year
            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_DAY_BEFORE

            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _day_in_next_week(self, date_list=None, original_list=None):
        """
        Detects "next <day of the week>" and its variants and returns the date on that day in the next week. Week starts
        with Sunday and ends with Saturday

        Matches "next" or "nxt" followed by day of the week - Sunday/Monday/Tuesday/Wednesday/Thursday/Friday/Saturday
        or their abbreviations. NOTE: Day of the week and their variants are fetched from the data store

        Example:
            If it is 7th February 2017, Tuesday while invoking this function,
            "next Sunday" would return [{'dd': 12, 'mm': 2, 'type': 'day_in_next_week', 'yy': 2017}]
            "next Saturday" would return [{'dd': 18, 'mm': 2, 'type': 'day_in_next_week', 'yy': 2017}]
            and other days would return dates between these dates

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
        patterns = re.findall(r'\b((ne?xt)\s+([A-Za-z]+))\b', self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            probable_day = pattern[2]
            day = self.__get_day_index(probable_day)
            current_day = self.__get_day_index(self.date_object.strftime("%A"))
            if day and current_day:
                date_after_days = int(day) - int(current_day) + 7
                day_to_set = self.date_object + datetime.timedelta(days=date_after_days)
                dd = day_to_set.day
                mm = day_to_set.month
                yy = day_to_set.year
                date_dict = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_NEXT_DAY
                }
                date_list.append(date_dict)
                original_list.append(original)
        return date_list, original_list

    def _day_within_one_week(self, date_list=None, original_list=None):
        """
        Detects "this <day of the week>" and its variants and returns the date on that day within one week from
        current date.

        Matches one of "this", "dis", "coming", "on", "for", "fr" followed by
        day of the week - Sunday/Monday/Tuesday/Wednesday/Thursday/Friday/Saturday or their abbreviations.
        NOTE: Day of the week and their variants are fetched from the data store

        Example:
            If it is 7th February 2017, Tuesday while invoking this function,
            "this Tuesday" would return [{'dd': 7, 'mm': 2, 'type': 'day_within_one_week', 'yy': 2017}]
            "for Monday" would return [{'dd': 13, 'mm': 2, 'type': 'day_within_one_week', 'yy': 2017}]
            and other days would return dates between these dates

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
        patterns = re.findall(r'\b((this|dis|coming|on|for)*[\s\-]*([A-Za-z]+))\b', self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0].strip()
            probable_day = pattern[2]
            day = self.__get_day_index(probable_day)
            current_day = self.__get_day_index(self.date_object.strftime("%A"))
            if day and current_day:
                if int(current_day) <= int(day):
                    date_after_days = int(day) - int(current_day)
                else:
                    date_after_days = int(day) - int(current_day) + 7
                day_to_set = self.date_object + datetime.timedelta(days=date_after_days)
                dd = day_to_set.day
                mm = day_to_set.month
                yy = day_to_set.year
                date_dict = {
                    'dd': int(dd),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_THIS_DAY
                }
                date_list.append(date_dict)
                original_list.append(original)
        return date_list, original_list

    def _date_identification_given_day(self, date_list=None, original_list=None):
        """
        Detects probable date given only day part. The month and year are assumed to be current month and current year
        respectively. Consider checking if the returned detected date is valid.

        format: <day><Optional space><ordinal indicator>
        where each part is in of one of the formats given against them
            day: d, dd
            ordinal indicator: "st", "nd", "rd", "th"

        Example:
            If it is 7th February 2017, Tuesday while invoking this function,
            "2nd" would return [{'dd': 2, 'mm': 2, 'type': 'possible_day', 'yy': 2017}]
            "29th" would return [{'dd': 29, 'mm': 2, 'type': 'possible_day', 'yy': 2017}]
            Please note that 29/2/2017 is not a valid date on calendar but would be returned anyway as a probable date

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
        patterns = re.findall(r'\b((0?[1-9]|[12][0-9]|3[01])\s*(?:nd|st|rd|th))\b', self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]

            dd = pattern[1]
            mm = self.date_object.month
            yy = self.date_object.year

            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_POSSIBLE_DAY
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _date_identification_given_day_and_current_month(self, date_list=None, original_list=None):
        """
        Detects probable date given day part and . The year is assumed to be current year
        Consider checking if the returned detected date is valid.

        Matches <day><Optional ordinal indicator><"this" or "dis"><Optional "current" or "curent"><"mnth" or "month">
        where each part is in of one of the formats given against them
            day: d, dd
            ordinal indicator: "st", "nd", "rd", "th"
        
        Optional "of" is allowed after ordinal indicator, example "dd th of this current month"

        Few valid examples:
            "3rd this month", "2 of this month", "05 of this current month" 

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
        regex_pattern = r'\b((0?[1-9]|[12][0-9]|3[01])\s*(?:nd|st|rd|th)?\s*(?:of)?\s*(?:this|dis)\s*(?:curr?ent)?' + \
                        r'\s*(month|mnth))\b'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]

            dd = pattern[1]
            mm = self.date_object.month
            yy = self.date_object.year

            date_dict = {
                'dd': int(dd),
                'mm': int(mm),
                'yy': int(yy),
                'type': TYPE_POSSIBLE_DAY
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _date_identification_given_day_and_next_month(self, date_list=None, original_list=None):
        """
        Detects probable date given day part and "next month" synonyms. The year is assumed to be current year
        Consider checking if the returned detected date is valid.

        Matches <day><Optional ordinal indicator><"this" or "dis"><"next" variants><"mnth" or "month">
        where each part is in of one of the formats given against them
            day: d, dd
            ordinal indicator: "st", "nd", "rd", "th"
            "next" variants: "next", "nxt", "comming", "coming", "commin", "following", "folowin", "followin",
                             "folowing"
        
        Optional "of" is allowed after ordinal indicator, example "dd th of this next month"

        Few valid examples:
            "3rd of next month", "2 of next month", "05 of next month" 

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities
        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        regex_pattern = r'\b((0?[1-9]|[12][0-9]|3[01])\s*(?:nd|st|rd|th)?\s*(?:of)?\s*' + \
                        r'(?:next|nxt|comm?ing?|foll?owing?|)\s*(mo?nth))\b'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]

            dd = pattern[1]
            previous_mm = self.date_object.month
            yy = self.date_object.year
            mm = int(previous_mm) + 1
            if mm > 12:
                mm = 1

            date_dict = {
                'dd': int(dd),
                'mm': mm,
                'yy': int(yy),
                'type': TYPE_POSSIBLE_DAY
            }
            date_list.append(date_dict)
            original_list.append(original)
        return date_list, original_list

    def _date_identification_everyday(self, date_list=None, original_list=None, n_days=30):
        """
        Detects "everyday" and its variants and returns all the dates of the next n_days from current date.
        Matches "everyday", "daily", "every day", "all day", "all days"

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                           date entities
            n_days: Optional, number of days from current date to return dates for if everyday is detected as a time
                    entity, default value is 30

        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        now = self.date_object
        end = now + datetime.timedelta(days=n_days)
        patterns = re.findall(r'\b\s*((everyday|daily|every\s{0,3}day|all\sday|all\sdays))\s*\b',
                              self.processed_text.lower())
        if patterns:
            pattern = patterns[0]
            original = pattern[0]
            date_dict = {
                'dd': now.day,
                'mm': now.month,
                'yy': now.year,
                'type': TYPE_EVERYDAY
            }

            while now < end:
                date_list.append(copy.deepcopy(date_dict))
                now += datetime.timedelta(days=1)
                date_dict = {
                    'dd': now.day,
                    'mm': now.month,
                    'yy': now.year,
                    'type': TYPE_EVERYDAY
                }
                original_list.append(original)
        return date_list, original_list

    def _date_identification_everyday_except_weekends(self, date_list=None, original_list=None, n_days=30):
        """
        First this method tries to detect "everday except weekends" and its variants. If that fails, it tries to detect
        "weekdays" and its variants and returns all the dates within the next n_days from
        current date except those that occur on Saturdays and Sundays.

        Matches <"everyday", "daily", "all days"><space><"except"><space><"weekend", "weekends">
        Matches <"weekday", "weekdays", "week days", "week day", "all weekdays">

        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                           date entities
            n_days: Optional, number of days from current date, to return all dates of weekdays in the interval from
                    current date to date after n_days, default value is 30

        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        now = self.date_object
        end = now + datetime.timedelta(days=n_days)
        patterns = re.findall(r'\b(([eE]veryday|[dD]aily)|all\sdays[\s]?except[\s]?([wW]eekend|[wW]eekends))\b',
                              self.processed_text.lower())

        if not patterns:
            patterns = re.findall(r'\b(weekdays|weekday|week day|week days| all weekdays)\b',
                                  self.processed_text.lower())
        constant_type = WEEKDAYS
        if self._is_everyday_present(self.text):
            constant_type = REPEAT_WEEKDAYS
        today = now.weekday()
        count = 0
        weekend = []
        date_day = self.date_object
        while count < 15:
            if today > 6:
                today = 0
            if today == 5 or today == 6:
                weekend.append(copy.deepcopy(date_day))
            count += 1
            today += 1
            date_day = date_day + datetime.timedelta(days=1)
        i = 0
        weekend_digit = []
        while i <= (len(weekend) - 1):
            weekend_date = weekend[i].day
            weekend_digit.append(copy.deepcopy(weekend_date))
            i += 1
        for pattern in patterns:
            original = pattern[0]
            date_dict = {
                'dd': now.day,
                'mm': now.month,
                'yy': now.year,
                'type': constant_type
            }
            current_date = date_dict['dd']
            while now < end:
                if current_date not in weekend_digit:
                    date_list.append(copy.deepcopy(date_dict))
                now += datetime.timedelta(days=1)
                date_dict = {
                    'dd': now.day,
                    'mm': now.month,
                    'yy': now.year,
                    'type': constant_type
                }
                current_date = now.day
                original_list.append(original)
        return date_list, original_list

    def _date_identification_everyday_except_weekdays(self, date_list=None, original_list=None, n_days=30):
        """
        First this method tries to detect "everday except weekdays" and its variants. If that fails, it tries to detect
        "weekends" and its variants and returns all the dates within the next n_days from
        current date that occur on Saturdays and Sundays.

        Matches <"everyday", "daily", "all days"><space><"except"><space><"weekday", "weekdays">
        Matches <"weekend", "weekends", "week end", "week ends", "all weekends">


        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                           date entities
            n_days: Optional, number of days from current date, to return all dates of weekends in the interval from
                    current date to date after n_days, default value is 30

        Returns:
            A tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if date_list is None:
            date_list = []
        if original_list is None:
            original_list = []
        now = self.date_object
        end = now + datetime.timedelta(days=n_days)
        patterns = re.findall(r'\b(([eE]veryday|[dD]aily)|[eE]very\s*day|all[\s]?except[\s]?([wW]eekday|[wW]eekdays))\b'
                              , self.processed_text.lower())

        if not patterns:
            patterns = re.findall(r'\b((weekends|weekend|week end|week ends | all weekends))\b',
                                  self.processed_text.lower())
        constant_type = WEEKENDS
        if self._is_everyday_present(self.text):
            constant_type = REPEAT_WEEKENDS

        today = now.weekday()
        count = 0
        weekend = []
        date_day = self.date_object
        while count < 50:
            if today > 6:
                today = 0
            if today == 5 or today == 6:
                weekend.append(copy.deepcopy(date_day))
            count += 1
            today += 1
            date_day = date_day + datetime.timedelta(days=1)
        i = 0
        weekend_digit = []
        while i <= (len(weekend) - 1):
            weekend_date = weekend[i].isocalendar()
            weekend_digit.append(copy.deepcopy(weekend_date))
            i += 1
        for pattern in patterns:
            original = pattern[0]
            date_dict = {
                'dd': now.day,
                'mm': now.month,
                'yy': now.year,
                'type': constant_type
            }
            current_date = now.isocalendar()
            while now < end:
                if current_date in weekend_digit:
                    date_list.append(copy.deepcopy(date_dict))
                now += datetime.timedelta(days=1)
                date_dict = {
                    'dd': now.day,
                    'mm': now.month,
                    'yy': now.year,
                    'type': constant_type
                }
                current_date = now.isocalendar()
                original_list.append(original)
        return date_list, original_list

    def _day_month_format_for_arrival_departure(self, date_list=None, original_list=None):
        """
        Detects probable "start_date to/till/- end_date of month" format and its variants and returns both start date
        and end date
        format: <day><ordinal indicator><range separator><day><ordinal indicator><separator><Optional "of"><month>
        where each part is in of one of the formats given against them
            day: d, dd
            month: mmm, mmmm (abbreviation or spelled out in full)
            separator: ",", space
            range separator: "to", "-", "till"

        Few valid examples:
            "21st to 30th of Jan", "2 till 15 Nov", "10 - 15 of february"

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
        regex_pattern = r'\b((0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?\s?(?:-|to|-|till)\s?' + \
                        r'(0?[1-9]|[12][0-9]|3[01])\s?(?:nd|st|rd|th)?[\ \,]\s?(?:of)?\s?([A-Za-z]+))\b'
        patterns = re.findall(regex_pattern, self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0]
            dd1 = pattern[1]
            dd2 = pattern[2]
            probable_mm = pattern[3]
            mm = self.__get_month_index(probable_mm)
            yy = self.date_object.year
            if mm:
                date_dict_1 = {
                    'dd': int(dd1),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_dict_2 = {
                    'dd': int(dd2),
                    'mm': int(mm),
                    'yy': int(yy),
                    'type': TYPE_EXACT
                }
                date_list.append(date_dict_1)
                date_list.append(date_dict_2)

                original_list.append(original)
                original_list.append(original)

        return date_list, original_list

    def _is_everyday_present(self, text):
        """
        Detects if there is one of following words in text:
            "every", "daily", "recur", "always", "continue", "every day", "all"

        Args:
            text: string to recognize date entities from

        Returns:
            Boolean, True if any one of the above listed words are found , False otherwise

        """
        pattern = re.compile(r'\b(every|daily|recur|always|continue|every\s*day|all)\b', re.IGNORECASE)
        result = pattern.findall(text)
        if result:
            return True
        else:
            return False

    def _check_current_day(self, date_list):
        """
        Checks if TYPE_THIS_DAY or TYPE_REPEAT_DAY type of date is present in the date_list consisting of detected
        date dictionaries by checking "type" of each date

        Args:
            date_list: list of dictionaries of detected dates

        Returns:
            Boolean, True if any date in list has "type" either TYPE_THIS_DAY or TYPE_REPEAT_DAY , False otherwise

        """
        for index in date_list:
            if index['type'] in [TYPE_THIS_DAY, TYPE_REPEAT_DAY]:
                return True
        else:
            return False

    def _check_date_presence(self, date_list):
        """
        Checks if TYPE_NORMAL type of date is present in the date_list consisting of detected date dictionaries by
        checking "type" of each date

        Args:
            date_list: list of dictionaries of detected dates

        Returns:
            Boolean, True if any date in list has "type" TYPE_NORMAL , False otherwise

        """
        for i in date_list:
            if i['type'] == TYPE_EXACT:
                return True
        else:
            return False

    def _weeks_identification(self, date_list=None, original_list=None):
        """
        Checks for repeating days and will replace the type to TYPE_REPEAT_DAY
        
        Few valid examples:
            "every monday", "every friday", "every thursday" 
            
        Args:
            date_list: Optional, list to store dictionaries of detected dates
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            date entities

        Returns:
            tuple of two lists with first list containing the detected date entities and second list containing their
            corresponding substrings in the given text.

        """
        if original_list is None:
            original_list = []
        if date_list is None:
            date_list = []
        new_date_list = []
        new_text = self.text.lower().replace(',', '')
        is_everyday = self._is_everyday_present(new_text)

        if self._check_current_day(date_list) and is_everyday:
            for index, val in enumerate(date_list):
                if val['type'] == TYPE_THIS_DAY:
                    val['type'] = TYPE_REPEAT_DAY
                    new_date_list.append(val)
        if new_date_list:
            date_list = new_date_list
            original_list = original_list[:len(date_list)]
        return date_list, original_list

    def __get_month_index(self, value):
        """
        Gets the index of month by comparing the value with month names and their variants from the data store

        Args:
            value: string of the month detected in the text

        Returns:
            integer between 1 to 12 inclusive if value matches one of the month or its variants
            None if value doesn't match any of the month or its variants
        """
        for month in self.month_dictionary:
            if value.lower() in self.month_dictionary[month]:
                return month
        return None

    def __get_day_index(self, value):
        """
        Gets the index of month by comparing the value with day names and their variants from the data store

        Args:
            value: string of the month detected in the text

        Returns:
            integer between 1 to 7 inclusive if value matches one of the day or its variants
            None if value doesn't match any of the day or its variants
        """
        for day in self.day_dictionary:
            if value.lower() in self.day_dictionary[day]:
                return day
        return None
