from ner_v1.constant import FROM_STRUCTURE_VALUE_VERIFIED, FROM_STRUCTURE_VALUE_NOT_VERIFIED, FROM_MESSAGE, \
    FROM_FALLBACK_VALUE, ORIGINAL_TEXT, ENTITY_VALUE, DETECTION_METHOD, ENTITY_VALUE_DICT_KEY
from ner_v1.detectors.numeral.budget.budget_detection import BudgetDetector
from ner_v1.detectors.numeral.size.shopping_size_detection import ShoppingSizeDetector
from ner_v1.detectors.textual.city.city_detection import CityDetector
from ner_v1.detectors.temporal.date.date_detection import DateDetector
from ner_v1.detectors.temporal.date.date_detection_advance import DateAdvanceDetector
from ner_v1.detectors.pattern.email.email_detection import EmailDetector
from ner_v1.detectors.numeral.number.number_detection import NumberDetector
from ner_v1.detectors.pattern.phone_number.phone_detection import PhoneDetector
from ner_v1.detectors.pattern.pnr.pnr_detection import PNRDetector
from ner_v1.detectors.textual.text.text_detection import TextDetector
from ner_v1.detectors.temporal.time.time_detection import TimeDetector
from ner_v1.detectors.textual.name.name_detection import NameDetector

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
    message: message on which detection logic needs to run. It is unstructured text from which entity needs to be
    extracted. For example "I want to order pizza"

    entity_name: name of the entity. It is used to run a particular detection logic by looking into the dictionary. In
    detection logic for example, get_text() the entity name will be different based on which entities we need to
    detect. For example, if we want to detect cuisine then entity_name must be "cuisine", for dish entity_name must be
    "dish" and so on. But in few detection logic like get_phone_number(), entity_name does not have any significance as
    detection logic of phone_number won't change based on the entity_name.

    structured_value: it is a value which is obtained from the structured text (For example, UI elements like form,
    payload, etc)

    fallback_value: it is a fallback value. If the detection logic fails to detect any value either from
    structured_value or message then we return a fallback_value as an output.
    This value is derived from third party api or from users profile. For example, if user says "Nearby ATMs". In this
    example user has not provided any information about his location in the chat but, we can pass a fallback_value that
    will contain its location value from its profile or third party api (like geopy, etc)

    bot_message: previous message from a bot/agent. This is an important parameter, many a times the entity value
    relies on the message from the bot/agent i.e. what bot saying or asking.
    For example: bot might ask for departure date to book a flight and user might reply with date.
    Now, it can not be disambiguated whether its departure date or arrival date unless  we know what bot is asking for?
      For example:
      bot: Please help me with date of departure?
      user: 23rd March


Format of entity detection functionality for a chatbot:

The general architecture of executing any detection logic is as follows:
1. We initialize the individual entity detection class by passing necessary parameters
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


def get_text(message, entity_name, structured_value, fallback_value, bot_message):
    """This functionality calls the TextDetector class to detect textual entities

    Attributes:
        NOTE: Explained above

    Output:
        NOTE: Explained above

    For Example:

        message = 'i want to order chinese from  mainland china and pizza from domminos'
        entity_name = 'restaurant'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_text(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'message', 'original_text': 'mainland china', 'entity_value':
            {'value': u'Mainland China'}}, {'detection': 'message', 'original_text': 'domminos',
            'entity_value': {'value': u"Domino's Pizza"}}]



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
    text_detection = TextDetector(entity_name=entity_name)
    if structured_value:
        text_entity_list, original_text_list = text_detection.detect_entity(structured_value)
        if text_entity_list:
            return output_entity_dict_list(text_entity_list, original_text_list, FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_value(structured_value, structured_value, FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        text_entity_list, original_text_list = text_detection.detect_entity(message)
        if text_entity_list:
            return output_entity_dict_list(text_entity_list, original_text_list, FROM_MESSAGE)
        elif fallback_value:
            return output_entity_dict_value(fallback_value, fallback_value, FROM_FALLBACK_VALUE)

    return None


def get_location(message, entity_name, structured_value, fallback_value, bot_message):
    """This functionality calls the TextDetector class to detect location

    TODO: We can improve this by creating separate class for location detection instead of using TextDetector

    Attributes:
        NOTE: Explained above

    Output:
        NOTE: Explained above

    """

    text_detection = TextDetector(entity_name=entity_name)
    if structured_value:
        text_entity_list, original_text_list = text_detection.detect_entity(structured_value)
        if text_entity_list:
            return output_entity_dict_list(text_entity_list, original_text_list, FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_value(structured_value, structured_value, FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        text_entity_list, original_text_list = text_detection.detect_entity(message)
        if text_entity_list:
            return output_entity_dict_list(text_entity_list, original_text_list, FROM_MESSAGE)
        elif fallback_value:
            return output_entity_dict_value(fallback_value, fallback_value, FROM_FALLBACK_VALUE)

    return None


def get_phone_number(message, entity_name, structured_value, fallback_value, bot_message):
    """This functionality calls the PhoneDetector class to detect phone numbers

    Attributes:
        NOTE: Explained above

    Output:
        NOTE: Explained above

    For Example:

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
    if structured_value:
        entity_list, original_text_list = phone_detection.detect_entity(text=structured_value)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_value(structured_value, structured_value, FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        entity_list, original_text_list = phone_detection.detect_entity(text=message)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_MESSAGE)
        elif fallback_value:
            return output_entity_dict_value(fallback_value, fallback_value, FROM_FALLBACK_VALUE)

    return None


def get_email(message, entity_name, structured_value, fallback_value, bot_message):
    """This functionality calls the EmailDetector class to detect email ids

    Attributes:
        NOTE: Explained above

    Output:
        NOTE: Explained above

    For Example:

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
    if structured_value:
        entity_list, original_text_list = email_detection.detect_entity(text=structured_value)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_value(structured_value, structured_value, FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        entity_list, original_text_list = email_detection.detect_entity(text=message)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_MESSAGE)
        elif fallback_value:
            return output_entity_dict_value(fallback_value, fallback_value, FROM_FALLBACK_VALUE)

    return None


def get_city(message, entity_name, structured_value, fallback_value, bot_message):
    """This functionality calls the CityDetector class to detect cities

    Attributes:
        NOTE: Explained above

    Output:
        NOTE: Explained above

    For Example:

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
    city_detection = CityDetector(entity_name=entity_name)
    city_detection.set_bot_message(bot_message=bot_message)
    if structured_value:
        entity_dict_list = city_detection.detect_entity(text=structured_value)
        entity_list, original_text_list, detection_method_list = \
            city_detection.convert_dict_in_tuple(entity_dict_list=entity_dict_list)
        if entity_list:
            return output_entity_dict_list(entity_value_list=entity_list, original_text_list=original_text_list,
                                           detection_method=FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_value(entity_value=structured_value, original_text=structured_value,
                                            detection_method=FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        entity_dict_list = city_detection.detect_entity(text=message, run_model=True)
        entity_list, original_text_list, detection_method_list = \
            city_detection.convert_dict_in_tuple(entity_dict_list=entity_dict_list)
        if entity_list:
            return output_entity_dict_list(entity_value_list=entity_list, original_text_list=original_text_list,
                                           detection_method_list=detection_method_list)
        elif fallback_value:
            return output_entity_dict_value(entity_value=fallback_value, original_text=fallback_value,
                                            detection_method=FROM_FALLBACK_VALUE)

    return None


def get_name(message, entity_name, structured_value, fallback_value, bot_message):
    """This functionality calls the NameDetector class to detect names

    Attributes:
        NOTE: Explained above

    Output:
        NOTE: Explained above

    For Example:

        message = 'My name is yash doshi'
        entity_name = 'name'
        structured_value = None
        fallback_value = Guest
        bot_message = None
        output = get_city(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message)
        print output
            //output without model
            >> [{'detection': 'message', 'original_text': 'yash doshi',
            'entity_value': {'first_name': yash, 'middle_name': None, 'last_name': doshi}}]
    """
    name_detection = NameDetector(entity_name=entity_name)
    if structured_value:
        entity_list, original_text_list = name_detection.detect_entity(text=structured_value)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_value(structured_value, structured_value, FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        entity_list, original_text_list = name_detection.detect_entity(text=message)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_MESSAGE)
        elif fallback_value:
            return output_entity_dict_value(fallback_value, fallback_value, FROM_FALLBACK_VALUE)


def get_pnr(message, entity_name, structured_value, fallback_value, bot_message):
    """This functionality calls the PNRDetector class to detect pnr

    Attributes:
        NOTE: Explained above

    Output:
        NOTE: Explained above

    For Example:

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
    if structured_value:
        entity_list, original_text_list = pnr_detection.detect_entity(text=structured_value)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_value(structured_value, structured_value, FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        entity_list, original_text_list = pnr_detection.detect_entity(text=message)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_MESSAGE)
        elif fallback_value:
            return output_entity_dict_value(fallback_value, fallback_value, FROM_FALLBACK_VALUE)

    return None


def get_shopping_size(message, entity_name, structured_value, fallback_value, bot_message):
    """This functionality calls the ShoppingSizeDetector class to detect cloth size

    Attributes:
        NOTE: Explained above

    Output:
        NOTE: Explained above

    For Example:

        message = "I want to buy Large shirt and jeans of 36 waist"
        entity_name = 'shopping_size'
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

    if structured_value:
        entity_list, original_text_list = size_detection.detect_entity(text=structured_value)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_value(structured_value, structured_value, FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        entity_list, original_text_list = size_detection.detect_entity(text=message)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_MESSAGE)
        elif fallback_value:
            return output_entity_dict_value(fallback_value, fallback_value, FROM_FALLBACK_VALUE)

    return None


def get_number(message, entity_name, structured_value, fallback_value, bot_message):
    """This functionality calls the NumberDetector class to detect numerals

    Attributes:
        NOTE: Explained above

    Output:
        NOTE: Explained above

    For Example:

        message = "I want to purchase 30 units of mobile and 40 units of Television"
        entity_name = 'number_of_unit'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_number(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'message', 'original_text': '30', 'entity_value': {'value': '30'}},
            {'detection': 'message', 'original_text': '40', 'entity_value': {'value': '40'}}]


        message = "I want to reserve a table for 3 people"
        entity_name = 'number_of_people'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_number(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'message', 'original_text': 'for 3 people', 'entity_value': {'value': '3'}}]

    """

    number_detection = NumberDetector(entity_name=entity_name)

    if structured_value:
        entity_list, original_text_list = number_detection.detect_entity(text=structured_value)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_value(structured_value, structured_value, FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        entity_list, original_text_list = number_detection.detect_entity(text=message)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_MESSAGE)
        elif fallback_value:
            return output_entity_dict_value(fallback_value, fallback_value, FROM_FALLBACK_VALUE)

    return None


def get_time(message, entity_name, structured_value, fallback_value, bot_message):
    """This functionality calls the TimeDetector class to detect time

    Attributes:
        NOTE: Explained above

    Output:
        NOTE: Explained above

    For Example:

        message = "John arrived at the bus stop at 13:50 hrs, expecting the bus to be there in 15 mins. \
        But the bus was scheduled for 12:30 pm"
        entity_name = 'time'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_time(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'message', 'original_text': '12:30 pm', 'entity_value': {'mm': 30, 'hh': 12, 'nn': 'pm'}},
            {'detection': 'message', 'original_text': 'in 15 mins', 'entity_value': {'mm': '15', 'hh': 0, 'nn': 'df'}},
            {'detection': 'message', 'original_text': '13:50', 'entity_value': {'mm': 50, 'hh': 13, 'nn': 'hrs'}}]
    """

    time_detection = TimeDetector(entity_name=entity_name)
    if structured_value:
        entity_list, original_text_list = time_detection.detect_entity(text=structured_value, form_check=True)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_value(structured_value, structured_value, FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        entity_list, original_text_list = time_detection.detect_entity(text=message)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_MESSAGE)
        elif fallback_value:
            return output_entity_dict_value(fallback_value, fallback_value, FROM_FALLBACK_VALUE)

    return None


def get_date(message, entity_name, structured_value, fallback_value, bot_message):
    """This functionality calls the DateDetector class to detect date

    Attributes:
        NOTE: Explained above

    Output:
        NOTE: Explained above

    For Example:

        message = "set me reminder on 23rd december"
        entity_name = 'date'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_date(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'message', 'original_text': '23rd december',
            'entity_value': {'mm': 12, 'yy': 2017, 'dd': 23, 'type': 'date'}}]


        message = "set me reminder day after tomorrow"
        entity_name = 'date'
        structured_value = None
        fallback_value = None
        bot_message = None
        output = get_date(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'message', 'original_text': 'day after tomorrow',
                'entity_value': {'mm': 3, 'yy': 2017, 'dd': 13, 'type': 'day_after'}}]

    """
    date_detection = DateDetector(entity_name=entity_name)
    if structured_value:
        entity_list, original_text_list = date_detection.detect_entity(text=structured_value)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_value(structured_value, structured_value, FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        entity_list, original_text_list = date_detection.detect_entity(text=message)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_MESSAGE)
        elif fallback_value:
            return output_entity_dict_value(fallback_value, fallback_value, FROM_FALLBACK_VALUE)

    return None


def get_budget(message, entity_name, structured_value, fallback_value, bot_message):
    """This functionality calls the BudgetDetector class to detect budget

    Attributes:
        NOTE: Explained above

    Output:
        NOTE: Explained above

    For Example:

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
    budget_detection = BudgetDetector(entity_name=entity_name)
    if structured_value:
        entity_list, original_text_list = budget_detection.detect_entity(text=structured_value)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_value(structured_value, structured_value, FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        entity_list, original_text_list = budget_detection.detect_entity(text=message)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_MESSAGE)
        elif fallback_value:
            return output_entity_dict_value(fallback_value, fallback_value, FROM_FALLBACK_VALUE)

    return None


def get_date_advance(message, entity_name, structured_value, fallback_value, bot_message):
    """This functionality calls the DateAdvanceDetector class to detect departure date and arrival date.
    We can add different properties of date detection in this class

    Attributes:
        NOTE: Explained above

    Output:
        NOTE: Explained above

    For Example:

        message = "21/2/17"
        entity_name = 'date'
        structured_value = None
        fallback_value = None
        bot_message = 'Please help me with return date?'
        output = get_date_advance(message=message, entity_name=entity_name, structured_value=structured_value,
                          fallback_value=fallback_value, bot_message=bot_message)
        print output

            >> [{'detection': 'message', 'original_text': '21/2/17',
            'entity_value': {'date_return': {'mm': 2, 'yy': 2017, 'dd': 21, 'type': 'date'}, 'date_departure': None}}]

    """
    date_detection = DateAdvanceDetector(entity_name=entity_name)
    date_detection.set_bot_message(bot_message=bot_message)
    if structured_value:
        entity_list, original_text_list = date_detection.detect_entity(text=structured_value)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_STRUCTURE_VALUE_VERIFIED)
        else:
            return output_entity_dict_value(structured_value, structured_value, FROM_STRUCTURE_VALUE_NOT_VERIFIED)
    else:
        entity_list, original_text_list = date_detection.detect_entity(text=message)
        if entity_list:
            return output_entity_dict_list(entity_list, original_text_list, FROM_MESSAGE)
        elif fallback_value:
            return output_entity_dict_value(fallback_value, fallback_value, FROM_FALLBACK_VALUE)

    return None


def output_entity_dict_list(entity_value_list=None, original_text_list=None, detection_method=None,
                            detection_method_list=None):
    """This function will return the list of dictionary as an output.

    Attributes:
        entity_value_list: list of entity values which are identified from given detection logic
        original_text_list: list original values or actual values from message/structured_value which are identified
        detection_method: this will store how the entity is detected i.e. whether from message, structured_value or
        fallback, verified from model or not.
        detection_method_list: this will store how the entity is detected in the list format.

    Output:
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
    count = 0
    if entity_value_list:
        while count < len(entity_value_list):
            if type(entity_value_list[count]) in [str, unicode]:
                entity_value_list[count] = {
                    ENTITY_VALUE_DICT_KEY: entity_value_list[count]
                }
            if detection_method_list:
                entity_list.append(
                    {
                        ENTITY_VALUE: entity_value_list[count],
                        DETECTION_METHOD: detection_method_list[count],
                        ORIGINAL_TEXT: original_text_list[count]
                    }
                )
            else:
                entity_list.append(
                    {
                        ENTITY_VALUE: entity_value_list[count],
                        DETECTION_METHOD: detection_method,
                        ORIGINAL_TEXT: original_text_list[count]
                    }
                )

            count += 1

    return entity_list


def output_entity_dict_value(entity_value=None, original_text=None, detection_method=None):
    """This function will return the list of dictionary as an output.
    It similar to output_entity_dict_list() except the parameters/attributes

    Attributes:
        entity_value: entity value which are identified from given detection logic
        original_text: original value or actual values from message/structured_value which are identified
        detection_method: this will store how the entity is detected i.e. whether from message, structured_value or
        fallback.

    Output:
        [
            {
                "entity_value": entity_value,
                "detection": detection_method,
                "original_text": original_text
            }
        ]
    """
    if type(entity_value) in [str, unicode]:
        entity_value = {
            ENTITY_VALUE_DICT_KEY: entity_value
        }

    entity_list = [
        {
            ENTITY_VALUE: entity_value,
            DETECTION_METHOD: detection_method,
            ORIGINAL_TEXT: original_text
        }
    ]
    return entity_list
