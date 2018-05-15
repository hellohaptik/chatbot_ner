import ast
import json

from django.http import HttpResponse

from chatbot_ner.config import ner_logger
from ner_v1.chatbot.combine_detection_logic import combine_output_of_detection_logic_and_tag
from ner_v1.chatbot.entity_detection import get_location, get_phone_number, get_email, get_city, get_pnr, \
    get_number, get_shopping_size, get_time, get_date, get_budget, get_person_name, get_regex
from ner_v1.chatbot.tag_message import run_ner
from ner_v1.constant import PARAMETER_MESSAGE, PARAMETER_ENTITY_NAME, PARAMETER_STRUCTURED_VALUE, \
    PARAMETER_FALLBACK_VALUE, PARAMETER_BOT_MESSAGE, PARAMETER_TIMEZONE, PARAMETER_REGEX, PARAMETER_LANGUAGE_SCRIPT, \
    PARAMETER_SOURCE_LANGUAGE
from ner_v1.detectors.textual.text.text_detection import TextDetector
from ner_v1.language_utilities.constant import ENGLISH_LANG


def get_parameters_dictionary(request):
    """Returns the list of parameters require for NER
    
        Params
            request (HttpResponse)
                HTTP response from url
        Returns
           parameters_dict (json)
                parameter dictionary
    """
    parameters_dict = {PARAMETER_MESSAGE: request.GET.get('message'),
                       PARAMETER_ENTITY_NAME: request.GET.get('entity_name'),
                       PARAMETER_STRUCTURED_VALUE: request.GET.get('structured_value'),
                       PARAMETER_FALLBACK_VALUE: request.GET.get('fallback_value'),
                       PARAMETER_BOT_MESSAGE: request.GET.get('bot_message'),
                       PARAMETER_TIMEZONE: request.GET.get('timezone'),
                       PARAMETER_REGEX: request.GET.get('regex'),
                       PARAMETER_LANGUAGE_SCRIPT: request.GET.get('language_script', ENGLISH_LANG),
                       PARAMETER_SOURCE_LANGUAGE: request.GET.get('source_language', ENGLISH_LANG)}

    return parameters_dict


def text(request):
    """This functionality initializes text detection functionality to detect textual entities.

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        text_detector = TextDetector(entity_name=PARAMETER_ENTITY_NAME,
                                     source_language_script=PARAMETER_LANGUAGE_SCRIPT)
        entity_output = text_detector.detect(message=parameters_dict[PARAMETER_MESSAGE],
                                             structured_value=parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                             fallback_value=parameters_dict[PARAMETER_FALLBACK_VALUE],
                                             bot_message=parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError, e:
        ner_logger.debug('Exception for text_synonym: %s ' % e)
        return HttpResponse(status=400)
    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def location(request):
    """This functionality calls the get_location() functionality to detect location. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        entity_output = get_location(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                     parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                     parameters_dict[PARAMETER_FALLBACK_VALUE],
                                     parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError, e:
        ner_logger.debug('Exception for location: %s ' % e)
        return HttpResponse(status=400)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def phone_number(request):
    """This functionality calls the get_phone_number() functionality to detect phone numbers. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        entity_output = get_phone_number(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                         parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                         parameters_dict[PARAMETER_FALLBACK_VALUE],
                                         parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError, e:
        ner_logger.debug('Exception for phone_number: %s ' % e)
        return HttpResponse(status=400)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def regex(request):
    """This functionality calls the get_regex() functionality to detect text those abide by the specified regex.
    It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        entity_output = get_regex(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                  parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                  parameters_dict[PARAMETER_FALLBACK_VALUE],
                                  parameters_dict[PARAMETER_BOT_MESSAGE],
                                  parameters_dict[PARAMETER_REGEX])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError, e:
        ner_logger.debug('Exception for regex: %s ' % e)
        return HttpResponse(status=400)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def email(request):
    """This functionality calls the get_email() functionality to detect email. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        entity_output = get_email(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                  parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                  parameters_dict[PARAMETER_FALLBACK_VALUE],
                                  parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError, e:
        ner_logger.debug('Exception for email: %s ' % e)
        return HttpResponse(status=400)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def person_name(request):
    """This functionality calls the get_name() functionality to detect name. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        entity_output = get_person_name(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                        parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                        parameters_dict[PARAMETER_FALLBACK_VALUE],
                                        parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError, e:
        ner_logger.debug('Exception for person_name: %s ' % e)
        return HttpResponse(status=400)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def city(request):
    """This functionality calls the get_city() functionality to detect city. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        entity_output = get_city(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                 parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                 parameters_dict[PARAMETER_FALLBACK_VALUE],
                                 parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError, e:
        ner_logger.debug('Exception for city: %s ' % e)
        return HttpResponse(status=400)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def pnr(request):
    """This functionality calls the get_pnr() functionality to detect pnr. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        entity_output = get_pnr(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                parameters_dict[PARAMETER_FALLBACK_VALUE],
                                parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError, e:
        ner_logger.debug('Exception for pnr: %s ' % e)
        return HttpResponse(status=400)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def shopping_size(request):
    """This functionality calls the get_shopping_size() functionality to detect size. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        entity_output = get_shopping_size(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                          parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                          parameters_dict[PARAMETER_FALLBACK_VALUE],
                                          parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError, e:
        ner_logger.debug('Exception for shopping_size: %s ' % e)
        return HttpResponse(status=400)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def number(request):
    """This functionality calls the get_numeric() functionality to detect numbers. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        entity_output = get_number(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                   parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                   parameters_dict[PARAMETER_FALLBACK_VALUE],
                                   parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError, e:
        ner_logger.debug('Exception for numeric: %s ' % e)
        return HttpResponse(status=400)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def time(request):
    """This functionality calls the get_time() functionality to detect time. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        entity_output = get_time(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                 parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                 parameters_dict[PARAMETER_FALLBACK_VALUE],
                                 parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError, e:
        ner_logger.debug('Exception for time: %s ' % e)
        return HttpResponse(status=400)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def date(request):
    """This functionality calls the get_date() functionality to detect date. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        entity_output = get_date(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                 parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                 parameters_dict[PARAMETER_FALLBACK_VALUE],
                                 parameters_dict[PARAMETER_BOT_MESSAGE],
                                 parameters_dict[PARAMETER_TIMEZONE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError, e:
        ner_logger.debug('Exception for date: %s ' % e)
        return HttpResponse(status=400)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def budget(request):
    """This functionality calls the get_budget() functionality to detect budget. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        entity_output = get_budget(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                   parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                   parameters_dict[PARAMETER_FALLBACK_VALUE],
                                   parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError, e:
        entity_output = {}
        ner_logger.debug('Exception for budget: %s ' % e)
        return HttpResponse(status=400)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def ner(request):
    """This functionality calls the run_ner() functionality to tag the message .
    It is called through api call

    Attributes:
        request: url parameters

    """
    message = request.GET.get('message')
    entities_data = request.GET.get('entities', [])
    entities = []
    if entities_data:
        entities = ast.literal_eval(entities_data)
    ner_logger.debug('Start: %s -- %s' % (message, entities))
    output = run_ner(entities=entities, message=message)
    ner_logger.debug('Finished %s : %s ' % (message, output))
    return HttpResponse(json.dumps({'data': output}), content_type='application/json')


def combine_output(request):
    """This functionality calls the combine_output_of_detection_logic_and_tag()  through api call

    Attributes:
        request: url parameters

    """
    message = request.GET.get('message')
    entity_data = request.GET.get('entity_data', '{}')
    entity_data_json = json.loads(entity_data)
    ner_logger.debug('Start: %s ' % message)
    output = combine_output_of_detection_logic_and_tag(entity_data=entity_data_json, text=message)
    ner_logger.debug('Finished %s : %s ' % (message, output))
    return HttpResponse(json.dumps({'data': output}), content_type='application/json')
