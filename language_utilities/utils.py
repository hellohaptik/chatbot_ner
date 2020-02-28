# coding=utf-8
from language_utilities.constant import ENGLISH_LANG
from language_utilities.constant import TRANSLATED_TEXT
from chatbot_ner.config import ner_logger, GOOGLE_TRANSLATE_API_KEY
import six.moves.urllib.request
import six.moves.urllib.parse
import six.moves.urllib.error
import requests


TRANSLATE_URL = "https://www.googleapis.com/language/translate/v2?key=" + GOOGLE_TRANSLATE_API_KEY


def unicode_urlencode(params):
    """
    Method to convert the params to url encode data
    Args:
        params (dict): dict containing requests params
    Returns:
        (str): url string with params encoded
    """
    if isinstance(params, dict):
        params = list(params.items())
    return six.moves.urllib.parse.urlencode(
        [(
            k, isinstance(
                v,
                six.text_type
            ) and v.encode('utf-8') or v
        ) for (k, v) in params
        ]
    )


def translate_text(text, source_language_code, target_language_code=ENGLISH_LANG):
    """
    Args:
       text (str): Text snippet which needs to be translated
       source_language_code (str): ISO-639-1 code for language script corresponding to text ''
       target_language_code (str): ISO-639-1 code for target language script
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
        query_params = {"q": text, "format": "text", "source": source_language_code, "target": target_language_code}
        url = TRANSLATE_URL + "&" + unicode_urlencode(query_params)
        request = requests.get(url, timeout=2)
        if request.status_code == 200:
            translate_response = request.json()
            response[TRANSLATED_TEXT] = translate_response["data"]["translations"][0]["translatedText"]
            response['status'] = True
    except Exception as e:
        ner_logger.exception('Exception while translation: %s ' % e)
    return response
