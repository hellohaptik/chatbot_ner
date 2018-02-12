import re


class RegexDetector(object):
    def __init__(self, entity_name, regex):
        self.entity_name = entity_name
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.regex = regex
        self.original_regex_text = []
        self.tag = '__' + self.entity_name + '__'

    def detect_entity(self, text):
        """
        Take text and returns email details
        :param text:
        :param form:
        :return: tuple (list of email , original text)
        """
        self.text = ' ' + text + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        regex_list, original_list = self.detect_regex()
        return regex_list, original_list

    def detect_regex(self):
        original_list = []
        regex_list = []
        try:
            compiled_regex = re.compile(self.regex)
        except ValueError:
            return "Incorrect regex expression"
        regex_list.append(compiled_regex.findall(self.text)[0])
        original_list.extend(regex_list)
        self.update_processed_text(regex_list)
        return regex_list, original_list

    def update_processed_text(self, regex_list):
        """
        This function updates text by replacing already detected email
        :return:
        """
        for detected_text in regex_list:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')


