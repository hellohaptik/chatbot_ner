from chatbot_ner.config import CITY_MODEL_TYPE
from models import constants
from models.crf.test import PredictCRF


class Models(object):
    """""
    This class will decide which model to choose based on its model_type
    """""
    def __init__(self):
        """
        Initalises the object
        :return:
        """

    def run_model(self, entity_type, bot_message, user_message):
        """
        Runs the model based on the entity type
        :param entity_type:
        :return:
        """
        output_list = []
        if entity_type == constants.CITY_ENTITY_TYPE:
            if CITY_MODEL_TYPE == constants.CRF_MODEL_TYPE:
                crf_object = PredictCRF()
                output_list = crf_object.get_model_output(entity_type=entity_type, bot_message=bot_message,
                                                          user_message=user_message)
        return output_list
