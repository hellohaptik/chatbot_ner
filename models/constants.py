import os
from chatbot_ner.config import BASE_DIR

# Model Name for city model
city_model_name = 'model_13062017.crf'

# Model path for city
city_model_path = os.path.join(BASE_DIR, 'data', 'models', 'crf', 'city', city_model_name)

# Entity types for models
CITY_ENTITY_TYPE = 'city'

