#!/usr/bin/env python3
"""
Builds a ranked database of YouTube music reviewers who surface Indian
independent / indie artists — not mainstream label content.

Output: data/reviewers.json

Ranking metric: average views on qualifying review videos (Indian indie focus),
with a secondary discovery-impact score (review views / artist subscriber count).

Run: YOUTUBE_API_KEY=xxx python3 scripts/fetch_reviewers.py
"""

import os, sys, json, re, time
from datetime import datetime, timezone
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError

API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
if not API_KEY:
    print("ERROR: YOUTUBE_API_KEY not set", file=sys.stderr)
    sys.exit(1)

BASE = "https://www.googleapis.com/youtube/v3"

DATA_DIR    = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "reviewers.json")
LATEST_PATH = os.path.join(DATA_DIR, "latest.json")

# ── Search queries ────────────────────────────────────────────────────────────
# Two tiers:
#   CHANNEL_QUERIES  — searched with type=channel to find reviewer channels directly
#   VIDEO_QUERIES    — searched with type=video to find individual review videos
#      (channel is then extracted from the video)

CHANNEL_QUERIES = [
    "india music review",
    "indian indie music review",
    "song review india",
    "music review hindi",
    "tamil music review",
    "telugu music review",
    "kannada music review",
    "malayalam music review",
    "bengali music review",
    "punjabi music review",
    "indian hip hop review",
    "desi music review",
    "bollywood review channel",
    "independent indian music critic",
]

VIDEO_QUERIES = [
    "song review independent indian artist",
    "reacting to indian indie music",
    "first listen indian indie",
    "honest review indian music",
    "artist review india indie",
    "reviewing new indian music",
    "song breakdown indian artist",
    "music analysis india indie",
    "listening to indian underground music",
    "new artist review india",
]

# ── Filters ───────────────────────────────────────────────────────────────────

# Channel names that indicate label-affiliated or mainstream-only content
LABEL_BLOCKLIST = re.compile(
    r"\b(t.?series|tseries|saregama|sony music|zee music|tips music|eros|"
    r"junglee|dharma|hungama|gaana|warner music|universal music|emi music|"
    r"times music|ultra music|speed records|white hill|desi music factory|"
    r"think music|sun music|star vijay|aditya music|lahari music|"
    r"muzik247|raj music|eskay music|shree venkatesh)\b",
    re.IGNORECASE,
)

# Title must indicate an actual review/reaction to a specific song or artist —
# NOT a list, compilation, or generic countdown
REVIEW_TITLE_RE = re.compile(
    r"\b(review|reaction|reacting|first listen|honest review|honest opinion|"
    r"breakdown|deep dive|analysis|song review|artist review|music review|"
    r"listening to|i listened|i reacted|my thoughts on|rating|rated)\b",
    re.IGNORECASE,
)

# Exclude list/compilation formats even if they use review-adjacent words
LIST_TITLE_RE = re.compile(
    r"\b(top \d|top\d|#\d|best \d|\d best|compilation|playlist|songs you|"
    r"songs that|most popular|went viral|every desi|all time)\b",
    re.IGNORECASE,
)

# Title keywords that flag mainstream / label-push content
MAINSTREAM_TITLE_RE = re.compile(
    r"\b(t.?series|saregama|zee music|sony music|arijit|badshah|diljit|"
    r"shreya ghoshal|atif aslam|neha kakkar|yo yo honey singh|"
    r"official music video|lyric video)\b",
    re.IGNORECASE,
)

# India relevance
INDIA_RE = re.compile(
    r"\b(india|indian|hindi|tamil|telugu|kannada|malayalam|bengali|punjabi|"
    r"marathi|desi|carnatic|bangalore|mumbai|chennai|kolkata|hyderabad|"
    r"delhi|kerala|indie india)\b",
    re.IGNORECASE,
)

LANG_KEYWORDS = {
    "Tamil":     ["tamil", "kollywood", "tamilnadu", "chennai", "carnatic"],
    "Telugu":    ["telugu", "tollywood", "hyderabad", "andhra", "telangana"],
    "Kannada":   ["kannada", "bangalore", "bengaluru", "karnataka"],
    "Malayalam": ["malayalam", "kerala", "malayali"],
    "Bengali":   ["bengali", "bangla", "kolkata", "bengal"],
    "Punjabi":   ["punjabi", "punjab", "chandigarh"],
    "Marathi":   ["marathi", "maharashtra", "pune"],
    "Hindi":     ["hindi", "delhi", "hindustani", "bollywood"],
    "English":   ["english"],
}


def yt_get(endpoint, params):
    params["key"] = API_KEY
    url = f"{BASE}/{endpoint}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=15) as r:
            return json.loads(r.read().decode())
    except HTTPError as e:
        body = e.read().decode()[:200]
        print(f"  HTTP {e.code} on {endpoint}: {body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  Error on {endpoint}: {e}", file=sys.stderr)
        return None


def search_channels(query, max_results=25):
    data = yt_get("search", {
        "part":       "snippet",
        "q":          query,
        "type":       "channel",
        "regionCode": "IN",
        "maxResults": max_results,
        "order":      "relevance",
    })
    if not data:
        return []
    return data.get("items", [])


def get_channel_recent_videos(channel_id, max_results=20):
    data = yt_get("search", {
        "part":       "snippet",
        "channelId":  channel_id,
        "type":       "video",
        "order":      "date",
        "maxResults": max_results,
    })
    if not data:
        return []
    return data.get("items", [])


def search_videos(query, max_results=50):
    data = yt_get("search", {
        "part":       "snippet",
        "q":          query,
        "type":       "video",
        "regionCode": "IN",
        "relevanceLanguage": "en",
        "maxResults": max_results,
        "order":      "relevance",
    })
    if not data:
        return []
    return data.get("items", [])


def get_video_stats(video_ids):
    if not video_ids:
        return {}
    data = yt_get("videos", {
        "part": "statistics,snippet",
        "id":   ",".join(video_ids),
    })
    if not data:
        return {}
    out = {}
    for item in data.get("items", []):
        vid  = item["id"]
        stat = item.get("statistics", {})
        snip = item.get("snippet", {})
        out[vid] = {
            "views":        int(stat.get("viewCount", 0)),
            "likes":        int(stat.get("likeCount", 0)),
            "comments":     int(stat.get("commentCount", 0)),
            "published_at": snip.get("publishedAt", ""),
            "channel_id":   snip.get("channelId", ""),
            "channel_name": snip.get("channelTitle", ""),
            "title":        snip.get("title", ""),
            "description":  snip.get("description", "")[:300],
        }
    return out


def get_channel_stats(channel_ids):
    if not channel_ids:
        return {}
    data = yt_get("channels", {
        "part": "statistics,snippet,brandingSettings",
        "id":   ",".join(channel_ids),
    })
    if not data:
        return {}
    out = {}
    for item in data.get("items", []):
        cid  = item["id"]
        stat = item.get("statistics", {})
        snip = item.get("snippet", {})
        branding = item.get("brandingSettings", {}).get("channel", {})
        out[cid] = {
            "name":         snip.get("title", ""),
            "description":  snip.get("description", "")[:400],
            "country":      snip.get("country", ""),
            "subscribers":  int(stat.get("subscriberCount", 0)),
            "total_views":  int(stat.get("viewCount", 0)),
            "video_count":  int(stat.get("videoCount", 0)),
            "keywords":     branding.get("keywords", ""),
            "custom_url":   snip.get("customUrl", ""),
            "published_at": snip.get("publishedAt", ""),
        }
    return out


def detect_languages(text):
    low = text.lower()
    langs = []
    for lang, kws in LANG_KEYWORDS.items():
        if any(k in low for k in kws):
            langs.append(lang)
    return langs or ["Hindi"]


def is_review_video(title, description):
    if MAINSTREAM_TITLE_RE.search(title):
        return False
    if LIST_TITLE_RE.search(title):
        return False
    return bool(REVIEW_TITLE_RE.search(title))  # title must carry the signal, not just description


def is_india_relevant(title, description, channel_name):
    text = f"{title} {description} {channel_name}"
    return bool(INDIA_RE.search(text))


def load_tracked_artists():
    """Load known indie artists from latest.json for discovery-impact scoring."""
    try:
        with open(LATEST_PATH) as f:
            data = json.load(f)
        return {v.get("channel", "").lower(): v.get("views", 0)
                for v in data.get("videos", []) if v.get("channel")}
    except Exception:
        return {}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Loading tracked artists for discovery-impact scoring...")
    tracked_artists = load_tracked_artists()
    print(f"  {len(tracked_artists)} tracked indie artists loaded")

    candidate_video_ids  = set()
    video_channel_map    = {}  # video_id → channel_id
    candidate_channel_ids = set()  # channels found via channel search

    # Step 1a: Search for reviewer channels directly
    print("\nSearching for reviewer channels...")
    for query in CHANNEL_QUERIES:
        print(f"  {query!r}...")
        items = search_channels(query, max_results=25)
        for item in items:
            cid   = item.get("id", {}).get("channelId")
            cname = item.get("snippet", {}).get("title", "")
            if cid and not LABEL_BLOCKLIST.search(cname):
                candidate_channel_ids.add(cid)
        time.sleep(0.5)

    print(f"  {len(candidate_channel_ids)} candidate channels found")

    # Step 1b: For each candidate channel, pull recent videos and filter to reviews
    print("\nPulling recent videos from candidate channels...")
    for cid in list(candidate_channel_ids):
        items = get_channel_recent_videos(cid, max_results=20)
        for item in items:
            vid  = item.get("id", {}).get("videoId")
            snip = item.get("snippet", {})
            title = snip.get("title", "")
            desc  = snip.get("description", "")
            cname = snip.get("channelTitle", "")
            if not vid:
                continue
            if not is_review_video(title, desc):
                continue
            if not is_india_relevant(title, desc, cname):
                continue
            candidate_video_ids.add(vid)
            video_channel_map[vid] = cid
        time.sleep(0.4)

    # Step 1c: Also search for review videos directly (catches channels not in step 1a)
    print("\nSearching for review videos directly...")
    for query in VIDEO_QUERIES:
        print(f"  {query!r}...")
        items = search_videos(query, max_results=50)
        for item in items:
            vid  = item.get("id", {}).get("videoId")
            snip = item.get("snippet", {})
            title = snip.get("title", "")
            desc  = snip.get("description", "")
            cname = snip.get("channelTitle", "")
            cid   = snip.get("channelId", "")
            if not vid or not cid:
                continue
            if LABEL_BLOCKLIST.search(cname):
                continue
            if not is_review_video(title, desc):
                continue
            if not is_india_relevant(title, desc, cname):
                continue
            candidate_video_ids.add(vid)
            video_channel_map[vid] = cid
        time.sleep(0.5)

    print(f"\n  {len(candidate_video_ids)} candidate review videos found")

    # Step 2: Fetch full video stats in batches of 50
    print("\nFetching video statistics...")
    vid_list   = list(candidate_video_ids)
    all_vstats = {}
    for i in range(0, len(vid_list), 50):
        batch = vid_list[i:i+50]
        all_vstats.update(get_video_stats(batch))
        time.sleep(0.2)
    print(f"  {len(all_vstats)} videos with stats")

    # Step 3: Aggregate by channel
    channel_videos = {}  # channel_id → list of video stat dicts
    for vid, vstats in all_vstats.items():
        cid = vstats.get("channel_id") or video_channel_map.get(vid)
        if not cid:
            continue
        if cid not in channel_videos:
            channel_videos[cid] = []
        vstats["video_id"] = vid
        vstats["video_url"] = f"https://www.youtube.com/watch?v={vid}"
        channel_videos[cid].append(vstats)

    print(f"  {len(channel_videos)} unique channels")

    # Step 4: Fetch channel stats in batches of 50
    print("\nFetching channel statistics...")
    all_cstats = {}
    cid_list = list(channel_videos.keys())
    for i in range(0, len(cid_list), 50):
        batch = cid_list[i:i+50]
        all_cstats.update(get_channel_stats(batch))
        time.sleep(0.2)

    # Step 5: Build ranked reviewer entries
    print("\nScoring and ranking reviewers...")
    reviewers = []

    for cid, videos in channel_videos.items():
        cstats = all_cstats.get(cid, {})
        cname  = cstats.get("name", "")

        # Re-check label blocklist on full channel name
        if LABEL_BLOCKLIST.search(cname):
            continue

        # Need at least 1 qualifying review video
        if len(videos) < 1:
            continue

        # Subscribers: ignore mega-channels (>5M) and tiny inactive ones (<500)
        subs = cstats.get("subscribers", 0)
        if subs > 5_000_000 or subs < 500:
            continue

        views_list = [v["views"] for v in videos if v["views"] > 0]
        if not views_list:
            continue

        avg_views    = int(sum(views_list) / len(views_list))
        median_views = sorted(views_list)[len(views_list) // 2]
        top_video    = max(videos, key=lambda v: v["views"])

        # Discovery impact: avg review views relative to channel size
        # High ratio = reviewer surfaces unknown artists to a much bigger audience
        discovery_impact = round(avg_views / max(subs, 1), 3)

        # Detect languages from channel description + video titles
        lang_text = cstats.get("description", "") + " " + cstats.get("keywords", "")
        lang_text += " " + " ".join(v["title"] for v in videos)
        languages = detect_languages(lang_text)

        # Indie focus ratio: what fraction of their videos are review (not uploads)
        # Approximation: qualifying videos / total channel video count
        indie_focus = round(len(videos) / max(cstats.get("video_count", 1), 1), 3)

        # Last active date
        pub_dates = [v["published_at"] for v in videos if v["published_at"]]
        last_active = max(pub_dates)[:10] if pub_dates else ""

        # Channel URL
        custom = cstats.get("custom_url", "")
        channel_url = (
            f"https://www.youtube.com/{custom}" if custom
            else f"https://www.youtube.com/channel/{cid}"
        )

        reviewers.append({
            "channel_id":        cid,
            "channel_name":      cname,
            "channel_url":       channel_url,
            "platform":          "youtube",
            "subscribers":       subs,
            "avg_review_views":  avg_views,
            "median_review_views": median_views,
            "discovery_impact":  discovery_impact,
            "qualifying_videos": len(videos),
            "indie_focus_ratio": indie_focus,
            "languages":         languages,
            "last_active":       last_active,
            "country":           cstats.get("country", ""),
            "description":       cstats.get("description", "")[:300],
            "top_review": {
                "title": top_video["title"],
                "url":   top_video["video_url"],
                "views": top_video["views"],
                "date":  top_video["published_at"][:10] if top_video.get("published_at") else "",
            },
            "sample_reviews": [
                {"title": v["title"], "url": v["video_url"], "views": v["views"]}
                for v in sorted(videos, key=lambda x: x["views"], reverse=True)[:5]
            ],
        })

    # Sort by avg_review_views descending (primary), discovery_impact (secondary)
    reviewers.sort(key=lambda r: (r["avg_review_views"], r["discovery_impact"]), reverse=True)

    # Assign rank
    for i, r in enumerate(reviewers, 1):
        r["rank"] = i

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total":        len(reviewers),
        "reviewers":    reviewers,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWritten → {OUTPUT_PATH}")
    print(f"  {len(reviewers)} reviewers ranked")
    if reviewers:
        print(f"\nTop 10 by avg review views:")
        for r in reviewers[:10]:
            print(f"  #{r['rank']:>3}  {r['channel_name']:<40}  "
                  f"avg {r['avg_review_views']:>7,} views  "
                  f"subs {r['subscribers']:>8,}  "
                  f"impact {r['discovery_impact']:.3f}  "
                  f"langs {', '.join(r['languages'][:2])}")


if __name__ == "__main__":
    main()
