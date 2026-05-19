#!/usr/bin/env python3
"""
Enriches YouTube channel data with Last.fm listener stats.
Reads:  data/latest.json
Writes: data/lastfm_enrichment.json
"""
import os, json, time, sys
import urllib.request, urllib.parse
from datetime import datetime, timezone

LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY", "0691809d6a805ec62ecdc12739435bb9")
# Words that appear in YouTube channel names but not Last.fm artist names
STRIP_WORDS = {"official", "music", "records", "vevo", "channel", "hd", "india",
               "entertainment", "studio", "studios", "productions", "tv", "media"}


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


def main():
    if not os.path.exists("data/latest.json"):
        print("data/latest.json not found — run fetch_youtube.py first", file=sys.stderr)
        sys.exit(1)

    with open("data/latest.json") as f:
        data = json.load(f)

    # Unique channels from YouTube data
    channels = {}
    for v in data.get("videos", []):
        name = v["channel"]
        if name not in channels:
            channels[name] = v.get("channel_id", "")

    # Fetch India top 100 once for rank + india-specific listeners
    print("Fetching Last.fm India top 100...")
    res = lastfm_get("geo.getTopArtists", {"country": "india", "limit": 100})
    india_chart = {}
    for i, a in enumerate(res.get("topartists", {}).get("artist", []), 1):
        key = normalize(a["name"])
        india_chart[key] = {"rank": i, "india_listeners": int(a["listeners"])}

    enrichment = {}
    total = len(channels)
    matched = 0

    for i, channel_name in enumerate(channels, 1):
        norm = normalize(channel_name)

        info = lastfm_get("artist.getInfo", {"artist": channel_name})
        stats = info.get("artist", {}).get("stats", {})
        global_listeners = int(stats.get("listeners", 0))
        global_playcount = int(stats.get("playcount", 0))

        india = india_chart.get(norm) or india_chart.get(channel_name.lower(), {})

        enrichment[channel_name] = {
            "global_listeners": global_listeners,
            "global_playcount": global_playcount,
            "india_listeners":  india.get("india_listeners", 0),
            "india_rank":       india.get("rank", None),
        }

        status = f"rank #{india['rank']}" if india else f"{global_listeners:,} global lstnrs"
        print(f"  [{i}/{total}] {channel_name} — {status}")
        if global_listeners > 0:
            matched += 1

        time.sleep(0.15)

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "artists":    enrichment,
    }
    with open("data/lastfm_enrichment.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone: {matched}/{total} channels matched on Last.fm → data/lastfm_enrichment.json")


if __name__ == "__main__":
    main()
