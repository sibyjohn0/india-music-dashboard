#!/usr/bin/env python3
"""
fetch_highape.py — Scrape HighApe music events via JSON-LD structured data.

HighApe embeds all city events as a Schema.org ItemList JSON-LD block in
the page HTML. No API interception needed — parse the <script type="application/ld+json">
block directly after page load.

URL pattern: https://highape.com/{city}
Cities: bangalore, mumbai, delhi-ncr, hyderabad, pune, chennai, goa, kolkata

Output: data/events-highape.json
"""

import asyncio, json, sys, re
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).parent.parent / "data" / "events-highape.json"

CITIES = [
    ("bangalore",  "Bangalore"),
    ("mumbai",     "Mumbai"),
    ("delhi-ncr",  "Delhi"),
    ("hyderabad",  "Hyderabad"),
    ("pune",       "Pune"),
    ("chennai",    "Chennai"),
    ("goa",        "Goa"),
    ("kolkata",    "Kolkata"),
]

BASE_URL = "https://highape.com"

# HighApe is a music/nightlife platform — accept everything except
# clearly non-music events. Don't require positive music keywords.
NON_MUSIC = [
    "comedy show", "stand-up", "standup", "open mic comedy", "improv comedy",
    "yoga", "fitness class", "dance class", "meditation",
    "speed dating", "trivia night", "quiz night", "gaming tournament", "esports",
    "art exhibition", "gallery opening", "theatre performance",
    "mafia night", "mafia game", "murder mystery", "networking event",
    "corporate", "seminar", "conference",
]


def load_last_known():
    if OUT.exists():
        with open(OUT) as f:
            return json.load(f)
    return None


def is_music_event(name, category=""):
    text = (name + " " + category).lower()
    return not any(kw in text for kw in NON_MUSIC)


def parse_date(date_str):
    """Convert ISO 8601 startDate to YYYY-MM-DD."""
    if not date_str:
        return ""
    try:
        # Handle '2026-06-13T18:00:00+05:30' format
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return date_str[:10] if len(date_str) >= 10 else ""


def parse_time(date_str):
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%H:%M")
    except Exception:
        return ""


async def scrape():
    from playwright.async_api import async_playwright

    all_events = []
    seen_urls  = set()  # dedup by URL globally; city derived from URL
    today      = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    CITY_FROM_SLUG = {slug: name for slug, name in CITIES}
    # Also map common city slugs that appear in event URLs
    CITY_FROM_URL_SLUG = {
        "bangalore": "Bangalore", "mumbai": "Mumbai", "delhi-ncr": "Delhi",
        "delhi": "Delhi", "hyderabad": "Hyderabad", "pune": "Pune",
        "chennai": "Chennai", "goa": "Goa", "kolkata": "Kolkata",
    }

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        for city_slug, city_name in CITIES:
            ctx = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page = await ctx.new_page()
            city_events = []

            try:
                await page.goto(
                    f"{BASE_URL}/{city_slug}",
                    wait_until="domcontentloaded",
                    timeout=45000,
                )
                await asyncio.sleep(4)

                html = await page.content()

                # Extract all JSON-LD blocks
                ld_blocks = re.findall(
                    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                    html, re.DOTALL
                )

                for block in ld_blocks:
                    try:
                        data = json.loads(block)
                    except json.JSONDecodeError:
                        continue

                    # Handle @graph arrays
                    items_to_check = []
                    if isinstance(data, list):
                        items_to_check = data
                    elif data.get("@type") == "ItemList":
                        items_to_check = [
                            item.get("item", {})
                            for item in data.get("itemListElement", [])
                        ]
                    elif data.get("@type") == "Event":
                        items_to_check = [data]
                    elif "@graph" in data:
                        items_to_check = data["@graph"]

                    for item in items_to_check:
                        if not isinstance(item, dict):
                            continue
                        if item.get("@type") != "Event":
                            continue

                        name = (item.get("name") or "").strip()
                        if not name:
                            continue
                        if not is_music_event(name):
                            continue

                        url       = item.get("url", "")
                        start     = item.get("startDate", "")
                        ev_date   = parse_date(start)
                        ev_time   = parse_time(start)

                        if ev_date and ev_date < today:
                            continue
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        # Derive city from URL path (/{city}/events/...) — more reliable
                        # than the page we scraped from, since HighApe shows cross-city events
                        city_from_url = city_name
                        if url:
                            m = re.search(r'highape\.com/([^/]+)/events/', url)
                            if m:
                                slug = m.group(1)
                                city_from_url = CITY_FROM_URL_SLUG.get(slug, city_name)

                        location = item.get("location", {})
                        venue    = (location.get("name") or "").strip()
                        # Clean city suffix from venue name
                        venue = re.sub(
                            r'\s*[-–]\s*(?:Bangalore|Mumbai|Delhi|Hyderabad|Pune|Chennai|Goa|Kolkata)\s*$',
                            '', venue, flags=re.IGNORECASE
                        ).strip()
                        if venue.lower() in ("to be announced", "tba", "venue tbc"):
                            venue = ""

                        city_events.append({
                            "name":      name,
                            "venue":     venue,
                            "city":      city_from_url,
                            "date":      ev_date,
                            "time":      ev_time,
                            "price_min": None,
                            "price_max": None,
                            "url":       url,
                        })

            except Exception as e:
                print(f"  {city_name}: failed ({e})", file=sys.stderr)
            finally:
                await page.close()
                await ctx.close()

            print(f"  {city_name}: {len(city_events)} music events")
            all_events.extend(city_events)
            await asyncio.sleep(1)

        await browser.close()

    return all_events


def main():
    print("Fetching HighApe events...")
    last_known = load_last_known()
    fetched_at = datetime.now(timezone.utc).isoformat()

    events = asyncio.run(scrape())
    events.sort(key=lambda e: (e.get("date") or "9999", e.get("city") or ""))

    if not events:
        print("  WARNING: no events — preserving last known data", file=sys.stderr)
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
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"  OK — {len(events)} events saved to events-highape.json")


if __name__ == "__main__":
    main()
