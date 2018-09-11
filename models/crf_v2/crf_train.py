import pycrfsuite
from chatbot_ner.config import ner_logger, AWS_MODEL_BUCKET, AWS_MODEL_REGION, MODELS_PATH
from datastore.datastore import DataStore
from .constants import SENTENCE_LIST, ENTITY_LIST
from lib.aws_utils import write_file_to_s3
from .crf_preprocess_data import CrfPreprocessData
from .exceptions import AwsWriteEntityFail, ESTrainingEntityListError, \
    ESTrainingTextListError
from datetime import datetime
import os


class CrfTrain(object):
    """
    This class is used to train a Linear Chain Crf Model using Word Embeddings to carry out
    Named Entity Recognition (NER).

    """
    def __init__(self, entity_name, cloud_storage=False, cloud_embeddings=False):
        """
        Args:
            entity_name (str): The destination path for saving the trained model.
        """
        self.entity_name = entity_name
        self.model_dir = None
        self.cloud_storage = cloud_storage
        self.cloud_embeddings = cloud_embeddings

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
            cloud_storage (bool): To indicate if cloud storage settings is required.
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
        ner_logger.debug('Training for entity %s started' % self.entity_name)

        trainer.train(MODELS_PATH + self.entity_name + '/' + self.entity_name)
        ner_logger.debug('Training for entity %s completed' % self.entity_name)
        ner_logger.debug('Model locally saved at %s' % self.entity_name)

        if self.cloud_storage:
            self.model_dir = self.generate_model_path()
            trainer.train(self.model_dir)
            ner_logger.debug('Training for entity %s completed' % self.entity_name)
            self.write_model_to_s3()
            return self.model_dir
        else:
            local_path = MODELS_PATH + self.entity_name
            trainer.train(local_path)
            ner_logger.debug('Training for entity %s completed' % self.entity_name)
            ner_logger.debug('Model locally saved at %s' % self.entity_name)
            return local_path

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
            cloud_storage (bool): To indicate if cloud storage settings is required.
        Returns:
            status (bool): Returns true if the training is successful.
        """

        ner_logger.debug('Preprocessing for Entity: %s started' % self.entity_name)
        x, y = CrfPreprocessData.get_processed_x_y(text_list=text_list, entity_list=entity_list,
                                                   cloud_embeddings=self.cloud_embeddings)
        ner_logger.debug('Preprocessing for Entity: %s completed' % self.entity_name)
        model_path = self.train_crf_model(x, y, c1, c2, max_iterations)
        return model_path

    def train_model_from_es_data(self):
        """
        This method is used to train the crf model by first extracting training data from ES
        for the entity and training the crf model for the same.
        Args:
            cloud_storage (bool): To indicate if cloud storage settings is required.
        """
        datastore_object = DataStore()
        ner_logger.debug('Fetch of data from ES for ENTITY: %s started' % self.entity_name)
        result = datastore_object.get_crf_data_for_entity_name(entity_name=self.entity_name)

        text_list = result.get(SENTENCE_LIST, [])
        entity_list = result.get(ENTITY_LIST, [])

        if not text_list:
            raise ESTrainingTextListError()
        if not entity_list:
            raise ESTrainingEntityListError()

        ner_logger.debug('Fetch of data from ES for ENTITY: %s completed' % self.entity_name)
        ner_logger.debug('Length of text_list %s' % str(len(text_list)))

        model_path = self.train_model(entity_list=entity_list, text_list=text_list)
        return model_path

    def write_model_to_s3(self):
        """
        This method is used to write data to S3 and
        Returns:

        Raises:
            AwsWriteEntityFail if writing to Aws fails
        """
        ner_logger.debug('Model %s saving at AWS started' % self.model_dir)
        result = write_file_to_s3(bucket_name=AWS_MODEL_BUCKET,
                                  bucket_region=AWS_MODEL_REGION,
                                  address=self.model_dir,
                                  disk_filepath=self.model_dir)
        if result:
            ner_logger.debug('Model : %s written to s3' % self.model_dir)
        else:
            ner_logger.debug('Failure in saving Model to s3 %s' % self.model_dir)
            raise AwsWriteEntityFail()

    def generate_model_path(self):
        """
        This method is used to generate the directory to store the entity along with the timestamp
        Returns:
            output_directory (str): The path where the model needs to be stored.
        """
        file_path = MODELS_PATH + self.entity_name
        entity_path = MODELS_PATH + self.entity_name + '/' + self.entity_name
        entity_directory = os.path.dirname(entity_path)
        file_directory = os.path.dirname(entity_path)
        if not os.path.exists(entity_directory):
            os.makedirs(file_directory)
            ner_logger.debug('creating new directory %s' % file_path)

        output_directory_prefix = MODELS_PATH + self.entity_name + '/'
        output_directory_postfix = datetime.now().strftime("%d%m%Y-%H%M%S")
        return output_directory_prefix + self.entity_name + output_directory_postfix
