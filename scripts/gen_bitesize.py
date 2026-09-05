#!/usr/bin/env python3
"""gen_bitesize.py — turn the website's guide FAQs into bite-sized Instagram cards.

Positions Instagram as the snackable version of the site: every guide FAQ becomes
a poppy-branded question/answer card that a website visitor can follow for. Reads
the FAQ Q&As already on the guide pages, so the content stays in sync with the
site and grows as the guides do.

Outputs:
  social/bitesize/*.png   full library for posting (gitignored, our IP)
  assets/bites/bite_*.png  a curated 6 for the homepage "on Instagram" strip (committed)

Usage: python scripts/gen_bitesize.py            # build everything
       python scripts/gen_bitesize.py --list     # just list available Q&As
"""
import re, html, sys, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from social_brand import (REPO, W, H, F, wrap, base, chip, shadow_card, footer,
                          INK, PINK, DARK, CREAM, HEAD, BODY, MONO)

LIB = REPO/"social"/"bitesize"
STRIP = REPO/"assets"/"bites"

def clean(s):
    return html.unescape(re.sub(r"\s+"," ", re.sub(r"<[^>]+>","",s))).strip()

def faqs():
    """Yield (cat, slug, question, answer) from every guide's FAQ section."""
    for f in sorted((REPO/"guides").glob("*/index.html")):
        h=f.read_text()
        m=re.search(r'Guide\s*&middot;\s*([^<]+)|Guide\s*·\s*([^<]+)', h)
        cat=clean((m.group(1) or m.group(2))) if m else "Guide"
        sec=re.search(r'<section id="related".*?</section>', h, re.S)
        if not sec: continue
        for q,a in re.findall(r'<h3[^>]*>(.*?)</h3>\s*<p>(.*?)</p>', sec.group(0), re.S):
            yield cat, f.parent.name, clean(q), clean(a)

def slug(s):
    return re.sub(r"[^a-z0-9]+","-", s.lower()).strip("-")[:48]

def card(cat, q, a):
    im,d=base(); x=84
    qf=F(HEAD,60); af=F(BODY,37)
    qlines=wrap(d, q, qf, W-2*x)[:4]
    alines=wrap(d, a, af, W-2*x-64)[:7]
    ch=len(alines)*52+52
    # vertically centre the chip + question + answer block between top bar and footer
    block = 54 + 44 + len(qlines)*70 + 30 + ch
    y=max(150, (14 + (H-120) - block)//2)
    chip(d, x, y, cat.upper()); y+=54+44
    for ln in qlines:
        d.text((x,y), ln, font=qf, fill=INK); y+=70
    y+=30
    shadow_card(d, [x, y, W-x, y+ch], radius=22)
    ay=y+28
    for ln in alines:
        d.text((x+30,ay), ln, font=af, fill=DARK); ay+=52
    d.rounded_rectangle([x-3, y+22, x+9, y+ch-22], radius=6, fill=PINK)  # pink accent tab
    footer(d)
    return im

# Curated homepage picks: short, high-interest, diverse topics. Match by a
# distinctive phrase from the question so it stays stable as content grows.
STRIP_PICKS = [
    "distrokid available in india",
    "how much is 1 million streams worth",
    "submit my music to spotify playlists",
    "difference between isrc and upc",
    "promote my music for free",
    "what is an epk for musicians",
]

def main():
    items=list(faqs())
    if "--list" in sys.argv:
        for c,s,q,a in items: print(f"[{c}] {q}")
        print(f"\n{len(items)} Q&As available.")
        return
    LIB.mkdir(parents=True, exist_ok=True)
    STRIP.mkdir(parents=True, exist_ok=True)
    for p in STRIP.glob("bite_*.png"): p.unlink()
    n=0
    for c,s,q,a in items:
        card(c,q,a).save(LIB/f"{s}__{slug(q)}.png"); n+=1
    # homepage strip: pick in the fixed order, fall back to first items
    picked=[]
    for key in STRIP_PICKS:
        hit=next((it for it in items if key in it[2].lower()), None)
        if hit: picked.append(hit)
    for it in items:
        if len(picked)>=6: break
        if it not in picked: picked.append(it)
    for i,(c,s,q,a) in enumerate(picked[:6],1):
        card(c,q,a).save(STRIP/f"bite_{i:02d}.png")
    print(f"gen_bitesize: {n} cards -> {LIB}")
    print(f"              6 homepage cards -> {STRIP}")

if __name__ == "__main__":
    main()
