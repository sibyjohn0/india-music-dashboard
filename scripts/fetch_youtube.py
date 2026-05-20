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

BASE               = "https://www.googleapis.com/youtube/v3"
REGION             = "IN"
MUSIC_CATEGORY     = "10"
INDIA_MUSIC_CPM_INR = 80
LOOKBACK_DAYS      = 90
SEARCH_MAX_RESULTS = 25                 # up from 15 — more candidates per query
MAX_VIEWS          = 3_000_000          # ignore already-established artists
MIN_VIEWS          = 1_000              # ignore brand-new / zero-traction uploads
TARGET_PER_LANGUAGE = 12               # max videos per language in final output
MAX_PER_CHANNEL    = 3                 # max videos from one channel per language bucket

# ── Label / distribution company blocklist ────────────────────
# Checked against CHANNEL NAME and TAGS only (not description).
MAJOR_LABELS = [
    # Pan-India majors
    "t-series", "tseries", "saregama", "sony music", "zee music",
    "tips music", "eros now", "eros music", "yrf", "junglee music",
    "dharma", "jiocinema", "jiosaavn", "hungama", "gaana",
    "warner music india", "universal music india", "emi music india",
    "times music", "ultra music", "vee music", "divo music",
    "reliance entertainment", "maddock music", "excel music",
    "balaji music", "goldmines", "wavemusic", "wave music",
    # Hindi / Bollywood
    "shemaroo", "venus music", "magnasound", "viacom18",
    "zee studios", "tips official", "bb ki vines",
    # Punjabi
    "speed records", "desi music factory", "white hill music",
    "saga music", "anand audio", "punjabi hits", "t-series apna punjab",
    # Tamil
    "think music india", "think music", "sun music", "star vijay",
    "agi music", "amigo films", "kalaignar tv", "trident arts",
    "muzik entertainment",
    # Telugu
    "aditya music", "lahari music", "etv music",
    "gemini music", "svr music", "sithara entertainments",
    # Malayalam
    "muzik247", "nu motion", "central pictures", "global one music",
    # Kannada
    "raj music", "raj digital", "kannada filmy", "anand audio kannada",
    # Bengali
    "eskay music", "shree venkatesh", "sv films", "echo bengali",
    # Marathi
    "zee marathi", "colors marathi", "sony marathi",
]

# ── Known mainstream artists ──────────────────────────────────
# Checked against CHANNEL NAME only.
MAINSTREAM_ARTISTS = [
    # Hindi mainstream vocalists / composers
    "arijit singh", "atif aslam", "shreya ghoshal", "sonu nigam",
    "jubin nautiyal", "armaan malik", "neha kakkar", "tony kakkar",
    "darshan raval", "guru randhawa", "b praak", "asees kaur",
    "palak muchhal", "udit narayan", "kumar sanu", "alka yagnik",
    "mohit chauhan", "shaan", "kk official", " kk ", "krishnakumar kunnath",
    "sunidhi chauhan", "kavita krishnamurthy",
    # Bollywood composers
    "pritam", "vishal-shekhar", "shankar ehsaan loy", "amit trivedi",
    "a.r. rahman", "ar rahman",
    # Hindi rap / hip-hop mainstream
    "badshah", "honey singh", "yo yo honey singh", "raftaar",
    "divine", "naezy", "mc stan", "ikka", "emiway bantai",
    "brodha v", "enkore",
    # Punjabi mainstream
    "diljit dosanjh", "hardy sandhu", "jassi gill", "mankirt aulakh",
    "g khan", "surjit bindrakhia", "sidhu moosewala", "ap dhillon",
    # Tamil mainstream
    "anirudh ravichander", "harris jayaraj", "devi sri prasad",
    "yuvan shankar raja", "sid sriram", "vijay antony", "spb",
    "s.p. balasubrahmanyam", "karthik singer",
    # Telugu mainstream
    "s thaman", "s. thaman", "thaman s",
    # Malayalam mainstream
    "bijibal", "vidyasagar", "m jayachandran",
    # Compilation / soundtrack signals in channel name
    "bollywood", "filmi", "film songs",
]

# ── Compilation / fan channel patterns ────────────────────────
COMPILATION_PATTERNS = [
    "jukebox", "24x7", "all songs", "best of", "top songs",
    "hit songs", "old songs", "love songs", "sad songs",
    "nonstop", "mashup", "remix collection", "audio jukebox",
    "love junction", "filmi gaane", "status video", "whatsapp status",
    "devotional songs", "christian songs", "bible songs",
]

# ── Devotional / religious channel blocklist ──────────────────
# Checked against channel name. These are not indie artists.
DEVOTIONAL_PATTERNS = [
    "church", "ministry", "worship", "devotional", "christian songs",
    "bible", "gospel", "jesus", "praise and", "prayer", "holy spirit",
    "lord songs", "god songs", "spiritual songs", "hymn",
    "islamic", "quran", "namaz", "bhajan", "aarti", "mandir",
    "temple songs", "pooja songs", "satsang",
]

# ── Title-level spam filter ───────────────────────────────────
TITLE_SPAM = [
    "type beat", "free beat", "instrumental beat", "rap beat", "trap beat",
    "hip hop beat", "drill beat", "beats free", "prod by",
    "distribution", "artist management", "music promotion", "submit your",
    "how to get", "music business", "grow your channel",
    "reaction video", "react to", "interview with",
    "whatsapp status", "status song", "ringtone",
    "christian devotional", "worship song", "devotional song",
    "praise and worship", "church live",
]

# ── Channel name patterns that signal an aggregator (not an artist) ──
AGGREGATOR_PATTERNS = [
    " songs",        # "Tamil Christian Songs", "Malayalam Songs"
    " music studio", # "Chengalpattu Music Studio"
    "lyrics channel",
    "fact ", "facts ",
    "song lyrics",
    "music zone", "music world", "music hub", "music factory",
    "hits official", "audio official",
]

# ── Language-first search structure ──────────────────────────
# Year removed from queries — publishedAfter parameter handles the window.
# Under-represented languages get more varied queries to find more candidates.
LANGUAGE_SEARCHES = {
    "Tamil": [
        ("tamil indie original song", "date"),
        ("independent tamil artist music", "date"),
        ("new tamil singer songwriter", "rating"),
        ("tamil underground music original", "date"),
        ("chennai indie music", "rating"),
    ],
    "Telugu": [
        ("telugu indie original song", "date"),
        ("independent telugu music artist", "date"),
        ("new telugu singer songwriter", "rating"),
        ("hyderabad indie music", "date"),
        ("telugu alternative music original", "rating"),
    ],
    "Kannada": [
        ("kannada indie music original", "date"),
        ("new independent kannada artist", "rating"),
        ("bangalore indie music kannada", "date"),
        ("karnataka indie singer original", "rating"),
        ("kannada folk indie song", "date"),
    ],
    "Malayalam": [
        ("malayalam indie original music", "date"),
        ("new independent malayalam artist", "rating"),
        ("kerala indie music original", "date"),
        ("malayalam alternative song independent", "rating"),
        ("malayalam singer songwriter", "date"),
    ],
    "Bengali": [
        ("bengali indie original song", "date"),
        ("bangla independent music artist", "date"),
        ("new bengali singer songwriter", "rating"),
        ("kolkata indie music original", "date"),
        ("bangladeshi indie song original", "rating"),
    ],
    "Punjabi": [
        ("punjabi indie original song", "date"),
        ("independent punjabi artist music", "rating"),
        ("new punjabi singer independent", "date"),
        ("punjabi underground music original", "date"),
    ],
    "Marathi": [
        ("marathi indie original song", "date"),
        ("new independent marathi artist", "rating"),
        ("pune indie music marathi", "date"),
        ("maharashtra indie singer original", "rating"),
        ("marathi singer songwriter", "date"),
    ],
    "Hindi": [
        ("hindi indie original song", "date"),
        ("hindi underground rap original", "date"),
        ("hindi bedroom pop singer songwriter", "date"),
        ("hindi indie artist unsigned", "rating"),
        ("delhi indie music original", "date"),
        ("mumbai indie music original", "date"),
    ],
    "English": [
        ("indian english indie band original", "date"),
        ("india english singer songwriter original", "date"),
        ("indian indie rock original", "rating"),
        ("indian english alternative music", "date"),
    ],
}

# ── Cross-genre / collective searches ────────────────────────
GENRE_SEARCHES = [
    ("Azadi Records", "date"),
    ("CARCOSA music india", "date"),
    ("when chai met toast", "date"),
    ("Indian jazz original music", "date"),
    ("Indian electronic original music", "date"),
    ("desi hip hop new artist", "date"),
    ("Indian folk fusion original", "date"),
    ("Indian lo-fi original", "date"),
    ("Indian bedroom pop original", "date"),
]


def get(endpoint, params):
    params["key"] = API_KEY
    url = f"{BASE}/{endpoint}?{urlencode(params)}"
    try:
        with urlopen(url) as r:
            return json.loads(r.read())
    except HTTPError as e:
        print(f"HTTP {e.code} on {endpoint} q={params.get('q','?')[:40]}", file=sys.stderr)
        return {}


def fetch_search_ids(query, order="date"):
    published_after = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%dT00:00:00Z")
    data = get("search", {
        "part":            "id",
        "q":               query,
        "type":            "video",
        "videoCategoryId": MUSIC_CATEGORY,
        "regionCode":      REGION,
        "order":           order,
        "maxResults":      SEARCH_MAX_RESULTS,
        "publishedAfter":  published_after,
    })
    return [i["id"]["videoId"] for i in data.get("items", []) if "videoId" in i.get("id", {})]


def fetch_video_details(ids):
    if not ids:
        return []
    items = []
    for i in range(0, len(ids), 50):
        data = get("videos", {"part": "snippet,statistics,contentDetails", "id": ",".join(ids[i:i+50])})
        items += data.get("items", [])
    return items


def detect_language(title, tags, description, hint=None):
    """hint is the LANGUAGE_SEARCHES key that found this video — trusted first."""
    if hint and hint in LANGUAGE_SEARCHES:
        return hint
    text = (title + " " + " ".join(tags) + " " + description).lower()
    checks = [
        ("Tamil",     ["tamil", "thamizh", "kollywood"]),
        ("Telugu",    ["telugu", "tollywood"]),
        ("Punjabi",   ["punjabi", "panjabi"]),
        ("Bengali",   ["bengali", "bangla"]),
        ("Kannada",   ["kannada", "sandalwood"]),
        ("Malayalam", ["malayalam", "mollywood"]),
        ("Marathi",   ["marathi"]),
        ("English",   ["indie rock", "alternative rock", "english indie"]),
    ]
    for lang, keywords in checks:
        if any(k in text for k in keywords):
            return lang
    return "Hindi"


def detect_genre(title, tags, description):
    text = (title + " " + " ".join(tags) + " " + description).lower()
    checks = [
        ("Lo-Fi",             ["lo-fi", "lofi", "lo fi", "chill beats", "study beats"]),
        ("Hip Hop / Rap",     ["hip hop", "hip-hop", "rap", "rapper", "trap", "drill", "freestyle"]),
        ("Jazz / Blues",      ["jazz", "blues", "fusion jazz", "swing"]),
        ("Folk / Acoustic",   ["folk", "acoustic", "unplugged", "sufi", "baul"]),
        ("Electronic",        ["electronic", "edm", "techno", "house", "ambient", "synthwave", "downtempo"]),
        ("R&B / Soul",        ["r&b", "rnb", "soul", "neo soul", "rhythm and blues"]),
        ("Indie Pop",         ["indie pop", "bedroom pop", "dream pop", "shoegaze"]),
        ("Rock / Alt",        ["rock", "metal", "punk", "alternative", "grunge", "post-rock"]),
        ("Classical/Fusion",  ["classical", "carnatic", "hindustani", "raag", "fusion classical"]),
    ]
    for genre, keywords in checks:
        if any(k in text for k in keywords):
            return genre
    return "Indie"


def discovery_score(views, engagement_rate, velocity, days_live):
    if views == 0:
        return 0
    # Engagement component: 5% engagement = max 40 pts (indie average is ~1-3%)
    eng = min(engagement_rate / 5.0, 1.0) * 40
    # Velocity component: 500 views/day = max 40 pts
    # Absolute benchmark — ratio was broken (always 100% on day 1)
    vel = min(velocity / 500, 1.0) * 40
    # Recency: up to 20 pts for videos under 30 days old
    recency = max(0, (30 - days_live) / 30) * 20 if days_live <= 30 else 0
    return round(eng + vel + recency, 1)


def is_blocked(channel, tags, title=""):
    ch  = channel.lower()
    tgs = " ".join(tags).lower()
    ttl = title.lower()
    if any(label in ch  for label in MAJOR_LABELS):           return True
    if any(label in tgs for label in MAJOR_LABELS):           return True
    if any(a     in ch  for a in MAINSTREAM_ARTISTS):         return True
    if any(pat   in ch  for pat in COMPILATION_PATTERNS):     return True
    if any(pat   in ch  for pat in DEVOTIONAL_PATTERNS):      return True
    if any(pat   in ch  for pat in AGGREGATOR_PATTERNS):      return True
    if any(spam  in ttl for spam in TITLE_SPAM):              return True
    return False


def parse_video(item, lang_hint=None):
    snip  = item.get("snippet", {})
    stats = item.get("statistics", {})
    now   = datetime.now(timezone.utc)

    views    = int(stats.get("viewCount", 0))
    likes    = int(stats.get("likeCount", 0))
    comments = int(stats.get("commentCount", 0))
    eng      = round((likes + comments) / views * 100, 2) if views > 0 else 0

    tags      = snip.get("tags", [])
    published = snip.get("publishedAt", "")
    desc      = snip.get("description", "")[:400]
    channel   = snip.get("channelTitle", "")
    days_live = max((now - datetime.fromisoformat(published.replace("Z", "+00:00"))).days, 1) if published else 1
    velocity  = round(views / days_live)

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
        "engagement_rate":  eng,
        "velocity":         velocity,
        "days_live":        days_live,
        "earnings_est_inr": round(views * INDIA_MUSIC_CPM_INR / 1000),
        "discovery_score":  discovery_score(views, eng, velocity, days_live),
        "language":         detect_language(snip.get("title",""), tags, desc, lang_hint),
        "genre":            detect_genre(snip.get("title",""), tags, desc),
        "tags":             tags[:20],
        "description":      desc,
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
            t = kw_count.get(tag.lower().strip(), 0)
            kw_count[tag.lower().strip()] = t + 1
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
        "month":               month_key,
        "last_updated":        date_str,
        "total_videos":        len(videos),
        "total_views":         sum(v["views"] for v in videos),
        "avg_discovery_score": round(sum(v["discovery_score"] for v in videos) / max(len(videos), 1), 1),
        "genre_breakdown":     genre_b,
        "language_breakdown":  lang_b,
        "top_channels":        sorted(top_channels.items(), key=lambda x: -x[1])[:10],
    }
    with open(f"data/monthly/{month_key}.json", "w") as f:
        json.dump(summary, f, indent=2)


def main():
    prev_views = load_prev_views()
    quota_used = 0
    quota_ok   = True

    # ── Phase 1: language-first searches ────────────────────────────────────
    id_to_lang = {}
    for lang, queries in LANGUAGE_SEARCHES.items():
        if not quota_ok:
            break                                   # fixed: exits outer loop too
        for query, order in queries:
            if quota_used + 100 > 8500:
                print(f"Quota cap at {quota_used} — stopping searches")
                quota_ok = False
                break
            for vid_id in fetch_search_ids(query, order):
                id_to_lang.setdefault(vid_id, lang)  # first language wins
            quota_used += 100

    # ── Phase 2: genre / collective searches ────────────────────────────────
    for query, order in GENRE_SEARCHES:
        if quota_used + 100 > 9000:
            break
        for vid_id in fetch_search_ids(query, order):
            id_to_lang.setdefault(vid_id, None)     # no language hint
        quota_used += 100

    unique_ids    = list(id_to_lang.keys())
    total_queries = sum(len(v) for v in LANGUAGE_SEARCHES.values()) + len(GENRE_SEARCHES)
    print(f"{len(unique_ids)} unique IDs from {total_queries} searches | quota ~{quota_used}")

    # ── Phase 3: enrich + filter ─────────────────────────────────────────────
    seen         = set()
    lang_buckets = {lang: [] for lang in LANGUAGE_SEARCHES}
    lang_buckets["Other"] = []

    for item in fetch_video_details(unique_ids):
        vid_id = item["id"]
        if vid_id in seen:
            continue
        seen.add(vid_id)

        lang_hint = id_to_lang.get(vid_id)
        v = parse_video(item, lang_hint)

        if is_blocked(v["channel"], v["tags"], v["title"]):
            continue
        if not (MIN_VIEWS <= v["views"] <= MAX_VIEWS):
            continue

        prev = prev_views.get(vid_id)
        v["views_delta"] = v["views"] - prev if prev is not None else None
        v["is_new"]      = prev is None

        bucket = v["language"] if v["language"] in lang_buckets else "Other"
        lang_buckets[bucket].append(v)

    # ── Phase 4: per-language balancing with per-channel cap ────────────────
    balanced = []
    for lang, vids in lang_buckets.items():
        vids.sort(key=lambda x: -x["discovery_score"])
        selected, ch_counts = [], {}
        for v in vids:
            ch = v.get("channel_id") or v["channel"]
            if ch_counts.get(ch, 0) >= MAX_PER_CHANNEL:
                continue
            ch_counts[ch] = ch_counts.get(ch, 0) + 1
            selected.append(v)
            cap = TARGET_PER_LANGUAGE if lang != "Other" else TARGET_PER_LANGUAGE // 2
            if len(selected) >= cap:
                break
        balanced.extend(selected)
        if vids:
            print(f"  {lang}: {len(selected)}/{len(vids)} selected")

    if not balanced:
        print("ERROR: 0 videos — refusing to overwrite", file=sys.stderr)
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
    print("Genres:    " + ", ".join(f"{g}:{c}" for g, c in genre_b))
    print("Languages: " + ", ".join(f"{l}:{c}" for l, c in lang_b))
    print("Top 5 by discovery score:")
    for v in balanced[:5]:
        print(f"  [{v['discovery_score']}] {v['channel']} — {v['title'][:55]} ({v['views']:,} views)")


if __name__ == "__main__":
    main()
