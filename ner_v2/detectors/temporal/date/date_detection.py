# coding=utf-8
import datetime
import importlib
import os

import ner_constants
import ner_v2.detectors.temporal.constant as temporal_constants
from language_utilities.constant import ENGLISH_LANG
from ner_v2.detectors.base_detector import BaseDetector
from ner_v2.detectors.temporal.utils import get_timezone
from ner_v2.detectors.utils import get_lang_data_path
from ner_v2.property_assignor import PropertyAssignor


def get_start_indices(text, original_texts):
    # type: (str, List[str]) -> List[int]
    prev = -1
    text_end = len(text)
    start_indices = []
    for original_text in original_texts:
        start = text.find(original_text, prev + 1)
        start = text_end if start == -1 else start
        start_indices.append(start)
        prev = start

    return start_indices


class DateDetector(BaseDetector):
    """
    Detects date in various formats from given text and tags them.

    Detects all date entities in given text and replaces them by entity_name.
    Additionally detect_entity() method returns detected date values in dictionary containing values for day (dd),
    month (mm), year (yy), type (exact, possible, everyday, weekend, range etc.)

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected date entities would be replaced with on calling detect_entity()
        tagged_text: string with date entities replaced with tag defichaloned by entity name
        processed_text: string with detected date entities removed
        timezone: Optional, pytz.timezone object used for getting current time, default is pytz.timezone('UTC')
        language: source language of text
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

    def __init__(self, entity_name='date', language=ENGLISH_LANG, timezone='UTC', past_date_referenced=False):
        """Initializes a DateDetector object with given entity_name and pytz timezone object

        Args:
            entity_name: A string by which the detected date entity substrings would be replaced with on calling
                        detect_entity()
            timezone (Optional, str): timezone identifier string that is used to create a pytz timezone object
                                      default is UTC
            past_date_referenced (bool): to know if past or future date is referenced for date text like 'kal', 'parso'
        """
        self._supported_languages = self.get_supported_languages()
        super(DateDetector, self).__init__(language=language)
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.timezone = get_timezone(timezone)
        self.language = language

        try:
            date_detector_module = importlib.import_module(
                'ner_v2.detectors.temporal.date.{0}.date_detection'.format(self.language))
            self._date_detector = date_detector_module.DateDetector(entity_name=entity_name,
                                                                    past_date_referenced=past_date_referenced,
                                                                    timezone=timezone)
        except ImportError:
            standard_date_regex = importlib.import_module(
                'ner_v2.detectors.temporal.date.standard_date_regex'
            )
            self._date_detector = standard_date_regex.DateDetector(
                entity_name=entity_name,
                data_directory_path=get_lang_data_path(detector_path=os.path.abspath(__file__),
                                                       lang_code=self.language),
                timezone=timezone,
                past_date_referenced=past_date_referenced
            )

    @property
    def supported_languages(self):
        return self._supported_languages

    def detect_entity(self, text, detect_ranges=True, assign_properties=True, **kwargs):
        """
        Detects all date strings in text and returns two lists of detected date entities and their corresponding
        original substrings in text respectively.

        Args:
            text: string to extract date entities from

        Returns:
            Tuple containing two lists, first containing dictionaries, containing
            date values as 'dd', 'mm', 'type', 'yy' for each detected date, and second list containing corresponding
            substrings in given for entity detection

            Examples:
                date_detector = DateDetector("date")
                date_detector.detect_entity('Remind me everyday')

                date_detector.tagged_text


        Additionally this function assigns these lists to self.date and self.original_date_text attributes
        respectively.

        """

        self.text = ' ' + text.strip().lower() + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        dates, original_texts = [], []
        if self._date_detector:
            dates, original_texts = self._date_detector.detect_date(self.processed_text, **kwargs)

        self.processed_text = self._date_detector.processed_text
        self.tagged_text = self._date_detector.tagged_text

        start_inidices = get_start_indices(self.text, original_texts)
        zipped = sorted(zip(dates, original_texts, start_inidices), key=lambda tup: tup[-1])

        if zipped:
            dates, original_texts, _ = zip(*zipped)

        dates = [{"value": date_dict, "range": None, "repeat": None, "property": None, } for date_dict in dates]

        range_repeat_properties_filepath = os.path.join(
            get_lang_data_path(detector_path=os.path.abspath(__file__), lang_code=self.language),
            temporal_constants.DATE_RANGE_REPEAT_PROPERTIES_FILE
        )

        property_assignor = PropertyAssignor(properties_data_path=range_repeat_properties_filepath,
                                             subset=temporal_constants.DATE_REPEAT_PROPERTIES)
        repeat_properties = property_assignor.assign_properties(text=self.text, detected_spans=original_texts)

        for i, assigned_property in enumerate(repeat_properties):
            dates[i]["repeat"] = assigned_property.property

        if detect_ranges:
            property_assignor = PropertyAssignor(properties_data_path=range_repeat_properties_filepath,
                                                 subset=temporal_constants.DATE_RANGE_PROPERTIES)
            range_properties = property_assignor.assign_properties(text=self.text, detected_spans=original_texts)

            for i, assigned_property in enumerate(range_properties):
                dates[i]["range"] = assigned_property.property

        if assign_properties:
            properties_filepath = os.path.join(
                get_lang_data_path(detector_path=os.path.abspath(__file__), lang_code=self.language),
                temporal_constants.DATE_PROPERTIES_FILE
            )
            property_assignor = PropertyAssignor(properties_data_path=properties_filepath)
            properties = property_assignor.assign_properties(text=self.text, detected_spans=original_texts)
            for i, assigned_property in enumerate(properties):
                dates[i]["property"] = assigned_property.property

        validated_date_list, validated_original_list = [], []
        # Note: Following leaves tagged text incorrect but avoids returning invalid dates like 30th Feb
        for date, original_text in zip(dates, original_texts):
            try:
                datetime.date(year=date["value"]["yy"], month=date["value"]["mm"], day=date["value"]["dd"])
                validated_date_list.append(date)
                validated_original_list.append(original_text)
            except ValueError:
                pass

        return validated_date_list, validated_original_list

    def set_bot_message(self, bot_message):
        """
        Sets the object's bot_message attribute

        Args:
            bot_message: is the previous message that is sent by the bot
        """
        self._date_detector.set_bot_message(bot_message)

    def to_datetime_object(self, date_dict):
        """
        Convert the given date value dict to a timezone localised datetime object

        Args:
            date_dict (dict): dict containing dd, mm, yy

        Returns:
            datetime object: datetime object localised with the timezone given on initialisation
        """
        datetime_object = datetime.datetime(year=date_dict['yy'],
                                            month=date_dict['mm'],
                                            day=date_dict['dd'], )
        return self.timezone.localize(datetime_object)

    @staticmethod
    def to_date_dict(datetime_object, date_type=temporal_constants.TYPE_EXACT):
        """
        Convert the given datetime object to a dictionary containing dd, mm, yy

        Args:
            datetime_object (datetime.datetime): datetime object
            date_type (str, optional, default TYPE_EXACT): 'type' metdata for this detected date

        Returns:
            dict: dictionary containing day, month, year in keys dd, mm, yy respectively with date type as additional
            metadata.
        """
        return {
            'dd': datetime_object.day,
            'mm': datetime_object.month,
            'yy': datetime_object.year,
            'type': date_type,
        }

    @staticmethod
    def output_entity_dict_list(entity_value_list, original_text_list, detection_method=None,
                                detection_method_list=None, detection_language=ENGLISH_LANG):
        """Format detected entity values in list of dictionaries that contain entity_value, detection and original_text

        Args:
            entity_value_list (list): list of entity values which are identified from given detection logic
            original_text_list (list): list original values or actual values from message/structured_value
                                       which are identified
            detection_method (str, optional): how the entity was detected
                                              i.e. whether from message, structured_value
                                                   or fallback, verified from model or not.
                                              defaults to None
            detection_method_list(list, optional): list containing how each entity was detected in the entity_value
                                                   list. if provided, this argument will be used over detection method
                                                   defaults to None
            detection_language(str): ISO 639 code for language in which entity is detected

        Returns:
              list of dict: list containing dictionaries, each containing entity_value, original_text and detection;
                            entity_value is in itself a dict with its keys varying from entity to entity

        Example Output:
            [
                {
                    "entity_value": entity_value,
                    "detection": detection_method,
                    "original_text": original_text
                }
            ]
        """
        if detection_method_list is None:
            detection_method_list = []
        if entity_value_list is None:
            entity_value_list = []

        entity_list = []
        for i, date_dict in enumerate(entity_value_list):
            entity_value = date_dict["value"]

            if "dinfo" in entity_value:
                entity_value.pop("dinfo")

            range_ = date_dict.get("range", None)
            repeat = date_dict.get("repeat", None)
            property_ = date_dict.get("property", None)

            method = detection_method_list[i] if detection_method_list else detection_method

            entity_list.append(
                {
                    ner_constants.ENTITY_VALUE: entity_value,
                    "range": range_,
                    "repeat": repeat,
                    "property": property_,
                    ner_constants.ORIGINAL_TEXT: original_text_list[i],
                    ner_constants.DETECTION_METHOD: method,
                    ner_constants.DETECTION_LANGUAGE: detection_language
                }
            )
        return entity_list
