# coding=utf-8
from __future__ import absolute_import
import importlib
import os

from language_utilities.constant import ENGLISH_LANG
from ner_v2.detectors.base_detector import BaseDetector
from ner_v2.detectors.temporal.utils import get_timezone
from ner_v2.detectors.utils import get_lang_data_path


class TimeDetector(BaseDetector):
    """Detects time in various formats from given text and tags them.

    Detects all time entities in given text and replaces them by entity_name.
    Additionally there are methods to get detected time values in dictionary containing values for hour (hh),
    minutes (mm), notation/meridiem (nn = one of {'hrs', 'am', 'pm', 'df'}, df stands for difference)

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected time entities would be replaced with on calling detect_entity()
        tagged_text: string with time entities replaced with tag defined by entity_name
        processed_text: string with detected time entities removed
        time: list of time entities detected
        original_time_text: list to store substrings of the text detected as time entities
        tag: entity_name prepended and appended with '__'
        timezone: Optional, timezone identifier string that is used to create a pytz timezone object
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

    def __init__(self, entity_name='time', timezone=None, language=ENGLISH_LANG):
        """Initializes a TimeDetector object with given entity_name and timezone

        Args:
            entity_name(str): A string by which the detected time stamp substrings would be replaced with on calling
                               detect_entity()
            timezone(str): timezone identifier string that is used to create a pytz timezone object
                            default is UTC
            language(str): ISO 639 code for language of entities to be detected by the instance of this class
        """
        # assigning values to superclass attributes
        self._supported_languages = self.get_supported_languages()
        super(TimeDetector, self).__init__(language=language)
        self.entity_name = entity_name
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.time = []
        self.original_time_text = []
        self.tag = '__' + entity_name + '__'
        if timezone:
            self.timezone = get_timezone(timezone)
        else:
            self.timezone = None
        self.language = language

        try:
            time_detector_module = importlib.import_module(
                'ner_v2.detectors.temporal.time.{0}.time_detection'.format(self.language))
            self.language_time_detector = time_detector_module.TimeDetector(entity_name=self.entity_name,
                                                                            timezone=self.timezone)

        except ImportError:
            standard_time_regex = importlib.import_module(
                'ner_v2.detectors.temporal.time.standard_time_regex'
            )
            self.language_time_detector = standard_time_regex.TimeDetector(
                entity_name=self.entity_name,
                data_directory_path=get_lang_data_path(detector_path=os.path.abspath(__file__),
                                                       lang_code=self.language),
                timezone=self.timezone,
            )

    @property
    def supported_languages(self):
        return self._supported_languages

    def detect_entity(self, text, range_enabled=False, form_check=False, **kwargs):
        """
        Detects all time strings in text and returns list of detected time entities and their corresponding original
        substrings in text

        Args:
            text (Union[str, unicode]): text to detect times from
            range_enabled (bool, optional): whether to detect time ranges. Defaults to False
            form_check (bool, optional): boolean set to False, used when passed text is a form type message

        Returns:
            Tuple[List[Dict[str, str]], List[Union[str, unicode]]]: tuple containing two lists,
                first containing dictionaries, each containing containing hour, minutes
                and meridiem/notation - either 'am', 'pm', 'hrs', 'df'
                ('df' denotes relative difference to current time)
                for each detected time, and second list containing corresponding original substrings in text

        """
        self.text = ' ' + text.lower() + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        self.time, self.original_time_text = self.language_time_detector.detect_time(text=self.processed_text,
                                                                                     range_enabled=range_enabled,
                                                                                     form_check=form_check,
                                                                                     **kwargs)
        return self.time, self.original_time_text

    def set_bot_message(self, bot_message):
        """
        Sets the object's bot_message attribute

        Args:
            bot_message (str): previous message that is sent by the bot
        """
        self.language_time_detector.set_bot_message(bot_message)
