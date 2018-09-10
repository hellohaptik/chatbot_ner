from lib.nlp.tokenizer import Tokenizer, NLTK_TOKENIZER
from .crf_preprocess_data import CrfPreprocessData
from .get_crf_tagger import CrfModel
from chatbot_ner.config import MODELS_PATH


class CrfDetection(object):
    """
    This method is used to detect a text entity using the Crf model.
    """
    def __init__(self, entity_name, cloud_storage=False):
        """
        This method is used to detect text entities using the Crf model
        Args:
            entity_name (str): Name of the entity for which the entity has to be detected
            cloud_storage (bool): To indicate if cloud storage settings is required.
        """
        self.entity_name = entity_name
        self.cloud_storage = cloud_storage

        crf_model = CrfModel(entity_name=self.entity_name)

        if self.cloud_storage:
            self.tagger = crf_model.load_model()
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
        x, _ = CrfPreprocessData.get_processed_x_y([text], [[]], cloud_storage=self.cloud_storage)
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

c = 0
for e in temp:
    print(e)
    x = text[e[0] + c:e[1] + c]
    tx = word_tokenize(x)
    print(tx)
    for i in range(len(tx)):
        if i == 0:
            tx[i] = 'B_en_' + tx[i]
        else:
            tx[i] = 'I_en_' + tx[i]
    dtx = detokenizer.detokenize(tx, return_str=True)
    print(dtx)
    text = text[:e[0] + c] + dtx + text[e[1] + c:]
    c += len(tx) * 5
    print(text)

c = 0
for e in temp:
    print(e)
    x = text[e[0] + c:e[1] + c]
    tx = x.split()
    len_tx = len(tx)
    print(tx)
    for i in range(len(tx)):
        if i == 0:
            tx[i] = 'B_en_' + tx[i]
        else:
            tx[i] = 'I_en_' + tx[i]
    dtx = detokenizer.detokenize(tx, return_str=True)
    print(dtx)
    text = text[:e[0] + c] + dtx + text[e[1] + c:]
    c += len_tx * 5
    print(text)
