# coding=utf-8
from googletrans import Translator
from ner_v1.language_utilities.constant import ENGLISH_LANG
from ner_v1.language_utilities.constant import TRANSLATED_TEXT
from chatbot_ner.config import ner_logger


def translate_text(text, source_language_code, target_language_code=ENGLISH_LANG):
    """   
    Args:
        text: Text snippet which needs to be translated
        source_language_code: ISO-639-1 code for language script corresponding to text ''
        target_language_code: ISO-639-1 code for target language script
    Return: 
        dict: Dictionary containing two keys corresponding to 'status'(bool) and 'translated text'(unicode)
        For example: Consider following example
                     text: 'नमस्ते आप कैसे हैं'
                     'source_language_code': 'hi'
                     'target_language_code': 'en'
                     
                     translate_text(text, 'hi', 'en')
                     >> {'status': True,
                        'translated_text': 'Hello how are you'}
    """
    response = {TRANSLATED_TEXT: None, 'status': False}
    try:
        tr = Translator()
        response[TRANSLATED_TEXT] = tr.translate(text, src=source_language_code, dest=target_language_code).text
        response['status'] = True
    except Exception, e:
        ner_logger.debug('Exception while translation: %s ' % e)
    return response
