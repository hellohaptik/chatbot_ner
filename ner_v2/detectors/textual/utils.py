import json
import six

from chatbot_ner.config import ner_logger
from language_utilities.constant import ENGLISH_LANG

from ner_constants import FROM_FALLBACK_VALUE
from ner_v2.detectors.textual.text_detection import TextDetector


def verify_text_request(request):
    request_data = json.loads(request.body)
    queries = request_data.get("queries")

    if not queries:
        raise KeyError("Parameter queries is required")


def get_text_detection(message, entity_dict, structured_value, bot_message,
                       language=ENGLISH_LANG, **kwargs):
    """
    Get text detection for given message on given entities dict using
    TextDetector module.
    Args:
        message: message to detect text on
        entity_dict: entity details dict
        structured_value: structured value
        bot_message: bot message
        language: langugae for text detection
        **kwargs: other kwargs

    Returns:

        detected entity output

    """
    text_detector = TextDetector(entity_dict=entity_dict, source_language_script=language)

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
    Parse text request coming from POST call on `/v2/text/`
    Args:
        request: request object

    Returns:
        output data
    """
    request_data = json.loads(request.body)
    message = request_data.get("message", [])
    bot_message = request_data.get("bot_message")
    entities = request_data.get("entities", {})
    language_script = request_data.get('language_script', ENGLISH_LANG)
    source_language = request_data.get('source_language', ENGLISH_LANG)

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
                                    structured_value=None, bot_message=bot_message)

        data[0]["entities"].update(output[0])

        # get detection for structured value text entities
        if structured_value_entities:
            for entity, value in structured_value_entities.items():
                entity_dict = {entity: value}
                sv = value.get("structured_value")
                print(sv)
                output = get_text_detection(message=message_str, entity_dict=entity_dict,
                                            structured_value=sv, bot_message=bot_message)

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
    Generate detection output for default fallback entities.
    Args:
        entities_dict: dict of entities details
        language: language to run

    Returns:
        TextDetection output for default fallback
    """
    output = {}
    if not entities_dict:
        return output

    for entity, value in entities_dict.items():
        fallback_value = value.get("fallback_value")
        
        if fallback_value:
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
        else:
            output[entity] = []

    return output
