#!/usr/bin/env python3
"""
generate_monthly_digest.py — Build a monthly digest entry for the annual log.

Reads the current month's daily history snapshots + venue-history + tracked_artists
and writes/updates an entry in data/monthly-digest.json.

This script is idempotent: running it multiple times in the same month updates
the current month's entry in place. Past months are never touched.

Over time, data/monthly-digest.json becomes the foundation for year-end reporting:
who broke out, which cities had the most shows, which genres led, etc.

Run: python scripts/generate_monthly_digest.py
"""

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT   = Path(__file__).parent.parent
DATA_DIR    = REPO_ROOT / "data"
HISTORY_DIR = DATA_DIR / "history"
DIGEST_PATH = DATA_DIR / "monthly-digest.json"


def load_digest():
    if DIGEST_PATH.exists():
        try:
            return json.loads(DIGEST_PATH.read_text())
        except Exception:
            pass
    return {}


def save_digest(d):
    DIGEST_PATH.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def median(vals):
    if not vals:
        return None
    return round(statistics.median(vals), 1)


def load_month_history(month_prefix):
    """Load all daily history files for the given YYYY-MM prefix."""
    files = sorted(HISTORY_DIR.glob(f"{month_prefix}-*.json"))
    snapshots = []
    for f in files:
        try:
            snapshots.append(json.loads(f.read_text()))
        except Exception:
            continue
    return snapshots


def build_month_entry(month_str, snapshots):
    """
    Build a digest entry for month_str (e.g. '2026-05') from daily snapshots.
    Uses the most recent snapshot for point-in-time data, and aggregates
    across all snapshots for trend signals.
    """
    if not snapshots:
        return None

    latest = snapshots[-1]
    first  = snapshots[0]

    # ── Artist / video counts ─────────────────────────────────────────────────
    all_channels = {}  # channel_id -> best discovery_score this month
    all_new_channels = set()

    for snap in snapshots:
        for v in snap.get("videos", []):
            cid   = v.get("channel_id") or v.get("channel", "")
            name  = v.get("channel", "")
            score = v.get("discovery_score", 0) or 0
            views = v.get("views", 0) or 0
            genre = v.get("genre", "")
            lang  = v.get("language", "")
            if cid not in all_channels or score > all_channels[cid]["score"]:
                all_channels[cid] = {
                    "name": name, "score": score, "views": views,
                    "genre": genre, "language": lang,
                }
            if v.get("is_new"):
                all_new_channels.add(cid)

    # Use latest snapshot for aggregate breakdown
    latest_videos  = latest.get("videos", [])
    total_videos   = len(latest_videos)
    total_artists  = len(all_channels)
    new_artists    = len(all_new_channels)

    scores = [v.get("discovery_score", 0) for v in latest_videos if v.get("discovery_score")]
    views_list = [v.get("views", 0) for v in latest_videos if v.get("views")]

    # Top 10 artists by peak discovery score this month
    top_artists = sorted(
        [{"name": v["name"], "score": v["score"], "views": v["views"],
          "genre": v["genre"], "language": v["language"]}
         for v in all_channels.values()],
        key=lambda x: -x["score"]
    )[:10]

    # Genre and language breakdown (from latest snapshot)
    genre_breakdown = latest.get("genre_breakdown", [])
    lang_breakdown  = latest.get("language_breakdown", [])

    # ── Views delta (growth from first to last snapshot) ──────────────────────
    first_views = {v.get("channel_id") or v.get("channel", ""): v.get("views", 0)
                   for v in first.get("videos", [])}
    fastest_growing = []
    for v in latest_videos:
        cid   = v.get("channel_id") or v.get("channel", "")
        delta = (v.get("views", 0) or 0) - (first_views.get(cid, 0) or 0)
        if delta > 0:
            fastest_growing.append({
                "name": v.get("channel", ""),
                "views_gained": delta,
                "genre": v.get("genre", ""),
                "language": v.get("language", ""),
            })
    fastest_growing.sort(key=lambda x: -x["views_gained"])
    fastest_growing = fastest_growing[:5]

    # ── Venue / city shows ────────────────────────────────────────────────────
    venue_history_path = DATA_DIR / "venue-history.json"
    city_shows = {}
    if venue_history_path.exists():
        try:
            vh = json.loads(venue_history_path.read_text())
            # Use the most recent snapshot that falls in this month
            for snap in reversed(vh):
                if snap.get("date", "").startswith(month_str):
                    for city, venues in snap.get("cities", {}).items():
                        city_shows[city] = sum(
                            v.get("shows", 0) for v in venues.values()
                        )
                    break
        except Exception:
            pass

    top_city = max(city_shows, key=city_shows.get) if city_shows else None

    # ── Assemble entry ────────────────────────────────────────────────────────
    return {
        "month":             month_str,
        "snapshots":         len(snapshots),
        "last_snapshot_at":  latest.get("fetched_at", ""),
        "total_videos":      total_videos,
        "total_artists":     total_artists,
        "new_artists_seen":  new_artists,
        "median_score":      median(scores),
        "median_views":      median(views_list),
        "top_artists":       top_artists,
        "fastest_growing":   fastest_growing,
        "genre_breakdown":   genre_breakdown,
        "language_breakdown": lang_breakdown,
        "city_shows":        city_shows,
        "top_city":          top_city,
        "total_shows":       sum(city_shows.values()),
    }


def main():
    now        = datetime.now(timezone.utc)
    month_str  = now.strftime("%Y-%m")

    print(f"Generating monthly digest for {month_str}...")

    snapshots = load_month_history(month_str)
    if not snapshots:
        print(f"  No history snapshots found for {month_str} — skipping")
        return

    print(f"  {len(snapshots)} daily snapshots found")

    entry = build_month_entry(month_str, snapshots)
    if not entry:
        print("  Could not build entry — skipping")
        return

    digest = load_digest()
    digest[month_str] = entry

    save_digest(digest)

    print(f"  Written to monthly-digest.json")
    print(f"  {len(digest)} months logged so far: {', '.join(sorted(digest.keys()))}")
    print(f"  Top artist this month: {entry['top_artists'][0]['name']} (score {entry['top_artists'][0]['score']}) " if entry['top_artists'] else "")
    print(f"  Top city for shows: {entry['top_city']} ({entry['city_shows'].get(entry['top_city'], 0)} shows)" if entry['top_city'] else "  No venue data yet")


if __name__ == "__main__":
    main()
