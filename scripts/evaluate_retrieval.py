"""Check reviewed source recall and deterministic routing without model calls.

This is not an answer-accuracy evaluation. Reports stay in ignored artifacts/.
"""
import argparse
import json
import time
from pathlib import Path

from backend.conversation import route_message
from backend.retrieval import Retriever, load_corpus
from backend.schemas import ChatRequest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--cache', default='.cache/fastembed')
    args = parser.parse_args()
    retriever = Retriever(load_corpus(args.corpus), args.index, 'hybrid', args.cache)
    results = []
    for case in json.loads(Path('evaluation/cases.json').read_text(encoding='utf-8')):
        body = ChatRequest(**{k: case[k] for k in ('message', 'history', 'language')})
        route = route_message(body)
        start = time.perf_counter()
        passages = [] if route else retriever.search(body.message, [h.content for h in body.history])
        expected = set(case['expected_source_urls'])
        hit = bool(expected & {p.url for p in passages}) if expected else None
        if case['company'] == 'both' and expected:
            hit = hit and {p.company for p in passages} == {'dar', 'wasalt'}
        results.append({'id': case['id'], 'route': route, 'expected_source_retrieved': hit,
                        'retrieval_ms': round((time.perf_counter() - start) * 1000, 2),
                        'passages': [{'url': p.url, 'text': p.text} for p in passages]})
    Path('artifacts').mkdir(exist_ok=True)
    Path('artifacts/final-offline-40.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    answerable = [r for r in results if r['expected_source_retrieved'] is not None]
    print(f"Source recall: {sum(r['expected_source_retrieved'] for r in answerable)}/{len(answerable)}")
    print('Missing:', [r['id'] for r in answerable if not r['expected_source_retrieved']])
    print(f"Routing decisions: {sum(bool(r['route']) for r in results)}; model calls: 0")


if __name__ == '__main__':
    main()
