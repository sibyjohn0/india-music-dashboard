#!/usr/bin/env python3
"""
fetch_events_district.py — Scrape District (district.in) music events via Playwright.

Source: https://www.district.in/events/music-in-{city}-book-tickets
API: POST https://www.district.in/gw/web/get_discovery_results (captured via XHR intercept)
Response: EDSResponse.rails[*].items[*].ItemDetails.EventData

Cities: Bengaluru, Mumbai, Delhi, Hyderabad, Pune, Chennai, Kolkata, Goa
Output: data/events-district.json
"""

import asyncio, json, os, sys, re
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).parent.parent / "data" / "events-district.json"

CITIES = [
    ("bengaluru", "Bangalore"),
    ("mumbai",    "Mumbai"),
    ("new-delhi",  "Delhi"),
    ("hyderabad", "Hyderabad"),
    ("pune",      "Pune"),
    ("chennai",   "Chennai"),
    ("kolkata",   "Kolkata"),
    ("goa",       "Goa"),
]

CITY_ALIASES = {
    "Delhi/NCR":  "Delhi",
    "Gurugram":   "Delhi",
    "Bengaluru":  "Bangalore",
    "bengaluru":  "Bangalore",
}

BASE_URL = "https://www.district.in"


def load_last_known():
    if OUT.exists():
        with open(OUT) as f:
            return json.load(f)
    return None


def parse_price(price_str):
    if not price_str:
        return None
    nums = re.findall(r"\d+", price_str.replace(",", ""))
    return int(nums[0]) if nums else None


def normalise_event(ev, city_hint):
    name  = ev.get("name", "").strip()
    venue = ev.get("venue_name", "").strip()
    city  = ev.get("city", "").strip() or city_hint
    city  = CITY_ALIASES.get(city, city)

    epoch = ev.get("start_time_epoch")
    if epoch:
        ev_date = datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d")
        ev_time = datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%H:%M")
    else:
        ev_date = ""
        ev_time = ""

    price_min = parse_price(ev.get("price_string", ""))
    slug      = ev.get("event_slug", "")
    url       = f"{BASE_URL}/events/{slug}" if slug else ""

    if not name:
        return None
    return {
        "name":      name,
        "venue":     venue,
        "city":      city,
        "date":      ev_date,
        "time":      ev_time,
        "price_min": price_min,
        "price_max": price_min,
        "url":       url,
    }


async def scrape():
    from playwright.async_api import async_playwright

    all_events = []
    seen_ids   = set()
    today      = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        for city_slug, city_name in CITIES:
            ctx = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page     = await ctx.new_page()
            captured = []

            async def handle_response(resp, _city=city_name):
                if "get_discovery_results" in resp.url and resp.status == 200:
                    try:
                        data = await resp.json()
                        rails = data.get("EDSResponse", {}).get("rails", [])
                        for rail in rails:
                            for item in rail.get("items", []):
                                ev = item.get("ItemDetails", {}).get("EventData")
                                if ev:
                                    captured.append(ev)
                    except Exception:
                        pass

            page.on("response", handle_response)

            try:
                await page.goto(
                    f"{BASE_URL}/events/music-in-{city_slug}-book-tickets",
                    wait_until="domcontentloaded",
                    timeout=45000,
                )
                # Wait for initial XHR to fire
                await asyncio.sleep(3)
                # Scroll down in steps to trigger lazy loading / pagination
                for scroll_step in range(6):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await asyncio.sleep(1.5)
            except Exception as e:
                print(f"  {city_name}: navigation failed ({e})", file=sys.stderr)
                await page.close()
                await ctx.close()
                continue

            city_count = 0
            for raw in captured:
                ev_id = raw.get("event_id", "")
                if ev_id and ev_id in seen_ids:
                    continue
                if ev_id:
                    seen_ids.add(ev_id)
                norm = normalise_event(raw, city_name)
                if norm and (not norm["date"] or norm["date"] >= today):
                    all_events.append(norm)
                    city_count += 1

            print(f"  {city_name}: {city_count} music events")
            await page.close()
            await ctx.close()
            await asyncio.sleep(1)

        await browser.close()

    return all_events


def main():
    print("Fetching District (district.in) events...")
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
    print(f"  OK — {len(events)} events saved to events-district.json")


if __name__ == "__main__":
    main()
