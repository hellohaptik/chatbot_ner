import os

from datastore import DataStore
from datastore.constants import DEFAULT_ENTITY_DATA_DIRECTORY

BASE_DIR = os.path.dirname(__file__)


# Below needs to be committed if you want to use existing data in the Elasticsearch Setup
# TODO move this part to a different script and run on-demand
# Comment out entire section if you want to reuse existing data

def setup_datastore():
    db = DataStore()
    print("Setting up DataStore for Chatbot NER")
    print("Deleting any stale data ...")
    db.delete(err_if_does_not_exist=False)
    print("Creating the structure ...")
    db.create(err_if_exists=True)
    print("Populating data from " + os.path.join(BASE_DIR, 'data', 'entity_data') + " ...")
    db.populate(entity_data_directory_path=DEFAULT_ENTITY_DATA_DIRECTORY)
    print("Done!")


if __name__ == '__main__':
    setup_datastore()
