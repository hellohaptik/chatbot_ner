from __future__ import absolute_import
import csv


def store_data_in_list(file_path, stemmer=None, lower_case=True):
    """Stores data in the list

    This function will read the file and store it in a list
    Args:
        file_path: file that needs to be converted to the list
        stemmer: object of stemmer
        lower_case: True if string needs to be converted to lower case
    Returns:
        The list of words

    """
    list_of_words = []
    input_file = open(file_path, "rt")  # file containing words
    csv_reader = csv.reader(input_file)
    # populate list of words
    for word in csv_reader:
        token = word[0].lower() if lower_case else word[0]
        if not stemmer:
            list_of_words.append(str(token))
        else:
            list_of_words.append(str(stemmer.stem_word(token)))
    input_file.close()
    return list_of_words


def filter_list(list_to_filter, remove_elements):
    """
    Args:
        list_to_filter (list): list to filter
        remove_elements (list): list elements to remove from first list

    Returns:
        list of str: The list of elements in first list but not in second

        For example, output = filter_list(['hi', 'hello', 'bye'],['hi', 'bye'])
        print(output)
        >> ['hello']
    """
    return [item for item in list_to_filter if item not in remove_elements]


