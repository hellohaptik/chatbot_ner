from __future__ import absolute_import
import os


def get_entity_name(file_path):
    base = os.path.basename(file_path)
    return os.path.splitext(base)[0]
