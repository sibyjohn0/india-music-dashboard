#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""add_guide_heroes.py — put a themed India-art hero banner on every guide.

Decorative only (empty alt, real text H1 stays below it for SEO). Picks an image
by the guide's category so related guides share a look. Idempotent: skips a guide
that already has one. CSS lives in poppy.css (.g-hero).

Run order: guides are a post-processing stack. After build_guides.py, run
normalize_guide_ctas.py, deepen_guides.py, then this.
"""
import re
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
HEROES = REPO/"assets"/"guide-heroes"

# category (lowercased) -> hero image basename
CATMAP = {
    "money":"cassette", "streaming":"cassette", "monetisation":"cassette",
    "distribution":"guitar-case", "playlists":"guitar-case", "releasing":"guitar-case",
    "rights":"green-room",
    "pr":"pink-loungers", "marketing":"pink-loungers", "promotion":"pink-loungers",
    "branding":"pink-loungers", "audience":"pink-loungers", "fans":"pink-loungers",
    "management":"desert-chair", "getting started":"desert-chair",
    "artist development":"desert-chair",
    "live":"pool-chair", "sync":"wall",
}
DEFAULT = "amp-corridor"

def hero_for(cat):
    c = cat.lower().strip()
    if c.startswith("scene"): return "lamp-pool"
    return CATMAP.get(c, DEFAULT)

def category(html):
    m = re.search(r'g-eyebrow">\s*Guide\s*(?:·|&middot;)\s*([^<]+)', html)
    return m.group(1).strip() if m else ""

def process(f):
    html = f.read_text()
    if 'class="g-hero"' in html:
        return None
    cat = category(html)
    img = hero_for(cat)
    if not (HEROES/f"{img}.jpg").exists():
        img = DEFAULT
    hero = (f'  <div class="g-hero"><img src="/assets/guide-heroes/{img}.jpg" alt="" '
            f'width="1300" height="340" /></div>\n')
    new = re.sub(r'(<div class="page">\s*\n)', r'\1' + hero, html, count=1)
    if new == html:
        return "no-anchor"
    f.write_text(new)
    return f"{cat or '?'} -> {img}"

def main():
    n = 0
    for d in sorted((REPO/"guides").iterdir()):
        fp = d/"index.html"
        if not fp.exists(): continue
        r = process(fp)
        if r and r != "no-anchor":
            print(f"  {d.name}: {r}"); n += 1
        elif r == "no-anchor":
            print(f"  {d.name}: NO .page anchor")
    print(f"add_guide_heroes: {n} guides got a hero.")

if __name__ == "__main__":
    main()
