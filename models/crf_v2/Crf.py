import pickle
import pandas as pd
import numpy as np

import nltk
from nltk.tokenize import word_tokenize

import pycrfsuite
from sklearn.metrics import classification_report


class VanillaCrf(object):
    def __init__(self, model_name):
        self.model_name = model_name

    @staticmethod
    def load_data(sentences, original_text):
        raw_data = pd.DataFrame()
        raw_data['body'] = sentences
        raw_data['original_text'] = original_text
        return raw_data

    @staticmethod
    def load_word_vectors(embeddings_path_vocab, embeddings_path_vectors):
        file_handler = open(embeddings_path_vocab, 'rb')
        vocab = pickle.load(file_handler)
        file_handler = open(embeddings_path_vectors, 'rb')
        word_vectors = np.array(pickle.load(file_handler))
        return vocab, word_vectors

    @staticmethod
    def pre_process_text_pandas(body, original_text_list):
        processed_data = []
        tokenized_body = word_tokenize(body)
        processed_original_text = []
        for original_text in original_text_list:
            processed_original_text = processed_original_text + word_tokenize(original_text)
        for token in tokenized_body:
            if token in processed_original_text:
                processed_data.append((token, 'N'))
            else:
                processed_data.append((token, 'I'))
        return processed_data

    @staticmethod
    def word_embeddings(processed_pos_tag_data, vocab, word_vectors):
        sentence = []

        for tuple_token in processed_pos_tag_data:
            word_vec = np.zeros([word_vectors.shape[1]])
            if tuple_token[0].lower() in vocab:
                word_vec = word_vectors[vocab.index(tuple_token[0].lower())]
            sentence.append((tuple_token[0],
                             tuple_token[1],
                             tuple_token[2],
                             word_vec))

        return sentence

    @staticmethod
    def pre_process_text(raw_data):
        processed_list = []
        for body, original_text in zip(raw_data['body'], raw_data['original_text']):
            processed_list.append(VanillaCrf.pre_process_text_pandas(body, original_text))
        raw_data['processed_text'] = processed_list

        return raw_data

    @staticmethod
    def pos_tag(docs):
        data = []
        for i, doc in enumerate(docs):
            # Obtain the list of tokens in the document
            tokens = [t for t, label in doc]
            # Perform POS tagging
            tagged = nltk.pos_tag(tokens)
            # Take the word, POS tag, and its label
            data.append([(w, pos, label) for (w, label), (word, pos) in zip(doc, tagged)])
        return data

    @staticmethod
    def convert_wordvec_features(prefix, word_vec):
        features = []
        for i, each in enumerate(word_vec):
            features.append(prefix + 'word_vec' + str(i) + '=' + str(each))
        return features

    def word2features(self, doc, i, embeddings_status):
        word = doc[i][0]
        postag = doc[i][1]
        # word_embedding = doc[i][3]
        # Common features for all words
        features = [
            'bias',
            'word.lower=' + word.lower(),
            'word.isupper=%s' % word.isupper(),
            'word.istitle=%s' % word.istitle(),
            'word.isdigit=%s' % word.isdigit(),
            'postag=' + postag
        ]
        if embeddings_status:
            word_embedding = doc[i][3]

            features.extend(VanillaCrf.convert_wordvec_features('', word_embedding))

        # Features for words that are not
        # at the beginning of a document

        if i > 1:
            word1 = doc[i - 2][0]
            postag1 = doc[i - 2][1]
            features.extend([
                '-2:word.lower=' + word1.lower(),
                '-2:word.istitle=%s' % word1.istitle(),
                '-2:word.isupper=%s' % word1.isupper(),
                '-2:word.isdigit=%s' % word1.isdigit(),
                '-2:postag=' + postag1,
                #   '-2:word.embedding=' + str(word_embedding)

            ])

            if embeddings_status:
                word_embedding = doc[i - 2][3]
                features.extend(VanillaCrf.convert_wordvec_features('-2', word_embedding))

        if i > 0:
            word1 = doc[i - 1][0]
            postag1 = doc[i - 1][1]
            features.extend([
                '-1:word.lower=' + word1.lower(),
                '-1:word.istitle=%s' % word1.istitle(),
                '-1:word.isupper=%s' % word1.isupper(),
                '-1:word.isdigit=%s' % word1.isdigit(),
                '-1:postag=' + postag1,
                #   '-1:word.embedding=' + str(word_embedding)

            ])
            if embeddings_status:
                word_embedding = doc[i - 1][3]
                features.extend(VanillaCrf.convert_wordvec_features('-1', word_embedding))
        else:
            # Indicate that it is the 'beginning of a document'
            features.append('BOS')

        # Features for words that are not
        # at the end of a document
        if i < len(doc) - 2:
            word1 = doc[i + 2][0]
            postag1 = doc[i + 2][1]
            features.extend([
                '+2:word.lower=' + word1.lower(),
                '+2:word.istitle=%s' % word1.istitle(),
                '+2:word.isupper=%s' % word1.isupper(),
                '+2:word.isdigit=%s' % word1.isdigit(),
                '+2:postag=' + postag1,
                #     '+2:word.embedding=' + str(word_embedding)
                # '+1:is_in_dict='+str(bool(lemmatizer.lemmatize(word1) in entity_dictionary_unigram_lemmas))
            ])
            if embeddings_status:
                word_embedding = doc[i + 2][3]
                features.extend(VanillaCrf.convert_wordvec_features('+2', word_embedding))

        if i < len(doc) - 1:
            word1 = doc[i + 1][0]
            postag1 = doc[i + 1][1]
            features.extend([
                '+1:word.lower=' + word1.lower(),
                '+1:word.istitle=%s' % word1.istitle(),
                '+1:word.isupper=%s' % word1.isupper(),
                '+1:word.isdigit=%s' % word1.isdigit(),
                '+1:postag=' + postag1,
                #     '+1:word.embedding=' + str(word_embedding)
                # '+1:is_in_dict='+str(bool(lemmatizer.lemmatize(word1) in entity_dictionary_unigram_lemmas))
            ])
            if embeddings_status:
                word_embedding = doc[i + 1][3]
                features.extend(VanillaCrf.convert_wordvec_features('+1', word_embedding))
        else:
            # Indicate that it is the 'end of a document'
            features.append('EOS')

        return features

    def extract_features(self, doc, embeddings_status):
        return [self.word2features(doc, i, embeddings_status) for i in range(len(doc))]

    @staticmethod
    # A function fo generating the list of labels for each document
    def get_labels(doc):
        return [label for (token, postag, label, word_emb) in doc]

    def train_crf_model(self, x, y, c1, c2, max_iterations):
        trainer = pycrfsuite.Trainer(verbose=False)

        # Submit training data to the trainer
        for xseq, yseq in zip(x, y):
            trainer.append(xseq, yseq)

        # Set the parameters of the model
        trainer.set_params({
            # coefficient for L1 penalty
            'c1': c1,

            # coefficient for L2 penalty
            'c2': c2,

            # maximum number of iterations
            'max_iterations': max_iterations,

            # whether to include transitions that
            # are possible, but not observed
            'feature.possible_transitions': True
        })

        # Provide a file name as a parameter to the train function, such that
        # the model will be saved to the file when training is finished
        trainer.train(self.model_name)
        print('-- Done Training --')

    def train_model(self, sentences, original_text, c1, c2, max_iterations, embeddings_path_vectors,
                    embeddings_path_vocab, embeddings_status):
        data = VanillaCrf.load_data(sentences=sentences, original_text=original_text)
        data = VanillaCrf.pre_process_text(data)
        data['processed_text'] = VanillaCrf.pos_tag(data['processed_text'])
        vocab, word_vectors = VanillaCrf.load_word_vectors(embeddings_path_vocab, embeddings_path_vectors)
        pre_processed_data = [VanillaCrf.word_embeddings(processed_pos_tag_data=each, vocab=vocab, word_vectors=word_vectors)
                              for each in data['processed_text']]
        x = [self.extract_features(doc, embeddings_status) for doc in pre_processed_data]
        y = [VanillaCrf.get_labels(doc) for doc in pre_processed_data]
        self.train_crf_model(x, y, c1, c2, max_iterations)
        return None
