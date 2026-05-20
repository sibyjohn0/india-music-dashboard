#!/usr/bin/env python3
"""
Fetches social conversations about Indian indie music.
Reddit:  free public JSON API — runs in GitHub Actions.
Twitter: optional --twitter flag, uses Chrome profile via Playwright (local only).
Outputs: data/social.json
"""

import argparse, json, os, re, time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError

DATA_DIR    = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "social.json")
LATEST_PATH = os.path.join(DATA_DIR, "latest.json")

REDDIT_UA = "IndiaIndieMusicRadar/1.0 (automated; opensource)"

# --- Subreddits ---
SUBREDDITS = [
    "IndieMusicIndia",
    "CarnaticMusic",
    "hindimusic",
    "kollywood",
    "Kerala",
    "IndianPop",
]

# Broad cross-Reddit searches to catch regional + under-represented language content
CROSS_SEARCHES = [
    "india indie music",
    "independent indian artist music",
    "bengali indie music",
    "marathi indie music",
    "kannada indie music",
    "punjabi indie music",
    "malayalam indie music",
    "telugu indie music",
    "indian singer songwriter original",
]

SUBREDDIT_LANG = {
    "CarnaticMusic": "Tamil",
    "kollywood":     "Tamil",
    "hindimusic":    "Hindi",
    "Kerala":        "Malayalam",
}

LANG_KEYWORDS = {
    "Tamil":     ["tamil", "kollywood", "tamilnadu", "chennai", "carnatic"],
    "Telugu":    ["telugu", "tollywood", "hyderabad", "andhra", "telangana"],
    "Kannada":   ["kannada", "bangalore", "bengaluru", "karnataka"],
    "Malayalam": ["malayalam", "kerala", "malayali"],
    "Bengali":   ["bengali", "bangla", "kolkata", "bengal"],
    "Punjabi":   ["punjabi", "punjab", "chandigarh"],
    "Marathi":   ["marathi", "maharashtra", "pune"],
    "Hindi":     ["hindi", "delhi", "bollywood", "hindustani"],
}

MUSIC_RE = re.compile(
    r"\b(music|song|track|album|artist|indie|band|singer|musician|original|"
    r"release|playlist|listen|stream|youtube|spotify|ep|single|soundcloud)\b",
    re.IGNORECASE,
)

# Required for cross-Reddit search results: must mention India/Indian context
INDIA_RE = re.compile(
    r"\b(india|indian|hindi|tamil|telugu|kannada|malayalam|bengali|punjabi|"
    r"marathi|bollywood|kollywood|tollywood|desi|carnatic|hindustani|"
    r"bangalore|mumbai|chennai|kolkata|hyderabad|delhi|kerala|pune)\b",
    re.IGNORECASE,
)

SPAM_RE = re.compile(
    r"\b(royalty.?free|stock music|piracy|torrent|crack|free download)\b",
    re.IGNORECASE,
)

# Mainstream/label terms to skip (mirrors fetch_youtube.py logic for consistency)
MAINSTREAM_RE = re.compile(
    r"\b(t.?series|zee music|sony music|tips music|eros now|saregama|"
    r"ar rahman|arijit singh|badshah|diljit|shreya ghoshal|atif aslam)\b",
    re.IGNORECASE,
)

# Subreddits that are clearly not India music -- block cross-search results from them
BLOCKED_SUBREDDITS = {
    "FinalFantasy", "DisneyMovies", "ToddintheShadow", "worldnews", "AskReddit",
    "Music_Anniversary", "primaverasound", "DesiFragranceAddicts", "videos",
    "gaming", "movies", "television", "sports", "politics", "news",
}


def _get(url, headers=None):
    req = Request(url, headers={"User-Agent": REDDIT_UA, **(headers or {})})
    try:
        with urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  Fetch error {url[:80]}: {e}")
        return None


def detect_language(text, subreddit=""):
    if subreddit in SUBREDDIT_LANG:
        return SUBREDDIT_LANG[subreddit]
    low = text.lower()
    for lang, kws in LANG_KEYWORDS.items():
        if any(k in low for k in kws):
            return lang
    return "Hindi"


def is_music_post(title, body="", require_india=False):
    text = f"{title} {body}"
    if SPAM_RE.search(text):
        return False
    if MAINSTREAM_RE.search(text):
        return False
    if not MUSIC_RE.search(text):
        return False
    if require_india and not INDIA_RE.search(text):
        return False
    return True


def load_artists():
    try:
        with open(LATEST_PATH) as f:
            data = json.load(f)
        artists = {}
        for v in data.get("videos", []):
            ch = v.get("channel", "")
            cid = v.get("channel_id") or ch
            if ch and len(ch) > 3:
                artists[ch.lower()] = ch  # lower -> original case
        return artists
    except Exception:
        return {}


def find_artist(title, body, artists):
    text = f"{title} {body}".lower()
    # longest match first to avoid partial-name false positives
    for key in sorted(artists, key=len, reverse=True):
        if key in text:
            return artists[key]
    return None


def parse_reddit_child(child, subreddit="", artists=None):
    d = child.get("data", {})
    title = d.get("title", "")
    body  = d.get("selftext", "") or ""
    sub   = d.get("subreddit", subreddit)
    score = d.get("score", 0)
    created = d.get("created_utc", 0)
    permalink = d.get("permalink", "")

    if body in ("[removed]", "[deleted]"):
        body = ""

    # For cross-Reddit results (not our curated subreddits), require India context
    from_curated = sub in set(SUBREDDITS) or subreddit in set(SUBREDDITS)
    if sub in BLOCKED_SUBREDDITS:
        return None
    if not is_music_post(title, body, require_india=not from_curated):
        return None

    lang   = detect_language(f"{title} {body}", sub)
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


def fetch_subreddit(sub, limit=30):
    url = f"https://www.reddit.com/r/{sub}/new.json?{urlencode({'limit': limit})}"
    data = _get(url)
    if not data:
        return []
    return data.get("data", {}).get("children", [])


def fetch_search(query, limit=25):
    url = f"https://www.reddit.com/search.json?{urlencode({'q': query, 'sort': 'new', 'limit': limit})}"
    data = _get(url)
    if not data:
        return []
    return data.get("data", {}).get("children", [])


def fetch_reddit(artists):
    posts, seen = [], set()

    for sub in SUBREDDITS:
        print(f"  r/{sub}...")
        for child in fetch_subreddit(sub):
            pid = child.get("data", {}).get("id", "")
            if pid in seen:
                continue
            seen.add(pid)
            p = parse_reddit_child(child, sub, artists)
            if p:
                posts.append(p)
        time.sleep(0.7)

    for query in CROSS_SEARCHES:
        print(f"  search: {query!r}...")
        for child in fetch_search(query):
            pid = child.get("data", {}).get("id", "")
            if pid in seen:
                continue
            seen.add(pid)
            sub = child.get("data", {}).get("subreddit", "")
            p = parse_reddit_child(child, sub, artists)
            if p:
                posts.append(p)
        time.sleep(0.7)

    return posts


def fetch_twitter_playwright(artists):
    """
    Scrape Twitter search via Playwright + your Chrome profile.
    Requires: pip install playwright && playwright install chromium
    Only works locally — not in GitHub Actions.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  playwright not installed — pip install playwright && playwright install chromium")
        return []

    CHROME_PROFILE = os.path.expanduser(
        "~/Library/Application Support/Google/Chrome"
    )
    if not os.path.isdir(CHROME_PROFILE):
        print(f"  Chrome profile not found at {CHROME_PROFILE}")
        return []

    QUERIES = [
        "#IndieMusicIndia",
        "indie music india original -filter:retweets",
        "new indian indie artist -filter:retweets",
        "independent indian music -filter:retweets",
        "indian singer songwriter original -filter:retweets",
        "bengali indie music -filter:retweets",
        "marathi indie music -filter:retweets",
        "kannada indie music -filter:retweets",
    ]

    tweets, seen = [], set()

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE,
            channel="chrome",
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        for query in QUERIES:
            print(f"  Twitter: {query!r}...")
            encoded = query.replace(" ", "%20").replace("#", "%23").replace(":", "%3A")
            try:
                page.goto(f"https://twitter.com/search?q={encoded}&f=live", timeout=20000)
                page.wait_for_timeout(3000)
            except Exception as e:
                print(f"    nav error: {e}")
                continue

            articles = page.query_selector_all("article[data-testid='tweet']")
            for art in articles[:15]:
                try:
                    text_el = art.query_selector("[data-testid='tweetText']")
                    text    = text_el.inner_text() if text_el else ""
                    link_el = art.query_selector("a[href*='/status/']")
                    link    = link_el.get_attribute("href") if link_el else ""
                    if link and not link.startswith("http"):
                        link = f"https://twitter.com{link}"
                    tid = link.split("/status/")[1].split("/")[0] if "/status/" in link else ""
                    if not tid or tid in seen:
                        continue
                    seen.add(tid)
                    if not is_music_post(text):
                        continue
                    lang   = detect_language(text)
                    artist = find_artist(text, "", artists)
                    tweets.append({
                        "platform": "twitter",
                        "subreddit": "",
                        "title":    text[:140],
                        "snippet":  "",
                        "url":      link,
                        "score":    0,
                        "language": lang,
                        "date":     datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "artist":   artist,
                    })
                except Exception:
                    continue

            time.sleep(2)

        ctx.close()

    return tweets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--twitter", action="store_true",
                        help="Also scrape Twitter/X via Chrome profile (local only)")
    args = parser.parse_args()

    print("Loading artists from latest.json...")
    artists = load_artists()
    print(f"  {len(artists)} artists available for matching")

    print("Fetching Reddit...")
    reddit_posts = fetch_reddit(artists)
    print(f"  {len(reddit_posts)} relevant posts")

    twitter_posts = []
    if args.twitter:
        print("Fetching Twitter via Chrome...")
        twitter_posts = fetch_twitter_playwright(artists)
        print(f"  {len(twitter_posts)} tweets")

    all_posts = reddit_posts + twitter_posts

    sort_key = lambda p: (-p["score"], p["date"])
    artist_posts = sorted([p for p in all_posts if p.get("artist")], key=sort_key)
    feed_posts   = sorted([p for p in all_posts if not p.get("artist")], key=sort_key)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total":         len(all_posts),
        "artist_posts":  artist_posts[:40],
        "feed":          feed_posts[:60],
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Written → {OUTPUT_PATH}  ({len(artist_posts)} artist-matched, {len(feed_posts)} general)")


if __name__ == "__main__":
    main()
