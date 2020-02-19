from __future__ import absolute_import
from lib.nlp.tokenizer import Tokenizer, NLTK_TOKENIZER
from .crf_preprocess_data import CrfPreprocessData
from .get_crf_tagger import CrfModel
from chatbot_ner.config import CRF_MODELS_PATH
from models.crf_v2.constants import CRF_B_LABEL, CRF_I_LABEL
from six.moves import range


class CrfDetection(object):
    """
    This method is used to detect a text entity using the Crf model.
    """
    def __init__(self, entity_name, read_model_from_s3=False, read_embeddings_from_remote_url=False, live_crf_model_path=''):
        """
        This method is used to detect text entities using the Crf model
        Args:
            entity_name (str): Name of the entity for which the entity has to be detected
            read_model_from_s3 (bool): To indicate if cloud storage settings is required.
            live_crf_model_path (str): Path for the model to be loaded.
            read_embeddings_from_remote_url (bool): To indicate if local embeddings have to be used or remote embeddings
        """
        self.entity_name = entity_name
        self.read_model_from_s3 = read_model_from_s3
        self.read_embeddings_from_remote_url = read_embeddings_from_remote_url
        self.live_crf_model_path = live_crf_model_path

        crf_model = CrfModel(entity_name=self.entity_name)

        if self.read_model_from_s3:
            self.tagger = crf_model.load_model(live_crf_model_path=live_crf_model_path)
        else:
            self.tagger = crf_model.load_model(model_path=CRF_MODELS_PATH + self.entity_name)

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
        x, _ = CrfPreprocessData.preprocess_crf_text_entity_list(sentence_list=[text],
                                                                 read_embeddings_from_remote_url=self.read_embeddings_from_remote_url)
        y_prediction = [self.tagger.tag(x_seq) for x_seq in x][0]

        word_tokenize = Tokenizer(tokenizer_selected=NLTK_TOKENIZER)

        tokenized_text = word_tokenize.tokenize(text)

        original_text = []
        for i in range(len(y_prediction)):
            temp = []
            if y_prediction[i] == CRF_B_LABEL:
                temp.append(tokenized_text[i])
                for j in range(i, len(y_prediction)):
                    if y_prediction[j] == CRF_I_LABEL:
                        temp.append(tokenized_text[j])
                original_text.append(' '.join(temp))

        return original_text
