#!/usr/bin/env python3
"""
fetch_news_rss.py — Fetch RSS feeds from Indian music publications and keep
only the India-relevant items.

Reality check (verified 2026-08-26): the usable Indian-music RSS landscape is
thin. Wild City dropped its RSS feed (old /feed now serves HTML). Homegrown's
feed lives at /stories.rss and is culture-wide (music is a fraction). Rolling
Stone India publishes prolifically but is ~80% global pop/K-pop/Hollywood —
its Indian edition is a minority of the firehose. So we pull the more
music-focused RS India category feeds plus Homegrown, then apply a POSITIVE
India-relevance filter and drop everything else. Better a short, genuinely
Indian feed than a long global one.

Output: data/news-rss.json  (already filtered — the display page trusts it)
Requires: feedparser (pip install feedparser)
"""

import os, json, sys, re
from datetime import datetime, timezone

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "news-rss.json")

FEEDS = [
    {"name": "Homegrown",           "url": "https://homegrown.co.in/stories.rss"},
    {"name": "Rolling Stone India", "url": "https://rollingstoneindia.com/category/artists/feed/"},
    {"name": "Rolling Stone India", "url": "https://rollingstoneindia.com/category/reviews/feed/"},
    {"name": "Rolling Stone India", "url": "https://rollingstoneindia.com/feed/"},
]

MAX_PER_SOURCE = 25

# --- India relevance: an item must match INDIA_RE to survive. -----------------
# Places, languages, scene/festival names, and India-only signals. Case-insensitive.
INDIA_RE = re.compile(
    r"\b("
    r"india|indian|desi|bharat|bollywood|"
    r"mumbai|bombay|delhi|new delhi|bengaluru|bangalore|chennai|kolkata|calcutta|"
    r"hyderabad|pune|goa|kochi|cochin|jaipur|ahmedabad|shillong|guwahati|chandigarh|"
    r"hindi|punjabi|tamil|telugu|marathi|bengali|malayalam|kannada|assamese|bhojpuri|gujarati|urdu|"
    r"carnatic|hindustani|ghazal|qawwali|sufi|bhangra|"
    r"nh7|weekender|ziro|magnetic fields|lollapalooza india|sunburn|hornbill|"
    r"mahindra blues|bacardi|ragasthan|paddy fields|control alt delete|malhar|"
    r"antisocial|blueFROG|bluefrog|prithvi|the piano man|g5a|"
    r"indie india|independent music india"
    r")\b", re.I)

# Known Indian indie / mainstream-Indian artist names (extend as needed).
INDIA_ARTISTS = re.compile(
    r"\b("
    r"prateek kuhad|when chai met toast|the local train|ritviz|nucleya|divine|"
    r"mc stan|seedhe maut|prabh deep|raftaar|badshah|ap dhillon|diljit|"
    r"anuv jain|taba chake|lifafa|peter cat recording co|parekh|singh|"
    r"raghu dixit|indian ocean|swarathma|agam|thermal and a quarter|"
    r"arijit|shreya|a\.?r\.? rahman|ar rahman|amit trivedi|"
    r"osho jain|kamakshi|dhruv|zaeden|kayan|hanumankind|"
    r"acyuta gopi|barkha ritu|kaam bhaari|frizzell|bloodywood"
    r")\b", re.I)


def is_india_relevant(article):
    # Broad India/place/scene signal is matched against the TITLE only — RS India's
    # summaries carry "Rolling Stone India" boilerplate that would match everything.
    title = article.get("title", "")
    blob  = title + " " + article.get("summary", "")
    # Specific artist names are safe to match anywhere (they don't appear in boilerplate).
    return bool(INDIA_RE.search(title) or INDIA_ARTISTS.search(blob))


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
        summary = strip_html(summary_raw)
        # Strip WordPress "The post X appeared first on Y." boilerplate.
        summary = re.split(r"\s*The post .+? appeared first on", summary)[0]
        summary = summary[:500].strip()
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

    raw_articles = []
    errors       = []

    for source in FEEDS:
        try:
            articles = fetch_feed(fp, source["name"], source["url"])
            raw_articles.extend(articles)
        except Exception as e:
            msg = f"{source['name']}: {e}"
            print(f"  ERROR: {msg}", file=sys.stderr)
            errors.append(msg)

    # Dedupe by URL (RS category + main feeds overlap), then keep only India-relevant.
    seen = set()
    deduped = []
    for a in raw_articles:
        key = a.get("url") or a.get("title")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(a)

    total_raw = len(deduped)
    all_articles = [a for a in deduped if is_india_relevant(a)]
    print(f"  India-relevant: {len(all_articles)} of {total_raw} unique articles")

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
        "sources":    sorted({s["name"] for s in FEEDS}),
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
