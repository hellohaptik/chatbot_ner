
from django.test import TestCase
from lib.nlp.spacy_utils import SpacyUtils


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
