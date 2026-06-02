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

# Locality-name → canonical city. Used to override URL-based city when
# the venue name contains a well-known neighbourhood that places it in a
# different city than the HighApe page it was scraped from.
LOCALITY_TO_CITY = {
    # Hyderabad
    "gachibowli": "Hyderabad", "gachibowil": "Hyderabad",
    "hitech city": "Hyderabad", "hitec city": "Hyderabad",
    "madhapur": "Hyderabad", "banjara hills": "Hyderabad",
    "jubilee hills": "Hyderabad", "kondapur": "Hyderabad",
    "manikonda": "Hyderabad", "lb nagar": "Hyderabad",
    "kukatpally": "Hyderabad", "secunderabad": "Hyderabad",
    "ameerpet": "Hyderabad", "begumpet": "Hyderabad",
    "miyapur": "Hyderabad",
    # Mumbai
    "bandra": "Mumbai", "andheri": "Mumbai", "juhu": "Mumbai",
    "lower parel": "Mumbai", "bkc": "Mumbai", "kurla": "Mumbai",
    "powai": "Mumbai", "dadar": "Mumbai", "goregaon": "Mumbai",
    "malad": "Mumbai", "worli": "Mumbai", "versova": "Mumbai",
    "navi mumbai": "Mumbai", "thane": "Mumbai", "borivali": "Mumbai",
    "vile parle": "Mumbai", "matunga": "Mumbai",
    # Delhi
    "connaught place": "Delhi", "hauz khas": "Delhi",
    "cyberhub": "Delhi", "cyber hub": "Delhi",
    "saket": "Delhi", "vasant kunj": "Delhi",
    "noida": "Delhi", "gurugram": "Delhi", "gurgaon": "Delhi",
    "mehrauli": "Delhi", "lajpat nagar": "Delhi",
    "south extension": "Delhi", "green park": "Delhi",
    # Bangalore (confirm genuinely Bangalore localities)
    "whitefield": "Bangalore", "koramangala": "Bangalore",
    "indiranagar": "Bangalore", "jayanagar": "Bangalore",
    "mg road": "Bangalore", "ulsoor": "Bangalore",
    "marathahalli": "Bangalore", "electronic city": "Bangalore",
    "jp nagar": "Bangalore", "btm layout": "Bangalore",
    "hsr layout": "Bangalore", "hebbal": "Bangalore",
    # Pune
    "koregaon park": "Pune", "kothrud": "Pune",
    "shivajinagar": "Pune", "viman nagar": "Pune",
    "baner": "Pune", "aundh": "Pune", "wakad": "Pune",
    "hinjewadi": "Pune", "kharadi": "Pune",
    # Chennai
    "t nagar": "Chennai", "nungambakkam": "Chennai",
    "anna nagar": "Chennai", "adyar": "Chennai",
    "velachery": "Chennai", "mylapore": "Chennai",
    # Kolkata
    "park street": "Kolkata", "salt lake": "Kolkata",
    "ballygunge": "Kolkata", "new town": "Kolkata",
    # Goa
    "calangute": "Goa", "baga": "Goa", "anjuna": "Goa",
    "panaji": "Goa", "panjim": "Goa", "vagator": "Goa",
    "assagao": "Goa", "candolim": "Goa", "chapora": "Goa",
    "morjim": "Goa", "arambol": "Goa", "mapusa": "Goa",
}

ADDR_LOCALITY_MAP = {
    "bengaluru": "Bangalore", "bangalore": "Bangalore",
    "mumbai": "Mumbai", "delhi": "Delhi", "new delhi": "Delhi",
    "hyderabad": "Hyderabad", "pune": "Pune", "chennai": "Chennai",
    "kolkata": "Kolkata", "goa": "Goa", "kochi": "Kochi", "cochin": "Kochi",
}


def city_from_locality(text):
    """Return city if text contains a known locality name, else None."""
    tl = text.lower()
    # Sort longest first so 'connaught place' beats 'place'
    for loc, city in sorted(LOCALITY_TO_CITY.items(), key=lambda x: -len(x[0])):
        if loc in tl:
            return city
    return None


# HighApe is a music/nightlife platform — accept everything except
# clearly non-music events. Don't require positive music keywords.
NON_MUSIC = [
    "comedy show", "stand-up", "standup", "open mic comedy", "improv comedy",
    "yoga", "fitness class", "dance class", "meditation",
    "speed dating", "trivia night", "quiz night", "gaming tournament", "esports",
    "art exhibition", "gallery opening", "theatre performance",
    "mafia night", "mafia game", "murder mystery", "networking event",
    "corporate", "seminar", "conference",
    # Craft / hobby workshops (common at Third Wave Coffee-style venues)
    " workshop", "resin ", "clay ", "kintsugi", "macrame", "candle making",
    "tote bag", "lego ", "pottery", "embroidery", "knitting", "crochet",
    "journaling", "vision board", "soap making", "terrarium", "origami",
    "sip and paint", "paint and sip", "painting workshop", "sketching class",
    # Treks, outdoor tours, travel packages (Namma Trip, e2e, etc.)
    " trek", "trekking", " hike", "hiking", "sunrise trek", "camping",
    "waterfall trek", "beach trek", "namma trip", "nammatrip",
    "nandi hills", "ooty trip", "chikmagalur trip", "kodaikanal",
    "coorg trip", "chopta", "tungnath", "entrepreneurs summit",
    "tour package", "trip package", "trip from bangalore",
    # Recurring nightclub/bar nights — not music shows
    "pool club", "ladies night", "ladies free", "girls night", "open bar",
    "tangled tuesdays", "thirsty thursdays", "whisper wednesdays",
    "fever fridays", "soulmate saturdays", "sweetheart sundays", "makeout mondays",
    # Weekly bar-night naming patterns
    "tuesdays at ", "wednesdays at ", "thursdays at ", "fridays at ",
    "saturdays at ", "sundays at ", "mondays at ",
    # Tech / startup events misclassified as music
    "tech ", "startup", "hackathon", "pitch night", "demo day",
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

                        # Derive city — priority order:
                        # 1. Schema.org address.addressLocality (most accurate)
                        # 2. Venue name locality keyword match
                        # 3. Page city (fallback — event URL slug is unreliable
                        #    because HighApe cross-promotes events across city pages
                        #    using the canonical URL from the event's home city)
                        location = item.get("location", {}) or {}
                        venue    = (location.get("name") or "").strip()
                        # Clean city suffix from venue name
                        venue = re.sub(
                            r'\s*[-–]\s*(?:Bangalore|Mumbai|Delhi|Hyderabad|Pune|Chennai|Goa|Kolkata)\s*$',
                            '', venue, flags=re.IGNORECASE
                        ).strip()
                        if venue.lower() in ("to be announced", "tba", "venue tbc"):
                            venue = ""

                        # 1. Schema.org address
                        addr = location.get("address") or {}
                        if isinstance(addr, str):
                            addr = {}
                        raw_addr_loc = (addr.get("addressLocality") or "").strip().lower()
                        city_from_addr = ADDR_LOCALITY_MAP.get(raw_addr_loc)

                        # 2. Venue name locality keyword
                        city_from_venue = city_from_locality(venue) if venue else None

                        actual_city = city_from_addr or city_from_venue or city_name

                        city_events.append({
                            "name":      name,
                            "venue":     venue,
                            "city":      actual_city,
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
