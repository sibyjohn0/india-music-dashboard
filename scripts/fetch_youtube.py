#!/usr/bin/env python3
import os, json, sys
from datetime import datetime, timezone
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

KEYWORD_SEARCHES = [
    "new hindi song 2026",
    "trending punjabi song 2026",
    "new tamil song 2026",
    "new telugu song 2026",
    "bollywood hits 2026",
    "new kannada song 2026",
    "new malayalam song 2026",
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


def fetch_search_ids(query):
    data = get("search", {
        "part": "id",
        "q": query,
        "type": "video",
        "videoCategoryId": MUSIC_CATEGORY,
        "regionCode": REGION,
        "order": "viewCount",
        "maxResults": 10,
        "publishedAfter": "2026-01-01T00:00:00Z",
    })
    return [i["id"]["videoId"] for i in data.get("items", []) if "videoId" in i.get("id", {})]


def fetch_video_details(ids):
    if not ids:
        return []
    data = get("videos", {
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(ids),
    })
    return data.get("items", [])


def parse_video(item):
    snip = item.get("snippet", {})
    stats = item.get("statistics", {})
    views = int(stats.get("viewCount", 0))
    likes = int(stats.get("likeCount", 0))
    comments = int(stats.get("commentCount", 0))
    engagement = round((likes + comments) / views * 100, 2) if views > 0 else 0
    tags = snip.get("tags", [])
    return {
        "id": item["id"],
        "title": snip.get("title", ""),
        "channel": snip.get("channelTitle", ""),
        "channel_id": snip.get("channelId", ""),
        "published_at": snip.get("publishedAt", ""),
        "thumbnail": snip.get("thumbnails", {}).get("medium", {}).get("url", ""),
        "views": views,
        "likes": likes,
        "comments": comments,
        "engagement_rate": engagement,
        "tags": tags[:20],
        "description": snip.get("description", "")[:300],
        "url": f"https://youtube.com/watch?v={item['id']}",
    }


def main():
    seen = set()
    videos = []

    # Trending chart
    for item in fetch_trending():
        v = parse_video(item)
        if v["id"] not in seen:
            seen.add(v["id"])
            v["source"] = "trending_chart"
            videos.append(v)

    # Keyword searches
    extra_ids = []
    for q in KEYWORD_SEARCHES:
        extra_ids += fetch_search_ids(q)

    new_ids = [i for i in dict.fromkeys(extra_ids) if i not in seen]
    for item in fetch_video_details(new_ids):
        v = parse_video(item)
        if v["id"] not in seen:
            seen.add(v["id"])
            v["source"] = "keyword_search"
            videos.append(v)

    # Keyword frequency
    kw_count = {}
    for v in videos:
        for tag in v["tags"]:
            t = tag.lower().strip()
            kw_count[t] = kw_count.get(t, 0) + 1

    top_keywords = sorted(kw_count.items(), key=lambda x: -x[1])[:60]

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total": len(videos),
        "videos": sorted(videos, key=lambda x: -x["views"]),
        "top_keywords": [{"tag": k, "count": c} for k, c in top_keywords],
    }

    os.makedirs("data/history", exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open("data/latest.json", "w") as f:
        json.dump(output, f, indent=2)
    with open(f"data/history/{date_str}.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved {len(videos)} videos — {date_str}")


if __name__ == "__main__":
    main()
