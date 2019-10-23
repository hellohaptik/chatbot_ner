DATE_CONSTANT_FILE = 'date_constant.csv'
TIME_CONSTANT_FILE = 'time_constant.csv'
DATETIME_CONSTANT_FILE = 'datetime_diff_constant.csv'
NUMERALS_CONSTANT_FILE = 'numbers_constant.csv'

# timezones data file and its columns
# name of the data file
TIMEZONES_CONSTANT_FILE = 'timezones.csv'
# index of the csv file(try using the common standard)
TIMEZONES_CODE_COLUMN_NAME = 'code'
# all regions in Olson format pytz
TIMEZONES_ALL_REGIONS_COLUMN_NAME = 'all_regions'
# preferred region in the above all_regions (Olson format pytz)
TIMEZONES_PREFERRED_REGION_COLUMN_NAME = 'preferred'
# Formal usage variants of the index
TIMEZONE_VARIANTS_VARIANTS_COLUMN_NAME = 'timezone_variants'

CONSTANT_FILE_KEY = 'key'

# date type referring to date in month like "2 tarikh" (reference: hindi)
MONTH_DATE_REF_TYPE = 'month_date_ref'

# date type referring to word like "kal", "aaj" (reference: hindi)
RELATIVE_DATE = 'relative_date'

# date type referring to literal word for day like "din", "dino" (reference: hindi)
DATE_LITERAL_TYPE = 'date_literal'

# date type referring to literal word for month like "mahina", "mahino" (reference: hindi)
MONTH_LITERAL_TYPE = 'month_literal'

# date type referring to weekdays like "friday", "monday", "sunday"
WEEKDAY_TYPE = 'weekday'

# date type referring to month of year like "jan", "feb"
MONTH_TYPE = 'month'

# datetime_diff type referring to words like "baad", "pehle", "pichhla"
ADD_DIFF_DATETIME_TYPE = 'add_diff_datetime'

# datetime_diff type referring to words like "sava", "paune"
REF_DATETIME_TYPE = 'ref_datetime'

HOUR_TIME_TYPE = 'hour'
MINUTE_TIME_TYPE = 'minute'
DAYTIME_MERIDIEM = 'daytime_meridiem'

POSITIVE_TIME_DIFF = 'df'
NEGATIVE_TIME_DIFF = 'ndf'

# DATE IDENTIFICATION constant
ENTITY_MONTH = 'month_list'
ENTITY_DAY = 'day_list'

# DATE TYPES
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
TYPE_POSSIBLE_DAY = 'possible_day'

# ORIGINAL constants
# TYPE_NEXT_DAY = 'next_day'
# TYPE_CURRENT_DAY = 'current_day'

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
    1: [u'jan', u'january'],
    10: [u'october', u'oct'],
    11: [u'november', u'nov'],
    12: [u'december', u'dec'],
    2: [u'february', u'feb'],
    3: [u'mar', u'march'],
    4: [u'apr', u'april'],
    5: [u'may'],
    6: [u'jun', u'june'],
    7: [u'july', u'jul'],
    8: [u'august', u'aug'],
    9: [u'september', u'sept', u'sep']
}
DAY_DICT = {
    1: [u'sun', u'sunday'],
    2: [u'mon', u'monday'],
    3: [u'tuesday', u'tue'],
    4: [u'wednesday', u'wed'],
    5: [u'thu', u'thursday', u'thurs', u'thur'],
    6: [u'fri', u'friday'],
    7: [u'saturday', u'sat']
}

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
ORDINALS_MAP = {
    'first': 1,
    '1st': 1,
    'second': 2,
    '2nd': 2,
    'third': 3,
    '3rd': 3,
    'fourth': 4,
    '4th': 4,
    'fifth': 5,
    '5th': 5,
    'sixth': 6,
    '6th': 6,
    'seventh': 7,
    '7th': 7,
    'eighth': 8,
    '8th': 8,
    'ninth': 9,
    '9th': 9,
    'tenth': 10,
    '10th': 10,
    'last': -1  # used to get last week of any month
}
