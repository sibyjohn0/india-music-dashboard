#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_reels.py — poppy 9:16 reels from the social-buckets doc.

Localized to rupees, India-first, and brand-rule compliant (no "algorithm", no em
dashes). Each reel is a short sequence of frames rendered to a SILENT mp4 (add
trending audio inside Instagram) plus the individual frames (rework in Canva:
drop a clip or a talking-head behind the text, animate, then post).

Output: social/reels/<name>/ (frames + <name>.mp4) — gitignored, our IP.
Usage: python scripts/gen_reels.py [name ...]   (default: all)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from social_reel import (W9, H9, MX, SAFE_TOP, SAFE_BOT, base9, footer9, chip9,
                         render_mp4)
from social_brand import (F, wrap, HEAD, BODY, MONO, INK, PINK, DARK, MUT,
                          YELLOW, VIOLET, MINT, PAPER)

REPO = Path(__file__).resolve().parent.parent
OUT = REPO/"social"/"reels"

# ---- one reusable frame layout, vertically centred in the safe zone ----------
def frame(eyebrow=None, head=None, head_size=84, body=None, rows=None,
          big=None, big_sub=None, eyebrow_fill=YELLOW):
    im,d=base9()
    HF=F(HEAD,head_size); BF=F(BODY,40); BIG=F(HEAD,150)
    # measure
    h=0
    if eyebrow: h+=62+34
    hl = wrap(d,head,HF,W9-2*MX) if head else []
    h+=len(hl)*int(head_size*1.12)
    if big: h+=40+150+ (54 if big_sub else 0)
    bl = wrap(d,body,BF,W9-2*MX) if body else []
    if body: h+=30+len(bl)*54
    if rows: h+=30+len(rows)*96
    y=SAFE_TOP+max(0,(SAFE_BOT-SAFE_TOP-h)//2)
    if eyebrow: chip9(d,MX,y,eyebrow,fill=eyebrow_fill); y+=62+34
    for ln in hl: d.text((MX,y),ln,font=HF,fill=INK); y+=int(head_size*1.12)
    if big:
        y+=40; d.text((MX,y),big,font=BIG,fill=PINK); y+=150
        if big_sub: d.text((MX,y+6),big_sub,font=F(BODY,42),fill=DARK); y+=54
    if body:
        y+=30
        for ln in bl: d.text((MX,y),ln,font=BF,fill=DARK); y+=54
    if rows:
        y+=30
        for tag,text,col in rows:
            tf=F(MONO,34); tw=max(96, d.textlength(tag,font=tf)+40)
            d.rounded_rectangle([MX,y,MX+tw,y+72],radius=14,fill=col,outline=INK,width=4)
            fg=(255,255,255) if col in (PINK,VIOLET,INK) else INK
            d.text((MX+tw/2,y+36),tag,font=tf,fill=fg,anchor="mm")
            for ln in wrap(d,text,F(BODY,38),W9-MX-(MX+tw+26))[:1]:
                d.text((MX+tw+26,y+16),ln,font=F(BODY,38),fill=INK)
            y+=96
    footer9(d)
    return im

# ---- the reels ---------------------------------------------------------------
def reel_expenses():
    return [
        frame(eyebrow="INDIE BUDGET", head="Where your money should actually go."),
        frame(eyebrow="EXPENSES, RANKED", head=None, rows=[
            ("S","A great mix & master, and a live show",MINT),
            ("A","Decent artwork, and a content day",YELLOW),
            ("B","PR",VIOLET),
            ("C","An expensive music video, too early",PINK),
            ("D","Buying fake streams",INK)]),
        frame(eyebrow="ON THE SITE", head="Save this before your next release."),
    ], [2.4,4.2,2.6]

def reel_budget():
    return [
        frame(eyebrow="CHOOSE YOUR BUDGET", head="You have ₹30,000 for your next single."),
        frame(eyebrow="CHOOSE TWO", head=None, rows=[
            ("₹15K","Production",VIOLET),
            ("₹10K","Content",YELLOW),
            ("₹10K","PR",MINT),
            ("₹5K","Ads",PINK),
            ("₹8K","Live session",VIOLET),
            ("₹5K","Artwork",YELLOW)]),
        frame(head="What are you cutting?", head_size=100),
        frame(eyebrow="OUR PICK", head="We answer in the comments."),
    ], [2.6,4.4,2.4,2.4]

def reel_streams():
    return [
        frame(eyebrow="THE REAL MATH", head="You got 100,000 streams on Spotify."),
        frame(head="Guess how much that paid.", head_size=104),
        frame(eyebrow="IN INDIA", head=None, big="₹3k–5k", big_sub="Streaming is discovery, not income."),
        frame(eyebrow="WHAT ACTUALLY PAYS", head="Live, sync, merch, and real fans.",
              body="Free royalty calculator on the site."),
    ], [2.6,2.2,3.0,3.0]

def reel_streamshare():
    return [
        frame(eyebrow="MYTH", head="Spotify doesn’t pay a fixed rate per stream."),
        frame(eyebrow="HOW IT WORKS", head="You get a share of the pool. Your % of the money, not a price per play.", head_size=72),
        frame(eyebrow="SO", head="Chase saves and repeat listens, not raw stream counts.", head_size=76),
        frame(eyebrow="ON THE SITE", head="Save this."),
    ], [2.8,3.4,3.2,2.2]

REELS = {
    "expenses-ranked": reel_expenses,
    "budget-30k": reel_budget,
    "100k-streams": reel_streams,
    "stream-share-myth": reel_streamshare,
}

def build(name):
    frames, holds = REELS[name]()
    d = OUT/name; d.mkdir(parents=True, exist_ok=True)
    for i,fr in enumerate(frames,1): fr.save(d/f"frame_{i:02d}.png")
    render_mp4(frames, d/f"{name}.mp4", holds=holds)
    dur=sum(holds)+0.35*(len(frames)-1)
    print(f"  {name}: {len(frames)} frames, ~{dur:.1f}s -> {d}/{name}.mp4")

def main():
    names = [a for a in sys.argv[1:] if a in REELS] or list(REELS)
    for n in names: build(n)
    print(f"gen_reels: {len(names)} reels in {OUT}")

if __name__ == "__main__":
    main()
