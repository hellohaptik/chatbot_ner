from .crf import CrfWordEmbeddings
from .crf_s3_storage import read_model_dict_from_s3
from chatbot_ner.config import ner_logger, AWS_MODEL_BUCKET, AWS_MODEL_REGION
import pycrfsuite
from lib.nlp.tokenizer import Tokenizer, NLTK_TOKENIZER


class CrfDetection(object):

    def __int__(self, entity_name, cloud_storage=False):
        self.entity_name = entity_name
        self.cloud_storage = cloud_storage
        self.entity_path = ''
        if self.cloud_storage:
            self.model_dict = CrfDetection.load_model_from_s3()
        else:
            self.model_dict = CrfDetection.load_model_from_local()
        self.tagger = self.initialize_tagger()

    def load_model_from_s3(self):
        model_dict = read_model_dict_from_s3(bucket_name=AWS_MODEL_BUCKET,
                                             bucket_region=AWS_MODEL_REGION,
                                             model_path_location=self.entity_path,
                                             )
        return model_dict

    def load_model_from_local(self):
        file_handler = open(self.entity_path, 'r')
        model_dict = file_handler.read()
        return model_dict

    def initialize_tagger(self):
        tagger = pycrfsuite.Tagger()
        tagger.open_inmemory(self.model_dict)
        return tagger

    def get_entity_path(self):
        return ''

    def get_predictions(self, text, cloud_storage=False):
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
        x, _ = CrfWordEmbeddings.get_processed_x_y([text], [[]])
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
