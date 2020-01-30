# DATE IDENTIFICATION constant

ENTITY_MONTH = 'month_list'
ENTITY_DAY = 'day_list'

TYPE_EXACT = 'date'
TYPE_EVERYDAY = 'everyday'
TYPE_PAST = 'past'  # for dates in the past
TYPE_TODAY = 'today'
TYPE_TOMORROW = 'tomorrow'
TYPE_YESTERDAY = 'yesterday'
TYPE_DAY_AFTER = 'day_after'
TYPE_DAY_BEFORE = 'day_before'
TYPE_N_DAYS_AFTER = 'after_n_days'
TYPE_NEXT_DAY = 'day_in_next_week'
TYPE_THIS_DAY = 'day_within_one_week'


# ORIGINAL constants
# TYPE_NEXT_DAY = 'next_day'
# TYPE_CURRENT_DAY = 'current_day'

TYPE_POSSIBLE_DAY = 'possible_day'

# BUDGET IDENTIFICATION

BUDGET_TYPE_NORMAL = 'normal_budget'
BUDGET_TYPE_TEXT = 'text_budget'

# CAROUSEL DETECTION
API_NAME = 'api_name'

# TIME DETECTION
AM_MERIDIEM = 'am'
PM_MERIDIEM = 'pm'
TWELVE_HOUR = 12
EVERY_TIME_TYPE = 'ev'

# WEEK DETECTION
WEEKDAYS = 'weekdays'
REPEAT_WEEKDAYS = 'repeat_weekdays'
WEEKENDS = 'weekends'
REPEAT_WEEKENDS = 'repeat_weekends'
TYPE_REPEAT_DAY = 'repeat_day'


MONTH_DICT = {
    u'1': [u'jan', u'january'],
    u'10': [u'october', u'oct'],
    u'11': [u'november', u'nov'],
    u'12': [u'december', u'dec'],
    u'2': [u'february', u'feb'],
    u'3': [u'mar', u'march'],
    u'4': [u'apr', u'april'],
    u'5': [u'may'],
    u'6': [u'jun', u'june'],
    u'7': [u'july', u'jul'],
    u'8': [u'august', u'aug'],
    u'9': [u'september', u'sept', u'sep']
}

DAY_DICT = {
    u'1': [u'sun', u'sunday'],
    u'2': [u'mon', u'monday'],
    u'3': [u'tuesday', u'tue'],
    u'4': [u'wednesday', u'wed'],
    u'5': [u'thu', u'thursday', u'thurs', u'thur'],
    u'6': [u'fri', u'friday'],
    u'7': [u'saturday', u'sat']
}

# CONSTANTS USED FOR CITY DETECTION
CITY_FROM_PROPERTY = 'from'
CITY_TO_PROPERTY = 'to'
CITY_VIA_PROPERTY = 'via'
CITY_NORMAL_PROPERTY = 'normal'
CITY_VALUE = 'value'
ORIGINAL_CITY_TEXT = 'text'
CITY_DETECTION_METHOD = 'detection_method'

# CONSTANTS USED FOR DATE DETECTION
DATE_FROM_PROPERTY = 'from'
DATE_TO_PROPERTY = 'to'
DATE_START_RANGE_PROPERTY = 'start_range'
DATE_END_RANGE_PROPERTY = 'end_range'
DATE_NORMAL_PROPERTY = 'normal'
DATE_TYPE_PROPERTY = 'type'
DATE_VALUE = 'value'
ORIGINAL_DATE_TEXT = 'text'
DATE_DETECTION_METHOD = 'detection_method'


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
MODEL_VERIFIED = 'model_verified'

#  **********************constants used for text detection************************************

PARAMETER_READ_MODEL_FROM_S3 = 'read_model_from_s3'
PARAMETER_READ_EMBEDDINGS_FROM_REMOTE_URL = 'read_embeddings_from_remote_url'
PARAMETER_LIVE_CRF_MODEL_PATH = 'live_crf_model_path'

#  ********************** emoji removal ******************************************************
EMOJI_RANGES = {
    'regional_indicators': u'\U0001f1e6-\U0001f1ff',
    'misc_pictograms': u'\U0001f300-\U0001f5ff',
    'emoticons': u'\U0001f600-\U0001f64f',
    'transport': u'\U0001f680-\U0001f6ff',
    'supplemental': u'\U0001f900-\U0001f9ff\U0001f980-\U0001f984\U0001f9c0',
    'zero_width_separator': u'\U0000200d',
    'variation_selector': u'\U0000fe0f',
    'misc_dingbats': u'\U00002600-\U000027bf',
    'emoticon_skintones': u'\U0001f3fb-\U0001f3ff',
    'letterlike_symbols': u'\U00002100-\U0000214F',
    'arrows': u'\U00002190-\U000021FF',
    'miscellaneous_technical': u'\U00002300-\U000023FF',
    'enclosed_alphanumerics': u'\U00002460-\U000024FF',
    'geometric_shapes': u'\U000025A0-\U000025FF',
}
