# coding=utf-8
from ner_v1.language_utilities.constant import ENGLISH_LANG
from ner_v1.language_utilities.constant import TRANSLATED_TEXT
from chatbot_ner.config import ner_logger, GOOGLE_TRANSLATE_API_KEY
import urllib
import demjson


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
        params = params.items()
    return urllib.urlencode([(k, isinstance(v, unicode) and v.encode('utf-8') or v) for k, v in params])


def make_request(url):
    """
    Method to make a request call and return data for given url
    Args:
        url (str): url to which to make request
    Returns:
        (str): returns url response data
    """
    return urllib.urlopen(url).read()


def get_translate(text, target, source):
    """
    Method to get raw response data of google translation API to translate given text from target
    language to source language
    Args:
        text (str): text to be translated
        target (str): language code in which text will be translated
        source (str): language code of the given text
    Returns:
        (dict): dict containing response
        For example: Consider following example
                 text: 'नमस्ते आप कैसे हैं'
                'source': 'hi'
                'target': 'en'

                >> get_translate(text, 'hi', 'en')
                >> {u'data': {u'translations': [{u'translatedText': u'\u092e\u0947\u0930\u093e \u0928\u093e\'}]}}
    """
    query_params = {"q": text, "source": source, "target": target}
    url = TRANSLATE_URL + "&" + unicode_urlencode(query_params)
    try:
        return demjson.decode(make_request(url))
    except Exception, e:
        ner_logger.debug('Exception while decoding json response data for translation: %s ' % e)
        return None


def translate(text, source_language_code, target_language_code=ENGLISH_LANG):
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
        response[TRANSLATED_TEXT] = \
            get_translate(text, target_language_code,
                          source_language_code)["data"]["translations"][0]["translatedText"].replace('&#39;', "'")
        response['status'] = True
    except Exception, e:
        ner_logger.debug('Exception while translation: %s ' % e)
    return response
