# Verification and AI assistance

## Completed local checks

- Backend unit/integration tests: 23 passed. Coverage includes real request validation, bounded body handling, CORS, rate limiting, SSE completion/interruption, missing credentials, citations, metadata privacy, bilingual lexical retrieval/follow-ups, free-only model gating, corpus integrity, permission gating, robots denial/precedence/wildcards/crawl delay and redirect restrictions.
- Frontend protocol tests: 7 passed. Coverage includes UTF-8/Arabic chunks, incomplete streams, quota errors, readiness retry, wake deadline and cancellation.
- TypeScript checking and production frontend build passed.
- Frontend dependency audit after patching the build/test toolchain: zero reported vulnerabilities.
- Python runtime dependency audit: no known vulnerabilities reported after removing the unused image-processing dependency tree and updating the HTTP framework/dotenv packages.
- Local hybrid retrieval profiling over four original synthetic passages after switching from JSON tokenization to equivalent SentencePiece tokenization: approximately 6 ms median, model load approximately 1.3 seconds, process resident memory approximately 241 MB on Windows. Five English/Arabic/mixed-language tokenization examples matched the original tokenizer exactly. These are fixture/local measurements, not hosted performance claims.
- GitHub Actions passed backend/frontend tests and production build on Linux after correcting an initial free-pricing-cache bug exposed by low system uptime. Initial Docker idle memory was approximately 471 MiB, but that version exceeded Render's 512 MiB peak-startup limit. After the SentencePiece fix, Docker build, readiness, English/Arabic query checks and restart passed under an enforced 512 MiB limit; idle memory after restart was approximately 237 MiB.
- Both Render services deployed successfully on free hosting. The hosted backend returned HTTP 200 for readiness and four-source metadata, with the expected exact frontend CORS origin. A hosted Arabic query retrieved passages in 9 ms and honestly returned `not_configured` because the API key is not present.
- English and Arabic desktop UI/RTL layout and fixture notices were inspected in Chrome. A mobile viewport override did not take effect through the available browser tooling, so mobile visual QA is not claimed.

## Checks that require external access or approved content

- The API key was configured directly by the owner in Render. An initial eight-case real-inference trial through `openrouter/free` produced four completed responses and four token-limit failures before answer text. Completed answers included a correct Arabic follow-up, English/Arabic live-price abstention and resistance to invented-price/citation instructions. The default was changed to a pinned free non-reasoning model; its follow-up verification is recorded separately below once complete.
- Docker checks run in GitHub Actions because Docker is not installed on the local machine. Query-time profiling on the free host remains necessary.
- The hosted UI/API are reachable. Real idle-sleep/wake timing, real inference and sustained query-time memory profiling remain pending. Automated frontend tests cover wake polling/deadlines/cancellation but do not replace a naturally idle hosted test.
- A 40-case real-content assessment and the 90% answer-quality acceptance target require approved content from both websites and human review. No accuracy result is claimed yet.
- Prompt injection unit tests check prompt structure and isolation; they do not prove that every free model resists injection. The evaluation suite includes adversarial questions for actual model testing.

## Review performed and remaining limitations

Generated code was inspected for credential handling, source URL validation, collection permission gates, paid fallbacks, request limits, SSE failure handling and React output rendering. Factual correctness requires checking statements against excerpts; valid citation numbers alone cannot establish entailment. A malicious source can still influence model text despite the instruction boundary, so human evaluation and conservative abstention matter.

AI assistance contributed application scaffolding, UI components/styles, retrieval code, OpenRouter integration, collector, tests and documentation. The final author is responsible for reviewing these components and understanding the implementation. Do not claim a test, deployment, permission or performance result until it has actually been observed and recorded.
