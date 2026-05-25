#!/usr/bin/env python3
"""
Finds Spotify playlist curators who have made playlists featuring Indian indie music.

Strategy:
  1. Search for playlists using Indian indie keywords.
  2. For each playlist, fetch tracks to verify Indian indie content.
  3. Extract the playlist owner (curator) profile.
  4. One unique curator = one reviewer entry.

Output: data/reviewers/spotify_curators.json
"""

import json, os, re, time, base64
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import HTTPError

DATA_DIR    = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "reviewers", "spotify_curators.json")
LATEST_PATH = os.path.join(DATA_DIR, "latest.json")

CLIENT_ID     = os.environ.get("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
BASE          = "https://api.spotify.com/v1"

# ── Playlist search queries ────────────────────────────────────────────────────
PLAYLIST_QUERIES = [
    "indian indie music",
    "india independent music",
    "desi indie",
    "indian indie pop",
    "indian indie folk",
    "indian indie rock",
    "hindi indie",
    "tamil indie",
    "telugu indie",
    "kannada indie",
    "bengali indie",
    "malayalam indie",
    "punjabi indie",
    "marathi indie",
    "indian underground music",
    "indie india",
    "new indian music",
    "fresh indian indie",
    "best indian indie",
    "indian bedroom pop",
    "desi hip hop underground",
    "indian lo fi",
    "carnatic indie",
    "indian fusion indie",
    "south asian indie",
    "desi alternative",
    "mumbai indie scene",
    "bangalore indie music",
    "delhi indie music",
]

# ── Known Indian indie artist IDs (used to verify playlist content) ────────────
# These are Spotify artist IDs for known Indian indie artists.
KNOWN_INDIE_ARTIST_IDS = {
    "6sFIWsNpZYqfjUpaCgueju",  # Prateek Kuhad
    "0oOet2f43PA68X26yx4zDS",  # Ritviz
    "1OBm9MO1MN1PQVKV3MJqY6",  # When Chai Met Toast
    "3mIj9lX2MWuHmhNda7oMHY",  # Sid Sriram
    "4tZwfgrHOc3mvqYlEYSvVi",  # STRFKR (placeholder — add real IDs)
    "7iK8PXO48WeuP03g8YR51W",  # Nucleya
    "2Tz1DTzVJ5Gyh8ZwVr6ekU",  # Hanumankind
}

# Min followers for a playlist to be worth extracting a curator from
MIN_PLAYLIST_FOLLOWERS = 50
# Min tracks in a playlist
MIN_PLAYLIST_TRACKS = 5
# Min Indian indie tracks needed to qualify playlist
MIN_INDIE_TRACKS = 2

_token = None
_token_expiry = 0


def get_token():
    global _token, _token_expiry
    now = time.time()
    if _token and now < _token_expiry - 60:
        return _token
    creds    = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    req      = Request(
        "https://accounts.spotify.com/api/token",
        data=b"grant_type=client_credentials",
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type":  "application/x-www-form-urlencoded",
        },
    )
    with urlopen(req, timeout=15) as r:
        data          = json.loads(r.read().decode())
        _token        = data["access_token"]
        _token_expiry = now + data.get("expires_in", 3600)
    return _token


def sp_get(path, params=None):
    token = get_token()
    url   = f"{BASE}/{path}"
    if params:
        url += "?" + urlencode(params)
    req = Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except HTTPError as e:
        if e.code == 429:
            retry = int(e.headers.get("Retry-After", 5))
            print(f"  Rate limited — sleeping {retry}s")
            time.sleep(retry)
            return sp_get(path, params)
        print(f"  Spotify error {path}: {e}")
        return {}
    except Exception as e:
        print(f"  Spotify error {path}: {e}")
        return {}


def search_playlists(query, offset=0, limit=10):
    data = sp_get("search", {
        "q":     query,
        "type":  "playlist",
        "limit": limit,
        "offset": offset,
    })
    return data.get("playlists", {}).get("items", [])


def get_playlist_details(playlist_id):
    return sp_get(f"playlists/{playlist_id}", {
        "fields": "id,name,description,followers,owner,tracks.total",
        "market": "IN",
    })


def get_playlist_tracks(playlist_id, limit=50):
    data = sp_get(f"playlists/{playlist_id}/tracks", {
        "fields": "items(track(artists(id,name)))",
        "limit":  limit,
    })
    return data.get("items", [])


def get_user_profile(user_id):
    return sp_get(f"users/{user_id}")


def get_user_playlists(user_id, limit=10):
    data = sp_get(f"users/{user_id}/playlists", {"limit": limit})
    return data.get("items", [])


def count_indie_tracks(tracks):
    count = 0
    for item in tracks:
        track = item.get("track")
        if not track:
            continue
        for artist in track.get("artists", []):
            if artist.get("id") in KNOWN_INDIE_ARTIST_IDS:
                count += 1
                break
    return count


def detect_languages(name, description):
    text = f"{name} {description}".lower()
    langs = []
    checks = {
        "Tamil":     ["tamil", "kollywood", "chennai"],
        "Telugu":    ["telugu", "tollywood", "hyderabad"],
        "Kannada":   ["kannada", "bangalore", "bengaluru"],
        "Malayalam": ["malayalam", "kerala"],
        "Bengali":   ["bengali", "bangla", "kolkata"],
        "Punjabi":   ["punjabi", "punjab"],
        "Marathi":   ["marathi", "maharashtra", "pune"],
        "Hindi":     ["hindi", "hindi indie", "bollywood indie"],
    }
    for lang, kws in checks.items():
        if any(k in text for k in kws):
            langs.append(lang)
    if not langs:
        langs = ["English"]
    return langs


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET not set")
        return

    # curator_id -> entry
    curators: dict = {}
    seen_playlists = set()

    for query in PLAYLIST_QUERIES:
        print(f"  searching playlists: {query!r}")
        for offset in [0, 10]:
            playlists = search_playlists(query, offset=offset)
            if not playlists:
                break

            for pl in playlists:
                if not pl:
                    continue
                pl_id  = pl.get("id", "")
                if not pl_id or pl_id in seen_playlists:
                    continue
                seen_playlists.add(pl_id)

                owner    = pl.get("owner", {})
                owner_id = owner.get("id", "")
                if not owner_id or owner_id == "spotify":
                    continue  # skip Spotify's own editorial playlists

                followers = (pl.get("followers") or {}).get("total", 0)
                if followers is None:
                    followers = 0

                # Fetch full details if needed
                if followers < MIN_PLAYLIST_FOLLOWERS:
                    detail = get_playlist_details(pl_id)
                    followers = (detail.get("followers") or {}).get("total", 0) or 0
                    if followers < MIN_PLAYLIST_FOLLOWERS:
                        continue

                tracks_total = pl.get("tracks", {}).get("total", 0) or 0
                if tracks_total < MIN_PLAYLIST_TRACKS:
                    continue

                # Sample tracks to verify Indian indie content
                tracks      = get_playlist_tracks(pl_id)
                indie_count = count_indie_tracks(tracks)

                pl_name = pl.get("name", "")
                pl_desc = pl.get("description", "")

                # Accept if has known indie tracks OR has strong Indian indie keywords in name
                india_re = re.compile(
                    r"\b(india|indian|indie|desi|hindi|tamil|telugu|kannada|"
                    r"malayalam|bengali|punjabi|marathi)\b", re.IGNORECASE
                )
                if indie_count < MIN_INDIE_TRACKS and not india_re.search(f"{pl_name} {pl_desc}"):
                    continue

                if owner_id not in curators:
                    curators[owner_id] = {
                        "spotify_user_id": owner_id,
                        "display_name":    owner.get("display_name") or owner_id,
                        "playlists":       [],
                        "total_followers": 0,
                    }

                curators[owner_id]["playlists"].append({
                    "id":          pl_id,
                    "name":        pl_name,
                    "url":         f"https://open.spotify.com/playlist/{pl_id}",
                    "followers":   followers,
                    "tracks":      tracks_total,
                    "indie_count": indie_count,
                    "languages":   detect_languages(pl_name, pl_desc),
                })
                curators[owner_id]["total_followers"] = max(
                    curators[owner_id]["total_followers"], followers
                )

            time.sleep(0.4)
        time.sleep(0.3)

    # Enrich curators with user profiles
    print(f"\nEnriching {len(curators)} curator profiles...")
    for uid, curator in list(curators.items()):
        profile = get_user_profile(uid)
        curator["display_name"] = profile.get("display_name") or curator["display_name"]
        curator["profile_url"]  = f"https://open.spotify.com/user/{uid}"
        # Count all public playlists
        user_pls = get_user_playlists(uid)
        curator["public_playlist_count"] = len(user_pls)
        time.sleep(0.3)

    # Build reviewer entries
    reviewers = []
    for uid, c in curators.items():
        pls = c.get("playlists", [])
        if not pls:
            continue
        top_pl   = sorted(pls, key=lambda p: p["followers"], reverse=True)[0]
        all_langs = list({lang for pl in pls for lang in pl.get("languages", [])})
        name     = c.get("display_name") or uid

        reviewers.append({
            "id":       re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"),
            "category": "spotify_curator",
            "name":     name,
            "url":      c.get("profile_url", f"https://open.spotify.com/user/{uid}"),
            "description": (
                f"Spotify curator with {len(pls)} Indian indie playlist(s). "
                f"Top playlist: '{top_pl['name']}' ({top_pl['followers']:,} followers)."
            ),
            "indie_focus": "medium" if top_pl["indie_count"] >= 5 else "low_medium",
            "languages":   all_langs or ["English"],
            "genres":      [],
            "reach": {
                "followers":          c["total_followers"],
                "avg_views":          None,
                "playlist_count":     len(pls),
                "public_playlists":   c.get("public_playlist_count", 0),
            },
            "discovery_impact": None,
            "active":          True,
            "last_verified":   datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "socials":         {},
            "youtube_url":     None,
            "pitch_to": [
                {
                    "label":   "Spotify message",
                    "contact": c.get("profile_url", f"https://open.spotify.com/user/{uid}"),
                }
            ],
            "content_types": ["playlist_feature"],
            "playlists": pls[:10],
            "notes": (
                f"{len(pls)} qualifying Indian indie playlists found. "
                f"Top playlist has {top_pl['followers']:,} followers."
            ),
        })

    reviewers.sort(key=lambda r: r["reach"]["followers"] or 0, reverse=True)
    for i, r in enumerate(reviewers, 1):
        r["rank"] = i

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "category":     "spotify_curator",
        "total":        len(reviewers),
        "reviewers":    reviewers,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWritten → {OUTPUT_PATH}")
    print(f"  {len(reviewers)} qualifying Spotify curators from {len(seen_playlists)} playlists scanned")


if __name__ == "__main__":
    main()
