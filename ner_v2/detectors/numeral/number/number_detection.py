import importlib
import os

from ner_v2.detectors.base_detector import BaseDetector
from language_utilities.constant import ENGLISH_LANG
from ner_v2.detectors.temporal.constant import LANGUAGE_DATA_DIRECTORY


def get_lang_data_path(lang_code):
    data_directory_path = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep),
            lang_code,
            LANGUAGE_DATA_DIRECTORY
        )
    )
    return data_directory_path


class NumberDetector(BaseDetector):
    """Detects number from the text  and tags them.

    Detects all numbers in given text for all supported languages and replaces them by entity_name

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
    @staticmethod
    def get_supported_languages():
        """
        Return list of supported languages
        Returns:
            (list): supported languages
        """
        supported_languages = []
        cwd = os.path.dirname(os.path.abspath(__file__))
        cwd_dirs = [x for x in os.listdir(cwd) if os.path.isdir(os.path.join(cwd, x))]
        for _dir in cwd_dirs:
            if len(_dir.rstrip(os.sep)) == 2:
                supported_languages.append(_dir)
        return supported_languages

    def __init__(self, entity_name, language=ENGLISH_LANG):
        """Initializes a NumberDetector object

        Args:
            entity_name: A string by which the detected numbers would be replaced with on calling detect_entity()
        """
        # assigning values to superclass attributes
        self._supported_languages = self.get_supported_languages()
        super(NumberDetector, self).__init__(language)
        self.entity_name = entity_name
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.number = []
        self.original_number_text = []
        self.tag = '__' + self.entity_name + '__'
        self.min_digit = 1
        self.max_digit = 3
        self.language = language
        try:
            number_detector_module = importlib.import_module(
                'ner_v2.detectors.numeral.number.{0}.number_detection'.format(self.language))
            self.language_number_detector = number_detector_module.NumberDetector(entity_name=self.entity_name)

        except ImportError:
            standard_number_regex = importlib.import_module(
                'ner_v2.detectors.numeral.number.standard_number_regex'
            )
            self.language_number_detector = standard_number_regex.NumberDetector(
                entity_name=self.entity_name,
                data_directory_path=get_lang_data_path(self.language)
            )

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
        number_data = self.language_number_detector.detect_number()
        self.number = number_data[0]
        self.original_number_text = number_data[1]
        return number_data
