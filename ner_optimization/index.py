import random
import string
import csv
import os
import glob
import requests
import json

def generate_random_word(word_length=0):
    if word_length < 2:
        word_length = random.randint(5, 10)
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(word_length))


def generate_file(num):
    file_name = f"entity_{num}.csv"
    print(f"Generating {file_name}")
    with open(f"input_data/{file_name}", mode='w') as csv_file:
        field_names = ['value', 'variants']
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        for i in range(1, 1001):
            writer.writerow({ 'value': generate_random_word(), 'variants': generate_random_word() })


def get_variants(variants_line):
    arr = variants_line.split('|')
    return [item.strip() for item in arr if item.strip()]


def convert_csv_to_dict(file_path, mode):
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


def get_entity_name(file_path):
    base = os.path.basename(file_path)
    return os.path.splitext(base)[0]
            

def index(mode='create'):
    for file_path in glob.glob(os.path.join('input_data', '*.csv')):
        entity_name = get_entity_name(file_path)
        print(f"Syncing {entity_name}, mode: {mode}")
        contents = convert_csv_to_dict(file_path, mode)
        url = 'http://localhost:8081/entities/data/v1'
        try:
            req = requests.post(f"{url}/cb_ner_op_{entity_name}", data=json.dumps(contents))
            req.raise_for_status()
            print(f"Done {entity_name}")
        except requests.exceptions.HTTPError as e:
            print(req.text)


def generate_input_files(number_of_files):
    for i in range(1, number_of_files+1):
        generate_file(i)


if __name__ == "__main__":
    NUMBER_OF_FILES = 1 # Change this number to the number of files you want to generate
    generate_input_files(NUMBER_OF_FILES)
    index()
    print('All Done!')
