from __future__ import absolute_import
import json
import os
import glob
import itertools
from . import common


def check_if_data_valid(entities_data_path):
    # type: (str) ->  boolean
    """
    Doing basic sanity checking here.
    Check that every test case is valid json and has the keys: input and expected

    Args:
        entities_data_path (str): Path to the data/entities directory

    Returns:
        (boolean): Returns True if all files contain valid json.

    Raises:
        Exception if data is invalid
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
        raise e


def read_entities_data(entities_data_path):
    # type: (str) -> Dict
    """Read all the files in data/entities and generate a single dictionary containing
    data for every entity.

    Args:
        entities_data_path (string): Path to the data/entities directory.

    Returns:
        dictionary (dict): Dict containing data read from the data files for every entity.
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
                for key, _ in d['input'].items():
                    d1[entity + '_' + key] = d['input'][key]
                d1[entity + '_expected'] = d['expected']
                modified_data.append(d1)
            entities_data[entity] = modified_data
    return entities_data


def generate_newman_data(entities_data_path):
    # type: (str) -> List[Dict[str, any]]
    """Generate data in a format that can be passed to the command-line tool
    newman for runing the tests.

    Args:
        entities_data_path (string): Path to the data/entities directory.

    Returns:
        newman_data (list): List of dictionaries where each dictionary is data for a single test iteration.
    """
    data = []
    entities_data = read_entities_data(entities_data_path)
    data = list(entities_data.values())
    newman_data = []
    for iteration_data in itertools.zip_longest(*data, fillvalue={}):
        temp = {}
        for item in iteration_data:
            temp.update(item)
        newman_data.append(temp)
    return newman_data
