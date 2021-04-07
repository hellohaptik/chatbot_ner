from __future__ import absolute_import

import collections
import json
import re

from six.moves import zip
from six import string_types

from datastore import constants
from language_utilities.constant import ENGLISH_LANG
from lib.nlp.const import TOKENIZER


def _generate_multi_entity_es_query(entities, text,
                                    fuzziness_threshold=1,
                                    language_script=ENGLISH_LANG,
                                    size=constants.ELASTICSEARCH_SEARCH_SIZE,
                                    as_json=False):
    """
    Generates compound elasticsearch boolean filter search query dictionary
    for a text for multiple entity_data.
    The query generated searches for entity_name in the index and returns search results for the
    matched word (of sentence) only if entity_name is found.

    Args:
        entities (list/str): list of the entity to perform a 'term' query on.
                             If str will converted to list internally.
        text (str): The text on which we need to identify the entities.
        fuzziness_threshold (int, optional): fuzziness_threshold for elasticsearch match query 'fuzziness' parameter.
            Defaults to 1
        language_script (str, optional): language of documents to be searched,
                                         optional, defaults to 'en'
        size (int, optional): number of records to return,
                              defaults to `ELASTICSEARCH_SEARCH_SIZE`
        as_json (bool, optional): Return the generated query as json string.
                                useful for debug purposes. Defaults to False

    Returns:
        dictionary, the search query for the text

    Examples Query generated:
        _generate_multi_entity_es_query(['city', 'restaurant'], "I want to go to
                                        mumbai")

        Outputs:
        {
        '_source': ['value', 'entity_data'],
            'query': {'bool': {'filter':
             [{'terms':
                {'entity_data': ['city', 'restaurant']}},
                {'terms': {'language_script': ['en']}}],
         'should': [{'match':
                    {'variants': {'query': 'I want to go to mumbai',
                     'fuzziness': 1, 'prefix_length': 1}}}],
                    'minimum_should_match': 1}},
          'highlight':
                {'fields': {'variants': {'type': 'unified'}},
                order': 'score', 'number_of_fragments': 20},
            'size': 10000
            }
    """

    # if entities instance of string convert to list
    if isinstance(entities, string_types):
        entities = [entities]

    filter_terms = []
    term_dict_entity_name = {
        'terms': {
            'entity_data': entities
        }
    }
    filter_terms.append(term_dict_entity_name)

    # search on language_script, add english as default search
    term_dict_language = {
        'terms': {
            'language_script': [ENGLISH_LANG]
        }
    }

    if language_script != ENGLISH_LANG:
        term_dict_language['terms']['language_script'].append(language_script)

    filter_terms.append(term_dict_language)

    should_terms = []
    query = {
        'match': {
            'variants': {
                'query': text,
                'fuzziness': fuzziness_threshold,
                'prefix_length': 1
            }
        }
    }

    should_terms.append(query)

    data = {
        '_source': ['value', 'entity_data'],
        'query': {
            'bool': {
                'filter': filter_terms,
                'should': should_terms,
                'minimum_should_match': 1
            },
        },
        'highlight': {
            'fields': {
                'variants': {
                    'type': 'unified'
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


def _parse_multi_entity_es_results(results_list):
    """
    This will parse highlighted results returned from elasticsearch query and
    generate a variants to values dictionary mapped to each entity for each
    search text terms.

    Args:
        results_list (list of dict):
            search results list of dictionaries from elasticsearch including highlights
             and scores

    Returns:
        list of dict of collections.OrderedDict:
            list containing dicts mapping each entity to matching variants to their entity
            values based on the parsed results from highlighted search query results

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
            {
            'city': OrderedDict([
                                ('Mumbai', 'Mumbai'),
                                ('mumbai', 'mumbai'),
                                ('goa', 'goa')
                                ])
            },
            {
            'city': OrderedDict([
                                ('Jabalpur', 'Jabalpur'),
                                ('Jamalpur', 'Jamalpur'),
                                ('goa', 'goa')
                                ])
            }
       ]



    """
    entity_variants_to_values_list = []

    if results_list:
        for results in results_list:
            entity_dict = {}
            entity_variants_to_values_dict = {}
            if results['hits']['total'] > 0:
                for hit in results['hits']['hits']:
                    if 'highlight' not in hit:
                        continue

                    value = hit['_source']['value']
                    entity_name = hit['_source']['entity_data']

                    if entity_name not in entity_dict:
                        entity_dict[entity_name] = {'value': [], 'variant': []}

                    entity_dict[entity_name]['value'].extend(
                        [value for _ in hit['highlight']['variants']])
                    entity_dict[entity_name]['variant'].extend(
                        [variant for variant in hit['highlight']['variants']])

                for each_entity in entity_dict.keys():
                    entity_values = entity_dict[each_entity]['value']
                    entity_variants = entity_dict[each_entity]['variant']
                    entity_variants_to_values = collections.OrderedDict()

                    for value, variant in zip(entity_values, entity_variants):
                        variant = re.sub(r'\s+', ' ', variant.strip())
                        variant_no_highlight_tags = variant.replace('<em>', '').replace('</em>', '').strip()
                        if variant.count('<em>') == len(TOKENIZER.tokenize(variant_no_highlight_tags)):
                            variant = variant_no_highlight_tags
                            if variant not in entity_variants_to_values:
                                entity_variants_to_values[variant] = value
                    entity_variants_to_values_dict[each_entity] = entity_variants_to_values
            entity_variants_to_values_list.append(entity_variants_to_values_dict)
    return entity_variants_to_values_list
