from external_api.exceptions import APIHandlerException
from datastore.datastore import DataStore


def dictionary_supported_languages(dictionary_name):
    """
    """
    datastore_obj = DataStore()
    return datastore_obj.get_dictionary_supported_languages(dictionary_name)


def dictionary_update_languages(dictionary_name, new_language_list):
    """
    """
    old_language_list = dictionary_supported_languages(dictionary_name)
    languages_added = set(new_language_list) - set(old_language_list)
    languages_removed = set(old_language_list) - set(new_language_list)

    if languages_removed:
        # raise exception as it is not currently supported
        raise APIHandlerException('Removing languages is not currently supported.')

    if not languages_added:
        # no change in language list. raise error
        raise APIHandlerException('No new languages provided. Nothing changed.')

    # fetch all words
    word_list = get_dictionary_words(dictionary_name)
    if not word_list:
        raise APIHandlerException('This dictionary does not have any records. Please verify the dictionary name')

    records_to_create = []
    for language_code in languages_added:
        # create records for all words
        for word in word_list:
            records_to_create.append({
                "word": word,
                "language_code": language_code
            })

    # Bulk create words from above JSON
    create_records_in_dictionary(dictionary_name, records_to_create)

    return True


def get_dictionary_unique_words(dictionary_name, word_search_term=None, variant_search_term=None):
    """
    """
    datastore_obj = DataStore()
    return datastore_obj.get_dictionary_unique_words(
        dictionary_name=dictionary_name,
        word_search_term=word_search_term,
        variant_search_term=variant_search_term
    )


def get_records_from_word_list(dictionary_name, filtered_word_list):
    datastore_obj = DataStore()
    return datastore_obj.get_dictionary_records(
        dictionary_name=dictionary_name,
        word_list=filtered_word_list
    )


def search_dictionary_records(
        dictionary_name, word_search_term=None, variant_search_term=None,
        pagination_size=None, pagination_from=None):
    """
    """
    word_list = get_dictionary_unique_words(
        dictionary_name=dictionary_name, word_search_term=word_search_term, variant_search_term=variant_search_term)

    if pagination_size > 0 and pagination_from >= 0:
        filtered_word_list = word_list[pagination_from:pagination_from + pagination_size]
    else:
        filtered_word_list = word_list

    records = get_records_from_word_list(dictionary_name, filtered_word_list)
    return records


def update_dictionary_records(dictionary_name, data):
    """
    """
    raise APIHandlerException("Not yet implemented")


def create_records_in_dictionary(dictionary_name, records):
    """
    """
    # bulk create
    pass


def delete_records_from_dictionary(dictionary_name, records):
    """
    """
    # bulk delete records
    pass
