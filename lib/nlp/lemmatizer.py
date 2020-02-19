from __future__ import absolute_import
from nltk.stem import WordNetLemmatizer

# constants
from lib.singleton import Singleton
import six

WORDNET_LEMMATIZER = 'WORDNET_LEMMATIZER'


class Lemmatizer(six.with_metaclass(Singleton, object)):
    """
    Detects the lemma of a word.
    Its a wrapper class which can be used to call respective lemmatizer library. Currently, It has been integrated
    with WordNetLemmatizer from nltk library but can be integrated with other libraries.
    In this class we have defined three functionality that can be used by the user to get the lemma of the word
        1. Given a word it will return its lemma
        2. Given a word and category it will return its lemma for given category
        3. Given a list of tokens it will return list of lemmas

    For Example:

        lemma=Lemmatizer()
        output= lemma.lemmatize_word_category('meeting','v')
        print output
        >> 'meet'

        lemma=Lemmatizer()
        output= lemma.lemmatize_word('plays')
        print output
        >> 'play'

        lemma=Lemmatizer()
        output= lemma.lemmatize_tokens(['plays','boys'])
        print output
        >> ['play','boy']

    Attributes:
        lemmatizer_selected: Lemmatizer which needs to be selected for processing
        lemmatizer_dict: It is a Dictionary where key is the lemmatizer type and value is the function that needs
        to be called to get its object
        lemmatizer: Object of the lemmatizer obtained from external library example, WordNetLemmatizer

    """

    def __init__(self, lemmatizer_selected=WORDNET_LEMMATIZER):
        """Initializes a Lemmatizer object

        Args:
            lemmatizer_selected: Lemmatizer which needs to be selected for processing
        """
        self.lemmatizer = None
        self.lemmatizer_selected = lemmatizer_selected
        self.lemmatizer_dict = {
            WORDNET_LEMMATIZER: self.__wordnet_lemmatizer
        }
        self.lemmatizer_dict[self.lemmatizer_selected]()

    def lemmatize_word_category(self, word, category):
        """Returns the lemma of a word given its category

        Args:
            word: string to extract to extract its lemma
            category: Grammatical category of that word

        Returns:
            The lemma of a word given its lemma
            For example:
                lemma=Lemmatizer()
                output= lemma.lemmatize_word_category('meeting','v')
                print output
                >> 'meet'

        """
        if WORDNET_LEMMATIZER == self.lemmatizer_selected:
            return self.lemmatizer.lemmatize(word, category)

    def lemmatize_word(self, word):
        """Returns the lemma of a word

        Args:
            word: string to extract to extract its lemma

        Returns:
            The lemma of a word
            For example:
                lemma=Lemmatizer()
                output= lemma.lemmatize_word('plays')
                print output
                >> 'play'

        """
        if WORDNET_LEMMATIZER == self.lemmatizer_selected:
            return self.lemmatizer.lemmatize(word)

    def lemmatize_tokens(self, tokens):
        """Returns the list of lemma for list of tokens

        Args:
            tokens: list of strings to extract its lemma

        Returns:
            The list of lemma
            For example:
                lemma=Lemmatizer()
                output= lemma.lemmatize_tokens(['plays','boys'])
                print output
                >> ['play','boy']

        """

        lemma_list = []
        for token in tokens:
            lemma_list.append(self.lemmatize_word(token.lower().strip()))
        return lemma_list

    def get_lemmatizer(self):
        """Returns the object of lemmatizer

        Returns:
            The object of lemmatizer
        """
        return self.lemmatizer

    def __wordnet_lemmatizer(self):
        """Initializes WordNetLemmatizer

        Returns:
            Initializes WordNetLemmatizer
        """
        self.lemmatizer = WordNetLemmatizer()
        # Call lemmatize to avoid lazy load
        _ = self.lemmatizer.lemmatize('start')

