import os
import time
import datetime


def get_current_timestamp():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
    return st


def create_directory(directory_name):
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)
        return True
    return False


def write_data(file_path, crf_data):
    file_object = open(file_path, 'w')
    file_object.write(crf_data)
    file_object.close()
