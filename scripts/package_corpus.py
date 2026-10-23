"""Package approved content and its precomputed index as one private secret file."""
import argparse
import base64
import json
from pathlib import Path

from backend.retrieval import load_corpus


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=Path("data/private/corpus.jsonl"))
    parser.add_argument("--index", type=Path, default=Path("data/private/index.npz"))
    parser.add_argument("--output", type=Path, default=Path("data/private/deployment-bundle.json"))
    args = parser.parse_args()
    load_corpus(args.corpus)
    payload = json.dumps({"corpus_jsonl": args.corpus.read_text(encoding="utf-8"),
        "index_base64": base64.b64encode(args.index.read_bytes()).decode("ascii")}, ensure_ascii=False)
    if len(payload.encode()) > 2_000_000:
        raise SystemExit("Bundle exceeds 2 MB; reduce corpus text before uploading to hosting secrets")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print("Private deployment bundle prepared. Never commit it.")


if __name__ == "__main__":
    main()
