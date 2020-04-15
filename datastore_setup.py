import os

from chatbot_ner.config import ES_INDEX_NAME, ES_ALIAS
from datastore import DataStore
from datastore.constants import DEFAULT_ENTITY_DATA_DIRECTORY
from datastore.elastic_search.connect import get_es_url
from datastore.elastic_search.transfer import ESTransfer

BASE_DIR = os.path.dirname(__file__)


# Below needs to be committed if you want to use existing data in the Elasticsearch Setup
# TODO move this part to a different script and run on-demand
# POPULATING DATASTORE
# Comment out entire section if you want to reuse existing data

def setup_datastore():
    db = DataStore()
    print("Setting up DataStore for Chatbot NER")
    print("Deleting any stale data ...")
    db.delete()
    print("Creating the structure ...")
    db.create()
    es_url = get_es_url()
    es_object = ESTransfer(source=es_url, destination=None)
    es_object.point_an_alias_to_index(es_url=es_url, alias_name=ES_ALIAS, index_name=ES_INDEX_NAME)
    print("Populating data from " + os.path.join(BASE_DIR, 'data', 'entity_data') + " ...")
    db.populate(entity_data_directory_path=DEFAULT_ENTITY_DATA_DIRECTORY)
    print("Done!")


if __name__ == '__main__':
    setup_datastore()
