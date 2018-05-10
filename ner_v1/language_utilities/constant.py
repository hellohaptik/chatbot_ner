import requests
from django.conf import settings
import re

ORIGINAL_TEXT = 'original_text'
SOURCE_LANGUAGE_CODE = 'source_language_code'
TARGET_LANGUAGE_CODE = 'target_language_code'
TRANSLITERATED_TEXT = 'transliterated_text'
TRANSLATED_TEXT = 'translated_text'

TRANSLATION_EXPIRY_TIME = 60 * 60 * 24 * 10
DETECTED_LANGUAGE_SCRIPT = 'detected_language_code'
DETECTED_LANGUAGE_SOURCE = 'detected_source_language'

# ISO 639-1 language codes
HINDI_LANG = 'hi'
ENGLISH_LANG = 'en'

LANGUAGE_UTILITIES_URL = settings.LANGUAGE_MODULE  # URL to language_utitlities

LANGUAGE_UTILITIES = 'language_utilities'

TRANSLATION_URL = 'language/translation'
TRANSLITERATION_URL = 'language/transliteration'
LANGUAGE_DETECTION_URL = 'language/language_detection'

LANGUAGE_UTILITIES_SESSION = requests.Session()
HTTP_TIMEOUT = 20

emoji_pattern = re.compile("["u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           u'\U0001f1e6-\U0001f1ff'
                           u'\U0001f300-\U0001f5ff'
                           u'\U0001f600-\U0001f64f'
                           u'\U0001f680-\U0001f6ff'
                           u'\U0001f910-\U0001f918\U0001f980-\U0001f984\U0001f9c0'
                           u'\U0000200d'
                           u'\U0000fe0f'
                           u'\U00002600-\U000027bf'
                           u'\U0001f3fb-\U0001f3ff'
                           "]+", flags=re.UNICODE)
