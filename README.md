# Atlas · Dar Global and Wasalt assistant

A bilingual React/FastAPI chatbot with hybrid passage retrieval, cited answers, free-only OpenRouter inference, and Docker deployment.

**Current content status: synthetic fixtures only.** The example project, city, and services in the fixtures are fictional. They are not facts about either company. Collection of real website information is gated on permission and robots/terms checks. This is an engineering preview, not yet a completed source-grounded assignment submission.

## Run locally

Requires Python 3.12 and Node 22.14 or later within Node 22.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
# Edit .env and set OPENROUTER_API_KEY locally. Never commit it.
.venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. Default local retrieval is explicitly labelled `lexical` in `/healthz`, making development possible without downloading an embedding model. Missing API credentials produce an honest configuration error; there are no hardcoded or simulated model answers.

For multilingual hybrid retrieval:

```powershell
.venv\Scripts\python -m scripts.build_index
# Set RETRIEVAL_MODE=hybrid in .env, then restart the API.
```

The build command downloads the public int8 multilingual E5-small ONNX model at a pinned revision. Runtime loading is offline. Direct ONNX Runtime inference avoids unnecessary image-processing dependencies. Document embeddings are precomputed; only the query is embedded during a chat request.

On macOS/Linux, substitute `.venv/bin/python` for `.venv\Scripts\python`, and `cp .env.example .env` for `Copy-Item`.

## Docker

```sh
docker build -t atlas-assistant .
docker run --rm -p 8000:8000 --env-file .env -e RETRIEVAL_MODE=hybrid -e EMBEDDING_CACHE=/opt/models atlas-assistant
```

The image runs the API as a non-root user, packages the model and fixture index during the build, and exposes `/healthz`. It does not contain credentials or privately collected material. The React application is built and hosted separately; configure `VITE_API_URL` to the API origin and `ALLOWED_ORIGINS` to the frontend's exact origin.

## Architecture

```text
React UI (English / Arabic, RTL)
  → FastAPI validation and request/concurrency limits
  → recent user context + BM25 / int8 multilingual E5 retrieval
  → up to six source passages, each assigned a citation number
  → free OpenRouter inference, streamed as SSE
  → citation validation and authoritative final answer + source cards
```

For a small corpus, NumPy vectors and in-process BM25 avoid an external database. Reciprocal-rank fusion combines semantic and lexical results, and results are limited to two passages per source page. Multilingual embeddings support asking in Arabic about English documents and vice versa. The application does not fine-tune a model or crawl during user requests.

`openrouter/free` is the default. It chooses among free models, so model identity and latency can vary. The actual returned model is recorded in final responses and metadata-only logs. Specific overrides must have a `:free` ID and zero catalog prompt/completion pricing. There is no paid fallback and no provider-side paid plugin configuration.

Citation validation checks that references map to retrieved passages and forbids model-generated external URLs. It does **not** prove every sentence is entailed by the passages. Human factual evaluation remains necessary, especially for Arabic, source conflicts, and prompt injection.

## API

- `GET /healthz`: readiness, retrieval mode, synthetic-data flag, inference configuration status. It does not call the inference provider.
- `GET /api/sources`: source titles, URLs, languages, timestamps and synthetic flags; never the corpus text.
- `POST /api/chat`: `{ "message": "…", "history": [{"role":"user","content":"…"}], "language": "en" }`; `language` is `en` or `ar`.
- Chat SSE events: `meta` (request ID, retrieval duration, fixture flag), `delta` (unverified draft text), `done` (authoritative answer, validated sources, model, timings), or `error` (safe error code/message). A connection without `done` is incomplete. Clients must discard partial text after errors.
- Current message maximum: 2,000 characters; up to eight history messages, each ≤2,000 characters and ≤8,000 history characters in total; maximum raw request body 48 KB.

## Data collection

Read [collection and permissions](docs/collection.md) before any real collection. The public seed manifest is a list of candidate URLs, not evidence of permission. In particular, [Wasalt's terms](https://wasalt.sa/en/s/terms-of-use) restrict extraction/reuse. No live collection has been performed by this project yet.

After permission:

```powershell
# Fill an actual permission record in data/private/permission.json.
.venv\Scripts\python -m scripts.collect --permission data/private/permission.json --max-pages 30
.venv\Scripts\python -m scripts.build_index --corpus data/private/corpus.jsonl --output data/private/index.npz
.venv\Scripts\python -m scripts.package_corpus
```

Review coverage for both companies and both languages, content quality, collection reports, and dated information before enabling real data. Upload the private deployment bundle only to hosting secret storage. See [deployment instructions](docs/deployment.md).

## Verification

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
npm --prefix frontend test
npm --prefix frontend run build
.venv\Scripts\python -m scripts.profile_retrieval
```

CI also builds the Docker image, checks container readiness/restart, and reports container memory. See [verification status](docs/verification.md) and the [40-case evaluation procedure](docs/evaluation.md). Neither unit tests with mocked inference nor fixture retrieval establishes the 90% real-answer acceptance target.

## Security and limitations

- API keys remain server-side. `.env`, private datasets, bundles and collection caches are ignored by Git and Docker.
- Source collection is restricted to the two HTTPS domains; redirects are validated, private/local destinations are refused, and robots failures are handled conservatively.
- The server bounds input, context, output, retries, total generation time and concurrency. The default request limit is eight per minute per observed client address.
- Forwarded client addresses are trusted only when configured by the ASGI server. Do not indiscriminately trust browser-supplied `X-Forwarded-For`. Behind an untrusted/shared proxy, rate limits may be shared; this intentionally errs toward limiting abuse.
- Answers render as React text, with no HTML or generated Markdown execution. Only validated source cards create external links. Streaming drafts are labelled until validation completes.
- Request logs contain IDs, outcomes, model names and durations, not user messages, source text or provider errors. The process does not persist chat history.
- Free Render backends sleep after 15 minutes of inactivity and can take approximately one minute to wake. The static UI stays independently available. There are no synthetic keep-alive requests.
- Free OpenRouter quotas/capacity can interrupt service. The app reports errors and does not silently switch to a paid model.
- This is a single-instance assessment demo, with no authentication, persistent conversations, live inventory, payment/booking functionality or production SLA.

## AI assistance and independent ownership

AI assisted with scaffolding, UI, retrieval, adapter code, tests, and documentation. Verification includes type checking/build, unit and integration tests, dependency audits, bilingual browser inspection, retrieval profiling, and container CI. [Verification notes](docs/verification.md) distinguish completed checks from pending ones. The author should review and explain the data flow, permission constraints, index/model matching, streaming failure handling and remaining grounding risks before submission.
