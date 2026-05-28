#!/usr/bin/env python3
"""
fetch_playboard.py — Scrape PlayBoard's fastest-growing Indian music YouTube channels (daily).

Source: https://playboard.co/en/youtube-ranking/most-growth-music-channels-in-india-daily
Output: data/playboard.json

PlayBoard is a Nuxt.js SPA. The ranking table is rendered client-side, so this script
uses Playwright to drive a headless Chromium browser and wait for the table to appear.

GitHub Actions note: requires `playwright install chromium` before running.
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR  = REPO_ROOT / "data"
OUT_PATH  = DATA_DIR / "playboard.json"

URL = "https://playboard.co/en/youtube-ranking/most-growth-music-channels-in-india-daily"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

TARGET_ROWS = 20


# ── helpers ───────────────────────────────────────────────────────────────────

def parse_number(text: str) -> int:
    """Convert '1.2M', '340K', '5,340', '+1.2M' etc. to an integer."""
    if not text:
        return 0
    text = text.strip().lstrip("+").replace(",", "").replace(" ", "")
    m = re.match(r"([\d.]+)\s*([KkMmBbGg]?)", text)
    if not m:
        return 0
    num    = float(m.group(1))
    suffix = m.group(2).upper()
    multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000, "G": 1_000_000_000}
    return int(num * multipliers.get(suffix, 1))


def load_last_known() -> dict | None:
    if OUT_PATH.exists():
        with open(OUT_PATH) as f:
            return json.load(f)
    return None


# ── scraper ───────────────────────────────────────────────────────────────────

def scrape_playboard(page) -> list[dict]:
    """
    Navigate to PlayBoard and extract up to TARGET_ROWS channel rows.
    Returns a list of channel dicts.
    """
    page.goto(URL, wait_until="domcontentloaded", timeout=30_000)

    # Wait for the ranking table to render (Nuxt.js SPA)
    # PlayBoard uses list items or table rows for channel entries.
    # Try several candidate selectors in order of specificity.
    CANDIDATE_SELECTORS = [
        ".ranking-item",
        "[class*='rankingItem']",
        "li.channel",
        "tr.channel",
        ".channel-item",
        "[class*='channelItem']",
    ]

    matched_selector = None
    for sel in CANDIDATE_SELECTORS:
        try:
            page.wait_for_selector(sel, timeout=8_000)
            matched_selector = sel
            print(f"  Table ready — matched selector: {sel}")
            break
        except Exception:
            continue

    if not matched_selector:
        print("  WARNING: could not find channel rows with any known selector", file=sys.stderr)
        return []

    # Extra 3-second buffer for JS to finish populating all rows
    time.sleep(3)

    rows = page.query_selector_all(matched_selector)
    print(f"  Found {len(rows)} candidate rows")

    channels: list[dict] = []
    for i, row in enumerate(rows[:TARGET_ROWS], 1):
        try:
            row_text = row.inner_text()
        except Exception:
            continue

        # Channel name: look for a prominent text element
        name = ""
        for name_sel in [
            "[class*='channelName']",
            "[class*='title']",
            "h3", "h4", "h2",
            "strong",
            ".name",
        ]:
            el = row.query_selector(name_sel)
            if el:
                candidate = el.inner_text().strip()
                if candidate and len(candidate) > 1:
                    name = candidate
                    break

        if not name:
            # Try first non-numeric text in the row
            lines = [ln.strip() for ln in row_text.splitlines() if ln.strip()]
            for ln in lines:
                if not re.match(r"^[\d,. KkMmBb%+\-]+$", ln) and len(ln) > 1:
                    name = ln
                    break

        # Channel URL
        channel_url = ""
        link_el = row.query_selector("a[href]")
        if link_el:
            href = link_el.get_attribute("href") or ""
            if href:
                # PlayBoard links are relative (/en/channel/...) or full YouTube URLs
                if href.startswith("/"):
                    channel_url = "https://playboard.co" + href
                else:
                    channel_url = href

        # Subscriber count: look for elements containing subscriber-style numbers
        subscribers = 0
        for subs_sel in [
            "[class*='subscriber']",
            "[class*='subs']",
            "[class*='count']",
            "[class*='follower']",
        ]:
            el = row.query_selector(subs_sel)
            if el:
                val = parse_number(el.inner_text())
                if val > 0:
                    subscribers = val
                    break

        # Growth count and percent
        growth_count = 0
        growth_pct   = ""
        for grow_sel in [
            "[class*='growth']",
            "[class*='gain']",
            "[class*='increase']",
            "[class*='delta']",
            "[class*='change']",
        ]:
            el = row.query_selector(grow_sel)
            if el:
                grow_text = el.inner_text().strip()
                # Look for percentage in parentheses or with % sign
                pct_m = re.search(r"\(([\d.+\-]+%)\)|(\d[\d.]*%)", grow_text)
                if pct_m:
                    growth_pct = pct_m.group(1) or pct_m.group(2)
                # Strip the percent part to get the count
                count_text = re.sub(r"\(.*?\)", "", grow_text).strip()
                val = parse_number(count_text)
                if val > 0:
                    growth_count = val
                break

        # If we have a name, include the row even with zeros for the rest
        if name:
            channels.append({
                "rank":         i,
                "channel_name": name,
                "channel_url":  channel_url,
                "subscribers":  subscribers,
                "growth_count": growth_count,
                "growth_pct":   growth_pct,
            })

    return channels


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "ERROR: playwright not installed. "
            "Run: pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        sys.exit(1)

    last_known  = load_last_known()
    scraped_at  = datetime.now(timezone.utc).isoformat()
    channels: list[dict] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                slow_mo=200,
            )
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1440, "height": 900},
                locale="en-US",
            )
            page = context.new_page()

            channels = scrape_playboard(page)

            context.close()
            browser.close()

    except Exception as e:
        print(f"WARNING: Playwright run failed: {e}", file=sys.stderr)

    if not channels:
        print("WARNING: no channel data scraped — preserving last known data.", file=sys.stderr)
        if last_known:
            print(f"  Last known data has {len(last_known.get('channels', []))} channels, preserved.")
            # Update only the scraped_at timestamp so consumers know it was attempted
            last_known["scraped_at_attempt"] = scraped_at
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(OUT_PATH, "w") as f:
                json.dump(last_known, f, indent=2)
        else:
            fallback = {
                "channels":  [],
                "scraped_at": scraped_at,
                "note": "PlayBoard JS rendering produced no rows on this run.",
            }
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(OUT_PATH, "w") as f:
                json.dump(fallback, f, indent=2)
            print("  Wrote empty placeholder.")
        sys.exit(0)

    # Stamp each channel row with the run time
    for ch in channels:
        ch["scraped_at"] = scraped_at

    out_data = {"channels": channels, "scraped_at": scraped_at}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out_data, f, indent=2)

    print(f"OK: playboard.json — {len(channels)} channels scraped at {scraped_at}")
    for ch in channels[:5]:
        subs  = ch["subscribers"]
        grow  = ch["growth_count"]
        pct   = ch["growth_pct"]
        label = f"#{ch['rank']} {ch['channel_name']} ({subs:,} subs, +{grow:,}{' ' + pct if pct else ''})"
        print(f"  {label}")


if __name__ == "__main__":
    main()
