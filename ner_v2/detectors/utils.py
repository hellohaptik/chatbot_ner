import os

import pytz
import six

from chatbot_ner.config import ner_logger
from ner_v2.constant import LANGUAGE_DATA_DIRECTORY


def get_lang_data_path(detector_path, lang_code):
    data_directory_path = os.path.abspath(
        os.path.join(
            os.path.dirname(detector_path).rstrip(os.sep),
            lang_code,
            LANGUAGE_DATA_DIRECTORY
        )
    )
    return data_directory_path


def get_timezone(timezone):
    if not isinstance(timezone, six.string_types) and hasattr(timezone, 'localize'):
        return timezone
    try:
        timezone = pytz.timezone(timezone)
    except Exception as e:
        ner_logger.debug('Timezone error: %s ' % e)
        timezone = pytz.timezone('UTC')
        ner_logger.debug('Default timezone passed as "UTC"')
    return timezone
