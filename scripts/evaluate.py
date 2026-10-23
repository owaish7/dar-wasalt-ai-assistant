"""Run the reviewed evaluation set; output is evidence for human scoring, not an accuracy claim."""
import argparse
import json
import time
from pathlib import Path

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--cases", type=Path, default=Path("evaluation/cases.json"))
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--allow-fixtures", action="store_true")
    parser.add_argument("--allow-inference", action="store_true")
    args = parser.parse_args()
    if not args.allow_inference:
        raise SystemExit("Pass --allow-inference to acknowledge consuming free model quota.")
    cases = json.loads(args.cases.read_text(encoding="utf-8"))[:args.limit]
    with httpx.Client(timeout=100) as client:
        health = client.get(args.url.rstrip("/") + "/healthz")
        health.raise_for_status()
        if health.json()["synthetic"] and not args.allow_fixtures:
            raise SystemExit("This service uses fixtures. Do not count it as a real-content evaluation.")
        if not health.json()["inference_configured"]:
            raise SystemExit("Configure the server-side API key first.")
        if not args.allow_fixtures and any(c["review_status"] != "ready" for c in cases):
            raise SystemExit("Review expected facts/source URLs against approved content and set review_status=ready first.")
        results = []
        for case in cases:
            start = time.perf_counter()
            events, first_delta = [], None
            with client.stream("POST", args.url.rstrip("/") + "/api/chat", json={k: case[k] for k in ("message", "history", "language")}) as response:
                response.raise_for_status()
                kind = ""
                for line in response.iter_lines():
                    if line.startswith("event:"):
                        kind = line[6:].strip()
                    elif line.startswith("data:"):
                        payload = json.loads(line[5:])
                        events.append({"event": kind, "data": payload})
                        if kind == "delta" and first_delta is None:
                            first_delta = round((time.perf_counter() - start) * 1000)
            results.append({"case": case, "events": events, "first_token_ms": first_delta,
                "total_ms": round((time.perf_counter() - start) * 1000),
                "human_review": {"correct": None, "supported": None, "appropriate_abstention": None, "notes": ""}})
            print(f"Recorded {case['id']}; manual review pending")
            time.sleep(8)  # Stay below the default per-client app limit; provider limits may be lower.
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/evaluation-results.json").write_text(json.dumps({"health": health.json(), "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Saved private evaluation results. No automatic accuracy score is claimed.")


if __name__ == "__main__":
    main()
