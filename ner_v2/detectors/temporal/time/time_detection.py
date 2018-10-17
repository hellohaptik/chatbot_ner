import importlib

from chatbot_ner.config import ner_logger
from ner_v2.language_utilities.constant import ENGLISH_LANG


class TimeDetector(object):
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

    def __init__(self, entity_name, timezone='UTC', range_enabled=False, form_check=False,
                 source_language=ENGLISH_LANG):
        """Initializes a TimeDetector object with given entity_name and timezone

        Args:
            entity_name (str): A string by which the detected time stamp substrings would be replaced with on calling
                        detect_entity()
            timezone (str): timezone identifier string that is used to create a pytz timezone object
                            default is UTC
            range_enabled (bool): whether time range needs to be detected
            form_check (bool): Optional, boolean set to False, used when passed text is a form type message
            source_language (str): ISO 639 code for language of entities to be detected by the instance of this
                                          class
        """
        # assigning values to superclass attributes
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
        self.source_language = source_language
        self.language_time_detector = self._get_time_language_detector()

    def detect_entity(self, text):
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

    def _get_time_language_detector(self):
        """
        Get language detector class for source language
        Returns:

        """
        try:
            time_detector_module = importlib.import_module(
                'ner_v2.detectors.temporal.time.{0}.time_detection'.format(self.source_language))
            return time_detector_module.TimeDetector(self.entity_name)
        except ImportError as e:
            ner_logger.exception("No time detector exists for %s language, Error - %s" %
                                 (self.source_language, str(e)))
            return None
