from __future__ import absolute_import
import re
import nltk
import regex

# constants
from lib.singleton import Singleton
import six

NLTK_TOKENIZER = 'WORD_TOKENIZER'
PRELOADED_NLTK_TOKENIZER = 'PRELOADED_NLTK_TOKENIZER'
LUCENE_STANDARD_TOKENIZER = 'LUCENE_STANDARD_TOKENIZER'
WHITESPACE_TOKENIZER = 'WHITESPACE_TOKENIZER'


class Tokenizer(six.with_metaclass(Singleton, object)):
    """
    Returns the list of the tokens from the text
    Its a wrapper class which can be used to call respective tokenizer library. Currently, It has been integrated
    with word tokenizer from nltk library but can be integrated with other libraries.

    For Example:
        output = token.tokenize('Hey, How are you doing?')
        print output
        >> ['Hey', ',', 'How', 'are', 'you', 'doing', '?']

    Attributes:
        tokenizer_selected: Tokenizer which needs to be selected for processing
        tokenizer_dict: It is a Dictionary where key is the tokenizer type and value is the function that needs
        to be called to get its object
        tokenizer: Object of the tokenizer obtained from external library example, Word Tokenizer

    """

    def __init__(self, tokenizer_selected=NLTK_TOKENIZER):
        """Initializes a Tokenizer object

        Args:
            tokenizer_selected: Tokenizer which needs to be selected for processing
        """
        self.tokenizer_selected = tokenizer_selected
        self.tokenizer_dict = {
            NLTK_TOKENIZER: self.__nltk_tokenizer,
            PRELOADED_NLTK_TOKENIZER: self.__preloaded_nltk_tokenizer,
            LUCENE_STANDARD_TOKENIZER: self.__lucene_standard_tokenizer,
            WHITESPACE_TOKENIZER: self.__whitespace_tokenizer,
        }
        self.tokenizer = self.tokenizer_dict[self.tokenizer_selected]()

    def __lucene_standard_tokenizer(self):
        """
        Tokenizer that mimicks Elasticsearch/Lucene's standard tokenizer
        Uses word boundaries defined in Unicode Annex 29
        """
        words_pattern = regex.compile(r'\w(?:\B\S)*', flags=regex.V1 | regex.WORD | regex.UNICODE)

        def word_tokenize(text):
            return words_pattern.findall(text)

        return word_tokenize

    def __nltk_tokenizer(self):
        """
        Get nltk word tokenizer

        Returns:
            callable: nltk.word_tokenize callable
        """
        return nltk.word_tokenize

    def __preloaded_nltk_tokenizer(self):
        """
        Get cached nltk tokenizer

        Faster version of nltk punkt tokenizer. It avoids a heavy I/O cycle at each tokenize call by preloading it
        WARNING! It loads only the english tokenizer

        Returns:
            callable: tokenizer with punkt tokenizer cached in memory
        """
        # Code pulled out of nltk == 3.2.5
        tokenizer = nltk.load('tokenizers/punkt/{0}.pickle'.format('english'))
        sent_tokenizer = tokenizer.tokenize

        def word_tokenize(text):
            sentences = sent_tokenizer(text)
            tokens = []
            for sent in sentences:
                tokens.extend(nltk.word_tokenize(sent, preserve_line=True))
            return tokens

        return word_tokenize

    def __whitespace_tokenizer(self):
        """
        Get simple whitespace tokenizer

        Returns:
            callable: A python callable that splits str into tokens delimited by whitespace

        """
        pattern = re.compile(r'\s+', re.IGNORECASE | re.UNICODE)
        return pattern.split

    def get_tokenizer(self):
        """
        Get the object of set tokenizer

        Returns:
            Any: The object of tokenizer
        """
        return self.tokenizer

    def tokenize(self, text):
        """
        Returns the list of tokens from text

        Args:
            text: text to tokenize

        Returns:
            list of str: The list of tokens
            For example:
                token = Tokenizer()
                output = token.tokenize('Hey, How are you doing?')
                print output
                >> ['Hey', ',', 'How', 'are', 'you', 'doing', '?']

        """
        return self.tokenizer(text)
