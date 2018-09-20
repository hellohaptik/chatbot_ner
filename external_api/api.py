import json
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
    EXTERNAL_API_DATA, SENTENCE_LIST, CLOUD_STORAGE, ES_CONFIG, CLOUD_EMBEDDINGS, LIVE_CRF_MODEL_PATH

from django.views.decorators.csrf import csrf_exempt
from models.crf_v2.crf_train import CrfTrain


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

    except BaseException as e:
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

    except BaseException as e:
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

    except BaseException as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    return HttpResponse(json.dumps(response), content_type='application/json', status=200)


def get_crf_training_data(request):
    """
    This function is used obtain the training data given the entity_name.
     Args:
         request (HttpResponse): HTTP response from url

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
        datastore_obj = DataStore()
        result = datastore_obj.get_crf_data_for_entity_name(entity_name=entity_name)
        response['result'] = result
        response['success'] = True

    except (DataStoreSettingsImproperlyConfiguredException,
            EngineNotImplementedException,
            EngineConnectionException, FetchIndexForAliasException) as error_message:
        response['error'] = str(error_message)
        ner_logger.exception('Error: %s' % error_message)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    except BaseException as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    return HttpResponse(json.dumps(response), content_type='application/json', status=200)


@csrf_exempt
def update_crf_training_data(request):
    """
    This function is used to update the training data
     Args:
         request (HttpResponse): HTTP response from url
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
        entity_name = external_api_data.get(ENTITY_NAME)
        entity_list = external_api_data.get(ENTITY_LIST)
        sentence_list = external_api_data.get(SENTENCE_LIST)
        language_script = external_api_data.get(LANGUAGE_SCRIPT)
        datastore_obj = DataStore()
        datastore_obj.update_entity_crf_data(entity_name=entity_name,
                                             entity_list=entity_list,
                                             sentence_list=sentence_list,
                                             language_script=language_script)
        response['success'] = True

    except (DataStoreSettingsImproperlyConfiguredException,
            EngineNotImplementedException,
            EngineConnectionException, FetchIndexForAliasException) as error_message:
        response['error'] = str(error_message)
        ner_logger.exception('Error: %s' % error_message)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    except BaseException as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)
    return HttpResponse(json.dumps(response), content_type='application/json', status=200)


@csrf_exempt
def train_crf_model(request):
    """
    This method is used to train crf model.
    Args:
        request (HttpResponse): HTTP response from url
    Returns:
        HttpResponse : HttpResponse with appropriate status and error message.
    Post Request Body:
    key: "external_api_data"
    value: {
    "entity_name": "crf_test",
    "cloud_storage": true,
    "es_config": true,
    "cloud_embeddings": true
    }
    """
    response = {"success": False, "error": "", "result": {}}
    try:
        external_api_data = json.loads(request.POST.get(EXTERNAL_API_DATA))
        entity_name = external_api_data.get(ENTITY_NAME)
        cloud_storage = external_api_data.get(CLOUD_STORAGE)
        es_config = external_api_data.get(ES_CONFIG)
        cloud_embeddings = external_api_data.get(CLOUD_EMBEDDINGS)
        crf_model = CrfTrain(entity_name=entity_name,
                             cloud_storage=cloud_storage,
                             cloud_embeddings=cloud_embeddings)

        if es_config:
            model_path = crf_model.train_model_from_es_data()
        else:
            text_list = external_api_data.get(SENTENCE_LIST)
            entity_list = external_api_data.get(ENTITY_LIST)
            model_path = crf_model.train_model(text_list=text_list, entity_list=entity_list)

        response['result'] = {LIVE_CRF_MODEL_PATH: model_path}
        response['success'] = True

    except (IndexNotFoundException, InvalidESURLException,
            SourceDestinationSimilarException, InternalBackupException, AliasNotFoundException,
            PointIndexToAliasException, FetchIndexForAliasException, DeleteIndexFromAliasException,
            AliasForTransferException, IndexForTransferException, NonESEngineTransferException) as error_message:
        response['error'] = str(error_message)
        ner_logger.exception('Error: %s' % error_message)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    except BaseException as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    return HttpResponse(json.dumps(response), content_type='application/json', status=200)
