# Stdlib imports
import os

# Following index is used for gogo entity detection
ES_INDEX_TEXT_DETECTION = 'gogo_entity_data'
ES_DOC_TYPE_TEXT_DETECTION = 'data_dictionary'

# ************************ constant used for detection_method ************************

# when entity is detected from message
FROM_MESSAGE = 'message'
# entity is detected from structured_value and verified with detection logic
FROM_STRUCTURE_VALUE_VERIFIED = 'structure_value_verified'
# entity is detected from structured_value and not verified with detection logic
FROM_STRUCTURE_VALUE_NOT_VERIFIED = 'structure_value_not_verified'
# entity is detected from fallback_value
FROM_FALLBACK_VALUE = 'fallback_value'

# ************************ constant used as key of output dictionary in entity detection ************************
# Consider this example for below reference 'I want to order from mcd'
# entity_value is a key that will store value of entity which is detected. For example Mc Donalds
ENTITY_VALUE = 'entity_value'
# detection is a key that will store how the entity is detected i.e. from chat, structured_value, fallback, etc
DETECTION_METHOD = 'detection'
# original_text is a key that will store actual value that was detected. For example, mcd
ORIGINAL_TEXT = 'original_text'

# ************************ constants tell us what to do with structured_value ************************
# This will execute entity detection on the structured_value.
STRUCTURED_VALUE_DICTIONARY_VERIFICATION = 0
# This will consider structured_value as an entity value without executing entity detection logic.
STRUCTURED_VALUE_WITHOUT_DICTIONARY_VERIFICATION = 1
# This will execute entity detection on structured_value, if it returns None then we consider structure_value as it is.
STRUCTURED_VALUE_NORMAL_VERIFICATION = 2
# verifies with dictionary if match then it will return the value else it will take the same value

# ************************ constants used as a key of request  ************************
PARAMETER_MESSAGE = 'message'
PARAMETER_ENTITY_NAME = 'entity_name'
PARAMETER_STRUCTURED_VALUE = 'structured_value'
PARAMETER_STRUCTURED_VALUE_VERIFICATION = 'structured_value_verification'
PARAMETER_FALLBACK_VALUE = 'fallback_value'
PARAMETER_EXPERT_MESSAGE = 'expert_message'

DICTIONARY_DATA_GENERAL = 'general'
DICTIONARY_DATA_VARIANTS = 'variants'
DICTIONARY_DATA_NGRAMS = 'ngrams'
