import concurrent.futures
import functools
import json
import time

import six
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ner_constants import (PARAMETER_MESSAGE, PARAMETER_ENTITY_NAME, PARAMETER_STRUCTURED_VALUE,
                           PARAMETER_FALLBACK_VALUE,
                           PARAMETER_BOT_MESSAGE, PARAMETER_TIMEZONE, PARAMETER_LANGUAGE_SCRIPT,
                           PARAMETER_SOURCE_LANGUAGE,
                           PARAMETER_PAST_DATE_REFERENCED, PARAMETER_MIN_DIGITS, PARAMETER_MAX_DIGITS,
                           PARAMETER_NUMBER_UNIT_TYPE,
                           PARAMETER_LOCALE, PARAMETER_RANGE_ENABLED, PARAMETER_REGEX)
from ner_v1.chatbot.entity_detection import (get_location, get_phone_number, get_email, get_city, get_pnr,
                                             get_number, get_passenger_count, get_shopping_size, get_time,
                                             get_time_with_range, get_date, get_budget,
                                             get_person_name, get_regex, get_text)
from ner_v1.constant import (PARAMETER_FUZZINESS, PARAMETER_MIN_TOKEN_LEN_FUZZINESS,
                             PARAMETER_READ_EMBEDDINGS_FROM_REMOTE_URL, PARAMETER_READ_MODEL_FROM_S3,
                             PARAMETER_LIVE_CRF_MODEL_PATH)
from ner_v2.detectors.numeral.number.number_detection import NumberDetector as NumberDetectorV2
from ner_v2.detectors.numeral.number_range.number_range_detection import NumberRangeDetector as NumberRangeDetectorV2
from ner_v2.detectors.pattern.phone_number.phone_number_detection import PhoneDetector as PhoneDetectorV2
from ner_v2.detectors.temporal.date.date_detection import DateAdvancedDetector as DateAdvancedDetectorV2
from ner_v2.detectors.temporal.time.time_detection import TimeDetector as TimeDetectorV2


def date_v2(parameters_dict):
    entity_name = parameters_dict[PARAMETER_ENTITY_NAME]
    timezone = parameters_dict[PARAMETER_TIMEZONE] or 'UTC'
    past_date_referenced = to_bool(parameters_dict.get(PARAMETER_PAST_DATE_REFERENCED, False))
    date_detection = DateAdvancedDetectorV2(entity_name=parameters_dict[PARAMETER_ENTITY_NAME],
                                            language=parameters_dict[PARAMETER_SOURCE_LANGUAGE],
                                            timezone=timezone,
                                            past_date_referenced=past_date_referenced,
                                            locale=parameters_dict[PARAMETER_LOCALE])
    date_detection.set_bot_message(bot_message=parameters_dict[PARAMETER_BOT_MESSAGE])
    message = parameters_dict[PARAMETER_MESSAGE]
    entity_output = date_detection.detect(message=message,
                                          structured_value=parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                          fallback_value=parameters_dict[PARAMETER_FALLBACK_VALUE])
    return entity_name, entity_output


def time_v2(parameters_dict):
    entity_name = parameters_dict[PARAMETER_ENTITY_NAME]
    timezone = parameters_dict[PARAMETER_TIMEZONE] or None
    form_check = True if parameters_dict[PARAMETER_STRUCTURED_VALUE] else False
    range_enabled = True if parameters_dict[PARAMETER_RANGE_ENABLED] else False
    time_detection = TimeDetectorV2(entity_name=parameters_dict[PARAMETER_ENTITY_NAME],
                                    language=parameters_dict[PARAMETER_SOURCE_LANGUAGE],
                                    timezone=timezone)
    time_detection.set_bot_message(bot_message=parameters_dict[PARAMETER_BOT_MESSAGE])
    message = parameters_dict[PARAMETER_MESSAGE]
    entity_output = time_detection.detect(message=message,
                                          structured_value=parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                          fallback_value=parameters_dict[PARAMETER_FALLBACK_VALUE],
                                          form_check=form_check,
                                          range_enabled=range_enabled)
    return entity_name, entity_output


def number_v2(parameters_dict):
    entity_name = parameters_dict[PARAMETER_ENTITY_NAME]
    number_detection = NumberDetectorV2(entity_name=parameters_dict[PARAMETER_ENTITY_NAME],
                                        language=parameters_dict[PARAMETER_SOURCE_LANGUAGE],
                                        unit_type=parameters_dict[PARAMETER_NUMBER_UNIT_TYPE])

    if parameters_dict[PARAMETER_MIN_DIGITS] and parameters_dict[PARAMETER_MAX_DIGITS]:
        min_digit = int(parameters_dict[PARAMETER_MIN_DIGITS])
        max_digit = int(parameters_dict[PARAMETER_MAX_DIGITS])
        number_detection.set_min_max_digits(min_digit=min_digit, max_digit=max_digit)

    message = parameters_dict[PARAMETER_MESSAGE]
    entity_output = number_detection.detect(message=message,
                                            structured_value=parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                            fallback_value=parameters_dict[PARAMETER_FALLBACK_VALUE],
                                            bot_message=parameters_dict[PARAMETER_BOT_MESSAGE])

    return entity_name, entity_output


def number_range_v2(parameters_dict):
    entity_name = parameters_dict[PARAMETER_ENTITY_NAME]
    number_range_detector = NumberRangeDetectorV2(entity_name=parameters_dict[PARAMETER_ENTITY_NAME],
                                                  language=parameters_dict[PARAMETER_SOURCE_LANGUAGE],
                                                  unit_type=parameters_dict[PARAMETER_NUMBER_UNIT_TYPE])

    message = parameters_dict[PARAMETER_MESSAGE]

    entity_output = number_range_detector.detect(message=message,
                                                 structured_value=parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                                 fallback_value=parameters_dict[PARAMETER_FALLBACK_VALUE],
                                                 bot_message=parameters_dict[PARAMETER_BOT_MESSAGE])
    return entity_name, entity_output


def phone_number_v2(parameters_dict):
    entity_name = parameters_dict[PARAMETER_ENTITY_NAME]
    language = parameters_dict[PARAMETER_SOURCE_LANGUAGE]

    phone_number_detection = PhoneDetectorV2(entity_name=entity_name,
                                             language=language,
                                             locale=parameters_dict[PARAMETER_LOCALE])
    message = parameters_dict[PARAMETER_MESSAGE]

    entity_output = phone_number_detection.detect(message=message,
                                                  structured_value=parameters_dict[PARAMETER_STRUCTURED_VALUE],
                                                  fallback_value=parameters_dict[PARAMETER_FALLBACK_VALUE],
                                                  bot_message=parameters_dict[PARAMETER_BOT_MESSAGE])
    return entity_name, entity_output


def unpacked_executor(parameters_dict, fn):
    parameters_dict['language'] = parameters_dict[PARAMETER_SOURCE_LANGUAGE]
    parameters_dict['pattern'] = parameters_dict[PARAMETER_REGEX]
    return parameters_dict[PARAMETER_ENTITY_NAME], fn(**parameters_dict)


MAP = {
    'v1/text/': functools.partial(unpacked_executor, get_text),
    'v1/location/': functools.partial(unpacked_executor, get_location),
    'v1/phone_number/': functools.partial(unpacked_executor, get_phone_number),
    'v1/email/': functools.partial(unpacked_executor, get_email),
    'v1/city/': functools.partial(unpacked_executor, get_city),
    'v1/pnr/': functools.partial(unpacked_executor, get_pnr),
    'v1/shopping_size/': functools.partial(unpacked_executor, get_shopping_size),
    'v1/passenger_count/': functools.partial(unpacked_executor, get_passenger_count),
    'v1/number/': functools.partial(unpacked_executor, get_number),
    'v1/time/': functools.partial(unpacked_executor, get_time),
    'v1/time_with_range/': functools.partial(unpacked_executor, get_time_with_range),
    'v1/date/': functools.partial(unpacked_executor, get_date),
    'v1/budget/': functools.partial(unpacked_executor, get_budget),
    'v1/person_name/': functools.partial(unpacked_executor, get_person_name),
    'v1/regex/': functools.partial(unpacked_executor, get_regex),
    'v2/date/': date_v2,
    'v2/time/': time_v2,
    'v2/number/': number_v2,
    'v2/phone_number/': phone_number_v2,
    'v2/number_range/': number_range_v2,
}


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


def parse_kwargs(request_data):
    parameters_dict = {
        PARAMETER_MESSAGE: request_data.get('message'),
        PARAMETER_ENTITY_NAME: request_data.get('entity_name'),
        PARAMETER_STRUCTURED_VALUE: request_data.get('structured_value'),
        PARAMETER_FALLBACK_VALUE: request_data.get('fallback_value'),
        PARAMETER_BOT_MESSAGE: request_data.get('bot_message'),
        PARAMETER_TIMEZONE: request_data.get('timezone', 'UTC'),
        PARAMETER_LANGUAGE_SCRIPT: request_data.get('language_script', 'en'),
        PARAMETER_SOURCE_LANGUAGE: request_data.get('source_language', 'en'),
        PARAMETER_MIN_DIGITS: request_data.get('min_number_digits'),
        PARAMETER_MAX_DIGITS: request_data.get('max_number_digits'),
        PARAMETER_NUMBER_UNIT_TYPE: request_data.get('unit_type'),
        PARAMETER_LOCALE: request_data.get('locale'),
        PARAMETER_RANGE_ENABLED: request_data.get('range_enabled'),
        PARAMETER_PAST_DATE_REFERENCED: to_bool(request_data.get('past_date_referenced', False)),
        PARAMETER_REGEX: request_data.get('regex'),
        PARAMETER_FUZZINESS: request_data.get('fuzziness'),
        PARAMETER_MIN_TOKEN_LEN_FUZZINESS: request_data.get('min_token_len_fuzziness'),
        PARAMETER_READ_EMBEDDINGS_FROM_REMOTE_URL: to_bool(request_data.get('read_embeddings_from_remote_url')),
        PARAMETER_READ_MODEL_FROM_S3: to_bool(request_data.get('read_model_from_s3')),
        PARAMETER_LIVE_CRF_MODEL_PATH: request_data.get('live_crf_model_path')
    }

    return parameters_dict


@csrf_exempt
def detect_entities(request):
    response = {'entities': {}, 'exec_time': -1}
    request_data = json.loads(request.body)
    exec_backend = request_data.get('exec_backend')
    if exec_backend is None:
        exec_backend = ''
    exec_backend = exec_backend.strip()
    num_workers = request_data.get('num_workers', 4)
    entities = request_data.get('entities', {})
    start_time = time.time()
    if exec_backend in ['threadpool', 'futures_threadpool', 'processpool', 'futures_processpool']:
        if 'thread' in exec_backend:
            exec_cls = concurrent.futures.ThreadPoolExecutor
        else:
            exec_cls = concurrent.futures.ProcessPoolExecutor
        with exec_cls(max_workers=num_workers) as parallel_executor:
            futures = []
            for entity_name, entity_kwargs in entities.items():
                entity_url_key = entity_kwargs.pop('entity_url_key')
                parsed_kwargs = parse_kwargs(entity_kwargs)
                futures.append(parallel_executor.submit(MAP[entity_url_key], parameters_dict=parsed_kwargs))

            for future in concurrent.futures.as_completed(futures):
                entity_name_, data = future.result()
                response['entities'][entity_name_] = {'data': data}
    else:
        for entity_name, entity_kwargs in entities.items():
            entity_url_key = entity_kwargs.pop('entity_url_key')
            parsed_kwargs = parse_kwargs(entity_kwargs)
            entity_name_, data = MAP[entity_url_key](parameters_dict=parsed_kwargs)
            response['entities'][entity_name_] = {'data': data}
    response['exec_time'] = time.time() - start_time
    return JsonResponse(response)
