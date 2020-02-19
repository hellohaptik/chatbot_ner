from __future__ import absolute_import
from collections import defaultdict
from six import iteritems
from lib.nlp.const import TOKENIZER
from lib.nlp.regexreplace import RegexReplace
from ner_constants import ORIGINAL_TEXT, DETECTION_METHOD, FROM_MESSAGE, FROM_MODEL_VERIFIED, FROM_MODEL_NOT_VERIFIED


def combine_output_of_detection_logic_and_tag(entity_data, text):
    """NER is often used to tag the chat so it can be used in disambiguation process. Also, many times one entity may
    overlap with another.
    For example: "I want to order from Delhi Dhaba" and we want to detect two entities i.e. restaurant and city.
    So, first we will run individual detection logic of restaurant and city and from this we are able to derive two
    entity values i.e. Delhi Dhaba (restaurant) and Delhi (city) but we see that entity city is irrelevant in above
    case because message is about ordering from restaurant. So it necessary to process the output which is obtained by
    running individual detection logic and keep the relevant entities.

    Attributes:
        text: a message on which detection logic needs to run. For example "i want to order form  delhi dhaba"
        entity_data: dictionary containing key as entity_name and value as a output from entities detection logic.
        For example:
            {
            "restaurant":
                [
                    {
                        "detection": "chat",
                        "original_text": "delhi dhaba",
                        "entity_value":"Delhi Dhaba"
                    }
                ],
            "city":
                [
                    {
                        "detection": "chat",
                        "original_text": "delhi",
                        "entity_value":"New Delhi"
                    }
                ]
        }

    Output:
        will be list of dictionary
        {
            'entity_data':  PROCESSED_ENTITY_DICTIONARY,
            'tag': TAGGED_TEXT

        }

        entity_data will be processed dictionary of entities containg valid entity value and will remove the ambiguity
        tagged_text will be the tagged_data
        For example:
          {
            "entity_data":
                {
                    "restaurant":
                        [
                            {
                                "detection": "chat",
                                "original_text": "delhi dhaba",
                                "entity_value":"Delhi Dhaba"
                            }
                        ],
                    "city":
                        [
                            {
                                "detection": "chat",
                                "original_text": "delhi",
                                "entity_value":"New Delhi"
                            }
                        ]
                },
            "tagged_text": "i want to order from __restaurant__"
          }

    """
    regex = RegexReplace([(r'[\'\/]', r''), (r'\s+', r' ')])
    text = regex.text_substitute(text)
    final_entity_data = defaultdict(list)
    tagged_text = text.lower()
    processed_text = text.lower()
    tag_preprocess_dict = defaultdict(list)
    for entity, entity_list in iteritems(entity_data):
        if entity_list:
            for entity_identified in entity_list:
                if entity_identified[ORIGINAL_TEXT] and \
                        entity_identified[DETECTION_METHOD] in [FROM_MESSAGE, FROM_MODEL_VERIFIED,
                                                                FROM_MODEL_NOT_VERIFIED]:
                    tag_preprocess_dict[entity_identified[ORIGINAL_TEXT].lower()].append([entity_identified, entity])
                else:
                    tag_preprocess_dict['NA'].append([entity_identified, entity])
        else:
            final_entity_data[entity] = None

    original_text_list = list(tag_preprocess_dict.keys())
    original_text_list = sort_original_text(original_text_list)
    for original_text in original_text_list:
        tag = ''
        if original_text in processed_text:
            processed_text = processed_text.replace(original_text, '')
            for entity_dict, entity in tag_preprocess_dict[original_text]:
                tag += '_' + entity
                if final_entity_data[entity]:
                    final_entity_data[entity].append(entity_dict)
                else:
                    final_entity_data[entity] = [entity_dict]
            if tag != '':
                tag = '_' + tag + '__'
            tagged_text = tagged_text.replace(original_text, tag)
        else:
            for entity_dict, entity in tag_preprocess_dict[original_text]:
                if not final_entity_data[entity]:
                    final_entity_data[entity] = None

    if tag_preprocess_dict.get('NA'):
        for entity_dict, entity in tag_preprocess_dict['NA']:
            if final_entity_data[entity]:
                final_entity_data[entity].append(entity_dict)
            else:
                final_entity_data[entity] = [entity_dict]

    return {'entity_data': final_entity_data, 'tag': tagged_text}


def sort_original_text(original_text_list):
    """
    Sorts the original text list based on tokens and length of string
    :param original_text_list:
    :return:
    """
    final_original_text = []
    sort_original_text_dict = defaultdict(list)
    original_text_list.sort(key=lambda s: len(TOKENIZER.tokenize(s)), reverse=True)
    for original in original_text_list:
        length_of_token = len(TOKENIZER.tokenize(original))
        sort_original_text_dict[length_of_token].append(original)
    for token_length in reversed(sorted(sort_original_text_dict.keys())):
        list_of_tokens = sort_original_text_dict[token_length]
        list_of_tokens.sort(key=lambda s: len(s), reverse=True)
        final_original_text.extend(list_of_tokens)
    return final_original_text
