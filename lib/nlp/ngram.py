from __future__ import absolute_import
import nltk


class Ngram(object):
    """
    Utility to generate ngrams with filters like removing stop words

    For Example:
        ngram_object = Ngram()
        ngram = 2
        word_list = ['hi','hello','how','are','you','hi']
        stop_word_list = ['hi','you']
        output = ngram_object.ngram_list(ngram, word_list, stop_word_list)
        print output
        >> ['hi hello', 'hello how', 'how are', 'are you']

    In above example the output does'nt contain  'you hi' as both are stop words
    """

    def __init__(self):
        pass

    @staticmethod
    def ngram_list(n, word_list, stop_word_list=None):
        """
        Generate ngrams with width n excluding those that are entirely formed of stop words

        Args:
            n (int): i.e. 1, 2, 3...
            word_list (list of str): list of words
            stop_word_list (list of str, Optional): list of words that should be excluded while obtaining
                                                    list of ngrams

        Returns:
            list of str: List of ngrams formed from the given word list except for those that have all their tokes in
                         stop words list
        """
        stop_word_set = set(stop_word_list) if stop_word_list else []
        all_ngrams = nltk.ngrams(word_list, n)
        ngram_list = []
        for ngram in all_ngrams:
            lowered_ngram_tokens = [token.lower() for token in ngram]
            if any(token not in stop_word_set for token in lowered_ngram_tokens):
                ngram_list.append(' '.join(ngram))
        return ngram_list
