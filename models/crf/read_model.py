# -*- coding: utf-8 -*-
import csv
import json
import os, os.path
import nltk
import CRFPP
from lib.nlp.const import tokenizer
from models.constants import city_model_path, CITY_ENTITY_TYPE
from models.utils import get_current_timestamp, create_directory
from models.constants import CITY_FROM_B, CITY_TO_B, CITY_VIA_B, CITY_FROM_I, CITY_TO_I, CITY_VIA_I, INBOUND, \
    OUTBOUND, FROM, TO, VIA, ENTITY

"""
The class PredictCRF uses context random fields to establish relationship between words in the sentence
You have been given a template which it follows to achieve this.

We have used seven types of labels to tag our data for ENTITYE='city'.
"""
class PredictCRF(object):

    def __init__(self):
        self.tagger = None
        self._model_path = None

    def get_crf_output(self, bot_message, user_message):
        """
        Thus function is a calls all other in order get final json_list of tagged data


        """

        self.initialize_files(CITY_ENTITY_TYPE)
        self.add_data_to_tagger(bot_message, user_message)
        output = self.run_crf()
        print output
        print self.generate_city_output(output)

    def initialize_files(self, entity_type):
        """
        This function checks the type of entity. We have currently done it for ENTITY='city'.
        If the input parameter is entity type city, it will run CRF model loaded for city and initialize the 
        tagger and model_path accordingly
        """

        if entity_type == CITY_ENTITY_TYPE:
            self._model_path = city_model_path
            self.tagger = CRFPP.Tagger("-m %s -v 3 -n2" % self._model_path)

    def add_data_to_tagger(self, bot_message, user_message):
        """
        As explained, CRF need data in a particular format, this function converts the bot_message and user_message into
        that format and add it to the tagger. 

        for Example:
            bot_message = 'none'
            user_message = 'flights from delhi to goa'

            Then this functions tokenize the bot and user messages, gets the POS tags, tags them as outbound or inbound as per the
            sender and adds it to the tagger object.

            tokens_bot_message = ['none']
            tokens_user_message = ['flights', 'from', 'delhi', 'goa']
            pos_bot_message = [['none', 'NN']]
            pos_user_message = [['flights','NNS'], ['from', 'VBP'], ['delhi', 'NN'], ['to', 'TO'], ['goa', 'VB']]

            Note* bot messages get a feature of 
        """

        tokens_bot_message = tokenizer.tokenize(bot_message)
        tokens_user_message = tokenizer.tokenize(user_message)

        pos_bot_message = nltk.pos_tag(tokens_bot_message)
        pos_user_message = nltk.pos_tag(tokens_user_message)
        for token in pos_bot_message:
            self.tagger.add(token[0]+' '+token[1]+' '+OUTBOUND)

        for token in pos_user_message:
            self.tagger.add(token[0]+' '+token[1]+' '+INBOUND)

    def run_crf(self):
        output = []
        # parse and change internal stated as 'parsed'
        self.tagger.parse()

        size = self.tagger.size()
        for i in range(0, size):
           output.append([self.tagger.x(i, 0), self.tagger.y2(i)])
        return output


    def generate_city_output(self, crf_output_list):
        """
        This function takes a list of crf output as input and returns a json with proper tags of the entity

        for Example:
            bot_message = 'none'
            user_message = 'flights for delhi to goa'

            Then run_crf will give the following output:
                crf_output_list = [['none','O'], ['flights', 'O'], ['from', 'O'], ['delhi', 'from-B'], ['to', 'O'], ['goa', 'to-B']]

            Calling generate_city_output with crf_output_list will extract required text and return a json in th following form:
                [[{'city': 'delhi', 'via': 0, 'from': 1, 'to': 0}], [{'city': 'goa', 'via': 0, 'from': 0, 'to': 1}]]

        This functions iterates over the list and calls the check_label which will return a json list of tagged words.

        """
        list_json = []
        read_line = 0
        while read_line<(len(crf_output_list)):
            if crf_output_list[read_line][1]=='O':
                # print reader[read_line]
                pass
            else:
                temp_list = self.check_label(reader_list=crf_output_list, reader_pointer=read_line,
                                             begin_label=CITY_FROM_B, inner_label=CITY_FROM_I, from_bool=1, to_bool=0,
                                             via_bool=0)
                if len(temp_list) is not 0:
                    list_json.append(temp_list)

                else:
                    temp_list = self.check_label(reader_list=crf_output_list, reader_pointer=read_line,
                                                 begin_label=CITY_TO_B, inner_label=CITY_TO_I, from_bool=0, to_bool=1,
                                                 via_bool=0)
                    if len(temp_list) is not 0:
                        list_json.append(temp_list)

                    else:
                        temp_list = self.check_label(reader_list=crf_output_list, reader_pointer=read_line,
                                                     begin_label=CITY_VIA_B, inner_label=CITY_VIA_I,
                                                     from_bool=0, to_bool=0, via_bool=1)
                        if len(temp_list) is not 0:
                            list_json.append(temp_list)
            read_line+=1
        return list_json

    def make_json(self, city_value, from_bool, to_bool, via_bool):
        """
        This function return json of the value found in function check_label

        for Example:
            city_value = 'delhi'
            from_bool = 1
            to_bool = 0
            via_bool = 0

            then calling this function with ab ove parameters will give:
                {'city': 'delhi', 'via': 0, 'from': 1, 'to': 0}
        """


        python_dict = {ENTITY: city_value, FROM: from_bool, TO: to_bool, VIA: via_bool}
        return python_dict

    def check_label(self, reader_list, reader_pointer, begin_label, inner_label, from_bool, to_bool, via_bool):
        """
        this function checks if a particular word has been given a particular label

        for Example:
            reader_list = list returned by run_crf
            reader_pointer = 3
            begin_label = CITY_FROM_B
            inner_label = VITY_FROM_I
            from_bool = 1
            to_bool = 0
            via_bool = 0

            When check_label is called with above parameters, it checks if the word has been given CITY_FROM_B label and its following words
            have CITY_FROM_I label. I so it returns the proper json.
            For above inputs it will return
            [{'city': 'delhi', 'via': 0, 'from': 1, 'to': 0}]
        """
        list_json = []
        if reader_list[reader_pointer][1]==begin_label:
            xyz_city = reader_list[reader_pointer][0]
            if reader_pointer==(len(reader_list)-1):
                return self.make_json(city_value=xyz_city, from_bool=from_bool, to_bool=to_bool, via_bool=via_bool)

            else:
                check_pointer = reader_pointer+1
                while check_pointer < (len(reader_list)):
                    if reader_list[check_pointer][1]!=inner_label:
                        return self.make_json(city_value=xyz_city, from_bool=from_bool, to_bool=to_bool, via_bool=via_bool)
                    else:
                        xyz_city = xyz_city +' '+ reader_list[check_pointer][0]
                        check_pointer+=1
                        if check_pointer==(len(reader_list)-1):
                            return self.make_json(city_value=xyz_city, from_bool=from_bool, to_bool=to_bool, via_bool=via_bool)
        return list_json