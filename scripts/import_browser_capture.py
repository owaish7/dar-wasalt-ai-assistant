"""Import reviewed visible-text Wasalt captures; never fetch or solve access challenges."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from backend.retrieval import load_corpus, safe_url
from scripts.collect import permitted, validate_permissions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--permission', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(Path('data/private').resolve()):
        raise ValueError('Output must stay under data/private')
    approvals = json.loads(args.permission.read_text(encoding='utf-8'))
    validate_permissions(approvals, ('wasalt',))
    rows = json.loads(args.input.read_text(encoding='utf-8'))
    for row in rows:
        if not safe_url(row['url']) or not permitted(row['url'], {'wasalt': approvals['wasalt']}):
            raise ValueError('Capture URL is outside scope')
        ar, corporate = row['language'] == 'ar', '/corporate' in row['url']
        start = ('حلول عقارية مبتكرة' if ar else 'Innovating AI-Powered') if corporate else ('وصلت - منصتك' if ar else 'Sell, Rent, Buy')
        end = ('تواصل معنا' if ar else 'Contact us') if corporate else ('أشهر المدن والعقارات' if ar else 'Popular searches')
        text = row['text']
        if start not in text or end not in text or text.index(start) >= text.index(end):
            raise ValueError('Expected reviewed page boundaries missing; inspect capture')
        text = text[text.index(start):text.index(end)]
        # These are sample UI/team illustrations, not company headcounts.
        text = text.replace('46 Members', '').replace('46 عضو', '')
        text = ' '.join(re.sub(r'[\ue000-\uf8ff]', '', text).split())
        row.pop('faqs', None)
        row.update(text=text, company='wasalt', synthetic=False,
                   permission_reference=approvals['wasalt']['reference'],
                   collection_method='browser-visible-text; FAQ accordions explicitly expanded',
                   content_hash=hashlib.sha256(text.encode()).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text('\n'.join(json.dumps(row, ensure_ascii=False) for row in rows) + '\n', encoding='utf-8')
    print(f'Imported {len(rows)} source pages / {len(load_corpus(args.output))} passages')


if __name__ == '__main__':
    main()
