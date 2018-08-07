from six import string_types
import re
import collections
from lib.nlp.const import TOKENIZER
from ..constants import ELASTICSEARCH_SEARCH_SIZE, ELASTICSEARCH_VERSION_MAJOR, ELASTICSEARCH_VERSION_MINOR

log_prefix = 'datastore.elastic_search.query'


def dictionary_query(connection, index_name, doc_type, entity_name, **kwargs):
    """
    Get all variants data for a entity stored in the index as a dictionary

    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        doc_type: The type of the documents that will be indexed
        entity_name: name of the entity to perform a 'term' query on
        kwargs:
            Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search

    Returns:
        dictionary, search results of the 'term' query on entity_name, mapping keys to lists containing
        synonyms/variants of the key
    """
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
    kwargs = dict(kwargs, body=data, doc_type=doc_type, size=ELASTICSEARCH_SEARCH_SIZE, index=index_name,
                  scroll='1m')
    search_results = _run_es_search(connection, **kwargs)

    # Parse hits
    results = search_results['hits']['hits']
    for result in results:
        results_dictionary[result['_source']['value']] = result['_source']['variants']

    return results_dictionary


def full_text_query(connection, index_name, doc_type, entity_name, sentence, fuzziness_threshold,
                    search_language_script=None, **kwargs):
    """
    Performs compound elasticsearch boolean search query with highlights for the given sentence . The query
    searches for entity_name in the index & returns search results for the sentence only if entity_name is found.

    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        doc_type: The type of the documents that will be indexed
        entity_name: name of the entity to perform a 'term' query on
        sentence: sentence in which entity has to be searched
        fuzziness_threshold: fuzziness_threshold for elasticsearch match query 'fuzziness' parameter
        search_language_script: language of elasticsearch documents which are eligible for match
        kwargs:
            Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search

    Returns:
        collections.OrderedDict: dictionary of the parsed results from highlighted search query results
                                 on the sentence, mapping highlighted fuzzy entity variant to entity value ordered
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
    data = _generate_es_search_dictionary(entity_name, sentence, fuzziness_threshold,
                                          language_script=search_language_script)
    kwargs = dict(kwargs, body=data, doc_type=doc_type, size=ELASTICSEARCH_SEARCH_SIZE, index=index_name)
    results = _run_es_search(connection, **kwargs)
    results = _parse_es_search_results(results)
    return results


def _run_es_search(connection, **kwargs):
    """
    Execute the elasticsearch.ElasticSearch.search() method and return all results using
    elasticsearch.ElasticSearch.scroll() method if and only if scroll is passed in kwargs.
    Note that this is not recommended for large queries and can severly impact performance.

    Args:
        connection: Elasticsearch client object
        kwargs:
            Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search
    Returns:
        dictionary, search results from elasticsearch.ElasticSearch.search
    """
    scroll = kwargs.pop('scroll', False)
    if not scroll:
        return connection.search(**kwargs)

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
        if ELASTICSEARCH_VERSION_MAJOR > 6 or (ELASTICSEARCH_VERSION_MAJOR == 6 and ELASTICSEARCH_VERSION_MINOR >= 2):
            return fuzzy_setting
        return 'auto'

    return fuzzy_setting


def _generate_es_search_dictionary(entity_name, text, fuzziness_threshold, language_script=None):
    """
    Generates compound elasticsearch boolean search query dictionary for the sentence. The query generated
    searches for entity_name in the index and returns search results for the matched word (of sentence)
     only if entity_name is found.

    Args:
        entity_name: name of the entity to perform a 'term' query on
        text: The text on which we need to identify the enitites.
        fuzziness_threshold: fuzziness_threshold for elasticsearch match query 'fuzziness' parameter
        language_script: language of documents to be searched, optional, defaults to None

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

    if language_script is not None:
        term_dict_language = {
            'term': {
                'language_script': {
                    'value': language_script
                }
            }
        }
        must_terms.append(term_dict_language)

    data = {
        'query': {
            'bool': {
                'must': must_terms,
                'should': [],
                'minimum_number_should_match': 1
            }
        }
    }
    query_should_data = []
    query = {
        'match': {
            'variants': {
                'query': text,
                'fuzziness': _get_dynamic_fuzziness_threshold(fuzziness_threshold),
                'prefix_length': 1
            }
        }
    }
    query_should_data.append(query)
    data['query']['bool']['should'] = query_should_data
    data['highlight'] = {
        'fields': {
            'variants': {}
        },
        'order': 'score',
        'number_of_fragments': 20
    }
    return data


def _parse_es_search_results(results):
    """
    Parse highlighted results returned from elasticsearch query and generate a variants to values dictionary

    Args:
        results (dict): search results dictionary from elasticsearch including highlights and scores

    Returns:
        collections.OrderedDict: dict mapping matching variants to their entity values based on the
                                 parsed results from highlighted search query results

    Example:
        Parameter ngram_results has highlighted search results as follows:

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
        u'_index': u'gogo_entity_data',
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

        After parsing highlighted results, this function returns

        {...
         u'Mumbai': u'Mumbai',
         ...
         u'goa': u'goa',
         u'mumbai': u'mumbai',
         ...
        }

    """
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

    return variants_to_values
