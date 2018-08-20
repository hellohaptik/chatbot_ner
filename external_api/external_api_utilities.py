import requests
import json
from django.conf import settings


def structure_es_result(result):
    """
    This method is used to structure the query result in accordance to the external_api call format.
    Args:
        result (list): The result returned by the elastic search read query.

    Returns:
        structured_result (list): List dict each consisting of value and variants.
    """
    structured_result = []
    # The list around result.keys() is to make it compatible to python3
    key_list = list(result.keys())
    key_list.sort()
    for value in key_list:
        structured_result.append({'value': value, 'variants': result[value]})
    return structured_result


def structure_external_api_json(dict_list):
    """
    This method is used to structure the dictionary in the appropriate elastic search query format.
    Args:
        dict_list (list):  List of dicts consisting of value variants

    Returns:
        dictionary_value (dict): dict consisting of value variants as key value pairs
    """
    dictionary_value = {}

    for temp_dict in dict_list:
        dictionary_value[temp_dict['value']] = temp_dict['variants']

    return dictionary_value



