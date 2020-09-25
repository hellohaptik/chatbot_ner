from __future__ import absolute_import

import collections
import string

import six
from six import iteritems

import language_utilities.constant as lang_constant
from chatbot_ner.config import ner_logger

from ner_v2.detectors.textual.elastic_search import ElasticSearchDataStore

from lib.nlp.const import TOKENIZER, whitespace_tokenizer
from lib.nlp.levenshtein_distance import edit_distance
from six.moves import range

from ner_constants import (FROM_STRUCTURE_VALUE_VERIFIED, FROM_STRUCTURE_VALUE_NOT_VERIFIED,
                           FROM_MESSAGE, FROM_FALLBACK_VALUE, ORIGINAL_TEXT, ENTITY_VALUE,
                           DETECTION_METHOD, DETECTION_LANGUAGE, ENTITY_VALUE_DICT_KEY)

from ner_v1.constant import DATASTORE_VERIFIED, MODEL_VERIFIED

from language_utilities.constant import ENGLISH_LANG

try:
    import regex as re

    _re_flags = re.UNICODE | re.V1 | re.WORD

except ImportError:
    import re

    _re_flags = re.UNICODE


class TextDetector(object):
    """
    TextDetector detects multiple custom entities in text string by performing similarity searches against a list
    fetched from elasticsearch datastore.

    TextDetector detects text type custom entities that do not adhere to some strict/weak formats which other entities
    like date, time, email, etc do. Examples of such types of entites can be city, food dish name, brand names etc

    Attributes:
        entities_dict (dict): dict with details of entities to be dected. Each entites will contailn:
                    `value`: name of the entity

                    `_fuzziness` (str or int): If this parameter is str, elasticsearch's
                             auto is used with low and high term distances. Default low and high
                            term distances are 3 and 6 for elasticsearch. For this module they are
                            set to 4 and 7 respectively.

                            In auto mode, if length of term is less than low it must match exactly,
                              if it is between [low, high) one insert/delete/substitution is allowed,
                              for anything higher than equal to high, two inserts/deletes/substitutions
                               are allowed

                    `_min_token_size_for_fuzziness (int)`: minimum number of letters a word must
                                have to be considered for calculating edit distance with similar
                                ngrams from the datastore
        processed_text (str): string with detected text entities removed
    """

    def __init__(self, entity_dict=None,
                 source_language_script=lang_constant.ENGLISH_LANG,
                 target_language_script=ENGLISH_LANG):

        # define entities to detect
        self.entities_dict = entity_dict

        self.processed_text = None
        self.__texts = []
        self.__processed_texts = []

        # defaults for auto mode
        self._fuzziness = "4,7"

        self._fuzziness_lo, self._fuzziness_hi = 4, 7
        self._min_token_size_for_fuzziness = self._fuzziness_lo

        # defaults for non-auto mode
        self._min_token_size_for_fuzziness = 4

        # define data store and target languages
        self.esdb = ElasticSearchDataStore()

        self._source_language_script = source_language_script
        self._target_language_script = target_language_script

        # set default ES query fuzziness as `auto`
        self._es_fuzziness = "auto"

    def _reset_state(self):
        """
        Reset all the intermediary states of detection class.
        """
        self.processed_text = None
        self.__texts = []
        self.__processed_texts = []

    def set_fuzziness_low_high_threshold(self, fuzziness):
        """
        Sets the fuzziness thresholds high and low threshold for similarity searches.
        The fuzziness threshold corresponds to the maximum Levenshtein's distance
        allowed during similarity matching
        Args:

            fuzziness (iterable or int): If this parameter is int, elasticsearch's auto is used with
            low and high term distances.

            Please make sure the iterable has only two integers like (4, 7).
            This will generate "auto:4,7"

            Note that this also sets _min_token_size_for_fuzziness to first value of the iterable
            If this argument is int, elasticsearch will set fuzziness as min(2, fuzziness)
        """
        try:
            iter(fuzziness)
            if len(fuzziness) == 3:
                lo, hi = fuzziness.split(",")
                self._fuzziness_lo, self._fuzziness_hi = int(lo), int(hi)
                self._min_token_size_for_fuzziness = self._fuzziness_lo
        except TypeError:
            ner_logger.exception(f"Fuzziness not in correct format, got {fuzziness}")
            raise TypeError('Fuzziness has to be an iterable of length 2 ')

    def _get_fuzziness_threshold_for_token(self, token):
        """
        Return dynamic fuzziness threshold for damerau-levenshtein check based on length of token if elasticsearch
        fuzziness was set to auto mode

        Args:
            token (str or unicode): the string to calculate fuzziness threshold for
            fuzziness (int): fuzziness value provided

        Returns:
            int: fuzziness threshold for ngram matching on elastic search results
        """

        if len(token) < self._fuzziness_lo:
            return 0  # strict match
        elif len(token) >= self._fuzziness_hi:
            return 2  # Allow upto two inserts/deletes and one substitution
        else:
            return 1  # lo <= len < hi Allow only insert/delete

    def set_min_token_size_for_levenshtein(self, min_size):
        """
        Sets the minimum number of letters a word must have to be considered for calculating edit
        distance with similar ngrams from the datastore

        Args:
            min_size: integer, maximum allowed Levenshtein's distance from the word/phrase being tested for
            entity match
        """
        self._min_token_size_for_fuzziness = min_size

    def _process_text(self, texts):
        """
        This will pre-process texts for detection
        Args:
            texts: list of message strings
        """
        self._reset_state()
        for text in texts:
            text = text.lower()
            text = text.decode('utf-8') if isinstance(text, bytes) else text
            self.__texts.append(text)
            self.__processed_texts.append(u' ' + text + u' ')

    @staticmethod
    def _get_substring_from_processed_text(text, matched_tokens):
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

        Notice that & is dropped during tokenization but when finding original text,
        we recover it from processed text
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

    def _process_es_result(self, entity_result, entity_list, text,
                           processed_text):
        """
        Process ElasticSearch results which will contain list of dictionary where for
        each item key will be variant and value will be entity value this will be
        processed to get the original text which has been identified and will
        return the results dictionary for each entity detected

        Args:
            entity_result: ES result for entity
            entity_list: List of entity for which ES query ran
            text: original text message
            processed_text: processed text on which detection ran

        Returns:
            result_dict: dictionary with detected text and original text for
                         each entity

        """
        result_dict = {}

        for each_key in entity_list:
            original_final_list = []
            value_final_list = []
            variants_to_values = collections.OrderedDict()
            original_final_list_ = []
            value_final_list_ = []
            _processed_text = processed_text

            _variants_to_values = entity_result.get(each_key, [])

            if not _variants_to_values:
                result_dict[each_key] = ([], [])
                continue

            for variant, value in iteritems(_variants_to_values):
                variant = variant.lower()
                if isinstance(variant, bytes):
                    variant = variant.decode('utf-8')

                variants_to_values[variant] = value
            variants_list = list(variants_to_values.keys())

            exact_matches, fuzzy_variants = [], []

            for variant in variants_list:
                if u' '.join(TOKENIZER.tokenize(variant)) in text:
                    exact_matches.append(variant)
                else:
                    fuzzy_variants.append(variant)

            exact_matches.sort(key=lambda s: len(TOKENIZER.tokenize(s)), reverse=True)
            fuzzy_variants.sort(key=lambda s: len(TOKENIZER.tokenize(s)), reverse=True)

            variants_list = exact_matches + fuzzy_variants
            for variant in variants_list:

                original_text = self._get_entity_substring_from_text(_processed_text,
                                                                     variant, each_key)
                if original_text:
                    value_final_list.append(variants_to_values[variant])
                    original_final_list.append(original_text)
                    boundary_punct_pattern = re.compile(
                        r'(^[{0}]+)|([{0}]+$)'.format(re.escape(string.punctuation)))
                    original_text_ = boundary_punct_pattern.sub("", original_text)

                    _pattern = re.compile(r'\b%s\b' % re.escape(original_text_), flags=_re_flags)
                    tag = '__' + each_key + '__'
                    _processed_text = _pattern.sub(tag, _processed_text)

            value_final_list_.append(value_final_list)
            original_final_list_.append(original_final_list)

            result_dict[each_key] = (value_final_list_, original_final_list_)

        return result_dict

    def _get_single_text_detection_with_variants(self, message):
        """
        This function will normalise the message by breaking it into trigrams,
        bigrams and unigrams.

        The generated ngrams will be used to create query to retrieve search results from datastore.

        These results will contain list of dictionary where for each item key will be variant and
        value will be entity value this will be further processed to get the original text which has
        been identified and will return the results

        Returns:
            list of dict: list of dict for each message with key as entity name
                            containing the detected text entities and original message.
        """

        entities_dict = self.entities_dict
        es_entity_list = []
        structured_value_entities_list = []
        text_value_entities_list = []
        texts = []

        for each_entity, value in entities_dict.items():
            structured_value = value.get('structured_value')

            if structured_value:
                # add entity list and text for each structured entity
                # for ES query
                es_entity_list.append([each_entity])
                structured_value_entities_list.append(each_entity)
                texts.append(structured_value)
            else:
                text_value_entities_list.append(each_entity)

        if text_value_entities_list:
            # add entity list and text for all other textual
            # entity for ES query
            es_entity_list.append(text_value_entities_list)
            texts.append(message)

        # pre-process text
        self._process_text(texts)
        texts = [u' '.join(TOKENIZER.tokenize(processed_text)) for
                 processed_text in self.__processed_texts]

        # fetch ES datastore search result
        es_results = self.esdb.get_multi_entity_results(entities=es_entity_list,
                                                        texts=texts,
                                                        fuzziness_threshold=self._es_fuzziness,
                                                        search_language_script=self._target_language_script
                                                        )

        final_list = []
        result_dict = {}

        for index, entity_result in enumerate(es_results):
            processed_text = self.__processed_texts[index]
            text = texts[index]
            entity_list = es_entity_list[index]
            result_dict.update(self._process_es_result(entity_result=entity_result,
                                                       entity_list=entity_list,
                                                       text=text, processed_text=processed_text))

        final_list.append(result_dict)

        return final_list

    def _get_bulk_text_detection_with_variants(self, messages):
        """
        This function will normalise the message by breaking it into trigrams, bigrams and unigrams.
        The generated ngrams will be used to create query to retrieve search results from datastore.
        These results will contain list of dictionary where for each item key will be variant and
        value will be entity value this will be further processed to get the original text which has
        been identified and will return the results

        Args:
            messages (list of str): list of message for which detection needs to be perform

        Returns:
         tuple:
            list of lists: list of dict for each message with key as entity name
                            containing the detected text entities and original message.
        """

        self._process_text(messages)

        texts = [u' '.join(TOKENIZER.tokenize(processed_text)) for
                 processed_text in self.__processed_texts]

        entity_list = list(self.entities_dict)

        # entity list for ES search should be list of entities
        # for all list of texts
        es_entity_list = [entity_list]
        es_texts = [texts]

        # fetch ES datastore search result
        es_results = self.esdb.get_multi_entity_results(entities=es_entity_list,
                                                        texts=es_texts,
                                                        fuzziness_threshold=self._es_fuzziness,
                                                        search_language_script=self._target_language_script
                                                        )

        final_list = []

        for index, entity_result in enumerate(es_results):
            processed_text = self.__processed_texts[index]
            text = texts[index]
            result_list = self._process_es_result(entity_result=entity_result,
                                                  entity_list=entity_list,
                                                  text=text, processed_text=processed_text)
            final_list.append(result_list)

        return final_list

    def _get_entity_substring_from_text(self, text, variant, entity_name):
        """
            Check ngrams of the text for similarity against the variant (can be a ngram) using Levenshtein distance
            and return the closest substring in the text that matches the variant.
            For each entity fuziness and min_token_size_for_fuzziness is used from the entity details.
            Args:
              variant(str or unicode): string, ngram of variant to fuzzy detect in the text using
                                       Levenshtein distance
              text(str or unicode): sentence from self.processed on which detection is being done
              entity_name (str): name of the entity to get fuzziness and min_token_lenght value
            Returns:
              str or unicode or None: part of the given text that was detected as entity given the variant,
                                      None otherwise
            Example:
              >>> text_detector = TextDetector(entity_dict={'city':{})
              >>> text = 'Come to Chennai, Tamil Nadu,  I will visit Delehi next year'.lower()
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

            # get fuzziness and min_token_size_for_fuziness value from entity dict
            entity_dict = self.entities_dict.get(entity_name, {})

            # get fuzziness from entity if not set default
            fuzziness = entity_dict.get('fuzziness') or self._fuzziness

            self.set_fuzziness_low_high_threshold(fuzziness)

            min_token_size_for_fuzziness = entity_dict.get('min_token_len_fuzziness')

            if not min_token_size_for_fuzziness:
                min_token_size_for_fuzziness = self._min_token_size_for_fuzziness

            ft = self._get_fuzziness_threshold_for_token(token=text_token)

            # set substitution cost to one
            if same or (len(text_token) > min_token_size_for_fuzziness
                        and edit_distance(string1=variant_token,
                                          string2=text_token,
                                          substitution_cost=1,
                                          max_distance=ft + 1) <= ft):
                original_text_tokens.append(text_token)
                variant_token_i += 1
                if variant_token_i == len(variant_tokens):
                    return self._get_substring_from_processed_text(text, original_text_tokens)
            else:
                original_text_tokens = []
                variant_token_i = 0
        return None

    @staticmethod
    def _add_verification_source(values, verification_source_dict):
        text_entity_verified_values = []
        for text_entity_value in values:
            text_entity_dict = {ENTITY_VALUE_DICT_KEY: text_entity_value}
            text_entity_dict.update(verification_source_dict)
            text_entity_verified_values.append(text_entity_dict)
        return text_entity_verified_values

    def combine_results(self, values, original_texts, predetected_values):
        """
        This method is used to combine the results provided by the datastore search and the
        crf_model if trained.
        Args:
            values (list): List of values detected by datastore
            original_texts (list): List of original texts present in the texts for which value shave been
                                   detected
            predetected_values (list): Entities detected by the models like crf etc.
        Returns:
            combined_values (list): List of dicts each dict consisting of the entity value and additionally
                                    the keys for the datastore and crf model detection
            combined_original_texts (list): List of original texts detected by the datastore and the crf model.
        """
        unprocessed_crf_original_texts = []

        combined_values = self._add_verification_source(
            values=values, verification_source_dict={DATASTORE_VERIFIED: True, MODEL_VERIFIED: False}
        )
        combined_original_texts = original_texts

        for i in range(len(predetected_values)):
            match = False
            for j in range(len(original_texts)):
                if predetected_values[i].lower() == original_texts[j]:
                    combined_values[j][MODEL_VERIFIED] = True
                    match = True
                    break
                elif re.findall(r'\b%s\b' % re.escape(predetected_values[i]), original_texts[j]):
                    # If predetected value is a substring of some value detected by datastore,
                    # skip it from output
                    match = True
                    break
            if not match:
                unprocessed_crf_original_texts.append(predetected_values[i])

        unprocessed_crf_original_texts_verified = self._add_verification_source(
            values=unprocessed_crf_original_texts,
            verification_source_dict={DATASTORE_VERIFIED: False, MODEL_VERIFIED: True}
        )

        combined_values.extend(unprocessed_crf_original_texts_verified)
        combined_original_texts.extend(unprocessed_crf_original_texts)

        return combined_values, combined_original_texts

    def detect(self, message=None, **kwargs):
        """
        This method will detect all textual entities over the single message.

        If structured value is present for any given entity it will be preferred
        over message and a new ES query is added with text as structured value.

        After detection it will combine the result and outputs list of dictionary
        for all the entities detected over message

        Args:
            message (str): message on which textual entities needs to be detected
            **kwargs: other keyword arguments if required

        Returns:
            List of dict of all the entities with detected values of textual entites

        Examples:

            entity_dict = {
                            'city': {'structured_value': None, 'fallback_value': None},
                            'restaurant': {'structured_value': None, 'fallback_value': None},
                            'brand' : {'structured_value': 'Nike', 'fallback_value': None},
                            }

            text_detection = TextDetector(entity_dict)

            text_detection.detect('Buy ticket to Chennai from Mumbai')

            output:
                  [ {
                    'city': [
                                {'entity_value': {'value': 'Mumbai',
                                                'datastore_verified': True,
                                                'model_verified': False},
                                'detection': 'message',
                                'original_text': 'Mumbai',
                                'language': 'en'},

                                {'entity_value': {'value': 'Chennai',
                                                'datastore_verified': True,
                                                'model_verified': False},
                                'detection': 'message',
                                'original_text': 'Chennai',
                                'language': 'en'}
                            ],
                    'restaurant': [],
                    'brand': [
                                {'entity_value': {'value': 'Nike',
                                                'datastore_verified': True,
                                                'model_verified': False},
                                "detection": "structure_value_verified",
                                'original_text': 'Nike',
                                'language': 'en'}]
                    }]
        """

        res_list = self._get_single_text_detection_with_variants(message)
        data_list = []

        for index, res in enumerate(res_list):
            entities = {}

            for entity, value in res.items():
                entities[entity] = []
                values, texts = [], []
                text_entity_values, original_texts = value
                entity_dict = self.entities_dict.get(entity, {})

                # get structured value from entity dict
                structured_value = entity_dict.get('structured_value')

                # get predetected value list from entity dict
                predetected_values = entity_dict.get('predetected_values')

                # get predetected value for message from index
                if predetected_values:
                    _predetected_value = predetected_values[index]
                else:
                    _predetected_value = []

                # get fallback value from entity dict
                fallback_value = entity_dict.get('fallback_value')

                if text_entity_values and original_texts:
                    values, texts = text_entity_values[0], original_texts[0]

                entity_list, original_text_list = self.combine_results(values=values, original_texts=texts,
                                                                       predetected_values=_predetected_value)

                if structured_value:
                    if entity_list:
                        value, method, original_text = entity_list, FROM_STRUCTURE_VALUE_VERIFIED, original_text_list
                    else:
                        value, method, original_text = [structured_value], FROM_STRUCTURE_VALUE_NOT_VERIFIED, \
                                                       [structured_value]
                elif entity_list:
                    value, method, original_text = entity_list, FROM_MESSAGE, original_text_list
                elif fallback_value:
                    value, method, original_text = [fallback_value], FROM_FALLBACK_VALUE, [fallback_value]
                else:
                    continue

                out = self.output_entity_dict_list(entity_value_list=value, original_text_list=original_text,
                                                   detection_method=method,
                                                   detection_language=self._target_language_script)

                entities[entity] = out
            data_list.append(entities)

        return data_list

    def detect_bulk(self, messages=None, **kwargs):
        """
            This method will detect all textual entities over the multiple message.
            After detection it will combine the result and outputs list of dictionary
            for all the entities detected over message

            Args:

                messages (list of str): list of message for which detection needs to be perform
                **kwargs: other keyword arguments if required

            Returns:
                List of dict of all the entities with detected values of textual entites


            example:

            entity_dict = {
                            'city': {'fallback_value': 'Mumbai', 'use_fallback': False},
                            'restaurant': {'fallback_value': None, 'use_fallback': False}
                            }

            text_detection = TextDetector(entity_dict)
            text_detection.detect(['Buy ticket to Chennai from Mumbai',
                                    'I want to eat at dominoes'])

            output:
                  [ {
                    'city': [
                                {'entity_value': {'value': 'Mumbai',
                                                'datastore_verified': True,
                                                'model_verified': False},
                                'detection': 'message',
                                'original_text': 'Mumbai',
                                'language': 'en'},
                                {'entity_value': {'value': 'Chennai',
                                                'datastore_verified': True,
                                                'model_verified': False},
                                'detection': 'message',
                                'original_text': 'Chennai',
                                'language': 'en'}
                            ],
                    'restaurant': []},
                    {
                    'city': [],
                    'restaurant': [
                                {'entity_value': {'value': 'Domminoe's Pizza',
                                                'datastore_verified': True,
                                                'model_verified': False},
                                'detection': 'message',
                                'original_text': 'dominoes',
                                'language': 'en'}
                            ]
                    ]
        """

        res_list = self._get_bulk_text_detection_with_variants(messages)
        data_list = []

        for index, res in enumerate(res_list):
            entities = {}
            for entity, value in res.items():
                entities[entity] = []
                values, texts = [], []
                # get predetected value from entity dict
                entity_dict = self.entities_dict.get(entity, {})
                predetected_values = entity_dict.get('predetected_values')

                # get predetected value for message from index
                if predetected_values:
                    _predetected_value = predetected_values[index]
                else:
                    _predetected_value = []

                # get fallback value from entity dict
                fallback_value = entity_dict.get('fallback_value')

                text_entity_values, original_texts = value
                if text_entity_values and original_texts:
                    values, texts = text_entity_values[0], original_texts[0]

                entity_list, original_text_list = self.combine_results(values=values, original_texts=texts,
                                                                       predetected_values=_predetected_value)

                if entity_list:
                    value, method, original_text = entity_list, FROM_MESSAGE, original_text_list
                elif fallback_value:
                    value, method, original_text = [fallback_value], FROM_FALLBACK_VALUE, [fallback_value]
                else:
                    continue

                out = self.output_entity_dict_list(entity_value_list=value, original_text_list=original_text,
                                                   detection_method=method,
                                                   detection_language=self._target_language_script)

                entities[entity] = out
            data_list.append(entities)

        return data_list

    @staticmethod
    def output_entity_dict_list(entity_value_list, original_text_list, detection_method=None,
                                detection_method_list=None, detection_language=ENGLISH_LANG):
        """
            Format detected entity values for bulk detection

            Args:

            entity_values_list (list of lists): containing list of entity values which are identified from given
                                                detection logic
            original_texts_list (list of lists): containing list original values or actual values from
                                                messages which are identified
            detection_method (str, optional): how the entity was detected
                                              i.e. whether from message, structured_value
                                                   or fallback, verified from model or not.
                                              defaults to None
            detection_method_list(list, optional): list containing how each entity was detected in the entity_value
                                                list.If provided, this argument will be used over detection method
                                                defaults to None
            detection_language(str): ISO 639 code for language in which entity is detected

            Returns:

            list of lists of dict: list of lists containing dictionaries, each containing entity_value,
                                    original_text and detection;
                                    entity_value is in itself a dict with its keys varying from entity to entity
            Example Output:
            [
                [
                    {
                        "entity_value": entity_value_1,
                        "detection": detection_method,
                        "original_text": original_text_1
                    },
                    {
                        "entity_value": entity_value_2,
                        "detection": detection_method,
                        "original_text": original_text_2
                    }

                ],
                [
                    {
                        "entity_value": entity_value,
                        "detection": detection_method,
                        "original_text": original_text
                    }
                ]
            ]
        """
        if detection_method_list is None:
            detection_method_list = []
        if entity_value_list is None:
            entity_value_list = []

        entity_list = []
        for i, entity_value in enumerate(entity_value_list):
            if type(entity_value) in [str, six.text_type]:
                entity_value = {
                    ENTITY_VALUE_DICT_KEY: entity_value
                }
            method = detection_method_list[i] if detection_method_list else detection_method
            entity_list.append(
                {
                    ENTITY_VALUE: entity_value,
                    DETECTION_METHOD: method,
                    ORIGINAL_TEXT: original_text_list[i],
                    DETECTION_LANGUAGE: detection_language
                }
            )
        return entity_list
