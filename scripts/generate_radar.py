#!/usr/bin/env python3
"""
Generate "The Radar" weekly social carousel from scraped data.

Reads:
  data/tracked_artists.json    -> indie artists + trend/growth (from build_radar.py)
  data/spotify_enrichment.json -> artist cover images + Spotify URLs (from fetch_spotify.py)

Writes:
  social/radar/slide_01.png .. slide_NN.png  -> ready-to-post 3:4 carousel
  social/radar/caption.txt                   -> caption + the artists to tag

How "rising" is chosen (mirrors build_radar.py's own logic):
  build_radar.py flags an indie artist as trend="rising" when its Last.fm global
  listeners grew >=10% since the previous snapshot, OR its India rank improved by
  more than 5 places. This script prefers those rising artists (sorted by growth),
  then fills any remaining slots with the newest / best-ranked indie acts. It only
  picks artists that also have a Spotify cover image, so every slide has a real face.

Nothing is auto-posted. A human should review the 5 picks, tag each artist, and post.
"""
import json, os, io, glob, datetime, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
FONTS = REPO / "assets" / "fonts"
OUT = REPO / "social" / "radar"
N_ARTISTS = 5

W, H, M = 1080, 1440, 120
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
def footer(d,acc,tc):
    fy=H-116; f=mono(28)
    d.ellipse([M-1,fy+1,M+29,fy+31],fill=acc,outline=tc,width=4); d.ellipse([M+9,fy+11,M+19,fy+21],fill=tc)
    d.text((M+40,fy),"@indiemusicindia.co",font=f,fill=tc)
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

def pick(enr, arts):
    """Prefer rising (growth-based) indie artists that have a cover image."""
    rows = []
    for name, e in enr.items():
        if not e.get("image"): continue
        t = arts.get(name, {})
        rows.append({"name": name, "e": e, "t": t,
                     "trend": t.get("trend"), "growth": t.get("growth_pct"),
                     "rank": t.get("india_rank"), "listeners": t.get("latest_global_listeners") or e.get("followers") or 0})
    rising = [r for r in rows if r["trend"] == "rising"]
    rising.sort(key=lambda r: (r["growth"] or 0), reverse=True)
    rest = [r for r in rows if r["trend"] != "rising"]
    # fill: newest first, then best India rank, then listeners (keeps it emerging, not mainstream)
    rest.sort(key=lambda r: (r["trend"] == "new", -(r["rank"] or 10**9), r["listeners"]), reverse=True)
    return (rising + rest)[:N_ARTISTS]

def stat_line(r):
    if r["growth"] and r["growth"] > 0: return f"▲  {r['growth']}% listeners this month"
    if r["trend"] == "new": return "New on the radar"
    if r["rank"]: return f"#{r['rank']} in India this week"
    return "On our radar"

def genre_lang(r):
    t, e = r["t"], r["e"]
    genre = t.get("genre") or (e["genres"][0].title() if e.get("genres") else "Independent")
    return " · ".join([x for x in [t.get("language"), genre] if x])

def build(picks, images):
    OUT.mkdir(parents=True, exist_ok=True)
    for f in glob.glob(str(OUT/"slide_*.png")): os.remove(f)
    wk = datetime.date.today().strftime("%d %b %Y").upper()
    total = len(picks) + 2

    img = Image.new("RGB",(W,H),INK2); d=ImageDraw.Draw(img); circ(d,W-70,120,120,MINT)
    trk(d,(M,220),f"THE RADAR · {wk}",mono(30),MINT,3)
    d.text((M,300),"Rising",font=bric(150),fill=WHITE)
    d.text((M,450),"independent",font=bric(150),fill=WHITE)
    d.text((M,600),"artists.",font=bric(150),fill=YELLOW)
    tx=M
    for r in picks[:4]:
        im=images.get(r["name"])
        if im: img.paste(cover_fit(im,190,190),(tx,900)); d=ImageDraw.Draw(img)
        d.rectangle([tx,900,tx+190,1090],outline=WHITE,width=2); tx+=200
    d.text((M,1170),"Watch these names →",font=inter(40,600),fill=(225,222,232))
    f=mono(30); d.text((W-M-tw(d,"SWIPE →",f),1180),"SWIPE →",font=f,fill=MUT)
    footer(d,MINT,WHITE); img.save(OUT/"slide_01.png")

    for i,r in enumerate(picks,2):
        img=Image.new("RGB",(W,H),CREAM); d=ImageDraw.Draw(img)
        trk(d,(M,150),f"THE RADAR · {i:02d} / {total:02d}",mono(28),PINK,3)
        box=(M,205,W-M,205+770); im=images.get(r["name"])
        if im: img.paste(cover_fit(im,box[2]-box[0],box[3]-box[1]),(box[0],box[1])); d=ImageDraw.Draw(img)
        d.rectangle([box[0],box[1],box[2]-1,box[3]-1],outline=INK,width=4)
        yy=box[3]+34
        nm=r["name"] if tw(d,r["name"],bric(74))<W-2*M else r["name"][:18]+"…"
        d.text((M,yy),nm,font=bric(74),fill=INK)
        d.text((M,yy+90),genre_lang(r),font=inter(37,600),fill=(74,64,88))
        d.text((M,yy+142),stat_line(r),font=inter(35,650),fill=PINK)
        d.text((M,H-158),"Cover: Spotify · tag the artist when you post",font=inter(26),fill=MUT)
        footer(d,PINK,INK); img.save(OUT/f"slide_{i:02d}.png")

    img=grad([PINK,VIOLET,BLUE]); d=ImageDraw.Draw(img)
    trk(d,(M,180),"THE RADAR",mono(28),YELLOW,3)
    d.text((M,330),"Found your",font=bric(84),fill=WHITE)
    d.text((M,420),"new favourite?",font=bric(84),fill=WHITE)
    d.text((M,560),"Follow for next week's rising",font=inter(39),fill=(240,236,246))
    d.text((M,614),"independent Indian artists.",font=inter(39),fill=(240,236,246))
    footer(d,YELLOW,WHITE); img.save(OUT/f"slide_{total:02d}.png")

def write_caption(picks):
    names = ", ".join(r["name"] for r in picks)
    cap = (
        "THE RADAR — this week's rising independent artists in India \U0001F3A7\n\n"
        f"Swipe for {len(picks)} acts on our radar: {names}.\n"
        "Every one is an independent artist climbing right now. Save this, and tag a "
        "friend who needs new music.\n\n"
        "TAG EACH ARTIST in the post before publishing. Verify the picks first.\n\n"
        "#indianmusic #independentartist #newmusic #indiemusic #musicdiscovery "
        "#desimusic #newmusicfriday"
    )
    (OUT/"caption.txt").write_text(cap)

def main():
    enr, arts = load()
    picks = pick(enr, arts)
    if not picks:
        print("generate_radar: no candidates with cover images, skipping.")
        return
    images = {r["name"]: fetch(r["e"]["image"]) for r in picks}
    build(picks, images)
    write_caption(picks)
    print("generate_radar: built", len(picks), "artists ->", OUT)
    print("  picks:", [f"{r['name']} ({r['trend']})" for r in picks])

if __name__ == "__main__":
    main()
