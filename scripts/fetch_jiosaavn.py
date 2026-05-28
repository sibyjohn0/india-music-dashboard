#!/usr/bin/env python3
"""
fetch_jiosaavn.py — Scrape JioSaavn trending tracks.

Source: https://www.jiosaavn.com/featured/trending-today/I3ovYAWhFUc_
Output: data/jiosaavn.json

JioSaavn's public pages are server-side rendered. This script tries a plain
HTTP request first, then parses the embedded JSON (window.__INITIAL_STATE__
or JSON-LD) before falling back to BeautifulSoup HTML parsing.
"""

import os, json, sys, re
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

URL = "https://www.jiosaavn.com/featured/trending-today/I3ovYAWhFUc_"
# Also try the JioSaavn internal API endpoint (public, no key required)
API_URL = "https://www.jiosaavn.com/api.php?__call=content.getAlbumDetails&albumid=I3ovYAWhFUc_&_format=json&_marker=0&ctx=web6dot0"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "jiosaavn.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.jiosaavn.com/",
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


def parse_from_api(text):
    """Try parsing a JioSaavn API JSON response."""
    try:
        data = json.loads(text)
        songs = data.get("songs") or data.get("list") or []
        tracks = []
        for s in songs:
            title  = s.get("title") or s.get("song", "")
            # HTML entities in JioSaavn responses
            title  = re.sub(r"&amp;", "&", title)
            title  = re.sub(r"&#039;", "'", title)
            artist = s.get("primary_artists") or s.get("singers") or s.get("artist", "")
            artist = re.sub(r"&amp;", "&", artist)
            plays  = s.get("play_count") or s.get("playCount") or ""
            url    = s.get("perma_url") or s.get("url") or ""
            if title:
                tracks.append({
                    "title":  title,
                    "artist": artist,
                    "plays":  str(plays),
                    "url":    url,
                })
        return tracks
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def parse_from_html(html):
    """Extract tracks from JioSaavn's server-rendered HTML / embedded state."""
    tracks = []

    # Attempt 1: window.__INITIAL_STATE__ / __SSR_DATA__ JSON blob
    for pattern in [
        r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});\s*(?:window|</script>)",
        r"window\.__SSR_DATA__\s*=\s*(\{.*?\});\s*(?:window|</script>)",
        r'<script[^>]*type="application/json"[^>]*>(\{.*?\})</script>',
    ]:
        m = re.search(pattern, html, re.DOTALL)
        if not m:
            continue
        try:
            raw = m.group(1)[:500_000]
            data = json.loads(raw)
            # Walk for song/track arrays
            def walk(obj, depth=0):
                if depth > 12 or len(tracks) >= 50:
                    return
                if isinstance(obj, list):
                    for item in obj:
                        walk(item, depth + 1)
                elif isinstance(obj, dict):
                    # Detect a song-like object
                    if ("title" in obj or "song" in obj) and ("primary_artists" in obj or "singers" in obj or "artist" in obj):
                        title  = obj.get("title") or obj.get("song", "")
                        title  = re.sub(r"&amp;", "&", title)
                        title  = re.sub(r"&#039;", "'", title)
                        artist = obj.get("primary_artists") or obj.get("singers") or obj.get("artist", "")
                        artist = re.sub(r"&amp;", "&", artist)
                        plays  = str(obj.get("play_count") or obj.get("playCount") or "")
                        url    = obj.get("perma_url") or obj.get("url") or ""
                        if title and not any(t["title"] == title for t in tracks):
                            tracks.append({"title": title, "artist": artist, "plays": plays, "url": url})
                    else:
                        for v in obj.values():
                            walk(v, depth + 1)
            walk(data)
            if tracks:
                break
        except (json.JSONDecodeError, ValueError):
            continue

    # Attempt 2: BeautifulSoup fallback
    if not tracks:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            items = (
                soup.select(".song-list .c-content")
                or soup.select(".trending-track")
                or soup.select("[data-type='song']")
                or soup.select("li.list-item")
            )
            for item in items:
                title_el  = item.select_one(".song-name, .title, h3, h4, .name")
                artist_el = item.select_one(".song-artist, .artist, .subtitle")
                link_el   = item.select_one("a[href]")
                title  = title_el.get_text(strip=True) if title_el else ""
                artist = artist_el.get_text(strip=True) if artist_el else ""
                href   = link_el["href"] if link_el else ""
                if title:
                    tracks.append({"title": title, "artist": artist, "plays": "", "url": href})
        except ImportError:
            pass

    return tracks


def main():
    last_known  = load_last_known()
    scraped_at  = datetime.now(timezone.utc).isoformat()

    tracks = []

    # Strategy 1: Internal API endpoint
    try:
        text   = fetch_url(API_URL)
        tracks = parse_from_api(text)
        if tracks:
            print(f"  Fetched {len(tracks)} tracks from JioSaavn API.")
    except (HTTPError, URLError) as e:
        print(f"  API endpoint failed ({e}), trying HTML page...", file=sys.stderr)

    # Strategy 2: HTML page
    if not tracks:
        try:
            html   = fetch_url(URL)
            tracks = parse_from_html(html)
            if tracks:
                print(f"  Fetched {len(tracks)} tracks from JioSaavn HTML.")
        except (HTTPError, URLError) as e:
            print(f"WARNING: JioSaavn HTML fetch failed ({e}).", file=sys.stderr)

    if not tracks:
        msg = "Could not extract tracks from JioSaavn (page may require JS rendering)."
        print(f"WARNING: {msg}", file=sys.stderr)
        if last_known:
            print(f"  Preserving last known data ({len(last_known.get('trending_tracks', []))} tracks).")
            sys.exit(0)
        out_data = {"trending_tracks": [], "scraped_at": scraped_at, "note": msg}
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(out_data, f, indent=2)
        print("  Wrote placeholder.")
        sys.exit(0)

    out_data = {"trending_tracks": tracks, "scraped_at": scraped_at}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out_data, f, indent=2)

    print(f"OK: jiosaavn.json — {len(tracks)} trending tracks at {scraped_at}")
    for t in tracks[:5]:
        print(f"  {t['title']} — {t['artist']}")


if __name__ == "__main__":
    main()
