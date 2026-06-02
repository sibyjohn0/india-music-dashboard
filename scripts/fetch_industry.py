#!/usr/bin/env python3
"""
fetch_industry.py — Rebuild data/industry.json from the music-industry-db CSV.

Fetches music_database_clean.csv from github.com/sibyjohn0/music-industry-db,
groups rows by entity name, and writes data/industry.json preserving the
structure the industry/ page expects.

Output: data/industry.json
"""

import csv, io, json, sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("ERROR: pip install requests")

CSV_URL = (
    "https://raw.githubusercontent.com/sibyjohn0/music-industry-db/main/"
    "music_database_clean.csv"
)
OUT     = Path(__file__).parent.parent / "data" / "industry.json"
ED_FILE = Path(__file__).parent.parent / "data" / "industry-editorial.json"


def load_editorial():
    if ED_FILE.exists():
        return json.loads(ED_FILE.read_text())
    return {}


def fetch_csv():
    r = requests.get(CSV_URL, timeout=30)
    r.raise_for_status()
    return list(csv.DictReader(io.StringIO(r.text)))


def build_entities(rows):
    entities = {}
    for row in rows:
        name    = (row.get("Agency/Label Name") or "").strip()
        etype   = (row.get("Entity Type") or "").strip()
        country = (row.get("Country") or "").strip()
        artist  = (row.get("Artist Name") or "").strip()
        email   = (row.get("Contact/A&R Email") or "").strip()
        website = (row.get("Website") or "").strip()
        source  = (row.get("Source") or "").strip()
        note    = (row.get("Notes") or "").strip()

        if not name:
            continue

        if name not in entities:
            entities[name] = {
                "name":    name,
                "type":    etype,
                "country": country,
                "artists": [],
                "website": website,
                "source":  source,
                "emails":  [],
            }

        # update website/email if not yet set
        if website and not entities[name]["website"]:
            entities[name]["website"] = website
        if email and email not in entities[name]["emails"]:
            entities[name]["emails"].append(email)

        if artist:
            entry = {"name": artist}
            if note:
                entry["note"] = note
            # avoid duplicates
            if not any(a["name"] == artist for a in entities[name]["artists"]):
                entities[name]["artists"].append(entry)

    return list(entities.values())


def main():
    print("Fetching music-industry-db CSV…")
    try:
        rows = fetch_csv()
    except Exception as e:
        print(f"  ERROR fetching CSV: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"  {len(rows)} rows")
    entities = build_entities(rows)

    india_count = sum(1 for e in entities if (e.get("country") or "").lower() == "india")

    out = {
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "total_entities": len(entities),
        "india_count":    india_count,
        "entities":       entities,
    }

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"  OK — {len(entities)} entities ({india_count} India) → industry.json")


if __name__ == "__main__":
    main()
