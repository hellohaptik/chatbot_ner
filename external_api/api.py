import json
from chatbot_ner.config import ner_logger
from django.http import HttpResponse
from datastore.datastore import DataStore
from external_api.external_api_utilities import structure_es_result, structure_external_api_json
from chatbot_ner.config import CHATBOT_NER_DATASTORE
from external_api.es_transfer import ESTransfer


def get_entity_word_variants(request):
    """
    This function is used obtain the entity dictionary given the dictionary name.
    Args:
        request (HttpResponse): HTTP response from url

    Returns:

    """
    dictionary_name = request.GET.get('dictionary_name')
    datastore_obj = DataStore()
    result = datastore_obj.get_entity_dictionary(entity_name=dictionary_name)
    result = structure_es_result(result)

    return HttpResponse(json.dumps({'result': result}), content_type='application/json')


def update_dictionary(request):
    """
    This function is used to update the dictionary entities.
    Args:
        request (HttpResponse): HTTP response from url

    Returns:

    """
    word_entity_info = json.loads(request.body)
    dictionary_name = word_entity_info.get('dictionary_name')
    dictionary_data = word_entity_info.get('dictionary_data')
    language_script = word_entity_info.get('language_script')
    datastore_obj = DataStore()
    status = datastore_obj.external_api_update_entity(dictionary_name=dictionary_name,
                                                      dictionary_data=dictionary_data,
                                                      language_script=language_script)

    return HttpResponse(json.dumps({'status': status}), content_type='application/json')


def transfer_entities(request):
    """
    This method is used to transfer entities from the source to destination.
    Args:
        request (HttpResponse): HTTP response from url

    Returns:

    """
    status = False
    source = CHATBOT_NER_DATASTORE.get('elasticsearch').get('source_url')
    destination = CHATBOT_NER_DATASTORE.get('elasticsearch').get('destination_url')
    es_object = ESTransfer(source=source, destination=destination)
    entity_list_dict = json.loads(request.body)
    entity_list = entity_list_dict.get('entity_list')
    es_object.transfer_specific_entities(list_of_entities=entity_list)
    return HttpResponse(json.dumps({'status': status}), content_type='application/json')
