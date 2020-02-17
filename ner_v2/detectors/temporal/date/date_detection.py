# coding=utf-8
from __future__ import absolute_import

import copy
import datetime
import importlib
import os
import re

from six.moves import range
from six.moves import zip

import models.crf.constant as model_constant
import ner_v2.detectors.temporal.constant as temporal_constant
from language_utilities.constant import ENGLISH_LANG, TRANSLATED_TEXT
from language_utilities.utils import translate_text
from models.crf.models import Models
from ner_constants import (FROM_MESSAGE, FROM_MODEL_VERIFIED, FROM_MODEL_NOT_VERIFIED, FROM_STRUCTURE_VALUE_VERIFIED,
                           FROM_STRUCTURE_VALUE_NOT_VERIFIED, FROM_FALLBACK_VALUE)
from ner_v2.detectors.base_detector import BaseDetector
from ner_v2.detectors.temporal.constant import (TYPE_EXACT, TYPE_EVERYDAY, TYPE_PAST,
                                                TYPE_NEXT_DAY, TYPE_REPEAT_DAY)
from ner_v2.detectors.temporal.utils import get_timezone
from ner_v2.detectors.utils import get_lang_data_path


class DateAdvancedDetector(BaseDetector):
    """
    DateAdvancedDetector detects dates from the text. It detects date with the properties like "from", "to",
    "start_range", "end_range"and "normal". These dates are returned in a dictionary form that contains relevant text,
    its actual value and its attribute in boolean field i.e. "from", "to", "start_range", "end_range" and "normal".
    This class uses DateDetector to detect the entity values. It also has model integrated to it that can be used to
    extract relevant dates from the text

    Attributes:
        text: string to extract entities from
        tagged_text: string with date entities replaced with tag defined by entity name
        processed_text: string with detected date entities removed
        date: list of date entities detected
        original_date_text: list to store substrings of the date detected as date entities
        entity_name: string by which the detected date entities would be replaced with on calling detect_entity()
        tag: entity_name prepended and appended with '__'
        date_detector_object: DateDetector object used to detect dates in the given text
        bot_message: str, set as the outgoing bot text/message
    """

    @staticmethod
    def get_supported_languages():
        """
        Return list of supported languages
        Returns:
            (list): supported languages
        """
        supported_languages = []
        cwd = os.path.dirname(os.path.abspath(__file__))
        cwd_dirs = [x for x in os.listdir(cwd) if os.path.isdir(os.path.join(cwd, x))]
        for _dir in cwd_dirs:
            if len(_dir.rstrip(os.sep)) == 2:
                supported_languages.append(_dir)
        return supported_languages

    def __init__(self, entity_name='date', locale=None, language=ENGLISH_LANG, timezone='UTC',
                 past_date_referenced=False, bot_message=None):
        """
        Initializes the DateDetector object with given entity_name and pytz timezone object

        Args:
            entity_name (str): A string by which the detected date entity substrings would be replaced with on calling
                               detect_entity()

            timezone (Optional, str): timezone identifier string that is used to create a pytz timezone object
                                      default is UTC
            past_date_referenced (bool): to know if past or future date is referenced for date text like 'kal', 'parso'
        """
        self.locale = locale
        self._supported_languages = self.get_supported_languages()
        super(DateAdvancedDetector, self).__init__(language=language)
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.date = []
        self.original_date_text = []
        self.entity_name = entity_name
        self.tag = '__' + entity_name + '__'
        self.date_detector_object = DateDetector(entity_name=entity_name,
                                                 language=language,
                                                 timezone=timezone,
                                                 past_date_referenced=past_date_referenced,
                                                 locale=locale)
        self.bot_message = None
        if bot_message:
            self.set_bot_message(bot_message)

    @property
    def supported_languages(self):
        return self._supported_languages

    def detect_entity(self, text, run_model=False, **kwargs):
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
        :param text: text
        :param run_model: run_model
        """
        self.text = ' ' + text.lower() + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        date_data = []
        if run_model:
            date_data = self._date_model_detection()
        if not run_model or not date_data:
            date_data = self._detect_date()
        return self.unzip_convert_date_dictionaries(date_data)

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

        Notes:- This feature is currently supported for english language script only.

        Returns:
            The list of dictionary containing the dictionary for date which is detected as start_range and date
            that got detected as end_range. For start range the key "start_range" will be set to True.
            Whereas for end range the key "end_range" will be set to True.
        """
        date_dict_list = []
        regex_pattern = re.compile(r'\b(([12][0-9]|3[01]|0?[1-9])'
                                   r'\s?'
                                   r'(?:nd|st|rd|th)?'
                                   r'(?:(?:\s*\-\s*)|\s+(?:to|till|se)\s+)'
                                   r'([12][0-9]|3[01]|0?[1-9])'
                                   r'\s?'
                                   r'(?:nd|st|rd|th)?'
                                   r'[\s\,]+'
                                   r'(?:of\s+)?'
                                   r'([A-Za-z]+))\b', flags=re.UNICODE)

        regex_pattern_2 = re.compile(r'\b(([12][0-9]|3[01]|0?[1-9])'
                                     r'\s?'
                                     r'(?:nd|st|rd|th)?'
                                     r'[\s\,]+'
                                     r'(?:of\s+)?'
                                     r'([A-Za-z]+)'
                                     r'(?:(?:\s*\-\s*)|\s+(?:to|till|se)\s+)'
                                     r'([12][0-9]|3[01]|0?[1-9])'
                                     r'\s?'
                                     r'(?:nd|st|rd|th)?'
                                     r'(?:[\s\,]+(?:of\s+)?([A-Za-z]+))?)\b', flags=re.UNICODE)

        dd_to_dd_mmm_matches = regex_pattern.findall(self.processed_text)
        dd_mmm_to_dd_matches = regex_pattern_2.findall(self.processed_text)
        if dd_to_dd_mmm_matches:
            for match in dd_to_dd_mmm_matches:
                date_dicts = self._date_dict_from_text(text=match[0])
                if len(date_dicts) == 2:
                    date_dicts[0][temporal_constant.DATE_START_RANGE_PROPERTY] = True
                    date_dicts[1][temporal_constant.DATE_END_RANGE_PROPERTY] = True
                    date_dict_list.extend(date_dicts)

        elif dd_mmm_to_dd_matches:
            for match in dd_mmm_to_dd_matches:
                date_dicts = self._date_dict_from_text(text=match[0])
                if len(date_dicts) == 2:
                    date_dicts[0][temporal_constant.DATE_START_RANGE_PROPERTY] = True
                    date_dicts[1][temporal_constant.DATE_END_RANGE_PROPERTY] = True
                    date_dict_list.extend(date_dicts)
        else:
            for sentence_part in re.split(r'\s+(?:and|aur|&|or)\s+', self.processed_text):
                parts = re.split(r'\s+(?:\-|to|till|se)\s+', sentence_part)
                skip_next_pair = False
                _day_of_week_types = [temporal_constant.TYPE_THIS_DAY, temporal_constant.TYPE_NEXT_DAY]
                for start_part, end_part in zip(parts, parts[1:]):
                    if skip_next_pair:
                        skip_next_pair = False
                        continue
                    start_date_list = self._date_dict_from_text(text=start_part, start_range_property=True)
                    end_date_list = self._date_dict_from_text(text=end_part, end_range_property=True)
                    if start_date_list and end_date_list:
                        possible_start_date = start_date_list[0]
                        possible_end_date = end_date_list[-1]
                        start_date_type = possible_start_date[temporal_constant.DATE_VALUE]['type']
                        end_date_type = possible_end_date[temporal_constant.DATE_VALUE]['type']
                        if start_date_type in _day_of_week_types and end_date_type in _day_of_week_types:
                            start_date_list, end_date_list = self._fix_day_range(start_date_dict=possible_start_date,
                                                                                 end_date_dict=possible_end_date)
                        else:
                            # FIXME: Assumes end_date > start_date. Also can return dates in past when date detector
                            # returns dates in the past
                            start_date_list = [possible_start_date]
                            end_date_list = [possible_end_date]
                        date_dict_list.extend(start_date_list)
                        date_dict_list.extend(end_date_list)
                        skip_next_pair = True
        return date_dict_list

    def _fix_day_range(self, start_date_dict, end_date_dict):
        """
        If today is between the detected range, generate two day ranges - range for current week and the same range
        for next week, other wise both start date and end date dicts are returned as only elements of start date list
        and end date list respectively.

        For example, querying "Monday to Friday" on Wednesday would yield dates for Monday (in the past) to Friday
        and next Monday to next Friday

        Args:
            start_date_dict (dict): Dict containing the date value marked as start of the range
            end_date_dict (dict): Dict containing the date value marked as end of the range

        Returns:
            tuple containing
                list containing dictionaries of start of range dates
                list containing dictionaries of end of range dates

        """
        repeat_flag = start_date_dict[temporal_constant.DATE_VALUE]['type'] in [TYPE_EVERYDAY, TYPE_REPEAT_DAY]
        start_date_list, end_date_list = [start_date_dict], [end_date_dict]
        start_date = self.date_detector_object.to_datetime_object(start_date_dict[temporal_constant.DATE_VALUE])
        end_date = self.date_detector_object.to_datetime_object(end_date_dict[temporal_constant.DATE_VALUE])
        if end_date < start_date:
            current_range_start_date = start_date - datetime.timedelta(days=7)
            current_range_start_dict = self.date_detector_object.to_date_dict(current_range_start_date,
                                                                              date_type=TYPE_PAST)
            output_dict = copy.copy(start_date_dict)
            output_dict[temporal_constant.DATE_VALUE] = current_range_start_dict
            start_date_list.insert(0, output_dict)

            next_range_end_date = end_date + datetime.timedelta(days=7)
            next_range_end_dict = self.date_detector_object.to_date_dict(next_range_end_date, date_type=TYPE_NEXT_DAY)
            output_dict = copy.copy(end_date_dict)
            output_dict[temporal_constant.DATE_VALUE] = next_range_end_dict
            end_date_list.append(output_dict)

        if repeat_flag:
            _start_date_list = []
            for date_dict in start_date_list:
                date_dict[temporal_constant.DATE_VALUE]['type'] = TYPE_REPEAT_DAY
                _start_date_list.append(date_dict)

            _end_date_list = []
            for date_dict in end_date_list:
                date_dict[temporal_constant.DATE_VALUE]['type'] = TYPE_REPEAT_DAY
                _end_date_list.append(date_dict)

            start_date_list, end_date_dict = _start_date_list, _end_date_list

        return start_date_list, end_date_list

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
        regex_pattern = re.compile(r'\b'
                                   r'(?:check(?:\s|\-)?in date (?:is|\:)?|'
                                   r'onward date\s?(?:\:|\-)?|departure date|leaving on|starting from|'
                                   r'departing on|departing|going on|departs on|for)'
                                   r'\s+(.+?)(?:\band|&|(?<!\d)\.|$)', flags=re.UNICODE)
        matches = regex_pattern.findall(self.processed_text)

        for match in matches:
            date_dict_list.extend(self._date_dict_from_text(text=match, from_property=True))
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
        regex_pattern_1 = re.compile(r'\b'
                                     r'(?:check(?:\s|\-)?out date (?:is|\:)?|'
                                     r'coming back|return date\s?(?:\:|\-)?|returning on|returning at|'
                                     r'arriving|arrive|return|back)'
                                     r'\s+(.+?)(?:\band|&|(?<!\d)\.|$)', flags=re.UNICODE)
        regex_pattern_2 = re.compile(r'(.+?)\s+(?:ko?\s+)?(?:aana|ana|aunga|aaun)', flags=re.UNICODE)
        matches = None
        matches_1 = regex_pattern_1.findall(self.processed_text)
        matches_2 = regex_pattern_2.findall(self.processed_text)

        if matches_1:
            matches = matches_1
        elif matches_2:
            matches = matches_2

        matches = matches or []
        for match in matches:
            date_dict_list.extend(self._date_dict_from_text(text=match, to_property=True))
        return date_dict_list

    def _detect_any_date(self):
        """
        Finds departure and return type dates in the given text. It detects 'departure' and 'return' and their synonyms
        and tags all the detected dates in the text accordingly. If both type synonyms are found, and more than one
        dates are detected, first date is marked as departure type and last as return type. If only one date is found,
        it is marked as departure if 'departure' or both type synonyms are found and marked as 'return' type if
        'return' type synonyms were found in the given text


        Args:

        Returns:
            The list of dictionary containing the dictionary for date which is detected as departure date and date
            that got detected as arrival date or the date that got detected as normal date. For departure date
            the key "from" will be set to True.
            Whereas for arrival date the key "to" will be set to True.
            Otherwise the normal date with the key 'normal' will be set to True
        """
        departure_date_flag = False
        return_date_flag = False
        if self.bot_message:
            departure_regex_string = r'traveling on|going on|starting on|departure date|date of travel|' + \
                                     r'check in date|check-in date|date of check-in|' \
                                     r'date of departure\.|'
            hinglish_departure = u'जाने|जाऊँगा|जाना'
            departure_regex_string = departure_regex_string + hinglish_departure
            arrival_regex_string = r'traveling back|coming back|returning back|returning on|return date' + \
                                   r'|arrival date|check out date|check-out date|date of check-out' \
                                   r'|check out|'
            hinglish_arrival = u'आने|आगमन|अनेका|रिटर्न'
            arrival_regex_string = arrival_regex_string + hinglish_arrival
            departure_regexp = re.compile(departure_regex_string, flags=re.UNICODE)
            arrival_regexp = re.compile(arrival_regex_string, flags=re.UNICODE)
            if departure_regexp.search(self.bot_message) is not None:
                departure_date_flag = True
            elif arrival_regexp.search(self.bot_message) is not None:
                return_date_flag = True

        date_dict_list = self._date_dict_from_text(text=self.processed_text)
        if date_dict_list:
            if len(date_dict_list) > 1:
                for i in range(len(date_dict_list)):
                    date_dict_list[i][temporal_constant.DATE_NORMAL_PROPERTY] = True
            else:
                if departure_date_flag:
                    date_dict_list[0][temporal_constant.DATE_FROM_PROPERTY] = True
                elif return_date_flag:
                    date_dict_list[0][temporal_constant.DATE_TO_PROPERTY] = True
                else:
                    date_dict_list[0][temporal_constant.DATE_NORMAL_PROPERTY] = True
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
            self.tagged_text = self.tagged_text.replace(date_dict[temporal_constant.ORIGINAL_DATE_TEXT], self.tag)
            self.processed_text = self.processed_text.replace(date_dict[temporal_constant.ORIGINAL_DATE_TEXT], '')

    def set_bot_message(self, bot_message):
        """
        Sets the object's bot_message attribute

        Args:
            bot_message: is the previous message that is sent by the bot
        """
        self.bot_message = bot_message
        self.date_detector_object.set_bot_message(self.bot_message)

    def _date_dict_from_text(self, text, from_property=False, to_property=False, start_range_property=False,
                             end_range_property=False, normal_property=False, detection_method=FROM_MESSAGE):
        """
        Takes the text and the property values and creates a list of dictionaries based on number of dates detected

        Attributes:
            text: Text on which DateDetection needs to run on
            from_property: True if the text is belonging to "from" property". for example, From monday
            to_property: True if the text is belonging to "to" property". for example, To monday
            start_range_property: True if the text is belonging to "start_range" property". for example, starting from
                                  monday
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
        for index, date in enumerate(date_list):
            date_dict_list.append(self._to_output_dict(date_dict=date,
                                                       original_text=original_list[index],
                                                       from_property=from_property,
                                                       to_property=to_property,
                                                       start_range_property=start_range_property,
                                                       end_range_property=end_range_property,
                                                       normal_property=normal_property,
                                                       detection_method=detection_method))
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

    def unzip_convert_date_dictionaries(self, entity_dict_list):
        """
        Separate out date dictionaries into list of dictionaries of date values, corresponding list of substrings in
        the original text for each date dictionary
        Args:
            entity_dict_list (list of dict): list containing dictionaries containing detected date values and metadata

        Returns:
            Returns the tuple containing three lists of equal length
             list containing dictionaries of date values,
             list containing original text for each detected date value
        """
        entity_list, original_list = [], []
        for entity_dict in entity_dict_list:
            entity_list.append(
                {
                    temporal_constant.DATE_VALUE: entity_dict[temporal_constant.DATE_VALUE],
                    temporal_constant.DATE_FROM_PROPERTY: entity_dict[temporal_constant.DATE_FROM_PROPERTY],
                    temporal_constant.DATE_TO_PROPERTY: entity_dict[temporal_constant.DATE_TO_PROPERTY],
                    temporal_constant.DATE_START_RANGE_PROPERTY: entity_dict[
                        temporal_constant.DATE_START_RANGE_PROPERTY],
                    temporal_constant.DATE_END_RANGE_PROPERTY: entity_dict[temporal_constant.DATE_END_RANGE_PROPERTY],
                    temporal_constant.DATE_NORMAL_PROPERTY: entity_dict[temporal_constant.DATE_NORMAL_PROPERTY],

                }
            )
            original_list.append(entity_dict[temporal_constant.ORIGINAL_DATE_TEXT])
        return entity_list, original_list

    @staticmethod
    def _to_output_dict(date_dict, original_text, from_property, to_property, start_range_property,
                        end_range_property, normal_property, detection_method):
        """
        Generate output dict for the detected date value with extra metadata

        Args:
             date_dict (dict): dict containing dd, mm, yy of the detected date value
             original_text (str): substring which was detected as a date value
             from_property (bool): boolean indicating if this date was detected as a 'from start' date
             to_property (bool): boolean indicating if this date was detected as a 'to end' date
             start_range_property (bool): boolean indicating if this date marks the start of a range
             end_range_property (bool): boolean indicating if this date marks the end of a range
             normal_property (bool):  boolean indicating if this date is singular date and not associated with any
                                      range
             detection_method (str): detection method - pattern from message or using model
        Returns:
            dict: dictionary containing, detected date value and additional metadata like 'from', 'to', 'start',
                  'end', 'normal'
        """
        return {
            temporal_constant.DATE_VALUE: date_dict,
            temporal_constant.ORIGINAL_DATE_TEXT: original_text,
            temporal_constant.DATE_FROM_PROPERTY: from_property,
            temporal_constant.DATE_TO_PROPERTY: to_property,
            temporal_constant.DATE_START_RANGE_PROPERTY: start_range_property,
            temporal_constant.DATE_END_RANGE_PROPERTY: end_range_property,
            temporal_constant.DATE_NORMAL_PROPERTY: normal_property,
            temporal_constant.DATE_DETECTION_METHOD: detection_method,
        }

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

            data_dict = self._to_output_dict(date_dict=date_value,
                                             original_text=output[model_constant.MODEL_DATE_VALUE],
                                             from_property=output[model_constant.MODEL_DATE_FROM],
                                             to_property=output[model_constant.MODEL_DATE_TO],
                                             start_range_property=output[model_constant.MODEL_START_DATE_RANGE],
                                             end_range_property=output[model_constant.MODEL_END_DATE_RANGE],
                                             normal_property=output[model_constant.MODEL_DATE_NORMAL],
                                             detection_method=detection_method)
            date_dict_list.append(data_dict)
        return date_dict_list

    def detect(self, message=None, structured_value=None, fallback_value=None, **kwargs):
        """
        Use detector to detect entities from text. It also translates query to language compatible to detector

        Args:
            message (str): natural text on which detection logic is to be run. Note if structured value is
                                    detection is run on structured value instead of message
            structured_value (str): Value obtained from any structured elements. Note if structured value is
                                    detection is run on structured value instead of message
                                    (For example, UI elements like form, payload, etc)
            fallback_value (str): If the detection logic fails to detect any value either from structured_value
                              or message then we return a fallback_value as an output.

        Returns:
            dict or None: dictionary containing entity_value, original_text and detection;
                          entity_value is in itself a dict with its keys varying from entity to entity

        Example:
            1) Consider an example of restaurant detection from a message

                message = 'i want to order chinese from  mainland china and pizza from domminos'
                structured_value = None
                fallback_value = None
                output = detect(message=message, structured_value=structured_value,
                                  fallback_value=fallback_value)
                print output

                    >> [{'detection': 'message', 'original_text': 'mainland china', 'entity_value':
                    {'value': u'Mainland China'}}, {'detection': 'message', 'original_text': 'domminos',
                    'entity_value': {'value': u"Domino's Pizza"}}]

            2) Consider an example of movie name detection from a structured value

                message = 'i wanted to watch movie'
                entity_name = 'movie'
                structured_value = 'inferno'
                fallback_value = None
                output = get_text(message=message, entity_name=entity_name, structured_value=structured_value,
                                  fallback_value=fallback_value)
                print output

                    >> [{'detection': 'structure_value_verified', 'original_text': 'inferno', 'entity_value':
                    {'value': u'Inferno'}}]

            3) Consider an example of movie name detection from  a message
                message = 'i wanted to watch inferno'
                entity_name = 'movie'
                structured_value = 'delhi'
                fallback_value = None
                output = get_text(message=message, entity_name=entity_name, structured_value=structured_value,
                                  fallback_value=fallback_value)
                print output

                    >> [{'detection': 'message', 'original_text': 'inferno', 'entity_value': {'value': u'Inferno'}}]

        """
        if self._language != self._processing_language and self._translation_enabled:
            if structured_value:
                translation_output = translate_text(structured_value, self._language,
                                                    self._processing_language)
                structured_value = translation_output[TRANSLATED_TEXT] if translation_output['status'] else None
            elif message:
                translation_output = translate_text(message, self._language,
                                                    self._processing_language)
                message = translation_output[TRANSLATED_TEXT] if translation_output['status'] else None

        text = structured_value if structured_value else message
        entity_list, original_text_list = self.detect_entity(text=text)

        if structured_value:
            if entity_list:
                value, method, original_text = entity_list, FROM_STRUCTURE_VALUE_VERIFIED, original_text_list
            else:
                value, method, original_text = [structured_value], FROM_STRUCTURE_VALUE_NOT_VERIFIED, \
                                               [structured_value]
        elif entity_list:
            value, method, original_text = entity_list, FROM_MESSAGE, original_text_list
        elif fallback_value:
            entity_list, original_text_list = self.detect_entity(text=fallback_value)
            value, method, original_text = entity_list, FROM_FALLBACK_VALUE, original_text_list
        else:
            return None

        return self.output_entity_dict_list(entity_value_list=value, original_text_list=original_text,
                                            detection_method=method, detection_language=self._processing_language)


class DateDetector(object):
    """
    Detects date in various formats from given text and tags them.

    Detects all date entities in given text and replaces them by entity_name.
    Additionally detect_entity() method returns detected date values in dictionary containing values for day (dd),
    month (mm), year (yy), type (exact, possible, everyday, weekend, range etc.)

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected date entities would be replaced with on calling detect_entity()
        tagged_text: string with date entities replaced with tag defichaloned by entity name
        processed_text: string with detected date entities removed
        date: list of date entities detected
        original_date_text: list to store substrings of the text detected as date entities
        tag: entity_name prepended and appended with '__'
        timezone: Optional, pytz.timezone object used for getting current time, default is pytz.timezone('UTC')
        now_date: datetime object holding timestamp while DateDetector instantiation
        bot_message: str, set as the outgoing bot text/message
        language: source language of text
    """

    def __init__(self, entity_name, locale=None, language=ENGLISH_LANG, timezone='UTC', past_date_referenced=False):
        """Initializes a DateDetector object with given entity_name and pytz timezone object

        Args:
            entity_name: A string by which the detected date entity substrings would be replaced with on calling
                        detect_entity()
            timezone (Optional, str): timezone identifier string that is used to create a pytz timezone object
                                      default is UTC
            past_date_referenced (bool): to know if past or future date is referenced for date text like 'kal', 'parso'
            locale(Optional, str): user locale default is None
        """
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.date = []
        self.original_date_text = []
        self.entity_name = entity_name
        self.tag = '__' + entity_name + '__'
        self.timezone = get_timezone(timezone)
        self.now_date = datetime.datetime.now(tz=self.timezone)
        self.bot_message = None
        self.language = language
        self.locale = locale

        try:
            date_detector_module = importlib.import_module(
                'ner_v2.detectors.temporal.date.{0}.date_detection'.format(self.language))
            self.language_date_detector = date_detector_module.DateDetector(entity_name=self.entity_name,
                                                                            past_date_referenced=past_date_referenced,
                                                                            timezone=self.timezone,
                                                                            locale=self.locale)
        except ImportError:
            standard_date_regex = importlib.import_module(
                'ner_v2.detectors.temporal.date.standard_date_regex'
            )
            self.language_date_detector = standard_date_regex.DateDetector(
                entity_name=self.entity_name,
                data_directory_path=get_lang_data_path(detector_path=os.path.abspath(__file__),
                                                       lang_code=self.language),
                timezone=self.timezone,
                past_date_referenced=past_date_referenced,
                locale=self.locale
            )

    def detect_entity(self, text, **kwargs):
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
        :param text: text
        """

        self.text = ' ' + text.strip().lower() + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        if self.language_date_detector:
            self.date, self.original_date_text = self.language_date_detector.detect_date(self.processed_text)

        validated_date_list, validated_original_list = [], []

        # Note: Following leaves tagged text incorrect but avoids returning invalid dates like 30th Feb
        for date, original_text in zip(self.date, self.original_date_text):
            try:
                datetime.date(year=date['yy'], month=date['mm'], day=date['dd'])
                validated_date_list.append(date)
                validated_original_list.append(original_text)
            except ValueError:
                pass

        return validated_date_list, validated_original_list

    def set_bot_message(self, bot_message):
        """
        Sets the object's bot_message attribute

        Args:
            bot_message: is the previous message that is sent by the bot
        """
        self.bot_message = bot_message
        self.language_date_detector.set_bot_message(bot_message)

    def to_datetime_object(self, base_date_value_dict):
        """
        Convert the given date value dict to a timezone localised datetime object

        Args:
            base_date_value_dict (dict): dict containing dd, mm, yy

        Returns:
            datetime object: datetime object localised with the timezone given on initialisation
        """
        datetime_object = datetime.datetime(year=base_date_value_dict['yy'],
                                            month=base_date_value_dict['mm'],
                                            day=base_date_value_dict['dd'], )
        return self.timezone.localize(datetime_object)

    @staticmethod
    def to_date_dict(datetime_object, date_type=TYPE_EXACT):
        """
        Convert the given datetime object to a dictionary containing dd, mm, yy

        Args:
            datetime_object (datetime.datetime): datetime object
            date_type (str, optional, default TYPE_EXACT): 'type' metdata for this detected date

        Returns:
            dict: dictionary containing day, month, year in keys dd, mm, yy respectively with date type as additional
            metadata.
        """
        return {
            'dd': datetime_object.day,
            'mm': datetime_object.month,
            'yy': datetime_object.year,
            'type': date_type,
        }
