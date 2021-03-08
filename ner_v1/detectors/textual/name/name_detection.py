# coding=utf-8
from __future__ import absolute_import
import re
import string

from lib.nlp.const import nltk_tokenizer
from lib.nlp.pos import POS
from lib.nlp.spacy_utils import spacy_utils
from language_utilities.constant import (ENGLISH_LANG, INDIC_LANGUAGES_SET, EUROPEAN_LANGUAGES_SET)
from ner_v1.constant import DATASTORE_VERIFIED, MODEL_VERIFIED
from ner_v1.constant import EMOJI_RANGES, FIRST_NAME, MIDDLE_NAME, LAST_NAME
from ner_v1.detectors.textual.name.lang_constants import (INDIC_BADWORDS, INDIC_QUESTIONWORDS,
                                                          INDIC_STOPWORDS, NAME_VARIATIONS, INDIC_UNICODE_RANGE,
                                                          COMMON_INDIC_WORDS_OCCURRING_WITH_NAME)
from six.moves import range


# TODO: Refactor this module for readability and useability. Remove any hacks

class NameDetector(object):
    """
    NameDetector class detects names from text. This class uses TextDetector
    to detect the entity values. This class also contains templates and pos_tagger to capture
    names which are missed by TextDetector.

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected person_name entities would be replaced with
                     on calling detect_entity()
        tagged_text: string with city entities replaced with tag defined by entity_name
        processed_text: string with detected time entities removed
        bot_message: previous message
    """

    def __init__(self, entity_name, language=ENGLISH_LANG):
        """
        Initializes a NameDetector object with given entity_name

        Args:
            entity_name: A string by which the detected substrings that correspond to text entities would be replaced
                         with on calling detect_entity()
        """
        self.entity_name = entity_name
        self.language = language
        self.text = ''
        self.names = []
        self.tagged_text = ''
        self.processed_text = ''
        self.original_name_text = []
        self.tag = '_' + entity_name + '_'

        self.bot_message = None

    @staticmethod
    def get_format_name(name_tokens, text):
        """
        Takes input as name_list which contains the names detected.
        It separates the first, middle and last names.
        It returns two lists:
        1.Containing the names separated into first, middle and last name.
        2.The original text.

        Args:
            name_tokens (list): List of tokens in the name. e.g. ['yash', 'doshi']

        Returns:
            (list, list): tuple containing
                list: list of dictionaries, one for each detected name
                list: list of str, the original text span for each detected name

        Examples:
            >>> NameDetector.get_format_name(['yash', 'p.', 'm.', 'doshi'], 'my name is yash p. m. doshi')
            ([{first_name: 'yash', middle_name: 'p. m.', last_name: 'doshi'}],
            ['yash p. m. doshi'])
        """
        entity_value = []
        original_text = []
        if not name_tokens:
            return entity_value, original_text

        name_text = " ".join(name_tokens)
        first_name = name_tokens[0]
        middle_name = None
        last_name = None

        if name_text in text:
            if len(name_tokens) > 1:
                last_name = name_tokens[-1]
                middle_name = " ".join(name_tokens[1:-1]) or None

            entity_value.append({
                FIRST_NAME: first_name,
                MIDDLE_NAME: middle_name,
                LAST_NAME: last_name,
                DATASTORE_VERIFIED: False,
                MODEL_VERIFIED: False,
            })
            original_text.append(name_text)
        return entity_value, original_text

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

        if self.language in EUROPEAN_LANGUAGES_SET:
            tagged_names = spacy_utils.tag(text=text.strip(), language=self.language)
        else:
            pos_tagger_object = POS()
            name_tokens = text.split()
            # Passing empty tokens to tag will cause IndexError
            tagged_names = pos_tagger_object.tag(name_tokens)

        is_question = [word[0] for word in tagged_names if word[1].startswith('WR') or
                       word[1].startswith('WP') or word[1].startswith('CD')]
        if is_question:
            return entity_value, original_text

        if len(tagged_names) < 4 and self.bot_message:
            if self.language in EUROPEAN_LANGUAGES_SET:
                pos_words = [word[0] for word in tagged_names if word[1].startswith('NOUN')
                             or word[1].startswith('ADJ') or word[1].startswith('PROPN')]
            else:
                pos_words = [word[0] for word in tagged_names if word[1].startswith('NN')
                             or word[1].startswith('JJ')]

            if pos_words:
                entity_value, original_text = self.get_format_name(pos_words, self.text)

        return entity_value, original_text

    def detect_entity(self, text, bot_message=None, predetected_values=None, **kwargs):
        """
        Takes text as input and  returns two lists
        1.entity_value in the form of first, middle and last names
        2.original text.
        Args:
           text(string): the original text
           bot_message(string): previous bot message
           predetected_values(list of str): detected values from prior detection

           Example:
                    text=my name is yash doshi
        Returns:
                [{first_name: "yash", middle_name: None, last_name: "modi"}], [ yash modi"]
        """

        self.text = text
        self.tagged_text = self.text
        self.bot_message = bot_message

        entity_value, original_text = ([], [])

        if not predetected_values:
            if self.bot_message:
                if not self.context_check_botmessage(self.bot_message):
                    return [], []
            if self.language in EUROPEAN_LANGUAGES_SET | {ENGLISH_LANG}:
                entity_value, original_text = self.detect_english_name()
            elif self.language in INDIC_LANGUAGES_SET:
                entity_value, original_text = self.detect_indic_name()

            for entity_value_dict in entity_value:
                entity_value_dict.update({DATASTORE_VERIFIED: True, MODEL_VERIFIED: False})

        else:
            replaced_text = self.replace_predetected_text(predetected_values, text=text)
            entity_value, original_text = self.detect_person_name_entity(replaced_text)

            for entity_value_dict in entity_value:
                entity_value_dict.update({DATASTORE_VERIFIED: False, MODEL_VERIFIED: True})

        self._update_processed_text(person_name_list=original_text)

        return entity_value, original_text

    def detect_english_name(self, text=None):
        """
        This method is used to detect English names from the provided text
        Returns:
            detect_text_lists (tuple): two dimensional tuple
            1. entity_value (list): representing the entity values of names
            2. original_text (list): representing the original text detected

        Example:

            text=my name is yash doshi
            detect_entity_english()
            >>[{first_name: "yash", middle_name: None, last_name: "modi"}], [ yash modi"]
        """
        if text is None:
            text = self.text
        entity_value, original_text = self.get_name_using_pos_tagger(text)
        return entity_value, original_text

    def detect_indic_name(self):
        """
        This method is used to detect Hindi names from the provided text

        Returns:
            detect_text_lists (tuple): two dimensional tuple
            1. entity_value (list): representing the entity values of names
            2. original_text (list): representing the original text detected

        Examples:
            text = u'प्रतिक श्रीदत्त जयराओ'
            detect_entity_hindi(text=text)
            >> [{first_name: u"प्रतिक", middle_name: u"श्रीदत्त", last_name: u"जयराओ"}], [ u'प्रतिक श्रीदत्त जयराओ']

        """
        if self.detect_abusive_phrases_indic(text=self.text) or self.detect_question_indic(text=self.text):
            return [], []

        text = self.remove_emojis(text=self.text)
        text_before_hindi_regex_operations = text
        regex = re.compile(u'[^{unicode_range}\\s]+'.format(unicode_range=INDIC_UNICODE_RANGE[self.language]), re.U)
        text = regex.sub(string=text, repl='')

        entity_value, original_text = self.get_indic_names_without_regex(text=text)
        # Further check for name, if it might have been written in latin script.
        if not entity_value:
            english_present_regex = re.compile(u'[a-zA-Z]+', re.U)
            if english_present_regex.search(text_before_hindi_regex_operations):
                remove_everything_except_english = re.compile(u'[^a-zA-Z\\s]+', re.U)
                text_only_english = remove_everything_except_english.sub(
                    string=text_before_hindi_regex_operations, repl='')
                entity_value, original_text = self.detect_english_name(text=text_only_english.strip())

        return entity_value, original_text

    def replace_predetected_text(self, predetected_values, text):
        """
        Replace detected names from the text according to replace_detected_text.
        Separate method for replacing predetected_values because it these results are not at token level.
        For example -
            text = "my name is yash doshi"
            predetected_values = ["yash doshi"]
            while, text_detection_original_texts = ["yash", "doshi"]


        Args:
            predetected_values(list): list containing predetected_values
            text(str): original to run detection on

        Returns:
            replaced_text(str): text with marked tokens

        Example:
            >> text = "my name is yash doshi"
            >> predetected_values = ["yash doshi"]
            >> replace_predetected_text(predetected_values, text)
            'my name is _yash_ _doshi_'

        """
        if self.language == ENGLISH_LANG:
            replaced_original_text_tokens = nltk_tokenizer.tokenize(text.lower())
            replaced_text_tokens = []
            for index, token in enumerate(replaced_original_text_tokens):
                # Fix to handle tokenizer error for tokens with trailing `.`. For eg.
                # >> text = "my name is v.k. singh"
                # >> tokens = tokenize(text)
                # >> tokens
                #    ["my", "name", "is", "v.k", ".", "singh"]
                # this extra `.` token causes problem while training.
                if token == "." and 0 < index < len(replaced_original_text_tokens) - 1 \
                        and replaced_text_tokens[-1] + "." in text.lower():
                    replaced_text_tokens[-1] = replaced_text_tokens[-1] + "."
                else:
                    # Fix to handle examples like `miami,21st street`
                    # where tokenizer gives ["miami,", "21st", "street"].
                    # This causes problems while tagging entities according indices.
                    # For eg is miami is an entity and its indices are (0,5) then due to this extra `,` tagging will be
                    # problem because now length of token will become 6 not 5.
                    _token = token.strip('!"#$%&\'()*+,-/:;<=>?@[\\]^_`{|}~')
                    if not _token:
                        _token = token
                    replaced_text_tokens.append(_token)
        else:
            replaced_text_tokens = text.lower().strip().split()

        for name in predetected_values:
            name_tokens = name.split()
            for token in name_tokens:
                for j in range(len(replaced_text_tokens)):
                    replaced_text_tokens[j] = replaced_text_tokens[j].replace(token, "_" + token + "_")

        return replaced_text_tokens

    def replace_detected_text(self, text_detection_result, text):
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
                    ['my', 'name', 'is', '_yash_', '_doshi_']

        """
        replaced_text_tokens = []
        if self.language == ENGLISH_LANG:
            replaced_text_tokens = nltk_tokenizer.tokenize(text.lower())
        elif self.language in EUROPEAN_LANGUAGES_SET:
            replaced_text_tokens = spacy_utils.tokenize(text.lower())
        elif self.language in INDIC_LANGUAGES_SET:
            replaced_text_tokens = text.lower().strip().split()

        for detected_original_text in (text_detection_result[1]):
            for j in range(len(replaced_text_tokens)):
                replaced_text_tokens[j] = replaced_text_tokens[j].replace(
                    detected_original_text, "_" + detected_original_text + "_")

        return replaced_text_tokens

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
            name_entity_value, original_text_value = self.get_format_name(name, self.text)
            original_text.extend(original_text_value)
            entity_value.extend(name_entity_value)

        return entity_value, original_text

    def context_check_botmessage(self, botmessage):
        """
        Checks if previous botmessage conatins name as a keyword or not

        Args:
            botmessage: it consists of the previous botmessage

        Example: what is your name ?

        Returns:
            True
        """

        regex_pattern = re.compile(r'[{}]+'.format(re.escape(string.punctuation)))
        botmessage = regex_pattern.sub(r'', botmessage)

        botmessage = " " + botmessage.lower().strip() + " "
        for variant in NAME_VARIATIONS.get(self.language, []):
            if " " + variant + " " in botmessage:
                return True
        return False

    def get_indic_names_without_regex(self, text):
        """
        This method is used to get detect hindi names without any regex pattern (This method is called only if
        detection from regex patterns fails)
        This method removes common hindi words ocurring in context of name and hindi stop words
        COMMON_HINDI_WORDS_OCCURING_WITH_NAME set of hindi words ocurring in context of name
        Args:
            text (str): the text from which hindi text has to be detected
        Returns:
            person_name (tuple): two dimensional tuple
            1. entity_value (list): representing the entity values of names
            2. original_text (list): representing the original text detected
        Example:
            text = u'प्रतिक श्रीदत्त जयराओ'
            get_hindi_names_without_regex(text=text)
            >> [{first_name: u"प्रतिक", middle_name: u"श्रीदत्त", last_name: u"जयराओ"}], [ u'प्रतिक श्रीदत्त जयराओ']
        """
        text_original = text
        text = self.replace_stopwords_hindi(text)
        text = " ".join(
            [word for word in text.split(" ") if word not in COMMON_INDIC_WORDS_OCCURRING_WITH_NAME[self.language]])

        if not text.strip():
            return [], []

        original_text_list = text.strip().split()

        if len(original_text_list) > 4 or not ' '.join(original_text_list) in text_original:
            original_text_list = []
        replaced_text = self.replace_detected_text((original_text_list, original_text_list), text=text)
        return self.detect_person_name_entity(replaced_text=replaced_text)

    def replace_stopwords_hindi(self, text):
        """
        This method is used to replace hindi stop words from the text
        Args:
            text (str): The text from which hindi stop words have to be removed

        Returns:
            clean_text (str): text from which hindi stop words have been removed
        """
        split_list = text.split(" ")
        split_list = [word for word in split_list if word not in INDIC_STOPWORDS[self.language]]
        if split_list:
            return " ".join(split_list)

        return ""

    def detect_abusive_phrases_indic(self, text):
        """
        This method is used to check for hindi abuses in the sentence
        Args:
            text (str): text in which abuses have to be checked

        Returns:
            status (bool): returns if the text consists of abuses
        """
        text = ' ' + text + ' '
        for abuse in INDIC_BADWORDS[self.language]:
            if ' ' + abuse + ' ' in text:
                return True
        return False

    def remove_emojis(self, text):
        """
        This method is used to remove emojis from the given text
        Args:
            text (str): the text from which the emojis have to be removed
        Returns:
            text (str): text with emojis replaced with ''
        """
        emoji_pattern = re.compile(u'[{0}]+'.format(''.join(list(EMOJI_RANGES.values()))), re.UNICODE)
        text = emoji_pattern.sub(repl='', string=text)
        return text

    def detect_question_indic(self, text):
        """
        This method is used to detect if the given text has a hindi question present in it
        Args:
            text (str): the text for which the question check has to be run

        Returns:
            status (bool): returns if the text has a question in it
        """
        for word in text.split():
            if word in INDIC_QUESTIONWORDS[self.language]:
                return True
        return False

    def _update_processed_text(self, person_name_list):
        """
        Replaces detected date with tag generated from entity_name used to initialize the object with

        A final string with all dates replaced will be stored in object's tagged_text attribute
        A string with all dates removed will be stored in object's processed_text attribute

        Args:
            person_name_list (list): list of substrings of original text to be replaced with tag
                                       created from entity_name
        """
        for detected_text in person_name_list:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')
