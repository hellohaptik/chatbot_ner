from __future__ import absolute_import

import collections
# std imports
import copy
import json
import re
import warnings

from six import string_types
from six.moves import range
from six.moves import zip

from datastore import constants
from datastore.exceptions import DataStoreRequestException
from external_api.constants import SENTENCE, ENTITIES
from language_utilities.constant import ENGLISH_LANG
from lib.nlp.const import TOKENIZER

# Local imports

log_prefix = 'datastore.elastic_search.query'


# Deprecated
def dictionary_query(connection, index_name, doc_type, entity_name, **kwargs):
    """
    Get all variants data for a entity stored in the index as a dictionary

    Args:
        connection: Elasticsearch client object
        index_name (str): The name of the index
        doc_type (str): The type of the documents that will be indexed
        entity_name (str): name of the entity to perform a 'term' query on
        kwargs:
            Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search

    Returns:
        dictionary, search results of the 'term' query on entity_name, mapping keys to lists containing
        synonyms/variants of the key
    """
    warnings.warn("dictionary_query() is deprecated; Please use get_entity_data()", DeprecationWarning)
    results_dictionary = {}
    data = {
        'query': {
            'term': {
                'entity_data': {
                    'value': entity_name
                }
            }
        }
    }
    kwargs = dict(kwargs, body=data, doc_type=doc_type, size=constants.ELASTICSEARCH_SEARCH_SIZE, index=index_name,
                  scroll='1m')
    search_results = _run_es_search(connection, **kwargs)

    # Parse hits
    results = search_results['hits']['hits']
    for result in results:
        results_dictionary[result['_source']['value']] = result['_source']['variants']

    return results_dictionary


def get_entity_supported_languages(connection, index_name, doc_type, entity_name, **kwargs):
    """
    Fetch languages supported by a specific entity
    Args:
        connection (elasticsearch.client.Elasticsearch): Elasticsearch client object
        index_name (str): The name of the index
        doc_type (str): The type of the documents that will be indexed
        entity_name (str): name of the entity for which the language codes are to be fetched
    Returns:
        (list): List of language codes supported by this entity
    """
    data = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "entity_data": entity_name
                        }
                    }
                ]
            }
        },
        "aggs": {
            "unique_values": {
                "terms": {
                    "field": "language_script.keyword",
                    "size": constants.ELASTICSEARCH_SEARCH_SIZE
                }
            }
        },
        "size": 0
    }
    kwargs = dict(
        kwargs, body=data, doc_type=doc_type, size=constants.ELASTICSEARCH_SEARCH_SIZE,
        index=index_name, filter_path=['aggregations.unique_values.buckets.key']
    )
    search_results = _run_es_search(connection, **kwargs)
    language_list = []
    if search_results:
        language_list = [bucket['key'] for bucket in search_results['aggregations']['unique_values']['buckets']]
    return language_list


def get_entity_data(connection, index_name, doc_type, entity_name, values=None, **kwargs):
    """
    Fetches entity data from ES for the specific entity
    Args:
        connection (elasticsearch.client.Elasticsearch): Elasticsearch client object
        index_name (str): The name of the index
        doc_type (str): The type of the documents that will be indexed
        entity_name (str): name of the entity for which the data is to be fetched
        values (str, optional): List of values for which data is to be fetched. If None, all
                                records are fetched
    Returns:
        (list): List of language codes supported by this entity
    """
    data = {
        "query": {
            "bool": {
                'must': [{
                    "match": {
                        "entity_data": entity_name
                    }
                }]
            }
        },
        "size": constants.ELASTICSEARCH_SEARCH_SIZE
    }

    query_list = []
    if values is not None:
        values_chunks = [values[i:i + 500] for i in range(0, len(values), 500)]
        for chunk in values_chunks:
            updated_query = copy.deepcopy(data)
            updated_query['query']['bool']['must'].append({
                "terms": {
                    "value.keyword": chunk
                }
            })
            query_list.append(updated_query)
    else:
        query_list.append(data)

    results = []
    for query in query_list:
        search_kwargs = dict(kwargs, body=query, doc_type=doc_type,
                             size=constants.ELASTICSEARCH_SEARCH_SIZE, index=index_name, scroll='1m')
        search_results = _run_es_search(connection, **search_kwargs)

        # Parse hits
        if search_results:
            results.extend(search_results['hits']['hits'])

    return results


def get_entity_unique_values(connection, index_name, doc_type, entity_name, value_search_term=None,
                             variant_search_term=None, empty_variants_only=False, **kwargs):
    """
    Search for values in entity with filters

    Args:
        connection (elasticsearch.client.Elasticsearch): Elasticsearch client object
        index_name (str): The name of the index
        doc_type (str): The type of the documents that will be indexed
        entity_name (str): name of the entity for which the data is to be fetched
        value_search_term (str): Filter values with the specific search term
        variant_search_term (str): Filter variants with the specific search term
        empty_variants_only (bool): Search for values with empty variants only
    Returns:
        list: List of values which match the filters and search criteria
    """
    # aggs count is set at 3,00,000 because it is a safe limit for now.
    # If the dictionary sizes increases beyond this, then the count will have to be
    # increased accordingly.
    # Also, aggs size doesn't belong in the const file because the number depends
    # on use case, data and the operation (unique/average/sum/min/max/count etc.)
    data = {
        "sort": [
            {
                "value.keyword": {
                    "order": "asc"
                }
            }
        ],
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "entity_data": entity_name
                        }
                    }
                ],
                "minimum_should_match": 0,
                "should": []
            }
        },
        "aggs": {
            "unique_values": {
                "terms": {
                    "field": "value.keyword",
                    "size": constants.ELASTICSEARCH_VALUES_SEARCH_SIZE,
                }
            }
        },
        "size": 0
    }

    if value_search_term:
        data['query']['bool']['minimum_should_match'] = 1
        _search_field = 'value'
        _search_term = value_search_term.lower()
        if len(_search_term.split()) > 1:
            # terms with spaces in them do not support wild queries on analyzed fields
            _search_field = 'value.keyword'
        data['query']['bool']['should'].append({
            "wildcard": {
                _search_field: u"*{0}*".format(_search_term)
            }
        })

    if empty_variants_only:
        data['query']['bool']['must_not'] = [
            {
                "exists": {
                    "field": "variants"
                }
            }
        ]
    elif variant_search_term:
        data['query']['bool']['minimum_should_match'] = 1
        data['query']['bool']['should'].append({
            "match": {
                "variants": variant_search_term
            }
        })

    kwargs = dict(
        kwargs, body=data, doc_type=doc_type, size=constants.ELASTICSEARCH_SEARCH_SIZE,
        index=index_name, filter_path=['aggregations.unique_values.buckets.key']
    )
    search_results = _run_es_search(connection, **kwargs)
    values = []
    if search_results:
        values = [bucket['key'] for bucket in search_results['aggregations']['unique_values']['buckets']]
    return values


def full_text_query(connection, index_name, doc_type, entity_name, sentences, fuzziness_threshold,
                    search_language_script=None, **kwargs):
    """
    Performs compound elasticsearch boolean search query with highlights for the given sentence . The query
    searches for entity_name in the index & returns search results for the sentence only if entity_name is found.

    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        doc_type: The type of the documents that will be indexed
        entity_name: name of the entity to perform a 'term' query on
        sentences(list of strings): sentences in which entity has to be searched
        fuzziness_threshold: fuzziness_threshold for elasticsearch match query 'fuzziness' parameter
        search_language_script: language of elasticsearch documents which are eligible for match
        kwargs:
            Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search

    Returns:
        list of collections.OrderedDict: list of dictionaries of the parsed results from highlighted search query
                            results on the sentence, mapping highlighted fuzzy entity variant to entity value ordered
                            by relevance order returned by elasticsearch

    Example:
        # The following example is just for demonstration purpose. Normally we should call
        # Datastore().get_similar_ngrams_dictionary to get these results

        db = DataStore()
        ngrams_list = ['Pune', 'Mumbai', 'Goa', 'Bangalore']
        ngrams_query(connection=db._client_or_connection, index_name=db._store_name,
                        doc_type=db._connection_settings[ELASTICSEARCH_DOC_TYPE],
                        entity_name='city', ngrams_list=ngrams_list,
                        fuzziness_threshold=2)

        {u'Bangalore': u'Bangalore',
         u'Mulbagal': u'Mulbagal',
         u'Multai': u'Multai',
         u'Mumbai': u'Mumbai',
         u'Pune': u'Pune',
         u'Puri': u'Puri',
         u'bangalore': u'bengaluru',
         u'goa': u'goa',
         u'mumbai': u'mumbai',
         u'pune': u'pune'}
    """
    index_header = json.dumps({'index': index_name, 'type': doc_type})
    data = []
    for sentence in sentences:
        query = _generate_es_search_dictionary(entity_name=entity_name,
                                               text=sentence,
                                               fuzziness_threshold=fuzziness_threshold,
                                               language_script=search_language_script)
        data.append(index_header)
        data.append(json.dumps(query))
    data = '\n'.join(data)

    kwargs = dict(kwargs, body=data, doc_type=doc_type, index=index_name)
    response = None
    try:
        response = _run_es_search(connection, msearch=True, **kwargs)
        results = _parse_es_search_results(response.get("responses"))
    except Exception as e:
        raise DataStoreRequestException(f'Error in datastore query on index: {index_name}', engine='elasticsearch',
                                        request=json.dumps(data), response=json.dumps(response)) from e
    return results


def _run_es_search(connection, msearch=False, **kwargs):
    """
    Execute the elasticsearch.ElasticSearch.msearch() method and return all results using
    elasticsearch.ElasticSearch.scroll() method if and only if scroll is passed in kwargs.
    Note that this is not recommended for large queries and can severly impact performance.

    Args:
        connection: Elasticsearch client object
        kwargs:
            Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search
    Returns:
        dictionary, search results from elasticsearch.ElasticSearch.msearch
    """
    scroll = kwargs.pop('scroll', False)
    if not scroll:
        if msearch:
            return connection.msearch(**kwargs)
        else:
            return connection.search(**kwargs)

    if scroll and msearch:
        raise ValueError('Scrolling is not supported in msearch mode')

    result = connection.search(scroll=scroll, **kwargs)
    scroll_id = result['_scroll_id']
    scroll_size = result['hits']['total']
    hit_list = result['hits']['hits']
    scroll_ids = [scroll_id]
    while scroll_size > 0:
        _result = connection.scroll(scroll_id=scroll_id, scroll=scroll)
        scroll_id = _result['_scroll_id']
        scroll_ids.append(scroll_id)
        scroll_size = len(_result['hits']['hits'])
        hit_list += _result['hits']['hits']

    result['hits']['hits'] = hit_list
    if scroll_ids:
        connection.clear_scroll(body={"scroll_id": scroll_ids})

    return result


def _get_dynamic_fuzziness_threshold(fuzzy_setting):
    """
    Approximately emulate AUTO:[low],[high] functionality of elasticsearch 6.2+ on older versions

    Args:
        fuzzy_setting (int or str): Can be int or "auto" or "auto:<int>,<int>"

    Returns:
         int or str: fuzziness as int when ES version < 6.2
                     otherwise the input is returned as it is
    """
    if isinstance(fuzzy_setting, string_types):
        if constants.ELASTICSEARCH_VERSION_MAJOR > 6 or \
                (constants.ELASTICSEARCH_VERSION_MAJOR == 6 and constants.ELASTICSEARCH_VERSION_MINOR >= 2):
            return fuzzy_setting
        return 'auto'

    return fuzzy_setting


def _generate_es_search_dictionary(entity_name, text,
                                   fuzziness_threshold=1,
                                   language_script=ENGLISH_LANG,
                                   size=constants.ELASTICSEARCH_SEARCH_SIZE,
                                   as_json=False):
    """
    Generates compound elasticsearch boolean search query dictionary for the sentence. The query generated
    searches for entity_name in the index and returns search results for the matched word (of sentence)
     only if entity_name is found.

    Args:
        entity_name (str): name of the entity to perform a 'term' query on
        text (str): The text on which we need to identify the enitites.
        fuzziness_threshold (int, optional): fuzziness_threshold for elasticsearch match query 'fuzziness' parameter.
            Defaults to 1
        language_script (str, optional): language of documents to be searched, optional, defaults to 'en'
        size (int, optional): number of records to return, defaults to `ELASTICSEARCH_SEARCH_SIZE`
        as_json (bool, optional): Return the generated query as json string. useful for debug purposes.
            Defaults to False

    Returns:
        dictionary, the search query for the text

    """
    must_terms = []
    term_dict_entity_name = {
        'term': {
            'entity_data': {
                'value': entity_name
            }
        }
    }
    must_terms.append(term_dict_entity_name)

    # search on language_script, add english as default search
    term_dict_language = {
        'terms': {
            'language_script': [ENGLISH_LANG]
        }
    }

    if language_script != ENGLISH_LANG:
        term_dict_language['terms']['language_script'].append(language_script)

    must_terms.append(term_dict_language)

    should_terms = []
    query = {
        'match': {
            'variants': {
                'query': text,
                'fuzziness': _get_dynamic_fuzziness_threshold(fuzziness_threshold),
                'prefix_length': 1
            }
        }
    }
    should_terms.append(query)

    data = {
        '_source': ['value'],
        'query': {
            'bool': {
                'must': must_terms,
                'should': should_terms,
                'minimum_should_match': 1
            },
        },
        'highlight': {
            'fields': {
                'variants': {
                    'type': 'unified'  # experimental in 5.x, default in 6.x and 7.x. Faster than 'plain'
                }
            },
            'order': 'score',
            'number_of_fragments': 20
        },
        'size': size
    }

    if as_json:
        data = json.dumps(data)

    return data


def _parse_es_search_results(results_list):
    """
    Parse highlighted results returned from elasticsearch query and generate a variants to values dictionary

    Args:
        results_list (list of dict): search results list of dictionaries from elasticsearch including highlights
                                    and scores

    Returns:
        list of collections.OrderedDict: list containing dicts mapping matching variants to their entity values based
                                  on the parsed results from highlighted search query results

    Example:
        Parameter ngram_results has highlighted search results as follows:

        [
            {u'_shards': {u'failed': 0, u'successful': 5, u'total': 5},
            u'hits': {u'hits': [{u'_id': u'AVrW02UE9WNuMIY9vmWn',
            u'_index': u'doc_type_name',
            u'_score': 11.501145,
            u'_source': {u'dict_type': u'variants',
            u'entity_data': u'city',
            u'value': u'goa',
            u'variants': [u'', u'goa']},
            u'_type': u'data_dictionary',
            u'highlight': {u'variants': [u'<em>goa</em>']}},
            {u'_id': u'AVrW02W99WNuMIY9vmcf',
            u'_index': u'entity_data',
            u'_score': 11.210829,
            u'_source': {u'dict_type': u'variants',
            u'entity_data': u'city',
            u'value': u'Mumbai',
            u'variants': [u'', u'Mumbai']},
            u'_type': u'data_dictionary',
            u'highlight': {u'variants': [u'<em>Mumbai</em>']}},
            ...
            u'max_score': 11.501145,
            u'total': 17},
            u'timed_out': False,
            u'took': 96}
        ]

        After parsing highlighted results, this function returns

        [
            {...
             u'Mumbai': u'Mumbai',
             ...
             u'goa': u'goa',
             u'mumbai': u'mumbai',
             ...
            }
        ]

    """
    variants_to_values_list = []
    if results_list:
        for results in results_list:
            entity_values, entity_variants = [], []
            variants_to_values = collections.OrderedDict()
            if results and results['hits']['total'] > 0:
                for hit in results['hits']['hits']:
                    if 'highlight' not in hit:
                        continue

                    value = hit['_source']['value']
                    for variant in hit['highlight']['variants']:
                        entity_values.append(value)
                        entity_variants.append(variant)

                for value, variant in zip(entity_values, entity_variants):
                    variant = re.sub('\s+', ' ', variant.strip())
                    variant_no_highlight_tags = variant.replace('<em>', '').replace('</em>', '').strip()
                    if variant.count('<em>') == len(TOKENIZER.tokenize(variant_no_highlight_tags)):
                        variant = variant_no_highlight_tags
                        if variant not in variants_to_values:
                            variants_to_values[variant] = value
            variants_to_values_list.append(variants_to_values)

    return variants_to_values_list


def get_crf_data_for_entity_name(connection, index_name, doc_type, entity_name, languages, **kwargs):
    """
    Get all sentence_list and entity_list for a entity stored in the index

    Args:
        connection (Elasticsearch): Elasticsearch client object
        index_name (str): The name of the index
        doc_type (str): The type of the documents that will be indexed
        entity_name (str): name of the entity to perform a 'term' query on
        languages (List[str]): list of languages for which to fetch sentences
        **kwargs: optional kwargs for es

    Returns:
        dictionary, search results of the 'term' query on entity_name, mapping keys to lists containing
        sentence_list and entity_list of the key

    Examples:
        training_data_query(connection, index_name, doc_type, entity_name, **kwargs)
        >>{
        'sentence_list': [
            'My name is hardik',
            'This is my friend Ajay'
                        ],
        'entity_list': [
            [
                'hardik'
            ],
            [
                'Ajay'
            ]
            ]
            }
    """

    data = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "entity_data": {
                                "value": entity_name
                            }
                        }
                    }
                ]
            }
        }
    }

    if languages:
        data['query']['bool']['filter'] = {
            "terms": {
                "language_script": languages
            }
        }

    kwargs = dict(kwargs,
                  body=data,
                  doc_type=doc_type,
                  size=constants.ELASTICSEARCH_SEARCH_SIZE,
                  index=index_name,
                  scroll='1m')
    search_results = _run_es_search(connection, **kwargs)

    # Parse hits
    results = search_results['hits']['hits']

    language_mapped_results = collections.defaultdict(list)

    for result in results:
        language_mapped_results[result['_source']['language_script']].append(
            {
                SENTENCE: result['_source']['sentence'],
                ENTITIES: result['_source']['entities']
            }
        )

    return dict(language_mapped_results)
