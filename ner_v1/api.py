from __future__ import absolute_import

import ast
import json

import six
from django.http import HttpResponse
from elasticsearch import exceptions as es_exceptions

from chatbot_ner.config import ner_logger
from datastore.exceptions import DataStoreRequestException
from language_utilities.constant import ENGLISH_LANG
from ner_constants import (PARAMETER_MESSAGE, PARAMETER_ENTITY_NAME, PARAMETER_STRUCTURED_VALUE,
                           PARAMETER_FALLBACK_VALUE, PARAMETER_BOT_MESSAGE, PARAMETER_TIMEZONE, PARAMETER_REGEX,
                           PARAMETER_LANGUAGE_SCRIPT, PARAMETER_SOURCE_LANGUAGE, PARAMETER_PRIOR_RESULTS)

from ner_v1.chatbot.combine_detection_logic import combine_output_of_detection_logic_and_tag
from ner_v1.chatbot.entity_detection import (get_location, get_phone_number, get_email, get_city, get_pnr,
                                             get_number, get_passenger_count, get_shopping_size, get_time,
                                             get_time_with_range, get_date, get_budget,
                                             get_person_name, get_regex, get_text)
from ner_v1.chatbot.tag_message import run_ner
from ner_v1.constant import (PARAMETER_MIN_TOKEN_LEN_FUZZINESS, PARAMETER_FUZZINESS, PARAMETER_MIN_DIGITS,
                             PARAMETER_MAX_DIGITS, PARAMETER_READ_MODEL_FROM_S3,
                             PARAMETER_READ_EMBEDDINGS_FROM_REMOTE_URL,
                             PARAMETER_LIVE_CRF_MODEL_PATH)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


def to_bool(value):
    # type: (Union[str, unicode, bool, int, None]) -> bool
    if isinstance(value, bool):
        return value

    if not value:
        return False

    if isinstance(value, (int, float)):
        return bool(value)

    if isinstance(value, (str, six.text_type)):
        return value.lower() == 'true'

    return False


def get_parameters_dictionary(request):
    # type: (django.http.HttpRequest) -> Dict[str, Any]
    """
    Extract GET parameters from HTTP request

    Args:
        request (django.http.HttpRequest): HTTP response from url

    Returns:
       dict: GET parameters from the request
    """
    parameters_dict = {
        PARAMETER_MESSAGE: request.GET.get('message'),
        PARAMETER_ENTITY_NAME: request.GET.get('entity_name'),
        PARAMETER_STRUCTURED_VALUE: request.GET.get('structured_value'),
        PARAMETER_FALLBACK_VALUE: request.GET.get('fallback_value'),
        PARAMETER_BOT_MESSAGE: request.GET.get('bot_message'),
        PARAMETER_TIMEZONE: request.GET.get('timezone'),
        PARAMETER_REGEX: request.GET.get('regex'),
        PARAMETER_LANGUAGE_SCRIPT: request.GET.get('language_script', ENGLISH_LANG),
        PARAMETER_SOURCE_LANGUAGE: request.GET.get('source_language', ENGLISH_LANG),
        PARAMETER_FUZZINESS: request.GET.get('fuzziness'),
        PARAMETER_MIN_TOKEN_LEN_FUZZINESS: request.GET.get('min_token_len_fuzziness'),
        PARAMETER_MIN_DIGITS: request.GET.get('min_number_digits'),
        PARAMETER_MAX_DIGITS: request.GET.get('max_number_digits'),
        PARAMETER_READ_EMBEDDINGS_FROM_REMOTE_URL: to_bool(request.GET.get('read_embeddings_from_remote_url')),
        PARAMETER_READ_MODEL_FROM_S3: to_bool(request.GET.get('read_model_from_s3')),
        PARAMETER_LIVE_CRF_MODEL_PATH: request.GET.get('live_crf_model_path'),
        PARAMETER_PRIOR_RESULTS: json.loads(request.GET.get("predetected_values", '[]'))
    }
    ner_logger.debug("parameters dict - {}".format(parameters_dict))
    return parameters_dict


def parse_post_request(request):
    # type: (django.http.HttpRequest) -> Dict[str, Any]
    """
    Extract POST request body from HTTP request

    Args:
        request (django.http.HttpRequest): HTTP response from url

    Returns:
       dict: parameters from the request
    """
    request_data = json.loads(request.body)
    parameters_dict = {
        PARAMETER_MESSAGE: request_data.get('message'),
        PARAMETER_ENTITY_NAME: request_data.get('entity_name'),
        PARAMETER_STRUCTURED_VALUE: request_data.get('structured_value'),
        PARAMETER_FALLBACK_VALUE: request_data.get('fallback_value'),
        PARAMETER_BOT_MESSAGE: request_data.get('bot_message'),
        PARAMETER_TIMEZONE: request_data.get('timezone'),
        PARAMETER_REGEX: request_data.get('regex'),
        PARAMETER_LANGUAGE_SCRIPT: request_data.get('language_script', ENGLISH_LANG),
        PARAMETER_SOURCE_LANGUAGE: request_data.get('source_language', ENGLISH_LANG),
        PARAMETER_FUZZINESS: request_data.get('fuzziness'),
        PARAMETER_MIN_TOKEN_LEN_FUZZINESS: request_data.get('min_token_len_fuzziness'),
        PARAMETER_MIN_DIGITS: request_data.get('min_number_digits'),
        PARAMETER_MAX_DIGITS: request_data.get('max_number_digits'),
        PARAMETER_READ_EMBEDDINGS_FROM_REMOTE_URL: to_bool(request_data.get('read_embeddings_from_remote_url')),
        PARAMETER_READ_MODEL_FROM_S3: to_bool(request_data.get('read_model_from_s3')),
        PARAMETER_LIVE_CRF_MODEL_PATH: request_data.get('live_crf_model_path'),
        PARAMETER_PRIOR_RESULTS: request_data.get("predetected_values", [])
    }

    ner_logger.debug("parameters dict - {}".format(parameters_dict))

    return parameters_dict


def parse_parameters_from_request(request):
    """
    Parse parameters from request based on the method type.
    It will return a parameters dict.

    Args:
        request (django.http.HttpRequest): HTTP response from url

    Returns:
       dict: parameters from the request
    """
    parameters_dict = {}
    if request.method == "POST":
        parameters_dict = parse_post_request(request)
        ner_logger.debug('Start POST : %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
    elif request.method == "GET":
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start GET : %s ' % parameters_dict[PARAMETER_ENTITY_NAME])

    return parameters_dict


@require_http_methods(["GET", "POST"])
@csrf_exempt
def text(request):
    """
    Run text detector with crf model on the 'message or list of messages' passed in the request

    Args:
        request (django.http.HttpRequest): HTTP response from url

    Returns:
        response (django.http.HttpResponse): HttpResponse object containing "entity_output"

        where "entity_output" is :
            list of dict: containing dict of detected entities with their original texts for a message
                OR
            list of lists: containing dict of detected entities with their original texts for each message in the list

        EXAMPLES:
        --- Single message
            >>> message = u'i want to order chinese from  mainland china and pizza from domminos'
            >>> entity_name = 'restaurant'
            >>> structured_value = None
            >>> fallback_value = None
            >>> bot_message = None
            >>> entity_output = get_text(message=message,
            >>>                   entity_name=entity_name,
            >>>                   structured_value=structured_value,
            >>>                   fallback_value=fallback_value,
            >>>                   bot_message=bot_message)
            >>> print(entity_output)

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
            >>> entity_output = get_text(message=message,
            >>>                   entity_name=entity_name,
            >>>                   structured_value=structured_value,
            >>>                   fallback_value=fallback_value,
            >>>                   bot_message=bot_message)
            >>> print(entity_output)

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
            >>> entity_output = get_text(message=message,
            >>>                   entity_name=entity_name,
            >>>                   structured_value=structured_value,
            >>>                   fallback_value=fallback_value,
            >>>                   bot_message=bot_message)
            >>> print(entity_output)

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
            >>> entity_name = u'city'
            >>> entity_output = get_text(message=message,
            >>>                   entity_name=entity_name,
            >>>                   structured_value=structured_value,
            >>>                   fallback_value=fallback_value,
            >>>                   bot_message=bot_message)
            >>> print(entity_output)

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
    try:
        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_text(
            message=parameters_dict[PARAMETER_MESSAGE],
            entity_name=parameters_dict[PARAMETER_ENTITY_NAME],
            structured_value=parameters_dict[PARAMETER_STRUCTURED_VALUE],
            fallback_value=parameters_dict[PARAMETER_FALLBACK_VALUE],
            bot_message=parameters_dict[PARAMETER_BOT_MESSAGE],
            language=parameters_dict[PARAMETER_SOURCE_LANGUAGE],
            fuzziness=parameters_dict[PARAMETER_FUZZINESS],
            min_token_len_fuzziness=parameters_dict[PARAMETER_MIN_TOKEN_LEN_FUZZINESS],
            live_crf_model_path=parameters_dict[PARAMETER_LIVE_CRF_MODEL_PATH],
            read_model_from_s3=parameters_dict[PARAMETER_READ_MODEL_FROM_S3],
            read_embeddings_from_remote_url=parameters_dict[PARAMETER_READ_EMBEDDINGS_FROM_REMOTE_URL],
            predetected_values=parameters_dict[PARAMETER_PRIOR_RESULTS]
        )
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except DataStoreRequestException as err:
        ner_logger.exception(f"Error in requesting ES {request.path}, error: {err}, query: {err.request},"
                             f" response: {err.response}")
        return HttpResponse(status=500)
    except es_exceptions.ConnectionTimeout as err:
        ner_logger.exception(f"Error in text_synonym for: {request.path}, error: {err}")
        return HttpResponse(status=500)
    except es_exceptions.ConnectionError as err:
        ner_logger.exception(f"Error in text_synonym for:  {request.path}, error: {err}")
        return HttpResponse(status=500)
    except (TypeError, KeyError) as err:
        ner_logger.exception(f"Error in text_synonym for: {request.path}, error: {err}")
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def location(request):
    """This functionality calls the get_location() functionality to detect location. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_location(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                     parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                     parameters_dict[PARAMETER_FALLBACK_VALUE],
                                     parameters_dict[PARAMETER_BOT_MESSAGE],
                                     predetected_values=parameters_dict[PARAMETER_PRIOR_RESULTS])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for location: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def phone_number(request):
    """This functionality calls the get_phone_number() functionality to detect phone numbers. It is called through
    api call

    Attributes:
        request: url parameters

    """
    try:

        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_phone_number(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                         parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                         parameters_dict[PARAMETER_FALLBACK_VALUE],
                                         parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for phone_number: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def regex(request):
    """This functionality calls the get_regex() functionality to detect text those abide by the specified regex.
    It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_regex(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                  parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                  parameters_dict[PARAMETER_FALLBACK_VALUE],
                                  parameters_dict[PARAMETER_BOT_MESSAGE],
                                  parameters_dict[PARAMETER_REGEX])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for regex: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def email(request):
    """This functionality calls the get_email() functionality to detect email. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_email(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                  parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                  parameters_dict[PARAMETER_FALLBACK_VALUE],
                                  parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for email: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def person_name(request):
    """This functionality calls the get_name() functionality to detect name. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_person_name(message=parameters_dict[PARAMETER_MESSAGE],
                                        entity_name=parameters_dict[PARAMETER_ENTITY_NAME],
                                        structured_value=parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                        fallback_value=parameters_dict[PARAMETER_FALLBACK_VALUE],
                                        bot_message=parameters_dict[PARAMETER_BOT_MESSAGE],
                                        language=parameters_dict[PARAMETER_SOURCE_LANGUAGE],
                                        predetected_values=parameters_dict[PARAMETER_PRIOR_RESULTS])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for person_name: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def city(request):
    """This functionality calls the get_city() functionality to detect city. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_city(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                 parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                 parameters_dict[PARAMETER_FALLBACK_VALUE],
                                 parameters_dict[PARAMETER_BOT_MESSAGE],
                                 parameters_dict[PARAMETER_SOURCE_LANGUAGE]
                                 )
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for city: %s ' % e)
        return HttpResponse(status=500)
    except KeyError as e:
        ner_logger.exception('Exception for text_synonym: %s ' % e)
        return HttpResponse(status=500)
    except es_exceptions.ConnectionTimeout as e:
        ner_logger.exception('Exception for text_synonym: %s ' % e)
        return HttpResponse(status=500)
    except es_exceptions.ConnectionError as e:
        ner_logger.exception('Exception for text_synonym: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def pnr(request):
    """This functionality calls the get_pnr() functionality to detect pnr. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_pnr(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                parameters_dict[PARAMETER_FALLBACK_VALUE],
                                parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for pnr: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def shopping_size(request):
    """This functionality calls the get_shopping_size() functionality to detect size. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_shopping_size(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                          parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                          parameters_dict[PARAMETER_FALLBACK_VALUE],
                                          parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for shopping_size: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def number(request):
    """This functionality calls the get_numeric() functionality to detect numbers. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_number(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                   parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                   parameters_dict[PARAMETER_FALLBACK_VALUE],
                                   parameters_dict[PARAMETER_BOT_MESSAGE],
                                   parameters_dict[PARAMETER_MIN_DIGITS],
                                   parameters_dict[PARAMETER_MAX_DIGITS]
                                   )
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for numeric: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def passenger_count(request):
    """This functionality calls the get_passenger_count() functionality to detect passenger count.
    It is called through api call

    Args:
        request (django.http.request.HttpRequest): HttpRequest object

    Returns:
        response (django.http.response.HttpResponse): HttpResponse object

    """
    try:
        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_passenger_count(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                            parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                            parameters_dict[PARAMETER_FALLBACK_VALUE],
                                            parameters_dict[PARAMETER_BOT_MESSAGE]
                                            )
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for passenger count: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def time(request):
    """This functionality calls the get_time() functionality to detect time. It is called through api call

    Args:
        request (django.http.request.HttpRequest): HttpRequest object
    Returns:
        response (django.http.response.HttpResponse): HttpResponse object
    """
    try:
        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_time(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                 parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                 parameters_dict[PARAMETER_FALLBACK_VALUE],
                                 parameters_dict[PARAMETER_BOT_MESSAGE],
                                 parameters_dict[PARAMETER_TIMEZONE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for time: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def time_with_range(request):
    """This functionality calls the get_time_with_range() functionality to detect time. It is called through api call

    Args:
        request (django.http.request.HttpRequest): HttpRequest object
    Returns:
        response (django.http.response.HttpResponse): HttpResponse object
    """
    try:
        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_time_with_range(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                            parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                            parameters_dict[PARAMETER_FALLBACK_VALUE],
                                            parameters_dict[PARAMETER_BOT_MESSAGE],
                                            parameters_dict[PARAMETER_TIMEZONE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except Exception as e:
        ner_logger.exception('Exception for time_with_range: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def date(request):
    """This functionality calls the get_date() functionality to detect date. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_date(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                 parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                 parameters_dict[PARAMETER_FALLBACK_VALUE],
                                 parameters_dict[PARAMETER_BOT_MESSAGE],
                                 parameters_dict[PARAMETER_TIMEZONE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for date: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def budget(request):
    """This functionality calls the get_budget() functionality to detect budget. It is called through api call

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = parse_parameters_from_request(request)
        entity_output = get_budget(parameters_dict[PARAMETER_MESSAGE], parameters_dict[PARAMETER_ENTITY_NAME],
                                   parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                   parameters_dict[PARAMETER_FALLBACK_VALUE],
                                   parameters_dict[PARAMETER_BOT_MESSAGE],
                                   parameters_dict[PARAMETER_MIN_DIGITS],
                                   parameters_dict[PARAMETER_MAX_DIGITS])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for budget: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


@require_http_methods(["GET", "POST"])
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


@require_http_methods(["GET", "POST"])
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
