from external_api.exceptions import APIHandlerException
from datastore.datastore import DataStore
from chatbot_ner.config import ner_logger


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
    word_list = get_dictionary_unique_words(dictionary_name)
    if not word_list:
        raise APIHandlerException('This dictionary does not have any records. Please verify the dictionary name')

    records_to_create = []
    for language_script in languages_added:
        # create records for all words
        for word in word_list:
            records_to_create.append({
                'word': word,
                'language_script': language_script,
                'variants': []
            })

    datastore_obj = DataStore()
    datastore_obj.add_data_elastic_search(dictionary_name, records_to_create)

    return True


def get_dictionary_unique_words(
    dictionary_name, empty_variants_only=False, word_search_term=None, variant_search_term=None
):
    """
    """
    datastore_obj = DataStore()
    return datastore_obj.get_dictionary_unique_words(
        dictionary_name=dictionary_name,
        word_search_term=word_search_term,
        variant_search_term=variant_search_term,
        empty_variants_only=empty_variants_only
    )


def get_records_from_word_list(dictionary_name, filtered_word_list=None):
    datastore_obj = DataStore()
    results = datastore_obj.get_dictionary_records(
        dictionary_name=dictionary_name,
        word_list=filtered_word_list
    )

    merged_records = {}
    for result in results:
        merged_records.setdefault(result['_source']['value'], {})
        merged_records[result['_source']['value']][result['_source']['language_script']] = {
            '_id': result['_id'],
            'value': result['_source']['variants'],
        }
    return merged_records


def delete_records_by_word_list(dictionary_name, word_list):
    datastore_obj = DataStore()
    return datastore_obj.delete_dictionary_records_by_word(
        dictionary_name=dictionary_name,
        word_list=word_list
    )


def search_dictionary_records(
        dictionary_name, word_search_term=None, variant_search_term=None, empty_variants_only=False,
        pagination_size=None, pagination_from=None):
    """
    """
    word_list = None
    total_records = None
    if word_search_term or variant_search_term or empty_variants_only:
        word_list = get_dictionary_unique_words(
            dictionary_name=dictionary_name,
            word_search_term=word_search_term,
            variant_search_term=variant_search_term,
            empty_variants_only=empty_variants_only,
        )
        total_records = len(word_list)
        if pagination_size > 0 and pagination_from >= 0:
            word_list = word_list[pagination_from:pagination_from + pagination_size]

    records_dict = get_records_from_word_list(dictionary_name, word_list)
    records_list = []
    for word, variant_data in records_dict.items():
        records_list.append({
            "word": word,
            "variants": variant_data,
        })

    if total_records is None:
        total_records = len(records_list)

    return {
        'records': records_list,
        'total': total_records
    }


def update_dictionary_records(dictionary_name, data):
    """
    """
    # Delete some records first
    records_to_delete = data.get('deleted', [])
    records_to_create = data.get('edited', [])
    replace_data = data.get('replace')

    if replace_data:
        words_to_delete = get_dictionary_unique_words(dictionary_name)
    else:
        words_to_delete = [record['word'] for record in records_to_delete]
        words_to_delete.extend([record['word'] for record in records_to_create])

    word_variants_to_create = []
    for record in records_to_create:
        for language_script, variants in record.get('variants', {}).items():
            word_variants_to_create.append({
                'word': record['word'],
                'language_script': language_script,
                'variants': variants.get('value', [])
            })

    ner_logger.debug(words_to_delete)
    ner_logger.debug(word_variants_to_create)

    # delete words
    delete_records_by_word_list(dictionary_name, words_to_delete)

    datastore_obj = DataStore()
    datastore_obj.add_data_elastic_search(dictionary_name, word_variants_to_create)
