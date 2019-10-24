# Number detector constants

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
NUMBER_DATA_FILE_UNIT_TYPE_COLUMN_NAME = 'unit_type'

# Return type keys of number detection
NUMBER_DETECTION_RETURN_DICT_VALUE = 'value'
NUMBER_DETECTION_RETURN_DICT_UNIT = 'unit'


# Number range data file name and columns
NUMBER_RANGE_KEYWORD_FILE_NAME = 'number_range_keywords.csv'
COLUMN_NUMBER_RANGE_VARIANTS = 'range_variants'
COLUMN_NUMBER_RANGE_POSITION = 'position'
COLUMN_NUMBER_RANGE_RANGE_TYPE = 'range_type'


# Number range types
NUMBER_RANGE_MIN_TYPE = 'min'
NUMBER_RANGE_MAX_TYPE = 'max'
NUMBER_RANGE_MIN_MAX_TYPE = 'min_max'

# Replace text for number detected in number range
NUMBER_REPLACE_TEXT = '__dnumber__'


# Number range detection return dict keys
NUMBER_RANGE_MIN_VALUE = 'min_value'
NUMBER_RANGE_MAX_VALUE = 'max_value'
NUMBER_RANGE_VALUE_UNIT = 'unit'
NUMBER_RANGE_ABS_VALUE = 'abs_value'
