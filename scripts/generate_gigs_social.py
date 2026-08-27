#!/usr/bin/env python3
"""
generate_gigs_social.py — Turn data/festivals.json into Instagram-ready posts.

Three post types (the ones chosen for the data play):
  gigs-month   "Live in <City>, <Month>"  — carousel of that month's gigs
  announced    "Just announced"           — new festivals/tours since last build
  onsale       "On sale now"              — a snapshot of what's bookable

On-demand only (NOT in the daily pipeline — social assets stay off GitHub).
Writes 1080x1350 (4:5) PNG slides to social/gigs/<post>/slide_NN.png.

Usage:
  python scripts/generate_gigs_social.py gigs-month --city Bangalore [--month 2026-09]
  python scripts/generate_gigs_social.py announced
  python scripts/generate_gigs_social.py onsale
"""
import os, sys, json, argparse, datetime, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "data" / "festivals.json"
FONTS = REPO / "assets" / "fonts"
OUTROOT = REPO / "social" / "gigs"

W, H = 1080, 1350
BG = (13, 13, 15)
SURFACE = (22, 22, 28)
ACCENT = (233, 69, 96)
BLUE = (122, 168, 255)
TEXT = (232, 232, 240)
MUTED = (138, 138, 160)
PAD = 90

def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)

HEAD = "BricolageGrotesque.ttf"
BODY = "Inter.ttf"
MONO = "SpaceMono-Bold.ttf"

def new_slide():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # subtle top accent bar
    d.rectangle([0, 0, W, 10], fill=ACCENT)
    return img, d

def footer(d):
    # brand mark: draw a filled ring (Space Mono has no ◉ glyph -> tofu box)
    cy = H - 78 + 15
    d.ellipse([PAD, cy - 15, PAD + 30, cy + 15], fill=ACCENT)
    d.ellipse([PAD + 10, cy - 5, PAD + 20, cy + 5], fill=BG)
    d.text((PAD + 46, H - 78), "indiemusicindia.com", font=font(MONO, 30), fill=MUTED)
    d.text((W - PAD, H - 78), "@indiemusicindia.co", font=font(MONO, 30), fill=MUTED, anchor="ra")

def wrap(d, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def save(img, outdir, n):
    outdir.mkdir(parents=True, exist_ok=True)
    p = outdir / f"slide_{n:02d}.png"
    img.save(p)
    return p

def fmt(iso):
    try:
        return datetime.date.fromisoformat(iso).strftime("%d %b")
    except Exception:
        return ""

# ---------- cover ----------
def cover(outdir, eyebrow, big, sub, n=1):
    img, d = new_slide()
    d.text((PAD, 150), eyebrow.upper(), font=font(MONO, 34), fill=ACCENT)
    y = 240
    for line in wrap(d, big, font(HEAD, 118), W - 2 * PAD):
        d.text((PAD, y), line, font=font(HEAD, 118), fill=TEXT)
        y += 128
    if sub:
        y += 20
        for line in wrap(d, sub, font(BODY, 44), W - 2 * PAD):
            d.text((PAD, y), line, font=font(BODY, 44), fill=MUTED)
            y += 60
    footer(d)
    return save(img, outdir, n)

# ---------- list slide (up to `per` gigs) ----------
def list_slide(outdir, title, rows, n):
    img, d = new_slide()
    d.text((PAD, 120), title.upper(), font=font(MONO, 34), fill=ACCENT)
    y = 210
    for r in rows:
        # date chip
        d.rounded_rectangle([PAD, y, PAD + 150, y + 66], radius=12, fill=SURFACE)
        d.text((PAD + 75, y + 33), r["when"], font=font(MONO, 30), fill=ACCENT, anchor="mm")
        tx = PAD + 180
        name_lines = wrap(d, r["title"], font(HEAD, 46), W - tx - PAD)[:2]
        yy = y
        for ln in name_lines:
            d.text((tx, yy), ln, font=font(HEAD, 46), fill=TEXT)
            yy += 52
        meta = " · ".join([x for x in [r.get("city", ""), r.get("venue", "")] if x])
        if meta:
            d.text((tx, yy), meta[:52], font=font(BODY, 32), fill=MUTED)
            yy += 44
        y = max(yy, y + 66) + 34
        if y > H - 200:
            break
    footer(d)
    return save(img, outdir, n)

def load():
    d = json.load(open(SRC))
    return d.get("festivals", []) + d.get("tours", []), d

def occurrences(entries):
    """Flatten entries into dated (title, date_obj, city, venue, type) rows."""
    occ = []
    for e in entries:
        for dt in e.get("dates", []):
            if dt.get("date_obj"):
                occ.append({"title": e["title"], "date_obj": dt["date_obj"],
                            "city": dt.get("city", ""), "venue": dt.get("venue", ""),
                            "type": e["type"], "origin": e.get("origin", "")})
    return occ

# ---------- post builders ----------
def build_gigs_month(city, month):
    entries, _ = load()
    occ = occurrences(entries)
    if month:
        occ = [o for o in occ if o["date_obj"].startswith(month)]
    else:
        # pick the soonest month that has >=3 gigs in the city
        future = sorted(o["date_obj"][:7] for o in occ if o["city"].lower() == city.lower())
        month = future[0] if future else datetime.date.today().strftime("%Y-%m")
        occ = [o for o in occ if o["date_obj"].startswith(month)]
    occ = [o for o in occ if o["city"].lower() == city.lower()]
    occ.sort(key=lambda o: o["date_obj"])
    mlabel = datetime.date.fromisoformat(month + "-01").strftime("%B") if len(month) == 7 else month
    outdir = OUTROOT / f"gigs-{city.lower()}-{month}"
    paths = [cover(outdir, "Gigs this month", f"Live in {city}", f"{mlabel} · {len(occ)} shows worth your time")]
    for i in range(0, len(occ), 5):
        chunk = [{"when": fmt(o["date_obj"]), "title": o["title"], "city": "", "venue": o["venue"] or o["type"].title()} for o in occ[i:i+5]]
        paths.append(list_slide(outdir, f"{city} · {mlabel}", chunk, len(paths) + 1))
    return outdir, paths, len(occ)

def build_announced():
    entries, data = load()
    names = set(data.get("new_this_run", []))
    new = [e for e in entries if e["title"] in names and e.get("dates")]
    outdir = OUTROOT / "just-announced"
    if not new:
        paths = [cover(outdir, "Just announced", "Nothing new today", "Check back — we scan the ticketing feeds daily.")]
        return outdir, paths, 0
    paths = [cover(outdir, "Just announced", "Just announced", f"{len(new)} new to the calendar")]
    rows = []
    for e in new:
        d0 = next((x for x in e["dates"] if x.get("date_obj")), e["dates"][0])
        rows.append({"when": fmt(d0.get("date_obj", "")), "title": e["title"],
                     "city": ", ".join(e.get("cities", [])[:3]), "venue": ""})
    for i in range(0, len(rows), 5):
        paths.append(list_slide(outdir, "New on the calendar", rows[i:i+5], len(paths) + 1))
    return outdir, paths, len(new)

def build_onsale():
    entries, _ = load()
    occ = [o for o in occurrences(entries)]
    today = datetime.date.today()
    occ = [o for o in occ if datetime.date.fromisoformat(o["date_obj"]) >= today]
    occ.sort(key=lambda o: o["date_obj"])
    outdir = OUTROOT / "on-sale"
    paths = [cover(outdir, "On sale now", "Book these", f"{len(occ)} festivals & tours with live tickets")]
    rows = [{"when": fmt(o["date_obj"]), "title": o["title"], "city": o["city"], "venue": ""} for o in occ[:15]]
    for i in range(0, len(rows), 5):
        paths.append(list_slide(outdir, "Tickets live", rows[i:i+5], len(paths) + 1))
    return outdir, paths, len(occ)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("post", choices=["gigs-month", "announced", "onsale"])
    ap.add_argument("--city", default="Bangalore")
    ap.add_argument("--month", default="", help="YYYY-MM (defaults to soonest with gigs)")
    a = ap.parse_args()
    if a.post == "gigs-month":
        outdir, paths, n = build_gigs_month(a.city, a.month)
    elif a.post == "announced":
        outdir, paths, n = build_announced()
    else:
        outdir, paths, n = build_onsale()
    print(f"{a.post}: {len(paths)} slides ({n} gigs) -> {outdir}")
    for p in paths:
        print("  ", p)

if __name__ == "__main__":
    main()
