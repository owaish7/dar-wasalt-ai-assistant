"""Normalize and deduplicate a private crawl before indexing; retain a review trail."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from backend.retrieval import load_corpus

CONTACT = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\+\d[\d ()-]{7,}\d")
RELATED = re.compile(r"\b(?:Other|Related)\s+projects\b.*?\bView\s+all\s+projects\b", re.I)
RELATED_AR = re.compile(r"(?:مشاريع\s+[أا]خرى|المشاريع\s+الأخرى).*?(?:عرض\s+(?:كل|جميع)\s+المشاريع|عرض\s+الكل)")


def curate(rows):
    kept, removed, seen = [], [], set()
    redactions = 0
    relabelled = []
    related_blocks = 0
    for original in rows:
        row = dict(original)
        text = " ".join(row["text"].split()).replace("Your browser does not support the video tag. ", "")
        text, removed_blocks = RELATED.subn(" ", text)
        related_blocks += removed_blocks
        text, removed_blocks = RELATED_AR.subn(" ", text)
        related_blocks += removed_blocks
        text = " ".join(text.split())
        text, count = CONTACT.subn("[contact omitted]", text)
        if row["language"] == "ar" and len(re.findall(r"[\u0621-\u064a]", text)) < 30:
            row["language"] = "en"
            relabelled.append(row["url"])
        redactions += count
        content_hash = hashlib.sha256(text.encode()).hexdigest()
        key = (row["language"], content_hash)
        reason = "duplicate normalized content" if key in seen else "insufficient readable text" if len(text) < 150 else None
        if reason:
            removed.append({"url": row["url"], "reason": reason})
            continue
        seen.add(key)
        row.update(text=text, content_hash=content_hash)
        kept.append(row)
    return kept, {"input_pages": len(rows), "retained_pages": len(kept), "removed": removed,
                  "contact_redactions": redactions, "languages": dict(Counter(r["language"] for r in kept)),
                  "arabic_routes_with_english_body": relabelled,
                  "related_project_blocks_removed": related_blocks,
                  "note": "Automated cleanup plus agent review; not human certification or independent verification of publisher claims."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(Path("data/private").resolve()):
        raise SystemExit("Curated content must remain under ignored data/private/")
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").split("\n") if line.strip()]
    # Prefer canonical project pages over identical product-category copies.
    rows.sort(key=lambda r: "/product-category/" in r["url"])
    kept, report = curate(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in kept) + "\n", encoding="utf-8")
    passages = load_corpus(args.output)
    report["passages"] = len(passages)
    args.output.with_suffix(".review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "removed"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
