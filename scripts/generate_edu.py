#!/usr/bin/env python3
"""
Develop a single-tile topic into a full multi-slide educational Reel:
cover (hook) -> 3-5 teaching slides (head + body) -> save/follow CTA.
Reuses the brand system (generate_radar as R). Local only.

Content lives in TOPICS below; add a key per single you want to develop.
Usage: python3 scripts/generate_edu.py release_timing
"""
import os, sys, glob
sys.path.insert(0, os.path.dirname(__file__))
import generate_radar as R
from pathlib import Path
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parent.parent
ACC = [R.PINK, R.YELLOW, R.MINT, R.VIOLET, R.BLUE]

TOPICS = {
  "release_timing": {
    "tag": "THE TIMING",
    "title": "The best day to release your music",
    "slides": [
      ("Friday. Full stop.",
       "Friday is global release day. New-music playlists refresh and the chart week "
       "starts Friday, so every first-day stream counts twice as hard."),
      ("But not blindly.",
       "Skip the Fridays sitting under a massive mainstream drop. You'll get buried. "
       "Check the release calendar and pick a clearer week."),
      ("Time it to your push.",
       "Announce 1-2 weeks out and open a pre-save. Day-one momentum is the signal "
       "that tells everyone this release actually matters."),
      ("Consistency beats the perfect day.",
       "A steady release rhythm does far more than agonising over one date. "
       "Ship, watch the numbers, release again."),
    ],
    "cta": ("Save this.", "Follow for the full release playbook."),
  },
}

def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if R.tw(d, t, font) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def build(key, t):
    W, H, M = R.W, R.H, R.M
    OUT = REPO / "social" / "edu" / key
    OUT.mkdir(parents=True, exist_ok=True)
    for f in glob.glob(str(OUT / "slide_*.png")): os.remove(f)
    total = len(t["slides"]) + 2

    # Cover
    img = Image.new("RGB", (W, H), R.INK2); d = ImageDraw.Draw(img); R.circ(d, W-70, 120, 120, R.PINK)
    R.trk(d, (M, 320), t["tag"], R.mono(30), R.PINK, 3)
    y = 440
    for ln in wrap(d, t["title"], R.bric(120), W - 2*M):
        d.text((M, y), ln, font=R.bric(120), fill=R.WHITE); y += 128
    d.text((M, 1450), "Swipe →", font=R.inter(44, 600), fill=(225,222,232))
    R.footer(d, R.PINK, R.WHITE); img.save(OUT / "slide_01.png")

    # Teaching slides
    for i, (head, body) in enumerate(t["slides"], 2):
        acc = ACC[(i-2) % len(ACC)]
        img = Image.new("RGB", (W, H), R.INK2); d = ImageDraw.Draw(img)
        R.trk(d, (M, 150), f"{i-1:02d} / {len(t['slides']):02d}", R.mono(28), acc, 3)
        y = 300
        for ln in wrap(d, head, R.bric(78), W - 2*M):
            d.text((M, y), ln, font=R.bric(78), fill=acc); y += 88
        y += 40
        for ln in wrap(d, body, R.inter(46, 500), W - 2*M):
            d.text((M, y), ln, font=R.inter(46, 500), fill=(222,216,230)); y += 64
        R.footer(d, acc, R.WHITE); img.save(OUT / f"slide_{i:02d}.png")

    # CTA
    img = R.grad([R.PINK, R.VIOLET, R.BLUE]); d = ImageDraw.Draw(img)
    R.trk(d, (M, 300), "INDIE MUSIC INDIA", R.mono(28), R.YELLOW, 3)
    d.text((M, 460), t["cta"][0], font=R.bric(120), fill=R.WHITE)
    for j, ln in enumerate(wrap(d, t["cta"][1], R.inter(46, 600), W - 2*M)):
        d.text((M, 640 + j*62), ln, font=R.inter(46, 600), fill=(240,236,246))
    R.footer(d, R.YELLOW, R.WHITE); img.save(OUT / f"slide_{total:02d}.png")
    return OUT

def main():
    key = sys.argv[1] if len(sys.argv) > 1 else "release_timing"
    if key not in TOPICS:
        print("unknown topic:", key, "| have:", list(TOPICS)); return
    OUT = build(key, TOPICS[key])
    print("generate_edu:", key, "->", OUT, f"({len(TOPICS[key]['slides'])+2} slides)")

if __name__ == "__main__":
    main()
