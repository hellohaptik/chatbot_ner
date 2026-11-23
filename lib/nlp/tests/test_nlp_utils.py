from __future__ import absolute_import
import os
import tempfile
import unittest

try:
    from django.test import TestCase
except ImportError:
    from unittest import TestCase

from lib.nlp.etc import filter_list, store_data_in_list
from lib.nlp.regexreplace import RegexReplace
from lib.nlp.ngram import Ngram

try:
    import spacy
    from lib.nlp.spacy_utils import SpacyUtils
    SPACY_AVAILABLE = True
except (ImportError, Exception):
    SPACY_AVAILABLE = False


class NLPUtilsTest(TestCase):
    def test_filter_list(self):
        output = filter_list(['hi', 'hello', 'bye'], ['hi', 'bye'])
        self.assertEqual(output, ['hello'])

        # Edge cases: empty remove_elements or empty list
        self.assertEqual(filter_list(['a', 'b'], []), ['a', 'b'])
        self.assertEqual(filter_list([], ['a', 'b']), [])

    def test_store_data_in_list(self):
        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8') as f:
            f.write("Apple\n\nBanana\n  \nCherry\n")
            temp_path = f.name

        try:
            words = store_data_in_list(temp_path, lower_case=True)
            self.assertEqual(words, ['apple', 'banana', 'cherry'])

            words_orig = store_data_in_list(temp_path, lower_case=False)
            self.assertEqual(words_orig, ['Apple', 'Banana', 'Cherry'])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_regex_replace(self):
        pattern_list = [(r'[\,\?]', ''), (r'\bu\b', 'you')]
        regex = RegexReplace(pattern_list)
        output = regex.text_substitute('Hey, where are u going?')
        self.assertEqual(output, 'Hey where are you going')

        # Test empty string / None handling
        self.assertEqual(regex.text_substitute(''), '')
        self.assertIsNone(regex.text_substitute(None))

    def test_ngram_list(self):
        word_list = ['hi', 'hello', 'how', 'are', 'you', 'hi']
        stop_word_list = ['hi', 'you']
        output = Ngram.ngram_list(2, word_list, stop_word_list)
        self.assertEqual(output, ['hi hello', 'hello how', 'how are', 'are you'])

        # Test with empty stop_word_list
        all_output = Ngram.ngram_list(2, ['hello', 'world'], None)
        self.assertEqual(all_output, ['hello world'])


@unittest.skipUnless(SPACY_AVAILABLE, "spacy is not available in environment")
class SpacyUtilsTest(TestCase):
    def setUp(self):
        self.spacy_utils = SpacyUtils()

    def test_spacy_utils(self):
        output = self.spacy_utils.tag(text='This is a test for tokenizer class', language='en')
        expected_output = [('This', 'DET'),
                           ('is', 'AUX'),
                           ('a', 'DET'),
                           ('test', 'NOUN'),
                           ('for', 'ADP'),
                           ('tokenizer', 'NOUN'),
                           ('class', 'NOUN')]
        self.assertEqual(output, expected_output, 'Unexpected output from spacy tagger')

        tokenizer_out = self.spacy_utils.tokenize(text='This is a test for tokenizer class', language='en')
        expected_tokenizer_output = ['This', 'is', 'a', 'test', 'for', 'tokenizer', 'class']
        self.assertEqual(tokenizer_out, expected_tokenizer_output, 'Unexpected output from spacy tokenizer')

        english_model_loaded = self.spacy_utils.spacy_language_to_model['en']['model'] is not None
        english_tokenizer_loaded = self.spacy_utils.tokenizers['en'] is not None
        self.assertTrue(english_tokenizer_loaded, 'English model not loaded')
        self.assertTrue(english_model_loaded, 'English tokenizer not loaded')
