# DATE IDENTIFICATION constant

ENTITY_MONTH = 'month_list'
ENTITY_DAY = 'day_list'

TYPE_EXACT = 'date'
TYPE_EVERYDAY = 'everyday'
TYPE_TODAY = 'today'
TYPE_TOMORROW = 'tomorrow'
TYPE_YESTERDAY = 'yesterday'
TYPE_DAY_AFTER = 'day_after'
TYPE_DAY_BEFORE = 'day_before'

# Note constant values have changed, haptik_api would break at
# haptik_api/ares/entities/constant.py
# haptik_api/ares/lib/external_api_response/cron.py
TYPE_NEXT_DAY = 'day_in_next_week'
TYPE_THIS_DAY = 'day_within_one_week'

# ORIGINAL constants
# TYPE_NEXT_DAY = 'next_day'
# TYPE_CURRENT_DAY = 'current_day'

TYPE_POSSIBLE_DAY = 'possible_day'

# BUDGET IDENTIFICATION

BUDGET_TYPE_NORMAL = 'normal_budget'
BUDGET_TYPE_TEXT = 'text_budget'
ES_BUDGET_LIST = 'budget'

# CAROUSEL DETECTION
API_NAME = 'api_name'

# TIME DETECTION
AM_MERIDIEM = 'am'
PM_MERIDIEM = 'pm'
TWELVE_HOUR = 12

# WEEK DETECTION
WEEKDAYS = 'weekdays'
REPEAT_WEEKDAYS = 'repeat_weekdays'
WEEKENDS = 'weekends'
REPEAT_WEEKENDS = 'repeat_weekends'
TYPE_REPEAT_DAY = 'repeat_day'
START_RANGE = 'start_range'
END_RANGE = 'end_range'
REPEAT_START_RANGE = 'repeat_start_range'
REPEAT_END_RANGE = 'repeat_end_range'
DATE_START_RANGE = 'date_start_range'
DATE_END_RANGE = 'date_end_range'

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
    u'9': [u'september', u'sept']
}

DAY_DICT = {
    u'1': [u'sun', u'sunday'],
    u'2': [u'mon', u'monday'],
    u'3': [u'tuesday', u'tue'],
    u'4': [u'wednesday', u'wed'],
    u'5': [u'thu', u'thursday'],
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
