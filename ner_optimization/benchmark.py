import csv
import os
import json
import glob

# Returns the list of all entity names from every input file
def get_entity_names():
    entity_names = ['cb_ner_op_locality', 'cb_ner_op_movie', 'cb_ner_op_restaurant', 'cb_ner_op_brand', 'cb_ner_op_clothes', 'cb_ner_op_cuisine', 'cb_ner_op_dish']
    for i in range(1, 101):
        entity_names.append(f'cb_ner_op_entity_{i}')
    return entity_names


# Returns the list of all variant names for a given file
def variant_names_from_file(file_path):
    result = []
    with open(file_path, 'r') as file:
        csv_data = csv.DictReader(file)
        for row in csv_data:
            line = row['variants'].split('|')
            result += [item.strip() for item in line if item.strip()]
    return result

# Returns the list of all variant names from every input file
def get_variant_names():
    variant_names = []
    for file_path in glob.glob(os.path.join('input_data', '*.csv')):
        variant_names += variant_names_from_file(file_path)
    variant_names = list(dict.fromkeys(variant_names)) # Remove duplicates
    return variant_names

def detect_entities(number_of_entities, number_of_variants):
    pass


entity_names = get_entity_names()
variant_names = get_variant_names()
print(variant_names)
print(len(variant_names))
