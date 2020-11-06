import six
from lib.singleton import Singleton
from language_utilities.constant import ENGLISH_LANG, SPANISH_LANG, DUTCH_LANG, GERMAN_LANG, FRENCH_LANG

import spacy


class SpacyTagger(six.with_metaclass(Singleton, object)):
    def __init__(self):
        self.spacy_language_to_model = {
            ENGLISH_LANG: {'name': 'en_core_web_sm', 'model': None},
            GERMAN_LANG: {'name': 'de_core_news_sm', 'model': None},
            FRENCH_LANG: {'name': 'fr_core_news_sm', 'model': None},
            DUTCH_LANG: {'name': 'nl_core_news_sm', 'model': None},
            SPANISH_LANG: {'name': 'es_core_news_sm', 'model': None}
        }

    def tag(self, text, language):
        spacy_model_name = self.spacy_language_to_model[language]['name']
        nlp = self.spacy_language_to_model[language]['model']
        if not nlp:
            nlp = spacy.load(spacy_model_name, disable=['parser', 'ner'])
        spacy_doc = nlp(text)
        tokens = []
        for spacy_token in spacy_doc:
            token = (spacy_token.text, spacy_token.tag)
            tokens.append(token)
        return tokens
