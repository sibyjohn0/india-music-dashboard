#!/usr/bin/env python3
"""
Generate "Busiest music venues in <City>" — a ranked, per-city carousel/Reel.
A repeatable series: one post per city, top 5 venues by shows on the calendar.

Reads:  data/events-*.json
Writes: social/venues/<city>/slide_01.png .. + caption.txt

POV (Siby, 2026-08-07): celebrate + curate + back the scene. Only defensible
claims — we rank by the number of shows WE tracked, nothing about the artists.

Usage: python3 scripts/generate_venues.py "Mumbai"
Local only (social/ is gitignored). Ranking is thin on a snapshot; it sharpens as
the events tracker accumulates weeks of history.
"""
import json, os, glob, re, sys, datetime
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
import generate_radar as R
from collections import Counter, defaultdict
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
N = 5
ACCENTS = [R.PINK, R.YELLOW, R.MINT, R.VIOLET, R.BLUE]

JUNK = re.compile(r"to be announced|^tba$|multiple venue|^venue$|\bmall\b|wonder world", re.I)
NOT_MUSIC = re.compile(r"karaoke|theme park|brunch|ladies|happy hour|pool party|comedy|"
                       r"stand[- ]?up|quiz|bingo|workshop|kitty|speed dating|hookah", re.I)

def norm_venue(v):
    v = v.split("|")[0].split(",")[0].strip()      # drop locality / pipe tails
    return re.sub(r"\s+", " ", v).strip()

def rank_city(city):
    today = datetime.date.today()
    cnt = Counter(); nxt = defaultdict(list)
    for f in glob.glob(str(DATA / "events-*.json")):
        try: d = json.load(open(f))
        except Exception: continue
        items = d if isinstance(d, list) else d.get("events", d)
        if isinstance(items, dict): items = list(items.values())
        for e in items:
            if not isinstance(e, dict): continue
            if (e.get("city") or "").strip().lower() != city.lower(): continue
            name = e.get("name") or ""; v = norm_venue(e.get("venue") or "")
            if not v or JUNK.search(v) or NOT_MUSIC.search(name): continue
            cnt[v] += 1
            try:
                dt = datetime.date.fromisoformat(str(e.get("date"))[:10])
                if dt >= today: nxt[v].append(dt)
            except Exception: pass
    ranked = []
    for v, c in cnt.most_common():
        upcoming = sorted(nxt[v])
        ranked.append({"venue": v, "shows": c, "next": upcoming[0] if upcoming else None})
    # rank by show count, then soonest next show
    ranked.sort(key=lambda r: (-r["shows"], r["next"] or datetime.date.max))
    return ranked[:N]

def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if R.tw(d, t, font) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines[:3]

def fit_name(d, text, maxw, sizes=(128, 112, 98, 86, 76)):
    """Largest Bricolage size whose full wrap fits in <=3 lines — makes the name pop."""
    best = None
    for sz in sizes:
        f = R.bric(sz)
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if R.tw(d, t, f) <= maxw: cur = t
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        best = (f, lines)
        widest = max((R.tw(d, ln, f) for ln in lines), default=0)
        if len(lines) <= 3 and widest <= maxw:      # fits by line count AND width
            return f, lines
    f, lines = best
    return f, lines[:3]

def fmt(dt): return dt.strftime("%a %d %b").upper() if dt else "TBA"

def load_handles(city):
    """Handles are namespaced by city (venue names collide across cities)."""
    try:
        return json.load(open(DATA / "venue_handles.json")).get("handles", {}).get(city.lower(), {})
    except Exception:
        return {}

def build(city, picks):
    OUT = REPO / "social" / "venues" / city.lower().replace(" ", "_")
    OUT.mkdir(parents=True, exist_ok=True)
    for f in glob.glob(str(OUT / "slide_*.png")): os.remove(f)
    W, H, M = R.W, R.H, R.M
    total = len(picks) + 2
    wk = datetime.date.today().strftime("%d %b %Y").upper()

    # Cover
    img = Image.new("RGB", (W, H), R.INK2); d = ImageDraw.Draw(img); R.circ(d, W-70, 120, 120, R.PINK)
    R.trk(d, (M, 320), f"MUSIC VENUES · {city.upper()}", R.mono(30), R.PINK, 3)
    d.text((M, 440), "Busiest", font=R.bric(150), fill=R.WHITE)
    d.text((M, 600), "rooms in", font=R.bric(150), fill=R.WHITE)
    d.text((M, 760), f"{city}.", font=R.bric(150), fill=R.YELLOW)
    d.text((M, 980), "Ranked by shows on the", font=R.inter(40, 600), fill=(225,222,232))
    d.text((M, 1036), "calendar right now.", font=R.inter(40, 600), fill=(225,222,232))
    d.text((M, 1450), "Swipe the ranking →", font=R.inter(44, 600), fill=(225,222,232))
    R.footer(d, R.PINK, R.WHITE); img.save(OUT / "slide_01.png")

    # Ranked venue cards — venue NAME is the hero (no show count)
    handles = load_handles(city)
    for i, g in enumerate(picks, 2):
        rank = i - 1
        acc = ACCENTS[(rank-1) % len(ACCENTS)]
        img = Image.new("RGB", (W, H), R.INK2); d = ImageDraw.Draw(img)
        R.trk(d, (M, 150), f"{city.upper()} · {i:02d} / {total:02d}", R.mono(28), acc, 3)
        d.text((M, 250), f"{rank:02d}", font=R.bric(210), fill=acc)   # big rank

        # big popping venue name — largest size that fits in <=3 lines
        name_f, lines = fit_name(d, g["venue"], W - 2*M)
        y = 620
        for ln in lines:
            d.text((M, y), ln, font=name_f, fill=R.WHITE); y += int(name_f.size * 1.04)

        # fixed bottom block: accent bar + handle (no date)
        d.rectangle([M, 1230, M + 130, 1244], fill=acc)
        h = handles.get(g["venue"])
        if h:
            d.text((M, 1280), h, font=R.inter(44, 650), fill=acc)
        R.footer(d, acc, R.WHITE); img.save(OUT / f"slide_{i:02d}.png")

    # Back-the-scene closer
    img = R.grad([R.PINK, R.VIOLET, R.BLUE]); d = ImageDraw.Draw(img)
    R.trk(d, (M, 300), "WHY IT MATTERS", R.mono(28), R.YELLOW, 3)
    for j, ln in enumerate(["A full room books", "the next show.", "An empty one", "goes dark. Go."]):
        d.text((M, 440 + j*130), ln, font=R.bric(88), fill=(R.YELLOW if j == 3 else R.WHITE))
    R.footer(d, R.YELLOW, R.WHITE); img.save(OUT / f"slide_{total:02d}.png")
    return OUT

def write_caption(city, picks, OUT):
    handles = load_handles(city)
    lines = []
    for i, g in enumerate(picks, 1):
        tag = handles.get(g["venue"], "")
        lines.append(f"{i}. {g['venue']}{'  ' + tag if tag else ''}")
    cap = (f"MUSIC VENUES ON OUR RADAR — {city.upper()} \U0001F3B5  the rooms keeping live music going.\n\n"
           + "\n".join(lines) +
           "\n\nSave it, pick one, go. Tag the venue when you're there.\n\n"
           f"#{city.lower().replace(' ','')}music #livemusic #musicvenues #indianmusic #gigguide #whatson")
    (OUT / "caption.txt").write_text(cap)

def main():
    city = sys.argv[1] if len(sys.argv) > 1 else "Mumbai"
    picks = rank_city(city)
    if not picks:
        print("no venues found for", city); return
    OUT = build(city, picks)
    write_caption(city, picks, OUT)
    print(f"generate_venues: {city} ->", OUT)
    for i, g in enumerate(picks, 1):
        print(f"   {i}. {g['shows']:2}x  next {fmt(g['next'])}  {g['venue']}")

if __name__ == "__main__":
    main()
