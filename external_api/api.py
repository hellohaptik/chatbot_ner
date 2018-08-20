import json
from django.http import HttpResponse
from datastore.datastore import DataStore
from external_api.external_api_utilities import structure_es_result
from chatbot_ner.config import CHATBOT_NER_DATASTORE
from external_api.es_transfer import ESTransfer


def get_entity_word_variants(request):
    """
    This function is used obtain the entity dictionary given the dictionary name.
    Args:
        request (HttpResponse): HTTP response from url

    Returns:
        HttpResponse : With data consisting of a list of value variants.
    """
    try:
        dictionary_name = request.GET.get('dictionary_name')
        datastore_obj = DataStore()
        result = datastore_obj.get_entity_dictionary(entity_name=dictionary_name)
        result = structure_es_result(result)
    except ValueError:
        return HttpResponse(status=500)
    return HttpResponse(json.dumps({'data': result}), content_type='application/json', status=200)


def update_dictionary(request):
    """
    This function is used to update the dictionary entities.
    Args:
        request (HttpResponse): HTTP response from url

    Returns:
        HttpResponse : HttpResponse with appropriate status.
    """
    try:
        word_info = json.loads(request.GET.get('word_info'))
        dictionary_name = word_info.get('dictionary_name')
        dictionary_data = word_info.get('dictionary_data')
        language_script = word_info.get('language_script')
        datastore_obj = DataStore()
        datastore_obj.external_api_update_entity(dictionary_name=dictionary_name,
                                                 dictionary_data=dictionary_data,
                                                 language_script=language_script)
    except ValueError:
        return HttpResponse(status=500)
    return HttpResponse(status=200)


def transfer_entities(request):
    """
    This method is used to transfer entities from the source to destination.
    Args:
        request (HttpResponse): HTTP response from url
    Returns:
        HttpResponse : HttpResponse with appropriate status.
    """

    entity_list_dict = json.loads(request.GET.get('word_info'))
    entity_list = entity_list_dict.get('entity_list')
    datastore_object = DataStore()
    status, error = datastore_object.transfer_entities(entity_list=entity_list)
    result = {"status": status, "error": error}
    if not status:
        HttpResponse(json.dumps({"data": result}), content_type='application/json', status=500)
    return HttpResponse(json.dumps({"data": result}), content_type='application/json', status=200)
