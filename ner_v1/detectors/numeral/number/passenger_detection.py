from __future__ import absolute_import
import re
from ner_v1.detectors.base_detector import BaseDetector
from ner_v1.detectors.numeral.number.number_detection import NumberDetector
from language_utilities.constant import ENGLISH_LANG


class PassengerDetector(BaseDetector):
    """Detects passenger count from the text and tags them.

    Detects all passenger count in given text and replaces them by entity_name

    For Example:

        passenger_detector = PassengerDetector("no_of_adults")
        message = "Can you please help me to book tickets for 3 people"
        passenger_count, original_passenger_string = passenger_detector.detect_entity(message)
        tagged_text = passenger_detector.tagged_text

        print passenger_count, ' -- ', original_passenger_string
        print 'Tagged text: ', tagged_text

         >> ['3']  --  ['3']
            Tagged text:   Can you please help me to book tickets for __no_of_adults__ people

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected passenger count would be replaced with on calling detect_entity()
        tagged_text: string with passenger count replaced with tag defined by entity name
        processed_text: string with detected passenger count removed
        passenger: list of passenger count detected
        original_passenger_text: list to store substrings of the text detected as passenger count
        tag: entity_name prepended and appended with '__'
        bot_message: str, set as the outgoing bot text/message

    Note:
        text and tagged_text will have a extra space prepended and appended after calling detect_entity(text)
    """
    def __init__(self, entity_name, source_language_script=ENGLISH_LANG, translation_enabled=False):
        """Initializes a PassengerDetector object

        Args:
            entity_name: A string by which the detected passenger count would be replaced with on calling
                        detect_entity()
            source_language_script: ISO 639 code for language of entities to be detected by the instance of this class
            translation_enabled: True if messages needs to be translated in case detector does not support a
                                 particular language, else False
        """
        # assigning values to superclass attributes
        self._supported_languages = [ENGLISH_LANG]
        super(PassengerDetector, self).__init__(source_language_script, translation_enabled)
        self.text = ''
        self.entity_name = entity_name
        self.tagged_text = ''
        self.processed_text = ''
        self.passenger = []
        self.original_passenger_text = []
        self.tag = '__' + self.entity_name + '__'
        self.bot_message = None
        self.number_detection = NumberDetector('numeric_range')
        self.number_detection.set_min_max_digits(min_digit=1, max_digit=2)

    @property
    def supported_languages(self):
        return self._supported_languages

    def detect_entity(self, text, **kwargs):
        """
        Detects passenger count in the text string

        Args:
            text (str): string to extract entities from
            **kwargs: it can be used to send specific arguments in future.

        Returns:
            (passenger_list, original_list) (tuple)
            passenger_list (list): a list consisting of passenger count obtained from text
            original_list (list): a list consisting of corresponding substrings of detected entities in the given text

            For example:

                (['3'], ['3'])
        """
        self.text = ' ' + text + ' '
        self.processed_text = self.text.lower()
        self.tagged_text = self.text
        passenger_data = self._detect_passenger_count()
        self.passenger = passenger_data[0]
        self.original_passenger_text = passenger_data[1]
        return passenger_data

    def _detect_passenger_count(self):
        """
        Detects passenger count from text

        Returns:
            (passenger_list, original_list) (tuple)
            passenger_list (list): a list consisting of passenger count obtained from text
            original_list (list): a list consisting of corresponding substrings of detected entities in the given text
        """
        original_list = []
        passenger_list = []
        if self.entity_name == 'no_of_adults':
            passenger_list, original_list = self._detect_adult_count()
            self._update_processed_text(original_list)
        elif self.entity_name == 'no_of_childs':
            passenger_list, original_list = self._detect_child_count()
            self._update_processed_text(original_list)
        elif self.entity_name == 'no_of_infants':
            passenger_list, original_list = self._detect_infant_count()
            self._update_processed_text(original_list)
        return passenger_list, original_list

    def _detect_adult_count(self):
        """
        Detects adult count from text

        Returns:
            (no_of_adults, original_list) (tuple)
            no_of_adults (list): a list consisting of no_of_adults obtained from text
            original_list (list): a list consisting of corresponding substrings of detected entities in the given text
        """
        no_of_adults = []
        original_list = []
        regex_adult = re.compile(r'((\w*\s*\w+)\s*(adult|people|passenger|log|person|ppl|'r'traveller))')
        patterns = regex_adult.findall(self.processed_text)
        if not patterns and self.bot_message:
            adult_regex = re.compile(r'((number|no|no.|how many)\W*(of)?\W*(adult|passenger|people|person|ppl| '
                                     r'traveller))')
            if adult_regex.search(self.bot_message) is not None:
                patterns = re.findall(r'([\w]+)', self.processed_text)

                for pattern in patterns:
                    number_list, original_number_list = self.number_detection.detect_entity(pattern.strip())
                    if number_list:
                        no_of_adults.append(number_list[0])
                        original_list.append(original_number_list[0])
        elif patterns:
            for pattern in patterns:
                number_list, original_number_list = self.number_detection.detect_entity(pattern[1].strip())
                if number_list:
                    no_of_adults.append(number_list[0])
                    original_list.append(original_number_list[0])
        return no_of_adults, original_list

    def _detect_child_count(self):
        """
        Detects children count from text

        Returns:
            (no_of_childs, original_list) (tuple)
            no_of_childs (list): a list consisting of no_of_childs obtained from text
            original_list (list): a list consisting of corresponding substrings of detected entities in the given text
        """
        no_of_childs = []
        original_list = []
        regex_child = re.compile(r'((\w*\s*\w+)\s*(child|children|kid))')
        patterns = regex_child.findall(self.processed_text)
        if not patterns and self.bot_message:
            child_regex = re.compile(r'((number|no|no.|how many)\W*(of)?\W*(child|children|kid))')
            if child_regex.search(self.bot_message) is not None:
                patterns = re.findall(r'([\w]+)', self.processed_text)
                for pattern in patterns:
                    number_list, original_number_list = self.number_detection.detect_entity(pattern.strip())
                    if number_list:
                        no_of_childs.append(number_list[0])
                        original_list.append(original_number_list[0])
        elif patterns:
            for pattern in patterns:
                number_list, original_number_list = self.number_detection.detect_entity(pattern[1].strip())
                if number_list:
                    no_of_childs.append(number_list[0])
                    original_list.append(original_number_list[0])
        return no_of_childs, original_list

    def _detect_infant_count(self):
        """
        Detects infant count from text

        Returns:
            (no_of_infants, original_list) (tuple)
            no_of_infants (list): a list consisting of no_of_infants obtained from text
            original_list (list): a list consisting of corresponding substrings of detected entities in the given text
        """
        no_of_infants = []
        original_list = []
        regex_infant = re.compile(r'((\w*\s*\w+)\s*(infant|bachcha))')
        patterns = regex_infant.findall(self.processed_text)
        if not patterns and self.bot_message:
            infant_regex = re.compile(r'((number|no|no.|how many)\W*(of)?\W*(infant|baby))')
            if infant_regex.search(self.bot_message) is not None:
                patterns = re.findall(r'([\w]+)', self.processed_text)
                for pattern in patterns:
                    number_list, original_number_list = self.number_detection.detect_entity(pattern.strip())
                    if number_list:
                        no_of_infants.append(number_list[0])
                        original_list.append(original_number_list[0])
        elif patterns:
            for pattern in patterns:
                number_list, original_number_list = self.number_detection.detect_entity(pattern[1].strip())
                if number_list:
                    no_of_infants.append(number_list[0])
                    original_list.append(original_number_list[0])
        return no_of_infants, original_list

    def _update_processed_text(self, original_passenger_strings):
        """
        Replaces detected passenger count with self.tag generated from entity_name used to initialize the object with

        A final string with all passenger count replaced will be stored in self.tagged_text attribute
        A string with all passenger count removed will be stored in self.processed_text attribute

        Args:
            original_passenger_strings: list of substrings of original text to be replaced with self.tag
        """
        for detected_text in original_passenger_strings:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')

    def set_bot_message(self, bot_message):
        """
        Sets the object's bot_message attribute

        Args:
            bot_message (str): previous message that is sent by the bot
        """
        self.bot_message = bot_message
