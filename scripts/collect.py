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


def permitted(url, approvals):
    if not safe_url(url):
        return False
    return any(url.startswith(prefix) for prefix in approvals[company_for(url)]["allowed_prefixes"])


def validate_permissions(approvals):
    for company in ("dar", "wasalt"):
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
            return cached["url"], cached["html"]
        final_url, html, content_type = self.fetch(url)
        if "text/html" not in content_type:
            raise ValueError("Not an HTML page")
        cache_file.write_text(json.dumps({"url": final_url, "html": html}, ensure_ascii=False), encoding="utf-8")
        return final_url, html


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--permission", required=True, type=Path)
    parser.add_argument("--max-pages", type=int, default=30, choices=range(2, 31))
    args = parser.parse_args()
    approvals = json.loads(args.permission.read_text(encoding="utf-8"))
    validate_permissions(approvals)
    seeds = json.loads(Path("data/source-manifest.json").read_text())["seeds"]
    target = Path("data/private")
    target.mkdir(parents=True, exist_ok=True)
    queue, visited, rows, report = deque(s["url"] for s in seeds), set(), [], []
    per_company = {"dar": 0, "wasalt": 0}
    with httpx.Client(headers={"User-Agent": AGENT}, timeout=20, follow_redirects=False) as client:
        collector = Collector(client, approvals, target / "collection-cache")
        while queue and len(rows) < args.max_pages and len(visited) < 100:
            url = canonical(queue.popleft())
            if url in visited:
                continue
            visited.add(url)
            company = company_for(url)
            if per_company[company] >= (args.max_pages + 1) // 2:
                continue
            try:
                final_url, html = collector.page(url)
                soup = BeautifulSoup(html, "html.parser")
                links = [canonical(urljoin(final_url, a["href"])) for a in soup.select("a[href]")]
                html_language = str(soup.html.get("lang", "")) if soup.html else ""
                language = "ar" if html_language.startswith("ar") or urlsplit(final_url).path.split("/")[1:2] == ["ar"] else "en"
                title = soup.title.get_text(" ", strip=True) if soup.title else final_url
                for tag in soup.select("script,style,nav,footer,header,form,noscript,svg"):
                    tag.decompose()
                main = soup.find("main") or soup.body or soup
                text = main.get_text(" ", strip=True)[:24000]
                if len(text) < 150:
                    raise ValueError("Insufficient readable content; no browser bypass attempted")
                if any(r["url"] == final_url for r in rows):
                    continue
                rows.append({"url": final_url, "title": title, "language": language,
                    "collected_at": datetime.now(timezone.utc).isoformat(), "text": text,
                    "content_hash": hashlib.sha256(text.encode()).hexdigest(), "company": company,
                    "synthetic": False, "permission_reference": approvals[company]["reference"]})
                per_company[company] += 1
                report.append({"url": url, "status": "collected"})
                for link in links:
                    path = urlsplit(link).path.lower()
                    if permitted(link, approvals) and not any(x in path for x in ("login", "privacy", "terms", "contact", "signup", "/api/", ".pdf")):
                        queue.append(link)
            except (ValueError, httpx.HTTPError) as exc:
                report.append({"url": url, "status": "skipped", "reason": type(exc).__name__ + ": " + str(exc)[:200]})
    (target / "collection-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not all(per_company.values()):
        raise SystemExit("Both websites must have approved readable content. See private collection report.")
    # Commit a new corpus atomically only after both sites have content.
    output = target / "corpus.jsonl"
    temporary = output.with_suffix(".tmp")
    temporary.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(f"Collected {len(rows)} pages; coverage: {per_company}. Review private report and text before deployment.")


if __name__ == "__main__":
    main()
