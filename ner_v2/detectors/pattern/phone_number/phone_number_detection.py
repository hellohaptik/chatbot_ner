# -*- coding: utf-8 -*-
from ner_v2.detectors.base_detector import BaseDetector
from ner_v2.detectors.numeral.number.number_detection import NumberDetector
from ner_v2.detectors.numeral.utils import get_number_from_number_word
from language_utilities.constant import ENGLISH_LANG
import collections
import re
import phonenumbers

NumberVariant = collections.namedtuple('NumberVariant', ['scale', 'increment'])


def create_number_word_dict():
    number_word_dictionary = {'one': NumberVariant(scale=1, increment=1),
                              'two': NumberVariant(scale=1, increment=2),
                              'three': NumberVariant(scale=1, increment=3),
                              'four': NumberVariant(scale=1, increment=4),
                              'five': NumberVariant(scale=1, increment=5),
                              'six': NumberVariant(scale=1, increment=6),
                              'seven': NumberVariant(scale=1, increment=7),
                              'eight': NumberVariant(scale=1, increment=8),
                              'nine': NumberVariant(scale=1, increment=9),
                              'zero': NumberVariant(scale=1, increment=0)}
    return number_word_dictionary


class PhoneDetector(BaseDetector):
    """
    This method is used to detect phone numbers present in text. The phone detector takes into
    consideration domestic as well as international phone numbers.

    Attributes:
         text(str): string provided to extract phone numbers detection
         phone (list): list of detected entity values
         original_phone_text (list): list to store substrings of the text detected as phone numbers
    """

    def __init__(self, entity_name, language=ENGLISH_LANG, locale='en-IN'):
        # Todo: Change default from india to get it from the bot.
        """
        Args:
            entity_name (str): A string by which the detected numbers would be replaced with
            on calling detect_entity()
            language (str, optional): language code of number text, defaults to 'en'
            locale(str, optional): locale of the country from which you are dialing. Ex: 'en-IN'
        """
        self._supported_languages = NumberDetector.get_supported_languages()
        super(PhoneDetector, self).__init__(language, locale)
        self.language = language
        self.entity_name = entity_name
        self.locale = locale
        self.text = ''
        self.phone = []
        self.original_phone_text = []
        self.country_code = ''
        self.number_word_dict = create_number_word_dict()

    @property
    def supported_languages(self):
        """
        This method returns the list of languages supported by entity detectors
        Return:
             list: List of ISO 639 codes of languages supported by subclass/detector
        """
        return self._supported_languages

    def get_country_code_from_locale(self):
        """
        This method sets self.country_code from given locale
        """
        regex_pattern = re.compile('[-_](.*$)', re.U)
        match = regex_pattern.findall(self.locale)
        self.country_code = match[0].upper()

    def convert_words_to_numbers(self, text):
        """
        :param text: user message
        :return: converted user message with words replaced with numbers
        """
        numbers_dict = get_number_from_number_word(text, self.number_word_dict)
        val = numbers_dict[0]
        word = numbers_dict[1]
        converted_sentence = text
        x = zip(val, word)
        unique_x = []
        for i in x:
            if i not in unique_x:
                unique_x.append(i)

        for j in unique_x:
            pattern = re.compile(j[1], re.U)
            converted_sentence = pattern.sub(string=converted_sentence, repl=str(j[0]))

        converted_sentence = re.sub(r'(double)(\s+)(\d)', r'\3\3', converted_sentence)
        converted_sentence = re.sub(r'(triple)(\s+)(\d)', r'\3\3\3', converted_sentence)

        while re.search(r'(\d+)(\s+)(\d+)', converted_sentence):
            converted_sentence = re.sub(r'(\d+)(\s+)(\d+)', r'\1\3', converted_sentence)
        return converted_sentence

    def get_correct_original_text(self, original_text):
        pattern = ''
        for text_match in original_text:
            pattern += ('(^.*)' + '(?:' + text_match + ')')
        pattern += '(.*$)'
        first_pattern = re.compile(pattern, re.U)
        first_matches = first_pattern.findall(self.text)

    def detect_entity(self, text, **kwargs):
        """Detects phone numbers in the text string

        Args:
            text: string to extract entities from
            **kwargs: it can be used to send specific arguments in future.

        Returns:

            self.phone (list): list consisting the detected phone numbers and their country calling codes
            self.original_phone_text (list): list containing their corresponding substrings in the original message.

        Examples:

        text = 'call +1 (408) 912-6172'
        p = PhoneDetector(entity_name='phone_number', language='en', locale='en-US')
        p.detect_entity(text=text)
        ([{'country_calling_code':'1', phone_number':'4089126172'} ],
         [u'+1 (408) 912-6172'])

        text = '+९१ ९८१९९८३१३२ पर कॉल करें और संदेश ९८२०३३४४१६ पर कॉल करें'
        p = PhoneDetector(entity_name='phone_number', language='hi', locale='en-IN')
        p.detect_entity(text=text)
        ([{'country_calling_code':'91', phone_number':'9819983132'}
        ,{ 'country_calling_code':'91', phone_number:'9820334416'} ],
        [u'+९१ ९८१९९८३१३२', u'+९१ ९८१९९८३१३२'])

        """
        self.get_country_code_from_locale()
        original_text = text
        if self.language == 'en':
            self.text = self.convert_words_to_numbers(text)
        else:
            self.text = text
        self.phone, self.original_phone_text = [], []
        for match in phonenumbers.PhoneNumberMatcher(self.text, self.country_code):
            self.phone.append({"country_calling_code": str(match.number.country_code),
                               "phone_number": str(match.number.national_number)})
            self.original_phone_text.append(self.text[match.start:match.end])
        # if original_text != self.text:
        #     self.get_correct_original_text(original_text)
        return self.phone, self.original_phone_text
