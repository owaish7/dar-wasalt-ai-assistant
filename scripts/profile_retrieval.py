"""Measure local embedding/retrieval latency and resident memory, not model latency."""
import argparse
import json
import statistics
import time
from pathlib import Path

import psutil

from backend.retrieval import Retriever, load_corpus


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=Path("data/fixtures/corpus.jsonl"))
    parser.add_argument("--index", type=Path, default=Path("data/fixtures/index.npz"))
    parser.add_argument("--cache", default=".cache/fastembed")
    args = parser.parse_args()
    start = time.perf_counter()
    retriever = Retriever(load_corpus(args.corpus), args.index, "hybrid", args.cache)
    load_s = time.perf_counter() - start
    measurements = []
    for question in ["Where are the waterfront villas?", "ما هي خدمات منصة وصلت؟", "Tell me about Cedar Bay", "ما الفرق بين المطور ومنصة العقارات؟"] * 5:
        start = time.perf_counter()
        retriever.search(question, [])
        measurements.append((time.perf_counter() - start) * 1000)
    report = {"synthetic": any(p.synthetic for p in retriever.passages), "passages": len(retriever.passages), "load_seconds": round(load_s, 3),
        "retrieval_median_ms": round(statistics.median(measurements), 2),
        "retrieval_max_ms": round(max(measurements), 2),
        "rss_mb": round(psutil.Process().memory_info().rss / 1024**2, 1),
        "note": "Local process RSS; not a hosted/container benchmark. No OpenRouter call was made."}
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/retrieval-profile.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
