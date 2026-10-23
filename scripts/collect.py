"""Permission-gated, bounded collection. No collection runs during chat requests."""
import argparse
import hashlib
import json
import time
from collections import deque
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup
from protego import Protego

from backend.retrieval import safe_url

AGENT = "AssessmentResearchBot/1.0"
MAX_BYTES = 2_000_000


def company_for(url):
    return "dar" if "darglobal.co.uk" in urlsplit(url).netloc else "wasalt"


def canonical(url):
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc.lower(), p.path or "/", "", ""))


def discover_links(soup, base_url, approvals):
    links = []
    for anchor in soup.select("a[href]"):
        raw = urljoin(base_url, anchor["href"])
        parsed = urlsplit(raw)
        # Do not turn searches, query routes or asset URLs into crawl targets.
        if parsed.query or parsed.fragment or parsed.scheme != "https":
            continue
        url = canonical(raw)
        path = parsed.path.lower()
        if permitted(url, approvals) and not any(x in path for x in (
            "login", "privacy", "terms", "contact", "signup", "/api/", ".pdf", "pay-online", "careers", "internship"
        )) and url not in links:
            links.append(url)
    return links


def permitted(url, approvals):
    if not safe_url(url):
        return False
    return any(url.startswith(prefix) for prefix in approvals.get(company_for(url), {}).get("allowed_prefixes", []))


def validate_permissions(approvals, companies=("dar", "wasalt")):
    for company in companies:
        rule = approvals.get(company, {})
        if not all(rule.get(k) for k in ("approved", "reference", "reviewed_terms_url", "allow_openrouter_processing", "allow_public_answers", "allowed_prefixes")):
            raise ValueError(f"Missing collection and processing permission for {company}")
        if date.fromisoformat(rule["expires_at"]) < date.today():
            raise ValueError(f"Permission expired for {company}")
        for prefix in rule["allowed_prefixes"]:
            if not safe_url(prefix) or company_for(prefix) != company or not prefix.endswith("/"):
                raise ValueError("Permission prefixes must be approved HTTPS directory roots ending in /")


class Collector:
    def __init__(self, client, approvals, cache_dir):
        self.client, self.approvals, self.cache_dir = client, approvals, cache_dir
        self.rules = {}
        self.last_request = 0.0
        self.minimum_delay = 2.0
        self.page_fetched_at = None
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, url):
        # All redirects are checked before following; off-domain redirects are refused.
        for _ in range(4):
            if not safe_url(url):
                raise ValueError("Redirect left allowlist")
            time.sleep(max(0, self.minimum_delay - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            with self.client.stream("GET", url) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    next_url = urljoin(url, response.headers["location"])
                    if not permitted(next_url, self.approvals) or not self.robot_allowed(next_url):
                        raise ValueError("Redirect not permitted")
                    url = next_url
                    continue
                response.raise_for_status()
                raw = bytearray()
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw) > MAX_BYTES:
                        raise ValueError("Response exceeded collection size limit")
                return url, bytes(raw).decode("utf-8", errors="replace"), response.headers.get("content-type", "")
        raise ValueError("Too many redirects")

    def robot_allowed(self, url):
        root = f"{urlsplit(url).scheme}://{urlsplit(url).netloc}"
        if root not in self.rules:
            # Sentinel prevents a redirect cycle while loading robots itself.
            self.rules[root] = None
            try:
                _, text, _ = self.fetch(root + "/robots.txt")
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code != 404:
                    raise ValueError("Could not verify robots.txt; collection stopped") from exc
                text = "User-agent: *\nAllow: /"
            rules = Protego.parse(text)
            crawl_delay = rules.crawl_delay(AGENT)
            if crawl_delay is not None:
                self.minimum_delay = max(self.minimum_delay, float(crawl_delay))
            rate = rules.request_rate(AGENT)
            if rate is not None and rate.requests > 0:
                self.minimum_delay = max(self.minimum_delay, rate.seconds / rate.requests)
            self.rules[root] = rules
        rules = self.rules[root]
        return rules is not None and rules.can_fetch(url, AGENT)

    def page(self, url):
        if not permitted(url, self.approvals) or not self.robot_allowed(url):
            raise ValueError("Collection denied by scope or robots.txt")
        cache_file = self.cache_dir / (hashlib.sha256(url.encode()).hexdigest() + ".json")
        if cache_file.exists():
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            if "_Incapsula_Resource" in cached["html"] or "cf-chl-" in cached["html"]:
                raise ValueError("Access challenge; not bypassed")
            self.page_fetched_at = cached.get("fetched_at")
            return cached["url"], cached["html"]
        final_url, html, content_type = self.fetch(url)
        if "text/html" not in content_type:
            raise ValueError("Not an HTML page")
        if "_Incapsula_Resource" in html or "cf-chl-" in html:
            raise ValueError("Access challenge; not bypassed")
        self.page_fetched_at = datetime.now(timezone.utc).isoformat()
        cache_file.write_text(json.dumps({"url": final_url, "html": html,
            "fetched_at": self.page_fetched_at}, ensure_ascii=False), encoding="utf-8")
        return final_url, html


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--permission", required=True, type=Path)
    parser.add_argument("--max-pages", type=int, default=30, choices=range(2, 201))
    parser.add_argument("--max-visits", type=int, default=400, choices=range(2, 801))
    parser.add_argument("--manifest", type=Path, default=Path("data/source-manifest.json"))
    parser.add_argument("--output-dir", type=Path, help="Separate private snapshot directory; never use a public source folder.")
    parser.add_argument("--seed-only", action="store_true", help="Fetch the selected manifest only; do not follow additional links.")
    parser.add_argument("--companies", nargs="+", choices=("dar", "wasalt"), default=["dar", "wasalt"],
                        help="Collect an approved company independently; default requires both.")
    args = parser.parse_args()
    approvals = json.loads(args.permission.read_text(encoding="utf-8"))
    companies = tuple(dict.fromkeys(args.companies))
    validate_permissions(approvals, companies)
    # Exclude other companies before any fetching or link discovery.
    approvals = {company: approvals[company] for company in companies}
    seeds = json.loads(args.manifest.read_text(encoding="utf-8"))["seeds"]
    # A partial snapshot cannot overwrite the final two-company corpus.
    target = args.output_dir or (Path("data/private") if len(companies) == 2 else Path("data/private") / companies[0])
    if not target.resolve().is_relative_to(Path("data/private").resolve()):
        raise ValueError("Collected content must remain under ignored data/private/")
    target.mkdir(parents=True, exist_ok=True)
    queue, visited, rows, report = deque(s["url"] for s in seeds if s["company"] in companies), set(), [], []
    per_company = {company: 0 for company in companies}
    consecutive_challenges = 0
    challenge_stopped = False
    with httpx.Client(headers={"User-Agent": AGENT}, timeout=20, follow_redirects=False) as client:
        collector = Collector(client, approvals, target / "collection-cache")
        while queue and len(rows) < args.max_pages and len(visited) < args.max_visits:
            url = canonical(queue.popleft())
            if url in visited:
                continue
            visited.add(url)
            company = company_for(url)
            if company not in companies or per_company[company] >= (args.max_pages + len(companies) - 1) // len(companies):
                continue
            try:
                final_url, html = collector.page(url)
                soup = BeautifulSoup(html, "html.parser")
                # Discover routes even when the current page has no useful body.
                if not args.seed_only:
                    queue.extend(link for link in discover_links(soup, final_url, approvals) if link not in visited)
                html_language = str(soup.html.get("lang", "")) if soup.html else ""
                language = "ar" if html_language.startswith("ar") or urlsplit(final_url).path.split("/")[1:2] == ["ar"] else "en"
                title_node = soup.title or soup.find("h1")
                title = title_node.get_text(" ", strip=True) if title_node else final_url
                for tag in soup.select("script,style,nav,footer,header,form,noscript,svg"):
                    tag.decompose()
                main = soup.find("main") or soup.body or soup
                text = " ".join(main.get_text(" ", strip=True).split())[:24000]
                if len(text) < 150:
                    raise ValueError("Insufficient readable content; no browser bypass attempted")
                if any(r["url"] == final_url for r in rows):
                    continue
                rows.append({"url": final_url, "title": title, "language": language,
                    "collected_at": collector.page_fetched_at or datetime.now(timezone.utc).isoformat(), "text": text,
                    "content_hash": hashlib.sha256(text.encode()).hexdigest(), "company": company,
                    "synthetic": False, "permission_reference": approvals[company]["reference"]})
                per_company[company] += 1
                report.append({"url": url, "status": "collected"})
                consecutive_challenges = 0
                print(f"Collected {len(rows)}/{args.max_pages}: {final_url}", flush=True)
            except (ValueError, httpx.HTTPError) as exc:
                report.append({"url": url, "status": "skipped", "reason": type(exc).__name__ + ": " + str(exc)[:200]})
                consecutive_challenges = consecutive_challenges + 1 if "Access challenge" in str(exc) else 0
            # Preserve coverage evidence even if a long crawl is interrupted.
            (target / "collection-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            if len(visited) % 10 == 0:
                print(f"Progress: {len(visited)} visited, {len(rows)} retained, {len(report) - len(rows)} skipped", flush=True)
            if consecutive_challenges >= 5:
                challenge_stopped = True
                print("Stopped after five consecutive access challenges; no bypass or automatic retry.", flush=True)
                break
    (target / "collection-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (target / "crawl-summary.json").write_text(json.dumps({"selected_companies": companies,
        "visited": len(visited), "collected": len(rows), "queued_remaining": len(set(queue) - visited),
        "page_limit": args.max_pages, "visit_limit": args.max_visits,
        "stop_reason": "access_challenge_threshold" if challenge_stopped else "page_limit" if len(rows) >= args.max_pages else "visit_limit" if len(visited) >= args.max_visits else "queue_exhausted",
        "snapshot_created_at": datetime.now(timezone.utc).isoformat()}, indent=2), encoding="utf-8")
    if not all(per_company.values()):
        raise SystemExit("Each selected website must have approved readable content. See private collection report.")
    # Commit atomically only after each selected site has content.
    output = target / "corpus.jsonl"
    temporary = output.with_suffix(".tmp")
    temporary.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(f"Collected {len(rows)} pages; coverage: {per_company}. Review private report and text before deployment.")


if __name__ == "__main__":
    main()
