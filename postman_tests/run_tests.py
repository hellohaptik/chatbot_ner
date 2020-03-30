from __future__ import absolute_import
import json
import os
import subprocess
import glob


postman_data_directory = 'postman_tests/'
entities_data_path = 'data/entities/'
newman_data_path = 'data/newman_data.json'
collection_data_path = 'data/ner_collection.json'
environment_file_path = 'data/environment.json'


def check_if_data_valid():
    # Doing basic sanity checking here.
    # Check that every test case is valid json and has the keys: input and expected
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


def get_entity_name(file_path):
    base=os.path.basename(file_path)
    return os.path.splitext(base)[0]


def read_entities_data():
    entities_data = {}
    for file_path in glob.glob(os.path.join(entities_data_path, '*.json')):
        entity = get_entity_name(file_path)
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


def generate_newman_data(entities_data):
    data = []
    for k in entities_data:
        data.append(entities_data[k])
    newman_data = []
    while True:
        found = False
        iteration_data = []
        for list in data:
            if list:
                iteration_data.append(list.pop(0))
                found = True
        if found == False:
            break
        else:
            temp = {}
            for item in iteration_data:
                temp.update(item)
            newman_data.append(temp)
    return newman_data


#Switch to postman_tests if not already in that directory
if(os.path.basename(os.getcwd()) != postman_data_directory):
    os.chdir(postman_data_directory)


if check_if_data_valid():
    try:
        entities_data = read_entities_data()
        newman_data = generate_newman_data(entities_data)
        with open(newman_data_path, 'w') as fp:
            json.dump(newman_data, fp, indent=4)
        subprocess.Popen(f"newman run {collection_data_path} -d {newman_data_path} -e {environment_file_path}", shell=True).wait()
    except Exception as e:
        print(str(e))
