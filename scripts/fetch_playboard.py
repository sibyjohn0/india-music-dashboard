#!/usr/bin/env python3
"""
fetch_playboard.py — Scrape PlayBoard's fastest-growing Indian music YouTube channels (daily).

Source: https://playboard.co/en/youtube-ranking/most-growth-music-channels-in-india-daily
Output: data/playboard.json

NOTE: PlayBoard is a JavaScript-heavy SPA. requests + BeautifulSoup can fetch the
initial HTML but the ranking table is rendered client-side. This script attempts a
plain HTTP request first. If the page returns an empty or bot-blocked response, it
falls back to writing the last known good data unchanged and exits with a warning.
A headless browser (Playwright/Selenium) would be needed for full JS rendering.
"""

import os, json, sys, re
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

URL = "https://playboard.co/en/youtube-ranking/most-growth-music-channels-in-india-daily"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "playboard.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def load_last_known():
    if os.path.exists(OUT):
        with open(OUT) as f:
            return json.load(f)
    return None


def parse_subscriber_count(text):
    """Convert '1.2M', '340K', '5,340' etc. to an integer."""
    text = text.strip().replace(",", "")
    m = re.match(r"([\d.]+)\s*([KkMmBb]?)", text)
    if not m:
        return 0
    num = float(m.group(1))
    suffix = m.group(2).upper()
    if suffix == "K":
        return int(num * 1_000)
    if suffix == "M":
        return int(num * 1_000_000)
    if suffix == "B":
        return int(num * 1_000_000_000)
    return int(num)


def parse_growth(text):
    """Parse '+1.2M' / '+340K' growth text, return (count, pct_str)."""
    text = text.strip()
    count_str = re.sub(r"[^0-9KkMmBb.+\-]", "", text.split("(")[0])
    pct_match = re.search(r"\(([\d.+\-]+%)\)", text)
    pct = pct_match.group(1) if pct_match else ""
    return parse_subscriber_count(count_str.lstrip("+")), pct


def scrape_html(html):
    """
    Try to extract channel rows from the rendered HTML.
    PlayBoard embeds JSON-LD or uses specific CSS classes — we probe both.
    Returns list of dicts or empty list if nothing found.
    """
    channels = []

    # Attempt 1: JSON-LD / window.__NUXT__ embedded data
    nuxt_match = re.search(r"window\.__NUXT__\s*=\s*(\{.*?\});?\s*</script>", html, re.DOTALL)
    if nuxt_match:
        try:
            raw = nuxt_match.group(1)
            # Truncate to first 200k chars to avoid huge parse
            data = json.loads(raw[:200_000])
            # Walk for lists that look like channel entries
            def walk(obj, depth=0):
                if depth > 10 or channels:
                    return
                if isinstance(obj, list):
                    for item in obj:
                        walk(item, depth + 1)
                elif isinstance(obj, dict):
                    if "channelId" in obj or "channel_id" in obj or "channelTitle" in obj:
                        channels.append(obj)
                    else:
                        for v in obj.values():
                            walk(v, depth + 1)
            walk(data)
        except Exception:
            pass

    # Attempt 2: BeautifulSoup HTML parsing (requires bs4)
    if not channels:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            # PlayBoard uses li.ranking-item or tr elements
            rows = soup.select("li.ranking-item") or soup.select("tr.ranking-row") or soup.select(".channel-item")
            for i, row in enumerate(rows, 1):
                name_el  = row.select_one(".channel-name, .title, h3, h4")
                link_el  = row.select_one("a[href*='/channel/'], a[href*='youtube.com']")
                subs_el  = row.select_one(".subscriber, .subs, .count")
                grow_el  = row.select_one(".growth, .gain, .increase")
                name     = name_el.get_text(strip=True) if name_el else ""
                href     = link_el["href"] if link_el and link_el.get("href") else ""
                subs_txt = subs_el.get_text(strip=True) if subs_el else "0"
                grow_txt = grow_el.get_text(strip=True) if grow_el else ""
                if name:
                    cnt, pct = parse_growth(grow_txt) if grow_txt else (0, "")
                    channels.append({
                        "rank":         i,
                        "channel_name": name,
                        "channel_url":  href,
                        "subscribers":  parse_subscriber_count(subs_txt),
                        "growth_count": cnt,
                        "growth_pct":   pct,
                    })
        except ImportError:
            pass

    return channels


def main():
    last_known = load_last_known()
    scraped_at = datetime.now(timezone.utc).isoformat()

    try:
        req  = Request(URL, headers=HEADERS)
        with urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError) as e:
        print(f"WARNING: Could not fetch PlayBoard ({e}). Keeping last known data.", file=sys.stderr)
        if last_known:
            print(f"  Last known data has {len(last_known.get('channels', []))} channels, preserved.")
        else:
            fallback = {"channels": [], "scraped_at": scraped_at,
                        "note": "PlayBoard requires JS rendering — plain HTTP fetch blocked."}
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            with open(OUT, "w") as f:
                json.dump(fallback, f, indent=2)
            print("  Wrote empty placeholder.")
        sys.exit(0)

    channels = scrape_html(html)

    if not channels:
        # PlayBoard is JS-rendered; plain HTML fetch likely returned skeleton only.
        note = (
            "PlayBoard requires JavaScript rendering. Plain HTTP fetch returned no channel data. "
            "To populate this file, run this script with Playwright or another headless browser."
        )
        print(f"WARNING: {note}", file=sys.stderr)
        if last_known:
            print(f"  Preserving last known data ({len(last_known.get('channels', []))} channels).")
            sys.exit(0)
        else:
            out_data = {"channels": [], "scraped_at": scraped_at, "note": note}
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            with open(OUT, "w") as f:
                json.dump(out_data, f, indent=2)
            print("  Wrote placeholder with note.")
            sys.exit(0)

    # Normalise channel entries
    normalized = []
    for i, ch in enumerate(channels, 1):
        normalized.append({
            "rank":         ch.get("rank", i),
            "channel_name": ch.get("channel_name") or ch.get("channelTitle", ""),
            "channel_url":  ch.get("channel_url") or ch.get("channelId", ""),
            "subscribers":  ch.get("subscribers", 0),
            "growth_count": ch.get("growth_count", 0),
            "growth_pct":   ch.get("growth_pct", ""),
            "scraped_at":   scraped_at,
        })

    out_data = {"channels": normalized, "scraped_at": scraped_at}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out_data, f, indent=2)

    print(f"OK: playboard.json — {len(normalized)} channels scraped at {scraped_at}")
    for ch in normalized[:5]:
        print(f"  #{ch['rank']} {ch['channel_name']} ({ch['subscribers']:,} subs, +{ch['growth_count']:,})")


if __name__ == "__main__":
    main()
