from __future__ import absolute_import
from ner_v2.constant import LANGUAGE_DATA_DIRECTORY
import os


def get_lang_data_path(detector_path, lang_code):
    data_directory_path = os.path.abspath(
        os.path.join(
            os.path.dirname(detector_path).rstrip(os.sep),
            lang_code,
            LANGUAGE_DATA_DIRECTORY
        )
    )
    return data_directory_path
