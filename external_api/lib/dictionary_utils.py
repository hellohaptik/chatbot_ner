from __future__ import absolute_import

"""
Note:
'word' and 'value' mean the same in this context and hasn't been cleaned because of dependency
on other haptik repository.
TODO: Move to consistent terminology and use 'value' everywhere
"""

from external_api.exceptions import APIHandlerException
from datastore.datastore import DataStore


def entity_supported_languages(entity_name):
    """
    Fetch list of supported languages for the specific entity

    Args:
        entity_name (str): Name of the entity for which unique values are to be fetched
    Returns:
        list: List of language_codes
    """
    datastore_obj = DataStore()
    return datastore_obj.get_entity_supported_languages(entity_name=entity_name)


def entity_update_languages(entity_name, new_language_list):
    """
    Updates the language support list of the entity by creating dummy records. Currently does not
    support removal of a language.
    It creates empty variant records for all the unique values present in this entity.

    Args:
        entity_name (str): Name of the entity for which unique values are to be fetched
        new_language_list (list): List of language codes for the new entity
    Returns:
        bool: Success flag if the update
    Raises:
        APIHandlerException (Exception): for any validation errors
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
    values = get_entity_unique_values(entity_name=entity_name)
    if not values:
        raise APIHandlerException('This entity does not have any records. Please verify the entity name')

    records_to_create = []
    for language_script in languages_added:
        # create records for all words
        for value in values:
            if value and language_script:
                records_to_create.append({
                    'value': value,
                    'language_script': language_script,
                    'variants': []
                })

    datastore_obj = DataStore()
    datastore_obj.add_entity_data(entity_name, records_to_create)

    return True


def get_entity_unique_values(
    entity_name, empty_variants_only=False, value_search_term=None, variant_search_term=None
):
    """
    Get a list of unique values belonging to this entity
    Args:
        entity_name (str): Name of the entity for which unique values are to be fetched
        empty_variants_only (bool, optional): Flag to search for values with empty variants only
        value_search_term (str, optional): Search term to filter values from this entity data
        variant_search_term (str, optional): Search term to filter out variants from the entity data
    Returns:
        list: List of strings which are unique values in the entity
    """
    datastore_obj = DataStore()
    return datastore_obj.get_entity_unique_values(
        entity_name=entity_name,
        value_search_term=value_search_term,
        variant_search_term=variant_search_term,
        empty_variants_only=empty_variants_only
    )


def get_records_from_values(entity_name, values=None):
    """
    Fetch entity data based for the specified values in that entity
    Args:
        entity_name (str): Name of the entity for which records are to be fetched
        values (list, optional): List of str values for which the data is to be fetched
    Returns:
        dict: dictionary mapping the entity_value to a dictionary
            Sample: {
                'entity_value': {
                    'en': {
                        '_id': 'Random ES ID',
                        'value': ['Variant 1', 'Variant 2']
                    },
                    'hi': {
                        '_id': 'Random ES ID',
                        'value': ['Variant 1', 'Variant 2']
                    }
                }
    """
    datastore_obj = DataStore()
    results = datastore_obj.get_entity_data(
        entity_name=entity_name,
        values=values
    )

    merged_records = {}
    for result in results:
        merged_records.setdefault(result['_source']['value'], {})
        merged_records[result['_source']['value']][result['_source']['language_script']] = {
            '_id': result['_id'],
            'value': result['_source']['variants'],
        }
    return merged_records


def delete_records_by_values(entity_name, values):
    """
    Delete entity data based for the specified values in that entity
    Args:
        entity_name (str): Name of the entity for which records are to be fetched
        values (list): List of str values for which the data is to be fetched
    Returns:
        None
    """
    datastore_obj = DataStore()
    datastore_obj.delete_entity_data_by_values(
        entity_name=entity_name,
        values=values
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
        value_search_term (str, optional): Search term to filter values from this entity data.
            If not provided, results are not filtered by values
        variant_search_term (str, optional): Search term to filter out variants from the entity data
            If not provided, results are not filtered by variants
        empty_variants_only (bool, optional): Flag to search for values with empty variants only
            If not provided, all variants are included
        pagination_size (int, optional): No. of records to fetch data when paginating
            If it is None, the results will not be paginated
        pagination_from (int, optional): Offset to skip initial data (useful for pagination queries)
            If it is None, the results will not be paginated
    Returns:
        dict: total records (for pagination) and a list of individual records which match by the search filters
    """
    values = None
    total_records = None
    if value_search_term or variant_search_term or empty_variants_only or pagination_size or pagination_from:
        values = get_entity_unique_values(
            entity_name=entity_name,
            value_search_term=value_search_term,
            variant_search_term=variant_search_term,
            empty_variants_only=empty_variants_only,
        )
        total_records = len(values)
        if pagination_size > 0 and pagination_from >= 0:
            values = values[pagination_from:pagination_from + pagination_size]

    records_dict = get_records_from_values(entity_name, values)
    records_list = []
    for value, variant_data in records_dict.items():
        records_list.append({
            "word": value,
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
        values_to_delete = get_entity_unique_values(entity_name)
    else:
        values_to_delete = [record['word'] for record in records_to_delete]
        values_to_delete.extend([record['word'] for record in records_to_create])

    value_variants_to_create = []
    for record in records_to_create:
        for language_script, variants in record.get('variants', {}).items():
            if record['word'] and language_script:
                value_variants_to_create.append({
                    'value': record['word'],
                    'language_script': language_script,
                    'variants': variants.get('value', [])
                })

    # delete words
    delete_records_by_values(entity_name=entity_name, values=values_to_delete)

    datastore_obj = DataStore()
    datastore_obj.add_entity_data(entity_name, value_variants_to_create)
