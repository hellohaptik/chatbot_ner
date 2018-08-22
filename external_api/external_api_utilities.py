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
