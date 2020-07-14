# Notes:
# This script assumes external service will make only 1 call with all texts and all entities provided.
# Our goal mostly is too optimize for len(texts) == 1
# We are keeping structured text, fallback text stuff etc on the side for now, those parts are simple
# if else conditions that shouldn't be bottleneck

# The ner side cost incurred in making multiple calls from an external service (serially or in parallel) is not
# measurable with this script. There is multiple levels of concurrency involved in that approach - how many workers
# in the tpool, how many ner web workers, tpool <-> ner throughput, ner workers <-> ES throughput
# Also todo is to think how can caching be applied on top of single query method

import json
from concurrent.futures import ThreadPoolExecutor

import requests

"""
Texts can be loop/msearch

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
    def parse(cls, response):
        print('=' * 80)
        print(cls.__name__)
        print('=' * 80)
        print(response)


class ET_1(Mode):
    # E * T network calls 1 search query each
    @staticmethod
    def build(texts, entities):
        q = []
        for text in texts:
            for entity in entities:
                body = [
                    json.dumps({'index': es_index, 'type': doc_type}),
                    json.dumps(base_query(text=text, entities=[entity]))
                ]
                q.append('\n'.join(body))
        return q


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
            q.append('\n'.join(body))
        return q


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
            q.append('\n'.join(body))
        return q


class One_ET(Mode):
    # 1 network call with E * T search query each
    @staticmethod
    def build(texts, entities):
        q = []
        body = []
        for entity in entities:
            for text in texts:
                body.append(json.dumps({'index': es_index, 'type': doc_type}))
                body.append(json.dumps(base_query(text=text, entities=[entity])))
        q.append('\n'.join(body))
        return q


class One_T(Mode):
    # 1 network call with T search query each
    @staticmethod
    def build(texts, entities):
        q = []
        body = []
        for text in texts:
            body.append(json.dumps({'index': es_index, 'type': doc_type}))
            body.append(json.dumps(base_query(text=text, entities=entities)))

        q.append('\n'.join(body))


# modes are ET/1, T/E, E/T, 1/ET, 1/T
QUERY_MODES = [ET_1, T_E, E_T, One_ET, One_T]
json_headers = {'Content-type': 'application/json'}


class Executor(object):
    def __init__(self, tpool_size=0):
        self.pool = None
        if tpool_size:
            # careful not to use ProcessPool in this place because child processes can stick around when script exits
            # as we are not terminating the pool explicitly
            self.pool = ThreadPoolExecutor(max_workers=tpool_size)

    def _execute(self, q):
        print('=' * 80)
        print(q)
        print('=' * 80)
        return requests.post(es_url, data=q, headers=json_headers).json()

    def execute(self, queries, parser_fn):
        results = []
        use_pool = len(queries) > 1 and self.pool
        if use_pool:
            results = self.pool.map(self._execute, queries)
        else:
            for q in queries:
                results.append(self._execute(q))

        return [parser_fn(result) for result in results]

    def run_detection(self, texts, entities):
        for qm in QUERY_MODES:
            queries = qm.build(texts, entities)
            self.execute(queries, parser_fn=qm.parse)

# for pool_size in [0, 2, 4, 8, 16, 32, 64]:
# make the queries
# execute them
# parse the response and convert it to a list of hits per text
# instrument ES execution and total
# run n times for average
# record outputs for each for raw comparison
# run rest of the text detector code*

