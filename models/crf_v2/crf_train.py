import pycrfsuite
from chatbot_ner.config import ner_logger, AWS_MODEL_BUCKET, AWS_MODEL_REGION, MODELS_PATH
from datastore.datastore import DataStore
from .constants import TEXT_LIST, ENTITY_LIST
from lib.aws_utils import write_file_to_s3
from .crf_preprocess_data import CrfPreprocessData
from lib.redis_utils import set_cache_ml
from .constants import ENTITY_REDIS_MODELS_PATH
from .exceptions import AwsWriteEntityFail, RedisWriteEntityFail


class CrfTrain(object):
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

    def train_crf_model(self, x, y, c1, c2, max_iterations, cloud_storage=False):
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
        trainer.train(MODELS_PATH + self.entity_name)
        if cloud_storage:
            self.write_model_to_s3()

    def train_model(self, text_list, entity_list, c1=0, c2=0, max_iterations=1000, cloud_storage=False):
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
            x, y = CrfPreprocessData.get_processed_x_y(text_list=text_list, entity_list=entity_list)

            self.train_crf_model(x, y, c1, c2, max_iterations, cloud_storage)
            status = True
            ner_logger.debug('Training Completed')
        except Exception as e:
            ner_logger.debug('Value Error %s' % e)

        return status

    def train_model_from_es_data(self, cloud_storage=False):
        datastore_object = DataStore()
        result = datastore_object.get_entity_training_data(entity_name=self.entity_name)
        text_list = result.get(TEXT_LIST, [])
        entity_list = result.get(ENTITY_LIST, [])
        self.train_model(entity_list=entity_list, text_list=text_list, cloud_storage=cloud_storage)

    def write_model_to_s3(self):
        result = write_file_to_s3(bucket_name=AWS_MODEL_BUCKET,
                                  bucket_region=AWS_MODEL_REGION,
                                  address=MODELS_PATH + self.entity_name,
                                  disk_filepath=self.entity_name)
        if result:
            ner_logger.debug('Entity : %s written to s3' % self.entity_name)
        else:
            ner_logger.debug('Failure in saving entity to s3 %s' % self.entity_name)
            raise AwsWriteEntityFail()

        result = set_cache_ml(ENTITY_REDIS_MODELS_PATH + self.entity_name, MODELS_PATH + self.entity_name)
        if result:
            ner_logger.debug('Entity path : %s written to Redis ' % self.entity_name)
        else:
            ner_logger.debug('Failure in saving entity path to Redis %s' % self.entity_name)
            raise RedisWriteEntityFail()
