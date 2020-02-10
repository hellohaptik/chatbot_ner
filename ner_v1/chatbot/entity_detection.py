from __future__ import absolute_import

from language_utilities.constant import ENGLISH_LANG
from ner_constants import (FROM_STRUCTURE_VALUE_VERIFIED, FROM_STRUCTURE_VALUE_NOT_VERIFIED, FROM_MESSAGE,
                           FROM_FALLBACK_VALUE, ORIGINAL_TEXT, ENTITY_VALUE, DETECTION_METHOD, ENTITY_VALUE_DICT_KEY)
from ner_v1.detectors.numeral.budget.budget_detection import BudgetDetector
from ner_v1.detectors.numeral.number.number_detection import NumberDetector
from ner_v1.detectors.numeral.number.passenger_detection import PassengerDetector
from ner_v1.detectors.numeral.size.shopping_size_detection import ShoppingSizeDetector
from ner_v1.detectors.pattern.email.email_detection import EmailDetector
from ner_v1.detectors.pattern.phone_number.phone_detection import PhoneDetector
from ner_v1.detectors.pattern.pnr.pnr_detection import PNRDetector
from ner_v1.detectors.pattern.regex.regex_detection import RegexDetector
from ner_v1.detectors.temporal.date.date_detection import DateAdvancedDetector
from ner_v1.detectors.temporal.time.time_detection import TimeDetector
from ner_v1.detectors.textual.city.city_detection import CityDetector
from ner_v1.detectors.textual.name.name_detection import NameDetector
from ner_v1.detectors.textual.text.text_detection import TextDetector
from chatbot_ner.config import ner_logger
import six

"""
This file contains functionality that performs entity detection over a chatbot.
The chatbot contains several elements which can be used to detect entity. For example, message, UI elements (like form,
payload, etc) and fallback_value(viz. obtained from user profile or third party api).

The entity detection logic for chatbot works in following format:
    UI elements (structured_value) --> message --> fallback_value
    We first run entity detection on UI elements because this information is extracted from some structured format.
    If the detection fails on UI element then we run detection on a message if it still fails then we assign
    the fallback_value if present

All the entity detection functionality have standardised format and parameters.
NOTE: We should make sure that whenever new entity detection logic gets created we maintain this structure
and parameters. Reason is maintenance.


Parameters:
    message (str): message on which detection logic is to be run. It is unstructured text from which entity needs to be
                   extracted. For example "I want to order pizza"
    entity_name (str): name of the entity. It is used to run a particular detection logic by looking
                       into the dictionary. In detection logic for example, get_text() the entity name will
                       be different based on which entities we need to detect.
                       For example, if we want to detect cuisine then entity_name must be "cuisine",
                       for dish entity_name must be "dish" and so on. But in few detection logic like
                       get_phone_number(), entity_name does not have any significance
                       as detection logic of phone_number won't change based on the entity_name.
    structured_value (str): it is a value which is obtained from the structured text
                            (For example, UI elements like form, payload, etc)
    fallback_value (str): If the detection logic fails to detect any value either from structured_value
                          or message then we return a fallback_value as an output. This value is derived
                          from third party api or from users profile. For example, if user says "Nearby ATMs".
                          In this example user has not provided any information about his location in the chat but,
                          we can pass a fallback_value that will contain its location value from its profile
                          or third party api (like geopy, etc)
    bot_message (str): previous message from a bot/agent. This is an important parameter, many a times the entity value
                       relies on the message from the bot/agent i.e. what bot saying or asking.
                       Example: bot might ask for departure date to book a flight and user might reply with date.
                       Now, it can not be disambiguated whether its departure date or arrival date unless
                       we know what bot is asking for?
                      Example:
                      bot: Please help me with date of departure?
                      user: 23rd March


Format of entity detection functionality for a chatbot:

The general architecture of executing any detection logic is as follows:
1. We initialize the individual entity detection by passing necessary parameters
2. if structured_value is present then we run the entity detection logic over the structured_value to extract the
necessary entity values if it fails then we consider the structured_value as entity value and return as it is.
3. if structured_value is not present then we execute the detection logic over a message and returns the entity
values from the message.
4. if we don't detect anything from the above two steps then we return the fallback value as an output

Output:

The output is stored in a list of dictionary contains the following structure
[
    {
        "entity_value": entity_value,
        "detection": detection_method,
        "original_text": original_text
    }
]
    - Consider this example for below explanation "I want to order from mcd"
    - "entity_value": this will store value of entity (ie. entity value) which is detected. It will be in dictionary
                      format. For example, {"value": McDonalds}.
    - "detection": this will store how the entity is detected i.e. whether from message, structured_value or fallback.
    - "original_text": this will store the actual value that is detected. For example, mcd.
"""


def get_text(message, entity_name, structured_value, fallback_value, bot_message, language=ENGLISH_LANG,
             predetected_values=None, **kwargs):
    """Use TextDetector (datastore/elasticsearch) to detect textual entities

    Args:
        message (str or unicode or None or list(bulk)): natural language text(s) on which detection logic is to be run.
                                          Note if structured value is passed detection is run on
                                          structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
        structured_value (str or unicode or None): Value obtained from any structured elements.
                                                   Note if structured value is detection is run on
                                                   structured value instead of message
                                                   (For example, UI elements like form, payload, etc)
        fallback_value (str or unicode or None): If the detection logic fails to detect any value
                                                 either from structured_value or message then
                                                 we return a fallback_value as an output.
        bot_message (str or unicode or None): previous message from a bot/agent.
        language (str): ISO 639-1 code of language of message
        **kwargs: extra configuration arguments for TextDetector
            fuzziness (str or int or None): fuzziness to apply while detecting text entities
            min_token_len_fuzziness (str or int or None): minimum length of the token to be eligible for fuzziness
            live_crf_model_path (str) : path to the CRF model to use to detect entites. Defaults to None
            read_model_from_s3 (bool): If True read CRF model from S3. Defaults to False
            read_embeddings_from_remote_url (bool): if True read word embeddings from configured remote url. Defaults
                                                    to False




    Returns:
        dict or None: dictionary containing entity_value, original_text and detection;
                      entity_value is in itself a dict with its keys varying from entity to entity

    Example:
        --- Single message
            >>> message = u'i want to order chinese from  mainland china and pizza from domminos'
            >>> entity_name = 'restaurant'
            >>> structured_value = None
            >>> fallback_value = None
            >>> bot_message = None
            >>> output = get_text(message=message,
            >>>                   entity_name=entity_name,
            >>>                   structured_value=structured_value,
            >>>                   fallback_value=fallback_value,
            >>>                   bot_message=bot_message)
            >>> print(output)

            [
                {
                    'detection': 'message',
                    'original_text': 'mainland china',
                    'entity_value': {'value': u'Mainland China'}
                },
                {
                    'detection': 'message',
                    'original_text': 'domminos',
                    'entity_value': {'value': u"Domino's Pizza"}
                }
            ]



            >>> message = u'i wanted to watch movie'
            >>> entity_name = 'movie'
            >>> structured_value = u'inferno'
            >>> fallback_value = None
            >>> bot_message = None
            >>> output = get_text(message=message,
            >>>                   entity_name=entity_name,
            >>>                   structured_value=structured_value,
            >>>                   fallback_value=fallback_value,
            >>>                   bot_message=bot_message)
            >>> print(output)

            [
                {
                    'detection': 'structure_value_verified',
                    'original_text': 'inferno',
                    'entity_value': {'value': u'Inferno'}
                }
            ]

            >>> message = u'i wanted to watch inferno'
            >>> entity_name = 'movie'
            >>> structured_value = u'delhi'
            >>> fallback_value = None
            >>> bot_message = None
            >>> output = get_text(message=message,
            >>>                   entity_name=entity_name,
            >>>                   structured_value=structured_value,
            >>>                   fallback_value=fallback_value,
            >>>                   bot_message=bot_message)
            >>> print(output)

            [
                {
                    'detection': 'message',
                    'original_text': 'inferno',
                    'entity_value': {'value': u'Inferno'}
                }
            ]

        --- Bulk detection
            >>> message = [u'book a flight to mumbai',
                            u'i want to go to delhi from mumbai']
            >>> entity_name = 'city'
            >>> output = get_text(message=message,
            >>>                   entity_name=entity_name,
            >>>                   structured_value=structured_value,
            >>>                   fallback_value=fallback_value,
            >>>                   bot_message=bot_message)
            >>> print(output)

            [
                [
                    {
                        'detection': 'message',
                        'entity_value': {'value': u'mumbai'},
                        'original_text': u'mumbai'
                    }
                ],
                [
                    {
                        'detection': 'message',
                        'entity_value': {'value': u'New Delhi'},
                        'original_text': u'delhi'
                    },
                    {
                        'detection': 'message',
                        'entity_value': {'value': u'mumbai'},
                        'original_text': u'mumbai'
                    }
                ]
            ]

    """
    fuzziness = kwargs.get('fuzziness', None)
    min_token_len_fuzziness = kwargs.get('min_token_len_fuzziness', None)
    predetected_values = predetected_values or []

    text_detector = TextDetector(entity_name=entity_name, source_language_script=language)
    if fuzziness:
        fuzziness = parse_fuzziness_parameter(fuzziness)
        text_detector.set_fuzziness_threshold(fuzziness)

    if min_token_len_fuzziness:
        min_token_len_fuzziness = int(min_token_len_fuzziness)
        text_detector.set_min_token_size_for_levenshtein(min_size=min_token_len_fuzziness)

    ner_logger.info("Predetected values: {}".format(predetected_values))
    if isinstance(message, six.string_types):
        entity_output = text_detector.detect(message=message,
                                             structured_value=structured_value,
                                             fallback_value=fallback_value,
                                             bot_message=bot_message,
                                             predetected_values=predetected_values)
    elif isinstance(message, (list, tuple)):
        entity_output = text_detector.detect_bulk(messages=message, fallback_values=fallback_value,
                                                  predetected_values=predetected_values)
    else:
        raise TypeError('`message` argument must be either of type `str`, `unicode`, `list` or `tuple`.')

    return entity_output


def get_location(message, entity_name, structured_value, fallback_value, bot_message,
                 predetected_values=None, **kwargs):
    """"Use TextDetector (elasticsearch) to detect location

    TODO: We can improve this by creating separate for location detection instead of using TextDetector

    Args:
        message (str): natural text on which detection logic is to be run. Note if structured value is
                                detection is run on structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
        structured_value (str): Value obtained from any structured elements. Note if structured value is
                                detection is run on structured value instead of message
                                (For example, UI elements like form, payload, etc)
        fallback_value (str): If the detection logic fails to detect any value either from structured_value
                          or message then we return a fallback_value as an output.
        bot_message (str): previous message from a bot/agent.
        predetected_values(list of str): prior detection results from models like crf etc.


    Returns:
        dict or None: dictionary containing entity_value, original_text and detection;
                      entity_value is in itself a dict with its keys varying from entity to entity

    Example:

        message = 'atm in andheri west'
        entity_name = 'locality_list'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_location(message=message, entity_name=entity_name, structured_value=structured_value,
                              fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'message', 'entity_value': {'value': 'Andheri West'}, 'language': 'en',
                 'original_text': 'andheri west'}]
    """
    predetected_values = predetected_values or []
    text_detection = TextDetector(entity_name=entity_name)
    return text_detection.detect(message=message, structured_value=structured_value, fallback_value=fallback_value,
                                 bot_message=bot_message, predetected_values=predetected_values)


def get_phone_number(message, entity_name, structured_value, fallback_value, bot_message):
    """Use PhoneDetector to detect phone numbers

    Args:
        message (str): natural text on which detection logic is to be run. Note if structured value is
                                detection is run on structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
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

        message = 'my contact number is 9049961794'
        entity_name = 'phone_number'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_phone_number(message=message, entity_name=entity_name, structured_value=structured_value,
                                  fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'message', 'original_text': '9049961794', 'entity_value': {'value': '9049961794'}}]

        message = 'Please call me'
        entity_name = 'phone_number'
        structured_value = None
        fallback_value = '9049961794'
        bot_message = None
        output = get_phone_number(message=message, entity_name=entity_name, structured_value=structured_value,
                                  fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'fallback_value', 'original_text': '9049961794',
                 'entity_value': {'value': '9049961794'}}]


    """

    phone_detection = PhoneDetector(entity_name=entity_name)
    return phone_detection.detect(message=message, structured_value=structured_value, fallback_value=fallback_value,
                                  bot_message=bot_message)


def get_email(message, entity_name, structured_value, fallback_value, bot_message):
    """Use EmailDetector to detect email ids

    Args:
        message (str): natural text on which detection logic is to be run. Note if structured value is
                                detection is run on structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
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

        message = 'my email id is apurv.nagvenkar@gmail.com'
        entity_name = 'email'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_email(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'message', 'original_text': 'apurv.nagvenkar@gmail.com',
            'entity_value': {'value': 'apurv.nagvenkar@gmail.com'}}]



        message = 'send me the email'
        entity_name = 'email'
        structured_value = None
        fallback_value = 'apurv.nagvenkar@gmail.com'
        bot_message = None
        output = get_email(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'fallback_value', 'original_text': 'apurv.nagvenkar@gmail.com',
            'entity_value': {'value': 'apurv.nagvenkar@gmail.com'}}]

    """
    email_detection = EmailDetector(entity_name=entity_name)
    return email_detection.detect(message=message, structured_value=structured_value, fallback_value=fallback_value,
                                  bot_message=bot_message)


def get_city(message, entity_name, structured_value, fallback_value, bot_message, language, **kwargs):
    """Use CityDetector to detect cities

    Args:
        message (str): natural text on which detection logic is to be run. Note if structured value is
                                detection is run on structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
        structured_value (str): Value obtained from any structured elements. Note if structured value is
                                detection is run on structured value instead of message
                                (For example, UI elements like form, payload, etc)
        fallback_value (str): If the detection logic fails to detect any value either from structured_value
                          or message then we return a fallback_value as an output.
        bot_message (str): previous message from a bot/agent.
        language (str): ISO 639-1 code of language of message


    Returns:
        dict or None: dictionary containing entity_value, original_text and detection;
                      entity_value is in itself a dict with its keys varying from entity to entity

    Example:

        message = 'i want to go to mummbai'
        entity_name = 'city'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_city(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message)
        print output
            //output without model
            >> [{'detection': 'message', 'original_text': 'mummbai',
            'entity_value': {'to': True, 'via': False, 'from': False, 'value': u'Mumbai', 'normal': False}}]

            //output with model
            >>[{'detection': 'model_verified', 'original_text': 'mummbai',
            'entity_value': {'to': True, 'via': False, 'from': False, 'value': u'Mumbai', 'normal': False}}]




        message = "I want to book a flight from delhhi to mumbai"
        entity_name = 'city'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_city(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message)
        print output
            //output without model
            >> [
            {'detection': 'message', 'original_text': 'delhhi',
            'entity_value': {'to': False, 'via': False, 'from': True, 'value': u'New Delhi', 'normal': False}},
            {'detection': 'message', 'original_text': 'mumbai',
            'entity_value': {'to': True, 'via': False, 'from': False, 'value': u'Mumbai', 'normal': False}}]

            //output with model
            >> [
            {'detection': 'model_verified', 'original_text': 'delhhi',
            'entity_value': {'to': False, 'via': False, 'from': True, 'value': u'New Delhi', 'normal': False}},
            {'detection': 'model_verified', 'original_text': 'mumbai',
            'entity_value': {'to': True, 'via': False, 'from': False, 'value': u'Mumbai', 'normal': False}}]


        message = "mummbai"
        entity_name = 'city'
        structured_value = None
        fallback_value = None
        bot_message = "Please help me departure city?"
        output = get_city(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message)
        print output
            //output without model
            >> [{'detection': 'message', 'original_text': 'mummbai',
            'entity_value': {'to': False, 'via': False, 'from': True, 'value': u'Mumbai', 'normal': False}}]

            //output with model
            >> [{'detection': 'model_verified', 'original_text': 'mummbai',
            'entity_value': {'to': False, 'via': False, 'from': True, 'value': u'Mumbai', 'normal': False}}]


    """
    city_detection = CityDetector(entity_name=entity_name, language=language)
    city_detection.set_bot_message(bot_message=bot_message)
    if structured_value:
        entity_dict_list = city_detection.detect_entity(text=structured_value)
        entity_list, original_text_list, detection_method_list = \
            city_detection.convert_city_dict_in_tuple(entity_dict_list=entity_dict_list)
        if entity_list:
            return output_entity_dict_list(entity_value_list=entity_list, original_text_list=original_text_list,
                                           detection_method=FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_list(entity_value_list=[structured_value],
                                           original_text_list=[structured_value],
                                           detection_method=FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        entity_dict_list = city_detection.detect_entity(text=message, run_model=False)
        entity_list, original_text_list, detection_method_list = \
            city_detection.convert_city_dict_in_tuple(entity_dict_list=entity_dict_list)
        if entity_list:
            return output_entity_dict_list(entity_value_list=entity_list, original_text_list=original_text_list,
                                           detection_method_list=detection_method_list)
        elif fallback_value:
            return output_entity_dict_list(entity_value_list=[fallback_value],
                                           original_text_list=[fallback_value],
                                           detection_method=FROM_FALLBACK_VALUE)

    return None


def get_person_name(message, entity_name, structured_value, fallback_value, bot_message,
                    language=ENGLISH_LANG, predetected_values=None, **kwargs):
    """Use NameDetector to detect names

    Args:
        message (str): natural text on which detection logic is to be run. Note if structured value is
                                detection is run on structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
        structured_value (str): Value obtained from any structured elements. Note if structured value is
                                detection is run on structured value instead of message
                                (For example, UI elements like form, payload, etc)
        fallback_value (str): If the detection logic fails to detect any value either from structured_value
                          or message then we return a fallback_value as an output.
        bot_message (str): previous message from a bot/agent.
        language (str): ISO 639-1 code of language of message
        predetected_values(list of str): prior detection results from models like crf etc.


    Returns:
        dict or None: dictionary containing entity_value, original_text and detection;
                      entity_value is in itself a dict with its keys varying from entity to entity

    Example:

        message = 'My name is yash doshi'
        entity_name = 'person_name'
        structured_value = None
        fallback_value = Guest
        bot_message = what is your name ?

            [{'detection': 'message', 'original_text': 'yash doshi',
            'entity_value': {'first_name': yash, 'middle_name': None, 'last_name': doshi}}]
    """
    # TODO refactor NameDetector to make this easy to read and use
    predetected_values = predetected_values or []

    name_detection = NameDetector(entity_name=entity_name, language=language)
    text, detection_method, fallback_text, fallback_method = (structured_value,
                                                              FROM_STRUCTURE_VALUE_VERIFIED,
                                                              structured_value,
                                                              FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    if not structured_value:
        text, detection_method, fallback_text, fallback_method = (message,
                                                                  FROM_MESSAGE,
                                                                  fallback_value,
                                                                  FROM_FALLBACK_VALUE)
    entity_list, original_text_list = [], []

    if text:
        entity_list, original_text_list = name_detection.detect_entity(
            text=text,
            bot_message=bot_message,
            predetected_values=predetected_values)

    if not entity_list and fallback_text:
        entity_list, original_text_list = NameDetector.get_format_name(fallback_text.split(), fallback_text)
        detection_method = fallback_method

    if entity_list and original_text_list:
        # if predetected_values:
        #     detection_method = "free text entity"
        return output_entity_dict_list(entity_list, original_text_list, detection_method)

    return None


def get_pnr(message, entity_name, structured_value, fallback_value, bot_message):
    """Use PNRDetector to detect pnr

    Args:
        message (str): natural text on which detection logic is to be run. Note if structured value is
                                detection is run on structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
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

        message = 'check my pnr status for 2141215305.'
        entity_name = 'train_pnr'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_pnr(message=message, entity_name=entity_name, structured_value=structured_value,
                        fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'message', 'original_text': '2141215305', 'entity_value': {'value': '2141215305'}}]

    """

    pnr_detection = PNRDetector(entity_name=entity_name)
    return pnr_detection.detect(message=message, structured_value=structured_value, fallback_value=fallback_value,
                                bot_message=bot_message)


def get_regex(message, entity_name, structured_value, fallback_value, bot_message, pattern):
    """Use RegexDetector to detect text that abide by the specified
        pattern.
        The meta_data consists the pattern

    Args:
        message (str): natural text on which detection logic is to be run. Note if structured value is
                                detection is run on structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
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

        message = 'abc123'
        entity_name = 'numerals'
        pattern = '\\d+'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_regex(message=message, entity_name=entity_name, structured_value=structured_value,
                           fallback_value=fallback_value, bot_message=bot_message, pattern=pattern)
        print output

            >> [{'detection': 'message', 'original_text': '123', 'entity_value': {'value': '123'}}]

    """
    regex_detector = RegexDetector(entity_name=entity_name, pattern=pattern)
    if structured_value:
        entity_list, original_text_list = regex_detector.detect_entity(text=structured_value)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_list([structured_value], [structured_value], FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        entity_list, original_text_list = regex_detector.detect_entity(text=message)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_MESSAGE)
        elif fallback_value:
            return output_entity_dict_list([fallback_value], [fallback_value], FROM_FALLBACK_VALUE)

    return None


def get_shopping_size(message, entity_name, structured_value, fallback_value, bot_message):
    """Use ShoppingSizeDetector to detect cloth size

    Args:
        message (str): natural text on which detection logic is to be run. Note if structured value is
                                detection is run on structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
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

        message = "I want to buy Large shirt and jeans of 36 waist"
        entity_name = 'shopping_clothes_size'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_shopping_size(message=message, entity_name=entity_name, structured_value=structured_value,
                                   fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'message', 'original_text': 'large', 'entity_value': {'value': u'L'}}, 
                {'detection': 'message', 'original_text': '36', 'entity_value': {'value': '36'}}]

    """
    size_detection = ShoppingSizeDetector(entity_name=entity_name)
    return size_detection.detect(message=message, structured_value=structured_value, fallback_value=fallback_value,
                                 bot_message=bot_message)


def get_passenger_count(message, entity_name, structured_value, fallback_value, bot_message):
    """Use PassengerDetector to detect passenger_count

    Args:
        message (str): natural text on which detection logic is to be run. Note if structured value is present
                       detection is run on structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
        structured_value (str): Value obtained from any structured elements. Note if structured value is present
                                detection is run on structured value instead of message
                                (For example, UI elements like form, payload, etc)
        fallback_value (str): If the detection logic fails to detect any value either from structured_value
                              or message then we return a fallback_value as an output.
        bot_message (str): previous message from a bot/agent.


    Returns:
        dict or None: dictionary containing entity_value, original_text and detection;
                      entity_value is in itself a dict with its keys varying from entity to entity

    Example:

        message = 'Can you please help me to book tickets for 3 people'
        entity_name = 'no_of_adults'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_passenger_count(message=message, entity_name=entity_name, structured_value=structured_value,
                                    fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'message', 'entity_value': {'value': '3'}, 'language': 'en', 'original_text': '3'}]

    """
    passenger_detection = PassengerDetector(entity_name=entity_name)
    passenger_detection.set_bot_message(bot_message=bot_message)
    return passenger_detection.detect(message=message, structured_value=structured_value,
                                      fallback_value=fallback_value, bot_message=bot_message)


def get_number(message, entity_name, structured_value, fallback_value, bot_message, min_digit=None, max_digit=None):
    """Use NumberDetector to detect numerals

    Args:
        message (str): natural text on which detection logic is to be run. Note if structured value is
                                detection is run on structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
        structured_value (str): Value obtained from any structured elements. Note if structured value is
                                detection is run on structured value instead of message
                                (For example, UI elements like form, payload, etc)
        fallback_value (str): If the detection logic fails to detect any value either from structured_value
                          or message then we return a fallback_value as an output.
        bot_message (str): previous message from a bot/agent.
        min_digit (str): min digit
        max_digit (str): max digit


    Returns:
        dict or None: dictionary containing entity_value, original_text and detection;
                      entity_value is in itself a dict with its keys varying from entity to entity

    Example:

        message = "I want to purchase 30 units of mobile and 40 units of Television"
        entity_name = 'number_of_unit'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_number(message=message, entity_name=entity_name, structured_value=structured_value,
                           fallback_value=fallback_value, bot_message=bot_message, min_digit=1, max_digit=2)
        print output

            >> [{'detection': 'message', 'original_text': '30', 'entity_value': {'value': '30'}},
                {'detection': 'message', 'original_text': '40', 'entity_value': {'value': '40'}}]


        message = "I want to reserve a table for 3 people"
        entity_name = 'number_of_people'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_number(message=message, entity_name=entity_name, structured_value=structured_value,
                           fallback_value=fallback_value, bot_message=bot_message, min_digit=1, max_digit=2)
        print output

            >> [{'detection': 'message', 'original_text': 'for 3 people', 'entity_value': {'value': '3'}}]

    """

    number_detection = NumberDetector(entity_name=entity_name)
    if min_digit and max_digit:
        min_digit = int(min_digit)
        max_digit = int(max_digit)
        number_detection.set_min_max_digits(min_digit=min_digit, max_digit=max_digit)
    return number_detection.detect(message=message, structured_value=structured_value, fallback_value=fallback_value,
                                   bot_message=bot_message)


def get_time(message, entity_name, structured_value, fallback_value, bot_message, timezone=None):
    """Use TimeDetector to detect time

    Args:
        message (str): natural text on which detection logic is to be run. Note if structured value is present
                                detection is run on structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
        structured_value (str): Value obtained from any structured elements. Note if structured value is present
                                detection is run on structured value instead of message
                                (For example, UI elements like form, payload, etc)
        fallback_value (str): If the detection logic fails to detect any value either from structured_value
                          or message then we return a fallback_value as an output.
        bot_message (str): previous message from a bot/agent.
        timezone (str): timezone of the user


    Returns:
        dict or None: dictionary containing entity_value, original_text and detection;
                      entity_value is in itself a dict with its keys varying from entity to entity

    Example:

        message = "John arrived at the bus stop at 13:50 hrs, expecting the bus to be there in 15 mins. \
        But the bus was scheduled for 12:30 pm"
        entity_name = 'time'
        structured_value = None
        fallback_value = None
        bot_message = None
        timezone = 'UTC'
        output = get_time(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message, timezone=timezone)
        print output

        >>  [{'detection': 'message', 'original_text': '12:30 pm', 'entity_value': {'mm': 30, 'hh': 12, 'nn': 'pm'}},
            {'detection': 'message', 'original_text': 'in 15 mins', 'entity_value': {'mm': '15', 'hh': 0, 'nn': 'df'}},
            {'detection': 'message', 'original_text': '13:50', 'entity_value': {'mm': 50, 'hh': 13, 'nn': 'hrs'}}]
    """
    form_check = True if structured_value else False
    time_detection = TimeDetector(entity_name=entity_name, timezone=timezone, form_check=form_check)
    time_detection.set_bot_message(bot_message=bot_message)
    return time_detection.detect(message=message, structured_value=structured_value, fallback_value=fallback_value,
                                 bot_message=bot_message)


def get_time_with_range(message, entity_name, structured_value, fallback_value, bot_message, timezone=None):
    """Use TimeDetector to detect time with range

    Args:
        message (str): natural text on which detection logic is to be run. Note if structured value is present
                                detection is run on structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
        structured_value (str): Value obtained from any structured elements. Note if structured value is present
                                detection is run on structured value instead of message
                                (For example, UI elements like form, payload, etc)
        fallback_value (str): If the detection logic fails to detect any value either from structured_value
                          or message then we return a fallback_value as an output.
        bot_message (str): previous message from a bot/agent.
        timezone (str): timezone of the user


    Returns:
        dict or None: dictionary containing entity_value, original_text and detection;
                      entity_value is in itself a dict with its keys varying from entity to entity

    Example:

        message = 'Set a drink water reminder for tomorrow from 7:00 AM to 6:00 PM'
        entity_name = 'time_with_range'
        structured_value = None
        fallback_value = None
        bot_message = None
        timezone = 'UTC'
        output = get_time_with_range(message=message, entity_name=entity_name, structured_value=structured_value,
                                     fallback_value=fallback_value, bot_message=bot_message, timezone=timezone)
        print output

            >> [{'detection': 'message', 'original_text': '7:00 am to 6:00 pm', 'entity_value': {'mm': 0, 'hh': 7,
                 'range': 'start', 'nn': 'am', 'time_type': None}, 'language': 'en'}, {'detection': 'message',
                 'original_text': '7:00 am to 6:00 pm', 'entity_value': {'mm': 0, 'hh': 6, 'range': 'end', 'nn': 'pm',
                 'time_type': None}, 'language': 'en'}]

    """
    form_check = True if structured_value else False
    time_detection = TimeDetector(entity_name=entity_name, timezone=timezone, range_enabled=True,
                                  form_check=form_check)
    return time_detection.detect(message=message, structured_value=structured_value, fallback_value=fallback_value,
                                 bot_message=bot_message)


def get_date(message, entity_name, structured_value, fallback_value, bot_message, timezone='UTC'):
    """Use DateDetector to detect date

    Args:
        message (str): natural text on which detection logic is to be run. Note if structured value is
                                detection is run on structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
        structured_value (str): Value obtained from any structured elements. Note if structured value is
                                detection is run on structured value instead of message
                                (For example, UI elements like form, payload, etc)
        fallback_value (str): If the detection logic fails to detect any value either from structured_value
                          or message then we return a fallback_value as an output.
        bot_message (str): previous message from a bot/agent.
        timezone (str, optional): str identifier for the timezone to use.
                                  E.g. 'Asia/Kolkata'
                                  Please refer pytz docs for this.
                                  Defaults to 'UTC'


    Returns:
        dict or None: dictionary containing entity_value, original_text and detection;
                      entity_value is in itself a dict with its keys varying from entity to entity

    Example:

        message = "set me reminder on 23rd december"
        entity_name = 'date'
        timezone = 'UTC'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_date(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message, timezone = timezone)
        print output

            >> [{'detection': 'message', 'original_text': '23rd december',
            'entity_value': {'mm': 12, 'yy': 2017, 'dd': 23, 'type': 'date'}}]


        message = "set me reminder day after tomorrow"
        entity_name = 'date'
        structured_value = None
        fallback_value = None
        bot_message = None
        timezone = 'UTC'
        output = get_date(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message, timezone = timezone)
        print output

            >> [{'detection': 'message', 'original_text': 'day after tomorrow',
                'entity_value': {'mm': 3, 'yy': 2017, 'dd': 13, 'type': 'day_after'}}]

    """
    if timezone is None:
        timezone = 'UTC'
    date_detection = DateAdvancedDetector(entity_name=entity_name, timezone=timezone)
    date_detection.set_bot_message(bot_message=bot_message)
    if structured_value:
        entity_dict_list = date_detection.detect_entity(text=structured_value)
        entity_list, original_text_list, detection_method_list = \
            date_detection.unzip_convert_date_dictionaries(entity_dict_list=entity_dict_list)
        if entity_list:
            return output_entity_dict_list(entity_value_list=entity_list, original_text_list=original_text_list,
                                           detection_method=FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_list(entity_value_list=[structured_value],
                                           original_text_list=[structured_value],
                                           detection_method=FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        entity_dict_list = date_detection.detect_entity(text=message, run_model=False)
        entity_list, original_text_list, detection_method_list = \
            date_detection.unzip_convert_date_dictionaries(entity_dict_list=entity_dict_list)
        if entity_list:
            return output_entity_dict_list(entity_value_list=entity_list, original_text_list=original_text_list,
                                           detection_method_list=detection_method_list)
        elif fallback_value:
            entity_dict_list = date_detection.detect_entity(text=fallback_value, run_model=False)
            entity_list, original_text_list, detection_method_list = \
                date_detection.unzip_convert_date_dictionaries(entity_dict_list=entity_dict_list)
            return output_entity_dict_list(entity_value_list=entity_list, original_text_list=original_text_list,
                                           detection_method=FROM_FALLBACK_VALUE)

    return None


def get_budget(message, entity_name, structured_value, fallback_value, bot_message, min_digit=None, max_digit=None):
    """Use BudgetDetector to detect budget

    Args:
        message (str): natural text on which detection logic is to be run. Note if structured value is
                                detection is run on structured value instead of message
        entity_name (str): name of the entity. Also acts as elastic-search dictionary name
                           if entity uses elastic-search lookup
        structured_value (str): Value obtained from any structured elements. Note if structured value is
                                detection is run on structured value instead of message
                                (For example, UI elements like form, payload, etc)
        fallback_value (str): If the detection logic fails to detect any value either from structured_value
                          or message then we return a fallback_value as an output.
        bot_message (str): previous message from a bot/agent.
        min_digit (str): min digit
        max_digit (str): max digit


    Returns:
        dict or None: dictionary containing entity_value, original_text and detection;
                      entity_value is in itself a dict with its keys varying from entity to entity

    Example:

        message = "shirts between 2000 to 3000"
        entity_name = 'budget'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_budget(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'message', 'original_text': '2000 to 3000', 'entity_value':
                {'max_budget': 3000, 'type': 'normal_budget', 'min_budget': 2000}}]


    """
    budget_detection = BudgetDetector(entity_name=entity_name, use_text_detection=True)
    if min_digit and max_digit:
        min_digit = int(min_digit)
        max_digit = int(max_digit)
        budget_detection.set_min_max_digits(min_digit=min_digit, max_digit=max_digit)
    return budget_detection.detect(message=message, structured_value=structured_value, fallback_value=fallback_value,
                                   bot_message=bot_message)


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
        if type(entity_value) in [str, six.text_type]:
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


def parse_fuzziness_parameter(fuzziness):
    """
    This function takes input as the fuzziness value.
    If the fuzziness is int it is returned as it is.
    If the input is a ',' separated str value, the function returns a tuple with all values
    present in the str after casting them to int.

    Args:
        fuzziness (str or int): The fuzzines value that needs to be parsed.

    Returns:
        fuzziness (tuple or int): It returns a tuple with of all the values cast to int present in the str.
                                  If the fuzziness is a single element then int is returned

    Examples:
        >>> fuzziness = 2
        >>> parse_fuzziness_parameter(fuzziness)
        2

        >>> fuzziness = '3,4'
        >>> parse_fuzziness_parameter(fuzziness)
        (3, 4)
    """
    try:
        if isinstance(fuzziness, int):
            return fuzziness
        fuzziness_split = fuzziness.split(',')
        if len(fuzziness_split) == 1:
            fuzziness = int(fuzziness)
        else:
            fuzziness = tuple([int(value.strip()) for value in fuzziness_split])
    except ValueError:
        fuzziness = 1
    return fuzziness
