from __future__ import absolute_import
from nltk.stem.porter import PorterStemmer

# constants
from lib.singleton import Singleton
import six

PORTER_STEMMER = 'PORTER_STEMMER'


class Stemmer(six.with_metaclass(Singleton, object)):
    """
    Detects the stemmer of a word.
    Its a wrapper class which can be used to call respective stemmer library. Currently, It has been integrated
    with PorterStemmer from nltk library but can be integrated with other libraries.
    In this class we have defined two functionality that can be used by the user to get the stem of the word
        1. Given a word it will return its stem
        2. Given a list of tokens it will return list of stems

    For Example:
        stemmer = Stemmer()
        output = stemmer.stem_word('beautiful')
        print output
        >> beauti

        stemmer = Stemmer()
        output = stemmer.stem_tokens(['beautiful','playing'])
        print output
        >> [u'beauti', u'play']


    Attributes:
        stemmer_selected: Stemmer which needs to be selected for processing
        stemmer_dict: It is a Dictionary where key is the stemmer type and value is the function that needs
        to be called to get its object
        stemmer: Object of the stemmer obtained from external library example, PorterStemmer

    """

    def __init__(self, stemmer_selected=PORTER_STEMMER):
        """Initializes a Stemmer object

        Args:
            stemmer_selected: Stemmer which needs to be selected for processing
        """

        self.stemmer = None
        self.stemmer_selected = stemmer_selected
        self.stemmer_dict = {
            PORTER_STEMMER: self.__porter_stemmer
        }
        self.stemmer_dict[self.stemmer_selected]()

    def stem_word(self, word):
        """Returns the stem of a word
            output = stemmer.stem_word('beautiful')
            print output
            >> beauti

        Args:
            word: string to extract to extract its stem

        Returns:
            The stem of a word
            For example:

        """
        if PORTER_STEMMER == self.stemmer_selected:
            return self.stemmer.stem(word.lower())

    def stem_tokens(self, tokens):
        """Returns the list of stem for list of tokens

        Args:
            tokens: list of strings to extract its stem

        Returns:
            The list of stem
            For example:
                stemmer = Stemmer()
                output = stemmer.stem_tokens(['beautiful','playing'])
                print output
                >> [u'beauti', u'play']

        """
        stem_list = []
        for token in tokens:
            stem_list.append(self.stem_word(token.lower().strip()))
        return stem_list

    def __porter_stemmer(self):
        """Initializes PorterStemmer

        Returns:
            Initializes PorterStemmer
        """
        self.stemmer = PorterStemmer()

    def get_stemmer(self):
        """Returns the object of stemmer

        Returns:
            The object of stemmer
        """
        return self.stemmer
