import os
from chatbot_ner.config import BASE_DIR

# Model Name for city model
city_model_name = 'model_13062017.crf'

# Model path for city
CITY_MODEL_PATH = os.path.join(BASE_DIR, 'data', 'models', 'crf', 'city', city_model_name)

# Entity types for models
CITY_ENTITY_TYPE = 'city'


# city tags for crf
CITY_FROM_B = 'from-B'
CITY_TO_B = 'to-B'
CITY_VIA_B = 'via-B'
CITY_FROM_I = 'from-I'
CITY_TO_I = 'to-I'
CITY_VIA_I = 'via-I'

CITY_VALUE = 'city'
FROM = 'from'
TO = 'to'
VIA = 'via'

# Tags for inbound and outbound message in crf
INBOUND = 'i'
OUTBOUND = 'o'
