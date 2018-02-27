import re
from chatbot_ner.config import ner_logger


class RegexDetector(object):
    """
    RegexDetector is used to detect text from the inbound message which abide by the specified regex.
    """
    def __init__(self, entity_name, regex):
        """

        Args:
            entity_name:
            regex:
        Attributes:
             self.entity_name (str) : holds the entity name
             self.text (str) : holds the original text
             self.tagged_text (str) : holds the detected entities replaced by self.tag
             self.processed_text (str) : holds the text left to be processed

        """
        self.entity_name = entity_name
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.regex = regex
        self.tag = '__' + self.entity_name + '__'

    def detect_entity(self, text):
        """
        Takes input as text and returns text detected for the specified regex.
        Args:
            text (str) : Contains the message sent by the user.

        Returns:
            (regex_list, original_list) (tuple):
            regex_list (list) : list of detected text for the specified text
            original_list (list) : list of original text provided by the user
        Example:
            self.regex = r'\d+'
            self.text = 'aman123"

            detect_entity()
            >> (['123'], ['123'])
        """
        self.text = text.strip()
        self.processed_text = self.text
        self.tagged_text = self.text
        regex_list, original_list = self.detect_regex()
        return regex_list, original_list

    def detect_regex(self):
        """
        Detects text based on the aforementioned regex
        Raises an error for an invalid regex
        Returns:
                (regex_list, original_list) (tuple):
                regex_list (list) : list of detected text for the specified text
                original_list (list) : list of original text provided by the user
        Example:
            self.regex = r'\d+'
            self.text = 'aman123"

            detect_entity()
            >> (['123'], ['123'])
        """
        original_list = []
        regex_list = []
        try:
            compiled_regex = re.compile(self.regex)
            regex_list.append(compiled_regex.findall(self.text)[0])
            original_list.extend(regex_list)
            self.update_processed_text(regex_list)
        except Exception as e:
            ner_logger.debug("Exception detect regex: %s" % e.message)
        return regex_list, original_list

    def update_processed_text(self, regex_list):
        """
        This function updates text by replacing already detected email
        :return:
        """
        for detected_text in regex_list:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')


