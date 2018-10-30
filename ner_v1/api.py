import ast
import json

from django.http import HttpResponse

from chatbot_ner.config import ner_logger
from ner_v1.chatbot.combine_detection_logic import combine_output_of_detection_logic_and_tag
from ner_v1.chatbot.entity_detection import get_location, get_phone_number, get_email, get_city, get_pnr, \
    get_number, get_passenger_count, get_shopping_size, get_time, get_time_with_range, get_date, get_budget, \
    get_person_name, get_regex
from ner_v1.chatbot.tag_message import run_ner
from ner_v1.constant import PARAMETER_MESSAGE, PARAMETER_ENTITY_NAME, PARAMETER_STRUCTURED_VALUE, \
    PARAMETER_FALLBACK_VALUE, PARAMETER_BOT_MESSAGE, PARAMETER_TIMEZONE, PARAMETER_REGEX, PARAMETER_LANGUAGE_SCRIPT, \
    PARAMETER_SOURCE_LANGUAGE, PARAMETER_MIN_TOKEN_LEN_FUZZINESS, PARAMETER_FUZZINESS, PARAMETER_MIN_DIGITS, \
    PARAMETER_MAX_DIGITS, PARAMETER_READ_MODEL_FROM_S3, PARAMETER_READ_EMBEDDINGS_FROM_REMOTE_URL, PARAMETER_LIVE_CRF_MODEL_PATH
from ner_v1.detectors.textual.text.text_detection_model import TextModelDetector
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
                       PARAMETER_SOURCE_LANGUAGE: request.GET.get('source_language', ENGLISH_LANG),
                       PARAMETER_FUZZINESS: request.GET.get('fuzziness'),
                       PARAMETER_MIN_TOKEN_LEN_FUZZINESS: request.GET.get('min_token_len_fuzziness'),
                       PARAMETER_MIN_DIGITS: request.GET.get('min_number_digits'),
                       PARAMETER_MAX_DIGITS: request.GET.get('max_number_digits'),
                       PARAMETER_READ_EMBEDDINGS_FROM_REMOTE_URL:
                           request.GET.get('read_embeddings_from_remote_url', 'False'),
                       PARAMETER_READ_MODEL_FROM_S3: request.GET.get('read_model_from_s3', 'False'),
                       PARAMETER_LIVE_CRF_MODEL_PATH: request.GET.get('live_crf_model_path')
                       }

    return parameters_dict


def text(request):
    """This functionality initializes text detection functionality to detect textual entities.

    Attributes:
        request: url parameters

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
        fuzziness = parameters_dict[PARAMETER_FUZZINESS]
        min_token_len_fuzziness = parameters_dict[PARAMETER_MIN_TOKEN_LEN_FUZZINESS]
        read_model_from_s3 = json.loads(parameters_dict[PARAMETER_READ_MODEL_FROM_S3].lower())
        read_embeddings_from_remote_url = json.loads(parameters_dict[PARAMETER_READ_EMBEDDINGS_FROM_REMOTE_URL].lower())
        text_model_detector = TextModelDetector(entity_name=parameters_dict[PARAMETER_ENTITY_NAME],
                                                source_language_script=parameters_dict[PARAMETER_LANGUAGE_SCRIPT],
                                                read_model_from_s3=read_model_from_s3,
                                                read_embeddings_from_remote_url=read_embeddings_from_remote_url,
                                                live_crf_model_path=parameters_dict[PARAMETER_LIVE_CRF_MODEL_PATH]
                                                )
        ner_logger.debug('fuzziness: %s min_token_len_fuzziness %s' % (str(fuzziness), str(min_token_len_fuzziness)))
        if fuzziness:
            fuzziness = parse_fuzziness_parameter(fuzziness)
            text_model_detector.set_fuzziness_threshold(fuzziness)

        if min_token_len_fuzziness:
            min_token_len_fuzziness = int(min_token_len_fuzziness)
            text_model_detector.set_min_token_size_for_levenshtein(min_size=min_token_len_fuzziness)

        entity_output = text_model_detector.detect(message=parameters_dict[PARAMETER_MESSAGE],
                                                   structured_value=parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                                   fallback_value=parameters_dict[PARAMETER_FALLBACK_VALUE],
                                                   bot_message=parameters_dict[PARAMETER_BOT_MESSAGE])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except Exception as e:
        ner_logger.exception('Exception for text_synonym: %s ' % e)
        return HttpResponse(status=500)
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
    except TypeError as e:
        ner_logger.exception('Exception for location: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def phone_number(request):
    """This functionality calls the get_phone_number() functionality to detect phone numbers. It is called through
    api call

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
    except TypeError as e:
        ner_logger.exception('Exception for phone_number: %s ' % e)
        return HttpResponse(status=500)

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
    except TypeError as e:
        ner_logger.exception('Exception for regex: %s ' % e)
        return HttpResponse(status=500)

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
    except TypeError as e:
        ner_logger.exception('Exception for email: %s ' % e)
        return HttpResponse(status=500)

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
    except TypeError as e:
        ner_logger.exception('Exception for person_name: %s ' % e)
        return HttpResponse(status=500)

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
    except TypeError as e:
        ner_logger.exception('Exception for city: %s ' % e)
        return HttpResponse(status=500)

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
    except TypeError as e:
        ner_logger.exception('Exception for pnr: %s ' % e)
        return HttpResponse(status=500)

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
    except TypeError as e:
        ner_logger.exception('Exception for shopping_size: %s ' % e)
        return HttpResponse(status=500)

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
                                   parameters_dict[PARAMETER_BOT_MESSAGE],
                                   parameters_dict[PARAMETER_MIN_DIGITS],
                                   parameters_dict[PARAMETER_MAX_DIGITS]
                                   )
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for numeric: %s ' % e)
        return HttpResponse(status=500)

    return HttpResponse(json.dumps({'data': entity_output}), content_type='application/json')


def passenger_count(request):
    """This functionality calls the get_passenger_count() functionality to detect passenger count.
    It is called through api call

    Args:
        request (django.http.request.HttpRequest): HttpRequest object

    Returns:
        response (django.http.response.HttpResponse): HttpResponse object

    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
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


def time(request):
    """This functionality calls the get_time() functionality to detect time. It is called through api call

    Args:
        request (django.http.request.HttpRequest): HttpRequest object
    Returns:
        response (django.http.response.HttpResponse): HttpResponse object
    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
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


def time_with_range(request):
    """This functionality calls the get_time_with_range() functionality to detect time. It is called through api call

    Args:
        request (django.http.request.HttpRequest): HttpRequest object
    Returns:
        response (django.http.response.HttpResponse): HttpResponse object
    """
    try:
        parameters_dict = get_parameters_dictionary(request)
        ner_logger.debug('Start: %s ' % parameters_dict[PARAMETER_ENTITY_NAME])
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
    except TypeError as e:
        ner_logger.exception('Exception for date: %s ' % e)
        return HttpResponse(status=500)

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
                                   parameters_dict[PARAMETER_BOT_MESSAGE],
                                   parameters_dict[PARAMETER_MIN_DIGITS],
                                   parameters_dict[PARAMETER_MAX_DIGITS])
        ner_logger.debug('Finished %s : %s ' % (parameters_dict[PARAMETER_ENTITY_NAME], entity_output))
    except TypeError as e:
        ner_logger.exception('Exception for budget: %s ' % e)
        return HttpResponse(status=500)

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


def parse_fuzziness_parameter(fuzziness):
    """
    This function takes input as the fuzziness value.
    If the fuzziness is int it is returned as it is.
    If the input is a ',' separated str value, the function returns a tuple with all values
    present in the str after casting them to int.
    Args:
        fuzziness (str) or (int): The fuzzines value that needs to be parsed.
    Returns:
        fuzziness (tuple) or (int): It returns a tuple with of all the values cast to int present
        in the str.
        If the fuzziness is a single element then int is returned

    Examples:
        fuzziness = 2
        parse_fuzziness_parameter(fuzziness)
        >> 2

        fuzziness = '3,4'
        parse_fuzziness_parameter(fuzziness)
        >> (3,4)
    """
    try:
        if isinstance(fuzziness, int):
            return fuzziness
        fuzziness_split = fuzziness.split(',')
        if len(fuzziness_split) == 1:
            fuzziness = int(fuzziness)
        else:
            fuzziness = tuple([int(value.strip()) for value in fuzziness_split])
    except ValueError as e:
        fuzziness = 1
    return fuzziness
