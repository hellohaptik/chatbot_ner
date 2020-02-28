from __future__ import absolute_import
import pycrfsuite
from chatbot_ner.config import ner_logger, CRF_MODEL_S3_BUCKET_NAME, CRF_MODEL_S3_BUCKET_REGION, CRF_MODELS_PATH
from datastore.datastore import DataStore
from .constants import SENTENCE_LIST, ENTITY_LIST
from lib.aws_utils import write_file_to_s3
from .crf_preprocess_data import CrfPreprocessData
from .exceptions import AwsCrfModelWriteException, ESCrfTrainingEntityListNotFoundException, \
    ESCrfTrainingTextListNotFoundException
from datetime import datetime
import os
from six.moves import zip


class CrfTrain(object):
    """
    This class is used to train a Linear Chain Crf Model using Word Embeddings to carry out
    Named Entity Recognition (NER).

    """
    def __init__(self, entity_name, read_model_from_s3=False, read_embeddings_from_remote_url=False):
        """
        Args:
            entity_name (str): The destination path for saving the trained model.
            read_model_from_s3 (bool): To indicate if cloud storage settings is required.
            read_embeddings_from_remote_url (bool): To indicate if cloud embeddings is active
        """
        self.entity_name = entity_name
        self.model_dir = None
        self.read_model_from_s3 = read_model_from_s3
        self.read_embeddings_from_remote_url = read_embeddings_from_remote_url

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
        for x_seq, y_seq in zip(x, y):
            trainer.append(x_seq, y_seq)

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
        ner_logger.debug('Training for entity %s started' % self.entity_name)

        trainer.train(CRF_MODELS_PATH + self.entity_name + '/' + self.entity_name)
        ner_logger.debug('Training for entity %s completed' % self.entity_name)
        ner_logger.debug('Model locally saved at %s' % self.entity_name)

        if self.read_model_from_s3:
            self.model_dir = self.generate_crf_model_path()
            trainer.train(self.model_dir)
            ner_logger.debug('Training for entity %s completed' % self.entity_name)
            self.write_crf_model_to_s3()
            return self.model_dir
        else:
            local_path = CRF_MODELS_PATH + self.entity_name
            trainer.train(local_path)
            ner_logger.debug('Training for entity %s completed' % self.entity_name)
            ner_logger.debug('Model locally saved at %s' % self.entity_name)
            return local_path

    def train_crf_model_from_list(self, sentence_list, entity_list, c1=0, c2=0, max_iterations=1000):
        """
        This model is used to train the crf model. It performs the pre processing steps
        and trains the models
        Args:
            c1 (int): Coefficient of regularization to control variance and bias.
            c2 (int): Coefficient of regularization to control variance and bias.
            max_iterations (int): Max number of iterations to be carried out.
            sentence_list (list): List of sentences on which the NER task has to be carried out.
            entity_list (list): List of entities present in each sentence of the text_list.
        Returns:
            status (bool): Returns true if the training is successful.
        """

        ner_logger.debug('Pre processing for Entity: %s started' % self.entity_name)
        x, y = CrfPreprocessData.preprocess_crf_text_entity_list(sentence_list=sentence_list, entity_list=entity_list,
                                                                 read_embeddings_from_remote_url=
                                                                 self.read_embeddings_from_remote_url)
        ner_logger.debug('Pre processing for Entity: %s completed' % self.entity_name)
        model_path = self.train_crf_model(x, y, c1, c2, max_iterations)
        return model_path

    def train_model_from_es_data(self):
        """
        This method is used to train the crf model by first extracting training data from ES
        for the entity and training the crf model for the same.
        """
        datastore_object = DataStore()
        ner_logger.debug('Fetch of data from ES for ENTITY: %s started' % self.entity_name)
        result = datastore_object.get_crf_data_for_entity_name(entity_name=self.entity_name)

        sentence_list = result.get(SENTENCE_LIST, [])
        entity_list = result.get(ENTITY_LIST, [])

        if not sentence_list:
            raise ESCrfTrainingTextListNotFoundException()
        if not entity_list:
            raise ESCrfTrainingEntityListNotFoundException()

        ner_logger.debug('Fetch of data from ES for ENTITY: %s completed' % self.entity_name)
        ner_logger.debug('Length of text_list %s' % str(len(sentence_list)))

        model_path = self.train_crf_model_from_list(entity_list=entity_list, sentence_list=sentence_list)
        return model_path

    def write_crf_model_to_s3(self):
        """
        This method is used to write data to S3 and
        Returns:

        Raises:
            AwsWriteEntityFail if writing to Aws fails
        """
        ner_logger.debug('Model %s saving at AWS started' % self.model_dir)
        result = write_file_to_s3(bucket_name=CRF_MODEL_S3_BUCKET_NAME,
                                  bucket_region=CRF_MODEL_S3_BUCKET_REGION,
                                  address=self.model_dir,
                                  disk_filepath=self.model_dir)
        if result:
            ner_logger.debug('Model : %s written to s3' % self.model_dir)
        else:
            ner_logger.debug('Failure in saving Model to s3 %s' % self.model_dir)
            raise AwsCrfModelWriteException()

    def generate_crf_model_path(self):
        """
        This method is used to generate the directory to store the entity along with the timestamp
        Returns:
            output_directory (str): The path where the model needs to be stored.
        """
        file_path = CRF_MODELS_PATH + self.entity_name
        entity_path = CRF_MODELS_PATH + self.entity_name + '/' + self.entity_name
        entity_directory = os.path.dirname(entity_path)
        file_directory = os.path.dirname(entity_path)
        if not os.path.exists(entity_directory):
            os.makedirs(file_directory)
            ner_logger.debug('creating new directory %s' % file_path)

        output_directory_prefix = CRF_MODELS_PATH + self.entity_name + '/'
        output_directory_postfix = datetime.now().strftime("%d%m%Y-%H%M%S")
        return output_directory_prefix + self.entity_name + output_directory_postfix
