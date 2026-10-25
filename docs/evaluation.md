# Bilingual factual evaluation

`evaluation/cases.json` contains 40 scenarios: 20 English and 20 Arabic. They cover both companies, cross-language questions, comparisons, follow-ups, unknown facts, live inventory, private information, instructions to fabricate citations and requests for secrets. Expected facts and candidate source URLs are filled against the reviewed 68-source snapshot. The current set also includes explicit ambiguity and off-topic scenarios. Candidate URLs are alternatives unless both companies are required; passing requires actual claim support, not merely a link match.

1. Review each case against the approved corpus. Add expected facts and supporting source URLs, and set `review_status` to `ready`. Replace broad questions with specific project/service names present in the corpus. For follow-ups, include the actual preceding user/assistant exchange. Do not mark a question answerable unless the collected sources support it.
2. Configure the server's OpenRouter key and confirm `synthetic=false` through `/healthz`.
3. Run `python -m scripts.evaluate --url https://YOUR-API.onrender.com --limit 40 --allow-inference`. This consumes free provider quota and deliberately spaces requests. Provider quotas may still prevent completing all 40 in one day; record that honestly and resume later.
4. Review the private `artifacts/evaluation-results.json`. For each completed response check correctness, support for every material claim, citation mapping, response language, company separation, dated information and appropriate abstention. Arabic needs a competent human review.
5. Count a case as correct only when every material claim is correct and supported. The target is at least 90% correct supported answers among answerable questions. Require valid displayed citation URLs/numbers for every cited response and appropriate abstention on all designated unsupported/adversarial cases. Report numerator, denominator and failures for each language separately.
6. A provider error, timeout, missing key or unfinished stream is an unavailable answer, not an appropriate factual abstention. Include availability failures in the report; never omit them to inflate accuracy.
7. Record actual returned models, first-token/full-answer durations and the corpus snapshot version. Do not transfer a fixture benchmark or mocked-provider result to the real-content evaluation.

For development-only fixture inference, add `--allow-fixtures`. The output remains explicitly synthetic and cannot satisfy final assignment acceptance.

Reproduce the eight focused fixture smoke scenarios with `python -m scripts.evaluate --cases evaluation/fixture-smoke-cases.json --limit 8 --allow-fixtures --allow-inference --url https://atlas-property-api-owaish7.onrender.com`. The runner stops on a quota/capacity error and preserves the results collected so far.

## Quota-free retrieval check

Run `python -m scripts.evaluate_retrieval --corpus data/private/expanded-browser/corpus.jsonl --index data/private/expanded-browser/index-float16.npz`. This records all 40 retrieval/routing cases without generation. It is a source-recall diagnostic, not an answer-accuracy score.
