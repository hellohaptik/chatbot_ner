from lib.nlp.tokenizer import Tokenizer
from ner_v1.detectors.textual.text.text_detection import TextDetector
from ner_v1.constant import FIRST_NAME, MIDDLE_NAME, LAST_NAME


class NameDetector(object):
    def __init__(self, entity_name):
        self.entity_name = entity_name
        self.text = ''
        self.names = []
        self.tagged_text = ''
        self.processed_text = ''
        self.original_name_text = []
        self.text_detection_object = TextDetector(entity_name=entity_name)

    def text_detection_name(self):
        """
        Makes a call to TextDetection
        :return: list of names detected in TextDetection
        """
        return self.text_detection_object.detect_entity(text=self.text)

    def detect_entity(self, text):
        """
        Takes text and and returns names
        :param text: The original text
            Example:
                text = My name is yash modi
        :return:
        [{first_name: "yash", middle_name: None, last_name: "modi"}], [ "yash modi"]

        """
        self.text = text
        self.tagged_text=self.text
        text_detection_result = self.text_detection_name()
        replaced_text = self.replace_detected_text(text_detection_result)

        return self.detect_name_entity(replaced_text)

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

    @staticmethod
    def detect_name_entity(replaced_text):
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
            original_text.append(" ".join(name))
            name_entity_value = {FIRST_NAME: name[0], MIDDLE_NAME: None, LAST_NAME: None}

            if len(name) > 1:
                name_entity_value[LAST_NAME] = name[-1]
                name_entity_value[MIDDLE_NAME] = " ".join(name[1:-1]) or None
            entity_value.append(name_entity_value)

        return entity_value, original_text
