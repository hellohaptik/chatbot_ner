
# ************************ constant used for detection_method ************************

# when entity is detected from message
FROM_MESSAGE = 'message'
# entity is detected from structured_value and verified with detection logic
FROM_STRUCTURE_VALUE_VERIFIED = 'structure_value_verified'
# entity is detected from structured_value and not verified with detection logic
FROM_STRUCTURE_VALUE_NOT_VERIFIED = 'structure_value_not_verified'
# entity is detected from fallback_value
FROM_FALLBACK_VALUE = 'fallback_value'
# entity is detected from a message, through model and verified from the dictionary
FROM_MODEL_VERIFIED = 'model_verified'
# entity is detected from a message, through model and but not verified from the dictionary
FROM_MODEL_NOT_VERIFIED = 'model_not_verified'

# ************************ constant used as key of output dictionary in entity detection ************************
# Consider this example for below reference 'I want to order from mcd'
# entity_value is a key that will store value of entity which is detected. For example Mc Donalds
ENTITY_VALUE = 'entity_value'
# detection is a key that will store how the entity is detected i.e. from chat, structured_value, fallback, etc
DETECTION_METHOD = 'detection'
# original_text is a key that will store actual value that was detected. For example, mcd
ORIGINAL_TEXT = 'original_text'
DETECTION_LANGUAGE = 'language'

ENTITY_VALUE_DICT_KEY = 'value'

# ************************ constants tell us what to do with structured_value ************************
# This will execute entity detection on the structured_value.
STRUCTURED = 0
# This will consider structured_value as an entity value without executing entity detection logic.
UNCHANGED = 1
# This will execute entity detection on structured_value, if it returns None then we consider structure_value as it is.
IF_POSSIBLE = 2
# verifies with dictionary if match then it will return the value else it will take the same value

# ************************ constants used as a key of request  ************************
PARAMETER_MESSAGE = 'message'
PARAMETER_ENTITY_NAME = 'entity_name'
PARAMETER_STRUCTURED_VALUE = 'structured_value'
PARAMETER_STRUCTURED_VALUE_VERIFICATION = 'structured_value_verification'
PARAMETER_FALLBACK_VALUE = 'fallback_value'
PARAMETER_BOT_MESSAGE = 'bot_message'
PARAMETER_TIMEZONE = 'timezone'
PARAMETER_REGEX = 'regex'

# Language parameters of the query.
PARAMETER_LANGUAGE_SCRIPT = 'language_script'  # ISO 639 code for language. For eg, 'en' for 'Namaste', 'Hello'
PARAMETER_SOURCE_LANGUAGE = 'source_language'  # ISO 639 code vocabulary.  For eg, 'hi' for 'Namaste', 'en' for 'Hello'
# ********************** constant used to define dict type in data dictionary *********************
DICTIONARY_DATA_VARIANTS = 'variants'

# **********************constants used for number detection************************************

DIGIT_UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
NUMERIC_VARIANTS = DIGIT_UNITS + [
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen", "and",
    "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
    "hundred", "thousand", "million", "billion", "trillion", "fourty", "ninty"
]
PARAMETER_MIN_DIGITS = 'min_number_digits'
PARAMETER_MAX_DIGITS = 'max_number_digits'

#  **********************constants used for name detection************************************

FIRST_NAME = 'first_name'
MIDDLE_NAME = 'middle_name'
LAST_NAME = 'last_name'


PARAMETER_FUZZINESS = 'fuzziness'
PARAMETER_MIN_TOKEN_LEN_FUZZINESS = 'min_token_len_fuzziness'
DATASTORE_VERIFIED = 'datastore_verified'
CRF_MODEL_VERIFIED = 'crf_model_verified'

#  **********************constants used for text detection************************************

PARAMETER_READ_MODEL_FROM_S3 = 'read_model_from_s3'
PARAMETER_CLOUD_EMBEDDINGS = 'cloud_embeddings'
PARAMETER_LIVE_CRF_MODEL_PATH = 'live_crf_model_path'
