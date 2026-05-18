#!/usr/bin/env python3
import os, json, sys, re
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
INDIA_MUSIC_CPM_INR = 80
LOOKBACK_DAYS = 90        # only videos from the last 3 months
SEARCH_MAX_RESULTS = 10   # 10 per query × 33 queries = ~330 IDs, ~3,300 quota units/day (well under 10K limit)
QUOTA_BUDGET = 9000       # stop issuing new search calls once estimated usage hits this

# ── Major label blocklist ────────────────────────────────────
# Anything from these channels/strings is excluded entirely
MAJOR_LABEL_BLOCKLIST = [
    "t-series", "tseries", "saregama", "sony music", "zee music",
    "tips music", "eros now", "yrf", "dharma", "jiocinema",
    "warner music india", "universal music india", "emi music india",
    "think music india", "aditya music", "lahari music",
    "speed records", "desi music factory", "white hill music",
    "shemaroo", "venus", "magnasound", "sony liv", "viacom18",
    "star vijay", "sun music", "etv music", "raj music",
]

# ── Indie label / collective allowlist ───────────────────────
INDIE_LABELS = [
    "azadi records", "mass appeal india", "gully gang", "xtatic music",
    "almost music", "naya records", "black box", "put chutney",
    "when chai met toast", "peter cat recording", "the yellow diary",
    "when chai met", "dastaan music", "pagal haina", "the local train",
    "shankar tucker", "still listening", "underscore records",
    "the storytellers", "madboy mink", "parekh & singh",
]

# ── Search queries — all indie-focused ───────────────────────
INDIE_SEARCHES = [
    # Genre / format
    "Indian indie music 2026",
    "India bedroom pop 2026",
    "Indian lo-fi beats 2026",
    "Indian folk indie 2026",
    "Indian jazz fusion 2026",
    "Indian alternative music 2026",
    "Indian singer songwriter 2026",
    "Indian R&B artist 2026",
    "Indian ambient music 2026",
    "India indie pop 2026",
    # Hip hop / rap
    "Indian underground hip hop 2026",
    "Indian independent rap 2026",
    "India trap music 2026",
    "desi hip hop independent",
    "Indian rapper independent 2026",
    # Electronic / production
    "Indian music producer 2026",
    "Indian producer type beat 2026",
    "India electronic music independent",
    "Indian lo-fi hip hop 2026",
    # Language-specific indie
    "indie hindi music 2026",
    "indie punjabi music 2026",
    "indie tamil music 2026",
    "indie bengali music 2026",
    "indie kannada music 2026",
    "indie malayalam music 2026",
    # City scenes
    "Mumbai indie music 2026",
    "Bangalore indie music 2026",
    "Delhi underground music 2026",
    # Labels / collectives
    "Azadi Records 2026",
    "Gully Gang music 2026",
    "independent artist india music",
    "unsigned artist india 2026",
    "self released india music 2026",
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


def fetch_search_ids(query, max_results=SEARCH_MAX_RESULTS):
    published_after = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%dT00:00:00Z")
    data = get("search", {
        "part": "id",
        "q": query,
        "type": "video",
        "videoCategoryId": MUSIC_CATEGORY,
        "regionCode": REGION,
        "order": "viewCount",
        "maxResults": max_results,
        "publishedAfter": published_after,
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


def detect_language(title, tags, description):
    text = (title + " " + " ".join(tags) + " " + description).lower()
    if any(w in text for w in ["tamil", "thamizh", "kollywood"]):
        return "Tamil"
    if any(w in text for w in ["telugu", "tollywood"]):
        return "Telugu"
    if any(w in text for w in ["punjabi", "panjabi"]):
        return "Punjabi"
    if any(w in text for w in ["bengali", "bangla"]):
        return "Bengali"
    if any(w in text for w in ["kannada", "sandalwood"]):
        return "Kannada"
    if any(w in text for w in ["malayalam", "mollywood"]):
        return "Malayalam"
    if any(w in text for w in ["marathi"]):
        return "Marathi"
    if any(w in text for w in ["hindi", "bollywood", "हिंदी"]):
        return "Hindi"
    return "Hindi"  # default for unlabelled Indian music


def detect_genre(title, tags, description):
    text = (title + " " + " ".join(tags) + " " + description).lower()
    if any(w in text for w in ["lo-fi", "lofi", "lo fi", "chill beats", "study beats"]):
        return "Lo-Fi"
    if any(w in text for w in ["hip hop", "hip-hop", "rap", "rapper", "trap", "drill"]):
        return "Hip Hop / Rap"
    if any(w in text for w in ["jazz", "blues", "fusion jazz"]):
        return "Jazz / Blues"
    if any(w in text for w in ["folk", "acoustic", "unplugged", "sufi"]):
        return "Folk / Acoustic"
    if any(w in text for w in ["electronic", "edm", "techno", "house", "ambient", "synthwave"]):
        return "Electronic"
    if any(w in text for w in ["r&b", "rnb", "soul", "neo soul"]):
        return "R&B / Soul"
    if any(w in text for w in ["pop", "indie pop", "bedroom pop"]):
        return "Indie Pop"
    if any(w in text for w in ["rock", "metal", "punk", "alternative", "grunge"]):
        return "Rock / Alt"
    if any(w in text for w in ["classical", "carnatic", "hindustani", "raag"]):
        return "Classical / Fusion"
    return "Indie"


def is_major_label(channel, tags, description):
    text = (channel + " " + " ".join(tags) + " " + description).lower()
    return any(label in text for label in MAJOR_LABEL_BLOCKLIST)


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
    description = snip.get("description", "")[:400]
    channel = snip.get("channelTitle", "")
    days_live = max((now - datetime.fromisoformat(published_at.replace("Z", "+00:00"))).days, 1) if published_at else 1

    return {
        "id": item["id"],
        "title": snip.get("title", ""),
        "channel": channel,
        "channel_id": snip.get("channelId", ""),
        "published_at": published_at,
        "thumbnail": snip.get("thumbnails", {}).get("medium", {}).get("url", ""),
        "views": views,
        "likes": likes,
        "comments": comments,
        "engagement_rate": engagement,
        "velocity": round(views / days_live),
        "earnings_est_inr": round(views * INDIA_MUSIC_CPM_INR / 1000),
        "language": detect_language(snip.get("title", ""), tags, description),
        "genre": detect_genre(snip.get("title", ""), tags, description),
        "tags": tags[:20],
        "description": description,
        "url": f"https://youtube.com/watch?v={item['id']}",
    }


def load_prev_views():
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    path = f"data/history/{yesterday}.json"
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return {v["id"]: v["views"] for v in json.load(f).get("videos", [])}


def build_breakdowns(videos):
    genre_count, lang_count, kw_count = {}, {}, {}
    for v in videos:
        genre_count[v["genre"]]    = genre_count.get(v["genre"], 0) + 1
        lang_count[v["language"]]  = lang_count.get(v["language"], 0) + 1
        for tag in v["tags"]:
            t = tag.lower().strip()
            kw_count[t] = kw_count.get(t, 0) + 1
    return (
        sorted(genre_count.items(), key=lambda x: -x[1]),
        sorted(lang_count.items(),  key=lambda x: -x[1]),
        sorted(kw_count.items(),    key=lambda x: -x[1])[:60],
    )


def update_monthly_summary(videos, date_str):
    month_key = date_str[:7]  # "YYYY-MM"
    os.makedirs("data/monthly", exist_ok=True)
    path = f"data/monthly/{month_key}.json"

    genre_count, lang_count, _ = build_breakdowns(videos)
    total_views = sum(v["views"] for v in videos)
    top_channels = {}
    for v in videos:
        c = v["channel"]
        top_channels[c] = top_channels.get(c, 0) + v["views"]
    top5_channels = sorted(top_channels.items(), key=lambda x: -x[1])[:5]

    # Merge with existing monthly data if present
    existing = {}
    if os.path.exists(path):
        with open(path) as f:
            existing = json.load(f)

    # Accumulate genre/lang counts across daily snapshots in this month
    # (just overwrite with latest day's snapshot — sufficient for MoM trends)
    summary = {
        "month": month_key,
        "last_updated": date_str,
        "total_videos": len(videos),
        "total_views": total_views,
        "genre_breakdown": genre_count,
        "language_breakdown": lang_count,
        "top_channels": top5_channels,
    }
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def main():
    seen = set()
    videos = []
    prev_views = load_prev_views()
    quota_used = 0

    all_ids = []
    for q in INDIE_SEARCHES:
        if quota_used + 100 > QUOTA_BUDGET:
            print(f"Quota budget reached at {quota_used} units — stopping searches early")
            break
        ids = fetch_search_ids(q)
        all_ids += ids
        quota_used += 100

    unique_ids = list(dict.fromkeys(all_ids))
    video_batches = (len(unique_ids) + 49) // 50
    quota_used += video_batches  # videos.list costs ~1 unit per 50
    print(f"Found {len(unique_ids)} unique IDs | est. quota used: {quota_used} units")

    for item in fetch_video_details(unique_ids):
        v = parse_video(item)
        if v["id"] in seen:
            continue
        if is_major_label(v["channel"], v["tags"], v["description"]):
            continue
        seen.add(v["id"])
        prev = prev_views.get(v["id"])
        v["views_delta"] = v["views"] - prev if prev is not None else None
        v["is_new"] = prev is None
        videos.append(v)

    videos.sort(key=lambda x: -x["views"])

    genre_breakdown, lang_breakdown, top_keywords = build_breakdowns(videos)

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total": len(videos),
        "quota_used_est": quota_used,
        "lookback_days": LOOKBACK_DAYS,
        "genre_breakdown": genre_breakdown,
        "language_breakdown": lang_breakdown,
        "videos": videos,
        "top_keywords": [{"tag": k, "count": c} for k, c in top_keywords],
    }

    if len(videos) == 0:
        print("ERROR: 0 videos fetched — refusing to overwrite existing data (likely quota exhausted)", file=sys.stderr)
        sys.exit(1)

    os.makedirs("data/history", exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open("data/latest.json", "w") as f:
        json.dump(output, f, indent=2)
    with open(f"data/history/{date_str}.json", "w") as f:
        json.dump(output, f, indent=2)

    update_monthly_summary(videos, date_str)

    genre_str = ", ".join(f"{g}:{c}" for g, c in genre_breakdown)
    print(f"Saved {len(videos)} indie videos — {date_str} | quota est: {quota_used}/10000")
    print(f"Genres: {genre_str}")


if __name__ == "__main__":
    main()
