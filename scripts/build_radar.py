#!/usr/bin/env python3
"""
Builds data/tracked_artists.json from indie YouTube artists + Last.fm enrichment.

Run after enrich_lastfm.py each day. Reads:
  data/latest.json          → indie artists + their genre/language
  data/lastfm_enrichment.json → Last.fm listener / India rank data
  data/tracked_artists.json   → previous snapshot (to compute growth trends)

Outputs: data/tracked_artists.json
"""

import json, os
from datetime import datetime, timezone
from collections import defaultdict

DATA_DIR     = os.path.join(os.path.dirname(__file__), "..", "data")
LATEST_PATH  = os.path.join(DATA_DIR, "latest.json")
LFM_PATH     = os.path.join(DATA_DIR, "lastfm_enrichment.json")
OUTPUT_PATH  = os.path.join(DATA_DIR, "tracked_artists.json")


def load_indie_artists():
    """Read unique artists from latest.json with genre/language from their top video."""
    try:
        with open(LATEST_PATH) as f:
            data = json.load(f)
    except Exception as e:
        print(f"  Could not read latest.json: {e}")
        return {}

    artists = {}
    for v in data.get("videos", []):
        ch   = v.get("channel", "")
        cid  = v.get("channel_id", "")
        lang = v.get("language") or "Hindi"
        genre = v.get("genre") or "Indie"
        key  = cid or ch
        if not key:
            continue
        if key not in artists:
            artists[key] = {"name": ch, "language": lang, "genre": genre, "channel_id": cid}
        else:
            # prefer the video's language/genre if not already set
            if artists[key]["genre"] == "Indie" and genre != "Indie":
                artists[key]["genre"] = genre
    return artists


def load_lfm_enrichment():
    try:
        with open(LFM_PATH) as f:
            data = json.load(f)
        return data.get("artists", {})
    except Exception:
        return {}


def load_prev_snapshot():
    """Load previous tracked_artists.json keyed by artist name for trend calc."""
    try:
        with open(OUTPUT_PATH) as f:
            data = json.load(f)
        return {a["name"]: a for a in data.get("artists", [])}
    except Exception:
        return {}


def calc_trend(prev_global, curr_global, prev_india_rank, curr_india_rank):
    """Return trend string and growth_pct based on listener and rank changes."""
    if prev_global is None or prev_global == 0:
        return "new", None

    growth_pct = round((curr_global - prev_global) / prev_global * 100, 1) if prev_global else None

    if growth_pct is not None and growth_pct >= 10:
        return "rising", growth_pct
    if growth_pct is not None and growth_pct <= -10:
        return "falling", growth_pct

    # If India rank improved significantly, call it rising even with small listener change
    if prev_india_rank and curr_india_rank and curr_india_rank < prev_india_rank - 5:
        return "rising", growth_pct

    return "stable", growth_pct


def main():
    print("Loading indie artists from latest.json...")
    indie = load_indie_artists()
    print(f"  {len(indie)} unique channels")

    print("Loading Last.fm enrichment...")
    lfm = load_lfm_enrichment()
    print(f"  {len(lfm)} artists enriched ({sum(1 for v in lfm.values() if v.get('global_listeners',0)>0)} with listener data)")

    print("Loading previous snapshot for trend calculation...")
    prev = load_prev_snapshot()
    print(f"  {len(prev)} previous entries")

    artists_out = []
    by_language = defaultdict(int)

    for key, info in indie.items():
        name  = info["name"]
        lang  = info["language"]
        genre = info["genre"]

        lfm_data = lfm.get(name, {})
        global_listeners = lfm_data.get("global_listeners", 0)
        india_listeners  = lfm_data.get("india_listeners", 0)
        india_rank       = lfm_data.get("india_rank", None)

        prev_entry = prev.get(name, {})
        prev_global = prev_entry.get("latest_global_listeners")
        prev_rank   = prev_entry.get("latest_india_rank")
        snap_count  = prev_entry.get("snapshot_count", 0) + 1

        trend, growth_pct = calc_trend(prev_global, global_listeners, prev_rank, india_rank)

        india_delta = None
        if prev_entry.get("latest_india_listeners") and india_listeners:
            india_delta = india_listeners - prev_entry["latest_india_listeners"]

        artists_out.append({
            "name":                  name,
            "channel_id":            info.get("channel_id", ""),
            "language":              lang,
            "genre":                 genre,
            "latest_india_listeners": india_listeners,
            "latest_india_rank":     india_rank,
            "latest_global_listeners": global_listeners,
            "snapshot_count":        snap_count,
            "growth_pct":            growth_pct,
            "india_delta":           india_delta,
            "trend":                 trend,
        })
        by_language[lang] += 1

    # Sort by global listeners desc
    artists_out.sort(key=lambda a: -(a["latest_global_listeners"] or 0))

    output = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total":       len(artists_out),
        "artists":     artists_out,
        "by_language": dict(by_language),
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    with_lfm = sum(1 for a in artists_out if a["latest_global_listeners"] > 0)
    on_chart  = sum(1 for a in artists_out if a["latest_india_rank"])
    print(f"\nWritten → {OUTPUT_PATH}")
    print(f"  {len(artists_out)} indie artists | {with_lfm} on Last.fm | {on_chart} on India chart")
    print(f"  By language: {dict(sorted(by_language.items(), key=lambda x:-x[1]))}")


if __name__ == "__main__":
    main()
