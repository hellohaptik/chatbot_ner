from __future__ import absolute_import
import csv
import os
from collections import defaultdict


def read_csv(file_path):
    """
    Creates the csv reader object for a file

    Args:
        file_path: path of the csv file
    Returns:
         csv reader object
    """
    file_object = open(file_path, 'rt')
    reader = csv.reader(file_object)
    return reader


def remove_duplicate_data(dictionary_value):
    """
    Removes duplicates from lists in a dictionary mapping keys to lists

    Args:
        dictionary_value: A dictionary mapping keys to iterable objects

    Returns:
        A dictionary mapping orignal keys to list conatining unique elements of list of elements they mapped to in
        remove_duplicate_data

    Example:
        remove_duplicate_data({"A": [1, 2, 3, 1, 1], "B": [100, 200, 300, 200]})

        Output:
            {"A": [2, 3, 1], "B": [100, 200, 300]}

    """
    dictionary_unique = defaultdict(list)
    for key in dictionary_value:
        dictionary_unique[key] = list(set(dictionary_value[key]))
    return dictionary_unique


def get_files_from_directory(directory_path):
    """
    Get list of all csv files in the directory path

    Args:
        directory_path: path of the directory to get csv filepaths from

    Returns:
        A list of path of all csv files in the directory_path
    """
    if not directory_path or not os.path.exists(directory_path):
        return []
    return [f for f in os.listdir(directory_path) if
            os.path.isfile(os.path.join(directory_path, f)) and f.endswith('.csv')]
