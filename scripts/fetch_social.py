#!/usr/bin/env python3
"""
Fetches Google News RSS about Indian indie music.
No API keys required.
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


def is_music_article(title, snippet=""):
    text = f"{title} {snippet}"
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


def find_artist(title, snippet, artists):
    text = f"{title} {snippet}".lower()
    for key in sorted(artists, key=len, reverse=True):
        if key in text:
            return artists[key]
    return None


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
        title  = (item.findtext("title") or "").strip()
        link   = (item.findtext("link") or "").strip()
        pub    = (item.findtext("pubDate") or "").strip()
        desc   = re.sub(r"<[^>]+>", "", item.findtext("description") or "").strip()
        source = (item.findtext("source") or "").strip()

        if not title or not link:
            continue
        if not is_music_article(title, desc):
            continue

        try:
            date = parsedate_to_datetime(pub).strftime("%Y-%m-%d")
        except Exception:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        lang   = detect_language(f"{title} {desc}")
        artist = find_artist(title, desc, artists)

        items.append({
            "platform": "news",
            "subreddit": source,
            "title":    title,
            "snippet":  desc[:200],
            "url":      link,
            "score":    0,
            "language": lang,
            "date":     date,
            "artist":   artist,
        })
    return items


def main():
    print("Loading artists from latest.json...")
    artists = load_artists()
    print(f"  {len(artists)} artists available for matching")

    posts, seen = [], set()
    for query in RSS_QUERIES:
        print(f"  RSS: {query!r}...")
        xml_bytes = fetch_rss(query)
        if not xml_bytes:
            continue
        for item in parse_rss(xml_bytes, artists):
            key = item["url"]
            if key not in seen:
                seen.add(key)
                posts.append(item)
        time.sleep(0.3)

    artist_posts = sorted([p for p in posts if p.get("artist")],
                          key=lambda x: x["date"], reverse=True)
    feed_posts   = sorted([p for p in posts if not p.get("artist")],
                          key=lambda x: x["date"], reverse=True)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total":        len(posts),
        "artist_posts": artist_posts,
        "feed":         feed_posts,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Written → {OUTPUT_PATH}  ({len(artist_posts)} artist-matched, {len(feed_posts)} general)")


if __name__ == "__main__":
    main()
