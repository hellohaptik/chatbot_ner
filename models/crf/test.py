# -*- coding: utf-8 -*-
from __future__ import absolute_import
from chatbot_ner.config import ner_logger, CITY_MODEL_PATH, DATE_MODEL_PATH
from lib.nlp.const import nltk_tokenizer
from lib.nlp.pos import POS
from .constant import CITY_ENTITY_TYPE, DATE_ENTITY_TYPE
from .constant import INBOUND, OUTBOUND
from .output_generation.city import generate_city_output
from .output_generation.date import generate_date_output
from six.moves import range

try:
    import CRFPP

    MODEL_RUN = True
except ImportError:
    CRFPP = False
    MODEL_RUN = False

"""
The class PredictCRF uses context random fields to establish relationship between words in the sentence
You have been given a template which it follows to achieve this.

This is explanation wrt. city detection
We have used seven types of labels to tag our data for ENTITY='city':

    Begining of departure city name is marked with label----- 'from-B'
    All other words in departure city name if marked with label----- 'from-I'

    Begining of arrivale city name is marked with label----- 'to-B'
    All other words in arrival city name if marked with label----- 'to-I'

    Begining of via city name is marked with label----- 'via-B'
    All other words in via city name if marked with label----- 'via-I'

    All the other words are marked with label----- 'O'

    A simple example is given below to explain out CRF labels:

        Args:
            bot_message = 'please help me with you departure city and arrival city'
            user_message = 'flights from new delhi to new york via dubai'

        Note*: bot messages get a feature as 'o'(outbound/sent by bot) and user message get a feature as
            'i'(inbound/sent by user) So the final tagged data will look like

        Corresponding CRF input data and corresponding output label:
            please NN o-------> O
            help VB o---------> O
            me NNS o----------> O
            with AD o---------> O
            your AJ o---------> O
            departure NN o----> O
            city PN o---------> O
            and NNS o---------> O
            arrival NN o------> O
            city PN o---------> O
            flights NNS i-----> O
            from VBP i--------> O 
            new NN i----------> from-B
            delhi NN i--------> from-I
            to TO i-----------> O
            new NN i----------> to-B
            york NN i---------> to-I
            via VB i----------> O
            dubai NN i--------> via-B

    We have provided you with a model in chatbot_ner/data/models/crf/city. you can replace it with your own model and
    use this class to run CRF. You will get a json list of all tagged data.

"""

CITY_MODEL_OBJECT = None  # store city model object
DATE_MODEL_OBJECT = None  # store date model object


class PredictCRF(object):
    def __init__(self):
        self.tagger = None
        self._model_path = None
        self.pos_tagger = POS()

    def get_model_output(self, entity_type, bot_message, user_message):
        """
        This function is a calls all other in order get final json list of tagged data.
        
        If model has been loaded then it calls initialize_files(), add_data_to_tagger and run_crf to get the 
        tagged data otherwise it will throw an error message
        """
        output_list = []
        if MODEL_RUN:
            self.initialize_files(entity_type=entity_type)
            self.add_data_to_tagger(bot_message, user_message)
            crf_output = self.run_crf()
            if entity_type == CITY_ENTITY_TYPE:
                output_list = generate_city_output(crf_data=crf_output)
                ner_logger.debug('NER MODEL OUTPUT: %s' % output_list)
            elif entity_type == DATE_ENTITY_TYPE:
                output_list = generate_date_output(crf_data=crf_output)
                ner_logger.debug('NER MODEL OUTPUT: %s' % output_list)
        else:
            ner_logger.debug('MODEL IS NOT RUNNING: CRFPP not installed')

        return output_list

    def initialize_files(self, entity_type):
        """
        This function checks the type of entity.
        We have currently done it for entity_type='city'.
        If the input parameter is entity_type city, it will run CRF model loaded for city and initialize the
        tagger and model_path accordingly

        Args:
            entity_type: type of entity

        """
        global CITY_MODEL_OBJECT, DATE_MODEL_OBJECT
        if entity_type == CITY_ENTITY_TYPE:
            self._model_path = CITY_MODEL_PATH
            if not CITY_MODEL_OBJECT:
                CITY_MODEL_OBJECT = CRFPP.Tagger("-m %s -v 3 -n2" % self._model_path)
                ner_logger.debug('CITY CRF model loaded %s' % self._model_path)

            self.tagger = CITY_MODEL_OBJECT
        elif entity_type == DATE_ENTITY_TYPE:
            self._model_path = DATE_MODEL_PATH
            if not DATE_MODEL_OBJECT:
                DATE_MODEL_OBJECT = CRFPP.Tagger("-m %s -v 3 -n2" % self._model_path)
                ner_logger.debug('date CRF model loaded %s' % self._model_path)

            self.tagger = DATE_MODEL_OBJECT

    def add_data_to_tagger(self, bot_message, user_message):
        """
        As explained, CRF need data in a particular format, this function converts the bot_message and user_message
        into that format and add it to the tagger.

        Args:
            bot_message: message from bot
            user_message: message from user

        for Example:
            Args:
                bot_message = 'none'
                user_message = 'flights from delhi to goa'

            Then this functions tokenize the bot and user messages, gets the POS tags, tags them as outbound or
            inbound as per the sender and adds it to the tagger object.

            tokens_bot_message = ['none']
            tokens_user_message = ['flights', 'from', 'delhi', 'goa']
            pos_bot_message = [['none', 'NN']]
            pos_user_message = [['flights','NNS'], ['from', 'VBP'], ['delhi', 'NN'], ['to', 'TO'], ['goa', 'VB']]

            none NN o
            flights NNS i
            from VBP i
            delhi NN i
            to TO i
            goa VB i
        """
        if bot_message is None:
            bot_message = ''

        tokens_bot_message = nltk_tokenizer.tokenize(bot_message)
        tokens_user_message = nltk_tokenizer.tokenize(user_message)

        pos_bot_message = self.pos_tagger.tag(tokens_bot_message)
        pos_user_message = self.pos_tagger.tag(tokens_user_message)
        for token in pos_bot_message:
            self.tagger.add(str(token[0]) + ' ' + str(token[1]) + ' ' + OUTBOUND)

        for token in pos_user_message:
            self.tagger.add(str(token[0]) + ' ' + str(token[1]) + ' ' + INBOUND)

    def run_crf(self):
        """
        This function runs CRF on data added to tagger and stores the [word    predicted_label] in output list and
        returns it. This list is then passed to generate_crf_output() to get the json list of data tagged.

        """
        output = []
        self.tagger.parse()

        size = self.tagger.size()
        for i in range(0, size):
            output.append([self.tagger.x(i, 0), self.tagger.y2(i)])
        self.tagger.clear()
        return output
