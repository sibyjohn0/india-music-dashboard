#!/usr/bin/env python3
"""
Fetches social conversations about Indian indie music.

Reddit:  Uses OAuth client-credentials (works in GitHub Actions).
         Requires REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET secrets.
         Falls back to public JSON API (may be rate-limited in CI).
Twitter: optional --twitter flag, uses Chrome profile via Playwright (local only).

Outputs: data/social.json
"""

import argparse, base64, json, os, re, time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError

DATA_DIR    = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "social.json")
LATEST_PATH = os.path.join(DATA_DIR, "latest.json")

REDDIT_UA        = "IndiaIndieMusicRadar/1.0 by /u/indiemusic_bot"
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_SECRET    = os.environ.get("REDDIT_CLIENT_SECRET", "")

SUBREDDITS = [
    "IndieMusicIndia",
    "CarnaticMusic",
    "hindimusic",
    "kollywood",
    "Kerala",
    "IndianPop",
    "indieheads",      # global indie but surfaces Indian artists
    "LofiHipHop",      # lo-fi producers
]

CROSS_SEARCHES = [
    "india indie music",
    "independent indian artist",
    "bengali indie music",
    "marathi indie singer",
    "kannada indie music",
    "punjabi indie artist",
    "malayalam indie music",
    "telugu indie artist",
    "tamil indie singer",
    "indian hip hop underground",
    "desi rapper original",
    "indian folk singer original",
    "collab india music",
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
    "Hindi":     ["hindi", "delhi", "hindustani", "desi"],
}

MUSIC_RE = re.compile(
    r"\b(music|song|track|album|artist|indie|band|singer|musician|original|"
    r"release|playlist|listen|stream|youtube|spotify|ep|single|soundcloud|"
    r"collab|collaboration|feature|producer|rapper|folk|acoustic)\b",
    re.IGNORECASE,
)

INDIA_RE = re.compile(
    r"\b(india|indian|hindi|tamil|telugu|kannada|malayalam|bengali|punjabi|"
    r"marathi|desi|carnatic|hindustani|bangalore|mumbai|chennai|kolkata|"
    r"hyderabad|delhi|kerala|pune|goa|assam)\b",
    re.IGNORECASE,
)

SPAM_RE = re.compile(
    r"\b(royalty.?free|stock music|piracy|torrent|crack|free download|"
    r"buy followers|promote your|get streams)\b",
    re.IGNORECASE,
)

MAINSTREAM_RE = re.compile(
    r"\b(t.?series|zee music|sony music|tips music|eros now|saregama|"
    r"ar rahman|arijit singh|badshah|diljit|shreya ghoshal|atif aslam)\b",
    re.IGNORECASE,
)

BLOCKED_SUBREDDITS = {
    "FinalFantasy", "DisneyMovies", "ToddintheShadow", "worldnews", "AskReddit",
    "Music_Anniversary", "primaverasound", "DesiFragranceAddicts", "videos",
    "gaming", "movies", "television", "sports", "politics", "news",
    "mildlyinteresting", "funny", "aww", "pics", "gifs", "IRCTC",
}


# ── Reddit OAuth ──────────────────────────────────────────────────────────────

_reddit_token = None
_token_expiry = 0

def get_reddit_token():
    global _reddit_token, _token_expiry
    if _reddit_token and time.time() < _token_expiry - 60:
        return _reddit_token
    if not REDDIT_CLIENT_ID or not REDDIT_SECRET:
        return None
    auth = base64.b64encode(f"{REDDIT_CLIENT_ID}:{REDDIT_SECRET}".encode()).decode()
    req = Request(
        "https://www.reddit.com/api/v1/access_token",
        data=urlencode({"grant_type": "client_credentials"}).encode(),
        headers={"Authorization": f"Basic {auth}", "User-Agent": REDDIT_UA},
    )
    try:
        res = json.loads(urlopen(req, timeout=10).read())
        _reddit_token = res.get("access_token")
        _token_expiry = time.time() + res.get("expires_in", 3600)
        return _reddit_token
    except Exception as e:
        print(f"  Reddit token error: {e}")
        return None


def _get(url):
    """Try OAuth first, fall back to public JSON API."""
    token = get_reddit_token()
    if token:
        req = Request(url.replace("www.reddit.com", "oauth.reddit.com"),
                      headers={"Authorization": f"bearer {token}", "User-Agent": REDDIT_UA})
    else:
        req = Request(url, headers={"User-Agent": REDDIT_UA})
    try:
        with urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode())
    except (HTTPError, URLError, Exception) as e:
        print(f"  Fetch error {url[:70]}: {e}")
        return None


# ── Parsing ───────────────────────────────────────────────────────────────────

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
    if SPAM_RE.search(text) or MAINSTREAM_RE.search(text):
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


def parse_reddit_child(child, subreddit="", artists=None):
    d     = child.get("data", {})
    title = d.get("title", "")
    body  = (d.get("selftext") or "")
    sub   = d.get("subreddit", subreddit)
    score = d.get("score", 0)
    created   = d.get("created_utc", 0)
    permalink = d.get("permalink", "")

    if body in ("[removed]", "[deleted]"):
        body = ""
    if sub in BLOCKED_SUBREDDITS:
        return None

    from_curated = sub in set(SUBREDDITS)
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
    url  = f"https://www.reddit.com/r/{sub}/new.json?{urlencode({'limit': limit})}"
    data = _get(url)
    return data.get("data", {}).get("children", []) if data else []


def fetch_search(query, limit=25):
    url  = f"https://www.reddit.com/search.json?{urlencode({'q': query, 'sort': 'new', 'limit': limit})}"
    data = _get(url)
    return data.get("data", {}).get("children", []) if data else []


def fetch_reddit(artists):
    posts, seen = [], set()
    token = get_reddit_token()
    if token:
        print(f"  Using Reddit OAuth (authenticated)")
    else:
        print(f"  No Reddit credentials — using public API (may be rate-limited)")

    for sub in SUBREDDITS:
        print(f"  r/{sub}...")
        for child in fetch_subreddit(sub):
            pid = child.get("data", {}).get("id", "")
            if pid not in seen:
                seen.add(pid)
                p = parse_reddit_child(child, sub, artists)
                if p:
                    posts.append(p)
        time.sleep(0.5)

    for query in CROSS_SEARCHES:
        print(f"  search: {query!r}...")
        for child in fetch_search(query):
            pid = child.get("data", {}).get("id", "")
            if pid not in seen:
                seen.add(pid)
                sub = child.get("data", {}).get("subreddit", "")
                p = parse_reddit_child(child, sub, artists)
                if p:
                    posts.append(p)
        time.sleep(0.5)

    print(f"  {len(posts)} relevant posts from Reddit")
    return posts


def fetch_twitter_playwright(artists):
    """Local only -- requires Chrome profile and --twitter flag."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  playwright not installed")
        return []

    CHROME_PROFILE = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    if not os.path.isdir(CHROME_PROFILE):
        print(f"  Chrome profile not found at {CHROME_PROFILE}")
        return []

    QUERIES = [
        "#IndieMusicIndia",
        "indie music india original -filter:retweets",
        "new indian indie artist -filter:retweets",
        "independent indian music -filter:retweets",
        "desi rap original -filter:retweets",
        "indian folk singer original -filter:retweets",
    ]

    tweets, seen = [], set()
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE, channel="chrome", headless=True,
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
            for art in page.query_selector_all("article[data-testid='tweet']")[:15]:
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
                    tweets.append({
                        "platform": "twitter", "subreddit": "",
                        "title": text[:140], "snippet": "",
                        "url": link, "score": 0,
                        "language": detect_language(text),
                        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "artist": find_artist(text, "", artists),
                    })
                except Exception:
                    pass
        ctx.close()
    return tweets


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--twitter", action="store_true")
    args = parser.parse_args()

    print("Loading artists from latest.json...")
    artists = load_artists()
    print(f"  {len(artists)} artists available for matching")

    print("Fetching Reddit...")
    posts = fetch_reddit(artists)

    if args.twitter:
        print("Fetching Twitter...")
        posts += fetch_twitter_playwright(artists)

    artist_posts = [p for p in posts if p.get("artist")]
    feed_posts   = [p for p in posts if not p.get("artist")]

    # Sort by score
    artist_posts.sort(key=lambda x: -x.get("score", 0))
    feed_posts.sort(key=lambda x: -x.get("score", 0))

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
