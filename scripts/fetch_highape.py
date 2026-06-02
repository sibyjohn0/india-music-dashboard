#!/usr/bin/env python3
"""
fetch_highape.py — Scrape HighApe music events via Playwright.

HighApe city pages render events client-side. We intercept the API
calls or parse the DOM after JS execution.

URL pattern: https://highape.com/{city}
Cities: bangalore, mumbai, delhi, hyderabad, pune, chennai, goa, kolkata

Output: data/events-highape.json
"""

import asyncio, json, sys, re
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).parent.parent / "data" / "events-highape.json"

CITIES = [
    ("bangalore",  "Bangalore"),
    ("mumbai",     "Mumbai"),
    ("delhi",      "Delhi"),
    ("hyderabad",  "Hyderabad"),
    ("pune",       "Pune"),
    ("chennai",    "Chennai"),
    ("goa",        "Goa"),
    ("kolkata",    "Kolkata"),
]

BASE_URL = "https://highape.com"

MUSIC_KEYWORDS = [
    "music", "concert", "gig", "live", "band", "singer", "acoustic",
    "jazz", "folk", "indie", "hip hop", "rap", "blues", "rock", "pop",
    "sufi", "ghazal", "classical", "fusion", "edm", "dj", "open mic",
]


def load_last_known():
    if OUT.exists():
        with open(OUT) as f:
            return json.load(f)
    return None


def is_music_event(name, category=""):
    text = (name + " " + category).lower()
    return any(kw in text for kw in MUSIC_KEYWORDS)


def parse_price(text):
    if not text:
        return None
    text = str(text).replace(",", "").replace("₹", "").strip()
    nums = re.findall(r"\d+", text)
    return int(nums[0]) if nums else None


async def scrape():
    from playwright.async_api import async_playwright

    all_events = []
    seen_keys  = set()
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
                url = resp.url
                if resp.status != 200:
                    return
                # Intercept any JSON API calls that look like event listings
                ct = resp.headers.get("content-type", "")
                if "json" not in ct:
                    return
                if not any(kw in url for kw in ["event", "listing", "discover", "search", "city"]):
                    return
                try:
                    data = await resp.json()
                    captured.append(data)
                except Exception:
                    pass

            page.on("response", handle_response)

            city_events = []
            try:
                await page.goto(
                    f"{BASE_URL}/{city_slug}",
                    wait_until="domcontentloaded",
                    timeout=45000,
                )
                await asyncio.sleep(3)
                # Scroll to trigger lazy loading
                for _ in range(5):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await asyncio.sleep(1.5)

                # Try to extract from DOM if API intercept didn't work
                # Look for event cards in common patterns
                cards = await page.query_selector_all("[class*='event'], [class*='Event'], [data-testid*='event']")

                for card in cards:
                    try:
                        name_el  = await card.query_selector("h1, h2, h3, h4, [class*='title'], [class*='name']")
                        date_el  = await card.query_selector("[class*='date'], time, [class*='time']")
                        venue_el = await card.query_selector("[class*='venue'], [class*='location']")
                        price_el = await card.query_selector("[class*='price'], [class*='cost'], [class*='ticket']")
                        link_el  = await card.query_selector("a[href]")

                        name  = (await name_el.inner_text()).strip()  if name_el  else ""
                        date  = (await date_el.inner_text()).strip()   if date_el  else ""
                        venue = (await venue_el.inner_text()).strip()  if venue_el else ""
                        price = (await price_el.inner_text()).strip()  if price_el else ""
                        href  = await link_el.get_attribute("href")   if link_el  else ""

                        if not name or len(name) < 3:
                            continue
                        if not is_music_event(name):
                            continue

                        url = href if href and href.startswith("http") else (BASE_URL + href if href else "")
                        key = name.lower() + "|" + city_slug
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)

                        price_val = parse_price(price)
                        city_events.append({
                            "name":      name,
                            "venue":     venue,
                            "city":      city_name,
                            "date":      "",
                            "time":      "",
                            "price_min": price_val,
                            "price_max": price_val,
                            "url":       url,
                        })
                    except Exception:
                        continue

            except Exception as e:
                print(f"  {city_name}: failed ({e})", file=sys.stderr)
            finally:
                await page.close()
                await ctx.close()

            # Also try to parse any captured JSON API responses
            for data in captured:
                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    for k in ["data", "events", "items", "results", "listings"]:
                        if isinstance(data.get(k), list):
                            items = data[k]; break

                for item in items:
                    if not isinstance(item, dict):
                        continue
                    name = (item.get("name") or item.get("title") or item.get("eventName") or "").strip()
                    if not name or not is_music_event(name, item.get("category", "")):
                        continue
                    key = name.lower() + "|" + city_slug
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    epoch = item.get("startTime") or item.get("start_time") or item.get("date")
                    ev_date = ""
                    if epoch and isinstance(epoch, (int, float)):
                        ev_date = datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d")
                    elif isinstance(epoch, str) and len(epoch) >= 10:
                        ev_date = epoch[:10]

                    if ev_date and ev_date < today:
                        continue

                    p = parse_price(item.get("price") or item.get("minPrice") or item.get("price_min"))
                    slug = item.get("slug") or item.get("url") or ""
                    url  = slug if slug.startswith("http") else (BASE_URL + "/" + slug.lstrip("/") if slug else "")

                    city_events.append({
                        "name":      name,
                        "venue":     (item.get("venue") or item.get("venueName") or "").strip(),
                        "city":      item.get("city") or city_name,
                        "date":      ev_date,
                        "time":      "",
                        "price_min": p,
                        "price_max": p,
                        "url":       url,
                    })

            print(f"  {city_name}: {len(city_events)} music events")
            all_events.extend(city_events)
            await asyncio.sleep(1)

        await browser.close()

    return all_events


def main():
    print("Fetching HighApe events...")
    last_known   = load_last_known()
    fetched_at   = datetime.now(timezone.utc).isoformat()

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
