#!/usr/bin/env python3
"""
fetch_bookmyshow.py — Fetch music events from BookMyShow via Playwright.

BookMyShow's API is behind Cloudflare; Playwright navigates the page and
intercepts the internal explore API response which carries structured event cards.

Cities: Bengaluru, Mumbai, Delhi, Hyderabad, Chennai, Pune, Kolkata, Goa
Output: data/events-bookmyshow.json
"""

import asyncio, json, os, sys, re, base64, time as _time
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).parent.parent / "data" / "events-bookmyshow.json"

CITIES = [
    "bengaluru", "mumbai", "delhi", "hyderabad",
    "chennai", "pune", "kolkata", "goa",
]

MUSIC_CATEGORIES = {
    "music-shows", "music-festivals", "concerts", "music-performing-arts",
    "music-workshops", "live-music",
}


def load_last_known():
    if OUT.exists():
        with open(OUT) as f:
            return json.load(f)
    return None


def extract_date(image_url):
    """Decode base64 date text overlay baked into the BMS card image URL."""
    m = re.search(r"ie-([A-Za-z0-9+/]+=*)", image_url or "")
    if not m:
        return ""
    try:
        raw = base64.b64decode(m.group(1) + "==").decode("utf-8", errors="ignore").strip()
        m2  = re.search(r"(\d{1,2})\s+([A-Za-z]{3,})", raw)
        if m2:
            day_num   = int(m2.group(1))
            month_str = m2.group(2)[:3]
            today     = datetime.now(timezone.utc)
            for yr in (today.year, today.year + 1):
                try:
                    dt = datetime.strptime(f"{day_num} {month_str} {yr}", "%d %b %Y")
                    if dt.date() >= today.date():
                        return dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass
    except Exception:
        pass
    return ""


def is_music(card):
    analytics = card.get("analytics", {})
    category  = analytics.get("category", "")
    cats      = {c.strip() for c in category.split("|")}
    return bool(cats & MUSIC_CATEGORIES)


def parse_price(texts):
    for block in texts:
        for comp in block.get("components", []):
            t    = comp.get("text", "")
            nums = re.findall(r"\d+", t.replace(",", ""))
            if nums:
                return int(nums[0])
    return None


def parse_card(card, city_slug):
    texts = card.get("text", [])
    name  = ""
    venue = ""
    city  = city_slug.title()

    if texts:
        comps = texts[0].get("components", [])
        name  = comps[0].get("text", "") if comps else ""

    if len(texts) > 1:
        comps    = texts[1].get("components", [])
        vc       = comps[0].get("text", "") if comps else ""
        if ": " in vc:
            venue, city = vc.rsplit(": ", 1)
        else:
            venue = vc

    price_min = parse_price(texts[2:])
    image_url = card.get("image", {}).get("url", "")
    ev_date   = extract_date(image_url)

    if not name:
        return None
    return {
        "name":      name.strip(),
        "venue":     venue.strip(),
        "city":      city.strip(),
        "date":      ev_date,
        "price_min": price_min,
        "price_max": price_min,
        "url":       card.get("ctaUrl", ""),
    }


async def scrape():
    from playwright.async_api import async_playwright

    all_events = []
    seen_urls  = set()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx     = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        )

        for city in CITIES:
            captured = {}

            async def handle_response(resp, _city=city):
                if (f"/api/explore/v1/discover/events-{_city}" in resp.url
                        and resp.status == 200):
                    try:
                        captured["data"] = await resp.json()
                    except Exception:
                        pass

            page = await ctx.new_page()
            page.on("response", handle_response)

            try:
                await page.goto(
                    f"https://in.bookmyshow.com/explore/events-{city}?categories=music-shows",
                    wait_until="load",
                    timeout=45000,
                )
                # Wait up to 8s for the explore API XHR to fire
                for _ in range(8):
                    if "data" in captured:
                        break
                    await asyncio.sleep(1)
            except Exception as e:
                print(f"  {city}: navigation failed ({e})", file=sys.stderr)
                await page.close()
                continue

            data         = captured.get("data", {})
            city_events  = 0
            for listing in data.get("listings", []):
                for card in listing.get("cards", []):
                    if not is_music(card):
                        continue
                    ev = parse_card(card, city)
                    if ev and ev["url"] and ev["url"] not in seen_urls:
                        seen_urls.add(ev["url"])
                        all_events.append(ev)
                        city_events += 1

            print(f"  {city}: {city_events} music events")
            await page.close()
            await asyncio.sleep(1)

        await browser.close()

    return all_events


def main():
    print("Fetching BookMyShow music events (Playwright)...")
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
    print(f"  OK — {len(events)} events saved to events-bookmyshow.json")


if __name__ == "__main__":
    main()
