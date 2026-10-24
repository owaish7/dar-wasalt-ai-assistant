# Expanded source coverage — 24 October 2026

Reviewed snapshot: **68 sources / 310 passages**, with **55 Dar Global and 13 Wasalt pages**, **52 English and 16 Arabic**. This is a bounded snapshot, not every page or live listing inventory. See `data/reviewed-source-manifest.json` for the complete retained URL inventory and capture dates.

## Added coverage

Dar: home/company information, Arabic company overview, investor relations, hospitality, commercial and golf segments, English/Arabic investment overview, six recent press announcements, three English blog articles and one Arabic article. These fill several previously blocked coverage areas through normal browser access.

Wasalt: advertising rules (Arabic text on an English route), English/Arabic service terms, three public Riyadh property examples, and three selected articles on buying a home, King Salman Park and Ejar. Existing English/Arabic home FAQs and corporate pages remain. The blog is an explicitly allowlisted official subdomain (`blog.wasalt.sa`); other arbitrary subdomains remain rejected.

## Collection and review

Ordinary Chrome navigation returned visible content without CAPTCHA, authentication, proxies or changed identity. No blocked challenge was solved. DOM text was captured with timestamps; navigation, footer, recommendation blocks and contact sections were trimmed. Only property fields before the advertiser/license section were retained for the three listing examples. Public contact patterns were redacted twice. The source language is classified by actual text, not the URL: the two advertising routes had identical Arabic content, so one was deduplicated.

The Dar FAQ link redirected to the homepage, and Wasalt's old business URL also redirected to its homepage. Neither redirect was counted as a new information page. Wasalt blog robots returned HTTP 200; the default group disallows `/wp-admin/`, while the named GPTBot group disallows crawling. This supervised user-requested browser workflow did not use or impersonate GPTBot. No WordPress administration routes were visited.

Publisher content can conflict: the Wasalt floor listing's title area and description cover differing measurements/prices; Dar's home/investor market counts also differ. The chatbot prompt instructs reporting source conflicts and treating prices, returns, legal, tax and visa claims as dated publisher information, not verified advice. Do not present these captures as current offers or certified facts.

## Reproduction

Raw captures: ignored `data/private/expanded-browser/captures.json`. Reviewed corpus, review report, full-precision index, compact index and bundle are in the same directory. Previous snapshots remain available locally.

```powershell
.venv\Scripts\python -m scripts.merge_reviewed_captures --base data/private/combined/corpus.jsonl --captures data/private/expanded-browser/captures.json --permission data/private/permission.json --output data/private/expanded-browser/corpus.jsonl
.venv\Scripts\python -m scripts.build_index --corpus data/private/expanded-browser/corpus.jsonl --output data/private/expanded-browser/index-float16.npz --storage-dtype float16
.venv\Scripts\python -m scripts.package_corpus --corpus data/private/expanded-browser/corpus.jsonl --index data/private/expanded-browser/index-float16.npz --output data/private/expanded-browser/deployment-bundle.json --compress-text
```

Compressed text restores exactly as UTF-8; startup enforces a 2 MB decompression bound. Float16 vectors are converted to float32 for scoring. Across 22 focused retrieval queries, compact and full-precision indices returned exactly the same ordered results; maximum vector rounding error was 0.0000604. The package is 429,582 bytes and fits with the original rollback secret file under Render's 1 MB aggregate limit. Corpus revision: `1f08fa38af30`.

## Verification and limits

Twenty of 22 queries retrieved the exact expected URL. The other two retrieved alternative Dar pages containing the requested CEO and stock-exchange facts, confirmed by inspecting the passages. This is evidence retrieval verification, not model-answer scoring. No OpenRouter calls were made. Full 40-question generated-answer evaluation, current provider availability, and sustained hosted memory measurements remain pending.

Remaining scope: all historical news/blog archives, every property/project listing, PDFs, account-only functions, auction transactions, and full Arabic counterparts are not collected. Riyadh alone displayed over 26,000 listing results; the app intentionally uses a small dated sample. Continue expansions by coverage gaps and resource limits rather than claiming an exhaustive mirror.


Deployment verification: public readiness returned exact revision `1f08fa38af30` and both companies; the source endpoint returned 68 pages / 52 English / 16 Arabic. Local profile: 2.317 seconds initialization, 10.01 ms median / 11.71 ms maximum retrieval across the profiler's 20 requests, 242.9 MiB process RSS. These are local measurements, not a hosted latency or RAM guarantee. CI passed for `07d5df6`; all 40 backend tests passed. Zero OpenRouter calls in this expansion.
