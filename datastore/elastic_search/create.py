from .utils import filter_kwargs

log_prefix = 'datastore.elastic_search.create'


def delete_index(connection, index_name, logger, **kwargs):
    """
    Deletes the index named index_name

    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        logger: logging object to log at debug and exception level
        kwargs:
            body: The configuration for the index (settings and mappings)
            master_timeout: Specify timeout for connection to master
            timeout: Explicit operation timeout
            update_all_types: Whether to update the mapping for all fields with the same name across all types or not
            wait_for_active_shards: Set the number of active shards to wait for before the operation returns.

        Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.client.IndicesClient.delete
    """
    try:
        connection.indices.delete(index=index_name, **kwargs)
        logger.debug('%s: Delete Index: Operation successfully completed' % log_prefix)
    except Exception as e:
        logger.exception('%s: Exception in deleting index %s ' % (log_prefix, e))


def _create_index(connection, index_name, doc_type, logger, mapping_body, ignore_if_exists=False, **kwargs):
    """
    Creates an Elasticsearch index needed for similarity based searching
    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        doc_type:  The type of the documents that will be indexed
        logger: logging object to log at debug and exception level
        mapping_body: dict, mappings to put on the index
        kwargs:
            master_timeout: Specify timeout for connection to master
            timeout: Explicit operation timeout
            update_all_types: Whether to update the mapping for all fields with the same name across all types or not
            wait_for_active_shards: Set the number of active shards to wait for before the operation returns.
            doc_type: The name of the document type
            allow_no_indices: Whether to ignore if a wildcard indices expression resolves into no concrete indices.
                              (This includes _all string or when no indices have been specified)
            expand_wildcards: Whether to expand wildcard expression to concrete indices that are open, closed or both.,
                              default 'open', valid choices are: 'open', 'closed', 'none', 'all'
            ignore_unavailable: Whether specified concrete indices should be ignored when unavailable
                                (missing or closed)
        Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.client.IndicesClient.create
        Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.client.IndicesClient.put_mapping
    """
    if exists(connection=connection, index_name=index_name):
        if ignore_if_exists:
            return
        else:
            raise Exception('Failed to create index {}. it already exists. Please check and delete it using '
                            'Datastore().delete()')
    try:
        body = {
            'index': {
                'analysis': {
                    'analyzer': {
                        'my_analyzer': {
                            'tokenizer': 'whitespace',
                            'filter': ['standard', 'lowercase', 'my_stemmer']
                        }
                    },
                    'filter': {
                        'my_stemmer': {
                            'type': 'stemmer',
                            'name': 'english'
                        }
                    }
                }
            }
        }

        # At this point in time, elasticsearch-py doesn't accept arbitrary kwargs, so we have to filter kwargs per
        # method. Refer https://github.com/elastic/elasticsearch-py/blob/master/elasticsearch/client/indices.py
        create_kwargs = filter_kwargs(kwargs=kwargs,
                                      keep_kwargs_keys=['master_timeout', 'timeout', 'update_all_types',
                                                        'wait_for_active_shards'])
        connection.indices.create(index=index_name, body=body, **create_kwargs)

        put_mapping_kwargs = filter_kwargs(kwargs=kwargs, keep_kwargs_keys=['allow_no_indices', 'expand_wildcards',
                                                                            'ignore_unavailable',
                                                                            'master_timeout', 'timeout',
                                                                            'update_all_types'])
        if doc_type:
            connection.indices.put_mapping(body=mapping_body, index=index_name, doc_type=doc_type,
                                           **put_mapping_kwargs)
        else:
            logger.debug('%s: doc_type not in arguments, skipping put_mapping on index ...' % log_prefix)
        logger.debug('%s: Create Index: Operation successfully completed' % log_prefix)
    except Exception as e:
        logger.exception('%s:Exception: while creating index, Rolling back \n %s' % (log_prefix, e))
        delete_index(connection=connection, index_name=index_name, logger=logger)


def exists(connection, index_name):
    """
    Checks if index_name exists

    Args:
        connection: Elasticsearch client object
        index_name: The name of the index

    Returns:
        boolean, True if index exists , False otherwise
    """
    return connection.indices.exists(index_name)


def create_entity_index(connection, index_name, doc_type, logger, **kwargs):
    """
    Creates an mapping specific to entity storage in elasticsearch and makes a call to create_index
    to create the index with the given mapping body
    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        doc_type:  The type of the documents that will be indexed
        logger: logging object to log at debug and exception level
        **kwargs:
            master_timeout: Specify timeout for connection to master
            timeout: Explicit operation timeout
            update_all_types: Whether to update the mapping for all fields with the same name across all types or not
            wait_for_active_shards: Set the number of active shards to wait for before the operation returns.
            doc_type: The name of the document type
            allow_no_indices: Whether to ignore if a wildcard indices expression resolves into no concrete indices.
                              (This includes _all string or when no indices have been specified)
            expand_wildcards: Whether to expand wildcard expression to concrete indices that are open, closed or both.,
                              default 'open', valid choices are: 'open', 'closed', 'none', 'all'
            ignore_unavailable: Whether specified concrete indices should be ignored when unavailable
                                (missing or closed)

        Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.client.IndicesClient.create
        Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.client.IndicesClient.put_mapping
    """
    mapping_body = {
        doc_type: {
            'properties': {
                'variants': {
                    'type': 'text',
                    'analyzer': 'my_analyzer',
                    'norms': {'enabled': False},  # Needed if we want to give longer variants higher scores
                }
            }
        }
    }

    _create_index(connection, index_name, doc_type, logger, mapping_body, **kwargs)


def create_crf_index(connection, index_name, doc_type, logger, **kwargs):
    """
    This method is used to create an index with mapping suited for story training_data
    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        doc_type:  The type of the documents that will be indexed
        logger: logging object to log at debug and exception level
        **kwargs:
            master_timeout: Specify timeout for connection to master
            timeout: Explicit operation timeout
            update_all_types: Whether to update the mapping for all fields with the same name across all types or not
            wait_for_active_shards: Set the number of active shards to wait for before the operation returns.
            doc_type: The name of the document type
            allow_no_indices: Whether to ignore if a wildcard indices expression resolves into no concrete indices.
                              (This includes _all string or when no indices have been specified)
            expand_wildcards: Whether to expand wildcard expression to concrete indices that are open, closed or both.,
                              default 'open', valid choices are: 'open', 'closed', 'none', 'all'
            ignore_unavailable: Whether specified concrete indices should be ignored when unavailable
                                (missing or closed)

        Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.client.IndicesClient.create
        Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.client.IndicesClient.put_mapping
    """
    mapping_body = {
        doc_type: {
            'properties': {
                "entity_data": {
                    "type": "text"
                },
                "sentence": {
                    "enabled": "false"
                },
                "entities": {
                    "enabled": "false"
                },
                "language_script": {
                    "type": "text"
                }
            }
        }
    }

    _create_index(connection, index_name, doc_type, logger, mapping_body, **kwargs)


def create_alias(connection, index_list, alias_name, logger, **kwargs):
    """
    This method is used to create alias for list of indices
    Args:
        connection:
        index_list (list): List of indices the alias has to point to
        alias_name (str): Name of the alias
        logger: logging object to log at debug and exception level

        **kwargs:
            https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-aliases.html
    """
    logger.debug('Alias creation %s started %s' % alias_name)
    connection.indices.put_alias(index=index_list, name=alias_name, **kwargs)
    logger.debug('Alias %s now points to indices %s' % (alias_name, str(index_list)))
