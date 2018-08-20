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
    engine = CHATBOT_NER_DATASTORE.get('engine')
    source = CHATBOT_NER_DATASTORE.get(engine).get('es_scheme') + \
        CHATBOT_NER_DATASTORE.get(engine).get('host') + ':' + \
        CHATBOT_NER_DATASTORE.get(engine).get('port')
    destination = CHATBOT_NER_DATASTORE.get(engine).get('destination_url')
    es_object = ESTransfer(source=source, destination=destination)
    entity_list_dict = json.loads(request.GET.get('word_info'))
    entity_list = entity_list_dict.get('entity_list')
    status, error = es_object.transfer_specific_entities(list_of_entities=entity_list)
    result = {"status": status, "error": error}
    if not status:
        HttpResponse(json.dumps({"data": result}), content_type='application/json', status=500)
    return HttpResponse(json.dumps({"data": result}), content_type='application/json', status=200)


def update_training_data(request):
    """
    This method is used to update the training text and entity list for the given entity.
    Args:
        request (HttpResponse): HTTP response from url

    Returns:
        HttpResponse: HttpResponse with appropriate status
    """
    try:
        training_data = json.loads(request.GET.get('word_info'))
        text_list = training_data.get('text_list')
        entity_list = training_data.get('entity_list')
        entity_name = training_data.get('entity_name')
        language_script = training_data.get('language_script')
        datastore_obj = DataStore()
        datastore_obj.external_api_update_training_data(entity_name=entity_name, entity_list=entity_list,
                                                        text_list=text_list, language_script=language_script)
    except ValueError:
        HttpResponse(status=500)
    return HttpResponse(status=200)


def get_training_data(request):
    """
    This function is used obtain the training text list and entities given the dictionary name.
    Args:
        request (HttpResponse): HTTP response from url

    Returns:
        HttpResponse: HttpResponse with appropriate status and data
    """
    try:
        dictionary_name = request.GET.get('dictionary_name')
        datastore_obj = DataStore()
        result = datastore_obj.get_entity_dictionary(training_config=True, entity_name=dictionary_name)
    except ValueError:
        return HttpResponse(status=500)
    return HttpResponse(json.dumps({'data': result}), content_type='application/json')
