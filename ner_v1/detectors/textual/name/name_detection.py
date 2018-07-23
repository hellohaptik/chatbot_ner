import re

from lib.nlp.const import nltk_tokenizer
from lib.nlp.pos import *
from ner_v1.constant import FIRST_NAME, MIDDLE_NAME, LAST_NAME
from ner_v1.detectors.textual.text.text_detection import TextDetector


class NameDetector(object):
    """
    NameDetector class detects names from text. This class uses TextDetector
    to detect the entity values. This class also contains templates and pos_tagger to capture
    names which are missed by TextDetector.

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected person_name entities would be replaced with on calling detect_entity()
        tagged_text: string with city entities replaced with tag defined by entity_name
        processed_text: string with detected time entities removed
        text_detection_object: the object which is used to call the TextDetector
    """

    def __init__(self, entity_name):
        """
        Initializes a NameDetector object with given entity_name

        Args:
            entity_name: A string by which the detected substrings that correspond to text entities would be replaced
                         with on calling detect_entity()
        """
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
        Takes input as name_list which contains the names detected.
        It separates the first, middle and last names.
        It returns two lists:
        1.Containing the names separated into first, middle and last name.
        2.The original text.

        Args:
            name_list (list): List of names detected
            Example:
                 ['yash', 'doshi']

        Returns:
        ({first_name: "yash", middle_name: None, last_name: "modi"}, "yash modi")
        """

        original_text = " ".join(name_list)

        first_name = name_list[0]
        middle_name = None
        last_name = None

        if len(name_list) > 1:
            last_name = name_list[-1]
            middle_name = " ".join(name_list[1:-1]) or None

        entity_value = {FIRST_NAME: first_name, MIDDLE_NAME: middle_name, LAST_NAME: last_name}

        return [entity_value], [original_text]

    def text_detection_name(self):
        """
        Makes a call to TextDetection and return the person_name detected from the elastic search.
        Returns:
           Tuple with list of names detected in TextDetection in the form of variants detected and original_text

         Example : my name is yash doshi

         ([u'dosh', u'yash'], ['doshi', 'yash'])
        """

        return self.text_detection_object.detect_entity(text=self.text)

    def get_name_using_pos_tagger(self, text):
        """
        First checks if the text contains cardinals or interrogation.
        Then passes the text through templates.
        Then returns words which are nouns or adjectives
        Args:
            text (string): The text obtained from the user.

            Example text= My name is yash modi
        Returns:
            [{first_name: "yash", middle_name: None, last_name: "modi"}], ["yash modi"]
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
                       word[1].startswith('WP') or word[1].startswith('CD')]
        if is_question:
            return entity_value, original_text

        if pattern1_match:
            entity_value, original_text = self.get_format_name(pattern1_match[0][1].split())

        elif pattern2_match:
            entity_value, original_text = self.get_format_name(pattern2_match[0].split())

        elif len(name_tokens) < 4:
            pos_words = [word[0] for word in tagged_names if word[1].startswith('NN') or
                         word[1].startswith('JJ')]
            if pos_words:
                entity_value, original_text = self.get_format_name(pos_words)

        return entity_value, original_text

    def detect_entity(self, text, bot_message=None):
        """
        Takes text as input and  returns two lists
        1.entity_value in the form of first, middle and last names
        2.original text.
        Args:
           text(string): the original text
           bot_message(string): previous bot message

           Example:
                    text=my name is yash doshi
       Returns:
                [{first_name: "yash", middle_name: None, last_name: "modi"}], [ yash modi"]
        """

        if bot_message:
            if not self.context_check_botmessage(bot_message):
                return [], []
        self.text = text
        self.tagged_text = self.text
        text_detection_result = self.text_detection_name()
        replaced_text = self.replace_detected_text(text_detection_result)
        entity_value, original_text = self.detect_person_name_entity(replaced_text)

        if not entity_value:
            entity_value, original_text = self.get_name_using_pos_tagger(text)

        return entity_value, original_text

    def replace_detected_text(self, text_detection_result):
        """
        Replaces the detected name from text_detection_result by _<name>_
        Args:
            text_detection_result: tuple of detected names from TextDetection
            consisting of two lists
            1.The variants detected
            2.The original text
            ([u'dosh', u'yash'], ['doshi', 'yash'])

            Example:
                    text_detection_result= ([u'dosh', u'yash'], ['doshi', 'yash'])
            Returns:
                    ['my', 'name', 'is', 'yash', 'doshi']

        """

        replaced_text = nltk_tokenizer.tokenize(self.text.lower())
        for detected_original_text in (text_detection_result[1]):
            for j in range(len(replaced_text)):
                replaced_text[j] = replaced_text[j].replace(detected_original_text, "_" + detected_original_text + "_")

        return replaced_text

    def detect_person_name_entity(self, replaced_text):
        """
        Separates the detected names into first, middle and last names.
        Returns in form of two lists entity_value and original_text
        Args:
            replaced_text: text in which names detected from TextDetector are replaced by
        _<name>_
        Example:
                replaced_text = My name is _yash_ _modi_
        Returns:
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
        Checks if previous botmessage conatins name as a keyword or not
        Args:
            botmessage: it consists of the previous botmessage
            Example: what is your name ?
        Returns:
            True
        """

        if "name" in botmessage:
            return True
        return False
