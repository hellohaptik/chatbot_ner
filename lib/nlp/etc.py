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


def remove_one_list_to_another(list1, list2):
    """Removes one list to another

    This function will remove the words from list1 which are present in the other list
    Args:
        list1: list of words
        list2: list of words

        It will return the list of words which are present in list1 but not in list2
    Returns:
        The list of words
        For example
        output = remove_one_list_to_another(list1=['hi', 'hello', 'bye'],['hi', 'bye'])
        print output
        >> ['hello']
    """

    token_list = []
    for token in list1:
        if not token in list2:
            token_list.append(token)
    return token_list

