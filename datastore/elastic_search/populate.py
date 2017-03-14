import os
from elasticsearch import helpers
from v1.constant import DICTIONARY_DATA_VARIANTS
from ..utils import *
from ..constants import ELASTICSEARCH_BULK_HELPER_MESSAGE_SIZE

log_prefix = 'datastore.elastic_search.populate'


def create_all_dictionary_data(connection, index_name, doc_type, entity_data_directory_path, logger, **kwargs):
    """
    This setter function create entire model by going through all the files
    :return:
    """
    logger.debug('%s: +++ Started: create_all_dictionary_data() +++' % log_prefix)
    if entity_data_directory_path:
        logger.debug('%s: \t== Fetching from variants/ ==' % log_prefix)
        create_dictionary_data_from_variants(connection=connection, index_name=index_name, doc_type=doc_type,
                                             variants_directory_path=entity_data_directory_path, update=False,
                                             logger=logger, **kwargs)
        logger.debug('%s: +++ Finished: create_all_dictionary_data() +++' % log_prefix)


def create_dictionary_data_from_variants(connection, index_name, doc_type, variants_directory_path, update, logger,
                                         **kwargs):
    """
    Creates the dictionary data from variants/
    :return:
    """
    dict_type = DICTIONARY_DATA_VARIANTS
    csv_files = get_files_from_directory(variants_directory_path)
    for dictionary_key_file in csv_files:
        dictionary_key = os.path.splitext(dictionary_key_file)[0]
        dictionary_value = get_variants_dictionary_value_from_key(variants_directory_path=variants_directory_path,
                                                                  dictionary_key=dictionary_key, logger=logger,
                                                                  **kwargs)
        if dictionary_value:
            add_data_elastic_search(connection=connection, index_name=index_name, doc_type=doc_type,
                                    dictionary_key=dictionary_key, dict_type=dict_type,
                                    dictionary_value=remove_duplicate_data(dictionary_value),
                                    update=update, logger=logger, **kwargs)


def get_variants_dictionary_value_from_key(variants_directory_path, dictionary_key, logger, **kwargs):
    """
    This function will get the dictionary values given dictionary key from variants
    :param logger:
    :param variants_directory_path:
    :param dictionary_key: cuisine,establishment_type etc
    :return:
    """
    dictionary_value = defaultdict(list)
    try:
        csv_reader = read_csv(os.path.join(variants_directory_path, dictionary_key + '.csv'))
        next(csv_reader)
        for data_row in csv_reader:
            try:
                data = map(str.strip, data_row[1].split('|'))
                dictionary_value[data_row[0].strip().replace('.', ' ')].extend(data)

            except Exception, e:
                logger.exception('%s: \t\t== Exception in dict creation for keyword: %s -- %s -- %s =='
                                 % (log_prefix, dictionary_key, data_row, e))

    except Exception, e:
        logger.exception(
            '%s: \t\t\t=== Exception in __get_variants_dictionary_value_from_key() Dictionary Key: %s \n %s  ===' % (
                log_prefix,
                dictionary_key, e.message))

    return dictionary_value


def add_data_elastic_search(connection, index_name, doc_type, dictionary_key, dict_type, dictionary_value, logger,
                            update=False,
                            **kwargs):
    """
    Generates a query for bulk operation and adds it to elastic search
    :param logger:
    :param index_name:
    :param connection:
    :param dictionary_key:
    :param dict_type:
    :param dictionary_value:
    :param update:
    :return:
    """
    str_query = []
    for value in dictionary_value:
        query_dict = {'_index': index_name,
                      'entity_data': dictionary_key,
                      'dict_type': dict_type,
                      'value': value,
                      'variants': dictionary_value[value],
                      '_type': doc_type
                      }
        if not update:
            query_dict['_op_type'] = 'create'
        str_query.append(query_dict)
        if len(str_query) > ELASTICSEARCH_BULK_HELPER_MESSAGE_SIZE:
            result = helpers.bulk(connection, str_query, stats_only=True, **kwargs)
            logger.debug('%s: \t++ %s status %s ++' % (log_prefix, dictionary_key, result))
            str_query = []
    if str_query:
        result = helpers.bulk(connection, str_query, stats_only=True, **kwargs)
        logger.debug('%s: \t++ %s status %s ++' % (log_prefix, dictionary_key, result))
