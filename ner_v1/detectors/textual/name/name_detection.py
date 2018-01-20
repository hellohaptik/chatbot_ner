import re
import models.constant as model_constant
from models.models import Models
from ner_v1.constant import FROM_MESSAGE, FROM_MODEL_VERIFIED, FROM_MODEL_NOT_VERIFIED
import ner_v1.detectors.constant as detector_constant
from ner_v1.detectors.textual.text.text_detection import TextDetector
from lib.nlp.tokenizer import Tokenizer


class NameDetector(object):
    def __init__(self, entity_name):
        self.entity_name = entity_name
        self.text = ''
        self.names=[]
        #self.text_dict = {}
        self.tagged_text = ''
        #self.processed_text = ''
        #self.city = []
        self.original_name_text = []
        self.text_detection_object = TextDetector(entity_name=entity_name)

    def text_detection_name(self, text):
        """
        Makes a call to text_detection
        Args:
            text: original text to be passed

        Returns: a list of names detected

        """
        return self.text_detection_object.detect_entity(text=text)


    def detect_entity(self, text):
        """

        Args:
            text:

        Returns:

        """
        self.text = text
        self.tagged_text=self.text
        text_detection_result = self.text_detection_name(text)
        print(text_detection_result)
        hashed_text = self.hasher(text, text_detection_result)
        return self.splitting_logic(hashed_text)

    def hasher(self,text, text_detection_result):
        """

        Args:
            raw_text:
            text_detection_result:

        Returns:

        """
        hashed_text = Tokenizer().tokenize(text.lower())

        for i in (text_detection_result[1]):
            for j in range(len(hashed_text)):
                hashed_text[j] = hashed_text[j].replace(i, "_" + i + "_")
        print(hashed_text)



        return hashed_text



    def splitting_logic(self, hashed_text):
        """

        Args:
            hashed_text:

        Returns:

        """
        results = []
        tokenized_text = hashed_text
        name_list = []
        name_holder = []

        for each in tokenized_text:
            if each.startswith('_') and each.endswith('_'):
                name_holder.append(each.replace('_', ''))

            else:
                if name_holder:
                    name_list.append(name_holder)
                    name_holder = []

        if name_holder:
            name_list.append(name_holder)

        for name in name_list:
            name_dict = {'original_text': " ".join(name),
                         'entity_value': {"first_name": name[0], "middle_name": None, "last_name": None}}

            if len(name) > 1:
                name_dict['entity_value']['last_name'] = name[-1]
                name_dict['entity_value']['middle_name'] = " ".join(name[1:-1]) or None

            results.append(name_dict)

        return results


