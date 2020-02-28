from __future__ import absolute_import
import nltk

# constants
from lib.singleton import Singleton
import six

DEFAULT_NLTK_TAGGER_PATH = 'taggers/maxent_treebank_pos_tagger/english.pickle'
NLTK_MAXENT_TAGGER = 'NLTK_MAXENT_TAGGER'
NLTK_AP_TAGGER = 'NLTK_AP_TAGGER'


class APTaggerUtils(object):
    tagger = nltk.PerceptronTagger()

    def tag(self, tokens, tagset=None):
        tagged_tokens = APTaggerUtils.tagger.tag(tokens)
        if tagset:
            tagged_tokens = [(token, nltk.map_tag('en-ptb', tagset, tag)) for (token, tag) in tagged_tokens]
        return tagged_tokens


class POS(six.with_metaclass(Singleton, object)):

    def __init__(self, tagger_selected=NLTK_AP_TAGGER, tagger=None):
        self.tagger_dict = {
            NLTK_MAXENT_TAGGER: self.__nltk_maxent_tagger,
            NLTK_AP_TAGGER: self.__nltk_ap_tagger,
        }
        self.tagger = tagger
        self.path = None
        self.tagger_selected = tagger_selected

        if not self.tagger:
            self.tagger = self.tagger_dict[self.tagger_selected]()

    def set_model_path(self, path):
        self.path = path

    def __nltk_maxent_tagger(self):
        if not self.path:
            self.path = DEFAULT_NLTK_TAGGER_PATH
        return nltk.data.load(self.path).tag

    def __nltk_ap_tagger(self):
        ap_tagger = APTaggerUtils()
        return ap_tagger

    def get_tagger(self):
        return self.tagger

    def tag(self, tokens):
        return self.tagger.tag(tokens)
