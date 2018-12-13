# Number detector constants

NUMBER_DIGIT_UNITS = [0, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 7, 8, 9]
DIGIT_UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
NUMERIC_VARIANTS = DIGIT_UNITS + [
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen", "and",
    "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
    "hundred", "thousand", "million", "billion", "trillion", "fourty", "ninty"
]

# Numeral data file name and their columns
NUMBER_NUMERAL_CONSTANT_FILE_NAME = 'numerals_constant.csv'
NUMBER_NUMERAL_FILE_VARIANTS_COLUMN_NAME = 'name_variants'
NUMBER_NUMERAL_FILE_VALUE_COLUMN_NAME = 'number_value'
NUMBER_NUMERAL_FILE_TYPE_COLUMN_NAME = 'number_type'

# type value of number in numeral_constant data file
NUMBER_TYPE_UNIT = 'unit'
NUMBER_TYPE_SCALE = 'scale'


# Units data file and their columns
NUMBER_UNITS_FILE_NAME = 'units.csv'
NUMBER_DATA_FILE_UNIT_VARIANTS_COLUMN_NAME = 'unit_variants'
NUMBER_DATA_FILE_UNIT_VALUE_COLUMN_NAME = 'unit_value'

# Return type keys of number detection
NUMBER_DETECTION_RETURN_DICT_VALUE = 'value'
NUMBER_DETECTION_RETURN_DICT_UNIT = 'unit'
