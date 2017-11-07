import os
from lib.nlp.etc import store_data_in_list
from lib.nlp.lemmatizer import Lemmatizer, WORDNET_LEMMATIZER
from lib.nlp.ngram import Ngram
from lib.nlp.stemmer import Stemmer, PORTER_STEMMER
from lib.nlp.tokenizer import Tokenizer, PRELOADED_NLTK_TOKENIZER
from lib.nlp.regex import Regex
from chatbot_ner.settings import BASE_DIR


stemmer = Stemmer(PORTER_STEMMER)
lemmatizer = Lemmatizer(WORDNET_LEMMATIZER)
tokenizer = Tokenizer(PRELOADED_NLTK_TOKENIZER)


# Creating list of stop words
stop_word_path = os.path.join(BASE_DIR, 'lib', 'nlp', 'data', 'stop_words.csv')  # file containing words to remove
stop_words = store_data_in_list(stop_word_path)

ngram_object = Ngram()

punctuation_removal_list = [(r'[^\w\'\/]', r' '), (r'\'', r'')]
regx_punctuation_removal = Regex(punctuation_removal_list)

