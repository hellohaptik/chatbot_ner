import abc
from ner_v1.language_utilities.constant import ENGLISH_LANG
from ner_v1.constant import (FROM_STRUCTURE_VALUE_VERIFIED, FROM_STRUCTURE_VALUE_NOT_VERIFIED, FROM_MESSAGE,
                             FROM_FALLBACK_VALUE, ORIGINAL_TEXT, ENTITY_VALUE, DETECTION_METHOD, ENTITY_VALUE_DICT_KEY)


class BaseDetector(object):
    __metaclass__ = abc.ABCMeta

    text = ''
    translated_text = ''
    supported_languages = set()
    language_script = ENGLISH_LANG
    language_processing_script = ENGLISH_LANG
    translation_enabled = False

    def __init__(self):
        pass

    @abc.abstractmethod
    def detect_entity(self, text):
        return [], []

    @abc.abstractmethod
    def set_bot_message(self, bot_message):
        pass

    @abc.abstractmethod
    def set_language_processing_script(self):
        pass

    def detect(self, message=None, structured_value=None, fallback_value=None, bot_message=None):
        """Use BaseDetector to detect textual entities

        Args:
            message (str): natural text on which detection logic is to be run. Note if structured value is
                                    detection is run on structured value instead of message
            structured_value (str): Value obtained from any structured elements. Note if structured value is
                                    detection is run on structured value instead of message
                                    (For example, UI elements like form, payload, etc)
            fallback_value (str): If the detection logic fails to detect any value either from structured_value
                              or message then we return a fallback_value as an output.
            bot_message (str): previous message from a bot/agent.

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
        self.set_bot_message(bot_message)
        text = structured_value if structured_value else message
        entity_list, original_text_list = self.detect_entity(text=text)

        if structured_value:
            if entity_list:
                value, method, original_text = entity_list, FROM_STRUCTURE_VALUE_VERIFIED, original_text_list
            else:
                value, method, original_text = structured_value, FROM_STRUCTURE_VALUE_NOT_VERIFIED, structured_value
        else:
            if entity_list:
                value, method, original_text = entity_list, FROM_MESSAGE, original_text_list
            else:
                value, method, original_text = fallback_value, FROM_FALLBACK_VALUE, fallback_value

        return self.output_entity_dict_list(entity_value_list=value, original_text_list=original_text,
                                            detection_method=method)

    @staticmethod
    def output_entity_dict_list(entity_value_list, original_text_list, detection_method=None,
                                detection_method_list=None):
        """Format detected entity values in list of dictionaries that contain entity_value, detection and original_text

        Args:
            entity_value_list (list): list of entity values which are identified from given detection logic
            original_text_list (list): list original values or actual values from message/structured_value 
                                       which are identified
            detection_method (str, optional): how the entity was detected 
                                              i.e. whether from message, structured_value
                                                   or fallback, verified from model or not.
                                              defaults to None
            detection_method_list(list, optional): list containing how each entity was detected in the entity_value list.
                                                   if provided, this argument will be used over detection method
                                                   defaults to None 

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

        entity_list = []
        for i, entity_value in enumerate(entity_value_list):
            if type(entity_value) in [str, unicode]:
                entity_value = {
                    ENTITY_VALUE_DICT_KEY: entity_value
                }
            method = detection_method_list[i] if detection_method_list else detection_method
            entity_list.append(
                {
                    ENTITY_VALUE: entity_value,
                    DETECTION_METHOD: method,
                    ORIGINAL_TEXT: original_text_list[i]
                }
            )
        return entity_list
