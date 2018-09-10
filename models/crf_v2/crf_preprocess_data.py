import numpy as np
from lib.nlp.pos import POS
import re
from lib.nlp.tokenizer import Tokenizer, NLTK_TOKENIZER
from models.crf_v2.word_embeddings import LoadWordEmbeddings
from chatbot_ner.config import ner_logger


class CrfPreprocessData(object):
    """
    This class is used to pre_process_data for the Crf model.
    """
    @staticmethod
    def pre_process_text_(text, entities):
        """
        This function takes input as the text and entities present in the text and processes
        them to generate processed tokens along with their respective IOB labels.
        Args:
            text (str): The text on which NER task has to be performed.
            entities (list): List of entities present in the text.

        Returns:
            processed_data (list): Returns a list of tuples where each tuple is of the form (token, label)

        Example:
            text = 'Book a flight from New York to California' '
            entity_list = ['New York', 'California']
            pre_process_text_(text, entity_list)
            >> [('Book', 'O'), ('a', 'O'), ('flight', 'O'), ('from', 'O'), ('New', 'B'), ('York', 'I'),
                ('to', 'O'), ('California', 'B')]
        """
        def IOB_prefixes(entity_value, word_tokenize):
            """
            This entity takes the input as the entity and returns the entity with its respective
            IOB-prefixes
            Args:
                entity_value (str): Entity for which IOB prefixing is required.

            Returns:
                iob_entites (str): IOB prefixed entit_values
            Example:
                For city entity
                entity_value = ['New York']
                IOB_prefixes(entity_value)
                >> 'B_city_New I_city_York'
            """
            iob_entities = ' '.join(['B_en_'+token_ if i_ == 0 else 'I_en_'+token_ for i_, token_
                                    in enumerate(word_tokenize.tokenize(entity_value))])
            return iob_entities

        word_tokenize = Tokenizer(tokenizer_selected=NLTK_TOKENIZER)
        entities.sort(key=lambda s: len(word_tokenize.tokenize(s)), reverse=True)
        tokenized_original_text = word_tokenize.tokenize(text)

        for entity in entities:
            text = re.sub(r'\b%s\b' % entity, IOB_prefixes(entity, word_tokenize), text)

        tokenized_text = word_tokenize.tokenize(text)

        labels = ['B' if 'B_en_' in tokenized_text[i]
                  else 'I' if 'I_en_' in tokenized_text[i]
                  else 'O' for i in range(len(tokenized_original_text))]

        return tokenized_original_text, labels
        # return [(g[0], 'O') if len(g) <= 1 else (g[1], g[0]) for g in
        #         [w.split('_en_') for w in word_tokenize.tokenize(text)]]

    @staticmethod
    def word_embeddings(processed_pos_tag_data, vocab, word_vectors):
        """
        This method is used to add word embeddings to the set of features.
        Args:
            processed_pos_tag_data :
            vocab (list): word_list consisting of words present in the word embeddings
            word_vectors (np.ndarray): word_vectors present in th word embeddings
        Returns:
            sentence (list): List of list of tuples where each tuple is of the form (token, pos_tag,
            label, word_emb)
        """
        word_embeddings = []
        for token in processed_pos_tag_data:
            word_vec = np.zeros([word_vectors.shape[1]])
            if token.lower() in vocab:
                word_vec = word_vectors[vocab.index(token.lower())]
            word_embeddings.append(word_vec)
        return word_embeddings

    @staticmethod
    def pre_process_text(text_list, entity_list):
        """
        This method is used to call pre_process_text for every text_list and entity_list
        Args:
            text_list (list): List of text on which NER has to be performed
            entity_list (list): List of entities present in text_list for every text occurenece.
        Returns:
            processed_list (dict): Nested list each being a list of tuples of the form (token, label)
        Examples:
            For city entity
            text_list = ['Book a flight to New York', 'I want to fly to California']
            entity_list = [['New York'], ['California']]
            pre_process_text(text_list, entity_list)
            >> [[('Book', 'O'),  ('a', 'O'),  ('flight', 'O'),  ('to', 'O'),  ('New', 'B'),  ('York', 'I')],
                [('I', 'O'),  ('want', 'O'),  ('to', 'O'),  ('fly', 'O'),  ('to', 'O'),  ('California', 'B')]]
        """

        processed_list = {'text_list': [],
                          'labels': []}

        for text, entities in zip(text_list, entity_list):
            tokenzied_text, labels = CrfPreprocessData.pre_process_text_(text, entities)
            processed_list['labels'].append(labels)
            processed_list['text_list'].append(tokenzied_text)
        return processed_list

    @staticmethod
    def pos_tag(docs):
        """
        This method is used to apply pos_tags to every token
        Args:
            docs (dict): List of tuples consisting of the token and label in (token, label) form.
        Returns:
            data (dict): List of tuples consisting of (token, pos_tag, label)
        Example:
            For city entity
            docs = [[('Book', 'O'),  ('a', 'O'),  ('flight', 'O'),  ('to', 'O'),  ('New', 'B'),  ('York', 'I')],
                [('I', 'O'),  ('want', 'O'),  ('to', 'O'),  ('fly', 'O'),  ('to', 'O'),  ('California', 'B')]]
            pos_tag(docs)

            >> [[('Book', 'NNP', 'O'),  ('a', 'DT', 'O'),  ('flight', 'NN', 'O'),  ('to', 'TO', 'O'),
              ('New', 'NNP', 'B'),  ('York', 'NNP', 'I')], [('I', 'PRP', 'O'),  ('want', 'VBP', 'O'),
                ('to', 'TO', 'O'),  ('fly', 'RB', 'O'),  ('to', 'TO', 'O'),  ('California', 'NNP', 'B')]]
        """
        docs['pos_tags'] = []
        pos_tagger = POS()
        for text in docs['text_list']:
            docs['pos_tags'].append([tag[1] for tag in pos_tagger.tagger.tag(text)])

        return docs

    @staticmethod
    def convert_wordvec_features(prefix, word_vec):
        """
        This method is used to unroll the word_vectors
        Args:
            prefix (str): Relative position of the word with respect to the current pointer.
            word_vec (np.ndarray): The word vector which has to be unrolled

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
            features.append(prefix + 'word_vec' + str(i) + '=' + str(each))
        return features

    @staticmethod
    def word_to_features(doc, i, j):
        """
        This class is used to convert the doc to CRF trainable features.
        Args:
            doc (dict): List of tuples consisting of the token and label in (token, pos_tag,word_emb ,label) form.
            i (int): Pointer to the current time_step.

        Returns:
            features (list): List of CRF trainable features.
        """

        word = doc['text_list'][i][j]
        pos_tag = doc['pos_tags'][i][j]
        # word_embedding = doc[i][3]
        # Common features for all words
        features = [
            'bias',
            'word.lower=' + word.lower(),
            'word.isupper=%s' % word.isupper(),
            'word.istitle=%s' % word.istitle(),
            'word.isdigit=%s' % word.isdigit(),
            'pos_tag=' + pos_tag
        ]

        word_embedding = doc['word_embeddings'][i][j]
        features.extend(CrfPreprocessData.convert_wordvec_features('', word_embedding))

        # Features for words that are not
        # at the beginning of a document

        if j > 1:
            word1 = doc['text_list'][i][j - 2]
            postag1 = doc['pos_tags'][i][j - 2]
            features.extend([
                '-2:word.lower=' + word1.lower(),
                '-2:word.istitle=%s' % word1.istitle(),
                '-2:word.isupper=%s' % word1.isupper(),
                '-2:word.isdigit=%s' % word1.isdigit(),
                '-2:pos_tag=' + postag1,
                #   '-2:word.embedding=' + str(word_embedding)

            ])

            word_embedding = doc['word_embeddings'][i][j - 2]
            features.extend(CrfPreprocessData.convert_wordvec_features('-2', word_embedding))

        if j > 0:
            word1 = doc['text_list'][i][j - 1]
            postag1 = doc['pos_tags'][i][j - 1]
            features.extend([
                '-1:word.lower=' + word1.lower(),
                '-1:word.istitle=%s' % word1.istitle(),
                '-1:word.isupper=%s' % word1.isupper(),
                '-1:word.isdigit=%s' % word1.isdigit(),
                '-1:pos_tag=' + postag1,

            ])
            word_embedding = doc['word_embeddings'][i][j - 1]
            features.extend(CrfPreprocessData.convert_wordvec_features('-1', word_embedding))
        else:
            # Indicate that it is the 'beginning of a document'
            features.append('BOS')

        # Features for words that are not
        # at the end of a document
        if j < len(doc['text_list'][i]) - 2:
            word1 = doc['text_list'][i][j + 2]
            postag1 = doc['pos_tags'][i][j + 2]
            features.extend([
                '+2:word.lower=' + word1.lower(),
                '+2:word.istitle=%s' % word1.istitle(),
                '+2:word.isupper=%s' % word1.isupper(),
                '+2:word.isdigit=%s' % word1.isdigit(),
                '+2:pos_tag=' + postag1,
            ])
            word_embedding = doc['word_embeddings'][i][j + 2]
            features.extend(CrfPreprocessData.convert_wordvec_features('+2', word_embedding))

        if j < len(doc['text_list'][i]) - 1:
            word1 = doc['text_list'][i][j + 1]
            postag1 = doc['pos_tags'][i][j + 1]
            features.extend([
                '+1:word.lower=' + word1.lower(),
                '+1:word.istitle=%s' % word1.istitle(),
                '+1:word.isupper=%s' % word1.isupper(),
                '+1:word.isdigit=%s' % word1.isdigit(),
                '+1:pos_tag=' + postag1,
            ])
            word_embedding = doc['word_embeddings'][i][j + 1]
            features.extend(CrfPreprocessData.convert_wordvec_features('+1', word_embedding))
        else:
            # Indicate that it is the 'end of a document'
            features.append('EOS')

        return features

    @staticmethod
    def extract_features(doc):
        """
        This method is used to extract features from the doc and it accomplishes this by calling the
        word_to_feature method.
        Args:
            doc (dict): List of tuples consisting of the token and label in (token, pos_tag,word_emb ,label) form.
        Returns:
            (list): List consisting of the features used to train the CRF model.
        """
        features = []
        for i in range(len(doc['text_list'])):
            features.append([CrfPreprocessData.word_to_features(doc, i, j) for j in range(len(doc['text_list'][i]))])
        return features

    @staticmethod
    def get_processed_x_y(text_list, entity_list, cloud_storage=False):
        """
        This method is used to convert the text_list and entity_list to the corresponding
        training features and labels.
        Args:
            text_list (list): List of sentences on which the NER task has to be carried out.
            entity_list (list): List of entities present in each sentence of the text_list.
            cloud_storage (bool): To indicate if cloud storage settings is required.
        Returns:
            features (list): List of features required for training the CRF Model
            labels (list): Labels corresponding in IOB format.
        """
        ner_logger.debug('pre_process_text Started')
        processed_text = CrfPreprocessData.pre_process_text(text_list, entity_list)
        ner_logger.debug('pre_process_text Completed')

        ner_logger.debug('pos_tag Started')
        processed_text_pos_tag = CrfPreprocessData.pos_tag(processed_text)
        ner_logger.debug('pos_tag Completed')

        ner_logger.debug('LoadWordEmbeddings Started')
        if cloud_storage:
            vocab, word_vectors = CrfPreprocessData.remote_word_embeddings(processed_text_pos_tag)
        else:
            word_embeddings = LoadWordEmbeddings()
            vocab = word_embeddings.vocab
            word_vectors = word_embeddings.word_vectors

        ner_logger.debug('LoadingWordEmbeddings Completed')

        processed_text_pos_tag['word_embeddings'] = [CrfPreprocessData.word_embeddings(processed_pos_tag_data=each, vocab=vocab,
                                                     word_vectors=word_vectors)
                                                     for each in processed_text_pos_tag['text_list']]
        ner_logger.debug('Loading Word Embeddings Completed')

        ner_logger.debug('CrfPreprocessData.extract_features Started')
        features = CrfPreprocessData.extract_features(processed_text_pos_tag)
        ner_logger.debug('CrfPreprocessData.extract_features Completed')

        ner_logger.debug('CrfPreprocessData.get_labels Started')
        labels = processed_text_pos_tag['labels']
        ner_logger.debug('CrfPreprocessData.get_labels Completed')
        return features, labels

    @staticmethod
    def remote_word_embeddings(processed_text_pos_tag):
        words_list = []
        for text in processed_text_pos_tag['text_list']:
            for token in text:
                words_list.append(token)

        word_vectors = LoadWordEmbeddings.load_word_vectors_remote(text_list=words_list)

        return words_list, word_vectors
