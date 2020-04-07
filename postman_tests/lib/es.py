from __future__ import absolute_import
import os
import glob
import json
import csv
import requests
from . import common


def get_es_api_url(config_path):
    if os.path.exists(f"{config_path}/dev.json"):
        config_file_path = f"{config_path}/dev.json"
    else:
        config_file_path = f"{config_path}/prod.json"
    with open(config_file_path, 'r') as f:
        data = json.load(f)
    base_url = data["es_host"]
    return f"http://{base_url}/entities/data/v1"


def sync(es_data_path, config_path, mode):
    """
    Index data for every entity being tested into ElasticSearch

    Parameters:
    es_data_path (string): Path to the data/elastic_search directory

    Returns:
    None
    """
    for file_path in glob.glob(os.path.join(es_data_path, '*.csv')):
        entity_name = common.get_entity_name(file_path)
        print(f"Syncing {entity_name}, mode: {mode}")
        contents = convert_csv_to_dict(file_path, mode)
        url = get_es_api_url(config_path)
        req = requests.post(f"{url}/{entity_name}", data=json.dumps(contents))
        print(req.text)


def convert_csv_to_dict(file_path, mode):
    """
    Read the csv file at file_path and convert its data to json

    Parameters:
    file_path (string): Path of a file in the data/elastic_search directory

    Returns:
    string: The JSON representation of the csv data in the file
    """
    if mode == 'create':
        data = {'replace': True, 'edited': []}
        key = 'edited'
    elif mode == 'delete':
        data = {'replace': True, 'deleted': []}
        key = 'deleted'

    with open(file_path, 'r') as file:
        csv_data = csv.DictReader(file)
        for row in csv_data:
            record = {'word': row['value']}
            record['variants'] = {
                'en': {
                    '_id': None,
                    'value': get_variants(row['variants'])
                }
            }
            data[key].append(record)
    return data


def get_variants(str):
    """
    Convert the string containing all the variants into a list

    Parameters:
    str (string): String containing all the variant names.

    Returns:
    list: List of strings where each string is a variant name.
    """
    arr = str.split('|')
    return [item.strip() for item in arr if item.strip()]
