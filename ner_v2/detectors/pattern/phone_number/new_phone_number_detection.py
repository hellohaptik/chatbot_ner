# -*- coding: utf-8 -*-
from ner_v2.detectors.base_detector import BaseDetector
from ner_v2.detectors.numeral.number.number_detection import NumberDetector
from language_utilities.constant import ENGLISH_LANG
import re
import phonenumbers


class NewPhoneDetector(BaseDetector):
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
        super(NewPhoneDetector, self).__init__(language, country_code)
        self.language = language
        self.entity_name = entity_name
        self.text = ''
        self.phone = []
        self.original_phone_text = []
        self.country_code = country_code.upper()

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

        self.text = text
        self.phone, self.original_phone_text = [], []
        for match in phonenumbers.PhoneNumberMatcher(text, self.country_code):
            self.phone.append({"country_calling_code": str(match.number.country_code),
                               "phone_number": str(match.number.national_number)})
            self.original_phone_text.append(self.text[match.start:match.end])

        return self.phone, self.original_phone_text
