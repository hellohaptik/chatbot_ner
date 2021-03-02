import logging
from typing import List, Dict, Any

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

from .utils import filter_kwargs

log_prefix = 'datastore.elastic_search.create'


def exists(connection, index_name):
    # type: (Elasticsearch, str) -> bool
    """
    Checks if index_name exists

    Args:
        connection: Elasticsearch client object
        index_name: The name of the index

    Returns:
        boolean, True if index exists , False otherwise
    """
    return connection.indices.exists(index_name)


def delete_index(connection, index_name, logger, err_if_does_not_exist=True, **kwargs):
    # type: (Elasticsearch, str, logging.Logger, bool, **Any) -> None
    """
    Deletes the index named index_name

    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        logger: logging object to log at debug and exception level
        err_if_does_not_exist: if to raise error if index does not exist already, defaults to True
        kwargs:
            body: The configuration for the index (settings and mappings)
            master_timeout: Specify timeout for connection to master
            timeout: Explicit operation timeout
            update_all_types: Whether to update the mapping for all fields with the same name across all types or not
            wait_for_active_shards: Set the number of active shards to wait for before the operation returns.

        Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.client.IndicesClient.delete
    """
    if not exists(connection, index_name):
        if err_if_does_not_exist:
            raise Exception('Failed to delete index {}. It does not exist!'.format(index_name))
        else:
            return

    try:
        delete_alias(connection=connection, index_list=[index_name], alias_name='_all', logger=logger)
    except NotFoundError:
        logger.warning('No aliases found on on index %s', index_name)

    connection.indices.delete(index=index_name, **kwargs)
    logger.debug('%s: Delete Index %s: Operation successfully completed', log_prefix, index_name)


def _create_index(connection, index_name, doc_type, logger, mapping_body, err_if_exists=True, **kwargs):
    # type: (Elasticsearch, str, str, logging.Logger, Dict[str, Any], bool, **Any) -> None
    """
    Creates an Elasticsearch index needed for similarity based searching
    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        doc_type:  The type of the documents that will be indexed
        logger: logging object to log at debug and exception level
        mapping_body: dict, mappings to put on the index
        err_if_exists: if to raise error if the index already exists, defaults to True
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
        if err_if_exists:
            raise Exception('Failed to create index {}. it already exists. Please check and delete it using '
                            'Datastore().delete()'.format(index_name))
        else:
            return
    try:
        body = {
            'index': {
                'analysis': {
                    'analyzer': {
                        'my_analyzer': {
                            'tokenizer': 'standard',
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
        logger.debug('%s: Create Index %s: Operation successfully completed', log_prefix, index_name)
    except Exception as e:
        logger.exception('%s: Exception while creating index %s, Rolling back \n %s', log_prefix, index_name, e)
        delete_index(connection=connection, index_name=index_name, logger=logger)
        raise e


def create_entity_index(connection, index_name, doc_type, logger, **kwargs):
    # type: (Elasticsearch, str, str, logging.Logger, **Any) -> None
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
                'language_script': {
                    'type': 'text',
                    'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}},
                },
                'value': {
                    'type': 'text',
                    'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}},
                },
                'variants': {
                    'type': 'text',
                    'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}},
                    'analyzer': 'my_analyzer',
                    'norms': {'enabled': False},  # Needed if we want to give longer variants higher scores
                },
                # other removed/unused fields, kept only for backward compatibility
                'dict_type': {
                    'type': 'text',
                    'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}},
                },
                'entity_data': {
                    'type': 'text',
                    'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}},
                },
                'source_language': {
                    'type': 'text',
                    'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}},
                }
            }
        }
    }

    _create_index(connection, index_name, doc_type, logger, mapping_body, **kwargs)


def create_crf_index(connection, index_name, doc_type, logger, **kwargs):
    # type: (Elasticsearch, str, str, logging.Logger, **Any) -> None
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
                'entity_data': {
                    'type': 'text'
                },
                'sentence': {
                    'enabled': False
                },
                'entities': {
                    'enabled': False
                },
                'language_script': {
                    'type': 'text'
                }
            }
        }
    }

    _create_index(connection, index_name, doc_type, logger, mapping_body, **kwargs)


def create_alias(connection, index_list, alias_name, logger, **kwargs):
    # type: (Elasticsearch, List[str], str, logging.Logger, **Any) -> None
    """
    This method is used to create alias for list of indices
    Args:
        connection: Elasticsearch client object
        index_list (list): List of indices the alias has to point to
        alias_name (str): Name of the alias
        logger: logging object to log at debug and exception level

        **kwargs:
            https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-aliases.html
    """
    logger.debug('Putting alias %s to indices: %s', alias_name, str(index_list))
    connection.indices.put_alias(index=index_list, name=alias_name, **kwargs)
    logger.debug('Alias %s now points to indices %s', alias_name, str(index_list))


def delete_alias(connection, index_list, alias_name, logger, **kwargs):
    # type: (Elasticsearch, List[str], str, logging.Logger, **Any) -> None
    """
    Delete alias `alias_name` from list of indices in `index_list`
    Args:
        connection: Elasticsearch client object
        index_list (list): List of indices the alias has to point to
        alias_name (str): Name of the alias
        logger: logging object to log at debug and exception level

        **kwargs:
            https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-aliases.html
    """
    logger.debug('Removing alias %s from indices: %s', alias_name, str(index_list))
    connection.indices.delete_alias(index=index_list, name=alias_name, **kwargs)
    logger.debug('Alias %s removed from indices %s', alias_name, str(index_list))
