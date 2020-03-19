from __future__ import absolute_import
import json
import traceback
import os


def get_number_of_records_per_entity():
    with open('data/number_range.json', 'r') as file:
        data = json.load(file)
    return len(data)


def check_if_data_valid(entities):
    # Doing basic sanity checking here.
    # Check if all data files are valid json and there are same number of records in all of them
    # Also check that every test case has the keys: input and expected
    try:
       number_of_records = get_number_of_records_per_entity()
       for entity in entities:
           file_name = 'data/' + entity + '.json'
           with open(file_name, 'r') as file:
               data = json.load(file)
           if (len(data) != number_of_records):
               print('Incorrect number of records in ' + file_name)
               return False
           for item in data:
               if not all (k in item for k in ('input', 'expected')):
                   print('Invalid json data in ' + file_name)
                   return False
       return True
    except Exception as e:
        print('Invalid json data in ' + file_name + '\n' + traceback.format_exc())
        return False


def read_entities_data(entities):
    entities_data = {}
    for entity in entities:
        file_name = 'data/' + entity + '.json'
        entities_data[entity] = []
        with open(file_name, 'r') as file:
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
    number_of_records = get_number_of_records_per_entity()
    result = []
    for i in range(number_of_records):
        l = []
        d = {}
        for k in entities_data:
            l.append(entities_data[k][i])
        for item in l:
            d.update(item)
        result.append(d)
    return result
    

entities = ['number_range', 'phoneV2']

if (check_if_data_valid(entities)):
    try:
        entities_data = read_entities_data(entities)
        newman_data = generate_newman_data(entities_data)
        with open('newman_v2_data.json', 'w') as fp:
            json.dump(newman_data, fp,  indent=4)
        os.system('newman run ner_v2_collection.json -d newman_v2_data.json -e dev.json')
    except Exception as e:
        print(traceback.format_exc())







    
