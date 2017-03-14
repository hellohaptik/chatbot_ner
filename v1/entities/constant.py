
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
