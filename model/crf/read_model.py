# -*- coding: utf-8 -*-
import subprocess
import gzip
import csv
import json
import requests
import numpy as np
import os, os.path
import time
import datetime
from nltk import word_tokenize, pos_tag
import re
from model.constant import RES, KEEP_COLS, EMOJI_PATTERN, TEXT, KEEP_CONV, MESSAGE_DIRECTION, STEP4_COLS, DATA, NOISE_LIST, STEP7_COLS_arrival, STEP7_COLS_arrival_departure, STEP7_COLS_departure
np.set_printoptions(threshold='nan')

"""
step1--> selects messages of type in RES and also columns in KEEP_COLS and returns a dataframe

step2--> removing json strings and extracting text from messages containing json while keeping other messages as they are and returns a new dataframe

step3--> changing dataframe returned by step2 to conversations. like ->>coll_id, outbound_msg, inbound_msg
        This step returns a dataframe of conversations

step4--> runs NER on inbound messages with bot_message as outbound_msg and retrieves arrival_city, departure_city, original text returned by city and city advance and cities detected by city along with inbound_msg, outbound_msg and coll_id

step5--> used to remove unwanted text from messages like product_id, image_id etc

step6--> used to convert entire dataframe to lowercase

step7--> divides dataframe from step4 to three parts--> csv containing messages which has only arrival_city, csv containing
        messages which has only departure city and csv which contains messages which has both arrival as well as departure city

step8--> generates crf files from each of the csv created by step7 (calls crf_generate functions to convert each type of crf(to, from, from-to) into crf files)

step9--> divides data to 75-25 for test train from three crf files in step8 and joins them to create one test and one train file(calls split_test_train())

write_to_file--> takes a file name, which mode to write in nad text to write as input and writes to that file

makeDir--> take a string as input to check if that directory exists or not and if not creates that directory

remove_noise--> removes noise from messages. where noise is elements of list NOISE_LIST

remove_non_ascii--> reomves non ascii character from text(emojis)

capitalize_first--> changes the case of fist letter of a string

capitalize_first_only--> changes the case of first letters of token in inbound and outbound messages and returns two lists

split_test_train--> function which takes a file name which we wants to divide into test and train, train file name and test file name.

--> The input to the main function variable is path to the file which contains data in csv format. (path with respect to current directory)

--> At the end, conversations will be saved in relevant_data directory. And a directory of crd_data will be created which will contain your 
    test, train and crf-from, to, from-to files.
"""
class GenerateCRFTrain(object):

    
    
    def __init__(self, file_to_process):
        self.file_name = file_to_process
        self.file_to_process = os.path.splitext(os.path.basename(self.file_name))[0]
        

    def generateCRF(self):
        self.makeDir('input')
        self.makeDir('crf_data')
        self.df_stage1 = self.step1()
        self.df_stage2 = self.step2()
        del self.df_stage1
        # self.df_stage2.to_csv('preprocess/flights1.csv', index=False, columns = KEEP_COLS)
        self.df_stage3 = self.step3()
        self.step6()
        del self.df_stage2
        # self.df_stage3.to_csv('preprocess/flights2.csv', index=False, columns=KEEP_CONV)
        self.df_stage4 = self.step4()
        del self.df_stage3
        self.df_stage4.to_csv('relevant_data/'+self.file_to_process+'.csv', index=False, columns=STEP4_COLS)
        self.df_stage4 = pd.read_csv('relevant_data/'+self.file_to_process+'.csv')
        self.step5()
        self.df_stage4.to_csv('preprocess/flights3.csv', index=False, columns=STEP4_COLS)
        self.step7()
        self.step8()
        self.step9()
        # self.step10()

    def write_to_file(self, file_to_open, mode_to_write, string_to_write):
        with open(file_to_open, mode_to_write)as f:
            f.write(string_to_write)

    def step9(self):
        self.makeDir('crf_data/train')
        self.makeDir('crf_data/train/city')
        self.makeDir('crf_data/test')
        self.makeDir('crf_data/test/city')
        self.makeDir('crf_data/train/city/'+self.file_to_process)
        self.makeDir('crf_data/test/city/'+self.file_to_process)
        self.split_test_train('crf_data/data/'+self.file_to_process+'/to.txt', 'crf_data/train/city/'+self.file_to_process+'/train.data', 'crf_data/test/city/'+self.file_to_process+'/test.data')
        self.split_test_train('crf_data/data/'+self.file_to_process+'/from.txt', 'crf_data/train/city/'+self.file_to_process+'/train.data', 'crf_data/test/city/'+self.file_to_process+'/test.data')
        self.split_test_train('crf_data/data/'+self.file_to_process+'/from-to.txt', 'crf_data/train/city/'+self.file_to_process+'/train.data', 'crf_data/test/city/'+self.file_to_process+'/test.data') 

    def step8(self):
        self.crfgenerate_to()
        self.crfgenerate_from()
        self.crfgenerate_to_from()
    

    def step7(self):
        df_arrival = pd.DataFrame()
        df_departure = pd.DataFrame()
        df_arrival_departure = pd.DataFrame()
        i=0
        while (i<len(self.df_stage4)):
            if (str(self.df_stage4.iloc[i][STEP4_COLS[8]])=='1'):
                if ((self.df_stage4.iloc[i][STEP4_COLS[5]])==' '):
                    temp = pd.DataFrame({STEP4_COLS[0]:[self.df_stage4.iloc[i][STEP4_COLS[0]]], STEP4_COLS[1]:[self.df_stage4.iloc[i][STEP4_COLS[1]]], STEP4_COLS[2]:[self.df_stage4.iloc[i][STEP4_COLS[2]]], STEP4_COLS[3]:[self.df_stage4.iloc[i][STEP4_COLS[3]]], STEP4_COLS[4]:[self.df_stage4.iloc[i][STEP4_COLS[4]]], STEP4_COLS[6]:[self.df_stage4.iloc[i][STEP4_COLS[6]]], STEP4_COLS[7]:[self.df_stage4.iloc[i][STEP4_COLS[7]]]})
                    df_departure = pd.concat([df_departure, temp])

                elif ((self.df_stage4.iloc[i][STEP4_COLS[6]])==' '):
                    temp = pd.DataFrame({STEP4_COLS[0]:[self.df_stage4.iloc[i][STEP4_COLS[0]]], STEP4_COLS[1]:[self.df_stage4.iloc[i][STEP4_COLS[1]]], STEP4_COLS[2]:[self.df_stage4.iloc[i][STEP4_COLS[2]]], STEP4_COLS[3]:[self.df_stage4.iloc[i][STEP4_COLS[3]]], STEP4_COLS[4]:[self.df_stage4.iloc[i][STEP4_COLS[4]]], STEP4_COLS[5]:[self.df_stage4.iloc[i][STEP4_COLS[5]]], STEP4_COLS[7]:[self.df_stage4.iloc[i][STEP4_COLS[7]]]})
                    df_arrival = pd.concat([df_arrival, temp])

                else:
                    temp = pd.DataFrame({STEP4_COLS[0]:[self.df_stage4.iloc[i][STEP4_COLS[0]]], STEP4_COLS[1]:[self.df_stage4.iloc[i][STEP4_COLS[1]]], STEP4_COLS[2]:[self.df_stage4.iloc[i][STEP4_COLS[2]]], STEP4_COLS[3]:[self.df_stage4.iloc[i][STEP4_COLS[3]]], STEP4_COLS[4]:[self.df_stage4.iloc[i][STEP4_COLS[4]]], STEP4_COLS[5]:[self.df_stage4.iloc[i][STEP4_COLS[5]]], STEP4_COLS[6]:[self.df_stage4.iloc[i][STEP4_COLS[6]]], STEP4_COLS[7]:[self.df_stage4.iloc[i][STEP4_COLS[7]]]})
                    df_arrival_departure = pd.concat([df_arrival_departure, temp])

            i=i+1
        df_arrival.to_csv('relevant_data/'+self.file_to_process+'_arrival.csv', index=False, columns=STEP7_COLS_arrival)
        df_departure.to_csv('relevant_data/'+self.file_to_process+'_departure.csv', index=False, columns=STEP7_COLS_departure)
        df_arrival_departure.to_csv('relevant_data/'+self.file_to_process+ '_arrival_departure.csv', index=False, columns=STEP7_COLS_arrival_departure)


    def step6(self):
        self.df_stage3.outbound_msg = self.df_stage3.outbound_msg.str.lower()
        self.df_stage3.inbound_msg = self.df_stage3.inbound_msg.str.lower()

    def step5(self):
        i=0
        while (i<len(self.df_stage4)):
            outbound_msg = re.sub(r'{.*?}}*', ' ',self.df_stage4.iloc[i][STEP4_COLS[1]])
            inbound_msg = re.sub(r'{.*?}}*', ' ', self.df_stage4.iloc[i][STEP4_COLS[2]])

            self.df_stage4.loc[i, STEP4_COLS[1]] = outbound_msg
            self.df_stage4.loc[i, STEP4_COLS[2]] = inbound_msg
            i=i+1


    def step4(self):
        temp_original_city, temp_detected_city, temp_arrival_city, temp_departure_city, temp_original_city_advance, arrival_city, departure_city, original_city_advance = ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '

        df_city = pd.DataFrame()
        """coll_id  outbound_msg    inbound_msg     detected_city   original_city   arrival_city"""
        i=0
        while (i<len(self.df_stage3)):
            response = requests.get('%s/v1/text/?message=%s&entity_name=%s&structured_value=&structured_value_verification=&fallback_value=None&bot_message=%s'%('http://khushal.hellohaptik.com:8081',self.df_stage3.iloc[i][KEEP_CONV[2]],'city',self.df_stage3.iloc[i][KEEP_CONV[1]]))
            if (response):
                entity_data_array = json.loads(response.content)[DATA]
                if (len(entity_data_array)>0):
                    j=0
                    while (j<len(entity_data_array)):
                        temp_original_city = temp_original_city+' '+entity_data_array[j]['original_text']
                        temp_detected_city = temp_detected_city+' '+entity_data_array[j]['entity_value']['value']
                        j=j+1
                    response = requests.get('%s/v1/city_advance/?message=%s&entity_name=%s&structured_value=&structured_value_verification=&fallback_value=None&bot_message=%s'%('http://khushal.hellohaptik.com:8081',self.df_stage3.iloc[i][KEEP_CONV[2]],'city',self.df_stage3.iloc[i][KEEP_CONV[1]]))
                    print temp_original_city
                    if ('arrival_city' in json.loads(response.content)[DATA][0]['entity_value']):
                        entity_data = json.loads(response.content)
                        entity_data_array = entity_data[DATA]
                        j=0
                        while(j<len(entity_data_array)):
                            arrival_city = entity_data_array[j]['entity_value']['arrival_city']
                            departure_city = entity_data_array[j]['entity_value']['departure_city']
                            original_city_advance = entity_data_array[j]['original_text']

                            if (arrival_city!=None):
                                temp_arrival_city = temp_arrival_city+' '+arrival_city
                            if (departure_city!=None):
                                temp_departure_city = temp_departure_city+' '+departure_city
                            
                            temp_original_city_advance = temp_original_city_advance+' '+original_city_advance
                            j=j+1

                    if (temp_detected_city!='  None'):
                        temp = pd.DataFrame({STEP4_COLS[0]:[self.df_stage3.iloc[i][STEP4_COLS[0]]], STEP4_COLS[1]: [self.df_stage3.iloc[i][STEP4_COLS[1]]], STEP4_COLS[2]: [self.df_stage3.iloc[i][STEP4_COLS[2]]], STEP4_COLS[3]: [temp_detected_city], STEP4_COLS[4]: [temp_original_city], STEP4_COLS[5]: [temp_arrival_city], STEP4_COLS[6]: [temp_departure_city], STEP4_COLS[7]: [temp_original_city_advance], STEP4_COLS[8]:[len(entity_data_array)]})
                        df_city = pd.concat([df_city, temp])
                    
                    temp_original_city, temp_detected_city, temp_arrival_city, temp_departure_city, temp_original_city_advance, arrival_city, departure_city, original_city_advance = ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '
            i=i+1

        return df_city


    def step3(self):
        inbound_msg = ' '
        outbound_msg = 'None'
        df = pd.DataFrame()
        i=0
        while (i<len(self.df_stage2)):
            conv_id = str(self.df_stage2.iloc[i][KEEP_COLS[1]])
            coll_id = str(self.df_stage2.iloc[i][KEEP_COLS[0]])
            message_direction = str(self.df_stage2.iloc[i][KEEP_COLS[2]])
            message = str(self.df_stage2.iloc[i][KEEP_COLS[4]])

            if (message_direction==MESSAGE_DIRECTION[0]):
                if (i>0):
                    temp_conv_id = str(self.df_stage2.iloc[i-1][KEEP_COLS[1]])
                    temp_coll_id = str(self.df_stage2.iloc[i-1][KEEP_COLS[0]])
                    temp_message_direction = str(self.df_stage2.iloc[i-1][KEEP_COLS[2]])
                    temp_message = str(self.df_stage2.iloc[i-1][KEEP_COLS[4]])

                    if ((temp_coll_id==coll_id)and(temp_conv_id==conv_id)and(temp_message_direction==MESSAGE_DIRECTION[1])):
                        outbound_msg = temp_message

                    while (1):
                        temp_conv_id = str(self.df_stage2.iloc[i][KEEP_COLS[1]])
                        temp_coll_id = str(self.df_stage2.iloc[i][KEEP_COLS[0]])
                        temp_message_direction = str(self.df_stage2.iloc[i][KEEP_COLS[2]])
                        temp_message = str(self.df_stage2.iloc[i][KEEP_COLS[4]])
                        if ((temp_coll_id==coll_id)and(temp_conv_id==conv_id)and(temp_message_direction==MESSAGE_DIRECTION[0])):
                            inbound_msg = inbound_msg+' '+temp_message
                        else:
                            temp = pd.DataFrame({KEEP_CONV[0]:[coll_id], KEEP_CONV[1]:[outbound_msg], KEEP_CONV[2]:[inbound_msg]})
                            df = pd.concat([df,temp])
                            outbound_msg = 'None'
                            inbound_msg = ' '
                            break
                        i=i+1
                        if (i>=len(self.df_stage2)):
                            temp = pd.DataFrame({KEEP_CONV[0]:[coll_id], KEEP_CONV[1]:[outbound_msg], KEEP_CONV[2]:[inbound_msg]})
                            df = pd.concat([df,temp])
                            outbound_msg = 'None'
                            inbound_msg = ' '
                            break
                else:

                    while(1):
                        temp_conv_id = str(self.df_stage2.iloc[i][KEEP_COLS[1]])
                        temp_coll_id = str(self.df_stage2.iloc[i][KEEP_COLS[0]])
                        temp_message_direction = str(self.df_stage2.iloc[i][KEEP_COLS[2]])
                        temp_message = str(self.df_stage2.iloc[i][KEEP_COLS[4]])

                        if ((temp_coll_id==coll_id)and(temp_conv_id==conv_id)and(temp_message_direction==MESSAGE_DIRECTION[0])):
                            inbound_msg = inbound_msg+' '+temp_message
                        else:
                            temp = pd.DataFrame({KEEP_CONV[0]:[coll_id], KEEP_CONV[1]:[outbound_msg], KEEP_CONV[2]:[inbound_msg]})
                            df = pd.concat([df,temp])
                            outbound_msg = 'None'
                            inbound_msg = ' '
                            break
                        i=i+1
                        if (i>=len(self.df_stage2)):
                            temp = pd.DataFrame({KEEP_CONV[0]:[coll_id], KEEP_CONV[1]:[outbound_msg], KEEP_CONV[2]:[inbound_msg]})
                            df = pd.concat([df,temp])
                            outbound_msg = 'None'
                            inbound_msg = ' '
                            break
            else:
                i=i+1

        return df


    def step2(self):
        df = pd.DataFrame()
        for index, row in self.df_stage1.iterrows():
            s = str(row[4])
            try:
                json_line = json.loads(s)
                try:
                    some_object_iterator = iter(json_line)
                    if (TEXT in json_line):
                        if ((json_line['text'])!=''):
                            temp = pd.DataFrame({KEEP_COLS[0]:row[0], KEEP_COLS[1]:row[1], KEEP_COLS[2]:row[2], KEEP_COLS[3]:row[3], KEEP_COLS[4]:[json_line[TEXT].encode('utf-8')]})
                            df = pd.concat([df,temp])
                except TypeError:
                    if ((EMOJI_PATTERN.sub(r'',s))!=''):
                        temp = pd.DataFrame({KEEP_COLS[0]:row[0], KEEP_COLS[1]:row[1], KEEP_COLS[2]:row[2], KEEP_COLS[3]:row[3], KEEP_COLS[4]:[EMOJI_PATTERN.sub(r'',s)]})
                        df = pd.concat([df,temp])
            except ValueError:
                if ((EMOJI_PATTERN.sub(r'',s))!=''):
                    temp = pd.DataFrame({KEEP_COLS[0]:[row[0]], KEEP_COLS[1]:[row[1]], KEEP_COLS[2]:[row[2]], KEEP_COLS[3]:[row[3]], KEEP_COLS[4]:[EMOJI_PATTERN.sub(r'',s)]})
                    df = pd.concat([df,temp])
        return df


    def makeDir(self, s):
        if not os.path.exists(s):
            os.makedirs(s)

    def step1(self):
        df = pd.read_csv(self.file_name)
        new_df_cols = df[KEEP_COLS]
        new_df_msg_type = new_df_cols[new_df_cols['msg_type'].isin(RES)]
        new_df_msg_type = new_df_msg_type.dropna()
        return new_df_msg_type

    def remove_noise(self, input_text):
        words = input_text.split() 
        noise_free_words = [word for word in words if word not in NOISE_LIST] 
        noise_free_text = " ".join(noise_free_words) 
        return noise_free_text

    def remove_non_ascii(self, text):
        return ''.join(i for i in text if ord(i)<128)   

    def capitalize_first(self, token_outbound, token_inbound, token_original_city):
        temp_token_outbound = []
        temp_token_inbound = []

        for token in token_outbound:
            if (token in token_original_city):
                token = token.title()
            temp_token_outbound.append(token)

        for token in token_inbound:
            if (token in token_original_city):
                token = token.title()
            temp_token_inbound.append(token)

        return temp_token_outbound, temp_token_inbound

        
    def crfgenerate_to(self):
        df = pd.read_csv('relevant_data/'+self.file_to_process+'_arrival.csv')

        i=0
        while (i<len(df)):
            
            # print i
            try:
                token_outbound = word_tokenize(df.iloc[i][STEP7_COLS_arrival[1]])#outbound msg
                token_inbound = word_tokenize(df.iloc[i][STEP7_COLS_arrival[2]])#inbound_msg

                token_original_city = word_tokenize(df.iloc[i][STEP4_COLS[4]])
                token_pos_original_city = pos_tag(token_original_city)

                # token_outbound, token_inbound = self.capitalize_first(token_outbound, token_inbound, token_original_city)

                token_pos_inbound = pos_tag(token_inbound)
                token_pos_outbound = pos_tag(token_outbound)

                flag=0
                counter=0

                while (counter<len(token_outbound)):
                    temp_word = token_outbound[counter]
                    temp_pos = token_pos_outbound[counter][1]
                    temp_io = 'o'
                    temp_label = ''

                    if (token_outbound[counter] in token_original_city):
                        if (flag==1):
                            temp_label = 'to-I'
                            temp_word[0].str.upper() 
                        else:
                            temp_label = 'to-B'
                            flag=1
                    else:
                        temp_label = 'O'

                    self.makeDir('crf_data/data/'+self.file_to_process)
                    self.write_to_file('crf_data/data/'+self.file_to_process+'/to.txt', 'a', temp_word+' '+temp_pos+' '+temp_io+' '+temp_label+'\n')
                    counter=counter+1

                flag=0
                counter=0

                while (counter<len(token_inbound)):
                    temp_word = token_inbound[counter]
                    temp_pos = token_pos_inbound[counter][1]
                    temp_io = 'i'
                    temp_label = ''

                    if (token_inbound[counter] in token_original_city):
                        if (flag==1):
                            temp_label = 'to-I'
                        else:
                            temp_label = 'to-B'
                            flag=1
                    else:
                        temp_label = 'O'

                    self.makeDir('crf_data/data/'+self.file_to_process)
                    self.write_to_file('crf_data/data/'+self.file_to_process+'/to.txt', 'a', temp_word+' '+temp_pos+' '+temp_io+' '+temp_label+'\n')
                    
                    counter=counter+1
                self.write_to_file('crf_data/data/'+self.file_to_process+'/to.txt', 'a', '\n')

            except Exception,e:
                print i, e
            i=i+1



    def crfgenerate_from(self):
        df = pd.read_csv('relevant_data/'+self.file_to_process+'_departure.csv')

        i=0
        while (i<len(df)):
            
            # print i
            try:
                token_outbound = word_tokenize(df.iloc[i][STEP7_COLS_arrival[1]])#outbound msg
                token_inbound = word_tokenize(df.iloc[i][STEP7_COLS_arrival[2]])#inbound_msg

                token_original_city = word_tokenize(df.iloc[i][STEP4_COLS[4]])
                token_pos_original_city = pos_tag(token_original_city)

                # token_outbound, token_inbound = self.capitalize_first(token_outbound, token_inbound, token_original_city)

                token_pos_inbound = pos_tag(token_inbound)
                token_pos_outbound = pos_tag(token_outbound)

                flag, counter = 0, 0
                while (counter<len(token_outbound)):
                    temp_word = token_outbound[counter]
                    temp_pos = token_pos_outbound[counter][1]
                    temp_io = 'o'
                    temp_label = ''

                    if (token_outbound[counter] in token_original_city):
                        if (flag==1):
                            if (token_inbound[counter-2]=='via'):
                                temp_label = 'via-I'
                            else:
                                if (token_outbound[counter-1] in token_original_city):
                                    temp_label = 'from-I'
                                else:
                                    temp_label = 'from-B'
                        else:
                            if (counter>0):
                                if (token_inbound[counter-1]=='via'):
                                    temp_label = 'via-B'
                                else:
                                    temp_label = 'from-B'
                            else:
                                temp_label = 'from-B'
                            flag=1
                    else:
                        temp_label = 'O'

                    self.makeDir('crf_data/data/'+self.file_to_process)
                    self.write_to_file('crf_data/data/'+self.file_to_process+'/from.txt', 'a', temp_word+' '+temp_pos+' '+temp_io+' '+temp_label+'\n')
                    counter=counter+1

                flag, counter = 0, 0
                while (counter<len(token_inbound)):
                    temp_word = token_inbound[counter]
                    temp_pos = token_pos_inbound[counter][1]
                    temp_io = 'i'
                    temp_label = ''

                    if (token_inbound[counter] in token_original_city):
                        if (flag==1):
                            if (token_inbound[counter-2]=='via'):
                                temp_label = 'via-I'
                            else:
                                if (token_inbound[counter-1] in token_original_city):
                                    temp_label = 'from-I'
                                else:
                                    temp_label = 'from-B'
                        else:
                            if (counter>0):
                                if (token_inbound[counter-1]=='via'):
                                    temp_label = 'via-B'
                                else:
                                    temp_label = 'from-B'
                            else:
                                temp_label = 'from-B'
                            flag=1
                    else:
                        temp_label = 'O'

                    self.makeDir('crf_data/data/'+self.file_to_process)
                    self.write_to_file('crf_data/data/'+self.file_to_process+'/from.txt', 'a', temp_word+' '+temp_pos+' '+temp_io+' '+temp_label+'\n')
                    counter=counter+1
                self.write_to_file('crf_data/data/'+self.file_to_process+'/from.txt', 'a', '\n')

            except Exception,e:
                print i, e
            i=i+1

    def capitalize_first_only(self, token_departure_city, token_arrival_city):
        temp_departure_city = []
        temp_arrival_city = []

        for token in token_departure_city:
            temp_departure_city.append(token.title())

        for token in token_arrival_city:
            temp_arrival_city.append(token.title())
        return temp_departure_city, temp_arrival_city

    def crfgenerate_to_from(self):
        df = pd.read_csv('relevant_data/'+self.file_to_process+'_arrival_departure.csv')
        i=0
        while(i<len(df)):
            try:
                token_outbound = word_tokenize(df.iloc[i][STEP7_COLS_arrival[1]])#outbound msg
                token_inbound = word_tokenize(df.iloc[i][STEP7_COLS_arrival[2]])#inbound_msg

                token_original_city = word_tokenize(df.iloc[i][STEP4_COLS[4]])
                token_pos_original_city = pos_tag(token_original_city)

                # token_outbound, token_inbound = self.capitalize_first(token_outbound, token_inbound, token_original_city)

                token_pos_inbound = pos_tag(token_inbound)
                token_pos_outbound = pos_tag(token_outbound)

                token_departure_city = word_tokenize(df.iloc[i][STEP4_COLS[6]].lower())
                token_arrival_city = word_tokenize(df.iloc[i][STEP4_COLS[5]].lower())

                # token_departure_city, token_arrival_city = self.capitalize_first_only(token_departure_city, token_arrival_city)

                flag_arrival, flag_departure, counter = 0,0,0

                while (counter<len(token_outbound)):
                    temp_word = token_outbound[counter]
                    temp_pos = token_pos_outbound[counter][1]
                    temp_io = 'i'
                    temp_label = ''
                    flag_found=0

                    if (temp_word in token_departure_city):
                        if (flag_departure==1):
                            if (token_outbound[counter-1] in token_departure_city):
                                temp_label = 'from-I'
                                flag_found = 1
                            else:
                                temp_label = 'from-B'
                                flag_found = 1
                        else:
                            temp_label = 'from-B'
                            flag_departure = 1
                            flag_found = 1
                    else:
                        temp_label = 'O'

                    if ((temp_word in token_arrival_city)):
                        if (flag_arrival==1):
                            if (token_outbound[counter-1] in token_arrival_city):
                                temp_label = 'to-I'
                                flag_found = 1
                            else:
                                temp_label = 'to-B'
                                flag_found = 1
                        else:
                            temp_label = 'to-B'
                            flag_arrival = 1
                            flag_found = 1
                    else:
                        if (flag_found==0):
                            temp_label = 'O'

                    self.makeDir('crf_data/data/'+self.file_to_process)
                    self.write_to_file('crf_data/data/'+self.file_to_process+'/from-to.txt', 'a', temp_word+' '+temp_pos+' '+temp_io+' '+temp_label+'\n')
                    counter=counter+1

                flag_arrival, flag_departure, counter = 0,0,0
                while (counter<len(token_inbound)):
                    temp_word = token_inbound[counter]
                    temp_pos = token_pos_inbound[counter][1]
                    temp_io = 'i'
                    temp_label = ''
                    flag_found = 0

                    if (temp_word in token_departure_city):
                        if (flag_departure==1):
                            if (token_inbound[counter-1] in token_departure_city):
                                temp_label = 'from-I'
                                flag_found = 1
                            else:
                                temp_label = 'from-B'
                                flag_found = 1
                        else:
                            temp_label = 'from-B'
                            flag_departure = 1
                            flag_found = 1
                    else:
                        temp_label = 'O'

                    if (temp_word in token_arrival_city):
                        if (flag_arrival==1):
                            if (token_inbound[counter-1] in token_arrival_city):
                                temp_label = 'to-I'
                                flag_found = 1
                            else:
                                temp_label = 'to-B'
                                flag_found = 1
                        else:
                            temp_label = 'to-B'
                            flag_arrival = 1
                            flag_found = 1
                    else:
                        if (flag_found==0):
                            temp_label = 'O'

                    self.makeDir('crf_data/data/'+self.file_to_process)
                    self.write_to_file('crf_data/data/'+self.file_to_process+'/from-to.txt', 'a', temp_word+' '+temp_pos+' '+temp_io+' '+temp_label+'\n')
                    counter=counter+1
                self.write_to_file('crf_data/data/'+self.file_to_process+'/from-to.txt', 'a', '\n')

            except Exception,e:
                print i, e
            i=i+1

    
    def split_test_train(self, file_to_open, file_to_write_train, file_to_write_test):
        with open (file_to_open)as f:
            row = f.read()
            reader =  row.split('\n\n')
            length_train = int(0.75*(len(reader)))
            counter = 0
            while(counter<length_train):
                self.write_to_file(file_to_write_train, 'a', reader[counter]+'\n'+'\n')
                counter = counter+1

            while(counter<len(reader)):
                self.write_to_file(file_to_write_test, 'a', reader[counter]+'\n'+'\n')
                counter = counter+1    

    def write_to_file(self, file_to_open, mode_to_write, string_to_write):
        with open(file_to_open, mode_to_write)as f:
            f.write(string_to_write)

    def removeDir(self, file_to_remove):
        if os.path.exists(file_to_remove):
            os.remove(file_to_remove)

    def predict(self, bot_message, user_message):
        self.makeDir('output')
        self.removeDir('test.data')
        self.removeDir('output/output1.txt')
        tokens_bot_message = word_tokenize(bot_message)
        tokens_user_message = word_tokenize(user_message)

        pos_bot_message = pos_tag(tokens_bot_message)
        pos_user_message = pos_tag(tokens_user_message)

        s = ''
        for token in pos_bot_message:
            # print token
            self.write_to_file('test.data','a',token[0]+' '+token[1]+' '+'o'+'\n')
            s = s+token[0]+' '+token[1]+' '+'o'+'\n'
        for token in pos_user_message:
            self.write_to_file('test.data', 'a', token[0]+' '+token[1]+' '+'i'+'\n')
            s = s+ token[0]+' '+token[1]+' '+'i'+'\n'

        os.system('bash exec.sh')
        self.give_output('output/output1.txt')

    def join_files(self):
        makeDir('crf_data/data/'+self.file_to_process)

    def give_output(self, file_path):
        departure_city = ''
        arrival_city = ''
        via_city = ''
        with open (file_path, 'r')as f:
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
        print 'departure_city: '+departure_city
        print 'arrival_city: '+arrival_city
        print 'via_city: '+via_city

    def get_crf_city(self, bot_message, user_message):
        current_time = self.get_current_timestamp()

        self.make_crf_file(bot_message, user_message, str(current_time))

        self.call_crf(str(current_time))

        print self.get_arrival_departure(str(current_time))

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

        s = ''
        for token in pos_bot_message:
            # print token
            self.write_to_file(file_name,'a',token[0]+' '+token[1]+' '+'o'+'\n')
            s = s+token[0]+' '+token[1]+' '+'o'+'\n'
        for token in pos_user_message:
            self.write_to_file(file_name, 'a', token[0]+' '+token[1]+' '+'i'+'\n')
            s = s+ token[0]+' '+token[1]+' '+'i'+'\n'

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

if __name__ == "__main__":

    """file_to_process = raw_input('Enter a file to process: ')
                obj = GenerateCRFTrain(str(file_to_process))
                # obj.generateCRF()
                sentence_bot = raw_input('Enter a bot sentence to process: ')
                sentence_user = raw_input('Enter a user sentence to process: ')
                obj.predict(str(sentence_bot), str(sentence_user))"""

    # obj.give_output('output/output1.txt')
    obj = GenerateCRFTrain('qwert')
    obj.get_crf_city('none', 'I am going to mumbai from ahmedabad')
