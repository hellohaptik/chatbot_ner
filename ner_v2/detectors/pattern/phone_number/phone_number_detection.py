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

    def __init__(self, entity_name, language=ENGLISH_LANG, country_code="IN"):
        # Todo: Change default from india to get it from the bot.
        """
        Args:
            entity_name (str): A string by which the detected numbers would be replaced with
            on calling detect_entity()
            language (str, optional): language code of number text, defaults to 'en'
            country_code(str, optional): country code of the country from which you are using
        """
        self._supported_languages = NumberDetector.get_supported_languages()
        super(PhoneDetector, self).__init__(language, country_code)
        self.language = language
        self.entity_name = entity_name
        self.text = ''
        self.phone = []
        self.original_phone_text = []
        self.country_code = country_code.upper()
        self.number_word_dict = create_number_word_dict()

    @property
    def supported_languages(self):
        """
        This method returns the list of languages supported by entity detectors
        Return:
             list: List of ISO 639 codes of languages supported by subclass/detector
        """
        return self._supported_languages

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

    def detect_entity(self, text, **kwargs):
        """Detects phone numbers in the text string

        Args:
            text: string to extract entities from
            **kwargs: it can be used to send specific arguments in future.

        Returns:

            self.phone (list): list consisting the detected phone numbers
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

        if self.language == 'en':
            self.text = self.convert_words_to_numbers(text)
        else:
            self.text = text
        self.phone, self.original_phone_text = [], []
        for match in phonenumbers.PhoneNumberMatcher(self.text, self.country_code):
            self.phone.append({"country_calling_code": str(match.number.country_code),
                               "phone_number": str(match.number.national_number)})
            self.original_phone_text.append(self.text[match.start:match.end])

        return self.phone, self.original_phone_text
