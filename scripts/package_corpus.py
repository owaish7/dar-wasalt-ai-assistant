"""Package approved content and its precomputed index as one private secret file."""
import argparse
import base64
import gzip
import json
from pathlib import Path

from backend.retrieval import load_corpus


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=Path("data/private/corpus.jsonl"))
    parser.add_argument("--index", type=Path, default=Path("data/private/index.npz"))
    parser.add_argument("--output", type=Path, default=Path("data/private/deployment-bundle.json"))
    parser.add_argument("--compress-text", action="store_true", help="Compress corpus text for Render's aggregate secret-file limit.")
    args = parser.parse_args()
    load_corpus(args.corpus)
    data = {"index_base64": base64.b64encode(args.index.read_bytes()).decode("ascii")}
    if args.compress_text:
        data["corpus_gzip_base64"] = base64.b64encode(gzip.compress(args.corpus.read_text(encoding="utf-8").encode("utf-8"), mtime=0)).decode("ascii")
    else:
        data["corpus_jsonl"] = args.corpus.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False)
    if len(payload.encode()) > 900_000:
        raise SystemExit("Bundle exceeds the 900 KB deployment budget. Render limits all secret files combined to 1 MB; reduce content and account for existing files.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print("Private deployment bundle prepared. Never commit it.")


if __name__ == "__main__":
    main()
