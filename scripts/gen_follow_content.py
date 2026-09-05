#!/usr/bin/env python3
"""Follow-driving content: 'Gigs this week in <city>' carousel + a 'feature call'
post. Poppy brand (matches the website + social_brand.py), 1080x1350.
Output: social/ (gitignored). On-demand."""
import json, glob, re
from datetime import date, timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
FONTS = REPO / "assets" / "fonts"
W, H = 1080, 1350
# poppy palette (see social_brand.py). WHITE/CARD are ink so headings read on cream.
BG=(255,247,238); CARD=(36,27,46); ACC=(255,77,141); WHITE=(36,27,46)
MUT=(107,96,118); MINT=(18,140,104)
def F(n,s): return ImageFont.truetype(str(FONTS/n),s)
HEAD="BricolageGrotesque.ttf"; BODY="Inter.ttf"; MONO="SpaceMono-Bold.ttf"

def wrap(d,t,f,mw):
    o=[];c=""
    for w in t.split():
        s=(c+" "+w).strip()
        if d.textlength(s,font=f)<=mw:c=s
        else:o.append(c);c=w
    if c:o.append(c)
    return o
def base():
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im); d.rectangle([0,0,W,8],fill=ACC); return im,d
def footer(d,page=None,total=None):
    cy=H-64; d.ellipse([64,cy-13,64+26,cy+13],fill=ACC); d.ellipse([73,cy-4,73+8,cy+4],fill=BG)
    d.text((104,H-78),"@indiemusicindia.co",font=F(MONO,26),fill=MUT)
    if page: d.text((W-64,H-78),f"{page}/{total}",font=F(MONO,26),fill=MUT,anchor="ra")

def pill(d,x,y,text,fs=26):
    """Rounded button sized to its text so it never overflows."""
    f=F(MONO,fs); tw=d.textlength(text,font=f)
    d.rounded_rectangle([x,y,x+tw+68,y+76],radius=14,fill=ACC,outline=(36,27,46),width=3)
    d.text((x+34,y+24),text,font=f,fill=(255,255,255))
    return y+76

def body(d,x,y,text,fs=42,fill=(58,49,66),lh=54):
    for ln in wrap(d,text,F(BODY,fs),W-2*x): d.text((x,y),ln,font=F(BODY,fs),fill=fill); y+=lh
    return y

# ---------- gigs this week ----------
def gigs_week(city, rx):
    today=date.today(); wk=today+timedelta(days=9)
    DROP=re.compile(r"comedy|standup|stand-up|quiz|brunch|kids|workshop|open mic|karaoke|"
                    r"bhajan|krishn|janmashtami|devotional|kirtan|satsang|tribute|ladies|retro night", re.I)
    seen=set(); gigs=[]
    for f in glob.glob(str(REPO/"data/events-*.json")):
        d=json.load(open(f)); arr=d.get("events",[]) if isinstance(d,dict) else d
        for e in arr:
            name=(e.get("name") or "").strip(); c=(e.get("city") or ""); v=(e.get("venue") or ""); dt=(e.get("date") or "")[:10]
            if not name or DROP.search(name) or DROP.search(v): continue
            if not (rx.search(c) or rx.search(v)): continue
            if not re.match(r"\d{4}-\d{2}-\d{2}",dt) or not(today.isoformat()<=dt<=wk.isoformat()): continue
            k=name.lower()
            if k in seen: continue
            seen.add(k)
            # clean the name (drop trailing "| City" etc.)
            nm=re.split(r"\s*[|]\s*", name)[0]
            gigs.append((dt, nm, v))
    gigs.sort()
    return gigs[:10], today, wk

def build_gigs(city, rx):
    gigs, today, wk = gigs_week(city, rx)
    out = REPO/"social"/f"gigs-week-{city.lower()}"; out.mkdir(parents=True, exist_ok=True)
    rng = f"{today.strftime('%d')}–{wk.strftime('%d %b').upper()}"
    per=5; chunks=[gigs[i:i+per] for i in range(0,len(gigs),per)]
    total=1+len(chunks)+1
    # cover
    im,d=base(); x=72
    d.text((x,150),"GIGS THIS WEEK",font=F(MONO,32),fill=ACC)
    y=250
    for ln in wrap(d,f"Live in {city}",F(HEAD,120),W-120): d.text((x,y),ln,font=F(HEAD,120),fill=WHITE); y+=128
    d.text((x,y+16),f"{len(gigs)} shows worth leaving the house for",font=F(BODY,42),fill=MINT)
    d.text((x,y+74),f"{rng}",font=F(MONO,30),fill=MUT)
    d.text((x,H-190),"Swipe the list, then save it →",font=F(BODY,38),fill=MUT)
    footer(d,1,total); im.save(out/"slide_01.png")
    # list slides
    def dchip(dt):
        from datetime import date as D
        d0=D.fromisoformat(dt); return d0.strftime("%d %b").upper()
    for ci,ch in enumerate(chunks):
        im,d=base(); x=72
        d.text((x,120),f"{city.upper()} · {rng}",font=F(MONO,28),fill=ACC)
        y=210
        for dt,nm,v in ch:
            d.rounded_rectangle([x,y,x+150,y+66],radius=12,fill=CARD)
            d.text((x+75,y+33),dchip(dt),font=F(MONO,24),fill=ACC,anchor="mm")
            tx=x+180
            nl=wrap(d,nm,F(HEAD,42),W-tx-72)[:2]; yy=y
            for ln in nl: d.text((tx,yy),ln,font=F(HEAD,42),fill=WHITE); yy+=48
            if v: d.text((tx,yy),v[:40],font=F(BODY,30),fill=MUT); yy+=40
            y=max(yy,y+66)+30
            if y>H-200: break
        footer(d,2+ci,total); im.save(out/f"slide_{2+ci:02d}.png")
    # follow CTA
    im,d=base(); x=72
    d.text((x,150),"NEVER MISS A SHOW",font=F(MONO,32),fill=ACC)
    y=260
    for ln in ["New gigs","every week."]:
        col=ACC if ln=="every week." else WHITE
        d.text((x,y),ln,font=F(HEAD,110),fill=col); y+=120
    yy=body(d,x,y+20,"We round up the shows worth your time in your city, every week.")
    pill(d,x,yy+24,"Follow @indiemusicindia.co")
    footer(d,total,total); im.save(out/f"slide_{total:02d}.png")
    print(f"gigs-week {city}: {total} slides ({len(gigs)} gigs) -> {out}")

# ---------- feature call ----------
def build_feature_call():
    out=REPO/"social"/"feature-call"; out.mkdir(parents=True,exist_ok=True)
    im,d=base(); x=72
    d.text((x,150),"ON OUR RADAR",font=F(MONO,32),fill=ACC)
    y=300
    for ln in ["Making music?"]:
        d.text((x,y),ln,font=F(HEAD,96),fill=WHITE); y+=110
    d.text((x,y),"Show us.",font=F(HEAD,150),fill=ACC); y+=190
    d.text((x,y),"Drop your latest release in the comments.",font=F(BODY,44),fill=(36,27,46)); y+=60
    y=body(d,x,y,"We feature the ones we love on The Radar, every week. No fee, no catch. Independent Indian artists only.",fs=40,fill=MUT,lh=52)
    pill(d,x,y+40,"Follow so we can find you")
    footer(d); im.save(out/"single_feature_call.png")
    print(f"feature-call: 1 slide -> {out}")

def build_news():
    d0=json.load(open(REPO/"data/news-rss.json"))
    arts=[a for a in d0.get("articles",[]) if a.get("title")][:8]
    out=REPO/"social"/"news-week"; out.mkdir(parents=True,exist_ok=True)
    per=4; chunks=[arts[i:i+per] for i in range(0,len(arts),per)]
    total=1+len(chunks)+1
    im,d=base(); x=72
    d.text((x,150),"THIS WEEK IN",font=F(MONO,32),fill=ACC)
    y=250
    for ln in ["Indian","music."]:
        col=ACC if ln=="music." else WHITE
        d.text((x,y),ln,font=F(HEAD,130),fill=col); y+=138
    d.text((x,y+16),"The headlines that matter, in 30 seconds.",font=F(BODY,42),fill=MINT)
    d.text((x,H-190),"Swipe, then save →",font=F(BODY,38),fill=MUT)
    footer(d,1,total); im.save(out/"slide_01.png")
    for ci,ch in enumerate(chunks):
        im,d=base(); x=72
        d.text((x,120),"ON THE WIRE",font=F(MONO,28),fill=ACC); y=210
        for a in ch:
            pub=(a.get("publication") or "").upper()
            d.text((x,y),pub[:28],font=F(MONO,24),fill=MUT); y+=40
            for ln in wrap(d,a["title"],F(HEAD,44),W-140)[:3]:
                d.text((x,y),ln,font=F(HEAD,44),fill=WHITE); y+=52
            y+=34
            if y>H-220: break
        footer(d,2+ci,total); im.save(out/f"slide_{2+ci:02d}.png")
    im,d=base(); x=72
    d.text((x,150),"STAY IN THE LOOP",font=F(MONO,32),fill=ACC); y=260
    for ln in ["The scene,","every week."]:
        col=ACC if ln=="every week." else WHITE
        d.text((x,y),ln,font=F(HEAD,110),fill=col); y+=120
    yy=body(d,x,y+20,"We track Indian music news so you don't have to.")
    pill(d,x,yy+24,"Follow @indiemusicindia.co")
    footer(d,total,total); im.save(out/f"slide_{total:02d}.png")
    print(f"news-week: {total} slides ({len(arts)} headlines) -> {out}")

if __name__ == "__main__":
    import sys
    if "news" in sys.argv: build_news()
    elif "feature" in sys.argv: build_feature_call()
    else:
        build_gigs("Bengaluru", re.compile(r"bengaluru|bangalore|koramangala|indiranagar|whitefield|hsr|jayanagar", re.I))
        build_feature_call()
        build_news()
