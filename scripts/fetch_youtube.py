#!/usr/bin/env python3
import os, json, sys, math
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
LOOKBACK_DAYS = 90
SEARCH_MAX_RESULTS = 15
# Discovery filter: ignore videos already at scale (they don't need discovering)
MAX_VIEWS_FOR_DISCOVERY = 5_000_000

# ── Major label blocklist ─────────────────────────────────────
MAJOR_LABELS = [
    "t-series", "tseries", "saregama", "sony music", "zee music",
    "tips music", "eros now", "yrf", "dharma", "jiocinema",
    "warner music india", "universal music india", "emi music",
    "aditya music", "lahari music", "speed records",
    "desi music factory", "white hill music", "shemaroo",
    "venus music", "magnasound", "viacom18", "star vijay",
    "sun music", "etv music", "raj music", "think music india",
]

# ── Search queries — ordered by date to surface new talent ────
# Mix of: newest uploads (order=date) + high engagement (order=rating)
# Niche enough that major labels won't dominate results
DISCOVERY_SEARCHES = [
    # Genre + independent signals
    ("Indian bedroom pop", "date"),
    ("Indian lo-fi original song", "date"),
    ("Indian indie singer songwriter", "date"),
    ("Indian underground rap original", "date"),
    ("Indian jazz original music", "date"),
    ("Indian folk fusion original", "date"),
    ("Indian indie pop original song", "date"),
    ("Indian R&B original 2026", "date"),
    ("Indian electronic original music", "date"),
    ("Indian ambient original", "date"),
    ("desi hip hop new artist", "date"),
    ("Indian trap original beat", "date"),
    # Language-specific indie
    ("hindi indie original song", "date"),
    ("punjabi indie artist original", "date"),
    ("tamil indie original music", "date"),
    ("telugu indie original song", "date"),
    ("bengali indie original", "date"),
    ("kannada indie original music", "date"),
    ("malayalam indie original", "date"),
    ("marathi indie original song", "date"),
    # City scenes
    ("Mumbai underground music", "date"),
    ("Bangalore indie artist", "date"),
    ("Delhi underground hip hop", "date"),
    ("Kolkata indie music", "date"),
    # High-engagement discovery
    ("new Indian independent artist music", "rating"),
    ("Indian music producer original beat", "rating"),
    ("indie india new song", "rating"),
    ("unsigned indian artist music", "rating"),
    # Label/collective specific
    ("Azadi Records", "date"),
    ("Gully Gang new", "date"),
    ("CARCOSA music india", "date"),
    ("Indian music independent release", "rating"),
]


def get(endpoint, params):
    params["key"] = API_KEY
    url = f"{BASE}/{endpoint}?{urlencode(params)}"
    try:
        with urlopen(url) as r:
            return json.loads(r.read())
    except HTTPError as e:
        print(f"HTTP {e.code} — {url.split('?')[0]} q={params.get('q','')[:40]}", file=sys.stderr)
        return {}


def fetch_search_ids(query, order="date"):
    published_after = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%dT00:00:00Z")
    data = get("search", {
        "part": "id",
        "q": query,
        "type": "video",
        "videoCategoryId": MUSIC_CATEGORY,
        "regionCode": REGION,
        "order": order,
        "maxResults": SEARCH_MAX_RESULTS,
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
    checks = [
        ("Tamil",     ["tamil", "thamizh", "kollywood"]),
        ("Telugu",    ["telugu", "tollywood"]),
        ("Punjabi",   ["punjabi", "panjabi"]),
        ("Bengali",   ["bengali", "bangla"]),
        ("Kannada",   ["kannada", "sandalwood"]),
        ("Malayalam", ["malayalam", "mollywood"]),
        ("Marathi",   ["marathi"]),
    ]
    for lang, keywords in checks:
        if any(k in text for k in keywords):
            return lang
    return "Hindi"


def detect_genre(title, tags, description):
    text = (title + " " + " ".join(tags) + " " + description).lower()
    checks = [
        ("Lo-Fi",          ["lo-fi", "lofi", "lo fi", "chill beats", "study beats"]),
        ("Hip Hop / Rap",  ["hip hop", "hip-hop", "rap", "rapper", "trap", "drill", "freestyle"]),
        ("Jazz / Blues",   ["jazz", "blues", "fusion jazz", "swing"]),
        ("Folk / Acoustic",["folk", "acoustic", "unplugged", "sufi", "baul"]),
        ("Electronic",     ["electronic", "edm", "techno", "house", "ambient", "synthwave", "downtempo"]),
        ("R&B / Soul",     ["r&b", "rnb", "soul", "neo soul", "rhythm and blues"]),
        ("Indie Pop",      ["indie pop", "bedroom pop", "dream pop", "shoegaze"]),
        ("Rock / Alt",     ["rock", "metal", "punk", "alternative", "grunge", "post-rock"]),
        ("Classical/Fusion",["classical", "carnatic", "hindustani", "raag", "fusion classical"]),
    ]
    for genre, keywords in checks:
        if any(k in text for k in keywords):
            return genre
    return "Indie"


def discovery_score(views, engagement_rate, velocity, days_live):
    if views == 0:
        return 0
    # Engagement: rewards videos where a high % of viewers interact
    eng = min(engagement_rate / 5.0, 1.0) * 40
    # Velocity ratio: daily views as % of total — catches fast-rising unknown tracks
    vel_ratio = (velocity / max(views, 1)) * 100
    vel = min(vel_ratio * 8, 40)
    # Recency bonus: very new uploads get a boost
    recency = max(0, (45 - days_live) / 45) * 20 if days_live <= 45 else 0
    return round(eng + vel + recency, 1)


def is_major_label(channel, tags, desc):
    text = (channel + " " + " ".join(tags) + " " + desc).lower()
    return any(label in text for label in MAJOR_LABELS)


def parse_video(item):
    snip  = item.get("snippet", {})
    stats = item.get("statistics", {})
    now   = datetime.now(timezone.utc)

    views    = int(stats.get("viewCount", 0))
    likes    = int(stats.get("likeCount", 0))
    comments = int(stats.get("commentCount", 0))
    engagement = round((likes + comments) / views * 100, 2) if views > 0 else 0

    tags        = snip.get("tags", [])
    published   = snip.get("publishedAt", "")
    description = snip.get("description", "")[:400]
    channel     = snip.get("channelTitle", "")
    days_live   = max((now - datetime.fromisoformat(published.replace("Z", "+00:00"))).days, 1) if published else 1
    velocity    = round(views / days_live)

    return {
        "id":               item["id"],
        "title":            snip.get("title", ""),
        "channel":          channel,
        "channel_id":       snip.get("channelId", ""),
        "published_at":     published,
        "thumbnail":        snip.get("thumbnails", {}).get("medium", {}).get("url", ""),
        "views":            views,
        "likes":            likes,
        "comments":         comments,
        "engagement_rate":  engagement,
        "velocity":         velocity,
        "days_live":        days_live,
        "earnings_est_inr": round(views * INDIA_MUSIC_CPM_INR / 1000),
        "discovery_score":  discovery_score(views, engagement, velocity, days_live),
        "language":         detect_language(snip.get("title",""), tags, description),
        "genre":            detect_genre(snip.get("title",""), tags, description),
        "tags":             tags[:20],
        "description":      description,
        "url":              f"https://youtube.com/watch?v={item['id']}",
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
        genre_count[v["genre"]]   = genre_count.get(v["genre"], 0) + 1
        lang_count[v["language"]] = lang_count.get(v["language"], 0) + 1
        for tag in v["tags"]:
            t = tag.lower().strip()
            kw_count[t] = kw_count.get(t, 0) + 1
    return (
        sorted(genre_count.items(), key=lambda x: -x[1]),
        sorted(lang_count.items(),  key=lambda x: -x[1]),
        sorted(kw_count.items(),    key=lambda x: -x[1])[:60],
    )


def update_monthly_summary(videos, date_str):
    month_key = date_str[:7]
    os.makedirs("data/monthly", exist_ok=True)
    genre_b, lang_b, _ = build_breakdowns(videos)
    top_channels = {}
    for v in videos:
        top_channels[v["channel"]] = top_channels.get(v["channel"], 0) + 1
    summary = {
        "month":              month_key,
        "last_updated":       date_str,
        "total_videos":       len(videos),
        "total_views":        sum(v["views"] for v in videos),
        "avg_discovery_score":round(sum(v["discovery_score"] for v in videos) / max(len(videos),1), 1),
        "genre_breakdown":    genre_b,
        "language_breakdown": lang_b,
        "top_channels":       sorted(top_channels.items(), key=lambda x: -x[1])[:10],
    }
    with open(f"data/monthly/{month_key}.json", "w") as f:
        json.dump(summary, f, indent=2)


def main():
    prev_views = load_prev_views()
    seen, all_ids, quota_used = set(), [], 0

    for query, order in DISCOVERY_SEARCHES:
        if quota_used + 100 > 9000:
            print(f"Quota cap at {quota_used} — stopping")
            break
        all_ids += fetch_search_ids(query, order)
        quota_used += 100

    unique_ids = list(dict.fromkeys(all_ids))
    print(f"{len(unique_ids)} unique IDs from {len(DISCOVERY_SEARCHES)} searches | quota ~{quota_used}")

    videos = []
    for item in fetch_video_details(unique_ids):
        v = parse_video(item)
        if v["id"] in seen:
            continue
        if is_major_label(v["channel"], v["tags"], v["description"]):
            continue
        if v["views"] > MAX_VIEWS_FOR_DISCOVERY:
            continue                     # already established — skip
        seen.add(v["id"])
        prev = prev_views.get(v["id"])
        v["views_delta"] = v["views"] - prev if prev is not None else None
        v["is_new"] = prev is None
        videos.append(v)

    if len(videos) == 0:
        print("ERROR: 0 videos — refusing to overwrite (quota exhausted?)", file=sys.stderr)
        sys.exit(1)

    # Primary sort: discovery score
    videos.sort(key=lambda x: -x["discovery_score"])

    genre_b, lang_b, top_kw = build_breakdowns(videos)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output = {
        "fetched_at":         datetime.now(timezone.utc).isoformat(),
        "total":              len(videos),
        "quota_used_est":     quota_used,
        "lookback_days":      LOOKBACK_DAYS,
        "genre_breakdown":    genre_b,
        "language_breakdown": lang_b,
        "videos":             videos,
        "top_keywords":       [{"tag": k, "count": c} for k, c in top_kw],
    }

    os.makedirs("data/history", exist_ok=True)
    with open("data/latest.json", "w") as f:
        json.dump(output, f, indent=2)
    with open(f"data/history/{date_str}.json", "w") as f:
        json.dump(output, f, indent=2)

    update_monthly_summary(videos, date_str)

    print(f"Saved {len(videos)} artists — {date_str} | quota ~{quota_used}/10000")
    print("Genres: " + ", ".join(f"{g}:{c}" for g,c in genre_b))
    print("Top 5 by discovery score:")
    for v in videos[:5]:
        print(f"  [{v['discovery_score']}] {v['channel']} — {v['title'][:50]} ({v['views']:,} views, {v['engagement_rate']}% eng)")


if __name__ == "__main__":
    main()
