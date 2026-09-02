#!/usr/bin/env python3
"""
fetch_radar_photos.py — auto-fetch official artist photos for the Radar allowlist.

Workflow: add an artist to data/radar_allowlist.json (name + handle, optionally a
`spotify` id/url for an exact match), run this, then run generate_radar.py. For
each artist without a cached photo, it looks them up on Spotify, downloads their
official artist image to data/radar_artists/<slug>.jpg, and writes that path back
into the allowlist `image` field. generate_radar.py then renders real faces
(and drops anyone still without a photo).

Needs SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET. If not in the environment, this
tries ~/Downloads/music_db/.env and the repo .env.
"""
import os, re, io, json, sys, urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ALLOW = REPO / "data" / "radar_allowlist.json"
PHOTOS = REPO / "data" / "radar_artists"

def load_env():
    if os.environ.get("SPOTIFY_CLIENT_ID") and os.environ.get("SPOTIFY_CLIENT_SECRET"):
        return
    for p in [Path.home() / "Downloads/music_db/.env", REPO / ".env"]:
        if p.exists():
            for line in p.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()
sys.path.insert(0, str(REPO / "scripts"))
try:
    from fetch_spotify import get_token, api_get   # reuse the repo's Spotify auth
except Exception as e:
    print(f"ERROR importing Spotify helpers: {e}", file=sys.stderr); sys.exit(1)

def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

def spotify_id_from(entry):
    s = (entry.get("spotify") or "").strip()
    if not s:
        return None
    m = re.search(r"artist[/:]([A-Za-z0-9]+)", s)     # url or uri
    return m.group(1) if m else (s if re.fullmatch(r"[A-Za-z0-9]{22}", s) else None)

def best_match(name):
    """Search Spotify and return (artist_name, image_url, id, followers) or None."""
    data = api_get("/search", {"q": name, "type": "artist", "market": "IN", "limit": 5})
    items = (data or {}).get("artists", {}).get("items", [])
    if not items:
        return None
    nl = name.lower()
    exact = [a for a in items if a.get("name", "").lower() == nl]
    a = (exact or items)[0]
    imgs = a.get("images", [])
    return (a.get("name"), imgs[0]["url"] if imgs else None, a.get("id"),
            a.get("followers", {}).get("total", 0))

def fetch_by_id(aid):
    a = api_get(f"/artists/{aid}")
    if not a:
        return None
    imgs = a.get("images", [])
    return (a.get("name"), imgs[0]["url"] if imgs else None, aid,
            a.get("followers", {}).get("total", 0))

def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    dest.write_bytes(urllib.request.urlopen(req, timeout=20).read())

def main():
    if not (os.environ.get("SPOTIFY_CLIENT_ID") and os.environ.get("SPOTIFY_CLIENT_SECRET")):
        print("ERROR: set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET (or add them to "
              "~/Downloads/music_db/.env).", file=sys.stderr); sys.exit(1)
    get_token()  # warm auth / fail fast
    PHOTOS.mkdir(parents=True, exist_ok=True)
    doc = json.load(open(ALLOW))
    artists = doc.get("artists", [])
    got = skipped = missed = 0
    for e in artists:
        name = (e.get("name") or "").strip()
        if not name:
            continue
        dest = PHOTOS / f"{slug(name)}.jpg"
        if dest.exists() and e.get("image"):
            skipped += 1; continue
        aid = spotify_id_from(e)
        res = fetch_by_id(aid) if aid else best_match(name)
        if not res or not res[1]:
            print(f"  MISS  {name}: no Spotify photo found "
                  f"({'bad id' if aid else 'no search match'}) — add a `spotify` link or a local image.")
            missed += 1; continue
        matched, url, sid, followers = res
        try:
            download(url, dest)
        except Exception as ex:
            print(f"  MISS  {name}: download failed ({ex})"); missed += 1; continue
        e["image"] = f"data/radar_artists/{slug(name)}.jpg"
        e["spotify_id"] = sid
        got += 1
        flag = "" if aid or matched.lower() == name.lower() else "  <-- VERIFY match"
        print(f"  OK    {name}: matched '{matched}' ({followers:,} followers){flag}")
    json.dump(doc, open(ALLOW, "w"), indent=2, ensure_ascii=False)
    print(f"\nfetch_radar_photos: {got} fetched, {skipped} cached, {missed} missing. "
          f"Photos in {PHOTOS}, paths written to radar_allowlist.json.")

if __name__ == "__main__":
    main()
