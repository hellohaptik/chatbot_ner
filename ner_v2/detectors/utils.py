import os
import six
from ner_v2.constant import LANGUAGE_DATA_DIRECTORY


def ensure_str(text, encoding="utf-8"):
    if isinstance(text, (int, float)):
        return six.text_type(text)
    if isinstance(text, bytes):
        text = text.decode(encoding=encoding)
    return text


def get_lang_data_path(detector_path, lang_code):
    data_directory_path = os.path.abspath(
        os.path.join(
            os.path.dirname(detector_path).rstrip(os.sep),
            lang_code,
            LANGUAGE_DATA_DIRECTORY
        )
    )
    return data_directory_path
