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
LOG_PATH = DATA_DIR / "playlist_insights_log.json"
MAX_LOG_ENTRIES = 365  # one compact entry/day -- this caps the file at roughly a year, not unbounded growth

LANGUAGES = [
    "Hindi", "Punjabi", "Tamil", "Telugu", "Kannada", "Malayalam",
    "Bengali", "Marathi", "Gujarati", "Urdu", "Assamese", "Odia", "Konkani",
]
LANG_MODIFIERS = [
    "indie", "indie music", "indie songs", "indie 2026", "underground",
    "indie pop", "indie folk", "indie rock", "bedroom pop",
    "singer songwriter", "lo-fi", "indie hip hop", "alternative",
]
EXTRA_QUERIES = [
    "indie india", "india indie music", "desi indie", "indie english india",
    "indian indie artists", "independent music india", "indie india 2026",
    "mumbai indie", "bangalore indie", "delhi indie", "chennai indie",
    "kolkata indie", "pune indie", "hyderabad indie", "goa indie",
    "india indie rock", "india indie folk", "india indie pop",
    "india bedroom pop", "india singer songwriter", "india lo-fi",
    "desi hip hop indie", "india alternative music",
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


# Confirmed by hand: a 429 can come back with Retry-After in the TENS OF
# THOUSANDS of seconds (one case: 75,996s, ~21 hours) -- not a transient
# throttle, a real "you've been cut off" response. Blindly sleeping for
# whatever the header says turns one bad response into an invisible
# multi-hour hang (this happened once, looked exactly like a stuck process
# until the unbuffered log line revealed it). Cap it: short waits still
# retry automatically, anything longer aborts loudly instead of blocking.
MAX_RATE_LIMIT_WAIT = 30

_severe_rate_limit_hit = False

def api_get(path, params=None, _retries=3):
    global _severe_rate_limit_hit
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
            if retry > MAX_RATE_LIMIT_WAIT:
                print(f"  SEVERE rate limit (Retry-After {retry}s) -- aborting this call, not waiting it out")
                _severe_rate_limit_hit = True
                return None
            if _retries > 0:
                print(f"  rate limit, sleeping {retry}s")
                time.sleep(retry)
                return api_get(path, params, _retries - 1)
            return None
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
        if _severe_rate_limit_hit:
            print(f"  Stopping early at query {qi+1}/{len(SEARCH_QUERIES)}: severe rate limit hit, "
                  f"continuing would just rack up more failed calls against an active ban.")
            break
        print(f"  [{qi+1}/{len(SEARCH_QUERIES)}] {query!r}...")
        items = []
        total = None
        for offset in range(0, 100, SEARCH_LIMIT):  # up to 10 pages = 100 results/query
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


def enrich_followers(found):
    """One GET per discovered playlist for follower count (not available from
    /search). The /tracks sub-resource is blocked for our tier, but this
    top-level GET works fine -- same call proven by hand before this was written."""
    n = len(found)
    for i, (pid, rec) in enumerate(found.items()):
        if _severe_rate_limit_hit:
            print(f"    Stopping follower enrichment early at {i+1}/{n}: severe rate limit hit.")
            break
        if (i + 1) % 25 == 0:
            print(f"    followers: {i+1}/{n}")
        data = api_get(f"/playlists/{pid}", {"fields": "followers.total"})
        rec["followers"] = (data or {}).get("followers", {}).get("total")
        time.sleep(0.08)


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

    print("Fetching follower counts...")
    enrich_followers(found)

    history = load_history()
    now_iso = datetime.now(timezone.utc).isoformat()
    new_history = {}
    recently_changed = 0

    playlists = []
    new_today = []
    gainers = []
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
        if not prev:
            new_today.append(rec["name"])
        prev_followers = (prev or {}).get("followers")
        cur_followers = rec.get("followers")
        if prev and prev_followers is not None and cur_followers is not None:
            delta = cur_followers - prev_followers
            if delta > 0:
                gainers.append({"name": rec["name"], "owner": rec["owner_name"], "delta": delta, "followers": cur_followers})
        new_history[pid] = {
            "snapshot_id": rec["snapshot_id"],
            "last_changed_at": last_changed_at,
            "first_seen_at": rec["first_seen_at"],
            "followers": cur_followers,
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
            "total_followers": 0,
        })
        c["playlist_ids"].append(rec["id"])
        c["languages"].update(rec["languages"])
        c["total_followers"] += rec.get("followers") or 0
        if not c["contact"] and rec["contact"]:
            c["contact"] = rec["contact"]
    curator_list = []
    for c in curators.values():
        c["languages"] = sorted(c["languages"])
        c["playlist_count"] = len(c["playlist_ids"])
        curator_list.append(c)
    curator_list.sort(key=lambda c: (-c["playlist_count"], -c["total_followers"]))

    lang_counts = {}
    for p in playlists:
        for l in p["languages"]:
            lang_counts[l] = lang_counts.get(l, 0) + 1
    gainers.sort(key=lambda g: -g["delta"])

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

    # Daily pattern log: one small entry per day, not a full dump, so this
    # stays readable and git-diffable even after months of runs. This is
    # what "watch for patterns over time" actually means: growth, new
    # discoveries and actual follower movers, logged daily, not just today's
    # snapshot overwriting yesterday's with no trail.
    today = now_iso[:10]
    log = json.loads(LOG_PATH.read_text()) if LOG_PATH.exists() else []
    log = [entry for entry in log if entry.get("date") != today]  # idempotent same-day reruns
    log.append({
        "date": today,
        "generated_at": now_iso,
        "playlist_count": len(playlists),
        "curator_count": len(curator_list),
        "new_playlists_today": len(new_today),
        "new_playlist_names": new_today[:10],
        "recently_changed": recently_changed,
        "language_counts": lang_counts,
        "top_followers_gainers": gainers[:5],
    })
    log.sort(key=lambda e: e["date"])
    log = log[-MAX_LOG_ENTRIES:]
    LOG_PATH.write_text(json.dumps(log, indent=2, ensure_ascii=False))

    print(f"Written -> {OUT_PATH} ({len(playlists)} playlists, {len(curator_list)} curators, {recently_changed} changed since last run)")
    print(f"Logged -> {LOG_PATH} ({len(log)} days of history, {len(new_today)} new playlists today)")


if __name__ == "__main__":
    main()
