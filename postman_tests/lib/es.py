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


def index_data(es_data_path, config_path):
    """
    Index data for every entity being tested into ElasticSearch

    Parameters:
    es_data_path (string): Path to the data/elastic_search directory

    Returns:
    None
    """
    for file_path in glob.glob(os.path.join(es_data_path, '*.csv')):
        entity_name = common.get_entity_name(file_path)
        print(f"Indexing {entity_name}")
        contents = convert_csv_to_json(file_path)
        url = get_es_api_url(config_path)
        req = requests.post(f"{url}/{entity_name}", data=contents)
        print(req.text)


def clear_data(es_data_path, config_path):
    """
    Clear the data for every entity that was indexed for testing from ElasticSearch

    Parameters:
    es_data_path (string): Path to the data/elastic_search directory.

    Returns:
    None
    """
    for file_path in glob.glob(os.path.join(es_data_path, '*.csv')):
        entity_name = common.get_entity_name(file_path)
        print(f"Clearing ES data for {entity_name}")
        contents = convert_csv_to_json(file_path)
        contents = contents.replace("\"edited\":", "\"deleted\":")
        url = get_es_api_url(config_path)
        req = requests.post(f"{url}/{entity_name}", data=contents)
        print(req.text)


def convert_csv_to_json(file_path):
    """
    Read the csv file at file_path and convert its data to json

    Parameters:
    file_path (string): Path of a file in the data/elastic_search directory

    Returns:
    string: The JSON representation of the csv data in the file
    """
    data = {'replace': True, 'edited': []}
    with open(file_path, 'r') as file:
        csv_data = csv.reader(file)
        next(file)  # Omit header row
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


def get_variants(str):
    """
    Convert the string containing all the variants into a list

    Parameters:
    str (string): String containing all the variant names.

    Returns:
    list: List of strings where each string is a variant name.
    """
    arr = str.split('|')
    return [item.strip() for item in arr if item]
