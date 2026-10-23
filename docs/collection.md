# Collection and permissions

Publicly readable does not automatically mean approved for extraction, provider processing or republication. Wasalt's [published terms](https://wasalt.sa/en/s/terms-of-use) explicitly restrict these activities. The assignment asks that access restrictions be respected. The application started with original fictional fixtures. On 23 October 2026 the user explicitly instructed proceeding with Dar Global for the company-issued assessment. A private Dar-only snapshot was collected on that stated authorization basis; Wasalt remains excluded. No company corpus is committed to the repository. Dar terms also reserve copying/transmission rights; this assessment basis is recorded as an assumption, not as a separately issued website licence.

Read-only policy checks on 23 October 2026: both robots.txt endpoints returned HTTP 200. Dar Global disallows its sitemap index, several tracking/query patterns and malformed paths; its root, blog, press and project paths have explicit allow entries. Wasalt's default group allows ordinary paths but disallows `/search` and `/cdn-cgi/rum`; the collector identifies itself honestly and does not impersonate one of the separately named AI bots. The referenced `/llms.txt` returned an HTTP 403 access challenge and was not bypassed. These robots rules do not resolve the separate published reuse restrictions.

## Clarification email draft

Reply in the existing recruitment thread. The owner sent the Wasalt clarification in the recruitment thread. The text below is retained as a draft/reference; this project does not send emails automatically.

> Dear Nada,
>
> Thank you for sharing the assignment. I have reviewed the requirements and am preparing the implementation.
>
> One clarification: Wasalt's published terms restrict content extraction and reuse. Could you please confirm permission to use a limited public-content snapshot for this assessment, including processing relevant excerpts through OpenRouter and displaying cited chatbot answers, or share an approved dataset?
>
> Best regards,
> Md. Owais

## Approved collection procedure

1. Record the actual authorization basis and its scope for each selected website, including third-party model processing and public generated answers. Do not invent a separate permission grant. The current Dar record uses the company-issued assessment and explicit user instruction; Wasalt is still awaiting clarification. Review applicable terms; record the reviewed URL and scope in the private permission record.
2. Copy `data/permission.example.json` into `data/private/permission.json`. Populate the reference, expiry and approved directory prefixes. Do not invent permission or simply change flags to bypass the gate.
3. Run `python -m scripts.collect --permission data/private/permission.json --max-pages 30`.
4. The collector checks robots.txt before pages (404 means no published rules; other failures stop that host), uses an identifying user agent, requests sequentially with at least two seconds between requests, checks redirects, and caches fetched HTML privately. It stops at denials and does not automate CAPTCHA, login or anti-bot bypasses. Caches are reused only after permission and robots checks; clear the task-specific cache manually when an intentional new snapshot is required.
5. Review `data/private/collection-report.json`, titles, language detection, extracted text and timestamps. The script targets 30 pages with a balanced company cap, but blocked or sparse pages can reduce coverage. By default a corpus is not written unless both websites have content. `--companies dar` validates only Dar authorization, refuses links to Wasalt and writes a separate `data/private/dar/corpus.jsonl`, so partial progress cannot replace the final two-company corpus.
6. Do not include owner/broker contact details or personal information. The collector excludes forms and navigation, but a human must review the text and remove any personal details remaining in page bodies before indexing.
7. Ensure English and Arabic coverage. The collector can read server-rendered HTML; it deliberately does not bypass JavaScript-dependent access restrictions. Request an approved dataset if necessary.
8. Build the index and deployment bundle; the fingerprint prevents accidentally serving an index from another corpus. Keep all real content in ignored `data/private/` and hosting secret storage.

The manifest contains only known seed URLs. Automatic link discovery stays within the approved prefixes. The tool never searches third-party websites or uses search engine text as a substitute for restricted content.

For a company-provided dataset, map approved records into the same JSONL schema demonstrated by the fixtures, set `synthetic` to false, attach `permission_reference`, calculate UTF-8 SHA-256 `content_hash`, then run `load_corpus`/indexing. Do not mark fixture facts as real company information.

## Dar only assessment snapshot

On 23 October 2026 the collector obtained 30 readable pages, then removed three duplicate product-category routes. The reviewed corpus contains 27 URLs: 23 English and four Arabic. Root, Arabic root, investor and Arabic investor/project landing paths returned insufficient readable HTML and were skipped. No browser/anti-bot bypass was used. See [source coverage](dar-source-coverage.md) for the retained URLs, limitations and review details.

```powershell
# Populate the private authorization record from the actual assessment scope first.
.venv\Scripts\python -m scripts.collect --permission data/private/permission.json --companies dar --max-pages 30
# Review and deduplicate before building. These commands do not fetch Wasalt.
.venv\Scripts\python -m scripts.build_index --corpus data/private/dar/corpus.jsonl --output data/private/dar/index.npz
.venv\Scripts\python -m scripts.package_corpus --corpus data/private/dar/corpus.jsonl --index data/private/dar/index.npz --output data/private/dar/deployment-bundle.json
```

The collected corpus and raw HTML are private ignored artifacts. The current review is agent-assisted: titles/languages, duplicate routes, email/phone-pattern scan and sampled project/FAQ text were checked. It is not a human certification of every source claim. Marketing claims about returns, visas, taxes, future handovers and sold-out status can be stale or contradictory; they must not be treated as live facts or verified professional advice.

If clarification is needed for Dar as well, a follow-up draft is: “Could you also confirm that the assessment authorizes a limited Dar Global snapshot, including relevant excerpt processing through OpenRouter and public cited answers? I noticed its terms also reserve copying and transmission rights.” This draft has not been sent by the agent.

## Expanded mapping and collection on 24 October 2026

The robots-allowed sitemap listed 477 URLs. `data/dar-expansion-manifest.json` records 176 planned candidates spanning company/FAQ entry points, projects, Arabic counterparts, selected news/blog posts and partners. This is a bounded coverage plan rather than an instruction to copy all historical material.

The expansion encountered widespread Incapsula access challenges. The audited continuation retained 12 readable pages and recorded 59 challenged URLs before it was stopped. Three readable URLs refreshed prior sources; nine were additions. The interrupted first pass predates checkpoint logging, so it is not represented as a complete audited attempt count. The previous 27-page corpus was preserved, then merged by URL with the readable cached additions and cleaned offline. The result is 36 source pages (27 English/nine Arabic), with 151 passages. See the updated [coverage inventory](dar-source-coverage.md) for gaps.

The collector now supports a separate private `--output-dir`, `--manifest`, up to 200 retained pages, bounded `--max-visits`, and `--seed-only`. It excludes tracking queries, fragments, contact/payment/login routes and PDF assets from discovery. Report checkpoints survive interruption, cached pages keep their fetch times, and five consecutive access challenges stop the run without automatic retry. These changes do not authorize bypasses or imply that all sitemap pages were collected.

```powershell
# Only run under normal permitted access and the recorded assessment scope.
.venv\Scripts\python -m scripts.collect --permission data/private/permission.json --companies dar --manifest data/dar-expansion-manifest.json --max-pages 140 --max-visits 220 --output-dir data/private/dar-expanded
# A stopped run can legitimately have no corpus; retain its report and previous snapshot.
# Review/merge readable source records privately, preferring the newer record for each URL.
.venv\Scripts\python -m scripts.curate_corpus --input data/private/dar-expanded/merged-corpus.jsonl --output data/private/dar-expanded/curated-corpus.jsonl
.venv\Scripts\python -m scripts.build_index --corpus data/private/dar-expanded/curated-corpus.jsonl --output data/private/dar-expanded/index.npz
.venv\Scripts\python -m scripts.package_corpus --corpus data/private/dar-expanded/curated-corpus.jsonl --index data/private/dar-expanded/index.npz --output data/private/dar-expanded/deployment-bundle.json
```

Curation normalizes whitespace, deduplicates exact content, checks whether Arabic-labelled bodies contain Arabic, removes email/international-phone patterns, updates hashes and writes a review trail. No contacts required redaction in this batch. Agent review sampled every added page's location, property type and amenities/FAQ text; publisher claims are not independently verified. Full company, FAQ landing, news and blog coverage remains blocked, as do Wasalt and the final two-company evaluation.
