import re

from lib.nlp.pos import POS
from ner_v1.constant import FIRST_NAME, MIDDLE_NAME, LAST_NAME
from ner_v1.detectors.textual.text.text_detection import TextDetector


class NameDetector(object):
    """
    NameDetector class detects names from text. This class uses TextDetector
    to detect the entity values. This class also contains templates and pos_tagger to capture
    names which are missed by TextDetector.

    Attributes:
        text (str): string to extract entities from
        entity_name (str): name of the entity to pass on to TextDetector. The datastore would have
                           dictionary of person names under this name
        tagged_text (str): string with person name entities replaced with tag defined by entity_name
        processed_text (str): string with detected time entities removed
        text_detector (TextDetector): TextDetector object
        detected_name_values (list): list containing formatted values for all names detected
        detected_name_original_texts (list): list containing spans of texts corresponding to values
                                             in detected_name_values
        tag (str): entity_name prepended and appended with '__'
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
        self.tagged_text = ''
        self.processed_text = ''
        self.detected_name_values = []
        self.detected_name_original_texts = []
        self.text_detector = TextDetector(entity_name=entity_name)
        self.tag = '__' + self.entity_name + '__'

    def detect_entity(self, text, bot_message=None):
        """
        Detect names using patterns and text detection

        Args:
           text (str): text to detect names from
           bot_message (str, optional): previous bot message in context.

        Returns:
            tuple:
                list of dict: containing first_name, middle_name and last_name
                list of str: original text corresponding to the found value

        Example:
            In: text = "my name is yash doshi"
            Out: [{first_name: "yash", middle_name: None, last_name: "modi"}], [ yash modi"]
        """
        self.text = text
        self.processed_text = self.text.lower()
        self.tagged_text = self.processed_text

        if bot_message:
            if not self._check_name_patterns_botmessage(bot_message):
                return [], []

        entity_values, original_texts = self._detect_name_with_text_detector()
        self.detected_name_values, self.detected_name_original_texts = entity_values, original_texts
        self._update_processed_text(original_texts)

        if not entity_values:
            entity_values, original_texts = self._detect_name_with_patterns_pos_tagger()
            self.detected_name_values, self.detected_name_original_texts = entity_values, original_texts
            self._update_processed_text(original_texts)

        return self.detected_name_values, self.detected_name_original_texts

    def _detect_name_with_text_detector(self):
        """
        Use TextDetector to find names in the given text using a long list of common names

        Returns:
            tuple:
                list of dict: containing first_name, middle_name and last_name
                list of str: original text corresponding to the found value

        Example:
            In: "my name is yash doshi"
            Out: [{first_name: "yash", middle_name: None, last_name: "modi"}], ["yash modi"]

        """
        entity_values, original_texts = [], []

        entity_value_list, original_text_list = self.text_detector.detect_entity(text=self.processed_text)
        detected_tokens = set(original_text_list)
        tokens = self.processed_text.split()
        start = 0
        while start < len(tokens):
            if tokens[start] in detected_tokens:
                end = start
                while end < len(tokens) and tokens[end] in detected_tokens:
                    end += 1
                entity_values.append(self.format_name_value(tokens[start:end]))
                original_texts.append(' '.join(tokens[start:end]))
                start = end
        return entity_values, original_texts

    def _detect_name_with_patterns_pos_tagger(self):
        """
        Use POS Tags and regex patterns to extract words that potentially be names

        if the text contains cardinals or interrogation, no entities are detected on such text
        Otherwise patterns are used to extract tokens that can be names. Pattern is formed of prefixes commonly
        used to introduce names

        If pattern matching fails to extract keywords, POS tags are used to extract Noun and Adjective words

        Returns:
            tuple:
                list of dict: containing first_name, middle_name and last_name
                list of str: original text corresponding to the found value

        Example:
             In: text = 'My name is yash modi'
             Out: [{first_name: "yash", middle_name: None, last_name: "modi"}], ["yash modi"]
        """
        entity_values, original_texts = [], []

        pos_tagger = POS()
        tokens = self.processed_text.split()
        tagged_tokens = pos_tagger.tag(tokens)

        is_question = [word[0] for word in tagged_tokens if word[1].startswith('WR') or
                       word[1].startswith('WP') or word[1].startswith('CD')]

        if is_question:
            return entity_values, original_texts

        pattern = re.compile(r"\b(?:name\s+is|name's|"
                             r"(?:me is|i\s+am|i'm)(?:\s+called)?|"
                             r"call\s+me|myself)"
                             r"\s+(\w+(?:\s+\w+){0,2})\b", re.UNICODE | re.IGNORECASE)
        # the above pattern can have false positives is the text does not end with name
        # because we greedily extract 3 tokens after introduction prefixes
        # It can also have false negatives if someone has name with more than three tokens or designations are involved

        pattern_matches = pattern.findall(self.processed_text)

        for pattern_match in pattern_matches:
            entity_value, original_text = self.format_name_value(pattern_match.split())
            entity_values.append(entity_value)
            original_texts.append(original_text)

        if not entity_values and len(tokens) < 4:  # Condition too strict
            # TODO: A better approach will be to find spans of NN* and JJ* in the text and tag them
            pos_words = [word[0] for word in tagged_tokens if word[1].startswith('NN') or
                         word[1].startswith('JJ')]  # this is not guaranteed to be a span
            if pos_words:
                entity_value, original_text = self.format_name_value(pos_words)
                entity_values.append(entity_value)
                original_texts.append(original_text)

        return entity_values, original_texts

    @staticmethod
    def format_name_value(name_parts_list):
        """
        Convert name parts list to a dict of first, middle and last names

        Args:
            name_parts_list (list): List of names detected
            Example:
                 ['yash', 'doshi']

        Returns:
            tuple:
                dict: containing first_name, middle_name and last_name
                str: original text corresponding to the found value

        E.g. output ({first_name: "yash", middle_name: None, last_name: "modi"}, "yash modi")
        """

        original_text = ' '.join(name_parts_list)

        first_name = name_parts_list[0]
        middle_name = None
        last_name = None

        if len(name_parts_list) > 1:
            last_name = name_parts_list[-1]
            middle_name = " ".join(name_parts_list[1:-1]) or None

        entity_value = {FIRST_NAME: first_name, MIDDLE_NAME: middle_name, LAST_NAME: last_name}

        return entity_value, original_text

    @staticmethod
    def _check_name_patterns_botmessage(botmessage):
        """
        Check if previous botmessage contains some patterns to trigger name detection ot not

        Args:
            botmessage: it consists of the previous botmessage

        Returns:
            bool: if bot message passes conditions to trigger detection

        """

        return "name" in botmessage

    def _update_processed_text(self, original_texts):
        """
        Replace detected names with tag generated from entity_name used to initialize the object with

        Args:
            original_texts(list of str): list of substrings of original text to be replaced with tag
                                         created from entity_name
        """
        for detected_text in original_texts:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')
