import argparse
import time
from pathlib import Path

import numpy as np

from backend.retrieval import EMBED_MODEL, embedding_model, fingerprint, load_corpus


def build(corpus: Path, output: Path, cache: str):
    passages = load_corpus(corpus)
    model = embedding_model(cache, allow_download=True)
    start = time.perf_counter()
    vectors = np.array(list(model.embed(["passage: " + p.title + " " + p.text for p in passages], batch_size=4)), dtype=np.float32)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, vectors=vectors, fingerprint=fingerprint(passages), model=EMBED_MODEL)
    print(f"Indexed {len(passages)} passages in {time.perf_counter() - start:.2f}s -> {output}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="data/fixtures/corpus.jsonl", type=Path)
    parser.add_argument("--output", default="data/fixtures/index.npz", type=Path)
    parser.add_argument("--cache", default=".cache/fastembed")
    args = parser.parse_args()
    build(args.corpus, args.output, args.cache)


if __name__ == "__main__":
    main()
