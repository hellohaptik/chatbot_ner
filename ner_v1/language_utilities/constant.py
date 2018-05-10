import requests
from django.conf import settings

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