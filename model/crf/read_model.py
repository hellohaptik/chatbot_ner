# -*- coding: utf-8 -*-
import subprocess
import csv
import json
import numpy as np
import os, os.path
import time
import datetime
from nltk import word_tokenize, pos_tag

class GenerateCRFTrain(object):

    def __init__(self):

        
    def write_to_file(self, file_to_open, mode_to_write, string_to_write):
        with open(file_to_open, mode_to_write)as f:
            f.write(string_to_write)

    def makeDir(self, s):
        if not os.path.exists(s):
            os.makedirs(s)

    def remove_noise(self, input_text):
        words = input_text.split() 
        noise_free_words = [word for word in words if word not in NOISE_LIST] 
        noise_free_text = " ".join(noise_free_words) 
        return noise_free_text

    def write_to_file(self, file_to_open, mode_to_write, string_to_write):
        with open(file_to_open, mode_to_write)as f:
            f.write(string_to_write)

    def removeDir(self, file_to_remove):
        if os.path.exists(file_to_remove):
            os.remove(file_to_remove)

    def get_crf_output(self, bot_message, user_message):
        current_time = self.get_current_timestamp()

        self.make_crf_file(bot_message, user_message, str(current_time))

        self.call_crf(str(current_time))

        return self.get_arrival_departure(str(current_time))

    def get_current_timestamp(self):
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        return st.replace(" ","")

    def call_crf(self, filename):
        file_name = 'output/'+filename+'.data'
        os.system('../crf/crf_test -m data/model/city/model '+file_name+ ' > output/'+filename+'.txt')
        self.removeDir(file_name)

    def make_crf_file(self, bot_message, user_message, filename):

        file_name = 'output/'+filename+'.data'
        self.makeDir('output')

        tokens_bot_message = word_tokenize(bot_message)
        tokens_user_message = word_tokenize(user_message)

        pos_bot_message = pos_tag(tokens_bot_message)
        pos_user_message = pos_tag(tokens_user_message)

        for token in pos_bot_message:
            self.write_to_file(file_name,'a',token[0]+' '+token[1]+' '+'o'+'\n')

        for token in pos_user_message:
            self.write_to_file(file_name, 'a', token[0]+' '+token[1]+' '+'i'+'\n')

    def get_arrival_departure(self, filename):
        file_name = 'output/'+filename+'.txt'
        departure_city = ''
        arrival_city = ''
        via_city = ''
        list_json = []
        with open (file_name, 'r')as f:
            reader = csv.reader(f, delimiter='\t')
            reader = list(reader)
            i = 0
            
            while(i<len(reader)):
                if (len(reader[i]) is 0):
                    pass
                elif (reader[i][3]=='from-B'):
                    departure_city = departure_city+' '+reader[i][0]

                elif(reader[i][3]=='from-I'):
                    departure_city = departure_city+reader[i][0]

                elif (reader[i][3]=='to-B'):
                    arrival_city = arrival_city+' '+reader[i][0]

                elif (reader[i][3]=='to-I'):
                    arrival_city = arrival_city+reader[i][0]

                elif (reader[i][3]=='via-B'):
                    via_city = via_city+' '+reader[i][0]

                elif(reader[i][3]=='via-I'):
                    via_city = via_city+reader[i][0]

                else:
                    pass
                i=i+1

        pythonDict = {'city': departure_city, 'to': 0, 'from': 1, 'via': 0}
        jsonData = json.dumps(pythonDict)
        list_json.append(jsonData)
        
        pythonDict = {'city': arrival_city, 'to': 1, 'from': 0, 'via': 0}
        jsonData = json.dumps(pythonDict)
        list_json.append(jsonData)

        pythonDict = {'city': via_city, 'to': 0, 'from': 0, 'via': 1}
        jsonData = json.dumps(pythonDict)
        list_json.append(jsonData)

        self.removeDir(file_name)
        return list_json
