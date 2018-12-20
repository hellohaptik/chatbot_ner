from ner_v2.detectors.base_detector import BaseDetector
from ner_v2.detectors.numeral.number.number_detection import NumberDetector
from language_utilities.constant import ENGLISH_LANG
import re


class PhoneDetector(BaseDetector):
    def __init__(self, entity_name, language=ENGLISH_LANG):

        self.number_detector = NumberDetector(language=language, entity_name=entity_name)
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
        return self._supported_languages

    def detect_entity(self, text, **kwargs):
        self.text = text.decode('utf-8')
        self.processed_text = self.text
        self.tagged_text = self.text

        self.number_detector.set_min_max_digits(8, 14)
        phone_number_original_list = self.get_number_regex()

        original_phone_list = [p[0] for p in phone_number_original_list]
        clean_phone_list = [self.clean_phone_number(p) for p in original_phone_list]

        self.phone, self.original_phone_text = self.get_number(original_phone_list=original_phone_list,
                                                               clean_phone_list=clean_phone_list)

        self.get_tagged_text()

        return self.phone, self.original_phone_text

    def get_number(self, clean_phone_list, original_phone_list):
        phone = []
        original_phone_text = []

        for each, each_i in zip(clean_phone_list, original_phone_list):
            detected_number = self.number_detector.detect_entity(each)[0]
            if detected_number:
                phone.append(detected_number[0]['value'])
                original_phone_text.append(each_i)

        return phone, original_phone_text

    def clean_phone_number(self, number):
        clean_regex = re.compile('[\+()\sext]+')
        return clean_regex.sub(string=number, repl='')

    def get_number_regex(self):
        phone_number_regex = re.compile(
            r'((?:\(?\+(\d{1,2})\)?[\s\-\.]*)?((?=[\-\d()\s\.]{9,16}'
            r'(?:\s*e?xt?\.?\s*(?:\d{1,20}))?(?:[^\d]+|$))'
            r'(?:[\d(]{1,20}(?:[\-)\s\.]*\d{1,20}){0,20}){1,20})'
            r'(?:\s*e?xt?\.?\s*(\d{1,20}))?)', re.U)
        phone_number_list = phone_number_regex.findall(self.text)
        return phone_number_list

    def get_tagged_text(self):
        for detected_text in self.original_phone_text:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')
