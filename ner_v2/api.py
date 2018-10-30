from chatbot_ner.config import ner_logger
from ner_constants import PARAMETER_MESSAGE, PARAMETER_ENTITY_NAME, PARAMETER_STRUCTURED_VALUE, PARAMETER_FALLBACK_VALUE, \
    PARAMETER_BOT_MESSAGE, PARAMETER_TIMEZONE, PARAMETER_REGEX, PARAMETER_LANGUAGE_SCRIPT, PARAMETER_SOURCE_LANGUAGE

from ner_v2.detectors.temporal.date.date_detection import DateAdvancedDetector
from ner_v2.detectors.temporal.time.time_detection import TimeDetector
from language_utilities.constant import ENGLISH_LANG

from django.http import HttpResponse
import json


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
                       PARAMETER_LANGUAGE_SCRIPT: request.GET.get('language_script', ENGLISH_LANG),
                       PARAMETER_SOURCE_LANGUAGE: request.GET.get('source_language', ENGLISH_LANG),
                       }

    return parameters_dict


def date(request):
    """This functionality use DateAdvanceDetector to detect date. It is called through api call

    Args:
        request (django.http.request.HttpRequest): HttpRequest object

        request params:
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
            source_language (str): source language code (ISO 639-1)
            language_script (str): language code of script (ISO 639-1)

    Returns:
        response (django.http.response.HttpResponse): HttpResponse object

    Example:

           message = "agle mahine k 5 tarikh ko mera birthday hai"
           entity_name = 'time'
           structured_value = None
           fallback_value = None
           bot_message = None
           timezone = 'UTC'
           source_language = 'hi'
           language_script = 'en'
           output = date(request)
           print output

           >>  [{'detection': 'message', 'original_text': 'agle mahine k 5 tarikh',
                 'entity_value': {'value': {'mm': 12, 'yy': 2018, 'dd': 5, 'type': 'date'}}}]
    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        timezone = parameters_dict[PARAMETER_TIMEZONE] or 'UTC'
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        date_detection = DateAdvancedDetector(entity_name=parameters_dict[PARAMETER_ENTITY_NAME],
                                              language=parameters_dict[PARAMETER_SOURCE_LANGUAGE],
                                              timezone=timezone)

        date_detection.set_bot_message(bot_message=parameters_dict[PARAMETER_BOT_MESSAGE])

        entity_output = date_detection.detect(message=parameters_dict[PARAMETER_MESSAGE],
                                              structured_value=parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                              fallback_value=parameters_dict[PARAMETER_FALLBACK_VALUE])

        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for date: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def time(request):
    """This functionality use TimeDetector to detect time. It is called through api call

    Args:
        request (django.http.request.HttpRequest): HttpRequest object

        request params:
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
            source_language (str): source language code (ISO 639-1)
            language_script (str): language code of script (ISO 639-1)

    Returns:
        response (django.http.response.HttpResponse): HttpResponse object

    Example:

           message = "kal subah 5 baje mujhe jaga dena"
           entity_name = 'time'
           structured_value = None
           fallback_value = None
           bot_message = None
           timezone = 'UTC'
           source_language = 'hi'
           language_script = 'en'
           output = time(request)
           print output

           >>  [{'detection': 'message', 'original_text': '12:30 pm',
                'entity_value': {'mm': 30, 'hh': 12, 'nn': 'pm'}}]
    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        timezone = parameters_dict[PARAMETER_TIMEZONE] or 'UTC'
        form_check = True if parameters_dict[PARAMETER_STRUCTURED_VALUE] else False
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        time_detection = TimeDetector(entity_name=parameters_dict[PARAMETER_ENTITY_NAME],
                                      language=parameters_dict[PARAMETER_SOURCE_LANGUAGE],
                                      timezone=timezone,
                                      form_check=form_check)

        time_detection.set_bot_message(bot_message=parameters_dict[PARAMETER_BOT_MESSAGE])
        entity_output = time_detection.detect(message=parameters_dict[PARAMETER_MESSAGE],
                                              structured_value=parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                              fallback_value=parameters_dict[PARAMETER_FALLBACK_VALUE])

        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for time: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')
