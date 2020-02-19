from __future__ import absolute_import
import numpy as np
from lib.singleton import Singleton
import pickle
from chatbot_ner.config import CRF_EMBEDDINGS_PATH_VOCAB, CRF_EMBEDDINGS_PATH_VECTORS, WORD_EMBEDDING_REMOTE_URL
import requests
import json
from models.crf_v2.constants import TEXT_LIST, CRF_WORD_EMBEDDINGS_LIST
from chatbot_ner.config import ner_logger
import six


class LoadWordEmbeddings(six.with_metaclass(Singleton, object)):
    """
    This method is used to load the word_embeddings into the memory
    """

    def __init__(self):
        """
        This method is used to load the word_embeddings into the memory
        """
        self.vocab, self.word_vectors = LoadWordEmbeddings.load_word_vectors_local()

    @staticmethod
    def load_word_vectors_local():
        """
        Thus function is used to load the word_list and word_vectors from the specified paths.
        Returns:
        vocab (list): word_list present at the specified path.
        word_vectors (numpy.array): word_vectors present at the specified path.
        """
        vocab = []
        word_vectors = np.array([])
        try:
            file_handler = open(CRF_EMBEDDINGS_PATH_VOCAB, 'rb')
            vocab = pickle.load(file_handler)
            file_handler = open(CRF_EMBEDDINGS_PATH_VECTORS, 'rb')
            word_vectors = np.array(pickle.load(file_handler))
        except Exception as e:
            ner_logger.debug('Error in loading local word vectors %s' % e)
        return vocab, word_vectors

    @staticmethod
    def load_word_vectors_remote(sentence_list):
        """
        This method is used to load word_vectors from a remote location
        Args:
            sentence_list (list): List of tokenized texts
            text_list = [['my', 'name', 'is', 'chatbot'], ['how', 'are', 'you']]
        Returns:
            word_vectors (np.ndarray): Numpy array of vectors for the provided text_list
        """
        word_vectors = np.array([])
        try:
            json_dict = {TEXT_LIST: [sentence_list]}
            result = json.loads(requests.get(url=WORD_EMBEDDING_REMOTE_URL, json=json_dict, timeout=120).text)
            word_vectors = result[CRF_WORD_EMBEDDINGS_LIST]
            if word_vectors:
                word_vectors = np.vstack(word_vectors)
        except Exception as e:
            ner_logger.debug('Error in loading remote models %s' % e)
        return word_vectors
