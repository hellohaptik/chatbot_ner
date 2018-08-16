import json
from chatbot_ner.config import ner_logger
from django.http import HttpResponse
from datastore.datastore import DataStore
from external_api.external_api_utilities import structure_es_result, structure_external_api_json
from chatbot_ner.config import CHATBOT_NER_DATASTORE
from external_api.es_transfer import ESTransfer


def get_entity_word_variants(request):
    """This functionality initializes text detection functionality to detect textual entities.

    Attributes:
        request: url parameters

    """
    status = False
    result = []
    try:
        dictionary_name = request.GET.get('dictionary_name')
        datastore_obj = DataStore()
        result = datastore_obj.get_entity_dictionary(entity_name=dictionary_name)
        result = structure_es_result(result)
        status = True

    except TypeError:
        ner_logger.debug('Error %s' % str(TypeError))
    return HttpResponse(json.dumps({'status': status, 'result': result}), content_type='application/json')


def update_dictionary(request):
    """This functionality initializes text detection functionality to detect textual entities.

    Attributes:
        request: url parameters

    """

    word_entity_info = json.loads(request.body)
    dictionary_name = word_entity_info.get('dictionary_name')
    dictionary_data = word_entity_info.get('dictionary_data')
    datastore_obj = DataStore()
    status = datastore_obj.external_api_update_entity(dictionary_name=dictionary_name,
                                                      dictionary_data=dictionary_data)

    return HttpResponse(json.dumps({'status': status}), content_type='application/json')


def transfer_entities(request):
    """This functionality initializes text detection functionality to detect textual entities.

    Attributes:
        request: url parameters

    """
    status = False
    source = CHATBOT_NER_DATASTORE.get('elasticsearch').get('source_url')
    destination = CHATBOT_NER_DATASTORE.get('elasticsearch').get('destination_url')
    es_object = ESTransfer(source=source, destination=destination)
    entity_list_dict = json.loads(request.body)
    entity_list = entity_list_dict.get('entity_list')
    es_object.transfer_specific_entities(list_of_entities=entity_list)
    return HttpResponse(json.dumps({'status': status}), content_type='application/json')
