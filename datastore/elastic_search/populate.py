from elasticsearch import helpers
from ner_v2.constant import DICTIONARY_DATA_VARIANTS
from ..constants import ELASTICSEARCH_BULK_HELPER_MESSAGE_SIZE, ELASTICSEARCH_SEARCH_SIZE
from ..utils import *
from ner_v2.language_utilities.constant import ENGLISH_LANG

log_prefix = 'datastore.elastic_search.populate'


def create_all_dictionary_data(connection, index_name, doc_type, logger, entity_data_directory_path=None,
                               csv_file_paths=None, **kwargs):
    """
    Indexes all entity data from csv files stored at entity_data_directory_path, one file at a time
    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        doc_type: The type of the documents being indexed
        logger: logging object to log at debug and exception level
        entity_data_directory_path: Optional, Path of the directory containing the entity data csv files.
                                    Default is None
        csv_file_paths: Optional, list of file paths to csv files. Default is None
        kwargs:
            Refer http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.bulk

    """
    logger.debug('%s: +++ Started: create_all_dictionary_data() +++' % log_prefix)
    if entity_data_directory_path:
        logger.debug('%s: \t== Fetching from variants/ ==' % log_prefix)
        csv_files = get_files_from_directory(entity_data_directory_path)
        for csv_file in csv_files:
            csv_file_path = os.path.join(entity_data_directory_path, csv_file)
            create_dictionary_data_from_file(connection=connection, index_name=index_name, doc_type=doc_type,
                                             csv_file_path=csv_file_path, update=False, logger=logger, **kwargs)
    if csv_file_paths:
        for csv_file_path in csv_file_paths:
            if csv_file_path and csv_file_path.endswith('.csv'):
                create_dictionary_data_from_file(connection=connection, index_name=index_name, doc_type=doc_type,
                                                 csv_file_path=csv_file_path, update=False, logger=logger, **kwargs)
    logger.debug('%s: +++ Finished: create_all_dictionary_data() +++' % log_prefix)


def recreate_all_dictionary_data(connection, index_name, doc_type, logger, entity_data_directory_path=None,
                                 csv_file_paths=None, **kwargs):
    """
    Re-indexes all entity data from csv files stored at entity_data_directory_path, one file at a time
    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        doc_type: The type of the documents being indexed
        logger: logging object to log at debug and exception level
        entity_data_directory_path: Optional, Path of the directory containing the entity data csv files.
                                    Default is None
        csv_file_paths: Optional, list of file paths to csv files. Default is None
        kwargs:
            Refer http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.bulk

    """
    logger.debug('%s: +++ Started: recreate_all_dictionary_data() +++' % log_prefix)
    if entity_data_directory_path:
        logger.debug('%s: \t== Fetching from variants/ ==' % log_prefix)
        csv_files = get_files_from_directory(entity_data_directory_path)
        for csv_file in csv_files:
            csv_file_path = os.path.join(entity_data_directory_path, csv_file)
            create_dictionary_data_from_file(connection=connection, index_name=index_name, doc_type=doc_type,
                                             csv_file_path=csv_file_path, update=True, logger=logger, **kwargs)
    if csv_file_paths:
        for csv_file_path in csv_file_paths:
            if csv_file_path and csv_file_path.endswith('.csv'):
                create_dictionary_data_from_file(connection=connection, index_name=index_name, doc_type=doc_type,
                                                 csv_file_path=csv_file_path, update=True, logger=logger, **kwargs)
    logger.debug('%s: +++ Finished: recreate_all_dictionary_data() +++' % log_prefix)


def get_variants_dictionary_value_from_key(csv_file_path, dictionary_key, logger, **kwargs):
    """
    Reads the csv file at csv_file_path and create a dictionary mapping entity value to a list of their variants.
    the entity values are first column of the csv file and their corresponding variants are stored in the second column
    delimited by '|'

    Args:
        csv_file_path: absolute file path of the csv file populate entity data from
        dictionary_key: name of the entity to be put the values under
        logger: logging object to log at debug and exception level
        kwargs:
            Refer http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.bulk

    Returns:
        Dictionary mapping entity value to a list of their variants.
    """
    dictionary_value = defaultdict(list)
    try:
        csv_reader = read_csv(csv_file_path)
        next(csv_reader)
        for data_row in csv_reader:
            try:
                data = map(str.strip, data_row[1].split('|'))
                # remove empty strings
                data = [variant for variant in data if variant]
                dictionary_value[data_row[0].strip().replace('.', ' ')].extend(data)

            except Exception as e:
                logger.exception('%s: \t\t== Exception in dict creation for keyword: %s -- %s -- %s =='
                                 % (log_prefix, dictionary_key, data_row, e))

    except Exception as e:
        logger.exception(
            '%s: \t\t\t=== Exception in __get_variants_dictionary_value_from_key() Dictionary Key: %s \n %s  ===' % (
                log_prefix,
                dictionary_key, e.message))

    return dictionary_value


def add_data_elastic_search(connection, index_name, doc_type, dictionary_key, dictionary_value, language_script, logger,
                            **kwargs):
    """
    Adds all entity values and their variants to the index. Entity value and its list of variants are keys and values
    of dictionary_value parameter generated from the csv file of this entity

    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        doc_type:  The type of the documents being indexed
        dictionary_key: file name of the csv file without the extension, also used as the entity name to index values
                        of this type. Example - 'city'
        dictionary_value: dictionary, mapping entity value to a list of its variants.
                            Example - 'New Delhi': ['Delhi', 'new deli', 'New Delhi']
        logger: logging object to log at debug and exception level
        language_script (str): Language code of the entity script
        kwargs:
            Refer http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.bulk

    Example of underlying index query
        {'_index': 'index_name',
         '_type': 'dictionary_data',
         'dict_type': 'variants',
         'entity_data': 'city',
         'value': 'Baripada Town'',
         'variants': ['Baripada', 'Baripada Town', '']
         '_op_type': 'index'
         }

    """
    str_query = []
    for value in dictionary_value:
        query_dict = {'_index': index_name,
                      'entity_data': dictionary_key,
                      'dict_type': DICTIONARY_DATA_VARIANTS,
                      'value': value,
                      'variants': dictionary_value[value],
                      "language_script": language_script,
                      '_type': doc_type,
                      '_op_type': 'index'
                      }
        str_query.append(query_dict)
        if len(str_query) > ELASTICSEARCH_BULK_HELPER_MESSAGE_SIZE:
            result = helpers.bulk(connection, str_query, stats_only=True, **kwargs)
            logger.debug('%s: \t++ %s status %s ++' % (log_prefix, dictionary_key, result))
            str_query = []
    if str_query:
        result = helpers.bulk(connection, str_query, stats_only=True, **kwargs)
        logger.debug('%s: \t++ %s status %s ++' % (log_prefix, dictionary_key, result))


def create_dictionary_data_from_file(connection, index_name, doc_type, csv_file_path, update, logger, **kwargs):
    """
    Indexes all entity data from the csv file at path csv_file_path
    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        doc_type:  The type of the documents being indexed
        csv_file_path: absolute file path of the csv file to populate entity data from
        update: boolean, True if this is a update type operation, False if create/index type operation
        logger: logging object to log at debug and exception level
        kwargs:
            Refer http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.bulk
    """

    base_file_name = os.path.basename(csv_file_path)
    dictionary_key = os.path.splitext(base_file_name)[0]

    if update:
        delete_entity_by_name(connection=connection, index_name=index_name, doc_type=doc_type,
                              entity_name=dictionary_key, logger=logger, **kwargs)
    dictionary_value = get_variants_dictionary_value_from_key(csv_file_path=csv_file_path,
                                                              dictionary_key=dictionary_key, logger=logger,
                                                              **kwargs)
    if dictionary_value:
        add_data_elastic_search(connection=connection, index_name=index_name, doc_type=doc_type,
                                dictionary_key=dictionary_key,
                                dictionary_value=remove_duplicate_data(dictionary_value), language_script=ENGLISH_LANG,
                                logger=logger, **kwargs)
    if os.path.exists(csv_file_path) and os.path.splitext(csv_file_path)[1] == '.csv':
        os.path.basename(csv_file_path)


def delete_entity_by_name(connection, index_name, doc_type, entity_name, logger, **kwargs):
    data = {
        'query': {
            'term': {
                'entity_data': {
                    'value': entity_name
                }
            }
        },
        "size": ELASTICSEARCH_SEARCH_SIZE
    }
    results = connection.search(index=index_name, doc_type=doc_type, scroll='2m', body=data)
    sid = results['_scroll_id']
    scroll_size = results['hits']['total']
    delete_bulk_queries = []
    str_query = []
    while scroll_size > 0:
        results = results['hits']['hits']
        for eid in results:
            delete_dict = {'_index': index_name,
                           '_type': doc_type,
                           '_id': eid["_id"],
                           '_op_type': 'delete',
                           }
            str_query.append(delete_dict)
            if len(str_query) > ELASTICSEARCH_BULK_HELPER_MESSAGE_SIZE:
                delete_bulk_queries.append(str_query)
                str_query = []
        results = connection.scroll(scroll_id=sid, scroll='2m')
        sid = results['_scroll_id']
        scroll_size = len(results['hits']['hits'])
    if str_query:
        delete_bulk_queries.append(str_query)
    for delete_query in delete_bulk_queries:
        result = helpers.bulk(connection, delete_query, stats_only=True, **kwargs)
        logger.debug('%s: \t++ %s Entity delete status %s ++' % (log_prefix, entity_name, result))


def entity_data_update(connection, index_name, doc_type, entity_data, entity_name, language_script,
                       logger, **kwargs):
    """
    This method is used to populate the elastic search via the external api call.
    Args:
        connection: Elasticsearch client object
        index_name (str): The name of the index
        doc_type (str): The type of the documents being indexed
        entity_data (list): List of dicts consisting of value and variants.
        entity_name (str): Name of the dictionary
        language_script (str): The code for the language script
        logger: logging object to log at debug and exception levellogging object to log at debug and exception level
        **kwargs: Refer http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.bulk
    """
    logger.debug('%s: +++ Started: external_api_entity_update() +++' % log_prefix)
    logger.debug('%s: +++ Started: delete_entity_by_name() +++' % log_prefix)
    delete_entity_by_name(connection=connection, index_name=index_name, doc_type=doc_type,
                          entity_name=entity_name, logger=logger, **kwargs)
    logger.debug('%s: +++ Completed: delete_entity_by_name() +++' % log_prefix)

    if entity_data:
        dictionary_value = {}
        for temp_dict in entity_data:
            dictionary_value[temp_dict['value']] = temp_dict['variants']

        logger.debug('%s: +++ Started: add_data_elastic_search() +++' % log_prefix)
        add_data_elastic_search(connection=connection, index_name=index_name, doc_type=doc_type,
                                dictionary_key=entity_name,
                                dictionary_value=dictionary_value, language_script=language_script, logger=logger, **kwargs)
        logger.debug('%s: +++ Completed: add_data_elastic_search() +++' % log_prefix)


def update_entity_crf_data_populate(connection, index_name, doc_type, entity_list, entity_name, sentence_list, language_script,
                                    logger, **kwargs):
    """
    This method is used to populate the elastic search traininf data.
    Args:
        connection: Elasticsearch client object
        index_name (str): The name of the index
        doc_type (str): The type of the documents being indexed
        entity_name (str): Name of the entity for which the training data has to be populated
        entity_list (list): List consisting of the entities corresponding to the sentence_list
        sentence_list (list): List of sentences for training
        language_script (str): The code for the language script
        logger: logging object to log at debug and exception levellogging object to log at debug and exception level
        **kwargs: Refer http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.bulk
    """
    logger.debug('%s: +++ Started: external_api_training_data_entity_update() +++' % log_prefix)
    logger.debug('%s: +++ Started: delete_entity_by_name() +++' % log_prefix)
    delete_entity_by_name(connection=connection, index_name=index_name, doc_type=doc_type,
                          entity_name=entity_name, logger=logger, **kwargs)
    logger.debug('%s: +++ Completed: delete_entity_by_name() +++' % log_prefix)

    logger.debug('%s: +++ Started: add_training_data_elastic_search() +++' % log_prefix)
    add_training_data_elastic_search(connection=connection, index_name=index_name, doc_type=doc_type,
                                     entity_name=entity_name,
                                     entity_list=entity_list,
                                     sentence_list=sentence_list,
                                     language_script=language_script, logger=logger, **kwargs)
    logger.debug('%s: +++ Completed: add_training_data_elastic_search() +++' % log_prefix)


def add_training_data_elastic_search(connection, index_name, doc_type, entity_name, entity_list, sentence_list, language_script, logger,
                                     **kwargs):
    """
    Adds all sentences and the corresponding entities to the specified index.
    If the same named entity is found a delete followed by an update is triggered
    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        doc_type:  The type of the documents being indexed
        entity_name (str): Name of the entity for which the training data has to be populated
        entity_list (list): List consisting of the entities corresponding to the sentence_list
        sentence_list (list): List of sentences for training
        logger: logging object to log at debug and exception level
        language_script (str): Language code of the entity script
        kwargs:
            Refer http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.bulk
    Example of underlying index query
            {'_index': 'training_index',
            'entity_data': 'name',
            'sentence': ['My name is Ajay and this is my friend Hardik'],
            'entities': ['Ajay', 'Hardik'],
            'language_script': 'en',
            '_type': 'training_index',
            '_op_type': 'index'
              }
    """
    str_query = []
    for sentence, entities in zip(sentence_list, entity_list):
        query_dict = {'_index': index_name,
                      'entity_data': entity_name,
                      'sentence': sentence,
                      'entities': entities,
                      'language_script': language_script,
                      '_type': doc_type,
                      '_op_type': 'index'
                      }
        str_query.append(query_dict)
        if len(str_query) > ELASTICSEARCH_BULK_HELPER_MESSAGE_SIZE:
            result = helpers.bulk(connection, str_query, stats_only=True, **kwargs)
            logger.debug('%s: \t++ %s status %s ++' % (log_prefix, entity_name, result))
            str_query = []
    if str_query:
        result = helpers.bulk(connection, str_query, stats_only=True, **kwargs)
        logger.debug('%s: \t++ %s status %s ++' % (log_prefix, entity_name, result))
