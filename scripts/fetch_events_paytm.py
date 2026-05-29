#!/usr/bin/env python3
"""
fetch_events_paytm.py — Scrape Paytm Insider music events.

Source: https://insider.in/music
Output: data/events-paytm.json

Paytm Insider (insider.in) serves event listings server-side and also exposes
a public JSON API. This script tries the API first, then falls back to HTML
parsing. On failure, last known good data is preserved.
"""

import os, json, sys, re
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

HTML_URL = "https://insider.in/music"
# Insider.in public API (no key required)
API_URL  = "https://api.insider.in/event/list?tags=music&pageSize=50&type=event&city=&page=1"
OUT      = os.path.join(os.path.dirname(__file__), "..", "data", "events-paytm.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/json, text/html;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://insider.in/",
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
    """Normalise epoch millis, ISO strings, or human text into ISO date string."""
    if not raw:
        return ""
    if isinstance(raw, (int, float)):
        try:
            return datetime.fromtimestamp(raw / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            return str(raw)
    return str(raw)[:10]


def parse_price(p):
    """Return int from various price representations."""
    if p is None:
        return 0
    if isinstance(p, (int, float)):
        return int(p)
    txt = re.sub(r"[^\d]", "", str(p))
    return int(txt) if txt else 0


def parse_from_api(text):
    """Parse the insider.in API JSON response."""
    events = []
    try:
        data = json.loads(text)
        items = (
            data.get("data", {}).get("events") if isinstance(data.get("data"), dict) else None
        ) or data.get("events") or data.get("data") or []
        if not isinstance(items, list):
            return []
        for ev in items:
            name   = ev.get("name") or ev.get("title") or ""
            # Artist may be nested or a flat string
            artist = (
                ev.get("artist_name")
                or ev.get("performer")
                or (ev.get("tags") or {}).get("artist", "")
                or ""
            )
            venue_obj = ev.get("venue") or {}
            venue  = (
                venue_obj.get("name") or venue_obj.get("title") if isinstance(venue_obj, dict)
                else str(venue_obj)
            ) or ""
            city   = (
                venue_obj.get("city") if isinstance(venue_obj, dict) else ""
            ) or ev.get("city") or ""
            date   = fmt_date(ev.get("start_time") or ev.get("min_show_start_time") or ev.get("date"))
            prices = ev.get("price_range") or ev.get("min_price") or {}
            if isinstance(prices, dict):
                price_min = parse_price(prices.get("min") or prices.get("from") or prices.get("startingFrom"))
                price_max = parse_price(prices.get("max") or prices.get("to"))
            elif isinstance(prices, (int, float, str)):
                price_min = parse_price(prices)
                price_max = price_min
            else:
                price_min = price_max = 0
            url = ev.get("url") or ev.get("event_url") or ev.get("slug") or ""
            if url and not url.startswith("http"):
                url = "https://insider.in/" + url.lstrip("/")
            if name:
                events.append({
                    "name":      name,
                    "artist":    artist,
                    "venue":     venue,
                    "city":      city,
                    "date":      date,
                    "price_min": price_min,
                    "price_max": price_max,
                    "url":       url,
                })
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass
    return events


def parse_from_html(html):
    """Parse events from insider.in HTML, including embedded JSON blobs."""
    events = []

    # Probe embedded JSON state blobs
    for pattern in [
        r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});\s*</script>",
        r"window\.__STATE__\s*=\s*(\{.*?\});\s*</script>",
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>(\{.*?\})</script>',
    ]:
        m = re.search(pattern, html, re.DOTALL)
        if not m:
            continue
        try:
            raw  = m.group(1)[:800_000]
            data = json.loads(raw)
            # Recursively walk for event-like dicts
            def walk(obj, depth=0):
                if depth > 12 or len(events) >= 100:
                    return
                if isinstance(obj, list):
                    for item in obj:
                        walk(item, depth + 1)
                elif isinstance(obj, dict):
                    if ("name" in obj or "title" in obj) and ("venue" in obj or "start_time" in obj or "date" in obj):
                        name  = obj.get("name") or obj.get("title", "")
                        artist = obj.get("artist_name") or obj.get("performer") or ""
                        vobj  = obj.get("venue") or {}
                        venue = (vobj.get("name") if isinstance(vobj, dict) else str(vobj)) or ""
                        city  = (vobj.get("city") if isinstance(vobj, dict) else "") or obj.get("city", "")
                        date  = fmt_date(obj.get("start_time") or obj.get("date"))
                        prices = obj.get("price_range") or {}
                        price_min = parse_price(prices.get("min", 0) if isinstance(prices, dict) else prices)
                        price_max = parse_price(prices.get("max", 0) if isinstance(prices, dict) else prices)
                        ev_url = obj.get("url") or obj.get("slug") or ""
                        if ev_url and not ev_url.startswith("http"):
                            ev_url = "https://insider.in/" + ev_url.lstrip("/")
                        if name and not any(e["name"] == name and e["date"] == date for e in events):
                            events.append({
                                "name": name, "artist": artist, "venue": venue,
                                "city": city, "date": date,
                                "price_min": price_min, "price_max": price_max,
                                "url": ev_url,
                            })
                    else:
                        for v in obj.values():
                            walk(v, depth + 1)
            walk(data)
            if events:
                break
        except (json.JSONDecodeError, ValueError):
            continue

    # BeautifulSoup fallback
    if not events:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            cards = (
                soup.select(".event-card")
                or soup.select("[class*='event-item']")
                or soup.select("article")
                or soup.select(".card")
            )
            for card in cards:
                name_el   = card.select_one("h2, h3, h4, .event-name, .title")
                artist_el = card.select_one(".artist, .performer, .subtitle")
                venue_el  = card.select_one(".venue, .location")
                date_el   = card.select_one(".date, time, [datetime]")
                price_el  = card.select_one(".price, .ticket-price")
                link_el   = card.select_one("a[href]")
                name   = name_el.get_text(strip=True) if name_el else ""
                artist = artist_el.get_text(strip=True) if artist_el else ""
                venue  = venue_el.get_text(strip=True) if venue_el else ""
                date   = (date_el.get("datetime") or date_el.get_text(strip=True) if date_el else "")
                price  = price_el.get_text(strip=True) if price_el else ""
                href   = link_el["href"] if link_el else ""
                if href and not href.startswith("http"):
                    href = "https://insider.in" + href
                if name:
                    events.append({
                        "name": name, "artist": artist, "venue": venue,
                        "city": "", "date": date[:10],
                        "price_min": parse_price(price), "price_max": parse_price(price),
                        "url": href,
                    })
        except ImportError:
            pass

    return events


def main():
    last_known = load_last_known()
    scraped_at = datetime.now(timezone.utc).isoformat()

    # insider.in is a fully JS-rendered React app. The /music path returns 404,
    # api.insider.in DNS does not resolve, and the homepage has no embedded event data.
    # Preserve last known data and exit cleanly rather than wasting time on failing requests.
    note = (
        "insider.in requires JS rendering (React SPA). "
        "API subdomain does not resolve. Preserving last known data."
    )
    print(f"INFO: {note}")
    if last_known and last_known.get("events"):
        n = len(last_known["events"])
        print(f"  Preserving {n} events from last successful run.")
        sys.exit(0)

    out_data = {"events": [], "scraped_at": scraped_at, "note": note}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out_data, f, indent=2)
    print("  Wrote empty placeholder.")
    sys.exit(0)

    # ── Dead code — preserved for future Playwright implementation ──
    events = []

    # Strategy 1: API
    try:
        text   = fetch_url(API_URL)
        events = parse_from_api(text)
        if events:
            print(f"  Fetched {len(events)} events from insider.in API.")
    except (HTTPError, URLError) as e:
        print(f"  API failed ({e}), trying HTML...", file=sys.stderr)

    # Strategy 2: HTML
    if not events:
        try:
            html   = fetch_url(HTML_URL)
            events = parse_from_html(html)
            if events:
                print(f"  Fetched {len(events)} events from insider.in HTML.")
        except (HTTPError, URLError) as e:
            print(f"WARNING: insider.in HTML fetch failed ({e}).", file=sys.stderr)

    if not events:
        msg = "Could not extract events from insider.in (may require JS rendering)."
        print(f"WARNING: {msg}", file=sys.stderr)
        if last_known:
            n = len(last_known.get("events", []))
            print(f"  Preserving last known data ({n} events).")
            sys.exit(0)
        out_data = {"events": [], "scraped_at": scraped_at, "note": msg}
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(out_data, f, indent=2)
        print("  Wrote placeholder.")
        sys.exit(0)

    out_data = {"events": events, "scraped_at": scraped_at}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out_data, f, indent=2)

    print(f"OK: events-paytm.json — {len(events)} events at {scraped_at}")
    for ev in events[:5]:
        print(f"  {ev['date']} | {ev['name']} @ {ev['venue']}, {ev['city']}")


if __name__ == "__main__":
    main()
