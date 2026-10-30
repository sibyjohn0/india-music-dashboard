#!/usr/bin/env python3
"""fetch_playlist_insights.py: discover India-focused indie playlists at
scale via Spotify's search API, and track which ones are actively being
maintained right now.

WHY: the existing reviewers.json "Spotify Curators" bucket has only 9
India-tagged entries, and they're thin (brand name + garbled genre tags +
a SubmitHub link, no real contact). This is a different, complementary
thing: real PLAYLISTS (not curator-brand profiles), including ones run by
ordinary people, discovered by actually searching Spotify rather than
depending on SubmitHub's crawl.

TECHNICAL CONSTRAINT (confirmed by hand before writing this): our Spotify
app only has client-credentials access, which blocks the /playlists/{id}/
tracks endpoint entirely (403, even on our own playlist): this is the
same 2024-era restriction that already broke /top-tracks and follower
counts for artists. So we cannot see which tracks were added or when.
What IS available on every playlist, including from the /search endpoint
directly (no extra per-playlist call needed): name, description, owner
(display name + profile link), public/collaborative flags, and a
snapshot_id that changes every time the playlist is edited.

"Live action" signal: we snapshot each playlist's snapshot_id on every
run. If it's different from last time, the playlist was actively edited
since: a real, honest "this is being maintained right now" signal, just
coarser than track-level (we know THAT it changed, not WHAT changed).

Run: SPOTIFY_CLIENT_ID=... SPOTIFY_CLIENT_SECRET=... python3 scripts/fetch_playlist_insights.py
Outputs: data/playlist_insights.json (current snapshot + curator rollup)
Reads/writes: data/playlist_insights_history.json (snapshot_id history, so
"recently active" survives across runs: do not delete this file)
"""
import json, os, re, sys, time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import HTTPError
from base64 import b64encode
from datetime import datetime, timezone

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
REPO = Path(__file__).resolve().parent.parent
DATA_DIR = REPO / "data"
OUT_PATH = DATA_DIR / "playlist_insights.json"
HISTORY_PATH = DATA_DIR / "playlist_insights_history.json"

LANGUAGES = [
    "Hindi", "Punjabi", "Tamil", "Telugu", "Kannada", "Malayalam",
    "Bengali", "Marathi", "Gujarati",
]
LANG_MODIFIERS = ["indie", "indie music", "indie songs", "underground"]
EXTRA_QUERIES = [
    "indie india", "india indie music", "desi indie", "indie english india",
    "indian indie artists", "independent music india",
]

def build_queries():
    qs = list(EXTRA_QUERIES)
    for lang in LANGUAGES:
        for mod in LANG_MODIFIERS:
            qs.append(f"{lang} {mod}")
    return qs

SEARCH_QUERIES = build_queries()

# Skip Spotify's own editorial playlists (owner id "spotify"): those
# aren't run by an individual, which is the whole point of this list.
EXCLUDE_OWNER_IDS = {"spotify", "spotifycharts"}

CONTACT_PHONE_RE = re.compile(r'(?:\+?91[\s-]?)?\b[6-9]\d{9}\b')
CONTACT_EMAIL_RE = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
WHATSAPP_HINT_RE = re.compile(r'whats\s*app', re.I)

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
        method="POST",
    )
    with urlopen(req, timeout=10) as r:
        d = json.loads(r.read())
    _token = d["access_token"]
    _token_expiry = time.time() + d["expires_in"]
    return _token


def api_get(path, params=None, _retries=3):
    url = f"https://api.spotify.com/v1{path}"
    if params:
        url += "?" + urlencode(params)
    req = Request(url, headers={"Authorization": f"Bearer {get_token()}"})
    try:
        with urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except HTTPError as e:
        if e.code == 429 and _retries > 0:
            retry = int(e.headers.get("Retry-After", 3))
            print(f"  rate limit, sleeping {retry}s")
            time.sleep(retry)
            return api_get(path, params, _retries - 1)
        if e.code == 403:
            return None  # expected for some private/restricted playlists
        print(f"  HTTP {e.code} on {path}")
        return None
    except Exception as e:
        print(f"  error on {path}: {e}")
        return None


# EDGE CASE (confirmed by hand, matches a known quirk already documented
# elsewhere in this repo's Spotify pipeline code): market=IN caps limit at
# 10: anything higher is a flat 400 "Invalid limit", undocumented by Spotify.
SEARCH_LIMIT = 10

def search_playlists(query, offset=0, limit=SEARCH_LIMIT):
    data = api_get("/search", {"q": query, "type": "playlist", "market": "IN",
                                "limit": limit, "offset": offset})
    if not data:
        return [], 0
    block = data.get("playlists") or {}
    items = [i for i in (block.get("items") or []) if i]
    return items, block.get("total", 0)


def extract_contact(description):
    if not description:
        return None
    out = {}
    email = CONTACT_EMAIL_RE.search(description)
    if email:
        out["email"] = email.group(0)
    phone = CONTACT_PHONE_RE.search(description)
    if phone:
        out["phone"] = phone.group(0)
        out["whatsapp_mentioned"] = bool(WHATSAPP_HINT_RE.search(description))
    return out or None


def discover():
    """Sweep all search queries, return deduped playlist records keyed by id."""
    found = {}
    for qi, query in enumerate(SEARCH_QUERIES):
        print(f"  [{qi+1}/{len(SEARCH_QUERIES)}] {query!r}...")
        items = []
        total = None
        for offset in range(0, 50, SEARCH_LIMIT):  # up to 5 pages = 50 results/query
            page, total = search_playlists(query, offset=offset)
            if not page:
                break
            items += page
            if offset + SEARCH_LIMIT >= total:
                break
            time.sleep(0.1)
        for pl in items:
            pid = pl.get("id")
            if not pid:
                continue
            owner = pl.get("owner") or {}
            if (owner.get("id") or "").lower() in EXCLUDE_OWNER_IDS:
                continue
            name = pl.get("name") or ""
            desc = pl.get("description") or ""
            # Quality filter: fuzzy search surfaces loosely-related results
            # (e.g. a generic Bollywood road-trip playlist for "hindi indie").
            # Require "indie" to actually appear somewhere in the playlist's
            # own text, not just in the query that found it.
            if "indie" not in (name + " " + desc).lower():
                continue
            rec = found.get(pid)
            if rec is None:
                rec = {
                    "id": pid,
                    "name": name,
                    "description": desc,
                    "owner_id": owner.get("id"),
                    "owner_name": owner.get("display_name"),
                    "owner_url": (owner.get("external_urls") or {}).get("spotify"),
                    "url": (pl.get("external_urls") or {}).get("spotify"),
                    "image": (pl.get("images") or [{}])[0].get("url"),
                    "public": pl.get("public"),
                    "collaborative": pl.get("collaborative"),
                    "snapshot_id": pl.get("snapshot_id"),
                    "matched_queries": [],
                    "contact": extract_contact(desc),
                }
                found[pid] = rec
            if query not in rec["matched_queries"]:
                rec["matched_queries"].append(query)
        time.sleep(0.15)
    return found


def infer_languages(rec):
    langs = set()
    for q in rec["matched_queries"]:
        for lang in LANGUAGES:
            if q.lower().startswith(lang.lower()):
                langs.add(lang)
    return sorted(langs)


def load_history():
    if HISTORY_PATH.exists():
        return json.loads(HISTORY_PATH.read_text())
    return {}


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set", file=sys.stderr)
        sys.exit(1)

    print("Getting Spotify token...")
    get_token()
    print("  OK")

    print(f"Searching {len(SEARCH_QUERIES)} queries for India-indie playlists...")
    found = discover()
    print(f"  {len(found)} unique playlists after owner/quality filtering")

    history = load_history()
    now_iso = datetime.now(timezone.utc).isoformat()
    new_history = {}
    recently_changed = 0

    playlists = []
    for pid, rec in found.items():
        rec["languages"] = infer_languages(rec)
        prev = history.get(pid)
        if prev and prev.get("snapshot_id") == rec["snapshot_id"]:
            last_changed_at = prev.get("last_changed_at")
        else:
            last_changed_at = now_iso
            if prev:  # existed before, snapshot changed = real activity
                recently_changed += 1
        rec["last_changed_at"] = last_changed_at
        rec["first_seen_at"] = (prev or {}).get("first_seen_at", now_iso)
        new_history[pid] = {
            "snapshot_id": rec["snapshot_id"],
            "last_changed_at": last_changed_at,
            "first_seen_at": rec["first_seen_at"],
        }
        del rec["matched_queries"][3:]  # keep it to a few representative queries
        playlists.append(rec)

    playlists.sort(key=lambda r: r["last_changed_at"], reverse=True)

    # Roll up by owner: this is how one person running many playlists
    # (confirmed real cases exist, e.g. 40+ playlists under one curator)
    # becomes visible as a single "curator" rather than N disconnected rows.
    curators = {}
    for rec in playlists:
        oid = rec.get("owner_id")
        if not oid:
            continue
        c = curators.setdefault(oid, {
            "owner_id": oid,
            "owner_name": rec["owner_name"],
            "owner_url": rec["owner_url"],
            "playlist_ids": [],
            "languages": set(),
            "contact": None,
        })
        c["playlist_ids"].append(rec["id"])
        c["languages"].update(rec["languages"])
        if not c["contact"] and rec["contact"]:
            c["contact"] = rec["contact"]
    curator_list = []
    for c in curators.values():
        c["languages"] = sorted(c["languages"])
        c["playlist_count"] = len(c["playlist_ids"])
        curator_list.append(c)
    curator_list.sort(key=lambda c: -c["playlist_count"])

    output = {
        "generated_at": now_iso,
        "queries_run": len(SEARCH_QUERIES),
        "playlist_count": len(playlists),
        "curator_count": len(curator_list),
        "recently_changed_this_run": recently_changed,
        "playlists": playlists,
        "curators": curator_list,
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    HISTORY_PATH.write_text(json.dumps(new_history, indent=2, ensure_ascii=False))
    print(f"Written -> {OUT_PATH} ({len(playlists)} playlists, {len(curator_list)} curators, {recently_changed} changed since last run)")


if __name__ == "__main__":
    main()
