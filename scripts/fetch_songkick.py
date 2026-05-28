#!/usr/bin/env python3
"""
fetch_songkick.py — Fetch upcoming music events in Indian cities via Songkick.

Strategy:
  1. If SONGKICK_API_KEY env var is set, use the Songkick REST API (free, non-commercial).
  2. Otherwise, scrape public Songkick metro pages with requests + BeautifulSoup.

Cities covered: Mumbai, Delhi, Bangalore, Chennai, Hyderabad, Pune, Kolkata

Output: data/events-songkick.json

Songkick API docs: https://www.songkick.com/developer
Metro IDs sourced from https://www.songkick.com/metro_areas/
"""

import os, json, sys, re
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "events-songkick.json")

# Songkick metro area IDs for Indian cities
METRO_AREAS = [
    {"name": "Mumbai",    "metro_id": 9838,  "slug": "mumbai"},
    {"name": "Delhi",     "metro_id": 9867,  "slug": "delhi"},
    {"name": "Bangalore", "metro_id": 9862,  "slug": "bangalore"},
    {"name": "Chennai",   "metro_id": 9907,  "slug": "chennai"},
    {"name": "Hyderabad", "metro_id": 11768, "slug": "hyderabad"},
    {"name": "Pune",      "metro_id": 9839,  "slug": "pune"},
    {"name": "Kolkata",   "metro_id": 9908,  "slug": "kolkata"},
]

API_BASE  = "https://api.songkick.com/api/3.0"
PAGE_BASE = "https://www.songkick.com/metro_areas"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
}


def load_last_known():
    if os.path.exists(OUT):
        with open(OUT) as f:
            return json.load(f)
    return None


def fetch_url(url, timeout=20):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


# ── API path ─────────────────────────────────────────────────────────────────

def fetch_via_api(api_key):
    """Use Songkick API to fetch events for all metro areas."""
    all_events = []
    for metro in METRO_AREAS:
        params = {
            "apikey":   api_key,
            "per_page": 50,
            "page":     1,
        }
        url = f"{API_BASE}/metro_areas/{metro['metro_id']}/calendar.json?{urlencode(params)}"
        try:
            text = fetch_url(url)
            data = json.loads(text)
            results = (
                data.get("resultsPage", {})
                    .get("results", {})
                    .get("event", [])
                or []
            )
            for ev in results:
                event = normalise_api_event(ev, metro["name"])
                if event:
                    all_events.append(event)
            print(f"  API: {metro['name']} — {len(results)} events")
        except (HTTPError, URLError, json.JSONDecodeError, KeyError) as e:
            print(f"  API: {metro['name']} failed ({e})", file=sys.stderr)
    return all_events


def normalise_api_event(ev, city_hint):
    """Convert a Songkick API event dict to our schema."""
    name    = ev.get("displayName", "")
    ev_url  = ev.get("uri", "")
    date    = ev.get("start", {}).get("date", "")

    # Artist(s)
    artists = ev.get("performance", [])
    artist  = ", ".join(p.get("displayName", "") for p in artists if p.get("displayName")) if artists else ""

    # Venue
    venue_obj = ev.get("venue") or {}
    venue     = venue_obj.get("displayName", "")
    capacity  = venue_obj.get("capacity") or ""
    location  = venue_obj.get("metroArea") or {}
    city      = location.get("displayName", "") or city_hint

    if not name:
        return None
    return {
        "name":             name,
        "artist":           artist,
        "venue":            venue,
        "venue_capacity":   capacity,
        "city":             city,
        "date":             date,
        "url":              ev_url,
    }


# ── Scrape path ───────────────────────────────────────────────────────────────

def scrape_metro(metro):
    """Scrape a Songkick metro area page for events."""
    # Try multiple URL formats; Songkick has changed URL structure over time
    candidate_urls = [
        f"{PAGE_BASE}/{metro['metro_id']}-{metro['slug']}-metro-area/calendar",
        f"{PAGE_BASE}/{metro['metro_id']}-{metro['slug']}/calendar",
        f"{PAGE_BASE}/{metro['metro_id']}-{metro['slug']}",
    ]
    html = None
    used_url = None
    for candidate in candidate_urls:
        try:
            html = fetch_url(candidate)
            used_url = candidate
            break
        except (HTTPError, URLError) as e:
            continue
    if html is None:
        print(f"  Scrape: {metro['name']} failed (all URL formats 404)", file=sys.stderr)
        return []
    events = []

    # Try embedded JSON-LD first
    for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
        try:
            obj = json.loads(m.group(1))
            items = obj if isinstance(obj, list) else [obj]
            for item in items:
                if item.get("@type") in ("MusicEvent", "Event"):
                    ev = parse_jsonld_event(item, metro["name"])
                    if ev:
                        events.append(ev)
        except (json.JSONDecodeError, TypeError):
            continue

    # BeautifulSoup fallback
    if not events:
        try:
            from bs4 import BeautifulSoup
            soup  = BeautifulSoup(html, "html.parser")
            cards = soup.select("li.event-listings-element, li.concert, .event-listing")
            for card in cards:
                name_el   = card.select_one("p.summary a, .event-name, h3, strong")
                artist_el = card.select_one(".artists, .headliner, .lineup-compact")
                venue_el  = card.select_one(".venue-name, .location-name")
                date_el   = card.select_one("time, [datetime]")
                link_el   = card.select_one("a[href*='/concerts/'], a[href*='/events/']")

                name   = name_el.get_text(strip=True) if name_el else ""
                artist = artist_el.get_text(strip=True) if artist_el else ""
                venue  = venue_el.get_text(strip=True) if venue_el else ""
                date   = (date_el.get("datetime") or date_el.get_text(strip=True))[:10] if date_el else ""
                href   = link_el["href"] if link_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.songkick.com" + href
                if name:
                    events.append({
                        "name":           name,
                        "artist":         artist,
                        "venue":          venue,
                        "venue_capacity": "",
                        "city":           metro["name"],
                        "date":           date,
                        "url":            href,
                    })
        except ImportError:
            pass

    print(f"  Scrape: {metro['name']} — {len(events)} events")
    return events


def parse_jsonld_event(item, city_hint):
    name     = item.get("name", "")
    ev_url   = item.get("url", "")
    date_raw = item.get("startDate", "")
    date     = date_raw[:10] if date_raw else ""
    location = item.get("location") or {}
    if isinstance(location, list):
        location = location[0] if location else {}
    venue    = location.get("name", "") if isinstance(location, dict) else ""
    city_obj = location.get("address", {}) if isinstance(location, dict) else {}
    city     = (city_obj.get("addressLocality") if isinstance(city_obj, dict) else "") or city_hint
    # Performer
    perf     = item.get("performer") or item.get("organizer") or []
    if isinstance(perf, dict):
        perf = [perf]
    artist   = ", ".join(p.get("name", "") for p in perf if isinstance(p, dict) and p.get("name"))
    capacity = location.get("maximumAttendeeCapacity", "") if isinstance(location, dict) else ""
    if not name:
        return None
    return {
        "name":           name,
        "artist":         artist,
        "venue":          venue,
        "venue_capacity": str(capacity) if capacity else "",
        "city":           city,
        "date":           date,
        "url":            ev_url,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def deduplicate(events):
    seen, out = set(), []
    for ev in events:
        key = (ev.get("name", "").lower()[:40], ev.get("date", ""), ev.get("city", ""))
        if key not in seen:
            seen.add(key)
            out.append(ev)
    return out


def main():
    last_known = load_last_known()
    fetched_at = datetime.now(timezone.utc).isoformat()
    api_key    = os.environ.get("SONGKICK_API_KEY", "")
    events     = []

    if api_key:
        print(f"Using Songkick API key (env: SONGKICK_API_KEY)...")
        try:
            events = fetch_via_api(api_key)
        except Exception as e:
            print(f"  API fetch failed: {e}", file=sys.stderr)

    if not events:
        if api_key:
            print("  API returned nothing, falling back to scraping...", file=sys.stderr)
        else:
            print("SONGKICK_API_KEY not set — scraping public pages...")
        for metro in METRO_AREAS:
            try:
                events.extend(scrape_metro(metro))
            except Exception as e:
                print(f"  Error scraping {metro['name']}: {e}", file=sys.stderr)

    events = deduplicate(events)
    # Sort by date, then city
    events.sort(key=lambda e: (e.get("date", ""), e.get("city", "")))

    if not events:
        msg = "No events found from Songkick API or scraping."
        print(f"WARNING: {msg}", file=sys.stderr)
        if last_known:
            n = len(last_known.get("events", []))
            print(f"  Preserving last known data ({n} events).")
            sys.exit(0)
        out_data = {"events": [], "fetched_at": fetched_at, "note": msg}
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(out_data, f, indent=2)
        print("  Wrote placeholder.")
        sys.exit(0)

    out_data = {
        "events":     events,
        "fetched_at": fetched_at,
        "cities":     [m["name"] for m in METRO_AREAS],
        "source":     "api" if api_key else "scrape",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out_data, f, indent=2)

    print(f"OK: events-songkick.json — {len(events)} events at {fetched_at}")
    for ev in events[:5]:
        cap = f" (cap {ev['venue_capacity']})" if ev.get("venue_capacity") else ""
        print(f"  {ev['date']} | {ev['city']} | {ev['name']} @ {ev['venue']}{cap}")


if __name__ == "__main__":
    main()
