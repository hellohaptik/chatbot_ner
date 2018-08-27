import pickle
import numpy as np
import nltk
import pycrfsuite
import re
from chatbot_ner.config import ner_logger
from lib.nlp.tokenizer import Tokenizer, NLTK_TOKENIZER
from datastore.datastore import DataStore
from .constants import TEXT_LIST, ENTITY_LIST, EMBEDDINGS_PATH_VOCAB, EMBEDDINGS_PATH_VECTORS
import boto3
import boto


class CrfWordEmbeddings(object):
    """
    This class is used to construct a Linear Chain Crf Model using Word Embeddings to carry out
    Named Entity Recognition (NER).

    """
    def __init__(self, entity_name):
        """
        Args:
            entity_name (str): The destination path for saving the trained model.
            embeddings_path_vocab (str): The path where the word_list for the embeddings are stored.
            embeddings_path_vectors (str): The path where the vectors are stored.
        """
        self.entity_name = entity_name

    @staticmethod
    def load_word_vectors():
        """
        Thus function is used to load the word_list and word_vectors from the specified paths.
        Returns:
        vocab (list): word_list present at the specified path.
        word_vectors (numpy.ndarray): word_vectors present at the specified path.
        """
        file_handler = open(EMBEDDINGS_PATH_VOCAB, 'rb')
        vocab = pickle.load(file_handler)
        file_handler = open(EMBEDDINGS_PATH_VECTORS, 'rb')
        word_vectors = np.array(pickle.load(file_handler))
        return vocab, word_vectors

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
        for entity in entities:
            text = re.sub(r'\b%s\b' % entity, IOB_prefixes(entity, word_tokenize), text)

        return [(g[0], 'O') if len(g) <= 1 else (g[1], g[0]) for g in
                [w.split('_en_') for w in word_tokenize.tokenize(text)]]

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
    def pre_process_text(text_list, entity_list):
        """
        This method is used to call pre_process_text for every text_list and entity_list
        Args:
            text_list (list): List of text on which NER has to be performed
            entity_list (list): List of entities present in text_list for every text occurenece.
        Returns:
            processed_list (list): Nested list each being a list of tuples of the form (token, label)
        Examples:
            For city entity
            text_list = ['Book a flight to New York', 'I want to fly to California']
            entity_list = [['New York'], ['California']]
            pre_process_text(text_list, entity_list)
            >> [[('Book', 'O'),  ('a', 'O'),  ('flight', 'O'),  ('to', 'O'),  ('New', 'B'),  ('York', 'I')],
                [('I', 'O'),  ('want', 'O'),  ('to', 'O'),  ('fly', 'O'),  ('to', 'O'),  ('California', 'B')]]
        """

        processed_list = []
        for text, entities in zip(text_list, entity_list):
            processed_list.append(CrfWordEmbeddings.pre_process_text_(text, entities))

        return processed_list

    @staticmethod
    def pos_tag(docs):
        """
        This method is used to apply pos_tags to every token
        Args:
            docs (list): List of tuples consisting of the token and label in (token, label) form.
        Returns:
            data (list): List of tuples consisting of (token, pos_tag, label)
        Example:
            For city entity
            docs = [[('Book', 'O'),  ('a', 'O'),  ('flight', 'O'),  ('to', 'O'),  ('New', 'B'),  ('York', 'I')],
                [('I', 'O'),  ('want', 'O'),  ('to', 'O'),  ('fly', 'O'),  ('to', 'O'),  ('California', 'B')]]
            pos_tag(docs)

            >> [[('Book', 'NNP', 'O'),  ('a', 'DT', 'O'),  ('flight', 'NN', 'O'),  ('to', 'TO', 'O'),
              ('New', 'NNP', 'B'),  ('York', 'NNP', 'I')], [('I', 'PRP', 'O'),  ('want', 'VBP', 'O'),
                ('to', 'TO', 'O'),  ('fly', 'RB', 'O'),  ('to', 'TO', 'O'),  ('California', 'NNP', 'B')]]
        """
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
    def word_to_features(doc, i):
        """
        This class is used to convert the doc to CRF trainable features.
        Args:
            doc (list): List of tuples consisting of the token and label in (token, pos_tag,word_emb ,label) form.
            i (int): Pointer to the current time_step.

        Returns:
            features (list): List of CRF trainable features.
        """

        word = doc[i][0]
        pos_tag = doc[i][1]
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

        word_embedding = doc[i][3]
        features.extend(CrfWordEmbeddings.convert_wordvec_features('', word_embedding))

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
                '-2:pos_tag=' + postag1,
                #   '-2:word.embedding=' + str(word_embedding)

            ])

            word_embedding = doc[i - 2][3]
            features.extend(CrfWordEmbeddings.convert_wordvec_features('-2', word_embedding))

        if i > 0:
            word1 = doc[i - 1][0]
            postag1 = doc[i - 1][1]
            features.extend([
                '-1:word.lower=' + word1.lower(),
                '-1:word.istitle=%s' % word1.istitle(),
                '-1:word.isupper=%s' % word1.isupper(),
                '-1:word.isdigit=%s' % word1.isdigit(),
                '-1:pos_tag=' + postag1,

            ])
            word_embedding = doc[i - 1][3]
            features.extend(CrfWordEmbeddings.convert_wordvec_features('-1', word_embedding))
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
                '+2:pos_tag=' + postag1,
            ])
            word_embedding = doc[i + 2][3]
            features.extend(CrfWordEmbeddings.convert_wordvec_features('+2', word_embedding))

        if i < len(doc) - 1:
            word1 = doc[i + 1][0]
            postag1 = doc[i + 1][1]
            features.extend([
                '+1:word.lower=' + word1.lower(),
                '+1:word.istitle=%s' % word1.istitle(),
                '+1:word.isupper=%s' % word1.isupper(),
                '+1:word.isdigit=%s' % word1.isdigit(),
                '+1:pos_tag=' + postag1,
            ])
            word_embedding = doc[i + 1][3]
            features.extend(CrfWordEmbeddings.convert_wordvec_features('+1', word_embedding))
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
            doc (list): List of tuples consisting of the token and label in (token, pos_tag,word_emb ,label) form.
        Returns:
            (list): List consisting of the features used to train the CRF model.
        """
        return [CrfWordEmbeddings.word_to_features(doc, i) for i in range(len(doc))]

    @staticmethod
    # A function fo generating the list of labels for each document
    def get_labels(doc):
        """
        This method is used to obtain the labels from the doc.
        Args:
            doc (list): doc (list): List of tuples consisting of the token and label
                        in (token, pos_tag,word_emb ,label) form.
        Returns:
            (list): List of tuples consisting of the lables in IOB format.
        """
        return [label for (token, postag, label, word_emb) in doc]

    def train_crf_model(self, x, y, c1, c2, max_iterations):
        """
        This is the main function where training of the model is carried out. The model post
        training is then saved to the specified.
        Args:
            x (list): List of features with which the crf model has to be trained
            y (list): List of labels in IOB format
            c1 (int): Coefficient of regularization to control variance and bias.
            c2 (int): Coeffiecnt of regularization to control variance and bias.
            max_iterations (int): Max number of iterations to be carried out.
        """
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
        trainer.train(self.entity_name)

    def get_processed_x_y(self, text_list, entity_list):
        """
        This method is used to convert the text_list and entity_list to the corresponding
        training features and labels.
        Args:
            text_list (list): List of sentences on which the NER task has to be carried out.
            entity_list (list): List of entities present in each sentence of the text_list.

        Returns:
            features (list): List of features required for training the CRF Model
            labels (list): Labels corresponding in IOB format.
        """
        processed_text = CrfWordEmbeddings.pre_process_text(text_list, entity_list)
        processed_text_pos_tag = CrfWordEmbeddings.pos_tag(processed_text)
        vocab, word_vectors = CrfWordEmbeddings.load_word_vectors()
        pre_processed_data = [CrfWordEmbeddings.word_embeddings(processed_pos_tag_data=each, vocab=vocab,
                                                                word_vectors=word_vectors)
                              for each in processed_text_pos_tag]
        features = [CrfWordEmbeddings.extract_features(doc) for doc in pre_processed_data]
        labels = [CrfWordEmbeddings.get_labels(doc) for doc in pre_processed_data]
        return features, labels

    def train_model(self, text_list, entity_list, c1=0, c2=0, max_iterations=1000):
        """
        This model is used to train the crf model. It performs the pre processing steps
        and trains the models
        Args:
            c1 (int): Coefficient of regularization to control variance and bias.
            c2 (int): Coefficient of regularization to control variance and bias.
            max_iterations (int): Max number of iterations to be carried out.
            text_list (list): List of sentences on which the NER task has to be carried out.
            entity_list (list): List of entities present in each sentence of the text_list.

        Returns:
            status (bool): Returns true if the training is successful.
        """
        status = False
        try:
            x, y = self.get_processed_x_y(text_list, entity_list)
            self.train_crf_model(x, y, c1, c2, max_iterations)
            status = True
            ner_logger.debug('Training Completed')
        except ValueError:
            ner_logger.debug('Value Error %s' % ValueError)

        return status

    def get_predictions(self, text):
        """
        This method is used to predict the Entities present in the text.
        Args:
            text (str): Text on which the NER has to be carried out.
        Returns:
            original_text (list): List of entities detected in the text.
        Examples:
            Shopping cart Entity
            text = 'I wish to buy brown rice and apples'
            get_predictions(text)
            >> ['brown rice', 'apples']
        """
        x, _ = self.get_processed_x_y([text], [[]])
        tagger = pycrfsuite.Tagger()
        tagger.open(self.entity_name)
        y_prediction = [tagger.tag(xseq) for xseq in x][0]
        word_tokenize = Tokenizer(tokenizer_selected=NLTK_TOKENIZER)
        tokenized_text = word_tokenize.tokenize(text)
        original_text = []

        for i in range(len(y_prediction)):
            temp = []
            if y_prediction[i] == 'B':
                temp.append(tokenized_text[i])
                for j in range(i, len(y_prediction)):
                    if y_prediction[j] == 'I':
                        temp.append(tokenized_text[j])
                original_text.append(' '.join(temp))

        return original_text

    def train_model_from_es_data(self):
        datastore_object = DataStore()
        result = datastore_object.get_entity_training_data(entity_name=self.entity_name)
        text_list = result.get(TEXT_LIST, [])
        entity_list = result.get(ENTITY_LIST, [])
        self.train_model(entity_list=entity_list, text_list=text_list)

    @staticmethod
    def read_model_dict_from_s3(bucket_name, model_path_location=None):
        """
        Read model dict from s3 for given model path location
        :param bucket_name: s3 bucket name
        :param model_path_location: model path location for domain
        :return:
        """
        model_dict = None
        try:
            s3 = boto3.resource('s3')
            bucket = s3.Bucket(bucket_name)
            pickle_file_handle = bucket.Object(model_path_location.lstrip('/'))
            # note read() will return str and hence cPickle.loads
            model_dict = pickle.loads(pickle_file_handle.get()['Body'].read())
            ner_logger.debug("Model Read Successfully From s3")
        except Exception as e:
            ner_logger.exception("Error Reading model from s3 for domain %s " % e)
        return model_dict

    @staticmethod
    def write_file_to_s3(bucket_name, address, disk_filepath, bucket_region=None):
        """
        Upload file on disk to s3 bucket with the given address
        WARNING! File will be overwritten if it exists

        Args:
            bucket_name (str): name of the bucket to upload file to
            address (str): full path including filename inside the bucket to upload the file at
            disk_filepath (str): full path including filename on disk of the file to upload to s3 bucket
            bucket_region (str, Optional): region of the s3 bucket, defaults to None

        Returns:
            bool: indicating whether file upload was successful

        """
        try:
            connection, bucket = CrfWordEmbeddings.get_s3_connection_and_bucket(bucket_name=bucket_name,
                                                                                bucket_region=bucket_region)
            key = bucket.new_key(address)
            key.set_contents_from_filename(disk_filepath)
            connection.close()
            return True
        except Exception as e:
            ner_logger.error("Error in write_file_to_s3 - %s %s %s : %s" % (bucket_name, address, disk_filepath, e))

        return False

    @staticmethod
    def get_s3_connection_and_bucket(bucket_name, bucket_region=None):
        """
        Connect to S3 bucket

        Args:
            bucket_name (str): name of the bucket to upload file to
            bucket_region (str, Optional): region of the s3 bucket, defaults to None

        Returns:
            tuple containing
                boto.s3.connection.S3Connection: Boto connection to s3 in the specified region
                boto.s3.bucket.Bucket: bucket object of the specified name

        """
        if bucket_region:
            connection = boto.s3.connect_to_region(bucket_region)
        else:
            connection = boto.connect_s3()
        bucket = connection.get_bucket(bucket_name)
        return connection, bucket
