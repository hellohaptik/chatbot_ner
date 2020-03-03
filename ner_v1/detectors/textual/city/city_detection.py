# coding=utf-8
from __future__ import absolute_import
import re

import models.crf.constant as model_constant
import ner_v1.constant as detector_constant
import language_utilities.constant as lang_constant
from models.crf.models import Models
from ner_constants import FROM_MESSAGE, FROM_MODEL_VERIFIED, FROM_MODEL_NOT_VERIFIED
from ner_v1.detectors.textual.text.text_detection import TextDetector


class CityDetector(object):
    """
    CityDetector detects cities from the text. It Detects city with the properties like "from", "to", "via" and
    "normal". These cities are returned in a dictionary form that contains relevant text, its actual value
    and its attribute in boolean field i.e. "from", "to", "via", "normal".
    This class uses TextDetector to detect the entity values. It also has model integrated to it that can be used to
    extract relevant text from the text

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected city entities would be replaced with on calling detect_entity()
        tagged_text: string with city entities replaced with tag defined by entity_name
        city: list to store detected entities from the text
        processed_text: string with detected time entities removed
        tag: entity_name prepended and appended with '__'
    """

    def __init__(self, entity_name, language=lang_constant.ENGLISH_LANG):
        """
        Initializes a CityDetector object with given entity_name

        Args:
            entity_name: A string by which the detected substrings that correspond to text entities would be replaced
                         with on calling detect_entity()
            language: language code of text
        """

        self.entity_name = entity_name
        self.text = ''
        self.bot_message = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.city = []
        self.text_detection_object = TextDetector(entity_name=entity_name, source_language_script=language)
        self.tag = '__' + self.entity_name + '__'

    def detect_entity(self, text, run_model=False):
        """Detects city in the text string

        Args:
            text: string to extract entities from
            run_model: True if model needs to be run else False
        Returns:
            It returns the list of dictionary containing the fields like detection_method, from, normal, to,
            text, value, via

            For example:

                [
                    {
                      'detection_method': 'message',
                      'from': False,
                      'normal': True,
                      'text': 'mumbai',
                      'to': False,
                      'value': u'BOM',
                      'via': False
                    }
                ]


            Additionally this function assigns this list to self.city

        """
        self.text = ' ' + text + ' '
        self.text = self.text.lower()
        self.processed_text = self.text
        self.tagged_text = self.text
        city_data = []
        if run_model:
            city_data = self._city_model_detection()
        if not run_model or not city_data:
            city_data = self._detect_city()
        self.city = city_data
        return city_data

    def _detect_city(self):
        """
        Detects a city and categorises it into "from", "to", "via" and "normal" attributes

        Returns:
            It returns the list of dictionary containing the fields like detection_method, from, normal, to,
            text, value, via


        """
        # print 'detection for default task'
        final_city_dict_list = []
        city_dict_list = self._detect_departure_arrival_city_prepositions()
        final_city_dict_list.extend(city_dict_list)
        self._update_processed_text(city_dict_list)

        city_dict_list = self._detect_departure_arrival_city()
        final_city_dict_list.extend(city_dict_list)
        self._update_processed_text(city_dict_list)

        city_dict_list = self._detect_arrival_departure_city()
        final_city_dict_list.extend(city_dict_list)
        self._update_processed_text(city_dict_list)

        city_dict_list = self._detect_departure_city()
        final_city_dict_list.extend(city_dict_list)
        self._update_processed_text(city_dict_list)

        city_dict_list = self._detect_arrival_city()
        final_city_dict_list.extend(city_dict_list)
        self._update_processed_text(city_dict_list)

        city_dict_list = self._detect_any_city()
        final_city_dict_list.extend(city_dict_list)
        self._update_processed_text(city_dict_list)

        return final_city_dict_list

    def _detect_departure_arrival_city(self):
        """
        Finds <any text><space(s)><'-' or 'to' or '2'><space(s)><any text> in the given text.
        It  splits the text into two parts on '-' or 'to' or '2'
        and detects the departure city in the first (left) part and detects arrival city in the second (right) part

        Args:
            None

        Returns:
            The list of dictionary containing the dictionary for city which is detected as departure_city and city
            that got detected as arrival_city. For departure city the key "from" will be set to True.
            Whereas for arrival city the key "to" will be set to True.
        """
        city_dict_list = []
        patterns = re.findall(u'\\s(([A-Za-z\u0900-\u097F]+)\\s'
                              u'+(\\-|to|2|se|से|and)\\s+([A-Za-z\u0900-\u097F\\s]+))\\.?',
                              self.processed_text.lower(), re.UNICODE)
        for pattern in patterns:
            city_dict_list.extend(
                self._city_dict_from_text(text=pattern[1], from_property=True)
            )

            city_dict_list.extend(
                self._city_dict_from_text(text=pattern[3], to_property=True)
            )

        return city_dict_list

    def _detect_departure_arrival_city_prepositions(self):
        """
        Finds <preposition><any text><space(s)><'-' or 'to' or '2' or preposition><space(s)><any text> in the given
        text.
        It  splits the text into two parts on '-' or 'to' or '2'
        and detects the departure city in the first (left) part and detects arrival city in the second (right) part

        Args:
            None

        Returns:
            The list of dictionary containing the dictionary for city which is detected as departure_city and city
            that got detected as arrival_city. For departure city the key "from" will be set to True.
            Whereas for arrival city the key "to" will be set to True.
        """
        city_dict_list = []
        patterns = re.findall(u'\\s((?:from|frm|departing|depart|leaving|leave)\\s+([A-Za-z\u0900-\u097F]+)'
                              u'\\s+(?:and|to|se|से|2|for|fr|arriving|arrive|reaching|reach|rch)'
                              u'\\s+([A-Za-z\u0900-\u097F]+))\\.?',
                              self.processed_text.lower(), re.UNICODE)

        for pattern in patterns:
            city_dict_list.extend(
                self._city_dict_from_text(text=pattern[1], from_property=True)
            )

            city_dict_list.extend(
                self._city_dict_from_text(text=pattern[2], to_property=True)
            )

        return city_dict_list

    def _detect_arrival_departure_city(self):
        """
        Finds <preposition><any text><space(s)><'-' or 'to' or '2' or preposition><space(s)><any text> in the given
        text.
        It  splits the text into two parts on '-' or 'to' or '2'
        and detects the arrival city in the first (left) part and detects departure city in the second (right) part

        Args:
            None

        Returns:
            The list of dictionary containing the dictionary for city which is detected as departure_city and city
            that got detected as arrival_city. For departure city the key "from" will be set to True.
            Whereas for arrival city the key "to" will be set to True.

        """
        city_dict_list = []
        patterns = re.findall(u'\\s((?:and|to|2|for|fr|arriving|arrive|reaching|reach|rch)'
                              u'\\s+([A-Za-z\u0900-\u097F]+)\\s+(?:from|frm|departing|depart|leaving|leave)'
                              u'\\s+([A-Za-z\u0900-\u097F]+))\\.?',
                              self.processed_text.lower(), re.UNICODE)

        for pattern in patterns:
            city_dict_list.extend(
                self._city_dict_from_text(text=pattern[2], from_property=True)
            )

            city_dict_list.extend(
                self._city_dict_from_text(text=pattern[1], to_property=True)
            )

        return city_dict_list

    def _detect_departure_city(self):
        """
        Finds departure type cities in the given text by matching few keywords like 'from', 'departing',
        'leaving', 'departure city', 'departing', 'going to' . It detects dates in the part of text right to these
        keywords.

        Args:
            None

        Returns:
            The list of dictionary containing the dictionary for city which is detected as departure_city.
            For departure city the key "from" will be set to True.

        """
        city_dict_list = []
        patterns = re.findall(u'\\s((from|frm|departing|depart|leaving|leave|origin '
                              u'city\\:|departure city\\:|going to)'
                              u'\\s+([A-Za-z\u0900-\u097F]+))\\.?\\s',
                              self.processed_text.lower(), re.UNICODE)

        for pattern in patterns:
            city_dict_list.extend(
                self._city_dict_from_text(text=pattern[2], from_property=True)
            )

        return city_dict_list

    def _detect_arrival_city(self):
        """
        Finds return type dates in the given text by matching few keywords like 'arriving', 'arrive',
        'reaching', 'reach', 'destination city:' . It detects city in the part of text right
        to these keywords.

        Args:
            None

        Returns:
            The list of dictionary containing the dictionary for city which is detected as arrival_city.
            for arrival city the key "to" will be set to True.

        """
        city_dict_list = []
        patterns_1 = re.findall(u'\\s((to|2|for|fr|arriving|arrive|reaching|'
                                u'reach|rch|destination city\\:|arrival city\\:)'
                                u'\\s+([A-Za-z\u0900-\u097F]+))\\.?\\s',
                                self.processed_text.lower(), re.UNICODE)
        patterns_2 = re.findall(u'([A-Za-z\u0900-\u097F]+)\\s+(jana|jaana|jau|ghum|ghoom|जाना|जाऊं|जाऊँ|घूम)',
                                self.processed_text.lower(),
                                re.UNICODE)
        for pattern in patterns_1:
            city_dict_list.extend(
                self._city_dict_from_text(text=pattern[2], to_property=True)
            )
        for pattern in patterns_2:
            city_dict_list.extend(
                self._city_dict_from_text(text=pattern[0], to_property=True)
            )

        return city_dict_list

    def _detect_any_city(self):
        """
        This function makes use of bot_message. In a chatbot user might just enter city name based on the
        previous question asked by the bot. So, if the previous question asked by the bot contains words like
        departure city, origin city, origin and if the current message contains city then we assign the
        detected city as departure_city. if the previous message contains words like arrival city, destination city,
        flying to in the bots message and the current message contains the city then we assign the detected city as
        arrival city


        Args:
            None

        Returns:
            The list of dictionary containing the dictionary for city which is detected as departure_city and city
            that got detected as arrival_city. For departure city the key "from" will be set to True.
            Whereas for arrival city the key "to" will be set to True.

        """
        city_dict_list = []
        departure_city_flag = False
        arrival_city_flag = False
        if self.bot_message:
            hinglish_departure = u'कहां से'
            departure_regexp = re.compile(u'departure city|origin city|origin|'
                                          u'traveling from|leaving from|flying from|travelling from|'
                                          + hinglish_departure)
            hinglish_arrival = u'कहां जाना|\u0916\u093c\u0924\u092e|\u0959\u0924\u092e'  # unicode for ख़तम
            arrival_regexp = re.compile(u'traveling to|travelling to|arrival city|'
                                        u'arrival|destination city|destination|leaving to|flying to|'
                                        + hinglish_arrival)
            if departure_regexp.search(self.bot_message) is not None:
                departure_city_flag = True
            elif arrival_regexp.search(self.bot_message) is not None:
                arrival_city_flag = True

        patterns = re.findall(u'\\s((.+))\\.?', self.processed_text.lower(), re.UNICODE)

        for pattern in patterns:
            pattern = list(pattern)
            city_dict_list = self._city_dict_from_text(text=pattern[1])
            if city_dict_list:
                if len(city_dict_list) > 1:
                    city_dict_list[0][detector_constant.CITY_FROM_PROPERTY] = True
                    city_dict_list[-1][detector_constant.CITY_TO_PROPERTY] = True
                else:
                    if departure_city_flag:
                        city_dict_list[0][detector_constant.CITY_FROM_PROPERTY] = True
                    elif arrival_city_flag:
                        city_dict_list[0][detector_constant.CITY_TO_PROPERTY] = True
                    else:
                        city_dict_list[0][detector_constant.CITY_NORMAL_PROPERTY] = True
        return city_dict_list

    def _city_dict_from_text(self, text, from_property=False, to_property=False, via_property=False,
                             normal_property=False, detection_method=FROM_MESSAGE):
        """
        Takes the text and the property values and creates a list of dictionaries based on number of cities detected

        Attributes:
            text: Text on which TextDetection needs to run on
            from_property: True if the text is belonging to "from" property". for example, From Mumbai
            to_property: True if the text is belonging to "to" property". for example, To Mumbai
            via_property: True if the text is belonging to "via" property". for example, via Mumbai
            normal_property: True if the text is belonging to "normal" property". for example, atms in Mumbai
            detection_method: method through which it got detected whether its through message or model

        Returns:

            It returns the list of dictionary containing the fields like detection_method, from, normal, to,
            text, value, via

            For example:

                [
                    {
                      'detection_method': 'message',
                      'from': False,
                      'normal': True,
                      'text': 'mumbai',
                      'to': False,
                      'value': u'BOM',
                      'via': False
                    }
                ]

        """
        city_dict_list = []
        city_list, original_list = self._city_value(text=text)
        index = 0
        for city in city_list:
            city_dict_list.append(
                {
                    detector_constant.CITY_VALUE: city,
                    detector_constant.ORIGINAL_CITY_TEXT: original_list[index],
                    detector_constant.CITY_FROM_PROPERTY: from_property,
                    detector_constant.CITY_TO_PROPERTY: to_property,
                    detector_constant.CITY_VIA_PROPERTY: via_property,
                    detector_constant.CITY_NORMAL_PROPERTY: normal_property,
                    detector_constant.CITY_DETECTION_METHOD: detection_method
                }
            )
            index += 1
        return city_dict_list

    def _city_value(self, text):
        """
        Detects city from text by running TextDetection class.

        Args:
            text: message to process
        Returns:
            A tuple of two lists with first list containing the detected cities and second list containing their
            corresponding substrings in the given text. For example:

            For example:

                (['Mumbai'], ['bombay'])
        """
        city_list, original_list = self.text_detection_object.detect_entity(text, return_str=True)
        return city_list, original_list

    def _update_processed_text(self, city_dict_list):
        """
        Replaces detected cities with tag generated from entity_name used to initialize the object with

        A final string with all cities replaced will be stored in object's tagged_text attribute
        A string with all cities removed will be stored in object's processed_text attribute

        Args:
            original_city_strings: list of substrings of original text to be replaced with tag created from entity_name
        """
        for city_dict in city_dict_list:
            self.tagged_text = self.tagged_text.replace(city_dict[detector_constant.ORIGINAL_CITY_TEXT], self.tag)
            self.processed_text = self.processed_text.replace(city_dict[detector_constant.ORIGINAL_CITY_TEXT], '')

    def set_bot_message(self, bot_message):
        """
        Sets the object's bot_message attribute

        Args:
            bot_message: string
        """

        self.bot_message = bot_message

    def convert_city_dict_in_tuple(self, entity_dict_list):
        """
        This function takes the input as a list of dictionary and converts it into tuple which is
        for now the standard format  of individual detector function

        Attributes:
            entity_dict_list: List of dictionary containing the detected cities from text. It contains all the
            necessary information like original_text, value, how its detected and properties like from, to, via and
            normal

        Returns:
            Returns the tuple containing list of entity_values, original_text and detection method

            For example:

                (['Mumbai'], ['bombay'], ['message'])

        """
        entity_list, original_list, detection_list = [], [], []
        for entity_dict in entity_dict_list:
            entity_list.append(
                {
                    detector_constant.CITY_VALUE: entity_dict[detector_constant.CITY_VALUE],
                    detector_constant.CITY_FROM_PROPERTY: entity_dict[detector_constant.CITY_FROM_PROPERTY],
                    detector_constant.CITY_TO_PROPERTY: entity_dict[detector_constant.CITY_TO_PROPERTY],
                    detector_constant.CITY_VIA_PROPERTY: entity_dict[detector_constant.CITY_VIA_PROPERTY],
                    detector_constant.CITY_NORMAL_PROPERTY: entity_dict[detector_constant.CITY_NORMAL_PROPERTY],

                }
            )
            original_list.append(entity_dict[detector_constant.ORIGINAL_CITY_TEXT])
            detection_list.append(entity_dict[detector_constant.CITY_DETECTION_METHOD])
        return entity_list, original_list, detection_list

    def _city_model_detection(self):
        """
        This function calls run_model functionality from class Models() and verifies the values returned by it through
        datastore.
        If the cities provided by the model are present in the datastore, it sets the value to FROM_MODEL_VERIFIED
        else FROM_MODEL_NOT_VERFIED is set.

        For Example:
            Note:  before calling this method you need to call set_bot_message() to set a bot message.

            self.bot_message = 'Please help me with your departure city?'
            self.text = 'mummbai

            Output:
                [
                    {
                        'city':'mumbai',
                        'original_text': 'mummbai',
                        'from': true,
                        'to': false,
                        'via': false,
                        'normal': false
                        'detection_method': model_verified
                    }
                ]


        For Example:

            self.bot_message = 'Please help me with your departure city?'
            self.text = 'dehradun'

            Output:
                 [
                    {
                        'city':'dehradun',
                        'original_text': 'dehradun',
                        'from': true,
                        'to': false,
                        'via': false,
                        'normal': false
                        'detection_method': model_not_verified

                    }
                ]

                 Note: Dehradun is not present in out datastore so it will take original value as entity value.

        """
        city_dict_list = []
        model_object = Models()
        model_output = model_object.run_model(entity_type=model_constant.CITY_ENTITY_TYPE,
                                              bot_message=self.bot_message, user_message=self.text)
        for output in model_output:
            entity_value_list, original_text_list = self._city_value(text=output[model_constant.MODEL_CITY_VALUE])
            if entity_value_list:
                city_value = entity_value_list[0]
                detection_method = FROM_MODEL_VERIFIED
            else:
                city_value = output[model_constant.MODEL_CITY_VALUE]
                detection_method = FROM_MODEL_NOT_VERIFIED

            city_dict_list.append(
                {
                    detector_constant.CITY_VALUE: city_value,
                    detector_constant.ORIGINAL_CITY_TEXT: output[model_constant.MODEL_CITY_VALUE],
                    detector_constant.CITY_FROM_PROPERTY: output[model_constant.MODEL_CITY_FROM],
                    detector_constant.CITY_TO_PROPERTY: output[model_constant.MODEL_CITY_TO],
                    detector_constant.CITY_VIA_PROPERTY: output[model_constant.MODEL_CITY_VIA],
                    detector_constant.CITY_NORMAL_PROPERTY: output[model_constant.MODEL_CITY_NORMAL],
                    detector_constant.CITY_DETECTION_METHOD: detection_method
                }

            )
        return city_dict_list
