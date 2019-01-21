from __future__ import absolute_import

import importlib
import os

from ner_v2.detectors.base_detector import BaseDetector
from language_utilities.constant import ENGLISH_LANG
from ner_v2.detectors.utils import get_lang_data_path


class NumberRangeDetector(BaseDetector):
    """Detects min and max value of number from number range text.

    Detects all number range in given text for all supported languages and replaces them by entity_name

    For Example:

        number_range_detector = NumberRangeDetector("number_of_units")
        message = "I want to purchase between 200 to 300 units of t-shirts"
        number_ranges, original_numbers = number_range_detector.detect_entity(message)
        tagged_text = number_range_detector.tagged_text
        print number_ranges, ' -- ', original_numbers
        print 'Tagged text: ', tagged_text

         >> [{'min_value': 200, 'max_value': 300, 'unit': None}] -- ['200 to 300']
            Tagged text: I want to purchase between __number_of_units__ units of t-shirts'


        number_range_detector = NumberRangeDetector("number_of_people")
        message = "He has invited more than 3000 guests in his marriage"
        number_ranges, original_numbers = number_range_detector.detect_entity(message)
        tagged_text = number_detector.tagged_text

        print number_ranges, ' -- ', original_numbers
        print 'Tagged text: ', tagged_text

        >> [{'min_value': 3000, 'max_value': None 'unit': 'people'}] -- ['more than 3000 guests']
            Tagged text: He has invited __number_of_people__ in his marriage

    Attributes:
        text(str): string to extract entities from
        entity_name(str): string by which the detected number would be replaced with on calling detect_entity()

        tagged_text(str): string with numbers replaced with tag defined by entity name
        processed_text(str): string with numbers detected removed
        number_ranges(list): list of number ranges detected
        original_number_text(list): list to store substrings of the text detected as numbers
        tag(str): entity_name prepended and appended with '__'

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

    def __init__(self, entity_name='number_range', language=ENGLISH_LANG, unit_type=None):
        """Initializes a NumberDetector object

        Args:
            entity_name(str): A string by which the detected numbers would be replaced with on calling detect_entity()
            language (str, optional): language code of number text, defaults to 'en'
            unit_type (str, optional): number unit types like weight, currency, temperature, used to detect number with
                                       specific unit type only. If None, it will detect all number ranges irrespective
                                       of units. You can see all unit types supported inside number detection
                                       language data with filename unit.csv.


        """
        # assigning values to superclass attributes
        self._supported_languages = self.get_supported_languages()
        super(NumberRangeDetector, self).__init__(language)
        self.entity_name = entity_name
        self.text = ''
        self.tag = '__' + self.entity_name + '__'
        self.language = language
        self.unit_type = unit_type
        try:
            number_range_detector_module = importlib.import_module(
                'ner_v2.detectors.numeral.number_range.{0}.number_range_detection'.format(self.language))
            self.language_number_range_detector = \
                number_range_detector_module.NumberRangeDetector(entity_name=self.entity_name,
                                                                 language=self.language,
                                                                 unit_type=self.unit_type)

        except ImportError:
            standard_number_range_regex = importlib.import_module(
                'ner_v2.detectors.numeral.number_range.standard_number_range_detector'
            )
            self.language_number_range_detector = standard_number_range_regex.NumberRangeDetector(
                entity_name=self.entity_name,
                language=language,
                unit_type=self.unit_type,
                data_directory_path=get_lang_data_path(
                    detector_path=os.path.abspath(__file__), lang_code=self.language)
            )

    @property
    def supported_languages(self):
        return self._supported_languages

    @property
    def tagged_text(self):
        return self.language_number_range_detector.tagged_text

    @property
    def processed_text(self):
        return self.language_number_range_detector.processed_text

    def detect_entity(self, text, **kwargs):
        """Detects numbers in the text string

        Args:
            text: string to extract entities from
            **kwargs: it can be used to send specific arguments in future.

        Returns:
            A tuple of two lists with first list containing the detected numbers and second list containing their
            corresponding substrings in the original message.

            For example:

                ([{'min_value': 3, 'max_value': None, 'unit': 'people'}], ['3 people'])

            Additionally this function assigns these lists to self.number and self.original_number_text attributes
            respectively.

        """
        self.text = ' ' + text.lower().strip() + ' '
        number_range_detected, original_text = \
            self.language_number_range_detector.detect_number_range(self.text)

        return number_range_detected, original_text
