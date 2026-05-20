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
MAX_VIEWS_FOR_DISCOVERY = 3_000_000  # lower cap — truly indie artists
MIN_VIEWS_FOR_DISCOVERY = 300        # floor — ignore brand-new uploads with <300 views
TARGET_PER_LANGUAGE = 12             # hard cap per language in final output

# ── Label / distribution company blocklist ────────────────────
# Checked against CHANNEL NAME and TAGS only (not description, to avoid
# blocking indie artists who merely mention a label in their description).
MAJOR_LABELS = [
    # Pan-India majors
    "t-series", "tseries", "saregama", "sony music", "zee music",
    "tips music", "eros now", "eros music", "yrf", "junglee music",
    "dharma", "jiocinema", "jiosaavn", "hungama", "gaana",
    "warner music india", "universal music india", "emi music india",
    "times music", "ultra music", "vee music",
    "reliance entertainment", "maddock music", "excel music",
    "balaji music", "goldmines",
    # Hindi / Bollywood
    "shemaroo", "venus music", "magnasound", "viacom18",
    "zee studios", "tips official",
    # Punjabi
    "speed records", "desi music factory", "white hill music",
    "saga music", "a series", "anand music", "punjabi hits",
    # Tamil
    "think music india", "think music", "sun music", "star vijay",
    "agi music", "amigo films", "kalaignar tv",
    # Telugu
    "aditya music", "lahari music", "etv music", "manomayee",
    "gemini music", "svr music",
    # Malayalam
    "muzik247", "nu motion", "central pictures",
    # Kannada
    "raj music", "raj digital", "kannada filmy",
    # Bengali
    "eskay music", "shree venkatesh", "sv films",
]

# ── Known mainstream artists — blocked regardless of views ────
MAINSTREAM_ARTISTS = [
    # Hindi mainstream
    "arijit singh", "atif aslam", "shreya ghoshal", "sonu nigam",
    "jubin nautiyal", "armaan malik", "neha kakkar", "tony kakkar",
    "darshan raval", "guru randhawa", "b praak", "asees kaur",
    "palak muchhal", "udit narayan", "kumar sanu", "alka yagnik",
    # Rap / hip-hop mainstream
    "badshah", "honey singh", "yo yo honey singh", "raftaar",
    "divine", "naezy", "mc stan", "ikka", "emiway bantai",
    # Punjabi mainstream
    "diljit dosanjh", "hardy sandhu", "jassi gill", "mankirt aulakh",
    "jassie gill", "g khan", "surjit bindrakhia",
    # Tamil / Telugu mainstream (film composers)
    "anirudh ravichander", "harris jayaraj", "a.r. rahman", "ar rahman",
    "devi sri prasad", "s. thaman", "s thaman", "vishal-shekhar",
    "pritam", "shankar ehsaan loy", "amit trivedi",
    # Bollywood compilation / soundtrack channels
    "bollywood", "filmi", "film songs",
]

# ── Compilation / fan channel patterns ────────────────────────
COMPILATION_PATTERNS = [
    "jukebox", "24x7", "all songs", "best of", "top songs",
    "hit songs", "old songs", "love songs", "sad songs",
    "nonstop", "mashup", "remix collection", "audio jukebox",
    "love junction", "filmi gaane",
]

# ── Title-level spam / non-artist content signals ─────────────
# Checked against video TITLE only. Blocks beats, promos, ads.
TITLE_SPAM = [
    "type beat", "free beat", "instrumental beat", "rap beat", "trap beat",
    "hip hop beat", "drill beat", "beats free", "prod by",
    "distribution", "artist management", "music promotion", "submit your",
    "how to get", "music business", "grow your channel",
    "reaction video", "react to", "interview with",
]

# ── Language-first search structure ──────────────────────────
# Each language gets dedicated searches so no language is starved.
# Generic "Indian X" searches are removed — they overwhelmingly return Hindi.
LANGUAGE_SEARCHES = {
    "Tamil":     [
        ("tamil indie original song 2025", "date"),
        ("independent tamil artist music", "date"),
        ("new tamil singer songwriter", "rating"),
    ],
    "Telugu":    [
        ("telugu indie original song 2025", "date"),
        ("independent telugu music artist", "date"),
        ("new telugu singer songwriter", "rating"),
    ],
    "Kannada":   [
        ("kannada indie music original 2025", "date"),
        ("new independent kannada artist", "rating"),
    ],
    "Malayalam": [
        ("malayalam indie original music 2025", "date"),
        ("new independent malayalam artist", "rating"),
    ],
    "Bengali":   [
        ("bengali indie original song 2025", "date"),
        ("bangla independent music artist", "date"),
        ("new bengali singer songwriter", "rating"),
    ],
    "Punjabi":   [
        ("punjabi indie original song 2025", "date"),
        ("independent punjabi artist music", "rating"),
    ],
    "Marathi":   [
        ("marathi indie original song 2025", "date"),
        ("new independent marathi artist", "rating"),
    ],
    "Hindi":     [
        ("hindi indie original song 2025", "date"),
        ("hindi underground rap original", "date"),
        ("hindi bedroom pop singer songwriter", "date"),
        ("hindi indie artist unsigned 2025", "rating"),
    ],
    "English":   [
        ("indian english indie band original", "date"),
        ("india english singer songwriter original", "date"),
        ("indian indie rock original 2025", "rating"),
    ],
}

# ── Cross-genre searches (language-agnostic, capped separately) ──
GENRE_SEARCHES = [
    ("Indian jazz original music 2025", "date"),
    ("Indian electronic original music", "date"),
    ("desi hip hop new artist 2025", "date"),
    ("Indian folk fusion original 2025", "date"),
    ("Azadi Records", "date"),
    ("CARCOSA music india", "date"),
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


def detect_language(title, tags, description, hint=None):
    """hint is the LANGUAGE_SEARCHES key that produced this video."""
    if hint and hint in LANGUAGE_SEARCHES:
        return hint  # trust the search bucket
    text = (title + " " + " ".join(tags) + " " + description).lower()
    checks = [
        ("Tamil",     ["tamil", "thamizh", "kollywood"]),
        ("Telugu",    ["telugu", "tollywood"]),
        ("Punjabi",   ["punjabi", "panjabi"]),
        ("Bengali",   ["bengali", "bangla"]),
        ("Kannada",   ["kannada", "sandalwood"]),
        ("Malayalam", ["malayalam", "mollywood"]),
        ("Marathi",   ["marathi"]),
        ("English",   ["indie rock", "indie pop", "alternative rock", "english indie"]),
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
    # Absolute velocity: views/day vs indie benchmark (500 v/day = max points)
    # Ratio-based velocity was broken — day-1 videos always scored 100% regardless of size
    vel = min(velocity / 500, 1.0) * 40
    # Recency bonus: smaller boost for newness, so velocity+engagement carry the weight
    recency = max(0, (30 - days_live) / 30) * 20 if days_live <= 30 else 0
    return round(eng + vel + recency, 1)


def is_blocked(channel, tags, desc, title=""):
    channel_lower = channel.lower()
    tags_lower    = " ".join(tags).lower()
    title_lower   = title.lower()
    # Labels: channel name and tags only
    if any(label in channel_lower for label in MAJOR_LABELS):
        return True
    if any(label in tags_lower for label in MAJOR_LABELS):
        return True
    # Mainstream artists: channel name only
    if any(artist in channel_lower for artist in MAINSTREAM_ARTISTS):
        return True
    # Compilation / fan channels: channel name only
    if any(pat in channel_lower for pat in COMPILATION_PATTERNS):
        return True
    # Beat / promo / non-artist content: video title
    if any(spam in title_lower for spam in TITLE_SPAM):
        return True
    return False


def parse_video(item, lang_hint=None):
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
        "language":         detect_language(snip.get("title",""), tags, description, lang_hint),
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
    quota_used = 0

    # ── Phase 1: language-first searches ─────────────────────────────────────
    # Each language gets its own search bucket so no language is starved.
    # Videos are tagged with their source language at fetch time.
    id_to_lang = {}   # video_id → language hint
    for lang, queries in LANGUAGE_SEARCHES.items():
        for query, order in queries:
            if quota_used + 100 > 8500:
                print(f"Quota cap at {quota_used} — stopping early")
                break
            for vid_id in fetch_search_ids(query, order):
                if vid_id not in id_to_lang:
                    id_to_lang[vid_id] = lang
            quota_used += 100

    # ── Phase 2: genre / cross-language searches ──────────────────────────────
    genre_ids = []
    for query, order in GENRE_SEARCHES:
        if quota_used + 100 > 9000:
            break
        genre_ids += fetch_search_ids(query, order)
        quota_used += 100
    for vid_id in genre_ids:
        id_to_lang.setdefault(vid_id, None)   # no language hint

    unique_ids = list(id_to_lang.keys())
    total_searches = sum(len(v) for v in LANGUAGE_SEARCHES.values()) + len(GENRE_SEARCHES)
    print(f"{len(unique_ids)} unique IDs from {total_searches} searches | quota ~{quota_used}")

    # ── Phase 3: enrich + filter ──────────────────────────────────────────────
    seen = set()
    lang_buckets = {lang: [] for lang in LANGUAGE_SEARCHES}
    lang_buckets["Other"] = []

    for item in fetch_video_details(unique_ids):
        vid_id = item["id"]
        if vid_id in seen:
            continue
        lang_hint = id_to_lang.get(vid_id)
        v = parse_video(item, lang_hint)

        if is_blocked(v["channel"], v["tags"], v["description"], v["title"]):
            continue
        if v["views"] < MIN_VIEWS_FOR_DISCOVERY:
            continue
        if v["views"] > MAX_VIEWS_FOR_DISCOVERY:
            continue
        seen.add(vid_id)

        prev = prev_views.get(vid_id)
        v["views_delta"] = v["views"] - prev if prev is not None else None
        v["is_new"] = prev is None

        bucket = v["language"] if v["language"] in lang_buckets else "Other"
        lang_buckets[bucket].append(v)

    # ── Phase 4: per-language balancing ──────────────────────────────────────
    # Take top TARGET_PER_LANGUAGE by discovery score per language.
    # This guarantees no single language floods the results.
    balanced = []
    for lang, vids in lang_buckets.items():
        vids.sort(key=lambda x: -x["discovery_score"])
        cap = TARGET_PER_LANGUAGE if lang != "Other" else TARGET_PER_LANGUAGE // 2
        balanced.extend(vids[:cap])
        if vids:
            print(f"  {lang}: {min(len(vids), cap)}/{len(vids)} selected")

    if not balanced:
        print("ERROR: 0 videos after balancing — refusing to overwrite", file=sys.stderr)
        sys.exit(1)

    balanced.sort(key=lambda x: -x["discovery_score"])

    genre_b, lang_b, top_kw = build_breakdowns(balanced)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output = {
        "fetched_at":         datetime.now(timezone.utc).isoformat(),
        "total":              len(balanced),
        "quota_used_est":     quota_used,
        "lookback_days":      LOOKBACK_DAYS,
        "genre_breakdown":    genre_b,
        "language_breakdown": lang_b,
        "videos":             balanced,
        "top_keywords":       [{"tag": k, "count": c} for k, c in top_kw],
    }

    os.makedirs("data/history", exist_ok=True)
    with open("data/latest.json", "w") as f:
        json.dump(output, f, indent=2)
    with open(f"data/history/{date_str}.json", "w") as f:
        json.dump(output, f, indent=2)

    update_monthly_summary(balanced, date_str)

    print(f"\nSaved {len(balanced)} videos — {date_str} | quota ~{quota_used}/10000")
    print("Genres:    " + ", ".join(f"{g}:{c}" for g,c in genre_b))
    print("Languages: " + ", ".join(f"{l}:{c}" for l,c in lang_b))
    print("Top 5 by discovery score:")
    for v in balanced[:5]:
        print(f"  [{v['discovery_score']}] {v['channel']} — {v['title'][:50]} ({v['views']:,} views)")


if __name__ == "__main__":
    main()
