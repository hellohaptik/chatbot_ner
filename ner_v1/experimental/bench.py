# Notes:
# This script assumes external service will make only 1 call with all texts and all entities provided.
# Our goal mostly is too optimize for len(texts) == 1
# We are keeping structured text, fallback text stuff etc on the side for now, those parts are simple
# if else conditions that shouldn't be bottleneck

# The ner side cost incurred in making multiple calls from an external service (serially or in parallel) is not
# measurable with this script. There is multiple levels of concurrency involved in that approach - how many workers
# in the tpool, how many ner web workers, tpool <-> ner throughput, ner workers <-> ES throughput
# Also todo is to think how can caching be applied on top of single query method

import collections
import json
from concurrent.futures import ThreadPoolExecutor
from timeit import default_timer as timer

import requests

"""
multiple entities E, multiple texts T
    ## E1 E2 E3 E4 ... E
    T1  .  .  .  . ... .
    T2  .  .  .  . ... .
    T3  .  .  .  . ... .
    .   .  .  .  . ... .
    .   .  .  .  . ... .
    .   .  .  .  . ... .
    T   .  .  .  . ... .
    
    E * T - double nested tpool loop with v1/text
    T - tpool loop over texts with E queries msearch (over entities)
    E - tpool loop over entities with T queries msearch (over texts)
    1 - E * T queries msearch flattened (text entity pairs)
    1 - T queries msearch (over texts)
    
    
Output as:
[
    [entity_name, value, [variants, ...]],
    ...
]
"""

scheme = 'http'
host = ''
port = ''
es_index = 'entity_index'
es_url = f'{scheme}://{host}:{port}/{es_index}/_msearch/'
doc_type = 'data_dictionary'
es_size = 100


def base_query(text, entities):
    q = {
        "_source": [
            "entity_data", "value"
        ],
        "query": {
            "bool": {
                "filter": [
                    {
                        "terms": {
                            "entity_data": entities
                        }
                    },
                    {
                        "terms": {
                            "language_script": [
                                "en"
                            ]
                        }
                    }
                ],
                "should": [
                    {
                        "match": {
                            "variants": {
                                "query": text,
                                "fuzziness": 1,
                                "prefix_length": 1
                            }
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        },
        "highlight": {
            "fields": {
                "variants": {
                    "type": "unified"
                }
            },
            "order": "score",
            "number_of_fragments": 0
        },
        "size": es_size
    }
    return q


class Mode(object):
    @classmethod
    def parse(cls, responses, len_t, len_e):
        # responses is [R, ... size T * E]
        es_took = 0
        r = []
        for i in range(len_t):
            d = collections.defaultdict(list)
            for j in range(len_e):
                es_r = responses[i * len_t + j][0]
                es_took += es_r['took']
                for hit in es_r['hits']['hits']:
                    entity_name = hit['_source']['entity_data']
                    entity_value = hit['_source']['value']
                    entity_variants = hit['highlight']['variants']
                    d[(entity_name, entity_value)].extend(entity_variants)
            for (entity_name, entity_value) in sorted(d.keys()):
                r.append([entity_name, entity_value, list(sorted(d[(entity_name, entity_value)]))])
        return es_took, r


class TE_One(Mode):
    # T * E network calls 1 search query each
    @staticmethod
    def build(texts, entities):
        q = []
        for text in texts:
            for entity in entities:
                body = [
                    json.dumps({'index': es_index, 'type': doc_type}),
                    json.dumps(base_query(text=text, entities=[entity]))
                ]
                body.append('\n')
                q.append('\n'.join(body))
        return q

    @classmethod
    def parse(cls, responses, len_t, len_e):
        # responses is [[R], ... size T x E]
        # flatten
        responses = [response[0] for response in responses]
        return Mode.parse(responses, len_t, len_e)


class One_TE(Mode):
    # 1 network call with T * E search query each
    @staticmethod
    def build(texts, entities):
        q = []
        body = []
        for text in texts:
            for entity in entities:
                body.append(json.dumps({'index': es_index, 'type': doc_type}))
                body.append(json.dumps(base_query(text=text, entities=[entity])))

        body.append('\n')
        q.append('\n'.join(body))
        return q

    @classmethod
    def parse(cls, responses, len_t, len_e):
        # responses is [R, ... size T * E]
        return Mode.parse(responses, len_t, len_e)


class T_E(Mode):
    # T network calls E search query each
    @staticmethod
    def build(texts, entities):
        q = []
        for text in texts:
            body = []
            for entity in entities:
                body.append(json.dumps({'index': es_index, 'type': doc_type}))
                body.append(json.dumps(base_query(text=text, entities=[entity])))
            body.append('\n')
            q.append('\n'.join(body))
        return q

    @classmethod
    def parse(cls, responses, len_t, len_e):
        # responses is [[R, ... size E], ... size T]
        # flatten
        responses = [es_r for response in responses for es_r in response]
        return Mode.parse(responses, len_t, len_e)


class E_T(Mode):
    # E network calls T search query each
    @staticmethod
    def build(texts, entities):
        q = []
        for entity in entities:
            body = []
            for text in texts:
                body.append(json.dumps({'index': es_index, 'type': doc_type}))
                body.append(json.dumps(base_query(text=text, entities=[entity])))
            body.append('\n')
            q.append('\n'.join(body))
        return q

    @classmethod
    def parse(cls, responses, len_t, len_e):
        # responses is [[R, ... size T], ... size E]
        # take a transpose and flatten
        responses = [response[i] for i in range(len_t) for response in responses]
        return Mode.parse(responses, len_t, len_e)


class One_T(Mode):
    # 1 network call with T search query each
    @staticmethod
    def build(texts, entities):
        q = []
        body = []
        for text in texts:
            body.append(json.dumps({'index': es_index, 'type': doc_type}))
            body.append(json.dumps(base_query(text=text, entities=entities)))

        body.append('\n')
        q.append('\n'.join(body))
        return q

    @classmethod
    def parse(cls, responses, len_t, len_e):
        # responses is [R', ... size T]
        es_took = 0
        r = []
        for es_r in responses:
            d = collections.defaultdict(list)
            es_took += es_r['took']
            for hit in es_r['hits']['hits']:
                entity_name = hit['_source']['entity_data']
                entity_value = hit['_source']['value']
                entity_variants = hit['highlight']['variants']
                d[(entity_name, entity_value)].extend(entity_variants)
            for (entity_name, entity_value) in sorted(d.keys()):
                r.append([entity_name, entity_value, list(sorted(d[(entity_name, entity_value)]))])
        return es_took, r


class T_One(Mode):
    # T network call with 1 search query each
    @staticmethod
    def build(texts, entities):
        q = []
        for text in texts:
            body = []
            body.append(json.dumps({'index': es_index, 'type': doc_type}))
            body.append(json.dumps(base_query(text=text, entities=entities)))
            body.append('\n')
            q.append('\n'.join(body))
        return q

    @classmethod
    def parse(cls, responses, len_t, len_e):
        # responses is [[R'], ... size T]
        # flatten
        responses = [response[0] for response in responses]
        return One_T.parse(responses, len_t, len_e)


# modes are TE/1, T/E, T/1, E/T, 1/TE, 1/T
QUERY_MODES = [TE_One, One_TE, T_One, One_T, T_E, E_T, ]
json_headers = {'Content-type': 'application/json'}


class Executor(object):
    def __init__(self, tpool_size=0):
        self.pool = None
        if tpool_size:
            # careful not to use ProcessPool in this place because child processes can stick around when script exits
            # as we are not terminating the pool explicitly
            self.pool = ThreadPoolExecutor(max_workers=tpool_size)

    def _execute(self, q):
        # print('=' * 80)
        # print(q)
        # print('=' * 80)
        return requests.post(es_url, data=q, headers=json_headers).json()['responses']

    def execute(self, queries):
        start = timer()
        results = []
        use_pool = len(queries) > 1 and self.pool
        if use_pool:
            results = self.pool.map(self._execute, queries)
        else:
            for q in queries:
                results.append(self._execute(q))

        return timer() - start, results

    def run_detection(self, texts, entities, mode_cls):
        queries = mode_cls.build(texts, entities)
        exe_time, responses = self.execute(queries)
        es_time, parsed = mode_cls.parse(responses, len(texts), len(entities))
        return exe_time, es_time, parsed

    def bench(self, texts, entities):
        for mode_cls in QUERY_MODES:
            exe_time, es_time, parsed = self.run_detection(texts, entities, mode_cls)
            print("=" * 80)
            print("-" * 80)
            print(f'{mode_cls.__name__}, exec time: {exe_time}, es time: {es_time}')
            print("-" * 80)
            print(parsed)
            print("-" * 80)
            print("=" * 80)


def make_expected_output(texts, entities):
    e = Executor()
    _, _, parsed = e.run_detection(texts, entities, TE_One)
    return parsed

# for pool_size in [0, 2, 4, 8, 16, 32, 64]:
# instrument ES execution and total
# run n times for average
# record outputs for each for raw comparison
# run rest of the text detector code*
