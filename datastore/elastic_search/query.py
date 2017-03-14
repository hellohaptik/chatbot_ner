import re
from ..constants import ELASTICSEARCH_SEARCH_SIZE

log_prefix = 'datastore.elastic_search.query'


def dictionary_query(connection, index_name, entity_list_name, **kwargs):
    results_dictionary = {}
    if 'index' not in kwargs:
        kwargs = dict(kwargs, index=index_name)
    data = {
        'query': {
            'term': {
                'entity_data': {
                    'value': entity_list_name
                }
            }
        },
        'size': ELASTICSEARCH_SEARCH_SIZE
    }
    kwargs = dict(kwargs, body=data)
    if 'doc_type' not in kwargs:
        kwargs = dict(kwargs, doc_type='')
    search_results = _run_es_search(connection, **kwargs)

    # Parse hits
    results = search_results['hits']['hits']
    for result in results:
        results_dictionary[result['_source']['value']] = result['_source']['variants']

    return results_dictionary


def ngrams_query(connection, index_name, entity_list_name, ngrams_list, ngrams_length, fuzziness_threshold, **kwargs):
    data = _generate_es_ngram_search_dictionary(entity_list_name, ngrams_list, fuzziness_threshold)
    if 'index' not in kwargs:
        kwargs = dict(kwargs, index=index_name)
    kwargs = dict(kwargs, body=data)
    if 'doc_type' not in kwargs:
        kwargs = dict(kwargs, doc_type='')
    ngram_results = _run_es_search(connection, **kwargs)
    return _parse_es_ngram_search_results(ngram_results, ngrams_length)


def _run_es_search(connection, **kwargs):
    """
    Bypass to elasticsearch.ElasticSearch.search() method
    Args:
        connection: Elasticsearch client object
        kwargs:
            Refer https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search
    """
    return connection.search(**kwargs)


def _generate_es_ngram_search_dictionary(entity_list_name, ngrams_list, fuzziness_threshold):
    term_dict = {
        'term': {
            'entity_data': {
                'value': entity_list_name
            }
        }
    }
    data = {
        'query': {
            'bool': {
                'must': [term_dict],
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
                    'fuzziness': fuzziness_threshold,
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
