from __future__ import absolute_import
from lib.singleton import Singleton
from chatbot_ner.config import CRF_MODEL_S3_BUCKET_REGION, CRF_MODEL_S3_BUCKET_NAME, ner_logger
from lib.aws_utils import read_model_dict_from_s3
import pycrfsuite
import six


class CrfModel(six.with_metaclass(Singleton, object)):
    """
    This class is used to load the crf tagger for a given entity
    """

    def __init__(self, entity_name):
        """
        This class is used to load the crf tagger for a given entity
        Args:
            entity_name (str): Name of the entity for which the tagger has to be loaded.
        """
        self.entity_name = entity_name
        self.loaded_model_path = None
        self.entity_model_dict = None
        self.tagger = pycrfsuite.Tagger()

    def load_model(self, model_path=None, live_crf_model_path=None):
        """
        Method that will load model data for entity and initialize the tagger for the same.
        If no model_path is given data will be loaded from the S3 with the path from redis
        Args:
            model_path (str): Path from where model has to be loaded for the given entity.
            live_crf_model_path (str): Live path for the Crf Model
        Returns:
            tagger (pycrfsuite.Tagger()): Tagger with the loaded model
        """
        if model_path:
            file_handler = open(model_path, 'r')
            self.entity_model_dict = file_handler.read()
            ner_logger.debug('Model dir %s path from local' % model_path)
            return self.initialize_tagger()

        ner_logger.debug('Model dir %s path from api' % live_crf_model_path)
        if live_crf_model_path == self.loaded_model_path:
            if not self.entity_model_dict:
                self.entity_model_dict = read_model_dict_from_s3(bucket_name=CRF_MODEL_S3_BUCKET_NAME,
                                                                 bucket_region=CRF_MODEL_S3_BUCKET_REGION,
                                                                 model_path_location=live_crf_model_path)
                ner_logger.debug('New Model dir %s path from api' % live_crf_model_path)
            else:
                return self.tagger
        else:
            self.entity_model_dict = read_model_dict_from_s3(bucket_name=CRF_MODEL_S3_BUCKET_NAME,
                                                             bucket_region=CRF_MODEL_S3_BUCKET_REGION,
                                                             model_path_location=live_crf_model_path)
            ner_logger.debug('New Model dir %s path from cache' % live_crf_model_path)
            self.loaded_model_path = live_crf_model_path
        return self.initialize_tagger()

    def initialize_tagger(self):
        """
        This method is used to load the model present in memory into the tagger.
        Returns:
            tagger (pycrfsuite.Tagger()): Tagger with the loaded model
        """
        self.tagger.open_inmemory(self.entity_model_dict)
        return self.tagger
