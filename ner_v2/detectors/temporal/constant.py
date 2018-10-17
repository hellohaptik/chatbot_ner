from chatbot_ner.config import BASE_DIR

DATE_CONSTANT_FILE = 'date_constant.csv'
TIME_CONSTANT_FILE = 'time_constant.csv'
DATETIME_CONSTANT_FILE = 'datetime_diff_constant.csv'
NUMERALS_CONSTANT_FILE = 'numbers_constant.csv'

CONSTANT_FILE_KEY = 'key'

MONTH_DATE_REF_TYPE = 'month_date_ref'
RELATIVE_DATE = 'relative_date'
DATE_LITERAL_TYPE = 'date_literal'
MONTH_LITERAL_TYPE = 'month_literal'
WEEKDAY_TYPE = 'weekday'
MONTH_TYPE = 'month'
ADD_DIFF_DATETIME_TYPE = 'add_diff_datetime'
REF_DATETIME_TYPE = 'ref_datetime'

HOUR_TIME_TYPE = 'hour'
MINUTE_TIME_TYPE = 'minute'
DAYTIME_MERIDIAN = 'daytime_meridian'

POSITIVE_TIME_DIFF = 'df'
NEGATIVE_TIME_DIFF = 'ndf'

BASE_DATE_DETECTOR_PATH = BASE_DIR.rstrip('/') + '/ner_v2/detectors/temporal/date/'
LANGUAGE_DATE_DETECTION_FILE = 'date_detection.py'
LANGUAGE_DATA_DIRECTORY = 'data'
