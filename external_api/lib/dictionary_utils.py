from external_api.exceptions import APIHandlerException
from datastore.datastore import DataStore
from chatbot_ner.config import ner_logger


def entity_supported_languages(entity_name):
    """
    """
    datastore_obj = DataStore()
    return datastore_obj.get_dictionary_supported_languages(entity_name)


def entity_update_languages(entity_name, new_language_list):
    """
    """
    old_language_list = entity_supported_languages(entity_name)
    languages_added = set(new_language_list) - set(old_language_list)
    languages_removed = set(old_language_list) - set(new_language_list)

    if languages_removed:
        # raise exception as it is not currently supported
        raise APIHandlerException('Removing languages is not currently supported.')

    if not languages_added:
        # no change in language list. raise error
        raise APIHandlerException('No new languages provided. Nothing changed.')

    # fetch all words
    word_list = get_entity_unique_values(entity_name=entity_name)
    if not word_list:
        raise APIHandlerException('This entity does not have any records. Please verify the entity name')

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
    datastore_obj.add_data_elastic_search(entity_name, records_to_create)

    return True


def get_entity_unique_values(
    entity_name, empty_variants_only=False, value_search_term=None, variant_search_term=None
):
    """
    Get a list of unique values belonging to this entity
    Args:
        entity_name (str): Name of the entity for which unique values are to be fetched
        empty_variants_only (bool): Flag to search for values with empty variants only
        value_search_term (str): Search term to filter values from this entity data
        variant_search_term (str): Search term to filter out variants from the entity data
    Returns:
        values_list (list): List of strings which are unique values in the entity
    """
    datastore_obj = DataStore()
    return datastore_obj.get_entity_unique_values(
        dictionary_name=entity_name,
        word_search_term=value_search_term,
        variant_search_term=variant_search_term,
        empty_variants_only=empty_variants_only
    )


def get_records_from_values(entity_name, values=None):
    """
    Fetch entity data based for the specified values in that entity
    Args:
        entity_name (str): Name of the entity for which records are to be fetched
        values (list): List of str values for which the data is to be fetched
    Returns:
        records (dict): dictionary with (key, value) as the value and language_code mapped
            variants and id
    """
    datastore_obj = DataStore()
    results = datastore_obj.get_dictionary_records(
        dictionary_name=entity_name,
        word_list=values
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
    """
    Delete entity data based for the specified values in that entity
    Args:
        entity_name (str): Name of the entity for which records are to be fetched
        values (list): List of str values for which the data is to be fetched
    Returns:
        records (dict): dictionary with (key, value) as the value and language_code mapped
            variants and id
    """
    datastore_obj = DataStore()
    return datastore_obj.delete_dictionary_records_by_word(
        dictionary_name=dictionary_name,
        word_list=word_list
    )


def search_entity_values(
        entity_name,
        value_search_term=None,
        variant_search_term=None,
        empty_variants_only=False,
        pagination_size=None,
        pagination_from=None
):
    """
    Searches for values within the specific entity. If pagination details not specified, all
    data will be returned.

    Args:
        entity_name (str): Name of the entity for which records are to be fetched
        value_search_term (str, optional): Search term to filter values from this entity data
        variant_search_term (str, optional): Search term to filter out variants from the entity data
        empty_variants_only (bool, optional): Flag to search for values with empty variants only
        pagination_size (int, optional): No. of records to fetch data when paginating
        pagination_from (int, optional): Offset to skip initial data (useful for pagination queries)
    Returns:
        (dict): total records (for pagination) and a list of individual records which match by the search filters
    """
    values = None
    total_records = None
    if value_search_term or variant_search_term or empty_variants_only:
        values = get_entity_unique_values(
            dictionary_name=entity_name,
            value_search_term=value_search_term,
            variant_search_term=variant_search_term,
            empty_variants_only=empty_variants_only,
        )
        total_records = len(values)
        if pagination_size > 0 and pagination_from >= 0:
            values = values[pagination_from:pagination_from + pagination_size]

    records_dict = get_records_from_values(entity_name, values)
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


def update_entity_records(entity_name, data):
    """
    Update dictionary data with the edited and deleted records

    Args:
        entity_name (str): Name of the entity for which records are to be fetched
        data (dict): Dictionary of edited, deleted data. If replace flag is true, then all
            existing data is deleted before adding the records

    Returns:
        None
    """
    # Delete some records first
    records_to_delete = data.get('deleted', [])
    records_to_create = data.get('edited', [])
    replace_data = data.get('replace')

    if replace_data:
        words_to_delete = get_entity_unique_values(entity_name)
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
    delete_records_by_word_list(entity_name, words_to_delete)

    datastore_obj = DataStore()
    datastore_obj.add_data_elastic_search(entity_name, word_variants_to_create)