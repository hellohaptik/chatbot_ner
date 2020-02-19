from __future__ import absolute_import
import collections
import string

import six
from six import iteritems

import language_utilities.constant as lang_constant
from chatbot_ner.config import ner_logger
from datastore import DataStore
from lib.nlp.const import TOKENIZER, whitespace_tokenizer
from lib.nlp.levenshtein_distance import edit_distance
from ner_v1.detectors.base_detector import BaseDetector
from ner_constants import ENTITY_VALUE_DICT_KEY
from six.moves import range

try:
    import regex as re

    _re_flags = re.UNICODE | re.V1 | re.WORD

except ImportError:
    import re

    _re_flags = re.UNICODE


class TextDetector(BaseDetector):
    """
    TextDetector detects custom entities in text string by performing similarity searches against a list fetched from
    datastore (elasticsearch) and tags them.

    TextDetector detects text type custom entities that do not adhere to some strict/weak formats which other entities
    like date, time, email, etc do. Examples of such types of entites can be city, food dish name, brand names etc


    Attributes:
        entity_name (str): string by which the detected time entities would
                           be replaced with on calling detect_entity()
        _fuzziness (str or int): If this parameter is str, elasticsearch's
                                 auto is used with low and high term distances. Default low and high term distances
                                 are 3 and 6 for elasticsearch. For this module they are set to 4 and 7 respectively.
                                 In auto mode, if length of term is less than low it must match exactly, if it is
                                 between [low, high) one insert/delete/substitution is allowed, for anything higher
                                 than equal to high, two inserts/deletes/substitutions are allowed
        _min_token_size_for_fuzziness (int): minimum number of letters a word must have to be considered
                                             for calculating edit distance with similar ngrams from the datastore
        tagged_text (str): string with time entities replaced with tag defined by entity_name
        processed_text (str): string with detected text entities removed
        tag (str): entity_name prepended and appended with '__'
    """

    def __init__(self, entity_name=None, source_language_script=lang_constant.ENGLISH_LANG, translation_enabled=False):
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
        self._supported_languages = [
            lang_constant.ENGLISH_LANG,
            lang_constant.HINDI_LANG,
            lang_constant.GUJARATI_LANG,
            lang_constant.HINDI_LANG,
            lang_constant.ENGLISH_LANG,
            lang_constant.GUJARATI_LANG,
            lang_constant.BENGALI_LANG,
            lang_constant.MARATHI_LANG,
            lang_constant.TELEGU_LANG,
            lang_constant.TAMIL_LANG,
            lang_constant.URDU_LANG,
            lang_constant.KANNADA_LANG,
            lang_constant.ORIYA_LANG,
            lang_constant.MALAYALAM_LANG,
            lang_constant.PUNJABI_LANG  # Added temporarily till text detection is ported to v2 api
        ]
        super(TextDetector, self).__init__(source_language_script, translation_enabled)
        self.tagged_text = None
        self.processed_text = None
        self.__texts = []
        self.__tagged_texts = []
        self.__processed_texts = []

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

    def _reset_state(self):
        self.tagged_text = None
        self.processed_text = None
        self.__texts = []
        self.__tagged_texts = []
        self.__processed_texts = []

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

    def _process_text(self, texts):
        self._reset_state()
        for text in texts:
            text = text.lower()
            text = text.decode('utf-8') if isinstance(text, bytes) else text
            self.__texts.append(text)
            # Note: following rules have been disabled because cause problem with generating original text
            # regex_to_process = RegexReplace([(r'[\'\/]', r''), (r'\s+', r' ')])
            # processed_text = self.regx_to_process.text_substitute(processed_text)
            self.__processed_texts.append(u' ' + text + u' ')
            self.__tagged_texts.append(u' ' + text + u' ')

    def _get_substring_from_processed_text(self, text, matched_tokens):
        """
        Get part of original text that was detected as some entity value.

        This method was written to tackle cases when original text contains special characters which are dropped
        during tokenization

        Args:
            matched_tokens (list): list of tokens (usually tokens from fuzzy match results from ES)
                                   to find as a contiguous substring in the processed sentence considering the effects
                                   of tokenizer
            text (string or unicode): sentence from self.processed_text  from where indices of given token will be
                                            given

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

        def _get_tokens_and_indices(txt):
            """
            Args:
                txt (str or unicode): text to get tokens from and indicies of those tokens in the given text

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
            txt = txt.rstrip() + ' __eos__'
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
            tokens, indices = _get_tokens_and_indices(text)
            for i in range(len(tokens) - n + 1):
                if tokens[i:i + n] == matched_tokens:
                    start = indices[i][0]
                    end = indices[i + n - 1][1]
                    return text[start:end]
        except (ValueError, IndexError):
            ner_logger.exception('Error getting original text (%s, %s)' % (matched_tokens, text))

        return u' '.join(matched_tokens)

    def detect_entity_bulk(self, texts, predetected_values=None, **kwargs):
        """
        Detects all textual entities in text that are similar to variants of 'entity_name' stored in the datastore and
        returns two lists of list of detected text entities  and their corresponding original substrings
        for each sentence in text respectively.
        Note that datastore stores number of values under a entity_name and each entity_value has its own list of
        variants, whenever a variant is matched sucessfully, the entity_value whose list the variant belongs to,
        is returned. For more information on how data is stored, see Datastore docs.

        Args:
            texts (list): list of str to extract textual entities from
            predetected_values (list of list of str): results from prior detection.
            **kwargs: it can be used to send specific arguments in future. for example, fuzziness, previous context.
        Returns:
            tuple:
                list or list of dicts: ith item is a list of values output as dictionary with structure
                    {'value': <value here>, ...} which were detected as entity values in texts[i]
                list or list of str: ith item contains corresponding original substrings in texts[i] that were
                    detected as entity values
        Example:
            DataStore().get_entity_dictionary('city')

                Output:
                    {
                        u'Agartala': [u'Agartala'],
                        u'Barnala': [u'Barnala'],
                        ...
                        u'chennai': [u'chennai', u'tamilnadu', u'madras'],
                        u'hyderabad': [u'hyderabad'],
                        u'koramangala': [u'koramangala']
                    }
                text_detection = TextDetector('city')
                list_of_sentences = ['Come to Chennai, TamilNadu,  I will visit Delhi next year',
                                    'I live in Delhi]

                text_detection.detect_entity_bulk(list_of_sentences)
                    Output:
                        (   [
                                [
                                    {'value': u'chennai'},
                                    {'value': u'tamilnadu'},
                                    {value': u'new delhi'},
                                ],
                                [
                                    {'value': u'new delhi'},
                                ]
                            ],
                            [
                                ['chennai', 'tamilnadu', 'delhi'],
                                [delhi]
                            ]
                        )

                text_detection.tagged_text
                    Output:
                        [
                            ' come to __city__, __city__,  i will visit __city__ next year ',
                            ' i live in __city__ '
                        ]

        """
        # For bulk detection predetected_values will be a list of list of str
        predetected_values = predetected_values or []
        self._process_text(texts)
        text_entity_values_list, original_texts_list = self._text_detection_with_variants()

        # itertate over text_entity_values_list, original_texts_list and if predetected_values has any entry
        # for that index use combine_results to merge the results from predetected_values and dictionary detection.
        combined_entity_values, combined_original_texts = [], []
        zipped_iter = six.moves.zip_longest(text_entity_values_list, original_texts_list, predetected_values)
        for i, (values, original_texts, inner_predetected_values) in enumerate(zipped_iter):
            inner_combined_entity_values, inner_combined_original_texts = self.combine_results(
                values=values,
                original_texts=original_texts,
                predetected_values=inner_predetected_values if inner_predetected_values else [])
            combined_entity_values.append(inner_combined_entity_values)
            combined_original_texts.append(inner_combined_original_texts)

        return combined_entity_values, combined_original_texts

    def detect_entity(self, text, predetected_values=None, return_str=False, **kwargs):
        """
        Detects all textual entities in text that are similar to variants of 'entity_name' stored in the datastore and
        returns two lists of detected text entities and their corresponding original substrings in text respectively.
        Note that datastore stores number of values under a entity_name and each entity_value has its own list of
        variants, whenever a variant is matched successfully, the entity_value whose list the variant belongs to,
        is returned. For more information on how data is stored, see Datastore docs.
        Args:
            text (str): string to extract textual entities from
            predetected_values (list of str): prior detection results
            return_str(bool): To call combine results or not.
            **kwargs: it can be used to send specific arguments in future. for example, fuzziness, previous context.
        Returns:
            tuple:
                list: list of dict with detected value against 'value'
                list: list of str containing corresponding original substrings in text
        Example:
            DataStore().get_entity_dictionary('city')
                Output:
                    {
                        u'Agartala': [u'Agartala'],
                        u'Barnala': [u'Barnala'],
                        ...
                        u'chennai': [u'chennai', u'tamilnadu', u'madras'],
                        u'hyderabad': [u'hyderabad'],
                        u'koramangala': [u'koramangala']
                    }
            text_detection = TextDetector('city')
            text_detection.detect_entity('Come to Chennai, TamilNadu,  I will visit Delhi next year')
                Output:
                    ([{'value': u'chennai'}, {'value': u'tamilnadu'}, {value': u'new delhi'}],
                    ['chennai', 'tamilnadu', 'delhi'])
            text_detection.tagged_text
                Output:
                    ' come to __city__, __city__,  i will visit __city__ next year '
        """
        values, texts = [], []
        predetected_values = predetected_values or []

        self._process_text([text])
        text_entity_values, original_texts = self._text_detection_with_variants()

        if text_entity_values and original_texts:
            self.tagged_text = self.__tagged_texts[0]
            self.processed_text = self.__processed_texts[0]
            values, texts = text_entity_values[0], original_texts[0]

        values, texts = self.combine_results(values=values, original_texts=texts,
                                             predetected_values=predetected_values)
        if return_str:
            values = [value_dict[ENTITY_VALUE_DICT_KEY] for value_dict in values]

        return values, texts

    def _text_detection_with_variants(self):
        """
        This function will normalise the message by breaking it into trigrams, bigrams and unigrams. The generated
        ngrams will be used to create query to retrieve search results from datastore. These results will contain a
        dictionary where key will be variant and value will be entity value this will be further processed to get the
        original text which has been identified and will return the results

        Returns:
             tuple:
                list of lists: list of lists containing the detected text entities
                list of lists: list of lists containing their corresponding substrings in the original message.
        """

        original_final_list_ = []
        value_final_list_ = []
        texts = [u' '.join(TOKENIZER.tokenize(processed_text)) for processed_text in self.__processed_texts]

        _variants_to_values_list = self.db.get_similar_dictionary(entity_name=self.entity_name,
                                                                  texts=texts,
                                                                  fuzziness_threshold=self._fuzziness,
                                                                  search_language_script=self._target_language_script)
        for index, _variants_to_values in enumerate(_variants_to_values_list):
            original_final_list = []
            value_final_list = []
            variants_to_values = collections.OrderedDict()
            for variant, value in iteritems(_variants_to_values):
                variant = variant.lower()
                if isinstance(variant, bytes):
                    variant = variant.decode('utf-8')

                variants_to_values[variant] = value
            variants_list = list(variants_to_values.keys())

            # Length based ordering, this reorders the results from datastore
            # that are already sorted by some relevance scoring

            exact_matches, fuzzy_variants = [], []
            _text = texts
            for variant in variants_list:
                if u' '.join(TOKENIZER.tokenize(variant)) in _text[index]:
                    exact_matches.append(variant)
                else:
                    fuzzy_variants.append(variant)
            exact_matches.sort(key=lambda s: len(TOKENIZER.tokenize(s)), reverse=True)
            fuzzy_variants.sort(key=lambda s: len(TOKENIZER.tokenize(s)), reverse=True)
            variants_list = exact_matches + fuzzy_variants

            for variant in variants_list:

                original_text = self._get_entity_substring_from_text(self.__processed_texts[index], variant)
                if original_text:
                    value_final_list.append(variants_to_values[variant])
                    original_final_list.append(original_text)

                    boundary_punct_pattern = re.compile(r'(^[{0}]+)|([{0}]+$)'.format(re.escape(string.punctuation)))
                    original_text_ = boundary_punct_pattern.sub("", original_text)

                    _pattern = re.compile(r'\b%s\b' % re.escape(original_text_), flags=_re_flags)
                    self.__tagged_texts[index] = _pattern.sub(self.tag, self.__tagged_texts[index])
                    # Instead of dropping completely like in other entities,
                    # we replace with tag to avoid matching non contiguous segments
                    self.__processed_texts[index] = _pattern.sub(self.tag, self.__processed_texts[index])
            value_final_list_.append(value_final_list)
            original_final_list_.append(original_final_list)

        return value_final_list_, original_final_list_

    def _get_entity_substring_from_text(self, text, variant):
        """
        Check ngrams of the text for similarity against the variant (can be a ngram) using Levenshtein distance
        and return the closest substring in the text that matches the variant

        Args:
            variant(str or unicode): string, ngram of variant to fuzzy detect in the text using Levenshtein distance
            text(str or unicode): sentence from self.processed on which detection is being done

        Returns:
            str or unicode or None: part of the given text that was detected as entity given the variant,
                                    None otherwise

        Example:
            >>> text_detector = TextDetector('city')
            >>> text = 'Come to Chennai, Tamil Nadu,  I will visit Delehi next year'.lower()
            >>> text_detector.detect_entity(text)
            >>> text_detector._get_entity_substring_from_text(variant='chennai')
            'chennai'
            >>> text_detector._get_entity_substring_from_text(variant='delhi')
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
                    return self._get_substring_from_processed_text(text, original_text_tokens)
            else:
                original_text_tokens = []
                variant_token_i = 0
        return None
