#!/usr/bin/env python3
"""
fetch_events_district.py — Scrape District (by Zomato) music events.

Source: https://district.zomato.com/events
Output: data/events-district.json

District serves a Next.js app. Script tries the internal API first,
then falls back to __NEXT_DATA__ JSON parsing, then BeautifulSoup.
On failure, last known good data is preserved.
"""

import os, json, sys, re
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

BASE_URL   = "https://district.zomato.com"
EVENTS_URL = "https://district.zomato.com/events"
# District internal API endpoints (reverse-engineered from network tab)
API_URLS = [
    "https://district.zomato.com/api/events?category=music&page=1&page_size=50",
    "https://api.district.zomato.com/events?category=music&limit=50",
]
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "events-district.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/json, text/html;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://district.zomato.com/",
}

INDIAN_CITIES = {
    "mumbai", "delhi", "bangalore", "bengaluru", "hyderabad",
    "chennai", "pune", "kolkata", "goa", "ahmedabad",
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


def fmt_date(raw):
    if not raw:
        return ""
    if isinstance(raw, (int, float)):
        try:
            return datetime.fromtimestamp(raw / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            return str(raw)
    return str(raw)[:10]


def parse_price(raw):
    if not raw:
        return None, None
    if isinstance(raw, (int, float)):
        return int(raw), int(raw)
    s = str(raw).replace(",", "")
    nums = re.findall(r"\d+", s)
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    if len(nums) == 1:
        return int(nums[0]), int(nums[0])
    return None, None


def normalise_event(raw):
    """Normalise an event dict from any source into a standard shape."""
    name    = raw.get("name") or raw.get("title") or raw.get("event_name") or ""
    venue   = raw.get("venue") or raw.get("venue_name") or raw.get("location") or ""
    if isinstance(venue, dict):
        venue = venue.get("name") or venue.get("venue_name") or ""
    city    = raw.get("city") or raw.get("city_name") or ""
    if isinstance(city, dict):
        city = city.get("name") or city.get("city_name") or ""
    date_raw  = raw.get("date") or raw.get("start_date") or raw.get("event_date") or raw.get("start_time") or ""
    price_raw = raw.get("price") or raw.get("price_info") or raw.get("min_price") or ""
    url_raw   = raw.get("url") or raw.get("event_url") or raw.get("slug") or ""
    if url_raw and not url_raw.startswith("http"):
        url_raw = BASE_URL + "/" + url_raw.lstrip("/")
    pmin, pmax = parse_price(price_raw)
    return {
        "name":      name,
        "venue":     venue,
        "city":      city,
        "date":      fmt_date(date_raw),
        "price_min": pmin,
        "price_max": pmax,
        "url":       url_raw,
    }


def is_music_event(ev):
    text = (ev.get("name", "") + " " + ev.get("category", "") + " " +
            ev.get("tags", "")).lower()
    music_kw = ["music", "concert", "gig", "band", "artist", "live", "dj",
                "fest", "festival", "performance", "show"]
    return any(k in text for k in music_kw)


def try_api():
    for url in API_URLS:
        try:
            raw = fetch_url(url)
            data = json.loads(raw)
            items = (data.get("events") or data.get("data") or
                     data.get("results") or (data if isinstance(data, list) else []))
            if items:
                print(f"  API success: {len(items)} events from {url}")
                return items
        except Exception as e:
            print(f"  API failed ({url}): {e}")
    return []


def try_next_data():
    try:
        raw = fetch_url(EVENTS_URL)
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', raw, re.S)
        if not m:
            return []
        nd = json.loads(m.group(1))

        def walk(obj, depth=0):
            if depth > 8:
                return []
            if isinstance(obj, list) and obj and isinstance(obj[0], dict):
                if any(k in obj[0] for k in ("name","title","event_name","slug")):
                    return obj
            if isinstance(obj, dict):
                for v in obj.values():
                    found = walk(v, depth + 1)
                    if found:
                        return found
            return []

        items = walk(nd)
        if items:
            print(f"  __NEXT_DATA__ success: {len(items)} items")
        return items
    except Exception as e:
        print(f"  __NEXT_DATA__ failed: {e}")
        return []


def try_beautifulsoup():
    try:
        from bs4 import BeautifulSoup
        raw = fetch_url(EVENTS_URL)
        soup = BeautifulSoup(raw, "lxml")
        cards = (soup.select("[class*='event-card']") or
                 soup.select("[class*='EventCard']") or
                 soup.select("[class*='event_card']") or
                 soup.select("article"))
        events = []
        for card in cards[:50]:
            name  = card.select_one("h2,h3,[class*='title'],[class*='name']")
            venue = card.select_one("[class*='venue'],[class*='location']")
            date  = card.select_one("[class*='date'],[class*='time'],time")
            price = card.select_one("[class*='price'],[class*='cost']")
            link  = card.select_one("a[href]")
            events.append({
                "name":  name.get_text(strip=True)  if name  else "",
                "venue": venue.get_text(strip=True) if venue else "",
                "city":  "",
                "date":  date.get_text(strip=True)  if date  else "",
                "price": price.get_text(strip=True) if price else "",
                "url":   BASE_URL + link["href"] if link else "",
            })
        if events:
            print(f"  BeautifulSoup: {len(events)} cards")
        return events
    except ImportError:
        print("  BeautifulSoup not available")
        return []
    except Exception as e:
        print(f"  BeautifulSoup failed: {e}")
        return []


def main():
    print("Fetching District (Zomato) events...")
    now = datetime.now(timezone.utc).isoformat()

    raw_events = try_api() or try_next_data() or try_beautifulsoup()

    if not raw_events:
        print("  WARNING: all methods failed — preserving last known data")
        last = load_last_known()
        if last:
            last["fetched_at"] = now
            last["note"] = "preserved from last successful fetch"
            with open(OUT, "w") as f:
                json.dump(last, f, indent=2)
        else:
            with open(OUT, "w") as f:
                json.dump({"events": [], "fetched_at": now, "note": "no data yet"}, f, indent=2)
        sys.exit(0)

    events = [normalise_event(e) for e in raw_events]
    events = [e for e in events if e["name"] and is_music_event(e)]
    events.sort(key=lambda e: e["date"] or "9999")

    output = {
        "fetched_at": now,
        "total":      len(events),
        "events":     events,
    }
    with open(OUT, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  OK — {len(events)} music events saved to events-district.json")


if __name__ == "__main__":
    main()
