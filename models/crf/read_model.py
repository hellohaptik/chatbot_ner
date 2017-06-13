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

class GenerateCRFTrain(object):

    def __init__(self):
        self.tagger = None
        self._model_path = None

    def get_crf_output(self, bot_message, user_message):
        self.initialize_files(CITY_ENTITY_TYPE)
        self.add_data_to_tagger(bot_message, user_message)
        output = self.run_crf()
        print output
        print self.generate_city_output(output)

    def initialize_files(self, entity_type):
        if entity_type == CITY_ENTITY_TYPE:
            self._model_path = city_model_path
            self.tagger = CRFPP.Tagger("-m %s -v 3 -n2" % self._model_path)

    def add_data_to_tagger(self, bot_message, user_message):
        tokens_bot_message = tokenizer.tokenize(bot_message)
        tokens_user_message = tokenizer.tokenize(user_message)

        pos_bot_message = nltk.pos_tag(tokens_bot_message)
        pos_user_message = nltk.pos_tag(tokens_user_message)
        for token in pos_bot_message:
            self.tagger.add(token[0]+' '+token[1]+' '+'o')

        for token in pos_user_message:
            self.tagger.add(token[0]+' '+token[1]+' '+'o')

    def run_crf(self):
        output = []
        # parse and change internal stated as 'parsed'
        self.tagger.parse()

        size = self.tagger.size()
        for i in range(0, size):
           output.append([self.tagger.x(i, 0), self.tagger.y2(i)])
        return output


    def generate_city_output(self, crf_output_list):
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
                if temp_list is not None:
                    list_json.append(temp_list)

                else:
                    temp_list = self.check_label(reader_list=crf_output_list, reader_pointer=read_line,
                                                 begin_label=CITY_TO_B, inner_label=CITY_TO_I, from_bool=0, to_bool=1,
                                                 via_bool=0)
                    if temp_list is not None:
                        list_json.append(temp_list)

                    else:
                        temp_list = self.check_label(reader_list=crf_output_list, reader_pointer=read_line,
                                                     begin_label=CITY_VIA_B, inner_label=CITY_VIA_I,
                                                     from_bool=0, to_bool=0, via_bool=1)
                        if temp_list is not None:
                            list_json.append(temp_list)
            read_line+=1
        return list_json

    def make_json(self, city_value, from_bool, to_bool, via_bool):
        python_dict = {ENTITY: city_value, FROM: from_bool, TO: to_bool, VIA: via_bool}
        return python_dict

    def check_label(self, reader_list, reader_pointer, begin_label, inner_label, from_bool, to_bool, via_bool):
        list_json = []
        if reader_list[reader_pointer][1]==begin_label:
            # print reader_list[reader_pointer]
            xyz_city = reader_list[reader_pointer][0]
            if reader_pointer==(len(reader_list)-1):
                list_json.append(self.make_json(city_value=xyz_city, from_bool=from_bool, to_bool=to_bool, via_bool=via_bool))
                return list_json

            else:
                check_pointer = reader_pointer+1
                while check_pointer < (len(reader_list)):
                    if reader_list[check_pointer][1]!=inner_label:
                        list_json.append(self.make_json(city_value=xyz_city, from_bool=from_bool, to_bool=to_bool, via_bool=via_bool))
                        return list_json
                    else:
                        xyz_city = xyz_city +' '+ reader_list[check_pointer][0]
                        check_pointer+=1
                        if check_pointer==(len(reader_list)-1):
                            list_json.append(self.make_json(city_value=xyz_city, from_bool=from_bool, to_bool=to_bool, via_bool=via_bool))
                            return list_json
        return list_json