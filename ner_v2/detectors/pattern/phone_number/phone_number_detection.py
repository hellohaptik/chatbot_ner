from ner_v2.detectors.base_detector import BaseDetector
from ner_v2.detectors.numeral.number.number_detection import NumberDetector
from language_utilities.constant import ENGLISH_LANG


class PhoneDetector(BaseDetector):

    def __init__(self, entity_name, language=ENGLISH_LANG):
        super(PhoneDetector, self).__init__(language)
        self._supported_languages = NumberDetector.get_supported_languages()
        self.language = language
        self.number_detector = NumberDetector(entity_name=entity_name, language=self.language)
        self.entity_name = entity_name
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.number = []
        self.original_number_text = []
        self.tag = '__' + self.entity_name + '__'

    @property
    def supported_languages(self):
        return self._supported_languages

    def get_number(self, text):
        self.number_detector.set_min_max_digits(min_digit=8, max_digit=14)
        self.number_detector.detect_entity(text=text)
        number_list, original_number_list = self.number_detector.detect_entity(text=text)
        return number_list, original_number_list

    def detect_entity(self, text, **kwargs):
        return self.get_number(text=text)
