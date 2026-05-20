#!/usr/bin/env python3
"""
Enriches dashboard artists with Spotify data and discovers new artists from
Spotify's Indian indie playlists. Uses Client Credentials flow (no user login).
Outputs: data/spotify_enrichment.json
"""

import json, os, sys, time, re
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import HTTPError
from base64 import b64encode
from datetime import datetime, timezone

CLIENT_ID     = os.environ.get("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
DATA_DIR      = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_PATH   = os.path.join(DATA_DIR, "spotify_enrichment.json")
LATEST_PATH   = os.path.join(DATA_DIR, "latest.json")

# Search queries to find public India indie playlists (editorial playlists are 403 in dev mode)
PLAYLIST_SEARCHES = [
    "India indie music",
    "Tamil indie music",
    "Telugu indie songs",
    "Kannada indie music",
    "Malayalam indie songs",
    "Bengali indie music",
    "Punjabi indie music",
    "Marathi indie music",
    "Hindi indie music",
]

_token = None
_token_expiry = 0


def get_token():
    global _token, _token_expiry
    if _token and time.time() < _token_expiry - 30:
        return _token
    creds = b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    req = Request(
        "https://accounts.spotify.com/api/token",
        data=b"grant_type=client_credentials",
        headers={"Authorization": f"Basic {creds}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    with urlopen(req, timeout=10) as r:
        d = json.loads(r.read())
    _token = d["access_token"]
    _token_expiry = time.time() + d["expires_in"]
    return _token


def api_get(path, params=None):
    url = f"https://api.spotify.com/v1{path}"
    if params:
        url += "?" + urlencode(params)
    req = Request(url, headers={"Authorization": f"Bearer {get_token()}"})
    try:
        with urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except HTTPError as e:
        if e.code == 429:
            retry = int(e.headers.get("Retry-After", 3))
            print(f"  rate limit — sleeping {retry}s")
            time.sleep(retry)
            return api_get(path, params)
        print(f"  HTTP {e.code} on {path}")
        return None
    except Exception as e:
        print(f"  error on {path}: {e}")
        return None


def _name_similarity(a, b):
    """Rough similarity: fraction of words in a that appear in b."""
    wa = set(re.sub(r"[^\w\s]", "", a.lower()).split())
    wb = set(re.sub(r"[^\w\s]", "", b.lower()).split())
    if not wa:
        return 0
    return len(wa & wb) / len(wa)


def search_artist(name):
    """Find Spotify artist by name; require reasonable name similarity."""
    # Skip generic / emoji-heavy channel names that won't match real artists
    clean = re.sub(r"[^\x00-\x7F]", "", name).strip()
    if len(clean) < 4:
        return None

    data = api_get("/search", {"q": name, "type": "artist", "market": "IN", "limit": 5})
    if not data:
        return None
    items = data.get("artists", {}).get("items", [])
    if not items:
        return None

    name_lower = name.lower()
    # Exact match first
    for item in items:
        if item["name"].lower() == name_lower:
            return item
    # Partial match with threshold
    for item in items:
        if _name_similarity(name, item["name"]) >= 0.6:
            return item
    return None


def get_artist_details(artist_id):
    return api_get(f"/artists/{artist_id}")


def get_playlist_tracks(playlist_id, limit=50):
    data = api_get(f"/playlists/{playlist_id}/tracks",
                   {"market": "IN", "limit": limit,
                    "fields": "items(track(name,artists,album(release_date),popularity))"})
    if not data:
        return []
    return [item["track"] for item in data.get("items", []) if item.get("track")]


def load_youtube_artists():
    try:
        with open(LATEST_PATH) as f:
            d = json.load(f)
        seen, artists = set(), []
        for v in d.get("videos", []):
            ch = v.get("channel", "")
            if ch and ch not in seen:
                seen.add(ch)
                artists.append({
                    "name": ch,
                    "language": v.get("language") or "Hindi",
                    "genre": v.get("genre") or "Indie",
                })
        return artists
    except Exception:
        return []


def enrich_youtube_artists(yt_artists):
    enriched = {}
    print(f"  Searching Spotify for {len(yt_artists)} YouTube artists...")
    for a in yt_artists:
        name = a["name"]
        result = search_artist(name)
        if not result:
            continue
        # Search results don't always include followers; fetch full artist detail
        detail = get_artist_details(result["id"]) or result
        enriched[name] = {
            "spotify_id":    detail["id"],
            "spotify_name":  detail["name"],
            "followers":     (detail.get("followers") or {}).get("total", 0),
            "popularity":    detail.get("popularity", 0),
            "genres":        detail.get("genres", []),
            "spotify_url":   (detail.get("external_urls") or {}).get("spotify", ""),
            "image":         detail["images"][0]["url"] if detail.get("images") else "",
        }
        followers = enriched[name]["followers"]
        print(f"    {name} -> {detail['name']} ({followers:,} followers, pop {enriched[name]['popularity']})")
        time.sleep(0.1)
    return enriched


def search_playlists(query, limit=5):
    data = api_get("/search", {"q": query, "type": "playlist", "market": "IN", "limit": limit})
    if not data:
        return []
    return data.get("playlists", {}).get("items", []) or []


def fetch_playlist_artists():
    """Discover artists from publicly-searchable India indie playlists."""
    discovered = {}
    tried_playlists = set()

    for query in PLAYLIST_SEARCHES:
        print(f"  Searching playlists: {query!r}...")
        playlists = search_playlists(query)
        for pl in playlists[:3]:
            if not pl:
                continue
            pid = pl.get("id", "")
            if not pid or pid in tried_playlists:
                continue
            tried_playlists.add(pid)
            pname = pl.get("name", query)
            tracks = get_playlist_tracks(pid, limit=30)
            for track in tracks:
                if not track:
                    continue
                for artist in track.get("artists", []):
                    aid   = artist.get("id", "")
                    aname = artist.get("name", "")
                    if not aid:
                        continue
                    if aid in discovered:
                        discovered[aid]["track_count"] += 1
                    else:
                        discovered[aid] = {
                            "spotify_id":   aid,
                            "name":         aname,
                            "popularity":   track.get("popularity", 0),
                            "playlist":     pname,
                            "track_count":  1,
                            "release_date": (track.get("album") or {}).get("release_date", ""),
                            "followers":    0,
                            "genres":       [],
                            "image":        "",
                            "spotify_url":  "",
                        }
        time.sleep(0.3)

    # Fetch full details for top-appearing artists
    top = sorted(discovered.values(), key=lambda x: -x["track_count"])[:40]
    result = []
    for a in top:
        details = get_artist_details(a["spotify_id"])
        if details:
            a["followers"]   = (details.get("followers") or {}).get("total", 0)
            a["genres"]      = details.get("genres", [])
            a["image"]       = details["images"][0]["url"] if details.get("images") else ""
            a["spotify_url"] = (details.get("external_urls") or {}).get("spotify", "")
            a["popularity"]  = details.get("popularity", a["popularity"])
        result.append(a)
        time.sleep(0.1)
    return result


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set", file=sys.stderr)
        sys.exit(1)

    print("Getting Spotify token...")
    get_token()
    print("  OK")

    print("Loading YouTube artists...")
    yt_artists = load_youtube_artists()
    print(f"  {len(yt_artists)} artists")

    print("Enriching YouTube artists with Spotify data...")
    enrichment = enrich_youtube_artists(yt_artists)
    print(f"  {len(enrichment)} matched on Spotify")

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "enrichment":   enrichment,   # YouTube artist name -> Spotify data
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Written -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
