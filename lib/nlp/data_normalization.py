from lib.nlp.const import lemmatizer, ngram_object, tokenizer, stemmer, regx_punctuation_removal, \
    stop_words
from lib.nlp.etc import filter_list
from chatbot_ner.config import nlp_logger


class Normalization(object):
    """ This class performance  text processing on a given text
    Performs several types processing over a message for example: tokenization, stemming, punctuation removal,
    lemmatization, ngram_list.

    Attributes:
        lemmatizer: its an object of Lemmatizer class
        ngram: its an object of Ngram class
        tokenizer: its an object of Tokenizer class
        stemmer: its an object of Stemmer class
        regx_to_process: its an object of Regex class
        stop_word_list: list of stop words
        text: message that needs to be processed
        text_to_process: isa text but regular expression and all the processing operations are performed on this
                            variable
        tokens: list of tokens obtained from input
        tokens_without_stop_words: list of tokens obtained from input without stop words
        stems: list of stems obtained from input
        stems_without_stop_words: list of stems obtained from input without stop words
        lemmas: list of lemmas obtained from input
        lemmas_without_stop_words: list of lemmas obtained from input without stop words
        trigram: list of trigrams obtained from input message
        bigram: list of bigrams obtained from input message
        unigram: list of unigrams obtained from input message
        flag_punctuation_removal: True if punctuations need to be removed from message
        flag_tokens_without_stop_words: True if  stop words need to remove from list of tokens
        flag_stem: True if stems need to obtained from a message
        flag_stem_without_stop_words: True if  stop words need to remove from list of stems
        flag_lemma: True if lemma need to obtained from a message
        flag_lemma_without_stop_words: True if  stop words need to remove from list of lemmas
        stem_unigram: True if list of unigrams needs to be stemmed
        stem_bigram: True if list of bigrams needs to be stemmed
        stem_trigram: True if list of trigrams needs to be stemmed
        stop_words_unigram: True if stop words need to be removed from unigram list
        stop_words_bigram: True if stop words need to be removed from bigram list
        stop_words_trigram: True if stop words need to be removed from trigram list

        data: its dictionary that contains the output.


    For Example:

        n=Normalization()
        message = 'I am playing cricket'
        output=n.preprocess_data(text=message,flag_punctuation_removal=True,flag_tokens=True,flag_stems=True,
        flag_lemma=True)
        print output

         >> {'bigram': [],
             'lemmas': ['i', 'am', 'playing', 'cricket'],
             'lemmas_without_stop_words': ['i', 'am', 'playing', 'cricket'],
             'original_text': 'I am playing cricket',
             'stems': [u'i', u'am', u'play', u'cricket'],
             'stems_without_stop_words': [u'i', u'am', u'play', u'cricket'],
             'text_lowercase': 'i am playing cricket',
             'text_to_process': 'i am playing cricket',
             'text_without_stop_words': 'i am playing cricket',
             'tokens': ['i', 'am', 'playing', 'cricket'],
             'tokens_without_stop_words': ['i', 'am', 'playing', 'cricket'],
             'trigram': [],
             'unigram': []}

        n=Normalization()
        message = 'I am playing cricket'
        output=n.ngram_data(text=message, flag_punctuation_removal=True, stem_unigram=True, stem_bigram=True,
                            stem_trigram=True, stop_words_unigram=True, stop_words_bigram=True,
                            stop_words_trigram=True)
        print output

            >> {'bigram': [u'i am', u'am play', u'play cricket'],
                 'lemmas': [],
                 'lemmas_without_stop_words': [],
                 'original_text': 'I am playing cricket',
                 'stems': [u'i', u'am', u'play', u'cricket'],
                 'stems_without_stop_words': [u'i', u'am', u'play', u'cricket'],
                 'text_lowercase': 'i am playing cricket',
                 'text_to_process': 'i am playing cricket',
                 'text_without_stop_words': 'i am playing cricket',
                 'tokens': ['i', 'am', 'playing', 'cricket'],
                 'tokens_without_stop_words': ['i', 'am', 'playing', 'cricket'],
                 'trigram': [u'i am play', u'am play cricket'],
                 'unigram': [u'i', u'am', u'play', u'cricket']}

    """

    def __init__(self):
        """Initializes a Normalization object
        """

        self.lemmatizer = lemmatizer
        self.ngram = ngram_object
        self.tokenizer = tokenizer
        self.stemmer = stemmer
        self.regx_to_process = regx_punctuation_removal

        self.stop_word_list = stop_words
        self.text = None
        self.text_to_process = None

        self.tokens = []
        self.tokens_without_stop_words = []

        self.stems = []
        self.stems_without_stop_words = []
        self.lemmas = []
        self.lemmas_without_stop_words = []

        self.trigram = []
        self.bigram = []
        self.unigram = []
        self.flag_punctuation_removal = False
        self.flag_tokens_without_stop_words = False
        self.flag_stem = False
        self.flag_stem_without_stop_words = False
        self.flag_lemma = False
        self.flag_lemma_without_stop_words = False

        self.stem_unigram = False
        self.stem_bigram = False
        self.stem_trigram = False
        self.stop_words_unigram = False
        self.stop_words_bigram = False
        self.stop_words_trigram = False

        self.data = {}

    def configuration_file(self, flag_punctuation_removal=True, flag_tokens_without_stop_words=True, flag_stem=True,
                           flag_stem_without_stop_words=True, flag_lemma=True, flag_lemma_without_stop_words=True,
                           stem_unigram=True, stem_bigram=True, stem_trigram=True, stop_words_unigram=True,
                           stop_words_bigram=True, stop_words_trigram=True):
        """Configuration function that enables different functionalities to execute by setting the flags to True

        Args:
            flag_punctuation_removal: True if punctuations need to be removed from message
            flag_tokens_without_stop_words: True if  stop words need to remove from list of tokens
            flag_stem: True if stems need to obtained from a message
            flag_stem_without_stop_words: True if  stop words need to remove from list of stems
            flag_lemma: True if lemma need to obtained from a message
            flag_lemma_without_stop_words: True if  stop words need to remove from list of lemmas
            stem_unigram: True if list of unigrams needs to be stemmed
            stem_bigram: True if list of bigrams needs to be stemmed
            stem_trigram: True if list of trigrams needs to be stemmed
            stop_words_unigram: True if stop words need to be removed from unigram list
            stop_words_bigram: True if stop words need to be removed from bigram list
            stop_words_trigram: True if stop words need to be removed from trigram list
        """
        self.flag_punctuation_removal = flag_punctuation_removal
        self.flag_tokens_without_stop_words = flag_tokens_without_stop_words
        self.flag_stem = flag_stem
        self.flag_stem_without_stop_words = flag_stem_without_stop_words
        self.flag_lemma = flag_lemma
        self.flag_lemma_without_stop_words = flag_lemma_without_stop_words
        self.stem_unigram = stem_unigram
        self.stem_bigram = stem_bigram
        self.stem_trigram = stem_trigram
        self.stop_words_unigram = stop_words_unigram
        self.stop_words_bigram = stop_words_bigram
        self.stop_words_trigram = stop_words_trigram

    def preprocess_data(self, text, flag_punctuation_removal=True, flag_tokens=True, flag_stems=True, flag_lemma=True):
        """Performs tokenization, stemming, taggig and lemmatization on text

        Args:
            flag_punctuation_removal: True if punctuations need to be removed from message
            flag_tokens: True if token need to obtained from a message
            flag_stems: True if stems need to obtained from a message
            flag_lemma: True if lemma need to obtained from a message

        Returns:
            Returns a dictionary that contains output

            For example:
                 n=Normalization()
                 message = 'I am playing cricket'
                 output=n.preprocess_data(text=message,flag_punctuation_removal=True,flag_tokens=True,flag_stems=True,
                 flag_lemma=True)
                 print output

                     >> {'bigram': [],
                         'lemmas': ['i', 'am', 'playing', 'cricket'],
                         'lemmas_without_stop_words': ['i', 'am', 'playing', 'cricket'],
                         'original_text': 'I am playing cricket',
                         'stems': [u'i', u'am', u'play', u'cricket'],
                         'stems_without_stop_words': [u'i', u'am', u'play', u'cricket'],
                         'text_lowercase': 'i am playing cricket',
                         'text_to_process': 'i am playing cricket',
                         'text_without_stop_words': 'i am playing cricket',
                         'tokens': ['i', 'am', 'playing', 'cricket'],
                         'tokens_without_stop_words': ['i', 'am', 'playing', 'cricket'],
                         'trigram': [],
                         'unigram': []}
        """
        self.__set_variables_to_none()
        self.text = text

        if flag_punctuation_removal:
            self.text_to_process = self.regx_to_process.text_substitute(self.text)
        else:
            self.text_to_process = self.text
        nlp_logger.debug('=== punctuation  removal is %s ===' % flag_punctuation_removal)
        self.text_to_process = self.text_to_process.lower()

        if flag_tokens:
            self.tokens = self.tokenizer.tokenize(self.text_to_process)
            self.tokens_without_stop_words = filter_list(self.tokens, self.stop_word_list)
        nlp_logger.debug('=== token is %s ===' % flag_tokens)

        if flag_stems:
            if not self.tokens:
                self.tokens = self.tokenizer.tokenize(self.text_to_process)
            self.stems = self.stemmer.stem_tokens(self.tokens)
            self.stems_without_stop_words = self.stemmer.stem_tokens(
                filter_list(self.tokens, self.stop_word_list))
        nlp_logger.debug('=== stem is %s ===' % flag_stems)

        if flag_lemma:
            if not self.tokens:
                self.tokens = self.tokenizer.tokenize(self.text_to_process)
            self.lemmas = self.lemmatizer.lemmatize_tokens(self.tokens)
            self.lemmas_without_stop_words = self.lemmatizer.lemmatize_tokens(
                filter_list(self.tokens, self.stop_word_list))

        return self.__normalization_dictionary()

    def ngram_data(self, text, flag_punctuation_removal=True, stem_unigram=True, stem_bigram=True, stem_trigram=True,
                   stop_words_unigram=True, stop_words_bigram=True, stop_words_trigram=True):
        """Gets Ngram information of a text

        Args:
            text: message that needs to be processed
            flag_punctuation_removal: True if punctuations need to be removed from message
            stem_unigram: True if list of unigrams needs to be stemmed
            stem_bigram: True if list of bigrams needs to be stemmed
            stem_trigram: True if list of trigrams needs to be stemmed
            stop_words_unigram: True if stop words need to be removed from unigram list
            stop_words_bigram: True if stop words need to be removed from bigram list
            stop_words_trigram: True if stop words need to be removed from trigram list

        Returns:
            Returns a dictionary that contains output

            For example:
                n=Normalization()
                message = 'I am playing cricket'
                output=n.ngram_data(text=message, flag_punctuation_removal=True, stem_unigram=True, stem_bigram=True,
                                    stem_trigram=True, stop_words_unigram=True, stop_words_bigram=True,
                                    stop_words_trigram=True)
                print output

                    >> {'bigram': [u'i am', u'am play', u'play cricket'],
                         'lemmas': [],
                         'lemmas_without_stop_words': [],
                         'original_text': 'I am playing cricket',
                         'stems': [u'i', u'am', u'play', u'cricket'],
                         'stems_without_stop_words': [u'i', u'am', u'play', u'cricket'],
                         'text_lowercase': 'i am playing cricket',
                         'text_to_process': 'i am playing cricket',
                         'text_without_stop_words': 'i am playing cricket',
                         'tokens': ['i', 'am', 'playing', 'cricket'],
                         'tokens_without_stop_words': ['i', 'am', 'playing', 'cricket'],
                         'trigram': [u'i am play', u'am play cricket'],
                         'unigram': [u'i', u'am', u'play', u'cricket']}
        """
        self.__set_variables_to_none()
        self.text = text

        if flag_punctuation_removal:
            self.text_to_process = self.regx_to_process.text_substitute(self.text)
        else:
            self.text_to_process = self.text
        nlp_logger.debug('=== punctuation  removal is %s ===' % flag_punctuation_removal)
        self.text_to_process = self.text_to_process.lower()

        self.tokens = self.tokenizer.tokenize(self.text_to_process)
        self.tokens_without_stop_words = filter_list(self.tokens, self.stop_word_list)
        self.stems = self.stemmer.stem_tokens(self.tokens)
        self.stems_without_stop_words = self.stemmer.stem_tokens(self.tokens_without_stop_words)

        if self.tokens or self.stems:
            self.trigram = self.__get_ngram(3, stem_trigram, stop_words_trigram)
            self.bigram = self.__get_ngram(2, stem_bigram, stop_words_bigram)
            self.unigram = self.__get_ngram(1, stem_unigram, stop_words_unigram)
            nlp_logger.debug('=== Ngrams are set  ===')
        else:
            nlp_logger.debug('=== Ngram can not be set  ===')

        return self.__normalization_dictionary()

    def normalize_data(self, text, regx_to_process=None):
        """This is main function that calls all the functionality based on the flags set from configuration_file()

        Args:
            text: message that needs to be processed
            regx_to_process: regex object that can be used to process the text

        Returns:
            Returns a dictionary that contains output

            For example:
                n=Normalization()
                message = 'I am playing cricket'
                n.configuration_file(flag_punctuation_removal=True, flag_tokens_without_stop_words=True,
                                    flag_stem=True, flag_stem_without_stop_words=True, flag_lemma=True,
                                    flag_lemma_without_stop_words=True, stem_unigram=True, stem_bigram=True,
                                     stem_trigram=True, stop_words_unigram=True, stop_words_bigram=True,
                                     stop_words_trigram=True)
                output=n.normalize_data(text=message)
                print output

                    >> {'bigram': [u'i am', u'am play', u'play cricket'],
                         'lemmas': ['i', 'am', 'playing', 'cricket'],
                         'lemmas_without_stop_words': ['i', 'am', 'playing', 'cricket'],
                         'original_text': 'I am playing cricket',
                         'stems': [u'i', u'am', u'play', u'cricket'],
                         'stems_without_stop_words': [u'i', u'am', u'play', u'cricket'],
                         'text_lowercase': 'i am playing cricket',
                         'text_to_process': 'i am playing cricket',
                         'text_without_stop_words': 'i am playing cricket',
                         'tokens': ['i', 'am', 'playing', 'cricket'],
                         'tokens_without_stop_words': ['i', 'am', 'playing', 'cricket'],
                         'trigram': [u'i am play', u'am play cricket'],
                         'unigram': [u'i', u'am', u'play', u'cricket']}

        """

        self.text = text
        self.__set_variables_to_none()
        self.__process_text(regx_to_process)
        return self.__normalization_dictionary()

    def __process_text(self, regx_to_process=None):
        """This function contains all the functionality i.e. text processing, tokenization, stemming , Ngrams

        Args:
            regx_to_process: regex object that can be used to process the text

        Returns:
            Returns a dictionary that contains output
        """

        if not regx_to_process:
            regx_to_process = self.regx_to_process
            nlp_logger.debug('=== selected default punctuation regular expression ===')
        if self.flag_punctuation_removal:
            self.text_to_process = regx_to_process.text_substitute(self.text)
        else:
            self.text_to_process = self.text
        nlp_logger.debug('=== punctuation  removal is %s ===' % self.flag_punctuation_removal)

        self.text_to_process = self.text_to_process.lower()
        self.tokens = self.tokenizer.tokenize(self.text_to_process)
        nlp_logger.debug('=== tokens are identified ===')

        if self.flag_tokens_without_stop_words:
            self.tokens_without_stop_words = filter_list(self.tokens, self.stop_word_list)
        nlp_logger.debug('=== tokens without stop words is %s ===' % self.flag_tokens_without_stop_words)

        if self.flag_stem and self.tokens:
            self.stems = self.stemmer.stem_tokens(self.tokens)
        nlp_logger.debug('=== stemmer is %s ===' % self.flag_stem)

        if self.flag_stem_without_stop_words:
            if self.tokens_without_stop_words:
                self.stems_without_stop_words = self.stemmer.stem_tokens(self.tokens_without_stop_words)
            else:
                self.stems_without_stop_words = self.stemmer.stem_tokens(
                    filter_list(self.tokens, self.stop_word_list))
        nlp_logger.debug('=== stemmer without stop words is %s ===' % self.flag_stem_without_stop_words)

        if self.flag_lemma and self.tokens:
            self.lemmas = self.lemmatizer.lemmatize_tokens(self.tokens)
        nlp_logger.debug('=== lemma is %s ===' % self.flag_lemma)

        if self.flag_lemma_without_stop_words:
            if self.tokens_without_stop_words:
                self.lemmas_without_stop_words = self.lemmatizer.lemmatize_tokens(self.tokens_without_stop_words)
            else:
                self.lemmas_without_stop_words = self.lemmatizer.lemmatize_tokens(
                    filter_list(self.tokens, self.stop_word_list))
        nlp_logger.debug('=== lemma without stop word is %s ===' % self.flag_lemma_without_stop_words)

        if self.stems or self.tokens:
            self.trigram = self.__get_ngram(3, self.stem_trigram, self.stop_words_trigram)
            self.bigram = self.__get_ngram(2, self.stem_bigram, self.stop_words_bigram)
            self.unigram = self.__get_ngram(1, self.stem_unigram, self.stop_words_unigram)
            nlp_logger.debug('=== Ngrams are set  ===')
        else:
            nlp_logger.debug('=== Ngram can not be set  ===')

    def __set_variables_to_none(self):
        """This function sets variables like self.text_to_process, self.tokens, self.tokens_without_stop_words,
        self.stems, self.stem_without_stop_words, self.lemmas, self.lemmas_without_stop_words, self.trigram,
        self.bigram, self.unigram to None
        """
        self.text_to_process = None

        self.tokens = []
        self.tokens_without_stop_words = []

        self.stems = []
        self.stems_without_stop_words = []
        self.lemmas = []
        self.lemmas_without_stop_words = []

        self.trigram = []
        self.bigram = []
        self.unigram = []
        self.data = {}
        nlp_logger.debug('=== variables are set to none ===')

    def __get_ngram(self, ngram, flag_stem, flag_stop_words):
        """This function returns list of ngrams
        Args:
            ngram: integer value i.e. 1, 2, 3
            flag_stem: True if stem list to used
            flag_stop_words: True if stop words need to be removed from ngram list

        Returns:
            list of ngrams
        """
        word_list = self.stems if flag_stem else self.tokens
        stop_words = self.stop_word_list if flag_stop_words else []
        return self.ngram.ngram_list(ngram, word_list, stop_words)

    def __normalization_dictionary(self):
        """This returns the output
        Returns:
            the dictionary
        """
        self.data['original_text'] = self.text
        self.data['text_lowercase'] = self.text.lower()
        self.data['text_to_process'] = self.text_to_process
        if self.tokens_without_stop_words:
            self.data['text_without_stop_words'] = ' '.join(self.tokens_without_stop_words)
        else:
            self.data['text_without_stop_words'] = None

        self.data['tokens'] = self.tokens
        self.data['tokens_without_stop_words'] = self.tokens_without_stop_words
        self.data['stems'] = self.stems
        self.data['stems_without_stop_words'] = self.stems_without_stop_words
        self.data['lemmas'] = self.lemmas
        self.data['lemmas_without_stop_words'] = self.lemmas_without_stop_words
        self.data['trigram'] = self.trigram
        self.data['bigram'] = self.bigram
        self.data['unigram'] = self.unigram
        nlp_logger.debug('=== dictionary created ===')

        return self.data
