from __future__ import absolute_import
import os
import glob
from . import common
import requests
import json
import csv

es_api_url = "http://localhost:8081/entities/data/v1"


# Generate the data object
def get_variants(str):
    str = str.replace(' ','')
    arr = str.split('|')
    return [item for item in arr if item]


def convert_csv_to_json(file_path):
    data = {'replace': True, 'edited': []}
    with open(file_path, 'r') as file:
        csv_data = csv.reader(file)
        next(file) # Omit header row
        for row in csv_data:
            record = {'word': row[0]}
            record['variants'] = {
                'en': {
                    '_id': None,
                    'value': get_variants(row[1])
                }
            }
            data['edited'].append(record)
    return json.dumps(data)


def index_data(es_data_path):
    for file_path in glob.glob(os.path.join(es_data_path, '*.csv')):
        entity_name = common.get_entity_name(file_path)
        print(f"Indexing {entity_name}")
        contents = convert_csv_to_json(file_path)
        req = requests.post(f"{es_api_url}/{entity_name}", data=contents)
        print(req.text)


def clear_data(es_data_path):
    for file_path in glob.glob(os.path.join(es_data_path, '*.csv')):
        entity_name = common.get_entity_name(file_path)
        print(f"Clearing ES data for {entity_name}")
        contents = convert_csv_to_json(file_path)
        contents = contents.replace("\"edited\":", "\"deleted\":")
        req = requests.post(f"{es_api_url}/{entity_name}", data=contents)
        print(req.text)
