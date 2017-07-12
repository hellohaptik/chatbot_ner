from chatbot_ner.config import CITY_MODEL_TYPE
from .constant import CRF_MODEL_TYPE, CITY_ENTITY_TYPE
from .crf.test import PredictCRF


class Models(object):
    """""
    This class will decide which model to choose based on its model_type
    """""
    def __init__(self):
        """
        Initalises the object
        """

    def run_model(self, entity_type, bot_message, user_message):
        """
        Runs the model based on the entity type

        Args:
            entity_type: type of entity which decides which entity model to call
            bot_message: message from the bot/expert
            user_message: message from the user

        Returns:
             The output detected from the respective model
        """
        output_list = []
        if entity_type == CITY_ENTITY_TYPE:
            if CITY_MODEL_TYPE == CRF_MODEL_TYPE:
                crf_object = PredictCRF()
                output_list = crf_object.get_model_output(entity_type=entity_type, bot_message=bot_message,
                                                          user_message=user_message)
        return output_list
