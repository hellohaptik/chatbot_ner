from lib.redis_utils import get_cache_ml, set_cache_ml_dest
from .constants import ENTITY_REDIS_MODELS_PATH
from chatbot_ner.config import ner_logger


class TransferCrfModel(object):

    def __init__(self, entity_name):
        self.entity_name = entity_name

    def transfer_model(self):
        status = False
        entity_key = ENTITY_REDIS_MODELS_PATH + self.entity_name
        ner_logger("Entity key %s for entity %s" % (entity_key, self.entity_name))
        entity_path_value = get_cache_ml(entity_key)
        ner_logger("Entity path value %s for entity %s" % (entity_path_value, self.entity_name))
        result = set_cache_ml_dest(entity_key, entity_path_value)
        if result:
            ner_logger('Entity %s model has been transferred succesfully' % self.entity_name)
            status = True
            return status
        else:
            ner_logger('Entity %s model has been transfer has failed' % self.entity_name)
        return status