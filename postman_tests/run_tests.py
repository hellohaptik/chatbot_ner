from __future__ import absolute_import
from lib import newman
import subprocess
import os
import json
from lib import es


postman_data_directory = 'postman_tests/'
entities_data_path = 'data/entities/'
newman_data_path = 'data/newman_data.json'
collection_data_path = 'data/ner_collection.json'
environment_file_path = 'data/environment.json'
es_data_path = 'data/elastic_search/'


#Switch to postman_tests if not already in that directory
if(os.path.basename(os.getcwd()) != postman_data_directory):
    os.chdir(postman_data_directory)


if newman.check_if_data_valid(entities_data_path):
    try:
        es.index_data(es_data_path)
        entities_data = newman.read_entities_data(entities_data_path)
        newman_data = newman.generate_newman_data(entities_data)
        with open(newman_data_path, 'w') as fp:
            json.dump(newman_data, fp, indent=4)
        subprocess.Popen(f"newman run {collection_data_path} -d {newman_data_path} -e {environment_file_path}", shell=True).wait()
        es.clear_data(es_data_path)
    except Exception as e:
        print(str(e))
