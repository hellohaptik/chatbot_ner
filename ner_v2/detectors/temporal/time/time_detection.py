import importlib
import os

from ner_v2.detectors.base_detector import BaseDetector
from language_utilities.constant import ENGLISH_LANG


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
        form_check: boolean, set to True at initialization, used when passed text is a form type message
        bot_message: str, set as the outgoing bot text/message
        departure_flag: bool, whether departure time is being detected
        return_flag: bool, whether return time is being detected
        range_enabled: bool, whether time range needs to be detected


    """

    @staticmethod
    def get_supported_languages():
        """
        Return list of supported languages
        Returns:
            (list): supported languages
        """
        supported_languages = []
        cwd = os.listdir((os.path.dirname(os.path.abspath(__file__))))
        cwd_dirs = [x for x in os.listdir('.') if os.path.isdir(cwd)]
        for _dir in cwd_dirs:
            if os.path.exists(os.path.join(_dir.rstrip(os.sep), LANGUAGE_DATE_DETECTION_FILE)):
                supported_languages.append(_dir)
        return supported_languages

    def __init__(self, entity_name, timezone='UTC', range_enabled=False, form_check=False,
                 language=ENGLISH_LANG):
        """Initializes a TimeDetector object with given entity_name and timezone

        Args:
            entity_name (str): A string by which the detected time stamp substrings would be replaced with on calling
                        detect_entity()
            timezone (str): timezone identifier string that is used to create a pytz timezone object
                            default is UTC
            range_enabled (bool): whether time range needs to be detected
            form_check (bool): Optional, boolean set to False, used when passed text is a form type message
            language (str): ISO 639 code for language of entities to be detected by the instance of this
                                          class
        """
        # assigning values to superclass attributes
        self._supported_languages = self.get_supported_languages()
        super(TimeDetector, self).__init__(language=language)
        self.entity_name = entity_name
        self.text = ''
        self.departure_flag = False
        self.return_flag = False
        self.tagged_text = ''
        self.processed_text = ''
        self.time = []
        self.original_time_text = []
        self.form_check = form_check
        self.tag = '__' + entity_name + '__'
        self.bot_message = None
        self.timezone = timezone or 'UTC'
        self.range_enabled = range_enabled
        self.language = language
        time_detector_module = importlib.import_module(
            'ner_v2.detectors.temporal.time.{0}.time_detection'.format(self.language))

        self.language_time_detector = time_detector_module.TimeDetector(self.entity_name)

    @property
    def supported_languages(self):
        return self._supported_languages

    def detect_entity(self, text, **kwargs):
        """
        Detects all time strings in text and returns list of detected time entities and their corresponding original
        substrings in text

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing
            containing hour, minutes and meridiem/notation - either 'am', 'pm', 'hrs', 'df' ('df' denotes relative
            difference to current time) for each detected time, and second list containing corresponding original
            substrings in text

        """
        self.text = ' ' + text.lower() + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        if self.language_time_detector:
            self.time, self.original_time_text = self.language_time_detector.detect_time(self.processed_text)
        return self.time, self.original_time_text

    def set_bot_message(self, bot_message):
        """
        Sets the object's bot_message attribute

        Args:
            bot_message (str): previous message that is sent by the bot
        """
        self.bot_message = bot_message

