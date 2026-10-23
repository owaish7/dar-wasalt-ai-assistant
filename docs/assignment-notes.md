# Technical assignment implementation notes

This note maps the original Word assignment to the implementation and records what is complete, what was tested, and what remains. It is a technical handover for the candidate and reviewer. The Word attachment and recruitment correspondence are not included in the public repository.

The system is built and deployed. The live Dar-only corpus has 36 distinct pages and 151 searchable passages. Wasalt content and the complete two-company evaluation remain pending. This is partial assignment progress, not a claim that all source requirements have been fulfilled.

## Original requirements and current status

| Assignment requirement | Implementation and evidence | Status |
|---|---|---|
| Collect public information from both websites while respecting restrictions | Bounded collector, robots checks, validated redirects, private provenance records; Dar collected for the company-issued assessment on the user-confirmed authorization basis | Dar live; Wasalt pending |
| Build a chatbot grounded in collected content | FastAPI retrieves relevant passages before free-model generation; numbered references are checked against retrieved metadata | Implemented; real Dar checks recorded in verification notes |
| Use a suitable free model through OpenRouter | Cohere North Mini Code free primary, Poolside Laguna free backup; catalog pricing checked and actual model recorded | Implemented and real inference verified |
| Containerise the application with Docker | Multi-stage Dockerfile packages the backend, runtime dependencies and multilingual model, runs as a non-root user | CI build/startup/query/restart checks passed under 512 MiB |
| Deploy and supply a live URL | Separate free Render static frontend and Docker backend | Live; see links below |
| Supply source repository and brief setup/deployment instructions | README, locked dependencies, environment example, deployment notes and GitHub Actions | Published |
| Explain architecture, collection, model, security and AI-code verification | This note and the linked detailed documents | Documented with limitations |

English/Arabic support, a public GitHub repository, free hosting, the 40-question evaluation and a 90% target are our agreed implementation choices. The Word document does not itself specify those languages, a public repository, that question count or that acceptance percentage. It asks for a source repository and evaluates functionality, engineering understanding, robustness, deployability, security awareness and independent ownership.

## Architecture and RAG

React and TypeScript provide the chat interface, English/Arabic selection, RTL layout, streaming state, compact suggestions and expandable sources. FastAPI validates requests and coordinates retrieval and generation. OpenRouter routes the request to a permitted free model; the browser never receives the API key.

Before deployment, cleaned documents are split into windows of 1,000 characters with up to 150 characters of preceding overlap. Each passage retains its URL, title, language, snapshot time and content provenance. Multilingual E5-small int8 embeddings are precomputed and saved with a fingerprint linking the vectors to the exact corpus. The model revision is pinned; loading an incompatible index fails readiness.

During chat, the current question and the last two user messages form the search query. BM25 matches names and keywords; E5 embeddings match meaning across English and Arabic. Reciprocal-rank fusion combines the results, with at most six passages and at most two per source URL. The small corpus uses NumPy and in-process search rather than a paid database.

Related-project recommendation cards are excluded during curation; a real expanded-corpus test exposed location contamination from those cards. The cleaned corpus revision is deployed and verified, but its targeted model retest was blocked by free-provider quota/capacity, so final model accuracy is still pending. The model receives the question, bounded history and numbered source excerpts. It is told that source text and history are untrusted, that claims need citations, and that missing facts require abstention. SSE streams an explicitly unverified draft. The backend validates reference numbers and forbids model-written external links; one bounded rewrite can repair omitted citations. The final event replaces the draft with the validated result or an abstention. Valid reference numbers alone do not prove factual entailment.

## Data collection and authorization basis

`scripts/collect.py` uses HTTPX, BeautifulSoup and Protego. It fetches only allowlisted HTTPS hosts and approved directory prefixes, identifies itself as `AssessmentResearchBot/1.0`, checks robots rules, honors crawl delays, validates redirects, and requests sequentially with at least two seconds between requests. No website crawling or document embedding occurs during chat.

The extractor removes scripts, navigation, forms, headers and footers, then keeps main text with URL, title, language, UTC collection time and SHA-256 hash. Cache, corpus, reports, index and deployment bundle stay under ignored private storage. No raw website corpus is published in GitHub or offered through an API download endpoint.

Dar terms also reserve copying and transmission rights. The recorded basis for the current limited snapshot is the company-issued assessment requesting Dar content and the user's explicit instruction to proceed on that basis. This is an authorization assumption for the assessment, not a claim that the website issued a separate licence. Wasalt stays excluded while its clarification is pending. Single-company collection writes its own directory, so it can progress without overwriting the final combined corpus.

The initial snapshot retained 27 pages after removing duplicate routes. The 24 October expansion mapped 477 sitemap URLs and selected 176 candidates. Its audited continuation obtained 12 readable pages and recorded 59 access challenges; nine of those pages were additions. Merging them with the preserved snapshot produced 36 pages, including 27 English and nine Arabic pages, indexed into 151 passages. Company, news and blog coverage remains incomplete because of access challenges. See [coverage and retained URLs](dar-source-coverage.md) and [collection procedure](collection.md). Prices, availability, handovers, market statistics and legal/visa statements are dated publisher claims, not verified current advice.

## Model choice and free deployment

The current default is `cohere/north-mini-code:free`, with `poolside/laguna-s-2.1:free` as backup. An initial `openrouter/free` trial routed some requests to reasoning models that exhausted their output budget before answering. A Gemma trial encountered capacity/quota errors. The current small free-model list, disabled reasoning, 900-token limit and requested answers under 150 words were selected after those observed failures. Provider availability and quotas remain variable; there is no paid fallback.

Render runs the React build as a free static site and FastAPI as a free Docker service. One worker and one concurrent hosted generation bound memory use. The multilingual model and fixture index are packaged during the Docker build; the real corpus and its precomputed index are supplied in a private deployment bundle. Startup restores that bundle from hosting secret storage on each restart.

Render was chosen for the agreed Docker deployment and a single hosting dashboard. Vercel is also technically possible; no comparison test has established that it would make this backend faster. Free Render web services sleep when idle. The frontend displays wake status and polls readiness for up to 90 seconds only during actual use; no artificial keep-alive traffic is configured.

## Security and robustness

- OpenRouter credentials stay server-side; private data, `.env` files, assignment attachment and recruitment correspondence are excluded from Git and Docker context.
- HTTPS source URLs are restricted to the two intended domains. Scope, redirect and robots checks prevent arbitrary crawl targets.
- Input is limited to 2,000 characters, eight history messages and 8,000 total history characters. Extra fields and system-role history are rejected; raw request bodies are capped at 48 KB.
- Exact-origin CORS, per-client rate limits, bounded concurrency, a 55-second generation deadline and bounded output prevent unbounded work.
- Model output is rendered as React text, without executing HTML or Markdown. Source links come from validated metadata; numeric citations, including grouped references, must identify supplied passages.
- Missing credentials, quota errors, timeouts and interrupted streams are visible failures. The UI discards unfinished drafts instead of presenting them as final answers.
- Logs contain operational metadata, not API keys, full prompts, source excerpts or private email content. Source prompt injection remains a model risk despite the instruction boundary.

## AI assistance and verification

AI assisted with application scaffolding, UI, collector, retrieval, model integration, tests and documentation. Review focused on secret handling, host validation, scope/permission gates, free-only inference, streaming completion, citation handling and corpus fingerprints. The candidate should understand these decisions and personally review the final evaluation before submission; AI-generated code is not evidence of correctness by itself.

Local backend checks now pass 38 tests, including the single-company permission scope, partial coverage metadata and a real-content issue where Unicode paragraph separators broke JSONL loading. The frontend production build passes; existing protocol tests and Docker checks run in CI. Prior fixture inference tests exposed output truncation, omitted citations and grouped-citation handling, which were recorded and corrected. See [verification evidence](verification.md) for measured results and remaining checks.

The 40-case two-company evaluation is not complete. An eight-case Dar trial returned supported core facts in all six answerable cases, with one repeated answer and some overly broad references. It refused invented pricing but initially hallucinated Wasalt services with Dar citations; an explicit backend company-coverage guard now rejects recognized unavailable-company questions before retrieval or generation, verified on the live service in English, Arabic and a follow-up. This is not a complete factual-quality score; Wasalt comparisons must remain unavailable until Wasalt content is supplied. The 90% answer-quality target is a future acceptance check, not an achieved score. Mobile visual QA, naturally idle hosted wake timing and sustained hosted memory profiling must also be reported honestly.

## Delivery links and next steps

- [Live frontend](https://atlas-property-chat-owaish7.onrender.com/)
- [Backend readiness](https://atlas-property-api-owaish7.onrender.com/healthz)
- [Source repository](https://github.com/owaish7/dar-wasalt-ai-assistant)
- [Setup](../README.md), [deployment](deployment.md), [evaluation protocol](evaluation.md), [submission draft](submission.md)

Finish by obtaining Wasalt content within the confirmed scope, building a combined corpus, reviewing all 40 expected answers against source snapshots, and recording actual quality/latency results. Send the live URL, repository URL and concise implementation notes only once the submission accurately reflects both companies' coverage.
