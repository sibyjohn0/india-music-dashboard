#!/usr/bin/env python3
"""normalize_guide_ctas.py — one consistent programme promise across every guide.

Problem this solves: the "here's how we're different" pitch had drifted into
wallpaper — an identical, vague CTA box bolted onto all 28 guides, plus a few
one-off variants. It set no real expectations and appeared everywhere, including
pages where the reader only wants a fact.

Fix, applied in place to every guide (generated or hand-built):
  * Reference pages (a reader wants an answer, not a pitch) lose the sales box and
    get one honest line instead.
  * Decision pages keep the box but carry the SAME concrete promise as the home
    hero and /programme/: a few artists at a time, founder-led, one month to start,
    no cut. Existing topic-specific headings are preserved.

Idempotent: re-running changes nothing once normalised. build_guides.py already
emits this shape for the guides it owns; this catches the ones it doesn't.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GUIDES = REPO / "guides"

# Reference = answer a fact; stay quiet. Everything else is a decision page.
REFERENCE = {
    "isrc-code-india", "register-music-copyright-iprs-india",
    "caller-tune-hello-tune-india", "spotify-pay-per-stream-india",
    "how-much-indian-artists-earn-spotify", "best-music-distributor-india",
    "free-music-distribution-india", "publish-music-in-india",
    "music-platforms-independent-artists-india",
    "independent-music-scene-mumbai", "independent-music-scene-bengaluru",
    "independent-music-scene-delhi",
}

CTA_BODY = ("For a few artists at a time: work directly with Siby and Karishma, "
            "plus a network of specialists for release strategy, PR, social, video, "
            "design, legal and IPRS. One month to start, no commitment beyond that, "
            "and no cut of your music.")

SOFTCTA = ('  <div class="g-softcta">Free to read, no sign-up. When you want a team on '
           'your releases, <a href="/programme/">the programme</a> is founder-led, one '
           'month to start, and never takes a cut of your music.</div>')

SOFT_STYLE = ('<style>.g-softcta{margin-top:38px;font-size:14px;color:var(--muted);'
              'line-height:1.65;border-left:3px solid var(--accent);padding:2px 0 2px 15px}'
              '.g-softcta a{color:var(--accent);font-weight:600}</style>')

BOX_RE = re.compile(r'[ \t]*<div class="g-cta">.*?</div>', re.S)
BODY_RE = re.compile(r'(<div class="g-cta">\s*<h3>.*?</h3>\s*)<p>.*?</p>', re.S)

def process(path):
    slug = path.parent.name
    html = path.read_text()
    orig = html
    has_box = 'class="g-cta"' in html
    has_soft = 'class="g-softcta"' in html

    if slug in REFERENCE:
        if has_box:                                   # swap the box for one line
            html = BOX_RE.sub(SOFTCTA, html, count=1)
            has_soft = True
        if has_soft and '.g-softcta{' not in html:    # ensure the style exists
            html = html.replace('<link rel="stylesheet" href="/assets/poppy.css">',
                                 SOFT_STYLE + '\n  <link rel="stylesheet" href="/assets/poppy.css">', 1)
    else:
        if has_box:                                   # keep box, canonical promise
            html = BODY_RE.sub(r'\g<1><p>' + CTA_BODY + '</p>', html, count=1)

    if html != orig:
        path.write_text(html)
        return slug, ("reference→line" if slug in REFERENCE else "decision→canonical")
    return None

def main():
    changed = []
    for d in sorted(GUIDES.iterdir()):
        f = d / "index.html"
        if f.exists():
            r = process(f)
            if r:
                changed.append(r)
    for slug, what in changed:
        print(f"  {what:22} {slug}")
    print(f"normalize_guide_ctas: {len(changed)} guides updated.")

if __name__ == "__main__":
    main()
