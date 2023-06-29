from __future__ import absolute_import
import json
import random

from django.http import HttpResponse
from datastore.datastore import DataStore
from datastore.exceptions import (DataStoreSettingsImproperlyConfiguredException, EngineNotImplementedException,
                                  EngineConnectionException, IndexForTransferException,
                                  AliasForTransferException, NonESEngineTransferException)
from datastore.exceptions import IndexNotFoundException, InvalidESURLException, \
    SourceDestinationSimilarException, \
    InternalBackupException, AliasNotFoundException, PointIndexToAliasException, \
    FetchIndexForAliasException, DeleteIndexFromAliasException
from chatbot_ner.config import ner_logger
from external_api.constants import ENTITY_DATA, ENTITY_NAME, LANGUAGE_SCRIPT, ENTITY_LIST, \
    EXTERNAL_API_DATA, SENTENCES, LANGUAGES

from django.views.decorators.csrf import csrf_exempt

from external_api.lib import dictionary_utils
from external_api.response_utils import external_api_response_wrapper
from external_api.exceptions import APIHandlerException


def get_entity_word_variants(request):
    """
    This function is used obtain the entity dictionary given the dictionary name.
    Args:
        request (HttpResponse): HTTP response from url

    Returns:
        HttpResponse : With data consisting of a list of value variants.
    """
    response = {"success": False, "error": "", "result": []}
    try:
        entity_name = request.GET.get(ENTITY_NAME)
        datastore_obj = DataStore()
        result = datastore_obj.get_entity_dictionary(entity_name=entity_name)

        structured_result = []
        # The list around result.keys() is to make it compatible to python3
        key_list = list(result.keys())
        key_list.sort()
        for value in key_list:
            structured_result.append({'value': value, 'variants': result[value]})
        result = structured_result

        response['result'] = result
        response['success'] = True

    except (DataStoreSettingsImproperlyConfiguredException,
            EngineNotImplementedException,
            EngineConnectionException, FetchIndexForAliasException) as error_message:
        response['error'] = str(error_message)
        ner_logger.exception('Error: %s' % error_message)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    except Exception as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    return HttpResponse(json.dumps(response), content_type='application/json', status=200)


@csrf_exempt
def update_dictionary(request):
    """
    This function is used to update the dictionary entities.
    Args:
        request (HttpResponse): HTTP response from url

    Returns:
        HttpResponse : HttpResponse with appropriate status and error message.
    """
    response = {"success": False, "error": "", "result": []}
    try:
        external_api_data = json.loads(request.POST.get(EXTERNAL_API_DATA))
        entity_name = external_api_data.get(ENTITY_NAME)
        entity_data = external_api_data.get(ENTITY_DATA)
        language_script = external_api_data.get(LANGUAGE_SCRIPT)
        datastore_obj = DataStore()
        datastore_obj.update_entity_data(entity_name=entity_name,
                                         entity_data=entity_data,
                                         language_script=language_script)
        response['success'] = True

    except (DataStoreSettingsImproperlyConfiguredException,
            EngineNotImplementedException,
            EngineConnectionException, FetchIndexForAliasException) as error_message:
        response['error'] = str(error_message)
        ner_logger.exception('Error: %s' % error_message)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    except Exception as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)
    return HttpResponse(json.dumps(response), content_type='application/json', status=200)


@csrf_exempt
def transfer_entities(request):
    """
    This method is used to transfer entities from the source to destination.
    Args:
        request (HttpResponse): HTTP response from url
    Returns:
        HttpResponse : HttpResponse with appropriate status and error message.
    """
    response = {"success": False, "error": "", "result": []}
    try:
        external_api_data = json.loads(request.POST.get(EXTERNAL_API_DATA))
        entity_list = external_api_data.get(ENTITY_LIST)

        datastore_object = DataStore()
        datastore_object.transfer_entities_elastic_search(entity_list=entity_list)
        response['success'] = True

    except (IndexNotFoundException, InvalidESURLException,
            SourceDestinationSimilarException, InternalBackupException, AliasNotFoundException,
            PointIndexToAliasException, FetchIndexForAliasException, DeleteIndexFromAliasException,
            AliasForTransferException, IndexForTransferException, NonESEngineTransferException) as error_message:
        response['error'] = str(error_message)
        ner_logger.exception('Error: %s' % error_message)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    except Exception as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    return HttpResponse(json.dumps(response), content_type='application/json', status=200)


def get_crf_training_data(request):
    """
    This function is used obtain the training data given the entity_name.
     Args:
         request (HttpRequest): HTTP response from url

     Returns:
         HttpResponse : With data consisting of a dictionary consisting of sentence_list and entity_list

     Examples:
         get request params
         key: "entity_name"
         value: "city"
    """
    response = {"success": False, "error": "", "result": []}
    try:
        entity_name = request.GET.get(ENTITY_NAME)
        languages = request.GET.get(LANGUAGES, '')

        languages = languages.split(',') if languages else []

        result = DataStore().get_crf_data_for_entity_name(entity_name=entity_name, languages=languages)

        response['result'] = result
        response['success'] = True

    except (DataStoreSettingsImproperlyConfiguredException,
            EngineNotImplementedException,
            EngineConnectionException, FetchIndexForAliasException) as error_message:
        response['error'] = str(error_message)
        ner_logger.exception('Error: %s' % error_message)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    except Exception as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    return HttpResponse(json.dumps(response), content_type='application/json', status=200)


@csrf_exempt
def update_crf_training_data(request):
    """
    This function is used to update the training data
     Args:
         request (HttpRequest): HTTP response from url
     Returns:
         HttpResponse : HttpResponse with appropriate status and error message.
    Example for data present in
    Post request body
    key: "external_api_data"
    value: {"sentence_list":["hello pratik","hello hardik"], "entity_list":[["pratik"], ["hardik"]],
    "entity_name":"training_try3", "language_script": "en"}
    """
    response = {"success": False, "error": "", "result": []}
    try:
        external_api_data = json.loads(request.POST.get(EXTERNAL_API_DATA))
        sentences = external_api_data.get(SENTENCES)
        entity_name = external_api_data.get(ENTITY_NAME)
        DataStore().update_entity_crf_data(entity_name=entity_name, sentences=sentences)
        response['success'] = True

    except (DataStoreSettingsImproperlyConfiguredException,
            EngineNotImplementedException,
            EngineConnectionException, FetchIndexForAliasException) as error_message:
        response['error'] = str(error_message)
        ner_logger.exception('Error: %s' % error_message)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    except Exception as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)
    return HttpResponse(json.dumps(response), content_type='application/json', status=200)


@csrf_exempt
@external_api_response_wrapper
def entity_language_view(request, entity_name):
    """
    API call to View and Edit the list of languages supported by an entity.
    """
    if request.method == 'GET':
        # Fetch Languages supported by the entity
        ner_logger.debug(f"Entity language view GET : {entity_name}")
        return {
            'supported_languages': dictionary_utils.entity_supported_languages(entity_name)
        }

    elif request.method == 'POST':
        # Update language support in the specified entity
        data = json.loads(request.body.decode(encoding='utf-8'))
        ner_logger.debug(f"Entity language view POST : {data}")
        dictionary_utils.entity_update_languages(entity_name, data.get('supported_languages', []))
        return True

    else:
        raise APIHandlerException("{0} is not allowed.".format(request.method))


@csrf_exempt
@external_api_response_wrapper
def entity_data_view(request, entity_name):
    """
    API call to fetch and edit entity data
    """
    if request.method == 'GET':
        params = request.GET.dict()

        shuffle = (params.get('shuffle', 'false') or '').lower() == 'true'
        try:
            seed = int(params.get('seed', random.randint(0, 1000000000)))
        except ValueError:
            raise APIHandlerException('seed should be sent as a number')

        try:
            size = int(params.get('size', 10))
        except ValueError:
            raise APIHandlerException('size should be sent as a number')

        try:
            pagination_from = int(params.get('from', 0))
        except ValueError:
            raise APIHandlerException('from should be sent as a number')
        ner_logger.debug(f" entity data GET : {params}")
        try:
            return dictionary_utils.search_entity_values(
                entity_name=entity_name,
                value_search_term=params.get('value_search_term', None),
                variant_search_term=params.get('variant_search_term', None),
                empty_variants_only=params.get('empty_variants_only', False),
                shuffle=shuffle,
                offset=pagination_from,
                size=size,
                seed=seed,
            )
        except ValueError as e:
            raise APIHandlerException(str(e)) from e

    elif request.method == 'POST':
        # Update language support in the specified entity
        data = json.loads(request.body.decode(encoding='utf-8'))
        ner_logger.debug(f"Entity data view POST : {data}")
        dictionary_utils.update_entity_records(entity_name, data)
        return True

    else:
        raise APIHandlerException("{0} is not allowed.".format(request.method))


@external_api_response_wrapper
def read_unique_values_for_text_entity(request, entity_name):
    """
    API call to View unique values for text entity.
    """
    if request.method == 'GET':
        try:
            return dictionary_utils.get_entity_unique_values(entity_name=entity_name)
        except (DataStoreSettingsImproperlyConfiguredException,
                EngineNotImplementedException,
                EngineConnectionException, FetchIndexForAliasException) as error_message:
            raise APIHandlerException(str(error_message))
    else:
        raise APIHandlerException("{0} is not allowed.".format(request.method))
