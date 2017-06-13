import os
from chatbot_ner.config import BASE_DIR

# Model Name for city model
city_model_name = 'model_13062017.crf'

# Model path for city
city_model_path = os.path.join(BASE_DIR, 'models', 'crf', 'city', city_model_name)

# input output directory for models that store the temporary files
io_model_directory = os.path.join(BASE_DIR, 'output')


# Entity types for models
CITY_ENTITY_TYPE = 'city'

