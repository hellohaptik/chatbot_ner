from __future__ import absolute_import
from ner_v1.chatbot.combine_detection_logic import combine_output_of_detection_logic_and_tag
from ner_v1.chatbot.entity_detection import get_text, get_city, get_date, get_time, get_email, \
    get_phone_number, get_budget, get_number, get_pnr, get_shopping_size


def run_ner(entities, message):
    """This function tags the message with the entity name and also identify the entity values.
    This functionality can be used when we have to identify entities from message without considering and
    structured_value and fallback_value.

    Attributes:
        entities: list of entity names that needs to be identified. For example, ['date', 'time', 'restaurant']
        message: message on which entity detection needs to run

    Output:
        will be list of dictionary
        {
            'entity_data':  PROCESSED_ENTITY_DICTIONARY,
            'tag': TAGGED_TEXT

        }

    Example:
        entities = ['date','time','restaurant']
        message = "Reserve me a table today at 6:30pm at Mainland China and on Monday at 7:00pm at Barbeque Nation"
        ner_output = run_ner(entities=entities, message=message)
        print ner_output

            >> "data": {
        "tag": "reserve me a table __date__ at __time__ at __restaurant__ and on __date__ at __time__ at __restaurant__",
        "entity_data": {
            "restaurant": [{
                "detection": "chat",
                "original_text": "barbeque nation",
                "entity_value": "Barbeque Nation"
            }, {
                "detection": "chat",
                "original_text": "mainland china",
                "entity_value": "Mainland China"
            }],
            "date": [{
                "detection": "chat",
                "original_text": " monday",
              "entity_value": {
                    "mm": 03,
                    "yy": 2017,
                    "dd": 13,
                    "type": "current_day"
                }
            }, {
                "detection": "chat",
                "original_text": "today",
                "entity_value": {
                    "mm": 03,
                    "yy": 2017,
                    "dd": 11,
                    "type": "today"
                }
            }],
            "time": [{
                "detection": "chat",
                "original_text": "6:30pm",
                "entity_value": {
                    "mm": 30,
                    "hh": 6,
                    "nn": "pm"
                }
            }, {
                "detection": "chat",
                "original_text": "7:00pm",
                "entity_value": {
                    "mm": 0,
                    "hh": 7,
                    "nn": "pm"
                }
            }]
        }
    }
}

    """
    entity_data = {}
    for entity in entities:
        entity_data[entity] = get_entity_function(entity=entity, message=message)
    return combine_output_of_detection_logic_and_tag(entity_data, message)


def get_entity_function(entity, message):
    """Calls the specific detection logic based on entity name. entity name plays crucial role in detecting textual
    entities (restaurant, cuisine, occupation, etc) but not while detecting phone number, email, etc.

    In this functionality we define a dictionary called as entity_function_dictionary = {}.
    In entity_function_dictionary  key is the name of the entity and the value is which functionality to call for that
    entity

    Attributes:
        entity: name of the entity that calls specific detection logic
        message: message on which detection logic needs to run

    Example:
        entity_output = get_entity_function(entity='date', message='set me reminder on 30th March')
        print entity_output
    """
    entity_function_dictionary = {
        'date': get_date,
        'time': get_time,
        'email': get_email,
        'phone_number': get_phone_number,
        'budget': get_budget,
        'number': get_number,
        'city': get_city,
        'train_pnr': get_pnr,
        'flight_pnr': get_pnr,
        'shopping_size': get_shopping_size

    }

    if entity in entity_function_dictionary:
        return entity_function_dictionary.get(entity)(message=message, entity_name=entity, structured_value=None,
                                                      fallback_value=None, bot_message=None)
    else:
        return get_text(message=message, entity_name=entity, structured_value=None, fallback_value=None,
                        bot_message=None)
