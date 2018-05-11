import re

from datastore import DataStore
from lib.nlp.const import tokenizer
from lib.nlp.data_normalization import Normalization
from lib.nlp.levenshtein_distance import edit_distance
from lib.nlp.regex import Regex


class TextDetector(object):
    """
    TextDetector detects custom entities in text string by performing similarity searches against a list fetched from
    datastore (elasticsearch) and tags them.

    TextDetector detects text type custom entities that do not adhere to some strict/weak formats which other entities
    like date, time, email, etc do. Examples of such types of entites can be city, food dish name, brand names etc


    Attributes:
        text (str): string to extract entities from
        entity_name (str): string by which the detected time entities would be replaced with on calling detect_entity()
        regx_to_process (lib.nlp.Regex): list of regex patterns to match and remove text that matches
                                         these patterns before starting to detect entities
        text_dict (dict): dictionary to store lemmas, stems, ngrams used during detection process
        _fuzziness (str or int): If this parameter is str, elasticsearch's
                                 auto is used with low and high term distances. Default low and high term distances
                                 are 3 and 6 for elasticsearch. For this module they are set to 4 and 7 respectively.
                                 In auto mode, if length of term is less than low it must match exactly, if it is
                                 between [low, high) one insert/delete/substitution is allowed, for anything higher
                                 than equal to high, two inserts/deletes/substitutions are allowed
        _min_token_size_for_fuzziness (int): minimum number of letters a word must have to be considered
                                             for calculating edit distance with similar ngrams from the datastore
        tagged_text (str): string with time entities replaced with tag defined by entity_name
        text_entity (list): list to store detected entities from the text
        original_text_entity (list): list of substrings of the text detected as entities
        processed_text (str): string with detected time entities removed
        tag (str): entity_name prepended and appended with '__'
    """

    def __init__(self, entity_name=None):
        """
        Initializes a TextDetector object with given entity_name

        Args:
            entity_name: A string by which the detected substrings that correspond to text entities would be replaced
                         with on calling detect_entity()
        """
        self.text = None
        self.regx_to_process = Regex([(r'[\'\/]', r'')])
        self.text_dict = {}
        self.tagged_text = None
        self.text_entity = []
        self.original_text_entity = []
        self.processed_text = None
        self.entity_name = entity_name
        self.tag = '__' + self.entity_name + '__'

        # defaults for auto mode
        self._fuzziness = "auto:4,7"
        self._fuzziness_lo, self._fuzziness_hi = 4, 7
        self._min_token_size_for_fuzziness = self._fuzziness_lo
        # self.set_fuzziness_threshold(fuzziness=(self._fuzziness_lo, self._fuzziness_hi))

        # defaults for non-auto mode
        self.set_fuzziness_threshold(fuzziness=1)
        self._min_token_size_for_fuzziness = 4

        self.db = DataStore()

    def set_fuzziness_threshold(self, fuzziness):
        """
        Sets the fuzziness thresholds for similarity searches. The fuzziness threshold corresponds to the
        maximum Levenshtein's distance allowed during similarity matching

        Args:
            fuzziness (iterable or int): If this parameter is int, elasticsearch's auto is used with
                                         low and high term distances.
                                         Please make sure the iterable has only two integers like (4, 7).
                                         This will generate "auto:4,7"

                                         Note that this also sets
                                         _min_token_size_for_fuzziness to first value of the iterable

                                         Default low and high term distances are 3 and 6 for elasticsearch.
                                         See [1] for more details.

                                         If this argument is int, elasticsearch will set fuzziness as
                                         min(2, fuzziness)

        [1] https://www.elastic.co/guide/en/elasticsearch/reference/current/common-options.html#fuzziness

        """
        try:
            iter(fuzziness)
            if len(fuzziness) == 2:
                lo, hi = fuzziness
                self._fuzziness_lo, self._fuzziness_hi = int(lo), int(hi)
                self._fuzziness = "auto:" + str(self._fuzziness_lo) + "," + str(self._fuzziness_hi)
                self._min_token_size_for_fuzziness = lo
            else:
                self._fuzziness = "auto"
        except TypeError:
            if type(fuzziness) == int or type(fuzziness) == float:
                self._fuzziness = int(fuzziness)  # Note that elasticsearch would take min(2, self._fuzziness)
            else:
                raise TypeError('fuziness has to be either an iterable of length 2 or an int')

    def _get_fuzziness_threshold_for_token(self, token):
        """
        Return dynamic fuzziness threshold for damerau-levenshtein check based on length of token if elasticsearch
        fuzziness was set to auto mode

        Args:
            token (str or unicode): the string to calculate fuzziness threshold for

        Returns:
            int: fuzziness threshold for ngram matching on elastic search results
        """
        if type(self._fuzziness) == int:
            return self._fuzziness
        else:
            if len(token) < self._fuzziness_lo:
                return 0  # strict match
            elif len(token) >= self._fuzziness_hi:
                return 2  # Allow upto two inserts/deletes and one substitution
            else:
                return 1  # lo <= len < hi Allow only insert/delete

    def set_min_token_size_for_levenshtein(self, min_size):
        """
        Sets the minimum number of letters a word must have to be considered for calculating edit distance with similar
        ngrams from the datastore

        Args:
            min_size: integer, maximum allowed Levenshtein's distance from the word/phrase being tested for
            entity match
        """
        self._min_token_size_for_fuzziness = min_size

    def detect_entity(self, text):
        """
        Detects all textual entities in text that are similar to variants of 'entity_name' stored in the datastore and
        returns two lists of detected text entities and their corresponding original substrings in text respectively.
        Note that datastore stores number of values under a entity_name and each entity_value has its own list of
        variants, whenever a variant is matched sucessfully, the entity_value whose list the variant belongs to,
        is returned. For more information on how data is stored, see Datastore docs.

        Args:
            text: string to extract textual entities from

        Returns:
            Tuple containing two lists, first containing entity value as defined into datastore
            and second list containing corresponding original substrings in text

        Example:
            DataStore().get_entity_dictionary('city')

                Output:
                    {
                        u'Agartala': [u'', u'Agartala'],
                        u'Barnala': [u'', u'Barnala'],
                        ...
                        u'chennai': [u'', u'chennai', u'tamilnadu', u'madras'],
                        u'hyderabad': [u'hyderabad'],
                        u'koramangala': [u'koramangala']
                    }

            text_detection = TextDetector('city')
            text_detection.detect_entity('Come to Chennai, TamilNadu,  I will visit Delhi next year')

                Output:
                    ([u'Chennai', u'New Delhi', u'chennai'], ['chennai', 'delhi', 'tamilnadu'])

            text_detection.tagged_text

                Output:
                    ' come to __city__, __city__,  i will visit __city__ next year '

        Additionally this function assigns these lists to self.time and self.original_text_entity attributes
        respectively.
        """
        self.text = text
        self.text = self.regx_to_process.text_substitute(self.text)
        self.text = ' ' + self.text.lower() + ' '
        self.processed_text = self.text
        text_entity_data = self._text_detection_with_variants()
        self.tagged_text = self.processed_text
        self.text_entity = text_entity_data[0]
        self.original_text_entity = text_entity_data[1]
        return text_entity_data

    def _text_detection_with_variants(self):
        """
        This function will normalise the message by breaking it into trigrams, bigrams and unigrams. The generated
        ngrams will be used to create query to retrieve search results from datastore. These results will contain a
        dictionary where key will be variant and value will be entity value this will be further processed to get the
        original text which has been identified and will return the results

        Returns:
             A tuple of two lists with first list containing the detected text entities and second list containing
             their corresponding substrings in the original message.
        """
        original_final_list = []
        value_final_list = []
        normalization = Normalization()
        self.text_dict = normalization.ngram_data(self.processed_text.lower(), flag_punctuation_removal=False,
                                                  stem_unigram=False, stem_bigram=False, stem_trigram=False,
                                                  stop_words_unigram=True, stop_words_bigram=True,
                                                  stop_words_trigram=True).copy()
        variant_dictionary = {}

        trigram_variants = self.db.get_similar_ngrams_dictionary(self.entity_name, self.text_dict['trigram'],
                                                                 self._fuzziness)
        bigram_variants = self.db.get_similar_ngrams_dictionary(self.entity_name, self.text_dict['bigram'],
                                                                self._fuzziness)
        unigram_variants = self.db.get_similar_ngrams_dictionary(self.entity_name, self.text_dict['unigram'],
                                                                 self._fuzziness)
        variant_dictionary.update(trigram_variants)
        variant_dictionary.update(bigram_variants)
        variant_dictionary.update(unigram_variants)
        variant_list = variant_dictionary.keys()

        exact_matches, fuzzy_variants = [], []
        for variant in variant_list:
            if variant.lower() in self.processed_text.lower():
                exact_matches.append(variant)
            else:
                fuzzy_variants.append(variant)

        exact_matches.sort(key=lambda s: len(tokenizer.tokenize(s)), reverse=True)
        fuzzy_variants.sort(key=lambda s: len(tokenizer.tokenize(s)), reverse=True)
        variant_list = exact_matches + fuzzy_variants

        for variant in variant_list:
            original_text = self._get_entity_from_text(variant, self.processed_text.lower())
            if original_text:
                value_final_list.append(variant_dictionary[variant])
                original_final_list.append(original_text)
                self.processed_text = re.sub(r'\b' + original_text + r'\b', self.tag, self.processed_text)

        return value_final_list, original_final_list

    def _get_entity_from_text(self, variant, text):
        """
        Checks ngrams of the text for similarity against the variant (can be a ngram) using Levenshtein distance

        Args:
            variant: string, ngram of variant to fuzzy detect in the text using Levenshtein distance
            text: text to detect entities from

        Returns:
            part of the given text that was detected as entity given the variant, None otherwise

        Example:
            text_detection = TextDetector('city')
            ...
            text_detection._get_entity_from_text(self, variant, text)
            text = 'Come to Chennai, Tamil Nadu,  I will visit Delehi next year'.lower()
            text_detection.get_entity_from_text('chennai', text)

            Output:
                'chennai'

            text_detection.get_entity_from_text('Delhi', text)

            Output:
                'delehi'
        """
        variant_tokens = tokenizer.tokenize(variant.lower())
        text_tokens = tokenizer.tokenize(text.lower())
        original_text = []
        variant_count = 0
        for text_token in text_tokens:
            variant_token = variant_tokens[variant_count]

            utext_token = text_token
            if type(utext_token) == 'str':
                utext_token = utext_token.decode('utf-8')

            same = variant_token == text_token
            ft = self._get_fuzziness_threshold_for_token(utext_token)
            if same or (len(utext_token) > self._min_token_size_for_fuzziness
                        and edit_distance(string1=variant_token,
                                          string2=text_token,
                                          max_distance=ft + 1) <= ft):
                original_text.append(text_token)
                variant_count += 1
                if variant_count == len(variant_tokens):
                    return ' '.join(original_text)
            else:
                original_text = []
                variant_count = 0
        return None
