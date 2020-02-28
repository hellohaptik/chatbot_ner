from __future__ import absolute_import
import os
from lib.nlp.etc import store_data_in_list
from lib.nlp.ngram import Ngram
from lib.nlp.stemmer import Stemmer, PORTER_STEMMER
from lib.nlp.tokenizer import Tokenizer, PRELOADED_NLTK_TOKENIZER, LUCENE_STANDARD_TOKENIZER, WHITESPACE_TOKENIZER
from lib.nlp.regexreplace import RegexReplace
from chatbot_ner.settings import BASE_DIR


stemmer = Stemmer(PORTER_STEMMER)
nltk_tokenizer = Tokenizer(PRELOADED_NLTK_TOKENIZER)
lucene_tokenizer = Tokenizer(LUCENE_STANDARD_TOKENIZER)
whitespace_tokenizer = Tokenizer(WHITESPACE_TOKENIZER)
# Currently we support only elasticsearch as datastore engine, so it safe to use lucene tokenizer as default
# This could change in future
TOKENIZER = lucene_tokenizer

# Creating list of stop words
stop_word_path = os.path.join(BASE_DIR, 'lib', 'nlp', 'data', 'stop_words.csv')  # file containing words to remove
stop_words = store_data_in_list(stop_word_path)

ngram_object = Ngram()

punctuation_removal_list = [(r'[^\w\'\/]', r' '), (r'\'', r'')]
regx_punctuation_removal = RegexReplace(punctuation_removal_list)
