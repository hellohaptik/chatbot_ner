from lib.nlp.tokenizer import Tokenizer, NLTK_TOKENIZER
from .crf_preprocess_data import CrfPreprocessData
from .get_crf_tagger import CrfModel
from chatbot_ner.config import MODELS_PATH


class CrfDetection(object):

    def __init__(self, entity_name, cloud_storage=False):
        self.entity_name = entity_name
        self.cloud_storage = cloud_storage

        crf_model = CrfModel(entity_name=self.entity_name)

        if self.cloud_storage:
            self.tagger = crf_model.load_model()
        else:
            self.tagger = crf_model.load_model(model_path=MODELS_PATH + self.entity_name + '/' + self.entity_name)

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
        x, _ = CrfPreprocessData.get_processed_x_y([text], [[]])
        y_prediction = [self.tagger.tag(xseq) for xseq in x][0]

        word_tokenize = Tokenizer(tokenizer_selected=NLTK_TOKENIZER)

        tokenized_text = word_tokenize.tokenize(text)

        original_text = []
        for i in range(len(y_prediction)):
            temp = []
            if y_prediction[i] == 'B':
                temp.append(tokenized_text[i])
                for j in range(i, len(y_prediction)):
                    if y_prediction[j] == 'I':
                        temp.append(tokenized_text[j])
                original_text.append(' '.join(temp))

        return original_text
