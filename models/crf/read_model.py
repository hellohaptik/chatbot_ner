# -*- coding: utf-8 -*-
import csv
import json
import os, os.path
import nltk
from lib.nlp.const import tokenizer
from models.constants import city_model_path, io_model_directory, CITY_ENTITY_TYPE
from models.utils import get_current_timestamp, create_directory


class GenerateCRFTrain(object):

    def __init__(self):
        self._test_input_file = None
        self._test_output_file = None
        self._model_path = None

    def initialize_files(self, entity_type):
        file_name = get_current_timestamp()
        create_directory(io_model_directory)
        self._test_input_file = os.path.join(io_model_directory, file_name + '.inp')
        self._test_output_file = os.path.join(io_model_directory, file_name + '.out')

        if entity_type == CITY_ENTITY_TYPE:
            self._model_path = city_model_path

    def generate_crf_data(self, bot_message, user_message):
        tokens_bot_message = tokenizer.tokenize(bot_message)
        tokens_user_message = tokenizer.tokenize(user_message)

        pos_bot_message = nltk.pos_tag(tokens_bot_message)
        pos_user_message = nltk.pos_tag(tokens_user_message)
        crf_data = ''
        for token in pos_bot_message:
            crf_data += token[0]+' '+token[1]+' '+'o'+'\n'

        for token in pos_user_message:
            crf_data += token[0]+' '+token[1]+' '+'i'+'\n'
        return crf_data

    def run_crf(self, file_path):

        os.system('../crf/crf_test -m data/model/city/model '+file_name+ ' > output/'+filename+'.txt')


    def get_crf_output(self, bot_message, user_message):
        current_time = self._get_current_timestamp()

        self.make_crf_file(bot_message=bot_message, user_message=user_message, filename=str(current_time))

        self.call_crf(str(current_time))

        return self.get_arrival_departure(str(current_time))

    def write_to_file(self, file_to_open, mode_to_write, string_to_write):
        with open(file_to_open, mode_to_write)as f:
            f.write(string_to_write)


    def removeDir(self, file_to_remove):
        if os.path.exists(file_to_remove):
            os.remove(file_to_remove)


    def read_model(self, bot_message, user_message):

        timestamp = self._get_current_timestamp()

        crf_data = self.generate_crf_data(bot_message=bot_message, user_message=user_message)
        self.write_crf(filename=timestamp, crf_data=crf_data)
        self.call_crf(filename=timestamp)






    def generate_city_output(self, filename):
        file_name = 'output/'+filename+'.txt'
        departure_city = ''
        arrival_city = ''
        via_city = ''
        list_json = []
        with open (file_name, 'r')as f:
            reader = csv.reader(f, delimiter='\t')
            reader = list(reader)
            i = 0
            
            while i<len(reader):
                if len(reader[i]) is 0:
                    pass
                elif reader[i][3]=='from-B':
                    departure_city = departure_city+' '+reader[i][0]
                elif reader[i][3]=='from-I':
                    departure_city = departure_city+reader[i][0]

                elif reader[i][3]=='to-B':
                    arrival_city = arrival_city+' '+reader[i][0]

                elif reader[i][3]=='to-I':
                    arrival_city = arrival_city+reader[i][0]

                elif reader[i][3]== "via-B":
                    via_city = via_city+' '+reader[i][0]

                elif reader[i][3]=='via-I':
                    via_city = via_city+reader[i][0]
                else:
                    pass
                i += 1

        pythonDict = {'city': departure_city, 'to': 0, 'from': 1, 'via': 0}
        list_json.append(pythonDict)
        
        pythonDict = {'city': arrival_city, 'to': 1, 'from': 0, 'via': 0}
        jsonData = json.dumps(pythonDict)
        list_json.append(jsonData)

        pythonDict = {'city': via_city, 'to': 0, 'from': 0, 'via': 1}
        jsonData = json.dumps(pythonDict)
        list_json.append(jsonData)

        self.removeDir(file_name)
        return list_json
