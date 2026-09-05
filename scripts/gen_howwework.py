#!/usr/bin/env python3
"""gen_howwework.py — the one 'how we work' promo card for Instagram.

Poppy brand (social_brand.py), no prices (rates stay on the private /tiers/ link
we send after a call). Shows the approach + the three tier NAMES as a hook and
drives to a DM. Output: social/work/ (gitignored). On-demand, post occasionally.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from social_brand import (REPO, W, H, F, wrap, base, chip, shadow_card, footer,
                          INK, PINK, DARK, CREAM, YELLOW, VIOLET, PAPER,
                          HEAD, BODY, MONO)

OUT = REPO/"social"/"work"

def pill(d, x, y, text, fill, fg=INK):
    f=F(MONO,24); tw=d.textlength(text, font=f)
    d.rounded_rectangle([x,y,x+tw+36,y+50], radius=999, fill=fill, outline=INK, width=3)
    d.text((x+18,y+12), text, font=f, fill=fg)
    return x+tw+36+12

def card():
    im,d=base(); x=84
    y=140
    chip(d, x, y, "WORK WITH US"); y+=54+40
    # headline
    for ln in wrap(d, "We build the career, not just the release.", F(HEAD,64), W-2*x):
        d.text((x,y), ln, font=F(HEAD,64), fill=INK); y+=74
    y+=18
    # body in a white shadow card
    body="Hands-on artist development for a few independent artists at a time. Positioning, release strategy, and audience, run with you. Founder-led. No cut of your music."
    bf=F(BODY,37); lines=wrap(d, body, bf, W-2*x-64)
    ch=len(lines)*52+52
    shadow_card(d, [x, y, W-x, y+ch], radius=22)
    ay=y+28
    for ln in lines: d.text((x+30,ay), ln, font=bf, fill=DARK); ay+=52
    d.rounded_rectangle([x-3, y+22, x+9, y+ch-22], radius=6, fill=PINK)
    y+=ch+40
    # three tier names as pills (no prices)
    d.text((x,y), "THREE WAYS IN", font=F(MONO,24), fill=VIOLET); y+=44
    nx=x
    for name,col in [("Roadmap",YELLOW),("Advisory",VIOLET),("Development",PINK)]:
        fg = (255,255,255) if col in (VIOLET,PINK) else INK
        nx=pill(d, nx, y, name, col, fg)
    y+=50+44
    # CTA
    cta="DM us to see if it's a fit"
    f=F(MONO,28); tw=d.textlength(cta, font=f)
    d.rounded_rectangle([x,y,x+tw+68,y+76], radius=14, fill=INK, outline=INK, width=3)
    d.text((x+34,y+24), cta, font=f, fill=(255,255,255))
    footer(d)
    return im

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    card().save(OUT/"how-we-work.png")
    print(f"gen_howwework: 1 card -> {OUT}/how-we-work.png")

if __name__ == "__main__":
    main()
