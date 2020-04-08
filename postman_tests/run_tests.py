from __future__ import absolute_import
import subprocess
import os
import json
from lib import newman
from lib import es
import sys
import traceback


postman_tests_directory = os.path.dirname(os.path.abspath(__file__))
entities_data_path = os.path.join(postman_tests_directory, 'data', 'entities')
newman_data_path = os.path.join(postman_tests_directory, 'data', 'newman_data.json')
collection_data_path = os.path.join(postman_tests_directory, 'data', 'ner_collection.json')
es_data_path = os.path.join(postman_tests_directory, 'data', 'elastic_search')
config_path = os.path.join(postman_tests_directory, 'config')


def get_newman_command():
    if os.path.exists(f"{config_path}/dev.json"):
        environment_file_path = f'{config_path}/dev.json'
        return (
            f'newman run {collection_data_path} -d {newman_data_path}'
            f' -e {environment_file_path} -r cli,htmlextra --reporter-htmlextra-logs'
        )
    else:
        environment_file_path = f'{config_path}/prod.json'
        return (
            f'newman run {collection_data_path} -d {newman_data_path}'
            f' -e {environment_file_path}'
        )


if newman.check_if_data_valid(entities_data_path):
    try:
        es.sync(es_data_path, config_path, 'create')
        newman_data = newman.generate_newman_data(entities_data_path)
        with open(newman_data_path, 'w') as fp:
            json.dump(newman_data, fp)
        newman_command = get_newman_command()
        subprocess.Popen(newman_command, shell=True).wait()
        es.sync(es_data_path, config_path, 'delete')
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        print(str(e))
