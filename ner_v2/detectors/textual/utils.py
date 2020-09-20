from __future__ import absolute_import

import json
import six

from chatbot_ner.config import ner_logger
from language_utilities.constant import ENGLISH_LANG

from ner_constants import FROM_FALLBACK_VALUE
from ner_v2.detectors.textual.text_detection import TextDetector


def verify_text_request(request):
    """
    Check the request object if proper message or entity is present in required
    format. If not present raises appropriate error.
    Args:
        request: API request object

    Returns:
        Raises KeyError if message or entities are not present
        Raises TypeError if message is not list or entities is not dict type
        Else Return none
    """

    request_data = json.loads(request.body)
    message = request_data.get("message")
    entities = request_data.get("entities")

    if not message:
        ner_logger.exception("Message param is not passed")
        raise KeyError("Message is required")

    if not entities:
        ner_logger.exception("Entities param is not passed")
        raise KeyError("Entities dict is required")

    if not isinstance(message, list):
        ner_logger.exception("Message param is not in correct format")
        raise TypeError("Message should be in format of list of string")

    if not isinstance(entities, dict):
        ner_logger.exception("Entities param is not in correct format")
        raise TypeError("Entities should be dict of entity details")


def get_text_detection(message, entity_dict, structured_value=None, bot_message=None,
                       language=ENGLISH_LANG, target_language_script=ENGLISH_LANG, **kwargs):
    """
    Get text detection for given message on given entities dict using
    TextDetector module.

    If the message is string type call TextDetector.detect() mwthod, if it is list
    call TextDetector.detect_bulk() method. Else, it wol raise an error.
    Args:
        message: message to detect text on
        entity_dict: entity details dict
        structured_value: structured value
        bot_message: bot message
        language: langugae for text detection
        target_language_script: target language for detection default ENGLISH
        **kwargs: other kwargs

    Returns:

        detected entity output
    """
    text_detector = TextDetector(entity_dict=entity_dict, source_language_script=language,
                                 target_language_script=target_language_script)
    if isinstance(message, six.string_types):
        entity_output = text_detector.detect(message=message,
                                             structured_value=structured_value,
                                             bot_message=bot_message)
    elif isinstance(message, (list, tuple)):
        entity_output = text_detector.detect_bulk(messages=message)
    else:
        raise TypeError('`message` argument must be either of type `str`, `unicode`, `list` or `tuple`.')

    return entity_output


def parse_text_request(request):
    """
    Parse text request coming from POST call on `/v2/text/` and call the
    get text detection.
    Message to detect text can be:

    1) Single entry in the list, for this we use `text_detector.detect` method.
    Also for this case we check if the structured value or use_fallback is present.

    2) For mulitple message, underlying code will call `text_detector.detect_bulk` method.
    In this case we ignore structured valur or use_fallback for all the entities.

    Args:
        request: request object
    Returns:
        output data list for all the message
    Examples:
        Request Object:
        {
                    "message": ["I want to go to Jabalpur"],
                    "bot_message": null,
                    "language_script": "en",
                    "source_language": "en",
                    "entities": {
                        "city": {
                            "structured_value": "Delhi",
                            "fallback_value": null,
                            "predetected_values": ["Mumbai"],
                            "fuzziness": null,
                            "min_token_len_fuzziness": null,
                            "use_fallback": false
                        },
                        "restaurant": {
                            "structured_value": null,
                            "fallback_value": null,
                            "predetected_values": null,
                            "fuzziness": null,
                            "min_token_len_fuzziness": null,
                            "use_fallback": false
                                }
                             }
                         }
            output response:
                        [
                            {
                            "entities": {
                                "restaurant": [],
                                "city": [
                                    {
                                        "entity_value": {
                                            "value": "New Delhi",
                                            "datastore_verified": true,
                                            "model_verified": false
                                        },
                                        "detection": "structure_value_verified",
                                        "original_text": "delhi",
                                        "language": "en"
                                    },
                                    {
                                        "entity_value": {
                                            "value": "Mumbai",
                                            "datastore_verified": false,
                                            "model_verified": true
                                        },
                                        "detection": "structure_value_verified",
                                        "original_text": "Mumbai",
                                        "language": "en"
                                    }
                        ]
    """
    request_data = json.loads(request.body)
    message = request_data.get("message", [])
    bot_message = request_data.get("bot_message")
    entities = request_data.get("entities", {})
    target_language_script = request_data.get('language_script') or ENGLISH_LANG
    source_language = request_data.get('source_language') or ENGLISH_LANG

    data = []

    message_len = len(message)

    if message_len == 1:

        # get first message
        message_str = message[0]

        structured_value_entities = {}
        fallback_value_entities = {}
        text_value_entities = {}

        data.append({"entities": {}, "language": source_language})

        for each_entity, value in entities.items():

            structured_value = value.get('structured_value')
            use_fallback = value.get('use_fallback', False)

            if use_fallback:
                fallback_value_entities[each_entity] = value
            elif structured_value:
                structured_value_entities[each_entity] = value
            else:
                text_value_entities[each_entity] = value

        # get detection for normal text entities
        output = get_text_detection(message=message_str, entity_dict=text_value_entities,
                                    structured_value=None, bot_message=bot_message,
                                    language_script=source_language,
                                    target_language_script=target_language_script)
        data[0]["entities"].update(output[0])

        # get detection for structured value text entities
        if structured_value_entities:
            for entity, value in structured_value_entities.items():
                entity_dict = {entity: value}
                sv = value.get("structured_value")
                output = get_text_detection(message=message_str, entity_dict=entity_dict,
                                            structured_value=sv, bot_message=bot_message,
                                            language_script=source_language,
                                            target_language_script=target_language_script)

                data[0]["entities"].update(output[0])

        # get detection for fallback value text entities
        if fallback_value_entities:
            output = get_output_for_fallback_entities(fallback_value_entities, source_language)
            data[0]["entities"].update(output)

    # check if more than one message
    elif len(message) > 1:
        text_detection_result = get_text_detection(message=message, entity_dict=entities,
                                                   structured_value=None, bot_message=bot_message)

        data = [{"entities": x, "language": source_language} for x in text_detection_result]

    else:
        ner_logger.debug("No valid message provided")
        raise KeyError("Message is required")

    return data


def get_output_for_fallback_entities(entities_dict, language=ENGLISH_LANG):
    """
    Generate default detection output for default fallback entities.
    It will check if fallback_value is present if not it will return
    empty list for that entity.

    Args:
        entities_dict: dict of entities details
        language: language to run

    Returns:
        TextDetection output (list of dict) for default fallback values

    Examples:
        Input:
        {
            'city': {'fallback_value': 'Mumbai', 'use_fallback': True},
            'restaurant': {'fallback_value': None, 'use_fallback': True}
        }

        Output:

        {
        'city': [
                    {'entity_value': {'value': 'Mumbai',
                                    'datastore_verified': False,
                                    'model_verified': False},
                    'detection': 'fallback_value',
                    'original_text': 'Mumbai',
                    'language': 'en'}
                ],
        'restaurant': []
        }

    """
    output = {}
    if not entities_dict:
        return output

    for entity, value in entities_dict.items():
        fallback_value = value.get("fallback_value")

        if not fallback_value:
            output[entity] = []

        else:
            output[entity] = [
                {
                    "entity_value": {
                        "value": fallback_value,
                        "datastore_verified": False,
                        "model_verified": False
                    },
                    "detection": FROM_FALLBACK_VALUE,
                    "original_text": fallback_value,
                    "language": language
                }
            ]
    return output
