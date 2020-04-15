from __future__ import absolute_import
import os
import time
import nltk

from datastore.elastic_search.connect import get_es_url
from datastore.elastic_search.transfer import ESTransfer

BASE_DIR = os.path.dirname(__file__)

print("Downloading nltk corpus: punkt ...")
status = nltk.download('punkt')
if not status:
    print("punkt Download was unsuccessful")

print("Downloading nltk corpus: wordnet ...")
status = nltk.download('wordnet')
if not status:
    print("wordnet Download was unsuccessful")

print("Downloading nltk corpus: MaxEnt POS ...")
status = nltk.download('maxent_treebank_pos_tagger')
if not status:
    print("MaxEnt POS Download was unsuccessful")

print("Downloading nltk corpus: AP POS Tagger...")
status = nltk.download('averaged_perceptron_tagger')
if not status:
    print("AP POS Tagger Download was unsuccessful")

# Below needs to be committed if you want to use existing data in the Elasticsearch Setup

time.sleep(20)
# waiting for Elasticsearch to come up properly, if you have a self hosted ES and not using via docker-compose
# You can remove this sleep
# TODO move this part to a different script and run on-demand
# POPULATING DATASTORE
# Comment out entire section if you want to reuse existing data
from datastore import DataStore
from datastore.constants import DEFAULT_ENTITY_DATA_DIRECTORY
from chatbot_ner.config import ES_INDEX_NAME, ES_ALIAS

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
