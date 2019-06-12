from __future__ import absolute_import

import abc

import six

from language_utilities.constant import ENGLISH_LANG
from language_utilities.constant import TRANSLATED_TEXT
from language_utilities.utils import translate_text
from ner_constants import (FROM_STRUCTURE_VALUE_VERIFIED, FROM_STRUCTURE_VALUE_NOT_VERIFIED, FROM_MESSAGE,
                           FROM_FALLBACK_VALUE, ORIGINAL_TEXT, ENTITY_VALUE, DETECTION_METHOD,
                           DETECTION_LANGUAGE, ENTITY_VALUE_DICT_KEY)


class BaseDetector(object):
    """
    This class is the base class from which will be inherited by individual detectors. It primarily contains the
    priority flow of structured value, message and fallback value and is also use to extend language support for
    detectors using translation

    Attributes:
        _language (str): ISO 639 language code of language of orignal query
        _processing_language (str): ISO-639 language code in which detector would process the query
        _translation_enabled (bool): Decides to either enable or disable translation API
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, language=ENGLISH_LANG, translation_enabled=False):
        """
        Initialize basedetector
        Args:
             language (str): ISO 639 language code of language of original query
             translation_enabled (bool): Decides to either enable or disable translation API
        """
        self._language = language
        self._processing_language = ENGLISH_LANG
        self._translation_enabled = translation_enabled
        self._set_language_processing_script()

    @abc.abstractproperty
    def supported_languages(self):
        """
        This method returns the list of languages supported by entity detectors
        Return:
             list: List of ISO 639 codes of languages supported by subclass/detector
        """
        return []

    @abc.abstractmethod
    def detect_entity(self, text, **kwargs):
        """
        This method runs the core entity detection logic defined inside entity detectors
        Args:
            text: text snippet from which entities needs to be detected
            **kwargs: values specific to different detectors such as 'last bot message', custom configs, etc.
        Return:
            tuple: Two lists of same length containing detected values and original substring from text which is used
            to derive the detected value respectively
        """
        return [], []

    def _set_language_processing_script(self):
        """
        This method is used to decide the language in which detector should run it's logic based on
        supported language and query language for which subclass is initialized
        """
        if self._language in self.supported_languages:
            self._processing_language = self._language
        elif ENGLISH_LANG in self.supported_languages and self._translation_enabled:
            self._processing_language = ENGLISH_LANG
        else:
            raise NotImplementedError('Please enable translation or extend language support'
                                      'for %s' % self._language)

    def detect(self, message=None, structured_value=None, fallback_value=None, **kwargs):
        """
        Use detector to detect entities from text. It also translates query to language compatible to detector

        Args:
            message (str): natural text on which detection logic is to be run. Note if structured value is
                                    detection is run on structured value instead of message
            structured_value (str): Value obtained from any structured elements. Note if structured value is
                                    detection is run on structured value instead of message
                                    (For example, UI elements like form, payload, etc)
            fallback_value (str): If the detection logic fails to detect any value either from structured_value
                              or message then we return a fallback_value as an output.

        Returns:
            dict or None: dictionary containing entity_value, original_text and detection;
                          entity_value is in itself a dict with its keys varying from entity to entity

        Example:
            1) Consider an example of restaurant detection from a message

                message = 'i want to order chinese from  mainland china and pizza from domminos'
                structured_value = None
                fallback_value = None
                bot_message = None
                output = detect(message=message, structured_value=structured_value,
                                  fallback_value=fallback_value, bot_message=bot_message)
                print output

                    >> [{'detection': 'message', 'original_text': 'mainland china', 'entity_value':
                    {'value': u'Mainland China'}}, {'detection': 'message', 'original_text': 'domminos',
                    'entity_value': {'value': u"Domino's Pizza"}}]

            2) Consider an example of movie name detection from a structured value

                message = 'i wanted to watch movie'
                entity_name = 'movie'
                structured_value = 'inferno'
                fallback_value = None
                bot_message = None
                output = get_text(message=message, entity_name=entity_name, structured_value=structured_value,
                                  fallback_value=fallback_value, bot_message=bot_message)
                print output

                    >> [{'detection': 'structure_value_verified', 'original_text': 'inferno', 'entity_value':
                    {'value': u'Inferno'}}]

            3) Consider an example of movie name detection from  a message
                message = 'i wanted to watch inferno'
                entity_name = 'movie'
                structured_value = 'delhi'
                fallback_value = None
                bot_message = None
                output = get_text(message=message, entity_name=entity_name, structured_value=structured_value,
                                  fallback_value=fallback_value, bot_message=bot_message)
                print output

                    >> [{'detection': 'message', 'original_text': 'inferno', 'entity_value': {'value': u'Inferno'}}]

        """
        if self._language != self._processing_language and self._translation_enabled:
            if structured_value:
                translation_output = translate_text(structured_value, self._language,
                                                    self._processing_language)
                structured_value = translation_output[TRANSLATED_TEXT] if translation_output['status'] else None
            elif message:
                translation_output = translate_text(message, self._language,
                                                    self._processing_language)
                message = translation_output[TRANSLATED_TEXT] if translation_output['status'] else None

        text = structured_value if structured_value else message
        entity_list, original_text_list = self.detect_entity(text=text, **kwargs)

        if structured_value:
            if entity_list:
                value, method, original_text = entity_list, FROM_STRUCTURE_VALUE_VERIFIED, original_text_list
            else:
                value, method, original_text = [structured_value], FROM_STRUCTURE_VALUE_NOT_VERIFIED, \
                                               [structured_value]
        elif entity_list:
            value, method, original_text = entity_list, FROM_MESSAGE, original_text_list
        elif fallback_value:
            value, method, original_text = [fallback_value], FROM_FALLBACK_VALUE, [fallback_value]
        else:
            return None

        return self.output_entity_dict_list(entity_value_list=value, original_text_list=original_text,
                                            detection_method=method, detection_language=self._processing_language)

    def detect_bulk(self, messages=None, **kwargs):
        """
        Use detector to detect entities from text. It also translates query to language compatible to detector

        Args:
            messages (list of strings): list of natural text(s) on which detection logic is to be run.
        Returns:
            dict or None: dictionary containing entity_value, original_text and detection;
                          entity_value is in itself a dict with its keys varying from entity to entity

        Example:
            1) Consider an example of restaurant detection from a message

                messages = ['i want to order chinese from  mainland china and pizza from domminos']
                output = detect(message=message)
                print output
                    >> [[{'detection': 'message', 'original_text': 'mainland china', 'entity_value':
                    {'value': u'Mainland China'}}, {'detection': 'message', 'original_text': 'domminos',
                    'entity_value': {'value': u"Domino's Pizza"}}]]
        """
        if messages is None:
            messages = []
        if self._language != self._processing_language and self._translation_enabled:
            translation_output_list = [
                translate_text(message_, self._language, self._processing_language)
                for message_ in messages]

            messages = []
            for translation_output in translation_output_list:
                messages.append(translation_output[TRANSLATED_TEXT] if translation_output['status'] else '')

        texts = messages
        bulk_entities_list, bulk_original_texts_list = [], []

        for text in texts:
            entities_list, original_texts_list = self.detect_entity(text=text, **kwargs)
            bulk_entities_list.append(entities_list)
            bulk_original_texts_list.append(original_texts_list)

        values_list, method, original_texts_list = bulk_entities_list, FROM_MESSAGE, bulk_original_texts_list

        return self.output_entity_bulk(entity_values_list=values_list, original_texts_list=original_texts_list,
                                       detection_method=method,
                                       detection_language=self._processing_language)


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
        for i, entity_value in enumerate(entity_value_list):
            if type(entity_value) in [str, six.text_type]:
                entity_value = {
                    ENTITY_VALUE_DICT_KEY: entity_value
                }
            method = detection_method_list[i] if detection_method_list else detection_method
            entity_list.append(
                {
                    ENTITY_VALUE: entity_value,
                    DETECTION_METHOD: method,
                    ORIGINAL_TEXT: original_text_list[i],
                    DETECTION_LANGUAGE: detection_language
                }
            )
        return entity_list

    @staticmethod
    def output_entity_bulk(entity_values_list, original_texts_list, detection_method=None,
                           detection_method_list=None, detection_language=ENGLISH_LANG):
        """
        Format detected entity values for bulk detection
        Args:
            entity_values_list (list of lists): containing list of entity values which are identified from given
                                                detection logic
            original_texts_list (list of lists): containing list original values or actual values from
                                                messages which are identified
            detection_method (str, optional): how the entity was detected
                                              i.e. whether from message, structured_value
                                                   or fallback, verified from model or not.
                                              defaults to None
            detection_method_list(list, optional): list containing how each entity was detected in the entity_value
                                                list.If provided, this argument will be used over detection method
                                                defaults to None
            detection_language(str): ISO 639 code for language in which entity is detected

        Returns:
            list of lists of dict: list of lists containing dictionaries, each containing entity_value,
                                    original_text and detection;
                                    entity_value is in itself a dict with its keys varying from entity to entity
        Example Output:
            [
                [
                    {
                        "entity_value": entity_value_1,
                        "detection": detection_method,
                        "original_text": original_text_1
                    },
                    {
                        "entity_value": entity_value_2,
                        "detection": detection_method,
                        "original_text": original_text_2
                    }

                ],
                [
                    {
                        "entity_value": entity_value,
                        "detection": detection_method,
                        "original_text": original_text
                    }
                ]
            ]
        """
        if detection_method_list is None:
            detection_method_list = []
        if entity_values_list is None:
            entity_values_list = []

        bulk_detection_entity_list = []
        for index, entity_values in enumerate(entity_values_list):
            entity_list = []
            for i, entity_value in enumerate(entity_values):
                if type(entity_value) in [str, six.text_type]:
                    entity_value = {
                        ENTITY_VALUE_DICT_KEY: entity_value
                    }
                method = detection_method_list[i] if detection_method_list else detection_method
                entity_list.append(
                    {
                        ENTITY_VALUE: entity_value,
                        DETECTION_METHOD: method,
                        ORIGINAL_TEXT: original_texts_list[index][i],
                        DETECTION_LANGUAGE: detection_language
                    }
                )
            bulk_detection_entity_list.append(entity_list)
        return bulk_detection_entity_list
