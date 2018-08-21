import json
from django.http import HttpResponse
from datastore.datastore import DataStore
from external_api.external_api_utilities import structure_es_result
from datastore.exceptions import (DataStoreSettingsImproperlyConfiguredException, EngineNotImplementedException,
                                  EngineConnectionException, IndexForTransferException,
                                  AliasForTransferException)
from external_api.es_transfer import IndexNotFoundException, InvalidESURLException, \
    SourceDestinationSimilarException, \
    InternalBackupException, AliasNotFoundException, PointIndexToAliasException, \
    FetchIndexForAliasException, DeleteIndexFromAliasException
from chatbot_ner.config import ner_logger


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
        dictionary_name = request.GET.get('dictionary_name')
        datastore_obj = DataStore()
        result = datastore_obj.get_entity_dictionary(entity_name=dictionary_name)
        result = structure_es_result(result)
        response['result'] = result
        response['success'] = True

    except ValueError as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    except AttributeError as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

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


def update_dictionary(request):
    """
    This function is used to update the dictionary entities.
    Args:
        request (HttpResponse): HTTP response from url

    Returns:
        HttpResponse : HttpResponse with appropriate status.
    """
    response = {"success": False, "error": ""}
    try:
        word_info = json.loads(request.GET.get('word_info'))
        dictionary_name = word_info.get('dictionary_name')
        dictionary_data = word_info.get('dictionary_data')
        language_script = word_info.get('language_script')
        datastore_obj = DataStore()
        datastore_obj.external_api_update_entity(dictionary_name=dictionary_name,
                                                 dictionary_data=dictionary_data,
                                                 language_script=language_script)
        response['success'] = True
    except ValueError as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    except AttributeError as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

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


def transfer_entities(request):
    """
    This method is used to transfer entities from the source to destination.
    Args:
        request (HttpResponse): HTTP response from url
    Returns:
        HttpResponse : HttpResponse with appropriate status.
    """
    response = {"success": False, "error": ""}
    try:
        entity_list_dict = json.loads(request.GET.get('word_info'))
        entity_list = entity_list_dict.get('entity_list')

        datastore_object = DataStore()
        datastore_object.transfer_entities(entity_list=entity_list)
        response['success'] = True

    except ValueError as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    except AttributeError as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    except (IndexNotFoundException, InvalidESURLException,
            SourceDestinationSimilarException, InternalBackupException, AliasNotFoundException,
            PointIndexToAliasException, FetchIndexForAliasException, DeleteIndexFromAliasException,
            AliasForTransferException, IndexForTransferException) as error_message:
        response['error'] = str(error_message)
        ner_logger.exception('Error: %s' % error_message)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    except BaseException as e:
        response['error'] = str(e)
        ner_logger.exception('Error: %s' % e)
        return HttpResponse(json.dumps(response), content_type='application/json', status=500)

    return HttpResponse(json.dumps(response), content_type='application/json', status=200)
