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
