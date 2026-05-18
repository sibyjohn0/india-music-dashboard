#!/usr/bin/env python3
import os, json, sys
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError

API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
if not API_KEY:
    print("ERROR: YOUTUBE_API_KEY not set", file=sys.stderr)
    sys.exit(1)

BASE = "https://www.googleapis.com/youtube/v3"
REGION = "IN"
MUSIC_CATEGORY = "10"
MAX_RESULTS = 50
INDIA_MUSIC_CPM_INR = 80  # ₹80 per 1K views (mid-range estimate for India music)

MAINSTREAM_SEARCHES = [
    "new hindi song 2026",
    "trending punjabi song 2026",
    "new tamil song 2026",
    "new telugu song 2026",
    "bollywood hits 2026",
    "new kannada song 2026",
    "new malayalam song 2026",
]

INDIE_SEARCHES = [
    "indie india music 2026",
    "independent artist india music",
    "indie hindi music 2026",
    "Indian bedroom pop",
    "Indian lo-fi music 2026",
    "underground hip hop india 2026",
    "Indian indie pop 2026",
    "Indian producer beats 2026",
    "Indian folk fusion 2026",
    "Indian electronic music 2026",
    "Indian jazz 2026",
    "Indian rapper underground 2026",
    "indie tamil music 2026",
    "indie bengali music 2026",
    "independent musician india",
]


def get(endpoint, params):
    params["key"] = API_KEY
    url = f"{BASE}/{endpoint}?{urlencode(params)}"
    try:
        with urlopen(url) as r:
            return json.loads(r.read())
    except HTTPError as e:
        print(f"HTTP {e.code} on {url}", file=sys.stderr)
        return {}


def fetch_trending():
    data = get("videos", {
        "part": "snippet,statistics,contentDetails",
        "chart": "mostPopular",
        "regionCode": REGION,
        "videoCategoryId": MUSIC_CATEGORY,
        "maxResults": MAX_RESULTS,
    })
    return data.get("items", [])


def fetch_search_ids(query, max_results=10):
    data = get("search", {
        "part": "id",
        "q": query,
        "type": "video",
        "videoCategoryId": MUSIC_CATEGORY,
        "regionCode": REGION,
        "order": "viewCount",
        "maxResults": max_results,
        "publishedAfter": "2026-01-01T00:00:00Z",
    })
    return [i["id"]["videoId"] for i in data.get("items", []) if "videoId" in i.get("id", {})]


def fetch_video_details(ids):
    if not ids:
        return []
    items = []
    for i in range(0, len(ids), 50):
        batch = ids[i:i+50]
        data = get("videos", {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(batch),
        })
        items += data.get("items", [])
    return items


def parse_video(item):
    snip = item.get("snippet", {})
    stats = item.get("statistics", {})
    now = datetime.now(timezone.utc)
    views = int(stats.get("viewCount", 0))
    likes = int(stats.get("likeCount", 0))
    comments = int(stats.get("commentCount", 0))
    engagement = round((likes + comments) / views * 100, 2) if views > 0 else 0
    tags = snip.get("tags", [])
    published_at = snip.get("publishedAt", "")
    days_live = max((now - datetime.fromisoformat(published_at.replace("Z", "+00:00"))).days, 1) if published_at else 1
    velocity = round(views / days_live)
    earnings_est_inr = round(views * INDIA_MUSIC_CPM_INR / 1000)
    return {
        "id": item["id"],
        "title": snip.get("title", ""),
        "channel": snip.get("channelTitle", ""),
        "channel_id": snip.get("channelId", ""),
        "published_at": published_at,
        "thumbnail": snip.get("thumbnails", {}).get("medium", {}).get("url", ""),
        "views": views,
        "likes": likes,
        "comments": comments,
        "engagement_rate": engagement,
        "velocity": velocity,
        "earnings_est_inr": earnings_est_inr,
        "tags": tags[:20],
        "description": snip.get("description", "")[:300],
        "url": f"https://youtube.com/watch?v={item['id']}",
    }


INDIE_LABELS = {
    "small ugly", "xtatic music", "azadi records", "mass appeal india",
    "almost music", "def jam india", "naya records", "think music",
    "still listening", "black box", "shankar tucker", "the local train",
}

def is_indie(video):
    channel = video["channel"].lower()
    tags = " ".join(video["tags"]).lower()
    desc = video["description"].lower()
    indie_signals = ["indie", "independent", "bedroom", "lo-fi", "lofi", "underground",
                     "self-released", "unsigned", "original artist", "producer"]
    big_labels = ["t-series", "saregama", "sony music", "zee music", "tips music",
                  "eros now", "yrf music", "dharma", "jiocinema"]
    if any(l in channel for l in big_labels):
        return False
    return any(s in channel + tags + desc for s in indie_signals) or \
           any(l in channel for l in INDIE_LABELS)


def load_prev_views():
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    path = f"data/history/{yesterday}.json"
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        prev = json.load(f)
    return {v["id"]: v["views"] for v in prev.get("videos", [])}


def main():
    seen = set()
    videos = []
    prev_views = load_prev_views()

    # Trending chart
    for item in fetch_trending():
        v = parse_video(item)
        if v["id"] not in seen:
            seen.add(v["id"])
            v["source"] = "trending_chart"
            v["category"] = "mainstream"
            videos.append(v)

    # Mainstream keyword searches
    mainstream_ids = []
    for q in MAINSTREAM_SEARCHES:
        mainstream_ids += fetch_search_ids(q, max_results=10)

    for item in fetch_video_details([i for i in dict.fromkeys(mainstream_ids) if i not in seen]):
        v = parse_video(item)
        if v["id"] not in seen:
            seen.add(v["id"])
            v["source"] = "keyword_search"
            v["category"] = "mainstream"
            videos.append(v)

    # Indie searches
    indie_ids = []
    for q in INDIE_SEARCHES:
        indie_ids += fetch_search_ids(q, max_results=10)

    for item in fetch_video_details([i for i in dict.fromkeys(indie_ids) if i not in seen]):
        v = parse_video(item)
        if v["id"] not in seen:
            seen.add(v["id"])
            v["source"] = "indie_search"
            v["category"] = "indie"
            videos.append(v)

    # Re-tag trending/mainstream videos that look indie
    for v in videos:
        if v["category"] == "mainstream" and is_indie(v):
            v["category"] = "indie"

    # Day-over-day delta
    for v in videos:
        prev = prev_views.get(v["id"])
        v["views_delta"] = v["views"] - prev if prev is not None else None
        v["is_new"] = prev is None

    # Keyword frequency
    kw_count = {}
    for v in videos:
        for tag in v["tags"]:
            t = tag.lower().strip()
            kw_count[t] = kw_count.get(t, 0) + 1

    top_keywords = sorted(kw_count.items(), key=lambda x: -x[1])[:60]

    indie_count = sum(1 for v in videos if v["category"] == "indie")
    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total": len(videos),
        "indie_count": indie_count,
        "mainstream_count": len(videos) - indie_count,
        "videos": sorted(videos, key=lambda x: -x["views"]),
        "top_keywords": [{"tag": k, "count": c} for k, c in top_keywords],
    }

    os.makedirs("data/history", exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open("data/latest.json", "w") as f:
        json.dump(output, f, indent=2)
    with open(f"data/history/{date_str}.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved {len(videos)} videos — {date_str} | indie: {indie_count} | prev_views loaded: {len(prev_views)}")


if __name__ == "__main__":
    main()
