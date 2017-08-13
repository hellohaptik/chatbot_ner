CRF_MODEL_TYPE = 'crf'  # constant value for CRF model

# Entity types for models
CITY_ENTITY_TYPE = 'city'
# city tags for crf
CITY_O = 'O'  # Outer tag for BIO tag set
CITY_FROM_B = 'FROM-B'  # Begin tag for property FROM
CITY_TO_B = 'TO-B'  # Begin tag for property TO
CITY_VIA_B = 'VIA-B'  # Begin tag for property VIA
CITY_NORMAL_B = 'NORMAL-B'  # Begin tag for property NORMAL

CITY_FROM_I = 'FROM-I'  # Inner tag for property FROM
CITY_TO_I = 'TO-I'  # Inner tag for property TO
CITY_VIA_I = 'VIA-I'  # Inner tag for property VIA
CITY_NORMAL_I = 'NORMAL-I'  # Inner tag for property NORMAL

MODEL_CITY_VALUE = 'city'  # Dictionary key of model output that stores the value
MODEL_CITY_FROM = 'from'  # Dictionary key of model output that stores whether property is From
MODEL_CITY_TO = 'to'  # Dictionary key of model output that stores whether property is To
MODEL_CITY_VIA = 'via'  # Dictionary key of model output that stores whether property is Via
MODEL_CITY_NORMAL = 'normal'  # Dictionary key of model output that stores whether property is Normal

MODEL_DATE_VALUE = 'date'  # Dictionary key of model output that stores the value
MODEL_DATE_FROM = 'from'  # Dictionary key of model output that stores whether property is From
MODEL_DATE_TO = 'to'  # Dictionary key of model output that stores whether property is To
MODEL_DATE_RANGE = 'range'  # Dictionary key of model output that stores whether property is Via
MODEL_DATE_NORMAL = 'normal'  # Dictionary key of model output that stores whether property is Normal

# Tags for inbound and outbound message in crf
INBOUND = 'i'
OUTBOUND = 'o'

CITY_MODEL_OBJECT = None  # store city model object
