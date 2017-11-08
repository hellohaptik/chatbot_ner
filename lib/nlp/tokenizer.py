import nltk

# constants
from lib.singleton import Singleton

NLTK_TOKENIZER = 'WORD_TOKENIZER'
PRELOADED_NLTK_TOKENIZER = 'PRELOADED_NLTK_TOKENIZER'


class Tokenizer(object):
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

    __metaclass__ = Singleton

    def __init__(self, tokenizer_selected=NLTK_TOKENIZER):
        """Initializes a Tokenizer object

        Args:
            tokenizer_selected: Tokenizer which needs to be selected for processing
        """
        self.tokenizer_selected = tokenizer_selected
        self.tokenizer_dict = {
            NLTK_TOKENIZER: self.__nltk_tokenizer,
            PRELOADED_NLTK_TOKENIZER: self.__preloaded_nltk_tokenizer,
        }
        self.tokenizer = self.tokenizer_dict[self.tokenizer_selected]()

    def __nltk_tokenizer(self):
        """Initializes Word Tokenizer

        Returns:
            Initializes Word Tokenizer
        """
        return nltk.word_tokenize

    def __preloaded_nltk_tokenizer(self):
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

    def get_tokenizer(self):
        """Returns the object of tokenizer

        Returns:
            The object of tokenizer
        """
        return self.tokenizer

    def tokenize(self, text):
        """Returns the list of tokens from text

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
