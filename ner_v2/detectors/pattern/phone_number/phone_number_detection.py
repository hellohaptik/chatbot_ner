# -*- coding: utf-8 -*-
from ner_v2.detectors.base_detector import BaseDetector
from ner_v2.detectors.numeral.number.number_detection import NumberDetector
from language_utilities.constant import ENGLISH_LANG
import re


class PhoneDetector(BaseDetector):
    """
    This method is used to detect phone numbers present in text. The phone detector takes into
    consideration domestic as well as international phone numbers.

    Attributes:
         text(str): string provided to extract phone numbers detection
         tagged_text (str): string in which the detected phone numbers are replaced by __<entity_name>__
         processed_text (str): string in which the detected phone numbers are removed
         phone (list): list of detected entity values
         original_phone_text (list): list to store substrings of the text detected as phone numbers
         tag (str): entity_name prepended and appended with '__'
    """
    def __init__(self, entity_name, language=ENGLISH_LANG):
        """
        Args:
            entity_name (str): A string by which the detected numbers would be replaced with
            on calling detect_entity()
            language (str, optional): language code of number text, defaults to 'en'
        """
        self._supported_languages = NumberDetector.get_supported_languages()
        super(PhoneDetector, self).__init__(language)
        self.language = language
        self.entity_name = entity_name
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.phone = []
        self.original_phone_text = []
        self.tag = '__' + self.entity_name + '__'

    @property
    def supported_languages(self):
        """
        This method returns the list of languages supported by entity detectors
        Return:
             list: List of ISO 639 codes of languages supported by subclass/detector
        """
        return self._supported_languages

    def detect_entity(self, text, **kwargs):
        """Detects phone numbers in the text string

        Args:
            text: string to extract entities from
            **kwargs: it can be used to send specific arguments in future.

        Returns:

            self.phone (list): list consisting the detected phone numbers in the same order as mentioned in message
            self.original_phone_text (list): list containing their corresponding substrings in the original message.

        Examples:

        text = 'call +1 (408) 912-6172 and send 100rs to 9920441344'

        p = PhoneDetector(entity_name='phone_number', language='en')
        p.detect_entity(text=text)
        (['14089126172', '9920441344'], [u'+1 (408) 912-6172', u'9920441344'])

        text = '+९१ ९८१९९८३१३२ पर कॉल करें और संदेश ९८२०३३४४१६ पर कॉल करें'
        p = PhoneDetector(entity_name='phone_number', language='hi')
        p.detect_entity(text=text)
        (['919819983132', '9820334416'],[u'+९१ ९८१९९८३१३२', u'+९१ ९८१९९८३१३२'])

        """

        self.text = text
        self.processed_text = self.text
        self.tagged_text = self.text

        phone_number_original_list = self.get_number_regex()

        original_phone_texts = [p[0] for p in phone_number_original_list]
        self.original_phone_text = self.check_length(original_phone_texts=original_phone_texts)
        clean_phone_list = [self.clean_phone_number(p) for p in self.original_phone_text]
        self.phone = [self.get_number(phone) for phone in clean_phone_list]
        self.get_tagged_text()

        return self.phone, self.original_phone_text

    def get_digit_length(self, text):
        return len(re.findall(pattern='\d', string=text, flags=re.U))

    def check_length(self, original_phone_texts):
        """
        This method is used to handle the corner case where consecutive numbers are present with
        space within them.
        Args:
            original_phone_texts (list): list of text substrings detected by the regex

        Returns:
            phone_number_list (list): list of phone numbers splitting based on length

        Examples:
             original_phone_texts = ['9820334415 91 9920441388', '9820551388982347']
             check_length(original_phone_texts=original_phone_texts)
             >> ['9820334415', '91 9920441388']
        """
        phone_number_list_1, phone_number_list2 = [], []

        for original_phone_text in original_phone_texts:

            if self.get_digit_length(text=original_phone_text) > 13:
                phone_parts = original_phone_text.split()
                visited = [0 for i in range(len(phone_parts))]

                for i in range(len(phone_parts)):
                    temp = ''
                    appended_parts = []

                    for j in range(i, len(phone_parts)):
                        if visited[j] == 0:
                            temp = temp + ' ' + phone_parts[j]
                            appended_parts.append(j)

                            if 13 >= self.get_digit_length(text=temp) > 7:
                                phone_number_list_1.append(temp.strip())
                                for m in appended_parts:
                                    visited[m] = 1
                                break
            else:
                phone_number_list2.append(original_phone_text)
        phone_number_list_1.extend(phone_number_list2)
        return phone_number_list_1

    def get_number(self, phone):
        """
        This method is used to convert phone numbers in language scripts other than English
        to the English
        Args:
            phone (str): The string phone number which is detected and cleaned

        Returns:
            phone (str): The string phone number converted to English script

        Examples:
            phone = u'९१९८१९९८३१३२'
            get_number(phone=phone)
            '919819983132'
        """
        phone_length = len(phone)
        phone = str(int(phone))

        if phone_length != len(phone):
            phone = phone.zfill(phone_length)

        return phone

    def clean_phone_number(self, number):
        """
        This method is used to clean the detected phone number.
        Args:
            number (str): The original substring which is detected and is required for cleaning

        Returns:
            number (str): The number post cleaning
        """
        # Remove (), -, whistespace, +
        clean_regex = re.compile('([()\-\s\+]+)', re.U)
        number = clean_regex.sub(string=number, repl='')
        return number

    def get_number_regex(self):

        """
        This method is used to detect the phone number patterns from the provided text
        Returns:
            phone_number_list (list): list of patterns detected from the regex pattern

            (each pattern: (complete original text, area code, number))
            (we further utitlize only the complete original text)
        Example:
            p = PhoneDetector(entity_name='phone_number', language='hi')
            text = u'Set a reminder on +1 (408) 912-6172'
            p.text = text
            p.get_number_regex()

            [(u'+1 (408) 912-6172', u'1', u'(408) 912-6172'),
             (u'+91 9820334416', u'91', u'9820334416'),
            (u'022 26129857', u'022', u'26129857')]
        """
        phone_number_regex = re.compile(
            r'((?:\(?\+(\d{1,2})\)?[\s\-\.]*)?((?=[\-\d()\s\.]{10,16}(?:[^\d]+|$))'
            r'(?:[\d(]{1,20}(?:[\-)\s\.]*\d{1,20}){0,20}){1,20}))', re.U)

        phone_number_list = phone_number_regex.findall(self.text)
        return phone_number_list

    def get_tagged_text(self):
        """
        Replaces detected phone numbers with tag generated from entity_name used to initialize the object with

        A final string with all phone numbers replaced will be stored in object's tagged_text attribute
        A string with all phone numbers removed will be stored in object's processed_text attribute

        """
        for detected_text in self.original_phone_text:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')
