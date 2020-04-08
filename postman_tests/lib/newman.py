from __future__ import absolute_import
import json
import os
import glob
from . import common


def check_if_data_valid(entities_data_path):
    """
    Doing basic sanity checking here.
    Check that every test case is valid json and has the keys: input and expected

    Parameters:
    entities_data_path (string): Path to the data/entities directory

    Returns:
    boolean: Returns True if all files contain valid json.
    """
    try:
        path = ''
        for file_path in glob.glob(os.path.join(entities_data_path, '*.json')):
            path = file_path
            with open(file_path, 'r') as file:
                data = json.load(file)
            for item in data:
                if not all(k in item for k in ('input', 'expected')):
                    print('Invalid json data in ' + file_path)
                    return False
        return True
    except Exception as e:
        print('Invalid json data in ' + path
              + '\n' + str(e))
        return False


def read_entities_data(entities_data_path):
    """
    Read all the files in data/entities and generate a single dictionary containing
    data for every entity.

    Parameters:
    entities_data_path (string): Path to the data/entities directory.

    Returns:
    dictionary: Dict containing data read from the data files for every entity.
    """
    entities_data = {}
    for file_path in glob.glob(os.path.join(entities_data_path, '*.json')):
        entity = common.get_entity_name(file_path)
        entities_data[entity] = []
        with open(file_path, 'r') as file:
            data = json.load(file)
            modified_data = []
            for d in data:
                d1 = {}
                for k, v in d['input'].items():
                    d1[entity + '_' + k] = d['input'][k]
                d1[entity + '_expected'] = d['expected']
                modified_data.append(d1)
            entities_data[entity] = modified_data
    return entities_data


def generate_newman_data(entities_data_path):
    """
    Generate data in a format that can be passed to the command-line tool
    newman for runing the tests.

    Parameters:
    entities_data_path (string): Path to the data/entities directory.

    Returns:
    list: List of dictionaries where each dictionary is data for a single test iteration.
    """
    data = []
    entities_data = read_entities_data(entities_data_path)
    data = list(entities_data.values())
    newman_data = []
    while True:
        found = False
        iteration_data = []
        for item in data:
            if item:
                iteration_data.append(item.pop(0))
                found = True
        if not found:
            break
        else:
            temp = {}
            for item in iteration_data:
                temp.update(item)
            newman_data.append(temp)
    return newman_data
