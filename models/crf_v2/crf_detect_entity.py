from lib.nlp.tokenizer import Tokenizer, NLTK_TOKENIZER
from .crf_preprocess_data import CrfPreprocessData
from .get_crf_tagger import CrfModel
from chatbot_ner.config import MODELS_PATH
from models.crf_v2.constants import B_LABEL, I_LABEL


class CrfDetection(object):
    """
    This method is used to detect a text entity using the Crf model.
    """
    def __init__(self, entity_name, cloud_storage=False, cloud_embeddings=False, live_crf_model_path=''):
        """
        This method is used to detect text entities using the Crf model
        Args:
            entity_name (str): Name of the entity for which the entity has to be detected
            cloud_storage (bool): To indicate if cloud storage settings is required.
            live_crf_model_path (str): Path for the model to be loaded.
            cloud_embeddings (bool): To indicate if local embeddings have to be used or remote embeddings
        """
        self.entity_name = entity_name
        self.cloud_storage = cloud_storage
        self.cloud_embeddings = cloud_embeddings
        self.live_crf_model_path = live_crf_model_path

        crf_model = CrfModel(entity_name=self.entity_name)

        if self.cloud_storage:
            self.tagger = crf_model.load_model(live_crf_model_path=live_crf_model_path)
        else:
            self.tagger = crf_model.load_model(model_path=MODELS_PATH + self.entity_name)

    def detect_entity(self, text):
        """
        This method is used to predict the Entities present in the text.
        Args:
            text (str): Text on which the NER has to be carried out.
        Returns:
            original_text (list): List of entities detected in the text.
        Examples:
            Shopping cart Entity
            text = 'I wish to buy brown rice and apples'
            get_predictions(text)
            >> ['brown rice', 'apples']
        """
        x, _ = CrfPreprocessData.get_processed_x_y(text_list=[text], cloud_embeddings=self.cloud_embeddings)
        y_prediction = [self.tagger.tag(x_seq) for x_seq in x][0]

        word_tokenize = Tokenizer(tokenizer_selected=NLTK_TOKENIZER)

        tokenized_text = word_tokenize.tokenize(text)

        original_text = []
        for i in range(len(y_prediction)):
            temp = []
            if y_prediction[i] == B_LABEL:
                temp.append(tokenized_text[i])
                for j in range(i, len(y_prediction)):
                    if y_prediction[j] == I_LABEL:
                        temp.append(tokenized_text[j])
                original_text.append(' '.join(temp))

        return original_text
