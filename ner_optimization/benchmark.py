import django

django.setup()

import csv
import os
import glob
import random
from ares.models import *  #For GlobalEntityModel
from ares.lib.entity_detection.entity_detection import EntityDetector

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

def detect_entities(number_of_entities):
    entity_names_indices = random.sample(range(0, len(entity_names)), number_of_entities)
    entities = []
    variant_names_indices = random.sample(range(0, len(variant_names)), 50)
    variants = []
    # Get list of number_of_entities random entities
    for index in entity_names_indices:
        entity = GlobalEntityModel.objects.get(name=entity_names[index])
        entities.append(entity)
    # Generate text of length 50 from randomly selected variant names
    for index in variant_names_indices:
        variants.append(variant_names[index])
    text = " ".join(variants)
    ed = EntityDetector(entities, text)
    return ed.start_detection()
    


entity_names = get_entity_names()
variant_names = get_variant_names()
print(detect_entities(2))
