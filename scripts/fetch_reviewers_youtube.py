#!/usr/bin/env python3
"""
Finds YouTube channels that have reviewed / reacted to Indian indie artists.

Strategy: inverted lookup — search by known artist name, not by genre.
This surfaces channels that have actually engaged with Indian indie music
rather than channels that merely describe themselves as music reviewers.

Output: data/reviewers/youtube.json
"""

import json, os, re, time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.parse import urlencode

DATA_DIR    = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "reviewers", "youtube.json")
API_KEY     = os.environ.get("YOUTUBE_API_KEY", "")
BASE        = "https://www.googleapis.com/youtube/v3"

# ── Known Indian indie artists to search against ───────────────────────────────
# Mix of mainstream-indie crossover (higher search volume) and pure indie
# to maximise channel discovery across the quality spectrum.
ARTISTS = [
    # English / Hindi indie
    "Prateek Kuhad", "Peter Cat Recording Co", "Ankur Tewari",
    "Ritviz", "Nucleya", "When Chai Met Toast", "Parvaaz",
    "Aswekeepsearching", "Skrat", "Sanjoy", "Dhruv Visvanath",
    "Raghu Dixit", "Sid Sriram", "Aditya Rikhari", "Hanumankind",
    "Seedhe Maut", "Prabh Deep", "Brodha V", "Raftaar",
    "Slow Cheetah", "Lucknowi", "Easy Wanderlings", "The Yellow Diary",
    "Aditi Ramesh", "Monica Dogra", "Shalmali Kholgade",
    "Amit Trivedi indie", "Clinton Cerejo", "Karsh Kale",
    # Tamil indie
    "Yuvan Shankar Raja indie", "Darbuka Siva", "Tenma",
    "Sanjay Subrahmanyan indie", "Pa Ranjith music",
    # Telugu indie
    "Rahul Sipligunj", "Mangli", "Kaala Bhairava indie",
    # Kannada indie
    "Raghu Dixit Project", "Swarathma",
    # Bengali indie
    "Cactus band", "Lakkhichhara", "Chandrabindoo", "Bhoomi band",
    "Fossils band", "Bangla indie music",
    # Malayalam indie
    "Avial band", "Thaikkudam Bridge", "Thaikoodam Bridge",
    # Regional / crossover
    "Indian Ocean band", "Thermal and a Quarter",
    "Zero bridge band", "Shaa'ir + Func",
    # User-specified artists
    "Sakre", "Shanka Tribe", "Paal Dabba", "Rasa band India", "Ashok Raka",
]

# Search suffixes — what reviewers/reactors add to artist names
# Kept to 2 to stay within 10,000 unit daily quota (100 units/search):
# 40 artists × 2 suffixes = 80 queries = 8,000 units
SUFFIXES = ["review", "reaction"]

# ── Filters ────────────────────────────────────────────────────────────────────

# Channels to skip regardless of what they review
CHANNEL_BLOCKLIST = {
    "T-Series", "Zee Music Company", "Sony Music India",
    "Tips Official", "Eros Now", "Saregama Music",
    "Speed Records", "Lahari Music",
}

# Video title must contain at least one of these to count as review content
REVIEW_RE = re.compile(
    r"\b(review|reaction|react|first listen|first time|analysis|breakdown|"
    r"honest|my thoughts|thoughts on|listening to|i listened|watched|heard)\b",
    re.IGNORECASE,
)

# Skip channels whose description suggests non-music focus
OFF_TOPIC_DESC_RE = re.compile(
    r"\b(cooking|gaming|tech|politics|news|sports|fitness|fashion|beauty|"
    r"travel|finance|investment|real estate|cricket|football)\b",
    re.IGNORECASE,
)

MIN_SUBSCRIBERS = 500      # ignore micro-micro channels
MIN_AVG_VIEWS   = 200      # ignore channels with no real reach
MAX_RESULTS_PER_QUERY = 15 # quota: 100 units per search call


def yt_get(endpoint, params):
    params["key"] = API_KEY
    url = f"{BASE}/{endpoint}?{urlencode(params)}"
    req = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  YT error {endpoint}: {e}")
        return {}


def search_videos(query, max_results=MAX_RESULTS_PER_QUERY):
    data = yt_get("search", {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "relevance",
    })
    return data.get("items", [])


def get_channel_stats(channel_ids):
    if not channel_ids:
        return {}
    data = yt_get("channels", {
        "part": "snippet,statistics",
        "id": ",".join(channel_ids),
        "maxResults": 50,
    })
    result = {}
    for item in data.get("items", []):
        cid   = item["id"]
        stats = item.get("statistics", {})
        snip  = item.get("snippet", {})
        result[cid] = {
            "name":        snip.get("title", ""),
            "description": snip.get("description", "")[:300],
            "country":     snip.get("country", ""),
            "subscribers": int(stats.get("subscriberCount", 0)),
            "video_count": int(stats.get("videoCount", 0)),
        }
    return result


def get_video_stats(video_ids):
    if not video_ids:
        return {}
    data = yt_get("videos", {
        "part": "statistics,snippet",
        "id": ",".join(video_ids),
    })
    result = {}
    for item in data.get("items", []):
        vid  = item["id"]
        stat = item.get("statistics", {})
        snip = item.get("snippet", {})
        result[vid] = {
            "views":        int(stat.get("viewCount", 0)),
            "title":        snip.get("title", ""),
            "channel_id":   snip.get("channelId", ""),
            "channel_name": snip.get("channelTitle", ""),
            "published_at": snip.get("publishedAt", "")[:10],
        }
    return result


def is_review_video(title):
    return bool(REVIEW_RE.search(title))


def is_blocked_channel(name):
    return any(b.lower() in name.lower() for b in CHANNEL_BLOCKLIST)


def main():
    if not API_KEY:
        print("ERROR: YOUTUBE_API_KEY not set")
        return

    # channel_id -> {name, description, country, subscribers,
    #                 qualifying_videos: [{title, url, views, date}]}
    channels: dict = {}

    total_queries = 0
    for artist in ARTISTS:
        for suffix in SUFFIXES:
            query = f"{artist} {suffix}"
            print(f"  searching: {query!r}")
            items = search_videos(query)
            total_queries += 1

            # Batch video IDs for stats
            video_ids = [
                i["id"]["videoId"] for i in items
                if i.get("id", {}).get("kind") == "youtube#video"
            ]
            if not video_ids:
                time.sleep(0.3)
                continue

            vid_stats = get_video_stats(video_ids)
            for vid, vs in vid_stats.items():
                if not is_review_video(vs["title"]):
                    continue
                cid  = vs["channel_id"]
                cname = vs["channel_name"]
                if is_blocked_channel(cname):
                    continue
                if cid not in channels:
                    channels[cid] = {
                        "channel_id":  cid,
                        "channel_url": f"https://www.youtube.com/channel/{cid}",
                        "qualifying_videos": [],
                    }
                channels[cid]["qualifying_videos"].append({
                    "title": vs["title"],
                    "url":   f"https://www.youtube.com/watch?v={vid}",
                    "views": vs["views"],
                    "date":  vs["published_at"],
                })

            time.sleep(1.5)

        # Fetch channel stats in batches of 50
        if len(channels) % 50 == 0 and channels:
            print(f"  fetching stats for {len(channels)} channels so far...")
            batch = [cid for cid in channels if "subscribers" not in channels[cid]]
            for i in range(0, len(batch), 50):
                chunk = batch[i:i+50]
                stats = get_channel_stats(chunk)
                for cid, s in stats.items():
                    channels[cid].update(s)
                time.sleep(0.3)

    # Final stats fetch for any remaining channels
    remaining = [cid for cid in channels if "subscribers" not in channels[cid]]
    print(f"\nFetching stats for remaining {len(remaining)} channels...")
    for i in range(0, len(remaining), 50):
        chunk = remaining[i:i+50]
        stats = get_channel_stats(chunk)
        for cid, s in stats.items():
            channels[cid].update(s)
        time.sleep(0.3)

    # Build reviewer entries
    reviewers = []
    for cid, ch in channels.items():
        subs     = ch.get("subscribers", 0)
        desc     = ch.get("description", "")
        name     = ch.get("name", cid)
        vids     = ch.get("qualifying_videos", [])
        if not vids:
            continue
        if subs < MIN_SUBSCRIBERS:
            continue
        if OFF_TOPIC_DESC_RE.search(desc):
            continue

        views_list = [v["views"] for v in vids]
        avg_views  = int(sum(views_list) / len(views_list)) if views_list else 0
        if avg_views < MIN_AVG_VIEWS:
            continue

        top_video = sorted(vids, key=lambda v: v["views"], reverse=True)[0]
        sample    = sorted(vids, key=lambda v: v["views"], reverse=True)[:5]

        reviewers.append({
            "id":              re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"),
            "category":        "youtube",
            "name":            name,
            "url":             ch.get("channel_url", ""),
            "description":     desc,
            "indie_focus":     "unknown",
            "languages":       [],
            "genres":          [],
            "reach": {
                "subscribers":  subs,
                "avg_views":    avg_views,
                "video_count":  ch.get("video_count", 0),
            },
            "discovery_impact": round(avg_views / subs, 3) if subs else 0,
            "active":          True,
            "last_verified":   datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "country":         ch.get("country", ""),
            "socials":         {},
            "youtube_url":     ch.get("channel_url", ""),
            "pitch_to":        [],
            "content_types":   ["reaction", "review"],
            "top_review": {
                "title": top_video["title"],
                "url":   top_video["url"],
                "views": top_video["views"],
                "date":  top_video["date"],
            },
            "sample_reviews": [
                {"title": v["title"], "url": v["url"], "views": v["views"]}
                for v in sample
            ],
            "notes": f"{len(vids)} qualifying review/reaction videos found via artist search.",
        })

    # Sort by discovery_impact desc
    reviewers.sort(key=lambda r: r["discovery_impact"], reverse=True)
    for i, r in enumerate(reviewers, 1):
        r["rank"] = i

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "category":     "youtube",
        "total":        len(reviewers),
        "reviewers":    reviewers,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWritten → {OUTPUT_PATH}")
    print(f"  {len(reviewers)} qualifying YouTube reviewer channels")
    print(f"  {total_queries} API search queries used")


if __name__ == "__main__":
    main()
