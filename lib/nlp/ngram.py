class Ngram(object):
    """
    This class is used to perform Ngram operations

    In this class we have defined following functionality that can be used to get list of ngrams
        1. ngram_list:
            Attributes:
                ngram: i.e. 1, 2, 3...
                word_list: list of words
                stop_word_list: list of words that should be excluded while obtaining list of ngrams
            This function will get the list of ngrams. If the ngram contains all the stop words then it will not be
            appended in the list
    For Example:
        ngram_object = Ngram()
        ngram=2
        word_list = ['hi','hello','how','are','you','hi']
        stop_word_list = ['hi','you']
        output = ngram_object.ngram_list(ngram, word_list, stop_word_list)
        print output
        >> ['hi hello', 'hello how', 'how are', 'are you']

    In above example the output does'nt contain  'you hi' as both are stop words
    """

    def __init__(self):
        pass

    def ngram_list(self, ngram, word_list, stop_word_list=None):
        """This function will get the list of ngrams. If the ngram contains all the stop words then it will not be
            appended in the list

        Args:
            ngram: i.e. 1, 2, 3...
            word_list: list of words
            stop_word_list: list of words that should be excluded while obtaining list of ngrams

        Returns:
            List of ngrams
        """

        ngram_list = []
        if len(word_list) >= ngram:
            n = 0
            for n in range(0, len(word_list) - ngram + 1):
                location = 0
                data = ''
                count_stop_word = 0
                while location < ngram:
                    if stop_word_list and (str(word_list[n + location].lower()) in stop_word_list):
                        count_stop_word += 1
                    data += word_list[n + location] + ' '
                    location += 1
                if count_stop_word < ngram:
                    ngram_list.append(data.strip())
                n += 1

        return ngram_list
