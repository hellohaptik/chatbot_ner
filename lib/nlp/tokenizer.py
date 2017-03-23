import nltk

# constants
WORD_TOKENIZER = 'WORD_TOKENIZER'


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

    def __init__(self, tokenizer_selected=WORD_TOKENIZER):
        """Initializes a Tokenizer object

        Args:
            tokenizer_selected: Tokenizer which needs to be selected for processing
        """
        self.tokenizer = None
        self.tokenizer_selected = tokenizer_selected
        self.tokenizer_dict = {
            WORD_TOKENIZER: self.__word_tokenizer
        }
        self.tokenizer_dict[self.tokenizer_selected]()

    def __word_tokenizer(self):
        """Initializes Word Tokenizer

        Returns:
            Initializes Word Tokenizer
        """
        self.tokenizer = nltk.word_tokenize

    def get_tokenizer(self):
        """Returns the object of tokenizer

        Returns:
            The object of tokenizer
        """
        return self.tokenizer

    def tokenize(self, text):
        """Returns the list of tokens from text

        Args:
            tokens: list of tokens

        Returns:
            The list of tokens
            For example:
                token = Tokenizer()
                output = token.tokenize('Hey, How are you doing?')
                print output
                >> ['Hey', ',', 'How', 'are', 'you', 'doing', '?']

        """

        if WORD_TOKENIZER == self.tokenizer_selected:
            return self.tokenizer(text)
