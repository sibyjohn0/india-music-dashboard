#!/usr/bin/env python3
"""
Merges all per-category reviewer files into a single data/reviewers.json.

Category files read:
  data/reviewers/editorial.json
  data/reviewers/youtube.json
  data/reviewers/spotify_curators.json
  data/reviewers/podcasts.json

Output: data/reviewers.json

Ranking within merged file:
  - editorial and podcasts sorted by indie_focus weight first, then name
  - youtube sorted by discovery_impact desc
  - spotify_curators sorted by followers desc
  - Final merged list: editorial > podcast > youtube > spotify (interleaved by quality tier)
"""

import json, os
from datetime import datetime, timezone

DATA_DIR    = os.path.join(os.path.dirname(__file__), "..", "data")
REVIEW_DIR  = os.path.join(DATA_DIR, "reviewers")
OUTPUT_PATH = os.path.join(DATA_DIR, "reviewers.json")

CATEGORY_FILES = {
    "editorial":        "editorial.json",
    "podcast":          "podcasts.json",
    "youtube":          "youtube.json",
    "spotify_curator":  "spotify_curators.json",
    "submithub":        "submithub.json",
}

INDIE_FOCUS_WEIGHT = {
    "very_high": 5,
    "high":      4,
    "medium":    3,
    "low_medium": 2,
    "low":       1,
    "unknown":   0,
}

CATEGORY_LABELS = {
    "editorial":       "Editorial & Blogs",
    "podcast":         "Podcasts",
    "youtube":         "YouTube Channels",
    "spotify_curator": "Spotify Curators",
    "submithub":       "SubmitHub Curators",
}


def load_category(category, filename):
    path = os.path.join(REVIEW_DIR, filename)
    if not os.path.exists(path):
        print(f"  [skip] {path} not found")
        return []
    with open(path) as f:
        data = json.load(f)
    entries = data.get("reviewers", [])
    for e in entries:
        e["category"] = category
    return entries


def quality_score(entry):
    base = INDIE_FOCUS_WEIGHT.get(entry.get("indie_focus", "unknown"), 0)
    category = entry.get("category", "")
    if category == "editorial":
        base += 3
    elif category == "podcast":
        base += 2
    elif category == "youtube":
        impact = entry.get("discovery_impact") or 0
        base += min(impact, 2)
    elif category == "spotify_curator":
        followers = (entry.get("reach") or {}).get("followers") or 0
        base += min(followers / 5000, 2)
    return base


def main():
    all_reviewers = []
    counts = {}

    for category, filename in CATEGORY_FILES.items():
        entries = load_category(category, filename)
        counts[category] = len(entries)
        all_reviewers.extend(entries)
        print(f"  {category}: {len(entries)} entries")

    # Sort by quality score desc
    all_reviewers.sort(key=quality_score, reverse=True)

    # Re-rank globally
    for i, r in enumerate(all_reviewers, 1):
        r["global_rank"] = i

    output = {
        "generated_at":  datetime.now(timezone.utc).isoformat(),
        "total":         len(all_reviewers),
        "by_category": {
            cat: {
                "label": CATEGORY_LABELS.get(cat, cat),
                "count": counts.get(cat, 0),
            }
            for cat in CATEGORY_FILES
        },
        "reviewers": all_reviewers,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWritten → {OUTPUT_PATH}")
    print(f"  {len(all_reviewers)} total reviewers across {len(counts)} categories")
    for cat, n in counts.items():
        print(f"    {CATEGORY_LABELS.get(cat, cat)}: {n}")


if __name__ == "__main__":
    main()
