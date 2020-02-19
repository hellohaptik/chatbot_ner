from __future__ import absolute_import
import re
from ner_v1.detectors.base_detector import BaseDetector
from language_utilities.constant import ENGLISH_LANG


class PhoneDetector(BaseDetector):
    """Detects phone numbers in given text and tags them.

    Detects all phone numbers in given text and replaces them by entity_name

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected phone numbers would be replaced with on calling detect_entity()
        tagged_text: string with phone numbers replaced with tag defined by entity name
        processed_text: string with phone numbers detected removed
        phone: list of phone numbers detected
        original_phone_text: list to store substrings of the text detected as phone numbers
        tag: entity_name prepended and appended with '__'

    For Example:

        text = "Hi, can you send a text message to +919222222222"
        phone_detector = PhoneDetector("phone_number")
        phone_numbers, original_phone_numbers = phone_detector.detect_entity(text)
        phone_detector.tagged_text

            Output:
                 ' Hi, can you send a text message to __phone_number__ '

        phone_numbers, original_phone_numbers

            Output:
                (['+919222222222'], ['+919222222222'])

    Note:
        text and tagged_text will have a extra space prepended and appended after calling detect_entity(text)
    """

    def __init__(self, entity_name, source_language_script=ENGLISH_LANG, translation_enabled=False):
        """Initializes a PhoneDetector object

        Args:
            entity_name: A string by which the detected phone numbers would be replaced with on calling detect_entity()
            source_language_script: ISO 639 code for language of entities to be detected by the instance of this class
            translation_enabled: True if messages needs to be translated in case detector does not support a
                                 particular language, else False
        """
        # assigning values to superclass attributes
        self._supported_languages = [ENGLISH_LANG]
        super(PhoneDetector, self).__init__(source_language_script, translation_enabled)
        self.text = ''
        self.entity_name = entity_name
        self.tagged_text = ''
        self.processed_text = ''
        self.phone = []
        self.original_phone_text = []
        self.tag = '__' + self.entity_name + '__'

    @property
    def supported_languages(self):
        return self._supported_languages

    def _detect_phone(self):
        """Detects phone numbers in the self.text

        Returns:
            A tuple of two lists with first list containing the detected phone numbers and second list containing their
            corresponding substrings in the given text.

            For example:
                (['+919222222222'], ['+919222222222'])

        """
        phone_list = []
        original_list = []
        phone_list, original_list = self._detect_phone_format(phone_list, original_list)
        self._update_processed_text(original_list)
        return phone_list, original_list

    def detect_entity(self, text, **kwargs):
        """Detects phone numbers in the text string

        Args:
            text: string to extract entities from
            **kwargs: it can be used to send specific arguments in future.

        Returns:
            A tuple of two lists with first list containing the detected phone numbers and second list containing their
            corresponding substrings in the given text.

            For example:

                (['+919222222222'], ['+919222222222'])

            Additionally this function assigns these lists to self.phone and self.original_phone_text attributes
            respectively.

        """
        self.text = ' ' + text + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        phone_data = self._detect_phone()
        self.phone = phone_data[0]
        self.original_phone_text = phone_data[1]
        return phone_data

    def _detect_phone_format(self, phone_list=None, original_list=None):
        """
        Detects phone numbers from self.text conforming to formats defined by regex pattern.

        Args:
            phone_list: Optional, list to store detected phone numbers
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            phone numbers

        Returns:
            A tuple of two lists with first list containing the detected phone numbers and second list containing their
            corresponding substrings in the given text. For example:

            For example:

                (['+919222222222'], ['+919222222222'])
        """
        if phone_list is None:
            phone_list = []
        if original_list is None:
            original_list = []

        patterns = self._detect_mobile_number_pattern(self.processed_text.lower())

        for pattern in patterns:
            original = pattern
            phone = pattern
            phone_list.append(phone)
            original_list.append(original)
        return phone_list, original_list

    def _detect_mobile_number_pattern(self, text):
        """
        Detects phone numbers from text that match the defined regex pattern

        Args:
            text: text string to extract entities from

        Returns:
            A list of substrings of text that match the defined regex pattern

            For example:

                (['+919222222222', '919999999999'])
        """
        return re.findall(r'\s((?:(?:\+|0{0,2})91(?:\s*[\-]\s*)?|[0]?)?[6789]\d{9})\b', text)

    def _update_processed_text(self, original_phone_strings):
        """
        Replaces detected phone numbers with tag generated from entity_name used to initialize the object with

        A final string with all phone numbers replaced will be stored in object's tagged_text attribute
        A string with all phone numbers removed will be stored in object's processed_text attribute

        Args:
            original_phone_strings: list of substrings of original text to be replaced with tag created
                                    from entity_name
        """
        for detected_text in original_phone_strings:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')
