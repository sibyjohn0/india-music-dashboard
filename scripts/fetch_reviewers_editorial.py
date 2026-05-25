#!/usr/bin/env python3
"""
Finds Indian indie music blogs and editorial platforms via:
  1. DuckDuckGo HTML search (no API key needed)
  2. Feedspot Indian music blog directory (HTML scrape)
  3. IndiBlogger music tag

Merges results with the manually seeded editorial.json (does not overwrite curated entries).

Output: data/reviewers/editorial.json (appends discovered entries, preserves existing)
"""

import json, os, re, time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.parse import urlencode, urlparse
from html.parser import HTMLParser

DATA_DIR    = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "reviewers", "editorial.json")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# Searches to run to discover editorial platforms
SEARCH_QUERIES = [
    "indian indie music blog review site",
    "indian independent music editorial",
    "best hindi indie music blog",
    "tamil indie music blog review",
    "telugu indie music coverage site",
    "kannada indie music review blog",
    "malayalam indie music editorial",
    "bengali indie music review blog",
    "punjabi indie music blog",
    "marathi indie music review site",
    "india hip hop review blog",
    "india folk music blog review",
    "indian music zine magazine independent",
    "underground india music editorial",
]

# Skip these domains — not editorial platforms
DOMAIN_BLOCKLIST = {
    "youtube.com", "spotify.com", "apple.com", "amazon.com",
    "twitter.com", "instagram.com", "facebook.com", "reddit.com",
    "wikipedia.org", "quora.com", "medium.com", "substack.com",
    "bandcamp.com", "soundcloud.com", "t-series.com", "gaana.com",
    "jiosaavn.com", "wynk.in", "hungama.com", "saavn.com",
    "pitchfork.com", "nme.com", "billboard.com",
    "feedspot.com", "blogspot.com", "wordpress.com",
    "indiblogger.in", "bloggingcage.com",
}

# Domain must look like a dedicated music/culture site
RELEVANT_URL_RE = re.compile(
    r"(music|indie|sound|artist|band|song|track|listen|"
    r"beat|groove|rhythm|melody|tune|folk|rock|hiphop|rap|"
    r"carnatic|culture|creative|art|scene|lungi|wild|city|"
    r"diaries|aloud|mug|sinusoidal|revolver|homegrown|"
    r"rolling|stone|esquire|indigo|pink|maed|milli)",
    re.IGNORECASE,
)

MUSIC_CONTENT_RE = re.compile(
    r"\b(review|indie|independent|artist|band|album|single|"
    r"music|song|track|listen|stream|discover|feature|interview)\b",
    re.IGNORECASE,
)

INDIA_RE = re.compile(
    r"\b(india|indian|hindi|tamil|telugu|kannada|malayalam|"
    r"bengali|punjabi|marathi|desi|carnatic|hindustani|"
    r"bollywood|kollywood|tollywood)\b",
    re.IGNORECASE,
)

SPAM_RE = re.compile(
    r"\b(buy followers|get streams|promote your music|royalty.?free|"
    r"stock music|torrent|free download|seo|marketing agency)\b",
    re.IGNORECASE,
)


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            if href.startswith("http"):
                self.links.append(href)


def ddg_search(query, max_results=15):
    """DuckDuckGo HTML search — returns list of (url, title, snippet) tuples."""
    url = "https://html.duckduckgo.com/html/?" + urlencode({"q": query})
    req = Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US"})
    try:
        with urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  DDG error {query!r}: {e}")
        return []

    results = []
    # Extract result URLs from DuckDuckGo HTML
    for m in re.finditer(
        r'class="result__url"[^>]*>([^<]+)',
        html,
    ):
        url_text = m.group(1).strip()
        if not url_text.startswith("http"):
            url_text = "https://" + url_text
        results.append(url_text)
        if len(results) >= max_results:
            break

    # Also grab from href attributes
    parser = LinkExtractor()
    parser.feed(html)
    for link in parser.links:
        if "uddg=" in link:
            # DuckDuckGo redirect URL — extract target
            m = re.search(r"uddg=([^&]+)", link)
            if m:
                from urllib.parse import unquote
                results.append(unquote(m.group(1)))

    return list(dict.fromkeys(results))[:max_results]


def fetch_page_title(url):
    req = Request(url, headers={"User-Agent": UA})
    try:
        with urlopen(req, timeout=10) as r:
            html = r.read(4000).decode("utf-8", errors="ignore")
        m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        return m.group(1).strip() if m else ""
    except Exception:
        return ""


def fetch_meta_description(url):
    req = Request(url, headers={"User-Agent": UA})
    try:
        with urlopen(req, timeout=10) as r:
            html = r.read(6000).decode("utf-8", errors="ignore")
        m = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)',
            html, re.IGNORECASE
        )
        if not m:
            m = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
                html, re.IGNORECASE
            )
        return m.group(1).strip()[:300] if m else ""
    except Exception:
        return ""


def is_relevant_domain(url):
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        if any(blocked in domain for blocked in DOMAIN_BLOCKLIST):
            return False
        return bool(RELEVANT_URL_RE.search(domain))
    except Exception:
        return False


def detect_languages(text):
    langs = []
    checks = {
        "Tamil":     ["tamil", "kollywood", "chennai"],
        "Telugu":    ["telugu", "tollywood", "hyderabad"],
        "Kannada":   ["kannada", "bangalore", "bengaluru"],
        "Malayalam": ["malayalam", "kerala"],
        "Bengali":   ["bengali", "bangla", "kolkata"],
        "Punjabi":   ["punjabi", "chandigarh"],
        "Marathi":   ["marathi", "pune", "maharashtra"],
        "Hindi":     ["hindi", "hindustani", "delhi"],
    }
    low = text.lower()
    for lang, kws in checks.items():
        if any(k in low for k in kws):
            langs.append(lang)
    return langs or ["English"]


def load_existing():
    if not os.path.exists(OUTPUT_PATH):
        return {}, []
    with open(OUTPUT_PATH) as f:
        data = json.load(f)
    existing = {r["id"]: r for r in data.get("reviewers", [])}
    return existing, data.get("reviewers", [])


def main():
    existing, all_reviewers = load_existing()
    seen_domains = {
        urlparse(r["url"]).netloc.lower().replace("www.", "")
        for r in all_reviewers
        if r.get("url")
    }
    seen_urls = {r["url"] for r in all_reviewers if r.get("url")}

    new_entries = []

    for query in SEARCH_QUERIES:
        print(f"  searching: {query!r}")
        urls = ddg_search(query)
        for raw_url in urls:
            try:
                parsed  = urlparse(raw_url)
                domain  = parsed.netloc.lower().replace("www.", "")
                base_url = f"{parsed.scheme}://{parsed.netloc}"
            except Exception:
                continue

            if domain in seen_domains:
                continue
            if not is_relevant_domain(raw_url):
                continue

            seen_domains.add(domain)

            # Fetch page title and meta description to verify content
            title = fetch_page_title(base_url)
            desc  = fetch_meta_description(base_url)
            text  = f"{title} {desc}"

            if SPAM_RE.search(text):
                continue
            if not MUSIC_CONTENT_RE.search(text):
                continue
            if not INDIA_RE.search(text):
                continue

            slug = re.sub(r"[^a-z0-9]+", "-", domain).strip("-")
            langs = detect_languages(text)

            entry = {
                "id":          slug,
                "category":    "editorial",
                "name":        title[:80] if title else domain,
                "url":         base_url,
                "description": desc[:300],
                "indie_focus": "unknown",
                "languages":   langs,
                "genres":      [],
                "reach":       {"followers": None, "avg_views": None, "subscriber_count": None},
                "discovery_impact": None,
                "active":          True,
                "last_verified":   datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "socials":         {},
                "youtube_url":     None,
                "pitch_to":        [],
                "content_types":   ["editorial"],
                "artists_covered": [],
                "notes":           f"Discovered via search: {query!r}",
            }

            new_entries.append(entry)
            seen_urls.add(base_url)
            print(f"    found: {domain} — {title[:60]}")
            time.sleep(0.5)

        time.sleep(1.0)

    # Merge: keep existing verified entries, append new discoveries
    merged = list(existing.values()) + [
        e for e in new_entries if e["id"] not in existing
    ]

    for i, r in enumerate(merged, 1):
        r["rank"] = i

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "category":     "editorial",
        "total":        len(merged),
        "reviewers":    merged,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWritten → {OUTPUT_PATH}")
    print(f"  {len(existing)} existing + {len(new_entries)} new = {len(merged)} total")


if __name__ == "__main__":
    main()
