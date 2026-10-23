# Collection and permissions

Publicly readable does not automatically mean approved for extraction, provider processing or republication. Wasalt's [published terms](https://wasalt.sa/en/s/terms-of-use) explicitly restrict these activities. The assignment asks that access restrictions be respected. The application therefore starts with original fictional fixtures; no company content has been copied into the repository.

Read-only policy checks on 23 October 2026: both robots.txt endpoints returned HTTP 200. Dar Global disallows its sitemap index, several tracking/query patterns and malformed paths; its root, blog, press and project paths have explicit allow entries. Wasalt's default group allows ordinary paths but disallows `/search` and `/cdn-cgi/rum`; the collector identifies itself honestly and does not impersonate one of the separately named AI bots. The referenced `/llms.txt` returned an HTTP 403 access challenge and was not bypassed. These robots rules do not resolve the separate published reuse restrictions.

## Clarification email draft

Reply in the existing recruitment thread. This is a draft only; it has not been sent.

> Dear Nada,
>
> Thank you for sharing the assignment. I have reviewed the requirements and am preparing the implementation.
>
> One clarification: Wasalt's published terms restrict content extraction and reuse. Could you please confirm permission to use a limited public-content snapshot for this assessment, including processing relevant excerpts through OpenRouter and displaying cited chatbot answers, or share an approved dataset?
>
> Best regards,
> Md. Owais

## Approved collection procedure

1. Obtain a permission reference for each website, including permission for third-party model processing and public generated answers. Review applicable terms; record the reviewed URL and scope in the private permission record.
2. Copy `data/permission.example.json` into `data/private/permission.json`. Populate the reference, expiry and approved directory prefixes. Do not invent permission or simply change flags to bypass the gate.
3. Run `python -m scripts.collect --permission data/private/permission.json --max-pages 30`.
4. The collector checks robots.txt before pages (404 means no published rules; other failures stop that host), uses an identifying user agent, requests sequentially with at least two seconds between requests, checks redirects, and caches fetched HTML privately. It stops at denials and does not automate CAPTCHA, login or anti-bot bypasses. Caches are reused only after permission and robots checks; clear the task-specific cache manually when an intentional new snapshot is required.
5. Review `data/private/collection-report.json`, titles, language detection, extracted text and timestamps. The script targets 30 pages with a balanced company cap, but blocked or sparse pages can reduce coverage. A corpus is not written unless both websites have content.
6. Do not include owner/broker contact details or personal information. The collector excludes forms and navigation, but a human must review the text and remove any personal details remaining in page bodies before indexing.
7. Ensure English and Arabic coverage. The collector can read server-rendered HTML; it deliberately does not bypass JavaScript-dependent access restrictions. Request an approved dataset if necessary.
8. Build the index and deployment bundle; the fingerprint prevents accidentally serving an index from another corpus. Keep all real content in ignored `data/private/` and hosting secret storage.

The manifest contains only known seed URLs. Automatic link discovery stays within the approved prefixes. The tool never searches third-party websites or uses search engine text as a substitute for restricted content.

For a company-provided dataset, map approved records into the same JSONL schema demonstrated by the fixtures, set `synthetic` to false, attach `permission_reference`, calculate UTF-8 SHA-256 `content_hash`, then run `load_corpus`/indexing. Do not mark fixture facts as real company information.
