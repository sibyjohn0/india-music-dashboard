#!/usr/bin/env python3
"""
Fetches Buzz tab content from two sources:
  1. Reddit public JSON API (no credentials required)
  2. Google News RSS

Outputs: data/social.json
"""

import json, os, re, time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.request import urlopen, Request
from urllib.parse import urlencode

DATA_DIR    = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "social.json")
LATEST_PATH = os.path.join(DATA_DIR, "latest.json")

UA = "IndiaIndieMusicRadar/1.0"

# ── Reddit config ─────────────────────────────────────────────────────────────

SUBREDDITS = [
    "IndieMusicIndia",
    "CarnaticMusic",
    "hindimusic",
    "kollywood",
    "Kerala",
    "IndianPop",
    "indieheads",
    "LofiHipHop",
]

SUBREDDIT_LANG = {
    "CarnaticMusic": "Tamil",
    "kollywood":     "Tamil",
    "hindimusic":    "Hindi",
    "Kerala":        "Malayalam",
}

BLOCKED_SUBS = {
    "FinalFantasy", "DisneyMovies", "worldnews", "AskReddit",
    "Music_Anniversary", "videos", "gaming", "movies", "television",
    "sports", "politics", "news", "funny", "aww", "pics",
    "mildlyinteresting", "gifs", "IRCTC", "DesiFragranceAddicts",
}

REDDIT_SEARCHES = [
    "india indie music",
    "independent indian artist",
    "bengali indie music",
    "tamil indie singer",
    "telugu indie artist",
    "kannada indie music",
    "malayalam indie music",
    "punjabi indie artist",
    "marathi indie singer",
    "indian hip hop underground",
    "desi rapper original",
]

INDIA_RE = re.compile(
    r"\b(india|indian|hindi|tamil|telugu|kannada|malayalam|bengali|punjabi|"
    r"marathi|desi|carnatic|bangalore|mumbai|chennai|kolkata|hyderabad|delhi|kerala)\b",
    re.IGNORECASE,
)

# ── Google News RSS config ────────────────────────────────────────────────────

RSS_QUERIES = [
    "india indie music",
    "independent indian music artist",
    "bengali indie music",
    "marathi indie singer",
    "kannada indie music",
    "punjabi indie artist",
    "malayalam indie music",
    "telugu indie artist",
    "tamil indie singer",
    "indian hip hop underground",
    "desi rapper original",
    "indian folk musician original",
    "india music release new",
    "indie artist india album single",
]

# ── Shared filters ────────────────────────────────────────────────────────────

LANG_KEYWORDS = {
    "Tamil":     ["tamil", "kollywood", "tamilnadu", "chennai", "carnatic"],
    "Telugu":    ["telugu", "tollywood", "hyderabad", "andhra", "telangana"],
    "Kannada":   ["kannada", "bangalore", "bengaluru", "karnataka"],
    "Malayalam": ["malayalam", "kerala", "malayali"],
    "Bengali":   ["bengali", "bangla", "kolkata", "bengal"],
    "Punjabi":   ["punjabi", "punjab", "chandigarh"],
    "Marathi":   ["marathi", "maharashtra", "pune"],
    "Hindi":     ["hindi", "delhi", "hindustani", "desi"],
}

MUSIC_RE = re.compile(
    r"\b(music|song|track|album|artist|indie|band|singer|musician|original|"
    r"release|playlist|listen|stream|youtube|spotify|ep|single|"
    r"collab|producer|rapper|folk|acoustic)\b",
    re.IGNORECASE,
)

SPAM_RE = re.compile(
    r"\b(royalty.?free|stock music|piracy|torrent|free download|"
    r"buy followers|promote your|get streams)\b",
    re.IGNORECASE,
)

MAINSTREAM_RE = re.compile(
    r"\b(t.?series|zee music|sony music|tips music|eros now|saregama|"
    r"ar rahman|arijit singh|badshah|diljit|shreya ghoshal|atif aslam)\b",
    re.IGNORECASE,
)

NEWS_NOISE_RE = re.compile(
    r"\b(murder|murdered|killed|dead|death|found dead|missing|kidnap|kidnapped|"
    r"arrested|rape|assault|suicide|accident|crash|police|crime|court|verdict|"
    r"jailed|imprisoned|politician|minister|government|election|protest|riot)\b",
    re.IGNORECASE,
)


def detect_language(text):
    low = text.lower()
    for lang, kws in LANG_KEYWORDS.items():
        if any(k in low for k in kws):
            return lang
    return "Hindi"


def is_music_post(title, body=""):
    text = f"{title} {body}"
    if SPAM_RE.search(text) or MAINSTREAM_RE.search(text) or NEWS_NOISE_RE.search(text):
        return False
    return bool(MUSIC_RE.search(text))


def load_artists():
    try:
        with open(LATEST_PATH) as f:
            data = json.load(f)
        artists = {}
        for v in data.get("videos", []):
            ch = v.get("channel", "")
            if ch and len(ch) > 3:
                artists[ch.lower()] = ch
        return artists
    except Exception:
        return {}


def find_artist(title, body, artists):
    text = f"{title} {body}".lower()
    for key in sorted(artists, key=len, reverse=True):
        if key in text:
            return artists[key]
    return None


# ── Reddit ────────────────────────────────────────────────────────────────────

def reddit_get(path):
    req = Request(
        f"https://www.reddit.com{path}",
        headers={"User-Agent": UA}
    )
    try:
        with urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  Reddit error {path[:60]}: {e}")
        return None


def parse_reddit_child(child, subreddit="", artists=None):
    d         = child.get("data", {})
    title     = d.get("title", "")
    body      = (d.get("selftext") or "")
    sub       = d.get("subreddit", subreddit)
    score     = d.get("score", 0)
    created   = d.get("created_utc", 0)
    permalink = d.get("permalink", "")

    if body in ("[removed]", "[deleted]"):
        body = ""
    if sub in BLOCKED_SUBS:
        return None
    if not is_music_post(title, body):
        return None
    # Non-curated subreddits must have explicit Indian context
    if sub not in set(SUBREDDITS) and not INDIA_RE.search(f"{title} {body}"):
        return None

    lang   = SUBREDDIT_LANG.get(sub, detect_language(f"{title} {body}"))
    artist = find_artist(title, body, artists or {})
    date   = datetime.fromtimestamp(created, tz=timezone.utc).strftime("%Y-%m-%d")

    return {
        "platform":  "reddit",
        "subreddit": sub,
        "title":     title,
        "snippet":   body[:200].strip(),
        "url":       f"https://www.reddit.com{permalink}",
        "score":     score,
        "language":  lang,
        "date":      date,
        "artist":    artist,
    }


def fetch_reddit(artists):
    posts, seen = [], set()

    for sub in SUBREDDITS:
        print(f"  r/{sub}...")
        data     = reddit_get(f"/r/{sub}/new.json?limit=30")
        children = data["data"]["children"] if data else []
        for child in children:
            pid = child.get("data", {}).get("id", "")
            if pid not in seen:
                seen.add(pid)
                p = parse_reddit_child(child, sub, artists)
                if p:
                    posts.append(p)
        time.sleep(0.6)

    for query in REDDIT_SEARCHES:
        print(f"  search: {query!r}...")
        data     = reddit_get(f"/search.json?{urlencode({'q': query, 'sort': 'new', 'limit': 25})}")
        children = data["data"]["children"] if data else []
        for child in children:
            pid = child.get("data", {}).get("id", "")
            if pid not in seen:
                seen.add(pid)
                sub = child.get("data", {}).get("subreddit", "")
                p   = parse_reddit_child(child, sub, artists)
                if p:
                    posts.append(p)
        time.sleep(0.6)

    print(f"  {len(posts)} Reddit posts")
    return posts


# ── Google News RSS ───────────────────────────────────────────────────────────

def fetch_rss(query):
    url = (
        "https://news.google.com/rss/search?"
        + urlencode({"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
    )
    req = Request(url, headers={"User-Agent": UA})
    try:
        with urlopen(req, timeout=15) as r:
            return r.read()
    except Exception as e:
        print(f"  RSS error {query!r}: {e}")
        return None


def parse_rss(xml_bytes, artists):
    items = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"  XML parse error: {e}")
        return items

    for item in root.findall(".//item"):
        title  = re.sub(r"(\s*[-–|]\s*[^-–|]{3,50})+$", "", (item.findtext("title") or "").strip())
        link   = (item.findtext("link") or "").strip()
        pub    = (item.findtext("pubDate") or "").strip()
        raw    = re.sub(r"<[^>]+>", "", item.findtext("description") or "")
        desc   = raw.replace("\xa0", " ").strip()
        source = (item.findtext("source") or "").strip()

        if desc.lower().startswith(title[:35].lower()):
            desc = ""
        if not title or not link:
            continue
        if not is_music_post(title, desc):
            continue

        try:
            date = parsedate_to_datetime(pub).strftime("%Y-%m-%d")
        except Exception:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        items.append({
            "platform": "news",
            "subreddit": source,
            "title":    title,
            "snippet":  desc[:200],
            "url":      link,
            "score":    0,
            "language": detect_language(f"{title} {desc}"),
            "date":     date,
            "artist":   find_artist(title, desc, artists),
        })
    return items


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Loading artists from latest.json...")
    artists = load_artists()
    print(f"  {len(artists)} artists available for matching")

    posts, seen_urls = [], set()

    print("\nFetching Reddit (public API)...")
    for p in fetch_reddit(artists):
        if p["url"] not in seen_urls:
            seen_urls.add(p["url"])
            posts.append(p)

    print("\nFetching Google News RSS...")
    for query in RSS_QUERIES:
        print(f"  {query!r}...")
        xml_bytes = fetch_rss(query)
        if not xml_bytes:
            continue
        for item in parse_rss(xml_bytes, artists):
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                posts.append(item)
        time.sleep(0.3)

    # Deduplicate news articles by normalized title (same story, multiple outlets)
    seen_titles, deduped = set(), []
    for p in posts:
        if p["platform"] == "reddit":
            deduped.append(p)
            continue
        key = re.sub(r"[^a-z0-9]", "", p["title"][:50].lower())
        if key not in seen_titles:
            seen_titles.add(key)
            deduped.append(p)

    # Cap per source to prevent any one outlet flooding the feed
    MAX_PER_SOURCE = 8
    source_counts: dict = {}
    capped = []
    for p in sorted(deduped, key=lambda x: x["date"], reverse=True):
        src = p["subreddit"]
        if source_counts.get(src, 0) < MAX_PER_SOURCE:
            source_counts[src] = source_counts.get(src, 0) + 1
            capped.append(p)

    artist_posts = sorted([p for p in capped if p.get("artist")],
                          key=lambda x: x["date"], reverse=True)
    feed_posts   = sorted([p for p in capped if not p.get("artist")],
                          key=lambda x: x["date"], reverse=True)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total":        len(capped),
        "artist_posts": artist_posts,
        "feed":         feed_posts,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    reddit_count = sum(1 for p in capped if p["platform"] == "reddit")
    news_count   = sum(1 for p in capped if p["platform"] == "news")
    print(f"\nWritten → {OUTPUT_PATH}")
    print(f"  {reddit_count} Reddit posts + {news_count} news articles = {len(capped)} total")
    print(f"  {len(artist_posts)} artist-matched, {len(feed_posts)} general")


if __name__ == "__main__":
    main()
