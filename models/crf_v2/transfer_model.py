from lib.redis_utils import get_cache_ml, set_cache_ml_dest
from .constants import ENTITY_REDIS_MODELS_PATH
from chatbot_ner.config import ner_logger


class TransferCrfModel(object):

    def __init__(self, entity_list):
        self.entity_list = entity_list

    def transfer_model(self):
        ner_logger("Entity transfer for entity_list %s started" % str(self.entity_list))
        for entity_name in self.entity_list:
            entity_key = ENTITY_REDIS_MODELS_PATH + entity_name
            ner_logger("Entity key %s for entity %s" % (entity_key, entity_name))
            entity_path_value = get_cache_ml(entity_key)
            ner_logger("Entity path value %s for entity %s" % (entity_path_value, entity_name))
            result = set_cache_ml_dest(entity_key, entity_path_value)
            if result:
                ner_logger('Entity %s model has been transferred succesfully' % entity_name)
            else:
                ner_logger('Entity %s model has been transfer has failed' % entity_name)
                return False
        return True
