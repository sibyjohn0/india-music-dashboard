#!/usr/bin/env python3
"""
fetch_skillboxes.py — Fetch music events from SkillBoxes (skillboxes.com).

API: POST https://www.skillboxes.com/servers/v3/api/event-new/get-event-new
Body: {"default_city": 1119023, "opcode": "search", "type": "fetchAll",
       "eventCityEnb": false, "page": N}

Paginates until next=false. Filters to music/concert/gig categories.

Output: data/events-skillboxes.json
"""

import json, os, sys, re, time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "events-skillboxes.json")
API_URL  = "https://www.skillboxes.com/servers/v3/api/event-new/get-event-new"
BASE_URL = "https://www.skillboxes.com"

MUSIC_KEYWORDS = {
    "music", "concert", "gig", "band", "live", "dj", "fest", "festival",
    "performance", "show", "club gig", "rave", "rock", "jazz", "indie",
    "hip hop", "electronic", "pop", "classical", "folk", "blues", "open mic",
    "jamming", "album", "listening session", "tribute",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://www.skillboxes.com",
    "Referer": "https://www.skillboxes.com/events",
}


def load_last_known():
    if os.path.exists(OUT):
        with open(OUT) as f:
            return json.load(f)
    return None


def post_json(url, payload):
    body = json.dumps(payload).encode("utf-8")
    req  = Request(url, data=body, headers=HEADERS, method="POST")
    with urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def is_music(item):
    category = (item.get("category") or "").lower()
    name     = (item.get("event_display_name") or item.get("event_name") or "").lower()
    subs     = " ".join(s.get("name", "") for s in item.get("subcategories", [])).lower()
    text     = f"{category} {name} {subs}"
    return any(kw in text for kw in MUSIC_KEYWORDS)


def parse_date(raw):
    """Convert '06 June 2026' to '2026-06-06'."""
    if not raw:
        return ""
    raw = str(raw).strip()
    for fmt in ("%d %B %Y", "%d %b %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw[:10]


def normalise(item):
    name  = item.get("event_display_name") or item.get("event_name") or ""
    slug  = item.get("slug") or ""
    url   = f"{BASE_URL}/events/{slug}" if slug else ""
    city  = item.get("city_name") or ""
    venue = item.get("venue_name") or ""
    raw_date = item.get("date") or item.get("event_date") or ""
    ev_date  = parse_date(raw_date)

    # Combine date and time for display purposes
    ev_time = item.get("event_time") or ""

    price_min = item.get("min_price")
    price_max = item.get("max_price")
    # price=0 on Skillboxes usually means "free" or "price TBA"
    if price_min == 0 and price_max and price_max > 0:
        price_min = None  # don't show 0 as floor

    return {
        "name":      name,
        "venue":     venue,
        "city":      city,
        "date":      ev_date,
        "time":      ev_time,
        "price_min": price_min if price_min else None,
        "price_max": price_max if price_max else None,
        "url":       url,
    }


def fetch_all():
    all_items = []
    page = 1
    while True:
        payload = {
            "default_city":  1119023,
            "opcode":        "search",
            "type":          "fetchAll",
            "eventCityEnb":  False,
            "page":          page,
        }
        try:
            resp = post_json(API_URL, payload)
        except (HTTPError, URLError, json.JSONDecodeError) as e:
            print(f"  page {page} failed: {e}", file=sys.stderr)
            break

        items = resp.get("items") or []
        all_items.extend(items)
        print(f"  page {page}: {len(items)} items (total so far: {len(all_items)})")

        if not resp.get("next") or not items:
            break
        page += 1
        time.sleep(0.5)
        if page > 10:  # safety cap
            break

    return all_items


def main():
    print("Fetching SkillBoxes events...")
    last_known = load_last_known()
    fetched_at = datetime.now(timezone.utc).isoformat()

    raw_items = fetch_all()
    events    = [normalise(i) for i in raw_items if is_music(i)]
    events    = [e for e in events if e["name"]]

    # Remove past events
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    events = [e for e in events if not e["date"] or e["date"] >= today]

    events.sort(key=lambda e: (e.get("date") or "9999", e.get("city") or ""))

    if not events:
        print("  WARNING: no music events — preserving last known data", file=sys.stderr)
        if last_known:
            last_known["fetched_at"] = fetched_at
            last_known["note"] = "preserved from last successful fetch"
            with open(OUT, "w") as f:
                json.dump(last_known, f, indent=2)
        else:
            with open(OUT, "w") as f:
                json.dump({"events": [], "fetched_at": fetched_at, "note": "no data yet"}, f, indent=2)
        sys.exit(0)

    out = {"fetched_at": fetched_at, "total": len(events), "events": events}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"  OK — {len(events)} music events saved to events-skillboxes.json")


if __name__ == "__main__":
    main()
