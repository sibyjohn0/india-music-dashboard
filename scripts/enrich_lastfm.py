#!/usr/bin/env python3
"""
Enriches YouTube channel data with Last.fm listener stats.
Uses artist.search to find matches -- channel names don't match Last.fm directly.
Reads:  data/latest.json
Writes: data/lastfm_enrichment.json
"""
import os, json, time, sys
import urllib.request, urllib.parse
from datetime import datetime, timezone

LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY", "")
if not LASTFM_API_KEY:
    print("LASTFM_API_KEY not set — skipping enrichment", file=sys.stderr)
    sys.exit(0)

# Strip these words from channel names before searching Last.fm
STRIP_WORDS = {
    "official", "music", "records", "vevo", "channel", "hd", "india",
    "entertainment", "studio", "studios", "productions", "tv", "media",
    "the", "a", "and", "of", "in",
}


def lastfm_get(method, params={}):
    p = {"method": method, "api_key": LASTFM_API_KEY, "format": "json", **params}
    url = "https://ws.audioscrobbler.com/2.0/?" + urllib.parse.urlencode(p)
    try:
        return json.loads(urllib.request.urlopen(url, timeout=10).read())
    except Exception:
        return {}


def normalize(name):
    words = [w for w in name.lower().split() if w not in STRIP_WORDS]
    return " ".join(words).strip()


def name_similarity(a, b):
    """Simple overlap ratio for artist name matching."""
    a_words = set(a.lower().split())
    b_words = set(b.lower().split())
    if not a_words or not b_words:
        return 0.0
    overlap = len(a_words & b_words)
    return overlap / max(len(a_words), len(b_words))


def find_lastfm_match(channel_name):
    """Search Last.fm for artist, return (matched_name, listeners) or None."""
    norm = normalize(channel_name)
    if not norm:
        return None

    # Try direct lookup first (fast path for well-known names)
    info = lastfm_get("artist.getInfo", {"artist": channel_name})
    stats = info.get("artist", {}).get("stats", {})
    listeners = int(stats.get("listeners", 0))
    if listeners > 100:
        return (channel_name, listeners, int(stats.get("playcount", 0)))

    # Fall back: search by normalized name
    res = lastfm_get("artist.search", {"artist": norm, "limit": 5})
    candidates = (res.get("results", {})
                     .get("artistmatches", {})
                     .get("artist", []))
    for c in candidates:
        if name_similarity(norm, c["name"]) >= 0.7:
            c_listeners = int(c.get("listeners", 0))
            if c_listeners > 100:
                return (c["name"], c_listeners, 0)

    return None


def main():
    if not os.path.exists("data/latest.json"):
        print("data/latest.json not found", file=sys.stderr)
        sys.exit(1)

    with open("data/latest.json") as f:
        data = json.load(f)

    channels = {}
    for v in data.get("videos", []):
        name = v["channel"]
        if name not in channels:
            channels[name] = v.get("channel_id", "")

    print(f"Fetching Last.fm India top 100...")
    res = lastfm_get("geo.getTopArtists", {"country": "india", "limit": 100})
    india_chart = {}
    for i, a in enumerate(res.get("topartists", {}).get("artist", []), 1):
        india_chart[normalize(a["name"])] = {"rank": i, "india_listeners": int(a["listeners"])}

    enrichment = {}
    matched = 0

    for i, channel_name in enumerate(channels, 1):
        match = find_lastfm_match(channel_name)
        india_key = normalize(channel_name)
        india = india_chart.get(india_key, {})

        if match:
            _, global_listeners, global_playcount = match
            enrichment[channel_name] = {
                "global_listeners": global_listeners,
                "global_playcount": global_playcount,
                "india_listeners":  india.get("india_listeners", 0),
                "india_rank":       india.get("rank", None),
            }
            matched += 1
            print(f"  [{i}/{len(channels)}] MATCH {channel_name} — {global_listeners:,} listeners")
        else:
            enrichment[channel_name] = {
                "global_listeners": 0,
                "global_playcount": 0,
                "india_listeners":  india.get("india_listeners", 0),
                "india_rank":       india.get("rank", None),
            }

        time.sleep(0.2)

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "artists":    enrichment,
    }
    with open("data/lastfm_enrichment.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone: {matched}/{len(channels)} matched → data/lastfm_enrichment.json")


if __name__ == "__main__":
    main()
