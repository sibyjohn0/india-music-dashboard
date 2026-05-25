#!/usr/bin/env python3
"""
Finds podcasts that cover Indian indie music.

Sources:
  1. iTunes Search API (free, no credentials)
  2. Curated known list of Indian music podcasts

Output: data/reviewers/podcasts.json
"""

import json, os, re, time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.parse import urlencode

DATA_DIR    = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "reviewers", "podcasts.json")

ITUNES_BASE = "https://itunes.apple.com/search"

PODCAST_QUERIES = [
    "india indie music",
    "indian music podcast",
    "indian independent music",
    "desi music podcast",
    "hindi music podcast",
    "tamil music podcast",
    "telugu music podcast",
    "kannada music",
    "bengali music podcast",
    "malayalam music podcast",
    "punjabi music podcast",
    "marathi music podcast",
    "indian hip hop podcast",
    "carnatic music podcast",
    "hindustani music podcast",
    "bollywood behind the scenes",
    "indian folk music",
    "desi artist interview",
    "indian music industry podcast",
    "south asian music podcast",
]

NOISE_RE = re.compile(
    r"\b(cricket|sports|politics|news|cooking|finance|yoga|meditation|"
    r"language learning|learn hindi|learn tamil|devotional|bhajan|prayer)\b",
    re.IGNORECASE,
)

MUSIC_RE = re.compile(
    r"\b(music|song|artist|band|singer|indie|album|playlist|track|"
    r"producer|musician|composer|guitar|drums|studio|record)\b",
    re.IGNORECASE,
)

INDIA_RE = re.compile(
    r"\b(india|indian|hindi|tamil|telugu|kannada|malayalam|bengali|"
    r"punjabi|marathi|desi|carnatic|hindustani|bollywood)\b",
    re.IGNORECASE,
)

# ── Curated known list (seed data beyond what iTunes returns) ──────────────────
CURATED = [
    {
        "id":          "maed-in-india",
        "name":        "Maed in India",
        "url":         "https://maedinindia.in",
        "itunes_url":  "https://podcasts.apple.com/in/podcast/maed-in-india/id978796980",
        "description": "India's longest-running independent music podcast. Weekly episodes featuring Indian indie music and artist interviews since 2014.",
        "indie_focus": "very_high",
        "languages":   ["English"],
        "genres":      ["Indie Pop", "Folk/Acoustic", "Electronic", "Hip Hop"],
        "pitch_to":    [{"label": "General", "contact": "contact@maed.in"}],
    },
    {
        "id":          "wild-city-podcast",
        "name":        "Wild City Podcast",
        "url":         "https://thewildcity.com/mixes",
        "itunes_url":  None,
        "description": "Mix series and artist sessions from Wild City. Focuses on electronic, experimental, and underground Indian music.",
        "indie_focus": "very_high",
        "languages":   ["English"],
        "genres":      ["Electronic", "Experimental", "Indie Pop"],
        "pitch_to":    [{"label": "Music submissions", "contact": "music@thewildcity.com"}],
    },
    {
        "id":          "the-music-run-down",
        "name":        "The Music Run Down",
        "url":         "https://open.spotify.com/show/the-music-run-down",
        "itunes_url":  None,
        "description": "Indian music news, reviews, and conversations with artists.",
        "indie_focus": "medium",
        "languages":   ["English", "Hindi"],
        "genres":      ["Indie Pop", "Rock", "Electronic"],
        "pitch_to":    [],
    },
]


def itunes_search(query, limit=200, country="IN"):
    params = {
        "term":    query,
        "media":   "podcast",
        "entity":  "podcast",
        "country": country,
        "limit":   limit,
    }
    url = f"{ITUNES_BASE}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "IndiaIndieMusicRadar/1.0"})
    try:
        with urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode()).get("results", [])
    except Exception as e:
        print(f"  iTunes error {query!r}: {e}")
        return []


def detect_languages(name, description):
    text = f"{name} {description}".lower()
    langs = []
    checks = {
        "Tamil":     ["tamil"],
        "Telugu":    ["telugu"],
        "Kannada":   ["kannada"],
        "Malayalam": ["malayalam"],
        "Bengali":   ["bengali", "bangla"],
        "Punjabi":   ["punjabi"],
        "Marathi":   ["marathi"],
        "Hindi":     ["hindi", "hindustani"],
    }
    for lang, kws in checks.items():
        if any(k in text for k in kws):
            langs.append(lang)
    if not langs:
        langs = ["English"]
    return langs


def is_relevant(name, description):
    text = f"{name} {description}"
    if NOISE_RE.search(text):
        return False
    return bool(MUSIC_RE.search(text) and INDIA_RE.search(text))


def main():
    seen_ids = set()
    reviewers = []

    # Start with curated seed list
    for entry in CURATED:
        seen_ids.add(entry["id"])
        reviewers.append({
            "id":       entry["id"],
            "category": "podcast",
            "name":     entry["name"],
            "url":      entry["url"],
            "description": entry["description"],
            "indie_focus": entry["indie_focus"],
            "languages":   entry["languages"],
            "genres":      entry.get("genres", []),
            "reach":       {"followers": None, "avg_views": None, "episode_count": None},
            "discovery_impact": None,
            "active":          True,
            "last_verified":   datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "socials":         {},
            "youtube_url":     None,
            "pitch_to":        entry.get("pitch_to", []),
            "content_types":   ["podcast_feature", "artist_interview"],
            "itunes_url":      entry.get("itunes_url"),
            "notes":           "Manually verified.",
        })

    # iTunes searches
    for query in PODCAST_QUERIES:
        print(f"  iTunes search: {query!r}")
        results = itunes_search(query)
        for r in results:
            name    = r.get("collectionName", "")
            desc    = r.get("description", "") or r.get("artistName", "")
            feed_id = str(r.get("collectionId", ""))
            if not name or not feed_id:
                continue
            if not is_relevant(name, desc):
                continue

            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            if slug in seen_ids or feed_id in seen_ids:
                continue
            seen_ids.add(slug)
            seen_ids.add(feed_id)

            reviewers.append({
                "id":          slug,
                "category":    "podcast",
                "name":        name,
                "url":         r.get("collectionViewUrl", ""),
                "description": desc[:300],
                "indie_focus": "unknown",
                "languages":   detect_languages(name, desc),
                "genres":      [],
                "reach": {
                    "followers":     None,
                    "avg_views":     None,
                    "episode_count": r.get("trackCount"),
                },
                "discovery_impact": None,
                "active":          True,
                "last_verified":   datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "socials":         {},
                "youtube_url":     None,
                "pitch_to":        [],
                "content_types":   ["podcast_feature"],
                "itunes_url":      r.get("collectionViewUrl"),
                "feed_url":        r.get("feedUrl"),
                "artwork_url":     r.get("artworkUrl600"),
                "artist_name":     r.get("artistName", ""),
                "episode_count":   r.get("trackCount"),
                "last_release":    (r.get("releaseDate") or "")[:10],
                "notes":           f"Found via iTunes search: {query!r}",
            })

        time.sleep(0.3)

    # Sort: curated first (manually verified), then by episode count desc
    curated_ids  = {e["id"] for e in CURATED}
    curated_set  = [r for r in reviewers if r["id"] in curated_ids]
    itunes_set   = [r for r in reviewers if r["id"] not in curated_ids]
    itunes_set.sort(key=lambda r: r.get("episode_count") or 0, reverse=True)
    reviewers = curated_set + itunes_set

    for i, r in enumerate(reviewers, 1):
        r["rank"] = i

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "category":     "podcast",
        "total":        len(reviewers),
        "reviewers":    reviewers,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWritten → {OUTPUT_PATH}")
    print(f"  {len(reviewers)} podcasts ({len(CURATED)} curated + {len(itunes_set)} from iTunes)")


if __name__ == "__main__":
    main()
