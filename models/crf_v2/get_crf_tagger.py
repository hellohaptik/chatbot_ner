from lib.singleton import Singleton
from lib.redis_utils import get_cache_ml
from .constants import ENTITY_REDIS_MODELS_PATH
from chatbot_ner.config import AWS_MODEL_REGION, AWS_MODEL_BUCKET
from lib.aws_utils import read_model_dict_from_s3
import pycrfsuite


class CrfModel(object):

    __metaclass__ = Singleton

    def __init__(self, entity_name):
        self.entity_name = entity_name
        self.loaded_model_path = None
        self.entity_model_dict = None
        self.tagger = pycrfsuite.Tagger()

    def load_model(self, model_path=None):
        """
        Method that will load model data for domain from s3 using model path store in redis
        :param model_path: (String) Path when model needs to be read locally
        :return: Dictionary of model
        """
        if model_path:
            file_handler = open(model_path, 'r')
            self.entity_model_dict = file_handler.read()
            return self.initialize_tagger()

        s3_model_path = get_cache_ml(ENTITY_REDIS_MODELS_PATH + self.entity_name)

        if s3_model_path == self.loaded_model_path:
            if not self.entity_model_dict:
                self.entity_model_dict = read_model_dict_from_s3(bucket_name=AWS_MODEL_BUCKET,
                                                                 bucket_region=AWS_MODEL_REGION,
                                                                 model_path_location=s3_model_path)
            else:
                return self.tagger
        else:
            self.entity_model_dict = read_model_dict_from_s3(bucket_name=AWS_MODEL_BUCKET,
                                                             bucket_region=AWS_MODEL_REGION,
                                                             model_path_location=s3_model_path)
            self.loaded_model_path = s3_model_path
        return self.initialize_tagger()

    def initialize_tagger(self):
        self.tagger.open_inmemory(self.entity_model_dict)
        return self.tagger
