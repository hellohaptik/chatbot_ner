import re

from ..constants import ELASTICSEARCH_SEARCH_SIZE, ELASTICSEARCH_VERSION_MAJOR, ELASTICSEARCH_VERSION_MINOR
from ner_v1.language_utilities.constant import ENGLISH_LANG


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


def ngrams_query(connection, index_name, doc_type, entity_name, ngrams_list, fuzziness_threshold,
                 search_language_script=ENGLISH_LANG, **kwargs):
    """
    Performs compound elasticsearch boolean search query with highlights for the given ngrams list. The query
    searches for entity_name in the index and returns search results for ngrams only if entity_name is found.

    Args:
        connection: Elasticsearch client object
        index_name: The name of the index
        doc_type: The type of the documents that will be indexed
        entity_name: name of the entity to perform a 'term' query on
        ngrams_list: list of ngrams to perform fuzzy search for
        fuzziness_threshold: fuzziness_threshold for elasticsearch match query 'fuzziness' parameter
        search_language_script: language of elasticsearch documents which are eligible for match
        kwargs:
            Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search

    Returns:
        dictionary of the parsed results from highlighted search query results on ngrams_list, mapping highlighted
        fuzzy entity variant to entity value

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
    ngram_results = {}
    if ngrams_list:
        ngrams_length = len(ngrams_list[0].strip().split())
        data = _generate_es_ngram_search_dictionary(entity_name, ngrams_list, fuzziness_threshold)
        kwargs = dict(kwargs, body=data, doc_type=doc_type, size=ELASTICSEARCH_SEARCH_SIZE, index=index_name,
                      language_script=search_language_script)
        ngram_results = _run_es_search(connection, **kwargs)
        ngram_results = _parse_es_ngram_search_results(ngram_results, ngrams_length)
    return ngram_results


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


def _get_dynamic_fuzziness_threshold(term, fuzzy_setting):
    """
    Approximately emulate AUTO:[low],[high] functionality of elasticsearch 6.2+ on older versions

    Args:
        term (str): search string
        fuzzy_setting (int or str): Can be int or "auto" or "auto:<int>,<int>"

    Returns:
         int or str: fuzziness as int when ES version < 6.2
                     otherwise the input is returned as it is
    """
    def parse_auto(auto_str):
        lo, hi = 3, 6
        if auto_str.lower().startswith("auto:"):
            try:
                lo, hi = map(int, auto_str[5:].split(","))
            except ValueError:
                pass
        return lo, hi

    if ELASTICSEARCH_VERSION_MAJOR > 6 or (ELASTICSEARCH_VERSION_MAJOR == 6 and ELASTICSEARCH_VERSION_MINOR >= 2):
        return fuzzy_setting

    if type(fuzzy_setting) == str:
        low, high = parse_auto(fuzzy_setting)
        if len(term) < low:
            return 0
        elif len(term) >= high:
            return 2
        else:
            return 1

    return fuzzy_setting


def _generate_es_ngram_search_dictionary(entity_name, ngrams_list, fuzziness_threshold, language_script=ENGLISH_LANG):
    """
    Generates compound elasticsearch boolean search query dictionary for the given ngrams list. The query generated
    searches for entity_name in the index and returns search results for ngrams only if entity_name is found.

    Args:
        entity_name: name of the entity to perform a 'term' query on
        ngrams_list: list of ngrams to perform fuzzy search for
        fuzziness_threshold: fuzziness_threshold for elasticsearch match query 'fuzziness' parameter
        language_script: language of documents to be searched
    Returns:
        dictionary, the search query for ngrams

    """
    term_dict_entity_name = {
        'term': {
            'entity_data': {
                'value': entity_name
            }
        }
    }
    term_dict_language = {
        'term': {
            'language_script': {
                'value': language_script
            }
        }
    }
    data = {
        'query': {
            'bool': {
                'must': [term_dict_entity_name, term_dict_language],
                'should': [],
                'minimum_number_should_match': 1
            }
        }
    }
    query_should_data = []
    for ngram in ngrams_list:
        query = {
            'match': {
                'variants': {
                    'query': ngram,
                    'fuzziness': _get_dynamic_fuzziness_threshold(ngram, fuzziness_threshold),
                    'prefix_length': 1,
                    'operator': 'and'
                }
            }
        }
        query_should_data.append(query)
    data['query']['bool']['should'] = query_should_data
    data['highlight'] = {
        'fields': {
            'variants': {}
        },
        'number_of_fragments': 20
    }

    return data


def _parse_es_ngram_search_results(ngram_results, ngrams_length):
    """
    Parses highlighted results returned from elasticsearch query on ngrams

    Args:
        ngram_results: search results dictionary from elasticsearch including highlights and scores
        ngrams_length: length of the ngrams in ngrams_list on which search query was performed

    Returns:
        dictionary of the parsed results from highlighted search query results on ngrams_list

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
    entity_value_list, variant_value_list = [], []
    variant_dictionary = {}
    if ngram_results and ngram_results['hits']['total'] > 0:
        for hit in ngram_results['hits']['hits']:
            count_of_variants = len(hit['highlight']['variants'])
            count = 0
            while count < count_of_variants:
                if len(hit['highlight']['variants'][count].split()) >= ngrams_length:
                    entity_value_list.append(hit['_source']['value'])
                    variant_value_list.append(hit['highlight']['variants'][count])
                count += 1
    count = 0

    while count < len(variant_value_list):
        variant_value_list[count] = re.sub('\s+', ' ', variant_value_list[count]).strip()
        if variant_value_list[count].count('<em>') == len(variant_value_list[count].split()):
            variant = variant_value_list[count].replace('<em>', '')
            variant = variant.replace('</em>', '')
            if variant.strip() in variant_dictionary:
                existing_value = variant_dictionary[variant.strip()]
                if len(existing_value.split(' ')) > len(entity_value_list[count].split(' ')):
                    variant_dictionary[variant.strip()] = entity_value_list[count]
            else:
                variant_dictionary[variant.strip()] = entity_value_list[count]
        count += 1

    return variant_dictionary
