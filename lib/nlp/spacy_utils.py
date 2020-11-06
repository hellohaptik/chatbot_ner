import six
from lib.singleton import Singleton
from language_utilities.constant import ENGLISH_LANG, SPANISH_LANG, DUTCH_LANG, GERMAN_LANG, FRENCH_LANG

import spacy
from spacy.tokenizer import Tokenizer


class SpacyUtils(six.with_metaclass(Singleton, object)):
    def __init__(self):
        self.spacy_language_to_model = {
            ENGLISH_LANG: {'name': 'en_core_web_sm', 'model': None},
            GERMAN_LANG: {'name': 'de_core_news_sm', 'model': None},
            FRENCH_LANG: {'name': 'fr_core_news_sm', 'model': None},
            DUTCH_LANG: {'name': 'nl_core_news_sm', 'model': None},
            SPANISH_LANG: {'name': 'es_core_news_sm', 'model': None}
        }

        self.tokenizers = {
            ENGLISH_LANG: None,
            GERMAN_LANG: None,
            FRENCH_LANG: None,
            DUTCH_LANG: None,
            SPANISH_LANG: None
        }

    def tag(self, text, language):
        spacy_model_name = self.spacy_language_to_model[language]['name']
        nlp = self.spacy_language_to_model[language]['model']
        if not nlp:
            nlp = spacy.load(spacy_model_name, disable=['parser', 'ner'])
            self.spacy_language_to_model[language]['model'] = nlp
        spacy_doc = nlp(text)
        tokens = []
        for spacy_token in spacy_doc:
            token = (spacy_token.text, spacy_token.tag_)
            tokens.append(token)
        return tokens

    def tokenize(self, text, language):
        tokenizer = self.tokenizers[language]

        if not tokenizer:
            spacy_model_name = self.spacy_language_to_model[language]['name']
            nlp = self.spacy_language_to_model[language]['model']
            if not nlp:
                nlp = spacy.load(spacy_model_name, disable=['parser', 'ner'])
                self.spacy_language_to_model[language]['model'] = nlp
            tokenizer = Tokenizer(nlp.vocab)
            self.tokenizers[language] = tokenizer

        tokens = []
        for token in tokenizer(text):
            tokens.append(token.text)
        return tokens


spacy_utils = SpacyUtils()
