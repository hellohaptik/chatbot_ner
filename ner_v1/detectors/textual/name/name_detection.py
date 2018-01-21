from lib.nlp.tokenizer import Tokenizer
from ner_v1.detectors.textual.text.text_detection import TextDetector


class NameDetector(object):
    def __init__(self, entity_name):
        self.entity_name = entity_name
        self.text = ''
        self.names=[]
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
        :return:
        [{ entity_value : { first_name: "", middle_name: "", last_name: "" }
            original_text: ""
            }]
        """
        self.text = text
        self.tagged_text=self.text
        text_detection_result = self.text_detection_name()
        replaced_text = self.replace_detected_text(text_detection_result)

        return self.creating_name_dictionary(replaced_text)

    def replace_detected_text(self, text_detection_result):
        """
        Replaces the detected names by _ _
        :param text_detection_result: list of detected names from TextDetection
        :return: tokenized list with detected names replaced by _ _
        """
        replaced_text = Tokenizer().tokenize(self.text.lower())
        for i in (text_detection_result[1]):
            for j in range(len(replaced_text)):
                replaced_text[j] = replaced_text[j].replace(i, "_" + i + "_")

        return replaced_text

    def creating_name_dictionary(self, replaced_text):
        """
        Forms a dictionary of the names
        :param replaced_text:
        :return: names detected
        [{ entity_value : { first_name: "", middle_name: "", last_name: "" }
            original_text: ""
            }]
        """
        results = []
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
            name_dict = {'original_text': " ".join(name),
                         'entity_value': {"first_name": name[0], "middle_name": None, "last_name": None}}

            if len(name) > 1:
                name_dict['entity_value']['last_name'] = name[-1]
                name_dict['entity_value']['middle_name'] = " ".join(name[1:-1]) or None

            results.append(name_dict)

        return results
