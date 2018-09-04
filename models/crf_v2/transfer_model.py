from lib.redis_utils import get_cache_ml, set_cache_ml_dest
from .constants import ENTITY_REDIS_MODELS_PATH
from chatbot_ner.config import ner_logger


class TransferCrfModel(object):
    """
    This method is used to transfer the crf model from source to destination using redis
    """
    def __init__(self, entity_list):
        """
        This method is used to transfer the crf model from source to destination using redis
        Args:
            entity_list (list): List of entities for which models need to be transferred
        """
        self.entity_list = entity_list

    def transfer_model(self):
        """
        This method is used to transfer model from source to destination for the list of entities
        by adding the latest path from the source redis to the destination redis.
        Returns:
            status (bool): To indicate if all entities were successfully transferred
        """
        ner_logger("Entity transfer for entity_list %s started" % str(self.entity_list))
        for entity_name in self.entity_list:
            entity_key = ENTITY_REDIS_MODELS_PATH + entity_name
            ner_logger("Entity key %s for entity %s" % (entity_key, entity_name))
            entity_path_value = get_cache_ml(entity_key)
            ner_logger("Entity path value %s for entity %s" % (entity_path_value, entity_name))
            result = set_cache_ml_dest(entity_key, entity_path_value)
            if result:
                ner_logger('Entity %s model has been transferred successfully' % entity_name)
            else:
                ner_logger('Entity %s model has been transfer has failed' % entity_name)
                return False
        return True
