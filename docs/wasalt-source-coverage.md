# Wasalt collection status — 24 October 2026

**4 browser-captured Wasalt source pages: two English and two Arabic.** The initial direct HTTP attempt returned 403 on all 14 candidates. Subsequent ordinary Chrome navigation loaded the homepage and corporate pages without a challenge or authentication. Those visible pages were captured and reviewed; no CAPTCHA, proxy, spoofed identity or challenge bypass was used.

The user explicitly instructed proceeding on an assumed assessment authorization basis. That assumption is recorded privately; it is not represented as an independently granted website licence. Access restrictions still apply.

## Discovery and scope

- `https://wasalt.sa/robots.txt` returned HTTP 200. Its default group allows ordinary paths and disallows `/search` and `/cdn-cgi/rum`.
- The published English and Arabic static sitemaps at `https://cdn.wasalt.sa/sitemap/static_sitemap_en_sa.xml.gz` and `https://cdn.wasalt.sa/sitemap/static_sitemap_ar_sa.xml.gz` were readable. Each listed nine routes, including policy pages.
- `https://wasalt.sa/llms.txt` returned a Cloudflare challenge and was left alone.
- The [candidate manifest](../data/wasalt-manifest.json) selects English/Arabic home, corporate, business, masterplan, advertising, auction and e-wallet information pages. The Arabic homepage is `/`, not `/ar`.
- Private account data, user profiles, contact information, search routes and bulk individual listings were excluded. This is a relevant-information collection plan, not a claim to capture every changing listing.

## Initial HTTP outcome

The collector used `AssessmentResearchBot/1.0`, sequential requests with a minimum two-second delay, robots checks and an allowlist. Every selected HTML page returned HTTP 403. Private `data/private/wasalt/collection-report.json` and `crawl-summary.json` record the outcome. No corpus, embeddings or deployment bundle were produced.

The web reader separately displayed some public pages during discovery; those results were not substituted for the blocked scrape or counted as retained sources. No challenge was solved or bypassed, and no alternative identity or proxy was used.

The attempt exposed a stopping-rule gap: HTTP errors were logged but did not increment the repeated-challenge counter. The collector now classifies HTTP 401, 403 and 429 as access denials, which count toward its existing five-consecutive-denial stop condition. Mocked tests cover classification, absence of cached denied content, and stopping/checkpoint behavior. No live recrawl was made just to test this fix.

## Browser collection and integration

The retained URLs are https://wasalt.sa/en, https://wasalt.sa/, https://wasalt.sa/en/corporate and https://wasalt.sa/corporate. FAQ accordions were explicitly expanded. Captures preserve the visible text, URL, language and UTC capture timestamp in ignored `data/private/wasalt-browser/browser-captures.json`.

The reproducible importer `scripts/import_browser_capture.py` trims navigation/footer/contact sections and icon glyphs and removes the illustrative “46 Members” team UI text, which is not an actual company headcount. Its exact output was compared with the reviewed corpus. Wasalt contributes 14 passages; combined with 36 Dar pages, the bundle contains 40 pages and 165 passages (29 English/11 Arabic source pages). Revision: `09bbdc97b456`. Bundle: 503,395 bytes, under the aggregate Render limit when retaining the original approximately 369 KB rollback file.

Coverage: platform/services, listing steps, login/OTP, auctions overview, Matchmaker, Wasalt Business CRM tools, company milestones and public board roles. These are dated publisher claims, not independently verified facts. No individual property inventory, live availability, detailed auction rules, complete blog, masterplan dataset or every sitemap page is claimed.

Twelve local hybrid-retrieval checks (English/Arabic Wasalt services plus Dar regressions) returned the expected company as the top result in all 12 cases, in approximately 10–16 ms locally. This is a retrieval check, not a generated-answer or full accuracy evaluation. The source corpus and index remain private. No OpenRouter requests were used for collection, indexing or these checks.
