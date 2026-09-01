#!/usr/bin/env python3
"""Streaming-earnings data carousel for IG (1080x1350, dark brand).
Sourced, save-worthy. Output: social/streaming-earnings/ (gitignored)."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FONTS = REPO / "assets" / "fonts"
OUT = REPO / "social" / "streaming-earnings"
W, H = 1080, 1350
BG=(13,13,15); CARD=(20,20,26); ACC=(233,69,96); WHITE=(240,240,246); MUT=(150,150,168); MINT=(31,207,158)
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
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    d.rectangle([0,0,W,8],fill=ACC)
    return im,d

def footer(d,page,total):
    cy=H-64
    d.ellipse([64,cy-13,64+26,cy+13],fill=ACC); d.ellipse([73,cy-4,73+8,cy+4],fill=BG)
    d.text((104,H-78),"indiemusicindia.com",font=F(MONO,26),fill=MUT)
    d.text((W-64,H-78),f"{page}/{total}",font=F(MONO,26),fill=MUT,anchor="ra")

def para(d,x,y,text,f,fill,mw,lh):
    for ln in wrap(d,text,f,mw):
        d.text((x,y),ln,font=f,fill=fill); y+=lh
    return y

TOTAL=7
OUT.mkdir(parents=True,exist_ok=True)

# ---- Slide 1: cover / hook ----
im,d=base(); x=72
d.text((x,150),"THE MATH NO ONE SHOWS YOU",font=F(MONO,30),fill=ACC)
d.text((x,250),"₹50.",font=F(HEAD,300),fill=ACC)
y=620
y=para(d,x,y,"That's roughly what 1,000 streams pays",F(HEAD,50),WHITE,W-140,62)
y=para(d,x,y,"an independent Indian artist.",F(HEAD,50),WHITE,W-140,62)
d.text((x,y+24),"The real math →",font=F(BODY,38),fill=MUT)
footer(d,1,TOTAL); im.save(OUT/"slide_01.png")

# ---- Slide 2: why ----
im,d=base(); x=72
d.text((x,150),"WHY SO LITTLE",font=F(MONO,30),fill=ACC)
y=para(d,x,230,"Streaming has no fixed rate.",F(HEAD,66),WHITE,W-140,78)
y+=26
y=para(d,x,y,"You are not paid per play. You are paid a share of the platform's revenue in your listener's country.",F(BODY,40),(200,200,214),W-140,54)
y+=18
y=para(d,x,y,"India has one of the world's biggest listenerships but low revenue per user, so the payout per stream here is small.",F(BODY,40),(200,200,214),W-140,54)
footer(d,2,TOTAL); im.save(OUT/"slide_02.png")

# ---- Slide 3: the numbers ----
im,d=base(); x=72
d.text((x,150),"WHAT ONE STREAM PAYS",font=F(MONO,30),fill=ACC)
def rowcard(d,y,label,val,sub,col):
    d.rounded_rectangle([x,y,W-72,y+150],radius=18,fill=CARD)
    d.text((x+34,y+30),label,font=F(MONO,28),fill=MUT)
    d.text((x+34,y+66),val,font=F(HEAD,58),fill=col)
    d.text((W-104,y+64),sub,font=F(BODY,30),fill=MUT,anchor="ra")
    return y+178
y=250
y=rowcard(d,y,"INDIAN LISTENERS","₹0.03 – ₹0.10","per stream",ACC)
y=rowcard(d,y,"INTERNATIONAL LISTENERS","₹0.25 – ₹0.42","per stream",MINT)
d.text((x,y+16),"Apple Music pays the most.",font=F(BODY,38),fill=WHITE)
d.text((x,y+64),"YouTube pays the least. Spotify sits between.",font=F(BODY,38),fill=(200,200,214))
footer(d,3,TOTAL); im.save(OUT/"slide_03.png")

# ---- Slide 4: reality check ----
im,d=base(); x=72
d.text((x,150),"THE REALITY CHECK",font=F(MONO,30),fill=ACC)
y=para(d,x,230,"To earn ₹1,00,000 from Spotify in India:",F(HEAD,50),WHITE,W-140,62)
d.text((x,y+30),"~20 lakh",font=F(HEAD,150),fill=ACC)
d.text((x,y+200),"streams",font=F(HEAD,90),fill=WHITE)
y2=y+340
para(d,x,y2,"mostly from Indian listeners. That is why streaming alone rarely pays the rent.",F(BODY,40),(200,200,214),W-140,54)
footer(d,4,TOTAL); im.save(OUT/"slide_04.png")

# ---- Slide 5: the lesson ----
im,d=base(); x=72
d.text((x,150),"THE LESSON",font=F(MONO,30),fill=ACC)
y=para(d,x,230,"Streaming is discovery, not salary.",F(HEAD,60),WHITE,W-140,74)
y+=24
y=para(d,x,y,"The artists who earn treat streams as the top of a funnel that leads to live shows, sync, and real fans.",F(BODY,40),(200,200,214),W-140,54)
y+=18
y=para(d,x,y,"Keep 100% of your rights, and register your publishing with IPRS so you collect every royalty you are owed.",F(BODY,40),(200,200,214),W-140,54)
footer(d,5,TOTAL); im.save(OUT/"slide_05.png")

# ---- Slide 6: CTA ----
im,d=base(); x=72
d.text((x,150),"YOUR TURN",font=F(MONO,30),fill=ACC)
y=para(d,x,230,"Run your own numbers.",F(HEAD,66),WHITE,W-140,78)
y+=20
y=para(d,x,y,"Free streaming royalty calculator. Adjust your India vs international split and watch the number move.",F(BODY,40),(200,200,214),W-140,54)
d.rounded_rectangle([x,y+30,x+560,y+118],radius=14,fill=ACC)
d.text((x+34,y+56),"indiemusicindia.com/tools",font=F(MONO,32),fill=WHITE)
d.text((x,y+170),"Save this for your next release. Share it with an artist who needs it.",font=F(BODY,34),fill=MUT)
footer(d,6,TOTAL); im.save(OUT/"slide_06.png")

# ---- Slide 7: sources ----
im,d=base(); x=72
d.text((x,150),"SOURCES & METHOD",font=F(MONO,30),fill=ACC)
y=230
srcs=[
 "Spotify Loud & Clear (loudandclear.byspotify.com). How streaming pays: a share of revenue, not a fixed per-stream rate.",
 "Business of Apps. Music streaming royalty rates by platform, 2026.",
 "Industry per-stream estimates (Duetti, Digital Music News).",
 "India per-stream figures are Indie Music India estimates, derived from global platform rates adjusted for India's lower revenue per user. Indicative, not exact.",
]
for s in srcs:
    d.ellipse([x,y+10,x+10,y+20],fill=ACC)
    y=para(d,x+28,y,s,F(BODY,32),(200,200,214),W-140,44)
    y+=16
footer(d,7,TOTAL); im.save(OUT/"slide_07.png")

# ---- Standalone single post (self-contained, no swipe cue) ----
im,d=base(); x=72
d.text((x,150),"THE MATH NO ONE SHOWS YOU",font=F(MONO,30),fill=ACC)
d.text((x,250),"₹50.",font=F(HEAD,300),fill=ACC)
y=620
y=para(d,x,y,"That's roughly what 1,000 streams pays",F(HEAD,50),WHITE,W-140,62)
y=para(d,x,y,"an independent Indian artist.",F(HEAD,50),WHITE,W-140,62)
y=para(d,x,y+24,"Streaming is discovery, not a salary. The full breakdown, with sources, is on our page.",F(BODY,38),MUT,W-140,50)
# footer without page marker
cy=H-64
d.ellipse([64,cy-13,64+26,cy+13],fill=ACC); d.ellipse([73,cy-4,73+8,cy+4],fill=BG)
d.text((104,H-78),"indiemusicindia.com",font=F(MONO,26),fill=MUT)
im.save(OUT/"single_streaming_50.png")

print(f"wrote 7 slides + 1 standalone to {OUT}")
