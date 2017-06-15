import os

import nltk

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

print "Downloading nltk corpus: punkt ..."
status = nltk.download('punkt')
if not status:
    print "punkt Download was unsucessful"

print "Downloading nltk corpus: wordnet ..."
status = nltk.download('wordnet')
if not status:
    print "wordnet Download was unsucessful"

print "Downloading nltk corpus: POS ..."
status = nltk.download('maxent_treebank_pos_tagger')
if not status:
    print "POS Download was unsucessful"

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
