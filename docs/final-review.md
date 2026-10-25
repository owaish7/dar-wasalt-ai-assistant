# Submission verification — 25 October 2026

## Requirement checklist

| Assignment requirement | Delivered evidence |
|---|---|
| Relevant public information from both websites | 68 reviewed source pages: 55 Dar Global, 13 Wasalt; 310 passages; public URL manifest, private text/index |
| Grounded chatbot | Hybrid BM25/E5 retrieval, evidence-only prompt, citation validation, unknown-information and scope handling |
| Free OpenRouter model | Server-side free-only model validation, actual model reporting, explicit quota errors; no paid fallback |
| Docker | Multi-stage non-root image; CI build, readiness and restart checks under 512 MiB |
| Live URL | https://atlas-property-chat-owaish7.onrender.com/ |
| Source code and setup | Public main branch, README, locked dependencies, fixtures and deployment instructions |
| Technical explanation | `assignment-notes.md`, collection and deployment documents |
| Security and AI-code verification | Input/body/history limits, exact CORS, bounded concurrency, safe links, server-side credentials, regression tests and CI |

## Final code checks

50 backend tests and nine frontend tests pass locally. The frontend production build passes. GitHub Actions run [40167099250](https://github.com/owaish7/dar-wasalt-ai-assistant/actions/runs/40167099250) passes for runtime commit `f6fea0b`, including Docker readiness/restart and the frontend dependency audit. A clean checkout uses clearly labelled fictional fixtures; the private real corpus is not in public Git.

The source library has been removed from the sidebar. Supporting sources remain collapsed below answers, and numeric citations link directly to supplied sources. Arabic RTL and the 390px mobile layout were checked without horizontal overflow.

## Answer evaluation

The 40-case bilingual baseline completed against runtime `dac3ad9` and corpus revision `1f08fa38af30`. This was real free-model inference, not mocked answers. Completion is not an accuracy score. Review found an Astera/Top-of-the-Astera attribution error, provider process commentary, a wrong Arabic bedroom category, and a repeated answer. Those failures motivated canonical-page retrieval, process-commentary rejection with one bounded rewrite, stricter translation instructions and exact whole-answer de-duplication. Live-inventory questions now receive a direct snapshot limitation without inference.

The quota-free retrieval/routing evaluation found expected source candidates for all 22 answerable questions. That measures source recall, not factual entailment. Eight baseline ambiguity/off-topic cases were routed without inference; the latest release adds two live-inventory routes.

An eight-case follow-up completed: the Arabic bedroom counts and English Astera attribution improved, but two Arabic answers still included process commentary and one Arabic comparison was truncated. Broader commentary detection and a free-backup rewrite were subsequently published in `f6fea0b`; their final hosted retest and deployment confirmation were interrupted and are not claimed as complete. A fresh 40-case accuracy score on the final release is not claimed. The planned 90% quality threshold must not be described as achieved without a fully scored final run. Review was AI-assisted; the candidate should personally inspect examples before presenting the work.

## Practical limits

Coverage is relevant and bounded, not exhaustive or live inventory. Collection records the user's assumed assessment authorization, not a separately issued website licence. Source pages can conflict or contain dated claims. Citation validity cannot prove that every model statement follows from its cited passage.

Free Render sleep and OpenRouter quotas remain limits. The UI polls readiness for up to 90 seconds during use, without artificial keep-alives. Container restart/readiness is verified in CI; a controlled natural-idle wake benchmark and sustained memory profiling on the actual free instance have not been completed. Earlier local retrieval measurements were about 10 ms median and 243 MiB process RSS, not hosted service guarantees.
