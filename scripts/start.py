"""Restore a private Render bundle, then replace this process with the ASGI server."""
import base64
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def main():
    load_dotenv()
    bundle_path = os.getenv("CORPUS_BUNDLE_PATH")
    if bundle_path:
        source = Path(bundle_path)
        if source.stat().st_size > 2_000_000:
            raise ValueError("Corpus bundle too large")
        payload = json.loads(source.read_text(encoding="utf-8"))
        target = Path("data/private/runtime")
        target.mkdir(parents=True, exist_ok=True)
        (target / "corpus.jsonl").write_text(payload["corpus_jsonl"], encoding="utf-8")
        (target / "index.npz").write_bytes(base64.b64decode(payload["index_base64"], validate=True))
        os.environ["CORPUS_PATH"] = str(target / "corpus.jsonl")
        os.environ["INDEX_PATH"] = str(target / "index.npz")
    os.execv(sys.executable, [sys.executable, "-m", "uvicorn", "backend.main:app",
        "--host", "0.0.0.0", "--port", os.getenv("PORT", "8000"), "--workers", "1",
        "--no-access-log", "--log-level", "info"])


if __name__ == "__main__":
    main()
