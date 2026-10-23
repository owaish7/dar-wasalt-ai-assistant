# Verification and AI assistance

## Completed local checks

- Backend unit/integration tests: 22 passed. Coverage includes real request validation, bounded body handling, CORS, rate limiting, SSE completion/interruption, missing credentials, citations, metadata privacy, bilingual lexical retrieval/follow-ups, free-only model gating, corpus integrity, permission gating, robots denial and redirect restrictions.
- Frontend protocol tests: 7 passed. Coverage includes UTF-8/Arabic chunks, incomplete streams, quota errors, readiness retry, wake deadline and cancellation.
- TypeScript checking and production frontend build passed.
- Frontend dependency audit after patching the build/test toolchain: zero reported vulnerabilities.
- Python runtime dependency audit: no known vulnerabilities reported after removing the unused image-processing dependency tree and updating the HTTP framework/dotenv packages.
- Local hybrid retrieval profiling over four original synthetic passages with weight prepacking disabled: approximately 7 ms median, model load approximately 1.9 seconds, process resident memory approximately 451 MB on Windows. These are fixture/local measurements, not hosted performance claims.
- GitHub Actions passed backend/frontend tests and production build on Linux after correcting an initial free-pricing-cache bug exposed by low system uptime. Docker build, container readiness and restart checks passed. Initial Docker idle memory was approximately 471 MiB; actual Render query-time memory still needs verification.

## Checks that require external access or approved content

- Real OpenRouter inference and observed first-token/full-answer latency require a configured API key.
- Docker checks run in GitHub Actions because Docker is not installed on the local machine. Query-time profiling on the free host remains necessary.
- Hosted UI/API, free-tier cold-start and memory checks require successful deployment.
- A 40-case real-content assessment and the 90% answer-quality acceptance target require approved content from both websites and human review. No accuracy result is claimed yet.
- Prompt injection unit tests check prompt structure and isolation; they do not prove that every free model resists injection. The evaluation suite includes adversarial questions for actual model testing.

## Review performed and remaining limitations

Generated code was inspected for credential handling, source URL validation, collection permission gates, paid fallbacks, request limits, SSE failure handling and React output rendering. Factual correctness requires checking statements against excerpts; valid citation numbers alone cannot establish entailment. A malicious source can still influence model text despite the instruction boundary, so human evaluation and conservative abstention matter.

AI assistance contributed application scaffolding, UI components/styles, retrieval code, OpenRouter integration, collector, tests and documentation. The final author is responsible for reviewing these components and understanding the implementation. Do not claim a test, deployment, permission or performance result until it has actually been observed and recorded.
