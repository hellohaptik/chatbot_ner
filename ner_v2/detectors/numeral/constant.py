# Number detector constants

NUMBER_DIGIT_UNITS = [0, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 7, 8, 9]
DIGIT_UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
NUMERIC_VARIANTS = DIGIT_UNITS + [
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen", "and",
    "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
    "hundred", "thousand", "million", "billion", "trillion", "fourty", "ninty"
]
NUMBER_DATA_FILE_NUMBER = 'number'
NUMBER_DATA_FILE_NAME_VARIANTS = 'name_variants'
NUMBER_DATA_FILE_VALUE = 'value'
NUMBER_DATA_FILE_TYPE = 'type'
NUMBER_TYPE_UNIT = 'unit'
NUMBER_TYPE_SCALE = 'scale'

NUMBER_NUMERAL_CONSTANT_FILE = 'numerals_constant.csv'
NUMBER_UNITS_FILE = 'units.csv'

NUMBER_UNIT_VARIANTS = 'unit_variants'
NUMBER_UNIT_VALUE = 'unit_value'


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
    'last': -1   # used to get last week of any month
}

NUMBER_DETECT_VALUE = 'value'
NUMBER_DETECT_UNIT = 'unit'

LANGUAGE_DATA_DIRECTORY = 'data'
