import os

from datastore import DataStore

BASE_DIR = os.path.dirname(__file__)

print "initial setup es started"
db = DataStore()
print "Setting up DataStore for Chatbot NER"
print "Deleting any stale data ..."
db.delete()
print "Creating the structure ..."
db.create()
print "Populating data from " + os.path.join(BASE_DIR, 'data', 'entity_data') + " ..."
db.populate()
print "Done!"
