# coding=utf-8
from googletrans import Translator
from ner_v1.language_utilities.constant import ENGLISH_LANG
from ner_v1.language_utilities.constant import TRANSLATED_TEXT
from chatbot_ner.config import ner_logger
import json
from ner_v1.language_utilities.constant import TRANSLATION_URL, TRANSLATION_EXPIRY_TIME, \
    TRANSLITERATION_URL, TRANSLITERATED_TEXT, HINDI_LANG, HTTP_TIMEOUT, LANGUAGE_UTILITIES,\
    LANGUAGE_UTILITIES_URL, LANGUAGE_UTILITIES_SESSION, emoji_pattern
import requests

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
    except Exception, e:
        ner_logger.debug('Exception while translation: %s ' % e)
    return response

def check_json_compatibility_translation(text, source_script, target_script):
    """
    This class used to check if text is a json and if it is it translates the text part.
    Args:
        text (str): The text for which translation has to be done
        source_script (str): The language code in which the language is written in.
        target_script (str): The language in which translation has to be performed.
    Returns:
        response (str): It returns a json dump.

    """
    data = text
    try:
        data = json.loads(text)
        if data:
            data['text'] = language_module_request(language_url=TRANSLATION_URL,
                                                   source_language_code=source_script,
                                                   target_language_code=target_script,
                                                   text=data['text'])[TRANSLATED_TEXT]
            # To handle emojis as translator doesnt handle emojis
            # To handle actionable_text
            try:
                actionable_text = data['data']['items'][0]['actionable_text']
                actionable_text = remove_emoji(actionable_text)
                data['data']['items'][0]['actionable_text'] = language_module_request(
                    language_url=TRANSLATION_URL,
                    source_language_code=source_script,
                    target_language_code=target_script,
                    text=actionable_text)[TRANSLATED_TEXT]
            except Exception:
                ner_logger.debug('No actionable_text available for %s' % text)
            # To handle message
            try:
                message = data['data']['items'][0]['payload']['message']
                message = remove_emoji(message)
                message_split = message.split('{')
                for i in range(len(message_split)):
                    if '}' not in message_split[i]:
                        message_split[i] = language_module_request(language_url=TRANSLATION_URL,
                                                                   source_language_code=source_script,
                                                                   target_language_code=target_script,
                                                                   text=message_split[i])[TRANSLATED_TEXT]
                data['data']['items'][0]['payload']['message'] = '{'.join(message_split)
            except Exception:
                ner_logger.debug('No message available for %s' % text)
    except Exception:
        ner_logger.debug('Cannot load json')
    return json.dumps(data)


def check_json_compatibility_transliteration(text, source_script, target_script):
    """
    This class used to check if text is a json and if it is it transliterates the text part.
    Args:
        text (str): The text for which translation has to be done
        source_script (str): The language code in which the language is written in.
        target_script (str): The language in which translation has to be performed.
    Returns:
        response (str): It returns a json dump.
    """
    data = text
    try:
        data = json.loads(text)
        if data:
            data['text'] = language_module_request(language_url=TRANSLITERATION_URL,
                                                   source_language_code=source_script,
                                                   target_language_code=target_script,
                                                   text=data['text'])[TRANSLITERATED_TEXT]
            #           To handle actionable_text
            try:
                actionable_text = data['data']['items'][0]['actionable_text']
                data['data']['items'][0]['actionable_text'] = language_module_request(
                    language_url=TRANSLITERATION_URL,
                    source_language_code=source_script,
                    target_language_code=target_script,
                    text=actionable_text)[TRANSLITERATED_TEXT]
            except Exception:
                ner_logger.debug('No actionable_text available for %s' % text)
            #           To handle message
            try:
                message = data['data']['items'][0]['payload']['message']
                message_split = message.split('{')
                for i in range(len(message_split)):
                    if '}' not in message_split[i]:
                        response = language_module_request(language_url=TRANSLITERATION_URL,
                                                           source_language_code=source_script,
                                                           target_language_code=target_script,
                                                           text=message_split[i])
                        message_split[i] = response[TRANSLITERATED_TEXT]
                data['data']['items'][0]['payload']['message'] = '{'.join(message_split)
            except Exception:
                ner_logger.debug('No message available for %s' % text)
    except Exception:
        ner_logger.debug('Cannot load json')
    return json.dumps(data)


def translate_haptik_message(text, source_script, target_script):
    """
    The following is used to translate text containing hsl characters.
    Args:
        text (str): The text that has to be translated
        source_script (str): The language code in which the language is written in.
        target_script (str): The language in which translation has to be performed.

    Returns:
        text (str): The translated sentence with hsl compatibility.
    Example
        text:u'{"text":"Hey [user.name], <b><i>Introducing IPL updates on Haptik</i>!</b><br>
        Now get toss info, score alerts and a lot more for IPL 2017.
         Subscribe now to get your own <b><i>#CricketBuddy</b></i> :)","type":"BUTTON","data":{"items"
        :[{"actionable_text":"Set Score Alerts","location_required":false,"uri":"","is_default":1,"type":"TEXT_ONLY",
        "payload":{"link":"","message":"Yes! Keep me updated","gogo_message":""},"emoji":""}]}}'

        translate_haptik_message(source_script='en', target_script='hi', text=text)
        >> {"text": "\u0905\u0930\u0947 [user.name], <b> <i> \</ b> </ i> :)",
        "type": "BUTTON", "data": {"items": [{"actionable_text": "Set Score Alerts", "location_required": false,
        "uri": "", "is_default": 1, "type": "TEXT_ONLY", "payload":
        {"gogo_message": "", "message": "Yes! Keep me updated", "link": ""}, "emoji": ""}]}}
    """
    status = False
    try:
        if isinstance(text, str):
            text = text.decode('utf-8')
        response_split = text.split('<m>')
        for i in range(len(response_split)):
            if '{' not in response_split[i]:
                response_split[i] = remove_emoji(response_split[i])
                response_split[i] = language_module_request(language_url=TRANSLATION_URL,
                                                            source_language_code=source_script,
                                                            target_language_code=target_script,
                                                            text=response_split[i])[TRANSLATED_TEXT]
            elif 'text' in response_split[i]:
                response_split[i] = ((check_json_compatibility_translation(
                    text=response_split[i], source_script=source_script, target_script=target_script)))
            else:
                response_split_braces = response_split[i].split('{')
                for j in range(len(response_split_braces)):
                    if '}' not in response_split_braces[j]:
                        response_split_braces[j] = remove_emoji(response_split_braces[j])
                        response_split_braces[j] = language_module_request(
                            language_url=TRANSLATION_URL,
                            source_language_code=source_script,
                            target_language_code=target_script,
                            text=response_split_braces[j])[TRANSLATED_TEXT]
                response_split[i] = '{'.join(response_split_braces)
        text = '<m>'.join(response_split)
        status = True
    except ValueError as e:
        ner_logger.debug("Exception while translating, Error %s" % str(e))
    return text, status


def transliterate_haptik_message(text, source_script, target_script=ENGLISH_LANG):
    """
    The following is used to translate text containing hsl characters.
    Args:
        text (str): The text that has to be translated
        source_script (str): The language code in which the language is written in.
        target_script (str): The language in which translation has to be performed.

    Returns:
        text (str): The translated sentence with hsl compatibility.

    Examples:
        text:{"text": "\u0905\u0930\u0947 [user.name], <b> <i> \u0939\u0948\u092a\u094d\u092a
        \u0940\u0915 \u092a\u0930 \u0906\u0908\u092a\u0940\u090f </ b> </ i> :)",
        "type": "BUTTON", "data": {"items": [{"actionable_text": "Set Score Alerts",
        "location_required": false,
        "uri": "", "is_default": 1, "type": "TEXT_ONLY", "payload":
        {"gogo_message": "", "message": "Yes! Keep me updated", "link": ""}, "emoji": ""}]}}

        transliterate_haptik_message(source_script='hi', target_script='en',
        text=text)


         >> '{"text": "are i  happik par aipiel update pesh karna   i
        now aipiel  ke liye tos jankari  score alrt aur bhut kuchh recieve karen  apna recieve
         karne ke liye abhi sadashyata len swyn     i   criketbddi       i   ",
        "type": "BUTTON", "data": {"items": [{"actionable_text": "Set Score Alerts", "loc
        action_required": false, "uri": "", "is_default": 1, "type": "TEXT_ONLY", "payload":
        {"link": "", "message": "Yes! Keep me updated", "gogo_message": ""}, "emoji": ""}]}}'
    """
    status = False
    try:
        response_split = text.split('<m>')
        for i in range(len(response_split)):
            if '{' not in response_split[i]:
                response_split[i] = language_module_request(language_url=TRANSLITERATION_URL,
                                                            source_language_code=source_script,
                                                            target_language_code=target_script,
                                                            text=response_split[i])[TRANSLITERATED_TEXT]
                if not response_split[i]:
                    response_split[i] = '  '
            elif 'text' in response_split[i]:
                response_split[i] = (check_json_compatibility_transliteration(
                    text=response_split[i], source_script=source_script, target_script=target_script))
            else:
                response_split_braces = response_split[i].split('{')
                for j in range(len(response_split_braces)):
                    if '}' not in response_split_braces[j]:
                        response_split_braces[j] = language_module_request(
                            language_url=TRANSLITERATION_URL,
                            source_language_code=source_script,
                            target_language_code=target_script,
                            text=response_split_braces[j])[TRANSLITERATED_TEXT]
                response_split[i] = '{'.join(response_split_braces)
        text = '<m>'.join(response_split)
        status = True
    except ValueError as e:
        ner_logger.debug("Exception while transliteration, Error %s" % str(e))
    return text, status


def remove_emoji(text):
    """
    This method is used to remove any emojis if present.
    Args:
        text (str): The input text from which emojis have to be removed

    Returns:
        text (str): Text without any emojis.
    """

    return emoji_pattern.sub(r'', text)


def language_module_request(language_url, **kwargs):
    """
    Make a HTTP GET request with kwargs as params to language_utilities for the given entity key

    Args:
        language_url (str): Key of the language_module url to be hit,
                              see ares.constant.LANGUAGE_UTILITIES_URLS for the mapping
        **kwargs: everything else to be sent as parameters in the GET request

    Returns:
        dict: valid dict values from json.loads

    """
    ner_logger.debug(str(language_url))
    url = LANGUAGE_UTILITIES_URL + language_url
    params = encode_values(kwargs)
    return language_get(url=url, params=params, service_name=LANGUAGE_UTILITIES)


def language_get(url, params, service_name):
    """
    Send HTTP GET call to url with params using requests.Session mapped to service_name in api_call.session_dict
    with a Timeout of 20s

    Args:
        url (str): url to hit
        params (dict): dictionary containing HTTP parameters
        service_name (str): 'language_utilities'

    Returns:
        valid dict values from json.loads: value of 'data' key in response of the HTTP call

    Raises:
        KeyError if service_name doesn't exist in api_call.session_dict ,
        requests lib HTTP Exceptions except requests.exceptions.Timeout

    """
    entity_data = None
    try:
        response = LANGUAGE_UTILITIES_SESSION.get(url,
                                                              params=encode_values(params),
                                                              timeout=HTTP_TIMEOUT)
        if response and response.status_code == 200:
            entity_data = json.loads(response.text)['data']
    except requests.exceptions.Timeout:
        ner_logger.exception('HTTP Connection Timeout for %s : %s' % (service_name, url))
    return entity_data


def encode_values(dictionary):
    """
    It used to encode str  values present in dictionary to unicode.
    Args:
        dictionary (dict): The dictionary whose values have to be encoded into unicdoe

    Returns:
        dictionary (dict): A dictionary in which all the values are in unicode.
    """
    for key, value in iteritems(dictionary):
        if type(value) != str:
            value = unicode(value)
            value = encode_text(value)
        dictionary[key] = value
    return dictionary


def encode_text(text, lower=False, strip=False, encoding='utf-8'):
    """

    Encode encoded string using specified encoding with optionally unicode.lower and unicode.strip transforms

    Args:
        text (str): string to encode
        lower (bool, optional): if True, unicode.lower is applied
        strip (bool, optional): if True, unicode.strip is applied
        encoding (str, optional): encoding to use to encode the string, defaults to 'utf-8'

    Returns:
        str: encoded string using the specified decoding

    """
    if lower:
        text = text.lower()
    if strip:
        text = text.strip()

    text_str = text.encode(encoding=encoding, errors='ignore')
    return text_str
