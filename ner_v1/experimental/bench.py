# Notes:
# This script assumes external service will make only 1 call with all texts and all entities provided.
# Our goal mostly is too optimize for len(texts) == 1
# We are keeping structured text, fallback text stuff etc on the side for now, those parts are simple
# if else conditions that shouldn't be bottleneck

# The ner side cost incurred in making multiple calls from an external service (serially or in parallel) is not
# measurable with this script. There is multiple levels of concurrency involved in that approach - how many workers
# in the tpool, how many ner web workers, tpool <-> ner throughput, ner workers <-> ES throughput
# Also todo is to think how can caching be applied on top of single query method

import argparse
import collections
import json
import pathlib
from concurrent.futures import ThreadPoolExecutor
from timeit import default_timer as timer

import pandas as pd
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

es_index = 'entity_index'
es_url = '...'
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
    def wrapped_parse(cls, *args, **kwargs):
        try:
            return cls.parse(*args, **kwargs)
        except Exception as e:
            print(f'Got error "{e}" while trying to parse for {cls.__name__}')

        return 1e9, []

    @classmethod
    def parse(cls, responses, len_t, len_e):
        # responses is [R, ... size T * E]
        es_took = 0
        r = []
        for i in range(len_t):
            d = collections.defaultdict(list)
            for j in range(len_e):
                es_r = responses[i * len_e + j]
                es_took += es_r['took']
                for hit in es_r['hits']['hits']:
                    entity_name = hit['_source']['entity_data']
                    entity_value = hit['_source']['value']
                    entity_variants = hit['highlight']['variants']
                    d[(entity_name, entity_value)].extend(entity_variants)
            for (entity_name, entity_value) in sorted(d.keys()):
                r.append([entity_name, entity_value, list(sorted(d[(entity_name, entity_value)]))])
        return es_took, r

    @classmethod
    def parse_multiplexed(cls, responses, len_t, len_e):
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
        # responses is [[R, ... size T * E]]
        return Mode.parse(responses[0], len_t, len_e)


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
        # responses is [[R', ... size T]]
        return Mode.parse_multiplexed(responses[0], len_t, len_e)


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
        return Mode.parse_multiplexed(responses, len_t, len_e)


# modes are TE/1, T/E, T/1, E/T, 1/TE, 1/T
QUERY_MODES = [TE_One, One_TE, T_One, One_T, T_E, E_T, ]
json_headers = {'Content-type': 'application/json'}


class Executor(object):
    def __init__(self, tpool_size=0):
        self.tpool_size = tpool_size
        self.pool = None

    def _execute(self, q):
        # print('=' * 80)
        # print(q)
        # print('=' * 80)
        return requests.post(f'{es_url}/_msearch/', data=q, headers=json_headers).json()['responses']

    def execute(self, queries):
        start = timer()
        results = []
        use_pool = len(queries) > 1 and self.pool
        if use_pool:
            results = list(self.pool.map(self._execute, queries))
        else:
            for q in queries:
                results.append(self._execute(q))

        return timer() - start, results

    def run_detection(self, texts, entities, mode_cls):
        queries = mode_cls.build(texts, entities)
        exe_time, responses = self.execute(queries)
        es_time, parsed = mode_cls.parse(responses, len(texts), len(entities))
        return exe_time, es_time, parsed

    def close(self):
        if self.pool:
            self.pool.shutdown()

    def __enter__(self):
        if self.tpool_size:
            # careful not to use ProcessPool in this place because child processes can stick around when script exits
            # as we are not terminating the pool explicitly
            self.pool = ThreadPoolExecutor(max_workers=self.tpool_size)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def chunks(texts_, bs):
    if bs:
        for i in range(0, len(texts_), bs):
            yield texts_[i:i + bs]
    else:
        yield texts_


def make_expected_output(texts, entities, bs=0):
    it = chunks(texts, bs)
    all_parsed = []
    with Executor() as e:
        for chunk in it:
            _, _, parsed = e.run_detection(chunk, entities, TE_One)
            all_parsed.append(parsed)
    return all_parsed


def bench(texts, entities, bs=0, n_runs=3, pool_sizes=(0,)):
    report_data_cols = ['mode', 'pool_size', 'avg_exe_time', 'avg_es_time', 'correct']
    report_data = []

    expected_parsed = make_expected_output(texts, entities, bs)
    for mode_cls in QUERY_MODES:
        for pool_size in pool_sizes:
            print(f'Running {mode_cls.__name__} with pool size {pool_size}')
            exe_times, es_times, acc = [], [], []
            for run_no in range(n_runs):
                # TODO: Should executor be re-init everytime ?
                exe_time, es_time, correct = 0, 0, True
                it = chunks(texts, bs)
                with Executor(tpool_size=pool_size) as e:
                    for chunk, expected_parsed_chunk in zip(it, expected_parsed):
                        exe_time_, es_time_, parsed_ = e.run_detection(chunk, entities, mode_cls)
                        exe_time += exe_time_
                        es_time += es_time_
                        if parsed_ != expected_parsed_chunk:
                            print('=' * 80)
                            print('-' * 80)
                            print(f'{mode_cls.__name__} has different output than expected')
                            print('-' * 80)
                            print(f'Got')
                            print('-' * 80)
                            print(parsed_)
                            print('-' * 80)
                            print(f'But expected')
                            print('-' * 80)
                            print(expected_parsed_chunk)
                            print('-' * 80)
                            print('=' * 80)
                            correct = False
                        # parsed += parsed_
                    exe_times.append(exe_time)
                    es_times.append(es_time)
                    acc.append(int(correct))

            mexe_times = float(sum(exe_times)) / len(exe_times)
            mes_times = float(sum(es_times)) / len(es_times)
            report_data.append((
                mode_cls.__name__,
                pool_size,
                mexe_times,
                mes_times,
                sum(acc),
            ))

    df = pd.DataFrame(report_data, columns=report_data_cols)
    return df
    # TODO:
    # run rest of the text detector code*
    # log
    # instrument total time


def main(args):
    import pdb
    global es_index, es_url
    es_index = args.es_index
    es_url = args.es_url
    texts = [line.strip() for line in open(args.texts_file)]
    entities = [line.strip() for line in open(args.entities_file)]
    tfile = pathlib.Path(args.texts_file).resolve()
    report_file = str(tfile.parent / f'{tfile.name}.{len(texts)}_texts.{len(entities)}_entities.out')
    try:
        df = bench(texts=texts, entities=entities, bs=args.batch_size, n_runs=args.n_runs, pool_sizes=args.pool_sizes)
        df.to_csv(report_file, index=False)
    except Exception:
        pdb.post_mortem()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--es_index', type=str, required=True)
    parser.add_argument('--es_url', type=str, required=True)
    parser.add_argument('--texts_file', type=str, required=True)
    parser.add_argument('--entities_file', type=str, required=True)
    parser.add_argument('--batch_size', type=int, required=False, default=0)
    parser.add_argument('--n_runs', type=int, required=False, default=3)
    parser.add_argument('--pool_sizes', type=int, nargs='+', required=False, default=[0])
    cargs = parser.parse_args()
    main(cargs)
