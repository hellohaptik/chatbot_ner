from six.moves import range

def edit_distance(string1, string2, insertion_cost=1, deletion_cost=1, substitution_cost=2, max_distance=None):
    """
    Calculate the weighted levenshtein distance between two strings

    Args:
        string1 (unicode): unicode string. If any encoded string type 'str' is passed, it will be decoded using utf-8
        string2 (unicode): unicode string. If any encoded string type 'str' is passed, it will be decoded using utf-8
        insertion_cost (int, optional): cost penalty for insertion operation, defaults to 1
        deletion_cost (int, optional): cost penalty for deletion operation, defaults to 1
        substitution_cost (int, optional): cost penalty for substitution operation, defaults to 2
        max_distance (int, optional): Stop computing edit distance if it grows larger than this argument.
                                      If None complete edit distance is returned. Defaults to None

    For Example:
        edit_distance('hello', 'helllo', max_distance=3)
        >> 1

        edit_distance('beautiful', 'beauty', max_distance=3)
        >> 3

    NOTE: Since, minimum edit distance is time consuming process, we have defined max_distance attribute.
    So, whenever distance exceeds the max_distance the function will break and return the max_distance else
    it will return levenshtein distance
    """
    if isinstance(string1, bytes):
        string1 = string1.decode('utf-8')

    if isinstance(string2, bytes):
        string2 = string2.decode('utf-8')

    if len(string1) > len(string2):
        string1, string2 = string2, string1
    distances = list(range(len(string1) + 1))
    for index2, char2 in enumerate(string2):
        new_distances = [index2 + 1]
        for index1, char1 in enumerate(string1):
            if char1 == char2:
                new_distances.append(distances[index1])
            else:
                new_distances.append(min((distances[index1] + substitution_cost,
                                         distances[index1 + 1] + insertion_cost,
                                         new_distances[-1] + deletion_cost)))
        distances = new_distances
        if max_distance and min(new_distances) > max_distance:
            return max_distance

    return distances[-1]
