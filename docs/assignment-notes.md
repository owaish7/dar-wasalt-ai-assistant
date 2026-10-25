# Assignment handover

## What was built

Atlas is a React/TypeScript chatbot with a FastAPI backend. It supports English and Arabic with RTL layout, follow-up questions, streaming answers, inline citation links and collapsed per-answer Sources. The sidebar contains no source library.

The Word assignment asks for relevant public information from Dar Global and Wasalt, grounded answers, free OpenRouter inference, Docker, a live URL, source code, setup/deployment instructions and an explanation of technical decisions. It does not require an exhaustive copy of either website. The bilingual 40-case evaluation and 90% target were additional project goals.

## Collection and coverage

The private snapshot contains 68 reviewed pages: 55 Dar Global and 13 Wasalt; 52 English and 16 Arabic pages, split into 310 passages. It covers selected projects, company information, services/FAQs, news, property guides and three dated Wasalt listing examples. The full metadata inventory is in `data/reviewed-source-manifest.json`.

There is one shared HTTP collector with company-specific URL manifests, not two unrelated scraper implementations. It checks allowed hosts, recorded scope, robots rules and redirects; rate-limits requests, caches successful captures and stops on repeated access challenges. When HTTP requests were denied, ordinary Chrome navigation could display some public pages. Those pages and expanded FAQs were captured from visible DOM content and passed through the browser import/merge scripts. No CAPTCHA, proxy or access-control bypass was used.

Cleaning removes navigation, unrelated project recommendation cards, duplicated text and contact details. Each record retains URL, title, actual language, collection timestamp and SHA-256 hash. The permission reference records the user's assumed assessment authorization; it does not assert a separately granted website licence. Collected text and index bundles stay outside public Git.

This is a bounded snapshot, not all pages, all listings or live inventory. Conflicting publisher facts remain conflicts; prices, completion dates and availability are dated claims. See `expanded-source-coverage.md` for details.

## How an answer is produced

1. React sends the current question, bounded recent history and selected language.
2. FastAPI validates input and applies rate/concurrency limits. Common off-topic requests and ambiguous project/price questions are handled without inference.
3. BM25 keyword retrieval and quantised multilingual E5-small embeddings find relevant passages. Reciprocal-rank fusion combines results, with at most six passages and two per page. An explicit Arabic Marriott name mapping improves recall for its English-only page.
4. The model receives only these passages as evidence, plus recent context. Instructions require concise professional language, source numbers, clarification where needed and abstention without evidence.
5. SSE streams a clearly labelled draft. The backend checks final citation numbers against retrieved passages, rejects invented URLs, and replaces the draft with a validated final result or an honest error. Numeric references become safe clickable links, while source cards stay collapsed.

No website crawl or document embedding occurs during chat. The corpus, index and query embedding model load once at startup. No external vector database or model fine-tuning is needed for this dataset.

## Models and hosting

The primary is `cohere/north-mini-code:free`, with `poolside/laguna-s-2.1:free` as a free-only fallback. The server checks zero catalog pricing before generation and records the actual returned model. Earlier `openrouter/free` experiments encountered output truncation from routed reasoning models; the current bounded configuration was selected from observed tests. Provider quotas and availability remain variable. There is no paid fallback.

Render hosts the React build on a free static site and the backend on a free Docker web service. The multi-stage image runs as a non-root user, uses locked dependencies and packages the quantised query model. A private compressed secret file restores the real corpus/index on each startup. Exact-origin CORS connects the frontend. Render was selected for straightforward Docker hosting and a single dashboard; Vercel was not benchmarked as an alternative.

The free backend sleeps when idle. The UI shows a waking status and retries readiness for up to 90 seconds during real use. No artificial keep-alive traffic is configured. One worker, one embedding thread and bounded chat concurrency control memory.

## Security and ownership

Credentials remain server-side. Git and Docker exclude `.env`, recruitment correspondence, assignment attachments and private corpus artifacts. Requests are bounded by message/history/body limits, rate limits, concurrency and timeouts. Website passages and history are treated as untrusted. React renders model text without HTML execution; citation links use exact HTTPS host allowlists. Quota exhaustion, missing keys and interrupted streams cannot silently produce a completed answer.

AI assisted with scaffolding, UI, collection scripts, retrieval, integration, tests and documentation. Review covered source attribution, related-project contamination, secret handling, URL validation, free-only pricing, stream completion, model control responses and Arabic retrieval. Automated citation validity does not establish factual entailment; generated claims must still be reviewed against passages. No company brand guide was supplied, so the tone is concise, courteous and professional, without claiming official company representation.

## Evidence and delivery

See `final-review.md` for the latest requirement matrix and actual evaluation outcome, and `verification.md` for the historical test record. CI performs clean-checkout backend tests, frontend tests/build/audit and a Docker build with readiness and restart checks under a 512 MiB container limit. Local process memory measurements are not sustained Render memory measurements.

- Live app: https://atlas-property-chat-owaish7.onrender.com/
- GitHub: https://github.com/owaish7/dar-wasalt-ai-assistant
- Setup: `README.md`; deployment: `docs/deployment.md`
- Submission email: `docs/submission.md` (prepared, not sent)
