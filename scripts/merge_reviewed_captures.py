"""Merge supervised browser captures with an existing private corpus, offline."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from backend.retrieval import load_corpus
from scripts.collect import permitted, validate_permissions
from scripts.curate_corpus import curate


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', required=True, type=Path)
    p.add_argument('--captures', required=True, type=Path)
    p.add_argument('--permission', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    if not args.output.resolve().is_relative_to(Path('data/private').resolve()):
        raise ValueError('Output must remain private')
    permissions = json.loads(args.permission.read_text(encoding='utf-8'))
    validate_permissions(permissions)
    rows = {r['url']: r for r in (json.loads(l) for l in args.base.read_text(encoding='utf-8').split('\n') if l)}
    captures = json.loads(args.captures.read_text(encoding='utf-8'))
    for row in captures:
        if not permitted(row['url'], permissions):
            raise ValueError('Capture URL outside approved scope')
        text = row['text']
        # The first home capture preceded DOM-based footer trimming.
        if row['url'] == 'https://darglobal.co.uk/':
            text = text[text.index('LONDON-LISTED'):].split('Discover Luxury Properties')[0]
        for marker in ('Related Blogs', 'Related Articles', 'Related Post', 'Discussion about this post', 'We value our privacy'):
            text = text.split(marker)[0]
        text = ' '.join(re.sub(r'[\ue000-\uf8ff]', '', text).split())
        arabic = len(re.findall(r'[\u0621-\u064a]', text))
        latin = len(re.findall(r'[A-Za-z]', text))
        if arabic > latin:
            row['language'] = 'ar'
        if len(text) > 24000:
            raise ValueError('Review and split long source before import')
        row.update(text=text, content_hash=hashlib.sha256(text.encode()).hexdigest(), synthetic=False,
                   permission_reference=permissions[row['company']]['reference'],
                   collection_method='supervised browser-visible text; reviewed content boundaries')
        rows[row['url']] = row
    kept, report = curate(list(rows.values()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in kept)+'\n', encoding='utf-8')
    report['passages'] = len(load_corpus(args.output))
    args.output.with_suffix('.review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
