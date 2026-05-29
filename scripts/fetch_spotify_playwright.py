#!/usr/bin/env python3
"""
fetch_spotify_playwright.py — Scrape Spotify artist pages for monthly listener counts,
top cities, and top track stream counts using Playwright.

Data scraped (not available via Spotify API, only on artist page HTML):
- Monthly listeners
- Top 5 cities (from About section)
- Top 5 tracks with approximate stream counts

Artist source:
  1. data/tracked_artists.json if it has spotify_id fields
  2. data/spotify_enrichment.json for spotify_id + name lookup

Output: data/spotify_playwright.json

GitHub Actions note: requires `playwright install chromium` before running.
"""

import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT   = Path(__file__).parent.parent
DATA_DIR    = REPO_ROOT / "data"
OUT_PATH    = DATA_DIR / "spotify_playwright.json"
TRACKED     = DATA_DIR / "tracked_artists.json"
ENRICHMENT  = DATA_DIR / "spotify_enrichment.json"

MAX_ARTISTS = 15        # ~40s per artist × 15 = ~600s; pipeline timeout is 600s
WALL_BUDGET_S = 480    # stop accepting new artists after this many seconds, write partial results
USER_AGENT  = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


# ── helpers ──────────────────────────────────────────────────────────────────

def parse_stream_count(text: str) -> int | None:
    """
    Parse Spotify stream-count strings like '1,234,567', '1.2M', '980K'.
    Returns an integer or None if the text cannot be parsed.
    """
    if not text:
        return None
    text = text.strip().replace(",", "").replace(" ", "")
    m = re.match(r"([\d.]+)\s*([KkMmBbGg]?)", text)
    if not m:
        return None
    num    = float(m.group(1))
    suffix = m.group(2).upper()
    multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000, "G": 1_000_000_000}
    return int(num * multipliers.get(suffix, 1))


def parse_monthly_listeners(text: str) -> int | None:
    """Parse '45,320 monthly listeners' or '1.2M monthly listeners'."""
    if not text:
        return None
    # Try the number part before "monthly"
    m = re.search(r"([\d,. ]+)\s*(?:monthly)?", text, re.IGNORECASE)
    if not m:
        return None
    return parse_stream_count(m.group(1))


def load_last_known() -> dict:
    """Load previous output so we can preserve data for artists that fail."""
    if OUT_PATH.exists():
        with open(OUT_PATH) as f:
            return json.load(f)
    return {}


def build_artist_list() -> list[dict]:
    """
    Return a list of dicts: [{"name": ..., "spotify_id": ...}, ...]

    Priority:
    1. tracked_artists.json — if any entry has a spotify_id field
    2. spotify_enrichment.json — keyed by artist name with spotify_id + spotify_url
    """
    artists: list[dict] = []

    # Try tracked_artists.json first
    if TRACKED.exists():
        with open(TRACKED) as f:
            data = json.load(f)
        for entry in data.get("artists", []):
            sid = entry.get("spotify_id")
            if sid:
                artists.append({"name": entry["name"], "spotify_id": sid})

    # Fall back to / supplement with spotify_enrichment.json
    if ENRICHMENT.exists():
        with open(ENRICHMENT) as f:
            enrich = json.load(f)
        seen_ids = {a["spotify_id"] for a in artists}
        for name, info in enrich.get("enrichment", {}).items():
            sid = info.get("spotify_id")
            if sid and sid not in seen_ids:
                artists.append({"name": name, "spotify_id": sid})
                seen_ids.add(sid)

    return artists[:MAX_ARTISTS]


# ── scraper ───────────────────────────────────────────────────────────────────

def scrape_artist(page, spotify_id: str, name: str) -> dict | None:
    """
    Navigate to the Spotify artist page and extract:
    - monthly_listeners
    - top_cities (up to 5)
    - top_tracks (up to 5 with stream counts)

    Returns a result dict or None on hard failure.
    """
    url = f"https://open.spotify.com/artist/{spotify_id}"
    scraped_at = datetime.now(timezone.utc).isoformat()

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    except Exception as e:
        print(f"  WARNING: goto failed for {name} ({spotify_id}): {e}", file=sys.stderr)
        return None

    # Wait for monthly listeners label
    try:
        page.wait_for_selector('[data-testid="monthly-listeners-label"]', timeout=10_000)
    except Exception:
        # Some artist pages don't show the label (very new / no listeners yet)
        print(f"  WARNING: monthly-listeners-label not found for {name} — skipping", file=sys.stderr)
        return None

    # ── Monthly listeners ─────────────────────────────────────────
    monthly_listeners: int | None = None
    try:
        el = page.query_selector('[data-testid="monthly-listeners-label"]')
        if el:
            monthly_listeners = parse_monthly_listeners(el.inner_text())
    except Exception as e:
        print(f"  WARNING: could not parse monthly listeners for {name}: {e}", file=sys.stderr)

    # ── Top tracks ────────────────────────────────────────────────
    top_tracks: list[dict] = []
    try:
        # Track rows are inside a section with data-testid="top-tracks"
        track_rows = page.query_selector_all('[data-testid="track-row"]')
        for row in track_rows[:5]:
            track_name_el = row.query_selector('[data-testid="internal-track-link"]')
            track_name = track_name_el.inner_text().strip() if track_name_el else ""

            # Stream count is in an aria-label or a specific column element
            streams: int | None = None
            # Spotify shows streams in a column; try a few selectors
            count_el = row.query_selector('[data-testid="playcount"]')
            if count_el:
                streams = parse_stream_count(count_el.inner_text())
            if not streams:
                # Some layouts expose it via aria-label on the row itself
                aria = row.get_attribute("aria-label") or ""
                m = re.search(r"([\d,]+)\s*play", aria, re.IGNORECASE)
                if m:
                    streams = parse_stream_count(m.group(1))

            if track_name:
                top_tracks.append({"name": track_name, "streams": streams})
    except Exception as e:
        print(f"  WARNING: could not parse top tracks for {name}: {e}", file=sys.stderr)

    # ── Top cities ────────────────────────────────────────────────
    top_cities: list[str] = []
    try:
        # Cities live in the About section or a "where people listen" card
        city_els = page.query_selector_all('[data-testid="city-list"] li, .city-name, [class*="cityName"]')
        if city_els:
            top_cities = [el.inner_text().strip() for el in city_els[:5] if el.inner_text().strip()]

        # Fallback: look for cities inside the About section text
        if not top_cities:
            about_el = page.query_selector('[data-testid="artist-about-section"]')
            if about_el:
                about_text = about_el.inner_text()
                # Cities are typically listed as "City1, City2, City3"
                m = re.search(r"(?:Cities?|Where People Listen)\s*[:\-–]?\s*(.+)", about_text, re.IGNORECASE)
                if m:
                    raw = m.group(1).strip()
                    top_cities = [c.strip() for c in re.split(r"[,\n]", raw) if c.strip()][:5]
    except Exception as e:
        print(f"  WARNING: could not parse top cities for {name}: {e}", file=sys.stderr)

    return {
        "spotify_id":        spotify_id,
        "name":              name,
        "monthly_listeners": monthly_listeners,
        "top_cities":        top_cities,
        "top_tracks":        top_tracks,
        "scraped_at":        scraped_at,
    }


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium", file=sys.stderr)
        sys.exit(1)

    artists = build_artist_list()
    if not artists:
        print("ERROR: no artists with spotify_id found in tracked_artists.json or spotify_enrichment.json", file=sys.stderr)
        sys.exit(1)

    print(f"Spotify Playwright scraper — {len(artists)} artists queued (max {MAX_ARTISTS})")

    # Load last known data so we can preserve results for artists that fail
    last_known_raw = load_last_known()
    last_known: dict[str, dict] = {}
    for entry in last_known_raw.get("artists", []):
        sid = entry.get("spotify_id")
        if sid:
            last_known[sid] = entry

    results: list[dict] = []
    scraped_at_run = datetime.now(timezone.utc).isoformat()
    wall_start = time.monotonic()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            slow_mo=500,
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = context.new_page()

        for i, artist in enumerate(artists):
            if time.monotonic() - wall_start > WALL_BUDGET_S:
                print(f"  Wall budget ({WALL_BUDGET_S}s) reached after {i} artists — writing partial results.")
                break

            name       = artist["name"]
            spotify_id = artist["spotify_id"]
            print(f"  [{i+1}/{len(artists)}] {name} ({spotify_id})")

            result = scrape_artist(page, spotify_id, name)

            if result is None:
                # Preserve last known data if available
                if spotify_id in last_known:
                    preserved = dict(last_known[spotify_id])
                    preserved["_preserved"] = True
                    results.append(preserved)
                    print(f"    Preserved last known data for {name}")
                else:
                    print(f"    No prior data — skipping {name}")
            else:
                results.append(result)
                ml = result["monthly_listeners"]
                cities = ", ".join(result["top_cities"]) if result["top_cities"] else "n/a"
                tracks = len(result["top_tracks"])
                print(f"    {ml:,} listeners | cities: {cities} | tracks: {tracks}" if ml else f"    listeners: n/a | cities: {cities} | tracks: {tracks}")

            # 2-3 second random delay between artists (skip delay on last artist)
            if i < len(artists) - 1:
                time.sleep(random.uniform(2, 3))

        context.close()
        browser.close()

    output = {
        "scraped_at": scraped_at_run,
        "total":      len(results),
        "artists":    results,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    ok_count = sum(1 for r in results if not r.get("_preserved"))
    preserved_count = sum(1 for r in results if r.get("_preserved"))
    print(f"\nSaved {len(results)} artists to data/spotify_playwright.json")
    print(f"  Fresh: {ok_count} | Preserved from prior run: {preserved_count}")


if __name__ == "__main__":
    main()
