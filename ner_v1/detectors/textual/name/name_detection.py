from lib.nlp.tokenizer import Tokenizer
from ner_v1.detectors.textual.text.text_detection import TextDetector
from ner_v1.constant import FIRST_NAME, MIDDLE_NAME, LAST_NAME
from lib.nlp.pos import *
import re


class NameDetector(object):
    def __init__(self, entity_name):
        self.entity_name = entity_name
        self.text = ''
        self.names = []
        self.tagged_text = ''
        self.processed_text = ''
        self.original_name_text = []
        self.text_detection_object = TextDetector(entity_name=entity_name)

    @staticmethod
    def get_format_name(name_list):
        """
        :param name_list: list of names detected
                Example ['yash', 'modi']
        :return: ({first_name: "yash", middle_name: None, last_name: "modi"}, "yash modi")
        """
        original_text = " ".join(name_list)

        first_name = name_list[0]
        middle_name = None
        last_mame = None

        if len(name_list) > 1:
            last_mame = name_list[-1]
            middle_name = " ".join(name_list[1:-1]) or None

        entity_value = {FIRST_NAME: first_name, MIDDLE_NAME: middle_name, LAST_NAME: last_mame}

        return [entity_value], [original_text]

    def text_detection_name(self):
        """
        Makes a call to TextDetection
        :return: list of names detected in TextDetection
        """
        return self.text_detection_object.detect_entity(text=self.text)

    def get_name_using_pos_tagger(self, text):
        """
        Runs the text through templates and the returns words which are nouns
        and not present in the templates.
        :param text:
                Example text= My name is yash modi
        :return: [{first_name: "yash", middle_name: None, last_name: "modi"}], [ "yash modi"]
        """

        entity_value, original_text = [], []
        pos_tagger_object = POS()
        pattern1 = re.compile(r"name\s*(is|)\s*([\w\s]+)")
        pattern2 = re.compile(r"myself\s+([\w\s]+)")
        name_tokens = text.split(' ')
        tagged_names = pos_tagger_object.tag(name_tokens)
        pattern1_match = pattern1.findall(text)
        pattern2_match = pattern2.findall(text)

        is_question = [word[0] for word in tagged_names if word[1].startswith('WR') or
                       word[1].startswith('WP')]
        if is_question:
            return entity_value, original_text

        if pattern1_match:
            entity_value, original_text = self.get_format_name(pattern1_match[0][1].split())

        elif pattern2_match:
            entity_value, original_text = self.get_format_name(pattern2_match[0].split())

        else:
            pos_words = [word[0] for word in tagged_names if word[1].startswith('NN') or
                         word[1].startswith('JJ')]
            if pos_words:
                entity_value, original_text = self.get_format_name(pos_words)

        return entity_value, original_text

    def detect_entity(self, text, bot_message):
        """
        Takes text and and returns names
        :param bot_message: previous botmessage
        :param text: The original text
            Example:
                text = My name is yash modi
        :return:
        [{first_name: "yash", middle_name: None, last_name: "modi"}], [ "yash modi"]

        """
        if not self.context_check_botmessage(bot_message):
            return [], []
        self.text = text
        self.tagged_text = self.text
        text_detection_result = self.text_detection_name()
        replaced_text = self.replace_detected_text(text_detection_result)
        entity_value, original_text = self.detect_name_entity(replaced_text)

        if not entity_value:
            entity_value, original_text = self.get_name_using_pos_tagger(text)

        return entity_value, original_text

    def replace_detected_text(self, text_detection_result):
        """
        Replaces the detected name by _<name>_
        :param text_detection_result: list of detected names from TextDetection
        :return: tokenized list with detected names replaced by _ _
        """
        replaced_text = Tokenizer().tokenize(self.text.lower())
        for i in (text_detection_result[1]):
            for j in range(len(replaced_text)):
                replaced_text[j] = replaced_text[j].replace(i, "_" + i + "_")

        return replaced_text

    def detect_name_entity(self, replaced_text):
        """
        Forms a dictionary of the names
        :param replaced_text:
        text: The original text
            Example:
                text = My name is yash modi
        :return:
        [{first_name: "yash", middle_name: None, last_name: "modi"}], [ "yash modi"]


        """
        original_text, entity_value = [], []
        name_list = []
        name_holder = []

        for each in replaced_text:
            if each.startswith('_') and each.endswith('_'):
                name_holder.append(each.replace('_', ''))

            else:
                if name_holder:
                    name_list.append(name_holder)
                    name_holder = []

        if name_holder:
            name_list.append(name_holder)

        for name in name_list:
            name_entity_value, original_text_value = self.get_format_name(name)
            original_text.extend(original_text_value)
            entity_value.extend(name_entity_value)

        return entity_value, original_text

    @staticmethod
    def context_check_botmessage(botmessage):
        """
        Checks if previous botmessage contains name as keyword or not
        :param botmessage: previous botmessage
        :return: 

        """
        if "name" in botmessage:
            return True
        return False
    




