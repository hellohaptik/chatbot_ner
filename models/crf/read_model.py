# -*- coding: utf-8 -*-
import csv
import json
import os, os.path
import nltk
import CRFPP
from lib.nlp.const import tokenizer
from models.constants import city_model_path, CITY_ENTITY_TYPE
from models.utils import get_current_timestamp, create_directory


class GenerateCRFTrain(object):

    def __init__(self):
        self.tagger = None
        self._model_path = None

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
        xsize = self.tagger.xsize()
        for i in range(0, size):
           output.append([self.tagger.x(i, 0), self.tagger.y2(i)])
        return output
    

    def get_crf_output(self, bot_message, user_message):
        self.initialize_files('city')
        self.add_data_to_tagger(bot_message, user_message)
        self.run()