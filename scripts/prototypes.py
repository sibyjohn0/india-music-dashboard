#!/usr/bin/env python3
"""Five hero-frame prototypes, each channeling a different handcrafted reference.
1080x1350 (4:5 feed). Real IMI content. Output: social/proto/frame_N.png
Honest scope: bold flat colour, grain, drawn objects, retro chrome, quote boxes and
poster type are code-doable. True collage / illustration / photography are not — those
need real assets and are noted where they'd go."""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FONTS = REPO / "assets" / "fonts"
OUT = REPO / "social" / "proto"; OUT.mkdir(parents=True, exist_ok=True)
W, H = 1080, 1350
SYS = "/System/Library/Fonts/Supplemental/"

def bric(sz, w=800):
    f = ImageFont.truetype(str(FONTS/"BricolageGrotesque.ttf"), sz)
    try: f.set_variation_by_axes([96, w, 100])
    except Exception: pass
    return f
def inter(sz, w=600):
    f = ImageFont.truetype(str(FONTS/"Inter.ttf"), sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def mono(sz): return ImageFont.truetype(str(FONTS/"SpaceMono-Bold.ttf"), sz)
def didot(sz): return ImageFont.truetype(SYS+"Didot.ttc", sz)
def tw(d,t,f): return d.textlength(t,font=f)

def grain(img, amount=16):
    a = np.asarray(img).astype("int16")
    n = np.random.randint(-amount, amount+1, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a+n, 0, 255).astype("uint8"))

def mesh(base, blobs):
    """Soft radial colour blobs over a base colour."""
    yy, xx = np.mgrid[0:H, 0:W].astype("float32")
    out = np.ones((H, W, 3), "float32") * np.array(base, "float32")
    for (cx, cy, r, col) in blobs:
        d = np.sqrt((xx-cx)**2 + (yy-cy)**2)
        w = np.clip(1 - d/r, 0, 1)[..., None] ** 1.6
        out = out*(1-w) + np.array(col, "float32")*w
    return Image.fromarray(np.clip(out,0,255).astype("uint8"))

def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t=(cur+" "+w).strip()
        if tw(d,t,f)<=maxw: cur=t
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    return lines

def trk(d,pos,txt,f,fill,t):
    x,y=pos
    for ch in txt: d.text((x,y),ch,font=f,fill=fill); x+=d.textlength(ch,font=f)+t

# ---------- Frame 1: Hinglish surreal, flat cobalt + acid + a coin ----------
def frame1():
    BLUE=(36,58,200); ACID=(214,242,74); MUST=(240,180,40); INK=(20,22,40)
    img=Image.new("RGB",(W,H),BLUE); d=ImageDraw.Draw(img)
    d.text((80,140),"1000 streams",font=bric(120,850),fill=(255,255,255))
    d.text((80,270),"ki royalty?",font=bric(120,850),fill=(255,255,255))
    d.text((80,470),"₹42.",font=bric(300,900),fill=ACID)
    trk(d,(84,820),"SPOTIFY INDIA · AUG 2026",mono(30),(200,214,255),3)
    # flat coin, bottom-right, with soft depth
    cx,cy,r=820,1120,150
    d.ellipse([cx-r+14,cy-r+18,cx+r+14,cy+r+18],fill=INK)      # shadow
    d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=MUST)
    d.ellipse([cx-r+22,cy-r+22,cx+r-22,cy+r-22],outline=INK,width=6)
    rs=bric(150,900); d.text((cx-tw(d,"₹",rs)/2,cy-110),"₹",font=rs,fill=INK)
    grain(img,14).save(OUT/"frame_1.png")

# ---------- Frame 2: acid quote box on cosmic dark (Landyn Zane) ----------
def frame2():
    img=mesh((8,20,12),[(300,300,700,(16,54,30)),(820,1050,650,(10,34,20))]); d=ImageDraw.Draw(img)
    rng=np.random.default_rng(7)
    for _ in range(90):
        x,y=rng.integers(0,W),rng.integers(0,H); s=rng.integers(1,4)
        d.ellipse([x,y,x+s,y+s],fill=(210,230,150))
    ACID=(214,242,74); INK=(18,20,10)
    bx0,by0,bx1,by1=70,690,700,1240
    d.rectangle([bx0,by0,bx1,by1],fill=ACID)
    d.text((bx0+40,by0+20),"“",font=bric(180,900),fill=INK)
    quote=["PUT THE SONG","OUT. THE PERFECT","VERSION IS NOT","COMING."]
    y=by0+190
    for ln in quote: d.text((bx0+44,y),ln,font=bric(58,850),fill=INK); y+=70
    trk(d,(bx0+44,by1-70),"— INDIE MUSIC INDIA",mono(26),INK,2)
    grain(img,12).save(OUT/"frame_2.png")

# ---------- Frame 3: alt gig poster, red/black/white (Baazigar) ----------
def frame3():
    CREAM=(240,236,226); RED=(224,74,50); INK=(20,18,16)
    img=Image.new("RGB",(W,H),CREAM); d=ImageDraw.Draw(img)
    d.polygon([(120,180),(620,120),(980,360),(880,560),(300,520)],fill=RED)   # angular block
    d.polygon([(80,760),(560,700),(720,980),(200,1020)],fill=RED)
    trk(d,(96,150),"UNITED SEVEN · LIVE",mono(30),INK,3)
    d.text((90,300),"ANJAN",font=bric(210,950),fill=INK)
    d.text((90,470),"DUTT",font=bric(210,950),fill=INK)
    d.text((96,720),"& THE D-TRIO",font=bric(84,850),fill=CREAM)
    trk(d,(96,1120),"FRI 07 AUG · ACADEMY OF FINE ARTS · KOLKATA",mono(28),INK,1)
    grain(img,10).save(OUT/"frame_3.png")

# ---------- Frame 4: Y2K retro-web collage (ELLE) ----------
def frame4():
    img=mesh((236,222,246),[(220,300,600,(250,200,230)),(880,260,560,(210,235,250)),
                            (300,1100,650,(220,245,215)),(860,1120,560,(245,225,200))]); d=ImageDraw.Draw(img)
    # window chrome
    wx0,wy0,wx1,wy1=90,470,990,1180
    d.rectangle([wx0,wy0,wx1,wy1],fill=(238,238,240),outline=(40,40,50),width=4)
    d.rectangle([wx0,wy0,wx1,wy0+64],fill=(60,64,150))
    d.text((wx0+20,wy0+14),"indie.exe",font=mono(30),fill=(255,255,255))
    for k,c in enumerate([(200,200,205),(200,200,205),(224,74,50)]):
        bx=wx1-60-k*48; d.rectangle([bx,wy0+16,bx+32,wy0+48],fill=c,outline=(40,40,50),width=2)
    # serif headline over the whole thing (breaks the frame, editorial)
    head=["Does the","algorithm think","all Indian indie","sounds the same?"]
    y=110
    for ln in head: d.text((90,y),ln,font=didot(78),fill=(30,24,40)); y+=88
    d.text((wx0+40,wy0+120),"> a scene worth arguing about",font=mono(30),fill=(50,50,60))
    d.text((wx0+40,wy1-70),"INDIE MUSIC INDIA",font=mono(28),fill=(60,64,150))
    grain(img,10).save(OUT/"frame_4.png")

# ---------- Frame 5: editorial cover (patchwork energy, type-led) ----------
def frame5():
    img=mesh((120,26,40),[(300,200,700,(170,40,55)),(850,1150,700,(80,16,28))]); d=ImageDraw.Draw(img)
    trk(d,(90,90),"INDIE MUSIC INDIA",mono(34),(240,220,200),6)
    d.line([(90,150),(990,150)],fill=(240,220,200),width=2)
    head=["The new","Indian","sound."]
    y=360
    for ln in head: d.text((84,y),ln,font=didot(190),fill=(245,236,224)); y+=190
    d.text((90,1120),"Nine cities. One scene. What to hear this month.",font=inter(38,600),fill=(238,214,206))
    trk(d,(90,1210),"ISSUE 01 · AUGUST",mono(28),(220,180,170),3)
    grain(img,12).save(OUT/"frame_5.png")

for fn in (frame1,frame2,frame3,frame4,frame5): fn()
# contact sheet
sc=0.34; tw2=int(W*sc); th2=int(H*sc); g=16
sheet=Image.new("RGB",(tw2*5+g*6, th2+g*2),(205,205,205))
for i in range(5):
    im=Image.open(OUT/f"frame_{i+1}.png").resize((tw2,th2),Image.LANCZOS)
    sheet.paste(im,(g+i*(tw2+g),g))
sheet.save("/private/tmp/claude-501/-Users-sibyjohn/f318b687-7c52-4861-b1b7-8f95bd8be1ac/scratchpad/proto.png")
print("built 5 frames ->", OUT)
