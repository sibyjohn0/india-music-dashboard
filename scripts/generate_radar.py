#!/usr/bin/env python3
"""
Generate "The Radar" weekly social carousel from scraped data.

Reads:
  data/tracked_artists.json    -> indie artists + trend/growth (from build_radar.py)
  data/spotify_enrichment.json -> artist cover images + Spotify URLs (from fetch_spotify.py)

Writes:
  social/radar/slide_01.png .. slide_NN.png  -> ready-to-post 9:16 story/reel carousel
  social/radar/caption.txt                   -> caption + the artists to tag

How "rising" is chosen (mirrors build_radar.py's own logic):
  build_radar.py flags an indie artist as trend="rising" when its Last.fm global
  listeners grew >=10% since the previous snapshot, OR its India rank improved by
  more than 5 places. This script prefers those rising artists (sorted by growth),
  then fills any remaining slots with the newest / best-ranked indie acts. It only
  picks artists that also have a Spotify cover image, so every slide has a real face.

Nothing is auto-posted. A human should review the 5 picks, tag each artist, and post.
"""
import json, os, io, glob, re, datetime, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
FONTS = REPO / "assets" / "fonts"
OUT = REPO / "social" / "radar"
EXCLUDE_PATH = DATA / "radar_exclude.json"
N_ARTISTS = 5

def load_exclude():
    """Human curation layer: names to never feature (AI/no-identity, repeats)."""
    try:
        names = json.load(open(EXCLUDE_PATH)).get("exclude", [])
        return {n.strip().lower() for n in names}
    except Exception:
        return set()

# Names that signal a compilation / mix / topic channel rather than a real artist.
# Their "cover art" is usually a text-heavy thumbnail, which also fails the clean-tile bar.
NON_ARTIST = re.compile(
    r"\b(mix|topic|playlist|lofi|lo-?fi|jukebox|mashup|non[- ]?stop|karaoke|"
    r"audio jukebox|full album|hit songs|old songs)\b", re.I)

# Label / aggregator / production channels — not individual artists. Ranking by
# listeners surfaces these, so drop them (e.g. "A2 Music Official", "Drop of Music",
# "Radha Entertainment", "MJ Production"). Real names with music inside a word
# (e.g. "MusicByRuhi") are kept because the token isn't a standalone trailing word.
LABEL = re.compile(
    r"\b(entertainment|productions?|records|studios?|media|films?|"
    r"official music|music official)\b|\bmusic$|\bmuzi[ckx]\b", re.I)

# Political / communal / devotional signals (best-effort, NAME-based only). This
# CANNOT catch content baked into a track's title or thumbnail under a neutral
# artist name — so a human eyeball on every pick before posting stays mandatory.
POLITICAL = re.compile(
    r"\b(modi|yogi|bjp|congress|kejriwal|hindutva|deshbhak|desh bhakti|andolan|"
    r"jai shree ram|jai shri ram|jai shri krishna|jai hind|har har mahadev|"
    r"bhajan|kirtan|devotional|mata rani|bhagwan|tiranga|shaheed|rashtra)\b", re.I)

W, H, M = 1080, 1920, 120   # 9:16 story/reel frames
PINK=(255,77,141); YELLOW=(255,210,63); VIOLET=(139,92,246); BLUE=(58,160,255)
MINT=(31,207,158); INK=(36,27,46); INK2=(24,18,34); CREAM=(255,247,238); WHITE=(255,255,255); MUT=(150,140,160)

def bric(sz, w=800):
    f = ImageFont.truetype(str(FONTS/"BricolageGrotesque.ttf"), sz)
    try: f.set_variation_by_axes([96, w, 100])
    except Exception: pass
    return f
def inter(sz, w=550):
    f = ImageFont.truetype(str(FONTS/"Inter.ttf"), sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def mono(sz): return ImageFont.truetype(str(FONTS/"SpaceMono-Bold.ttf"), sz)
def tw(d,t,f): return sum(d.textlength(c,font=f) for c in t)
def trk(d,pos,txt,f,fill,t):
    x,y=pos
    for ch in txt: d.text((x,y),ch,font=f,fill=fill); x+=d.textlength(ch,font=f)+t
def circ(d,cx,cy,r,fill): d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=fill)
def footer(d,acc,tc,note=None):
    # Brand mark only, no handle baked in (add the @ in the IG app when posting).
    fy=H-116
    d.ellipse([M-1,fy+1,M+29,fy+31],fill=acc,outline=tc,width=4); d.ellipse([M+9,fy+11,M+19,fy+21],fill=tc)
    if note:
        nf=inter(26); d.text((W-M-tw(d,note,nf),fy+2),note,font=nf,fill=MUT)
def grad(stops):
    yy,xx=np.mgrid[0:H,0:W]; t=((xx/W+yy/H)/2)[...,None]
    a,b,c=[np.array(s,float) for s in stops]
    return Image.fromarray(np.where(t<0.5,a+(b-a)*(t/0.5),b+(c-b)*((t-0.5)/0.5)).astype('uint8'))
def fetch(url):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        return Image.open(io.BytesIO(urllib.request.urlopen(req,timeout=20).read())).convert("RGB")
    except Exception: return None
def cover_fit(im,w,h):
    iw,ih=im.size; s=max(w/iw,h/ih); im=im.resize((int(iw*s),int(ih*s)),Image.LANCZOS); iw,ih=im.size
    return im.crop(((iw-w)//2,(ih-h)//2,(iw-w)//2+w,(ih-h)//2+h))

def load():
    enr = json.load(open(DATA/"spotify_enrichment.json")).get("enrichment", {})
    ta = json.load(open(DATA/"tracked_artists.json"))
    cont = ta.get("artists", ta) if isinstance(ta, dict) else ta
    arts = {a["name"]: a for a in (cont.values() if isinstance(cont, dict) else cont)
            if isinstance(a, dict) and a.get("name")}
    return enr, arts

def _lang(r):
    return (r["t"].get("language") or "Unknown").strip()

def _score(r):
    # Prefer real presence (Last.fm listeners), then rising growth, then better rank.
    return (r["listeners"] or 0, (r["growth"] or 0), -(r["rank"] or 10**9))

def compose(rows, skip=0):
    """Build a weekly set of 2 English + 3 Indian-language artists, using a
    different vernacular language for each of the 3 to represent the country.
    Ranked within each group by Last.fm presence. skip offsets each group for
    queueing a later week."""
    eng  = sorted([r for r in rows if _lang(r).lower() == "english"],  key=_score, reverse=True)[skip:]
    vern = sorted([r for r in rows if _lang(r).lower() != "english"],  key=_score, reverse=True)[skip:]

    picks = eng[:2]
    vpicks, used = [], set()
    for r in vern:                       # 3 distinct vernacular languages
        if _lang(r) in used: continue
        vpicks.append(r); used.add(_lang(r))
        if len(vpicks) == 3: break
    if len(vpicks) < 3:                   # not enough distinct languages: fill anyway
        for r in vern:
            if r not in vpicks: vpicks.append(r)
            if len(vpicks) == 3: break
    out = picks + vpicks
    if len(out) < N_ARTISTS:              # not enough English: top up from vernacular
        for r in vern:
            if r not in out: out.append(r)
            if len(out) == N_ARTISTS: break
    return out[:N_ARTISTS]

ALLOWLIST_PATH = DATA / "radar_allowlist.json"

def load_allowlist():
    try:
        return json.load(open(ALLOWLIST_PATH)).get("artists", [])
    except Exception:
        return []

def pick(enr, arts, skip=0, exclude=None, target=5):
    """PERMANENT FIX: the Radar is allowlist-driven. Only artists in
    data/radar_allowlist.json can be featured, so political/communal, devotional,
    aggregator and film-music content can never leak in (the old rank-then-blocklist
    model leaked them forever), and every pick carries a verified handle for tagging.
    No-repeat honoured; if the allowlist is exhausted by the no-repeat log, it cycles."""
    exclude = exclude or set()
    allow = load_allowlist()

    def rows_for(exc):
        rows = []
        for a in allow:
            name = (a.get("name") or "").strip()
            if not name or name.lower() in exc:
                continue
            e = enr.get(name, {}); t = arts.get(name, {})
            rows.append({"name": name, "e": e, "t": t,
                         "handle": a.get("handle", ""), "note": a.get("note", ""),
                         "alang": a.get("language", ""), "agenre": a.get("genre", ""),
                         "aimage": a.get("image", ""),
                         "trend": t.get("trend") or "on our radar", "growth": t.get("growth_pct"),
                         "rank": t.get("india_rank"),
                         "listeners": t.get("latest_global_listeners") or e.get("followers") or 0})
        return rows

    # Fresh only: exclude already includes the no-repeat featured log. Never pad
    # with repeats — if fewer than `target` are fresh, show fewer; if zero, the
    # caller prints "add more artists". Repeats only ever happen if a human clears
    # the radar featured log deliberately to start a new cycle.
    rows = rows_for(exclude)
    if skip:
        rows = rows[skip:] + rows[:skip]
    return rows[:target]

def stat_line(r):
    if r.get("note"): return r["note"]                       # curated one-liner wins
    if r["growth"] and r["growth"] >= 5: return f"▲  {round(r['growth'])}% listeners this month"
    if r["trend"] == "new": return "New on the radar"
    if r["rank"]: return f"#{r['rank']} in India this week"
    return "On our radar"

def genre_lang(r):
    t, e = r["t"], r["e"]
    lang = r.get("alang") or t.get("language")               # allowlist language wins
    genre = r.get("agenre") or t.get("genre") or (e["genres"][0].title() if e.get("genres") else "Independent")
    return " · ".join([x for x in [lang, genre] if x])

TILE_COLORS = [PINK, VIOLET, BLUE, MINT, YELLOW]

def artist_image(r):
    """Cover for an allowlisted artist: enrichment URL, else a local allowlist
    image, else None (a typographic tile is drawn instead so it always renders)."""
    url = r["e"].get("image")
    if url:
        try: return fetch(url)
        except Exception: pass
    p = r.get("aimage")
    if p:
        fp = Path(p) if os.path.isabs(p) else (REPO / p)
        try: return Image.open(fp).convert("RGB")
        except Exception: pass
    return None

def _initials(name):
    parts = [w for w in name.split() if w]
    return ("".join(w[0] for w in parts[:2]).upper()) or "?"

def tile(w, h, name, color, big=True):
    """Typographic fallback tile for artists with no photo yet."""
    im = Image.new("RGB", (w, h), color); d = ImageDraw.Draw(im)
    if big:
        f = bric(96)
        words, lines, cur = name.split(), [], ""
        for wd in words:
            t = (cur + " " + wd).strip()
            if d.textlength(t, font=f) <= w - 90: cur = t
            else: lines.append(cur); cur = wd
        if cur: lines.append(cur)
        lh = f.size + 10; y = (h - lh * len(lines)) // 2
        for ln in lines:
            d.text(((w - d.textlength(ln, font=f)) // 2, y), ln, font=f, fill=WHITE); y += lh
    else:
        ini = _initials(name); f = bric(int(h * 0.4))
        bb = d.textbbox((0, 0), ini, font=f)
        d.text(((w - (bb[2]-bb[0])) // 2 - bb[0], (h - (bb[3]-bb[1])) // 2 - bb[1]), ini, font=f, fill=WHITE)
    return im

def build(picks, images, out=OUT, wk=None):
    out.mkdir(parents=True, exist_ok=True)
    for f in glob.glob(str(out/"slide_*.png")): os.remove(f)
    wk = wk or datetime.date.today().strftime("%d %b %Y").upper()
    total = len(picks) + 2

    # --- Slide 1: cover (vertical rhythm tuned for the 1920px 9:16 frame) ---
    img = Image.new("RGB",(W,H),INK2); d=ImageDraw.Draw(img); circ(d,W-70,120,120,MINT)
    trk(d,(M,320),f"THE RADAR · {wk}",mono(30),MINT,3)
    d.text((M,440),"On our",font=bric(150),fill=WHITE)
    d.text((M,600),"radar.",font=bric(150),fill=YELLOW)
    d.text((M,820),"The Indian artists",font=inter(40,600),fill=(225,222,232))
    d.text((M,876),"we're watching this week.",font=inter(40,600),fill=(225,222,232))
    tx=M
    for idx,r in enumerate(picks[:4]):
        im=images.get(r["name"])
        thumb = cover_fit(im,200,200) if im else tile(200,200,r["name"],TILE_COLORS[idx%len(TILE_COLORS)],big=False)
        img.paste(thumb,(tx,1150)); d=ImageDraw.Draw(img)
        d.rectangle([tx,1150,tx+200,1350],outline=WHITE,width=2); tx+=210
    d.text((M,1450),"Watch these names →",font=inter(44,600),fill=(225,222,232))
    footer(d,MINT,WHITE); img.save(out/"slide_01.png")

    # --- Slides 2..N: one artist each, cover photo as the hero ---
    for i,r in enumerate(picks,2):
        img=Image.new("RGB",(W,H),CREAM); d=ImageDraw.Draw(img)
        trk(d,(M,170),f"THE RADAR · {i:02d} / {total:02d}",mono(28),PINK,3)
        box=(M,240,W-M,240+1060); im=images.get(r["name"]); bw,bh=box[2]-box[0],box[3]-box[1]
        hero = cover_fit(im,bw,bh) if im else tile(bw,bh,r["name"],TILE_COLORS[(i-2)%len(TILE_COLORS)],big=True)
        img.paste(hero,(box[0],box[1])); d=ImageDraw.Draw(img)
        d.rectangle([box[0],box[1],box[2]-1,box[3]-1],outline=INK,width=4)
        yy=box[3]+48
        nm=r["name"] if tw(d,r["name"],bric(76))<W-2*M else r["name"][:18]+"…"
        d.text((M,yy),nm,font=bric(76),fill=INK)
        d.text((M,yy+96),genre_lang(r),font=inter(37,600),fill=(74,64,88))
        d.text((M,yy+150),stat_line(r),font=inter(35,650),fill=PINK)
        footer(d,PINK,INK,note=("Cover art: Spotify" if im else None)); img.save(out/f"slide_{i:02d}.png")

    # --- Final slide: CTA on the brand gradient ---
    img=grad([PINK,VIOLET,BLUE]); d=ImageDraw.Draw(img)
    trk(d,(M,340),"THE RADAR",mono(28),YELLOW,3)
    d.text((M,520),"Found your",font=bric(92),fill=WHITE)
    d.text((M,632),"new favourite?",font=bric(92),fill=WHITE)
    d.text((M,820),"Follow for next week's",font=inter(42),fill=(240,236,246))
    d.text((M,878),"artists on our radar.",font=inter(42),fill=(240,236,246))
    footer(d,YELLOW,WHITE); img.save(out/f"slide_{total:02d}.png")

def load_handles():
    try:
        return json.load(open(DATA / "radar_handles.json")).get("handles", {})
    except Exception:
        return {}

def write_caption(picks, out=OUT):
    # Spotify link is reliable (from our enrichment); IG handle comes from the
    # verified radar_handles.json, else a @____ placeholder to fill by hand.
    handles = load_handles()
    lines = []
    for r in picks:
        url = r["e"].get("spotify_url", "")
        ig = r.get("handle") or handles.get(r["name"], "@______")
        lines.append(f"• {r['name']} — IG {ig}  |  {url}")
    artist_block = "\n".join(lines)
    cap = (
        "THE RADAR — the Indian artists on our radar this week \U0001F3A7\n\n"
        f"Swipe for {len(picks)} acts we're watching:\n{artist_block}\n\n"
        "Save this, and tag a friend who needs new music.\n\n"
        "TAG EACH ARTIST (fill the @handles above) before publishing. Verify the picks first.\n\n"
        "#indianmusic #independentartist #newmusic #indiemusic #musicdiscovery "
        "#desimusic #newmusicfriday"
    )
    (out/"caption.txt").write_text(cap)

def main():
    import argparse
    p = argparse.ArgumentParser(description="Build a Radar carousel from scraped data.")
    p.add_argument("--skip", type=int, default=0,
                   help="Drop the top N picks (queue a future week with the next tier).")
    p.add_argument("--out", default=None, help="Output dir (default: social/radar).")
    p.add_argument("--date", default=None,
                   help="Date label on the frames, e.g. '13 Aug 2026' (default: today).")
    p.add_argument("--exclude-extra", default="",
                   help="Comma-separated names to also skip (e.g. this week's picks, to avoid repeats next week).")
    p.add_argument("--preview", action="store_true",
                   help="Build without recording picks to the featured log (for previews).")
    a = p.parse_args()
    out = Path(a.out) if a.out else OUT
    wk = a.date.upper() if a.date else None
    import featured_log as FL
    exclude = (load_exclude()
               | FL.featured_radar()                       # never repeat an already-featured artist
               | {n.strip().lower() for n in a.exclude_extra.split(",") if n.strip()})

    enr, arts = load()
    picks = pick(enr, arts, skip=a.skip, exclude=exclude, target=N_ARTISTS * 3)  # over-fetch; drop imageless
    images = {r["name"]: artist_image(r) for r in picks}
    picks = [r for r in picks if images.get(r["name"])][:N_ARTISTS]   # PHOTOS ONLY — no image, drop the artist
    if not picks:
        print("generate_radar: no fresh allowlisted artists WITH a photo. "
              "Add artists (with Spotify presence, or a local image path) to data/radar_allowlist.json.")
        return
    images = {r["name"]: images[r["name"]] for r in picks}
    build(picks, images, out=out, wk=wk)
    write_caption(picks, out=out)
    if not a.preview:
        FL.record_radar([r["name"] for r in picks])        # record so next week won't repeat
    print("generate_radar: built", len(picks), "artists ->", out, "(preview)" if a.preview else "(recorded)")
    print("  picks:", [f"{r['name']} ({r['trend']})" for r in picks])

if __name__ == "__main__":
    main()
