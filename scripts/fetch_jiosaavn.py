#!/usr/bin/env python3
"""
fetch_jiosaavn.py — Fetch JioSaavn chart tracks (India Superhits Top 50 + English Top 20).

Strategy:
  1. Call content.getCharts to get live chart playlist tokens.
  2. For each chart, call webapi.get with the token to get 20 tracks.
  3. Deduplicate and write output.

No hardcoded IDs — chart tokens come from the API on every run.
Output: data/jiosaavn.json
"""

import os, json, sys, re
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

CHARTS_URL = (
    "https://www.jiosaavn.com/api.php"
    "?__call=content.getCharts&_format=json&_marker=0&ctx=web6dot0"
    "&language=hindi,english,punjabi,telugu,tamil"
)
PLAYLIST_URL_TMPL = (
    "https://www.jiosaavn.com/api.php"
    "?__call=webapi.get&token={token}&type=playlist&p=1&n=20"
    "&_format=json&_marker=0&ctx=web6dot0"
)

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "jiosaavn.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://www.jiosaavn.com/",
}

# Prefer these chart title substrings (case-insensitive match)
PREFERRED_CHARTS = ["superhits top 50", "english top", "trending", "top 20"]
MAX_CHARTS = 4


def fetch_json(url, timeout=20):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def clean(text):
    if not text:
        return ""
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&#039;", "'", text)
    text = re.sub(r"&quot;", '"', text)
    return text.strip()


def get_chart_token(chart):
    """Extract the playlist token from a chart item's perma_url."""
    perma = chart.get("perma_url", "")
    if perma:
        return perma.rstrip("/").split("/")[-1]
    return ""


def score_chart(chart):
    title = (chart.get("title") or "").lower()
    for i, keyword in enumerate(PREFERRED_CHARTS):
        if keyword in title:
            return i
    return len(PREFERRED_CHARTS)


def fetch_chart_tracks(token):
    url = PLAYLIST_URL_TMPL.format(token=token)
    data = fetch_json(url)
    songs = data.get("songs") or data.get("list") or []
    tracks = []
    for s in songs:
        title  = clean(s.get("song") or s.get("title") or "")
        artist = clean(s.get("primary_artists") or s.get("singers") or "")
        plays  = str(s.get("play_count") or "")
        url    = s.get("perma_url") or s.get("url") or ""
        lang   = s.get("language") or ""
        if title:
            tracks.append({
                "title":    title,
                "artist":   artist,
                "plays":    plays,
                "url":      url,
                "language": lang,
            })
    return tracks


def load_last_known():
    if os.path.exists(OUT):
        with open(OUT) as f:
            return json.load(f)
    return None


def main():
    last_known = load_last_known()
    scraped_at = datetime.now(timezone.utc).isoformat()
    all_tracks = []
    seen_titles = set()

    try:
        charts = fetch_json(CHARTS_URL)
    except (HTTPError, URLError, json.JSONDecodeError) as e:
        print(f"WARNING: Could not fetch JioSaavn charts list: {e}", file=sys.stderr)
        charts = []

    # Sort by preference, take top MAX_CHARTS
    charts = [c for c in charts if c.get("type") == "playlist" and c.get("perma_url")]
    charts.sort(key=score_chart)
    charts = charts[:MAX_CHARTS]

    for chart in charts:
        title = chart.get("title", "unknown chart")
        token = get_chart_token(chart)
        if not token:
            print(f"  Skipping {title!r} — no token", file=sys.stderr)
            continue
        try:
            tracks = fetch_chart_tracks(token)
            added = 0
            for t in tracks:
                key = t["title"].lower()
                if key not in seen_titles:
                    seen_titles.add(key)
                    all_tracks.append(t)
                    added += 1
            print(f"  {title}: {len(tracks)} fetched, {added} new")
        except (HTTPError, URLError, json.JSONDecodeError) as e:
            print(f"  {title!r}: failed ({e})", file=sys.stderr)

    if not all_tracks:
        msg = "Could not fetch any tracks from JioSaavn charts."
        print(f"WARNING: {msg}", file=sys.stderr)
        if last_known and last_known.get("trending_tracks"):
            n = len(last_known["trending_tracks"])
            print(f"  Preserving last known data ({n} tracks).")
            sys.exit(0)
        out_data = {"trending_tracks": [], "scraped_at": scraped_at, "note": msg}
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(out_data, f, indent=2)
        sys.exit(0)

    out_data = {"trending_tracks": all_tracks, "scraped_at": scraped_at}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)

    print(f"OK: jiosaavn.json — {len(all_tracks)} tracks at {scraped_at}")
    for t in all_tracks[:5]:
        print(f"  {t['title']} — {t['artist']}")


if __name__ == "__main__":
    main()
