from __future__ import absolute_import
import re
from word2number import w2n
from lib.nlp.const import nltk_tokenizer
from ner_v1.constant import DIGIT_UNITS, NUMERIC_VARIANTS
from ner_v1.detectors.base_detector import BaseDetector
from language_utilities.constant import ENGLISH_LANG


class NumberDetector(BaseDetector):
    """Detects number from the text  and tags them.

    Detects all numbers in given text and replaces them by entity_name

    For Example:

        number_detector = NumberDetector("number_of_units")
        message = "I want to purchase 30 units of mobile and 40 units of Television"
        numbers, original_numbers = number_detector.detect_entity(message)
        tagged_text = number_detector.tagged_text
        print numbers, ' -- ', original_numbers
        print 'Tagged text: ', tagged_text

         >> ['30', '40'] -- ['30', '40']
            Tagged text: I want to purchase 30 units of mobile and 40 units of Television'


        number_detector = NumberDetector("number_of_people")
        message = "Can you please help me to book tickets for 3 people"
        numbers, original_numbers = number_detector.detect_entity(message)
        tagged_text = number_detector.tagged_text

        print numbers, ' -- ', original_numbers
        print 'Tagged text: ', tagged_text

         >> ['3'] -- ['for 3 people']
            Tagged text: Can you please help me to book tickets __number_of_people__

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected number would be replaced with on calling detect_entity()

        tagged_text: string with numbers replaced with tag defined by entity name
        processed_text: string with numbers detected removed
        number: list of numbers detected
        original_number_text: list to store substrings of the text detected as numbers
        tag: entity_name prepended and appended with '__'
        min_digit: minimum digit that a number can take
        max_digit: maximum digit that a number can take

    Note:
        text and tagged_text will have a extra space prepended and appended after calling detect_entity(text)
        Currently, there are two detection logics for detecting numbers from text one to detect number of people
        and other any number. If we want detect number of people entity_name should be set to 'number_of_people'
        else any name can be passed as entity_name.
        We can detect numbers from 1 digit to 3 digit.
    """
    def __init__(self, entity_name, source_language_script=ENGLISH_LANG, translation_enabled=False):
        """Initializes a NumberDetector object

        Args:
            entity_name: A string by which the detected numbers would be replaced with on calling detect_entity()
            source_language_script: ISO 639 code for language of entities to be detected by the instance of this class
            translation_enabled: True if messages needs to be translated in case detector does not support a
                                 particular language, else False
        """
        # assigning values to superclass attributes
        self._supported_languages = [ENGLISH_LANG]
        super(NumberDetector, self).__init__(source_language_script, translation_enabled)
        self.entity_name = entity_name
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.number = []
        self.original_number_text = []
        self.tag = '__' + self.entity_name + '__'
        self.min_digit = 1
        self.max_digit = 3
        self.task_dict = {
            'number_of_people': self._detect_number_of_people_format,
            'number_of_ticket': self._detect_number_of_people_format,
            'no_of_guests': self._detect_number_of_people_format,
            'no_of_adults': self._detect_number_of_people_format,
            'travel_no_of_people': self._detect_number_of_people_format,
            'Default': self._detect_number_format
        }

    @property
    def supported_languages(self):
        return self._supported_languages

    def detect_entity(self, text, **kwargs):
        """Detects numbers in the text string

        Args:
            text: string to extract entities from
            **kwargs: it can be used to send specific arguments in future.

        Returns:
            A tuple of two lists with first list containing the detected numbers and second list containing their
            corresponding substrings in the original message.

            For example:

                (['3'], ['3 people'])

            Additionally this function assigns these lists to self.number and self.original_number_text attributes
            respectively.

        """
        self.text = ' ' + text.lower() + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        number_data = self._detect_number()
        self.number = number_data[0]
        self.original_number_text = number_data[1]
        return number_data

    def _detect_number(self):
        """Detects numbers in the self.text

        Returns:
            A tuple of two lists with first list containing the detected numbers and second list containing their
            corresponding substrings in the original message.

            For example:
                (['3'], ['for 3 people'])

        """
        number_list, original_list = self.task_dict.get(self.entity_name, self.task_dict['Default'])()
        self._update_processed_text(original_list)
        return number_list, original_list

    def _detect_number_format(self):
        """Detects any numbers from text
        This is a default function which will be called when we want to detect the number from the text

        Returns:
            A tuple of two lists with first list containing the detected numbers and second list containing their
            corresponding substrings in the original message.

            For example:
                input: "I want to purchase 30 units of mobile and 40 units of Television"
                output: (['30', '40'], ['30','40'])

        Note: By default we detect numbers from 1 digit to 3 digit
        """
        number_list = []
        original_list = []
        patterns = re.findall(r'\s([0-9]{{{0},{1}}})[\s|,]'.format(self.min_digit, self.max_digit),
                              self.processed_text.lower())
        for pattern in patterns:
            number_list.append(pattern)
            original_list.append(pattern)
        word2number_number_list, word2number_original_list = self._detect_numerals()
        number_list = number_list + word2number_number_list
        original_list = original_list + word2number_original_list
        return number_list, original_list

    def _detect_number_of_people_format(self):
        """Detects any numbers from text
        This is a function which will be called when we want to detect the number of persons from the text

        Returns:
            A tuple of two lists with first list containing the detected numbers and second list containing their
            corresponding substrings in the original message.

            For example:
                input text: "Can you please help me to book tickets for 3 people"
                output: (['3'], ['for 3 people'])

        Note: Currently, we can detect numbers from 1 digit to 3 digit. This function will be enabled only
        if entity_name is set to  'number_of_people'
        """
        number_list = []
        original_list = []
        patterns = re.findall(
            r'\s((fo?r)*\s*([0-9]{{{0},{1}}})\s*(ppl|people|passengers?|travellers?|persons?|pax|adults?)*)\s'.format(
                self.min_digit, self.max_digit),
            self.processed_text.lower()
        )
        for pattern in patterns:
            number_list.append(pattern[2])
            original_list.append(pattern[0])
        word2number_number_list, word2number_original_list = self._detect_numerals()
        number_list = number_list + word2number_number_list
        original_list = original_list + word2number_original_list
        return number_list, original_list

    def _update_processed_text(self, original_number_strings):
        """
        Replaces detected numbers with self.tag generated from entity_name used to initialize the object with

        A final string with all numbers replaced will be stored in self.tagged_text attribute
        A string with all numbers removed will be stored in self.processed_text attribute

        Args:
            original_number_strings: list of substrings of original text to be replaced with self.tag
        """
        for detected_text in original_number_strings:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')

    def set_min_max_digits(self, min_digit, max_digit):
        """
        Update min max digit

        Args:
            min_digit (int): min digit
            max_digit (int): max digit
        """
        self.min_digit = min_digit
        self.max_digit = max_digit

    def _detect_numerals(self):
        """
        1. Detects numerals from the given text
        2. Makes a call to convert_numerals_to_numbers which return a tuple consisting of two lists
            a.number_list consisting of numbers obtained from detected numerals
            b.original_list consisting of original detected numerals

        Returns:
            (number_list, original_list) (tuple)
            number_list (list): a list consisting of numbers obtained from detected numerals
            original_list (list): a list consisting of detected numerals

        Example:
            self.text = "My favorite number is seven but jersey number is twenty five"
            >>print(detect_numerals())
            (['7', '25'], ['seven', 'twenty five'])
        """
        original_list = []
        temp_str = ''
        tokenizer = nltk_tokenizer

        for word in tokenizer.tokenize(self.text.lower()):
            if word in NUMERIC_VARIANTS:
                temp_str = (temp_str + ' ' + word).strip()
            else:
                if temp_str.startswith('and') or (temp_str.endswith('and') and not temp_str.endswith('thousand')):
                    temp_str = temp_str.replace('and', '')
                original_list.append(temp_str.strip())
                temp_str = ''
        if temp_str.startswith('and') or (temp_str.endswith('and') and not temp_str.endswith('thousand')):
            temp_str = temp_str.replace('and', '')
        original_list.append(temp_str.strip())
        original_list = [w.strip() for w in original_list if w.strip()]

        _original_list = []
        for part in original_list:
            if all(unit in DIGIT_UNITS for unit in part.split()):
                _original_list.extend(part.split())
            else:
                _original_list.append(part)
        original_list = _original_list
        return self._convert_numerals_to_numbers(original_list)

    def _convert_numerals_to_numbers(self, original_list):
        """
        It converts the detected numerals using the python package word2number to numbers.
        word2number takes input as numerals or number and returns the number.

        Args:
            original_list (list): consists of list of numerals detected from given text.

        Returns:
            (number_list, original_list) (tuple)
            number_list (list): a list consisting of numbers obtained from detected numerals
            final_original_list (list): a list consisting of detected numerals

        Example:
            original_list = ['seven', 'twenty five']
            >>print(convert_numerals_to_numbers())
            (['7', '25'], ['seven', 'twenty five'])
        """
        final_original_list = []
        number_list = []
        for original_numbers in original_list:
            suggestion = str(w2n.word_to_num(str(original_numbers)))
            if self.max_digit >= len(suggestion) >= self.min_digit:
                number_list.append(suggestion)
                final_original_list.append(original_numbers)
        return number_list, final_original_list
