from __future__ import absolute_import
import numpy as np
from lib.nlp.pos import POS
import re
from lib.nlp.tokenizer import Tokenizer, NLTK_TOKENIZER
from models.crf_v2.load_word_embeddings import LoadWordEmbeddings
from chatbot_ner.config import ner_logger
from models.crf_v2.constants import SENTENCE_LIST, CRF_WORD_EMBEDDINGS, CRF_WORD_VEC_FEATURE, CRF_B_LABEL,\
    CRF_B_TAG, CRF_I_LABEL, CRF_I_TAG, CRF_POS_TAGS, CRF_LABELS, CRF_O_LABEL, CRF_BOS, CRF_EOS
from six.moves import range
from six.moves import zip


class CrfPreprocessData(object):
    """
    This class is used to pre_process_data for the Crf model.
    """
    @staticmethod
    def get_text_entity_list(text, entities):
        """
        This function takes input as the text and entities present in the text and processes
        them to generate processed tokens along with their respective IOB labels.
        Args:
            text (str): The text on which NER task has to be performed.
            entities (list): List of entities present in the text.

        Returns:
            processed_data (list): Returns a list of tuples where each tuple is of the form (token, label)

        Example:
            text_list ='book a flight from Mumbai to Delhi'
            entity_list = ['Mumbai', 'Delhi']
            get_text_entity_list(text, entity_list)
            >> ['book', 'a', 'flight', 'from', 'Mumbai', 'to', 'Delhi'],
                ['O', 'O', 'O', 'O', 'B', 'O', 'B']
        """

        word_tokenize = Tokenizer(tokenizer_selected=NLTK_TOKENIZER)
        entities.sort(key=lambda s: len(word_tokenize.tokenize(s)), reverse=True)
        tokenized_original_text = word_tokenize.tokenize(text)

        for entity in entities:
            text = re.sub(r'\b%s\b' % entity, CrfPreprocessData.iob_prefixes(entity, word_tokenize), text)

        tokenized_text = word_tokenize.tokenize(text)

        labels = [CRF_B_LABEL if CRF_B_TAG in tokenized_text[i]
                  else CRF_I_LABEL if CRF_I_TAG in tokenized_text[i]
                  else CRF_O_LABEL for i in range(len(tokenized_original_text))]

        return tokenized_original_text, labels

    @staticmethod
    def iob_prefixes(entity_value, word_tokenize):
        """
        This entity takes the input as the entity and returns the entity with its respective
        IOB-prefixes
        Args:
            entity_value (str): Entity for which IOB prefixing is required.
            word_tokenize (Tokenizer): Tokenizer for separatun g
        Returns:
            iob_entities (str): IOB prefixed entity_values
        Example:
            For city entity
            entity_value = ['New York']
            iob_prefixes(entity_value)
            >> 'B_city_New I_city_York'
        """
        iob_entities = ' '.join([CRF_B_TAG + token_ if i_ == 0 else CRF_I_TAG + token_ for i_, token_
                                 in enumerate(word_tokenize.tokenize(entity_value))])
        return iob_entities

    @staticmethod
    def word_embeddings(processed_pos_tag_data, vocab, word_vectors):
        """
        This method is used to add word embeddings to the set of features.
        Args:
            processed_pos_tag_data :
            vocab (list): word_list consisting of words present in the word embeddings
            word_vectors (np.array): word_vectors present in th word embeddings
        Returns:
            sentence (list): List of word embeddings for the text provided
        """
        word_embeddings = []
        for token in processed_pos_tag_data:
            word_vec = np.zeros([word_vectors.shape[1]])
            if token.lower() in vocab:
                word_vec = word_vectors[vocab.index(token.lower())]
            word_embeddings.append(word_vec)
        return word_embeddings

    @staticmethod
    def pre_process_text(sentence_list, entity_list):
        """
        This method is used to call pre_process_text for every text_list and entity_list
        Args:
            sentence_list (list): List of text on which NER has to be performed
            entity_list (list): List of entities present in text_list for every text occurrence.
        Returns:
            processed_list (dict): Dict consisting of the keys text_list and labels
        Examples:
            For city entity

            text_list =['book a flight from Mumbai to Delhi', 'Book a flight to Pune']
            entity_list = [['Mumbai', 'Delhi'], ['Pune']]

            pre_process_text(text_list, entity_list)

            >> {
            'labels': [['O', 'O', 'O', 'O', 'B', 'O', 'B'], ['O', 'O', 'O', 'O', 'B']],

            'text_list': [['book', 'a', 'flight', 'from', 'Mumbai', 'to', 'Delhi'],
                         ['Book', 'a', 'flight', 'to', 'Pune']]}
        """

        processed_list = {SENTENCE_LIST: [],
                          CRF_LABELS: []}

        for text, entities in zip(sentence_list, entity_list):
            tokenzied_text, labels = CrfPreprocessData.get_text_entity_list(text, entities)
            processed_list[SENTENCE_LIST].append(tokenzied_text)
            processed_list[CRF_LABELS].append(labels)
        return processed_list

    @staticmethod
    def get_pos_tagged_dict(docs):
        """
        This method is used to apply pos_tags to every token
        Args:
            docs (dict): List of tuples consisting of the token and label in (token, label) form.
        Returns:
            data (dict): This method assigns pos_tags to the tokens
        Example:
            For city entity
            docs = {
            'labels': [['O', 'O', 'O', 'O', 'B', 'O', 'B'], ['O', 'O', 'O', 'O', 'B']],

            'text_list': [['book', 'a', 'flight', 'from', 'Mumbai', 'to', 'Delhi'],
                        ['Book', 'a', 'flight', 'to', 'Pune']]}

            pos_tag(docs)

            >> {

             'labels': [['O', 'O', 'O', 'O', 'B', 'O', 'B'], ['O', 'O', 'O', 'O', 'B']],

             'pos_tags': [['NN', 'DT', 'NN', 'IN', 'NNP', 'TO', 'VB'],
                         ['VB', 'DT', 'NN', 'TO', 'VB']],

             'text_list': [['book', 'a', 'flight', 'from', 'Mumbai', 'to', 'Delhi'],
                          ['Book', 'a', 'flight', 'to', 'Pune']]

                }
        """
        docs[CRF_POS_TAGS] = []
        pos_tagger = POS()
        for text in docs[SENTENCE_LIST]:
            docs[CRF_POS_TAGS].append([tag[1] for tag in pos_tagger.tagger.tag(text)])

        return docs

    @staticmethod
    def convert_word_vector_to_crf_features(prefix, word_vec):
        """
        This method is used to unroll the word_vectors
        Args:
            prefix (str): Relative position of the word with respect to the current pointer.
            word_vec (np.array): The word vector which has to be unrolled

        Returns:
            features (list): List of word_vectors with appropriate format.
        Example:
             prefix = -1
             word_vec = [0.23, 0.45,0.11]
             convert_wordvec_features(prefix, word_vec)
             >> ['-1word_vec0=0.23', '-1word_vec1=0.45', '-1word_vec2=0.11']
        """
        features = []
        for i, each in enumerate(word_vec):
            features.append(prefix + CRF_WORD_VEC_FEATURE + str(i) + '=' + str(each))
        return features

    @staticmethod
    def get_crf_feature_from_word_vector(doc, i, j):
        """
        This class is used to convert the doc to CRF trainable features.
        Args:
        doc (dict): Dict consisting of the keys
            1. text_list
            2. labels
            3. pos_tags
            4. word_embeddings
        i (int): pointer to the sentence
        j (int): pointer to token in sentence

        Returns:
            features (list): List of CRF trainable features.
        """

        word = doc[SENTENCE_LIST][i][j]
        pos_tag = doc[CRF_POS_TAGS][i][j]
        # Common features for all words
        features = [
            'bias',
            'word.lower=' + word.lower(),
            'word.isupper=%s' % word.isupper(),
            'word.istitle=%s' % word.istitle(),
            'word.isdigit=%s' % word.isdigit(),
            'pos_tag=' + pos_tag
        ]

        word_embedding = doc[CRF_WORD_EMBEDDINGS][i][j]
        features.extend(CrfPreprocessData.convert_word_vector_to_crf_features('', word_embedding))

        # Features for words that are not
        # at the beginning of a document

        if j > 1:
            word1 = doc[SENTENCE_LIST][i][j - 2]
            pos_tag = doc[CRF_POS_TAGS][i][j - 2]
            features.extend([
                '-2:word.lower=' + word1.lower(),
                '-2:word.istitle=%s' % word1.istitle(),
                '-2:word.isupper=%s' % word1.isupper(),
                '-2:word.isdigit=%s' % word1.isdigit(),
                '-2:pos_tag=' + pos_tag,
                #   '-2:word.embedding=' + str(word_embedding)

            ])

            word_embedding = doc[CRF_WORD_EMBEDDINGS][i][j - 2]
            features.extend(CrfPreprocessData.convert_word_vector_to_crf_features('-2', word_embedding))

        if j > 0:
            word1 = doc[SENTENCE_LIST][i][j - 1]
            pos_tag = doc[CRF_POS_TAGS][i][j - 1]
            features.extend([
                '-1:word.lower=' + word1.lower(),
                '-1:word.istitle=%s' % word1.istitle(),
                '-1:word.isupper=%s' % word1.isupper(),
                '-1:word.isdigit=%s' % word1.isdigit(),
                '-1:pos_tag=' + pos_tag,

            ])
            word_embedding = doc[CRF_WORD_EMBEDDINGS][i][j - 1]
            features.extend(CrfPreprocessData.convert_word_vector_to_crf_features('-1', word_embedding))
        else:
            # Indicate that it is the 'beginning of a document'
            features.append(CRF_BOS)

        # Features for words that are not
        # at the end of a document
        if j < len(doc[SENTENCE_LIST][i]) - 2:
            word1 = doc[SENTENCE_LIST][i][j + 2]
            pos_tag = doc[CRF_POS_TAGS][i][j + 2]
            features.extend([
                '+2:word.lower=' + word1.lower(),
                '+2:word.istitle=%s' % word1.istitle(),
                '+2:word.isupper=%s' % word1.isupper(),
                '+2:word.isdigit=%s' % word1.isdigit(),
                '+2:pos_tag=' + pos_tag,
            ])
            word_embedding = doc[CRF_WORD_EMBEDDINGS][i][j + 2]
            features.extend(CrfPreprocessData.convert_word_vector_to_crf_features('+2', word_embedding))

        if j < len(doc[SENTENCE_LIST][i]) - 1:
            word1 = doc[SENTENCE_LIST][i][j + 1]
            pos_tag = doc[CRF_POS_TAGS][i][j + 1]
            features.extend([
                '+1:word.lower=' + word1.lower(),
                '+1:word.istitle=%s' % word1.istitle(),
                '+1:word.isupper=%s' % word1.isupper(),
                '+1:word.isdigit=%s' % word1.isdigit(),
                '+1:pos_tag=' + pos_tag,
            ])
            word_embedding = doc[CRF_WORD_EMBEDDINGS][i][j + 1]
            features.extend(CrfPreprocessData.convert_word_vector_to_crf_features('+1', word_embedding))
        else:
            # Indicate that it is the 'end of a document'
            features.append(CRF_EOS)

        return features

    @staticmethod
    def extract_crf_features(doc):
        """
        This method is used to extract features from the doc and it accomplishes this by calling the
        word_to_feature method.
        Args:
            doc (dict): Dict consisting of the keys
            1. text_list
            2. labels
            3. pos_tags
            4. word_embeddings
        Returns:
            (list): List consisting of the features used to train the CRF model.
        """
        features = []
        for i in range(len(doc[SENTENCE_LIST])):
            features.append([CrfPreprocessData.get_crf_feature_from_word_vector(doc, i, j) for j in range(len(doc[SENTENCE_LIST][i]))])
        return features

    @staticmethod
    def preprocess_crf_text_entity_list(sentence_list, entity_list=[[]], read_embeddings_from_remote_url=False):
        """
        This method is used to convert the text_list and entity_list to the corresponding
        training features and labels.
        Args:
            sentence_list (list): List of sentences on which the NER task has to be carried out.
            entity_list (list): List of entities present in each sentence of the text_list.
            read_embeddings_from_remote_url (bool): To indicate if cloud embeddings is active
        Returns:
            features (list): List of features required for training the CRF Model
            labels (list): Labels corresponding in IOB format.
        """
        ner_logger.debug('pre_process_text Started')
        processed_text = CrfPreprocessData.pre_process_text(sentence_list, entity_list)
        ner_logger.debug('pre_process_text Completed')

        ner_logger.debug('pos_tag Started')
        processed_text_pos_tag = CrfPreprocessData.get_pos_tagged_dict(processed_text)
        ner_logger.debug('pos_tag Completed')

        ner_logger.debug('LoadWordEmbeddings Started')
        if read_embeddings_from_remote_url:
            vocab, word_vectors = CrfPreprocessData.get_word_vectors_from_remote(processed_text_pos_tag)
        else:
            word_embeddings = LoadWordEmbeddings()
            vocab = word_embeddings.vocab
            word_vectors = word_embeddings.word_vectors

        ner_logger.debug('LoadingWordEmbeddings Completed')

        processed_text_pos_tag['word_embeddings'] = [CrfPreprocessData.word_embeddings(processed_pos_tag_data=each,
                                                                                       vocab=vocab,
                                                     word_vectors=word_vectors)
                                                     for each in processed_text_pos_tag[SENTENCE_LIST]]
        ner_logger.debug('Loading Word Embeddings Completed')

        ner_logger.debug('CrfPreprocessData.extract_features Started')
        features = CrfPreprocessData.extract_crf_features(processed_text_pos_tag)
        ner_logger.debug('CrfPreprocessData.extract_features Completed')

        ner_logger.debug('CrfPreprocessData.get_labels Started')
        labels = processed_text_pos_tag['labels']
        ner_logger.debug('CrfPreprocessData.get_labels Completed')
        return features, labels

    @staticmethod
    def get_word_vectors_from_remote(text_dict):
        """
        This method is used to obtain remotely setup word embeddings
        Args:
            text_dict (dict): Dictionary consisting of key text_list consisting of
                              tokenized text list.
        Returns:
            words_list(list): List of words for which word vectors have been obtained.
            word_vectors(np.array): Numpy array of the word vectors for the wordsList
        Example:
            text_dict:
              {
                'text_list': [['book', 'a', 'flight', 'from', 'Mumbai', 'to', 'Delhi'],
                ['Book', 'a', 'flight', 'to', 'Pune']]
              }
        """
        words_list = []
        for text in text_dict[SENTENCE_LIST]:
            for token in text:
                words_list.append(token)

        word_vectors = LoadWordEmbeddings.load_word_vectors_remote(sentence_list=words_list)

        return words_list, word_vectors
