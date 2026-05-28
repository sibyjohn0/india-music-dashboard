#!/usr/bin/env python3
"""
fetch_news_rss.py — Fetch RSS feeds from Indian indie music publications.

Sources:
  - Wild City:          https://www.wild-city.com/feed
  - Homegrown:          https://homegrown.co.in/feed
  - Rolling Stone India: https://rollingstoneindia.com/feed/

Output: data/news-rss.json

Requires: feedparser (pip install feedparser)
Keeps the last 20 articles per publication.
"""

import os, json, sys, re
from datetime import datetime, timezone

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "news-rss.json")

FEEDS = [
    {"name": "Wild City",           "url": "https://www.wild-city.com/feed"},
    {"name": "Homegrown",           "url": "https://homegrown.co.in/feed"},
    {"name": "Rolling Stone India", "url": "https://rollingstoneindia.com/feed/"},
]

MAX_PER_SOURCE = 20


def load_last_known():
    if os.path.exists(OUT):
        with open(OUT) as f:
            return json.load(f)
    return None


def ensure_feedparser():
    try:
        import feedparser
        return feedparser
    except ImportError:
        print("ERROR: feedparser not installed. Run: pip install feedparser", file=sys.stderr)
        sys.exit(1)


def strip_html(text):
    """Remove HTML tags and collapse whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#039;", "'", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_published(entry):
    """Return ISO 8601 string from a feedparser entry's date fields."""
    # feedparser populates published_parsed or updated_parsed as time.struct_time UTC
    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                import calendar
                ts = calendar.timegm(t)
                return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            except Exception:
                pass
    # Fallback: raw string
    for field in ("published", "updated", "created"):
        raw = getattr(entry, field, None)
        if raw:
            return str(raw)
    return ""


def fetch_feed(fp, source_name, url):
    """Fetch and parse one RSS feed. Returns list of article dicts."""
    try:
        feed = fp.parse(url)
    except Exception as e:
        print(f"  ERROR fetching {source_name}: {e}", file=sys.stderr)
        return []

    if feed.get("bozo") and not feed.get("entries"):
        print(f"  WARNING: {source_name} feed returned bozo error: {feed.get('bozo_exception')}", file=sys.stderr)

    articles = []
    for entry in feed.entries[:MAX_PER_SOURCE]:
        title = strip_html(getattr(entry, "title", ""))
        url_  = getattr(entry, "link", "") or getattr(entry, "id", "")
        pub   = parse_published(entry)
        # Summary: prefer summary, fall back to content
        summary_raw = (
            getattr(entry, "summary", "")
            or (entry.content[0].value if getattr(entry, "content", None) else "")
        )
        summary = strip_html(summary_raw)[:500]
        if title:
            articles.append({
                "title":        title,
                "publication":  source_name,
                "url":          url_,
                "published_at": pub,
                "summary":      summary,
            })

    print(f"  {source_name}: {len(articles)} articles")
    return articles


def main():
    last_known  = load_last_known()
    fetched_at  = datetime.now(timezone.utc).isoformat()
    fp          = ensure_feedparser()

    all_articles = []
    errors       = []

    for source in FEEDS:
        try:
            articles = fetch_feed(fp, source["name"], source["url"])
            all_articles.extend(articles)
        except Exception as e:
            msg = f"{source['name']}: {e}"
            print(f"  ERROR: {msg}", file=sys.stderr)
            errors.append(msg)

    if not all_articles:
        msg = "No articles fetched from any RSS feed."
        print(f"WARNING: {msg}", file=sys.stderr)
        if last_known:
            n = len(last_known.get("articles", []))
            print(f"  Preserving last known data ({n} articles).")
            sys.exit(0)
        out_data = {"articles": [], "fetched_at": fetched_at, "note": msg}
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(out_data, f, indent=2)
        print("  Wrote placeholder.")
        sys.exit(0)

    # Sort by published_at descending (ISO strings sort lexicographically)
    all_articles.sort(key=lambda a: a.get("published_at", ""), reverse=True)

    out_data = {
        "articles":   all_articles,
        "fetched_at": fetched_at,
        "sources":    [s["name"] for s in FEEDS],
        "errors":     errors,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out_data, f, indent=2)

    print(f"OK: news-rss.json — {len(all_articles)} articles at {fetched_at}")
    for a in all_articles[:5]:
        pub = a.get("published_at", "")[:10]
        print(f"  [{a['publication']}] {pub} — {a['title'][:65]}")


if __name__ == "__main__":
    main()
