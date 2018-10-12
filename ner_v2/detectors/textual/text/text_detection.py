import re
import collections
from six import iteritems

from chatbot_ner.config import ner_logger
from datastore import DataStore
from lib.nlp.const import TOKENIZER, whitespace_tokenizer
from lib.nlp.levenshtein_distance import edit_distance
# from lib.nlp.regexreplace import RegexReplace
from ner_v2.detectors.base_detector import BaseDetector
from ner_v2.language_utilities.constant import ENGLISH_LANG, HINDI_LANG


class TextDetector(BaseDetector):
    """
    TextDetector detects custom entities in text string by performing similarity searches against a list fetched from
    datastore (elasticsearch) and tags them.

    TextDetector detects text type custom entities that do not adhere to some strict/weak formats which other entities
    like date, time, email, etc do. Examples of such types of entites can be city, food dish name, brand names etc


    Attributes:
        text (str): string to extract entities from
        entity_name (str): string by which the detected time entities would be replaced with on calling detect_entity()
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
        text_entity_values (list): list to store detected entities from the text
        original_texts (list): list of substrings of the text detected as entities
        processed_text (str): string with detected text entities removed
        tag (str): entity_name prepended and appended with '__'
    """

    def __init__(self, entity_name=None, source_language_script=ENGLISH_LANG, translation_enabled=False):
        """
        Initializes a TextDetector object with given entity_name

        Args:
            entity_name: A string by which the detected substrings that correspond to text entities would be replaced
                         with on calling detect_entity()
            source_language_script: ISO 639 code for language of entities to be detected by the instance of this class
            translation_enabled: True if messages needs to be translated in case detector does not support a
                                 particular language, else False
        """
        # assigning values to superclass attributes
        self._supported_languages = [ENGLISH_LANG, HINDI_LANG]
        super(TextDetector, self).__init__(source_language_script, translation_enabled)

        self.text = None
        self.text_dict = {}
        self.tagged_text = None
        self.text_entity_values = []
        self.original_texts = []
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

    @property
    def supported_languages(self):
        return self._supported_languages

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

    def _process_text(self, text):
        self.text = text.lower()
        if isinstance(self.text, bytes):
            self.text = self.text.decode('utf-8')

        self.processed_text = self.text

        # Note: following rules have been disabled because cause problem with generating original text
        # regx_to_process = RegexReplace([(r'[\'\/]', r''), (r'\s+', r' ')])
        # self.processed_text = self.regx_to_process.text_substitute(self.processed_text)
        self.processed_text = u' ' + self.processed_text + u' '
        self.tagged_text = self.processed_text

    def _get_substring_from_processed_text(self, matched_tokens):
        """
        Get part of original text that was detected as some entity value.

        This method was written to tackle cases when original text contains special characters which are dropped
        during tokenization

        Args:
            matched_tokens (list): list of tokens (usually tokens from fuzzy match results from ES)
                                   to find as a contiguous substring in the processed text considering the effects
                                   of tokenizer

        Returns:
            str or unicode: part of original text that corresponds to given tokens

        E.g.
        self.processed_text = u'i want to order 1 pc hot & crispy'
        tokens = [u'i', u'want', u'to', u'order', u'1', u'pc', u'hot', u'crispy']
        indices = [(1, 2), (3, 7), (8, 10), (11, 16), (17, 18), (19, 21), (22, 25), (28, 34)])

        In: matched_tokens = [u'1', u'pc', u'hot', u'crispy']
        Out: 1 pc hot & crispy

        Notice that & is dropped during tokenization but when finding original text, we recover it from processed text
        """

        def _get_tokens_and_indices(text):
            """
            Args:
                text (str or unicode): text to get tokens from and indicies of those tokens in the given text

            Returns:
                tuple:
                    list: containing tokens, direct results from tokenizer.tokenize
                    list: containing (int, int) indicating start and end position of ith token (of first list)
                          in given text

            E.g.
            In: text = u'i want to order 1 pc hot & crispy'
            Out: ([u'i', u'want', u'to', u'order', u'1', u'pc', u'hot', u'crispy'],
                  [(1, 2), (3, 7), (8, 10), (11, 16), (17, 18), (19, 21), (22, 25), (28, 34)])

            """
            txt = text.rstrip() + ' __eos__'
            processed_text_tokens = TOKENIZER.tokenize(txt)
            processed_text_tokens_indices = []

            offset = 0
            for token in processed_text_tokens:
                st = txt.index(token)
                en = st + len(token)

                # Small block to handle tricky cases like '(A B) C'
                # It extends the previous token's end boundary if there are special characters except whitespace
                # towards the end of previous token
                prefix = txt[:en]
                prefix_tokens = whitespace_tokenizer.tokenize(prefix)
                if prefix and len(prefix_tokens) > 1 and prefix_tokens[0]:
                    if processed_text_tokens_indices:
                        s, e = processed_text_tokens_indices.pop()
                        e += len(prefix_tokens[0])
                        processed_text_tokens_indices.append((s, e))

                txt = txt[en:]
                processed_text_tokens_indices.append((offset + st, offset + en))
                offset += en

            # remove eos parts
            processed_text_tokens.pop()
            processed_text_tokens_indices.pop()

            return processed_text_tokens, processed_text_tokens_indices

        try:
            n = len(matched_tokens)
            tokens, indices = _get_tokens_and_indices(self.processed_text)
            for i in range(len(tokens) - n + 1):
                if tokens[i:i + n] == matched_tokens:
                    start = indices[i][0]
                    end = indices[i + n - 1][1]
                    return self.processed_text[start:end]
        except (ValueError, IndexError):
            ner_logger.exception('Error getting original text (%s, %s)' % (matched_tokens, self.processed_text))

        return u' '.join(matched_tokens)

    def detect_entity(self, text, **kwargs):
        """
        Detects all textual entities in text that are similar to variants of 'entity_name' stored in the datastore and
        returns two lists of detected text entities and their corresponding original substrings in text respectively.
        Note that datastore stores number of values under a entity_name and each entity_value has its own list of
        variants, whenever a variant is matched sucessfully, the entity_value whose list the variant belongs to,
        is returned. For more information on how data is stored, see Datastore docs.

        Args:
            text (unicode): string to extract textual entities from
            **kwargs: it can be used to send specific arguments in future. for example, fuzziness, previous context.
        Returns:
            tuple:
                list: containing entity value as defined into datastore
                list: containing corresponding original substrings in text

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

        Additionally this function assigns these lists to self.text_entity_values and self.original_texts attributes
        respectively.
        """
        self._process_text(text)

        values, original_texts = self._text_detection_with_variants()

        self.text_entity_values, self.original_texts = values, original_texts

        return self.text_entity_values, self.original_texts

    def _text_detection_with_variants(self):
        """
        This function will normalise the message by breaking it into trigrams, bigrams and unigrams. The generated
        ngrams will be used to create query to retrieve search results from datastore. These results will contain a
        dictionary where key will be variant and value will be entity value this will be further processed to get the
        original text which has been identified and will return the results

        Returns:
             tuple:
                list: containing the detected text entities
                list: containing their corresponding substrings in the original message.
        """
        original_final_list = []
        value_final_list = []
        variants_to_values = collections.OrderedDict()

        _variants_to_values = self.db.get_similar_dictionary(entity_name=self.entity_name,
                                                             text=u' '.join(TOKENIZER.tokenize(self.processed_text)),
                                                             fuzziness_threshold=self._fuzziness,
                                                             search_language_script=self._target_language_script)
        for variant, value in iteritems(_variants_to_values):
            variant = variant.lower()
            if isinstance(variant, bytes):
                variant = variant.decode('utf-8')

            variants_to_values[variant] = value

        variants_list = variants_to_values.keys()

        # Length based ordering, this reorders the results from datastore
        # that are already sorted by some relevance scoring

        exact_matches, fuzzy_variants = [], []
        _text = u' '.join(TOKENIZER.tokenize(self.processed_text))
        for variant in variants_list:
            if u' '.join(TOKENIZER.tokenize(variant)) in _text:
                exact_matches.append(variant)
            else:
                fuzzy_variants.append(variant)

        exact_matches.sort(key=lambda s: len(TOKENIZER.tokenize(s)), reverse=True)
        fuzzy_variants.sort(key=lambda s: len(TOKENIZER.tokenize(s)), reverse=True)
        variants_list = exact_matches + fuzzy_variants

        for variant in variants_list:
            original_text = self._get_entity_substring_from_text(variant, self.processed_text)
            if original_text:
                value_final_list.append(variants_to_values[variant])
                original_final_list.append(original_text)
                _pattern = re.compile(r'\b%s\b' % re.escape(original_text), re.UNICODE)
                self.tagged_text = _pattern.sub(self.tag, self.tagged_text)
                # Instead of dropping completely like in other entities,
                # we replace with tag to avoid matching non contiguous segments
                self.processed_text = _pattern.sub(self.tag, self.processed_text)
        return value_final_list, original_final_list

    def _get_entity_substring_from_text(self, variant, text):
        """
        Checks ngrams of the text for similarity against the variant (can be a ngram) using Levenshtein distance

        Args:
            variant: string, ngram of variant to fuzzy detect in the text using Levenshtein distance
            text: text to detect entities from

        Returns:
            str or unicode: part of the given text that was detected as entity given the variant, None otherwise

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
        variant_tokens = TOKENIZER.tokenize(variant)
        text_tokens = TOKENIZER.tokenize(text)
        original_text_tokens = []
        variant_token_i = 0
        for text_token in text_tokens:
            variant_token = variant_tokens[variant_token_i]

            same = variant_token == text_token
            ft = self._get_fuzziness_threshold_for_token(text_token)
            if same or (len(text_token) > self._min_token_size_for_fuzziness
                        and edit_distance(string1=variant_token,
                                          string2=text_token,
                                          max_distance=ft + 1) <= ft):
                original_text_tokens.append(text_token)
                variant_token_i += 1
                if variant_token_i == len(variant_tokens):
                    return self._get_substring_from_processed_text(original_text_tokens)
            else:
                original_text_tokens = []
                variant_token_i = 0
        return None
