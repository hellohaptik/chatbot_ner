import os
import time

import nltk

BASE_DIR = os.path.dirname(__file__)

print "Downloading nltk corpus: punkt ..."
status = nltk.download('punkt')
if not status:
    print "punkt Download was unsucessful"

print "Downloading nltk corpus: wordnet ..."
status = nltk.download('wordnet')
if not status:
    print "wordnet Download was unsucessful"

print "Downloading nltk corpus: MaxEnt POS ..."
status = nltk.download('maxent_treebank_pos_tagger')
if not status:
    print "MaxEnt POS Download was unsucessful"

print "Downloading nltk corpus: AP POS Tagger..."
status = nltk.download('averaged_perceptron_tagger')
if not status:
    print "AP POS Tagger Download was unsucessful"

# Below needs to be committed if you want to use existing data in the Elasticsearch Setup

time.sleep(20)
# waiting for Elasticsearch to come up properly, if you have a self hosted ES and not using via docker-compose
# You can remove this sleep
# TODO move this part to a different script and run on-demand
# POPULATING DATASTORE
# Comment out entire section if you want to reuse existing data
from datastore import DataStore

db = DataStore()
print "Setting up DataStore for Chatbot NER"
print "Deleting any stale data ..."
db.delete()
print "Creating the structure ..."
db.create()
print "Populating data from " + os.path.join(BASE_DIR, 'data', 'entity_data') + " ..."
db.populate()
print "Done!"
