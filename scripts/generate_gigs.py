#!/usr/bin/env python3
"""
Generate "Gigs on our radar" — a weekly live-music carousel from scraped events.

Reads:  data/events-*.json  (bookmyshow, district, skillbox, ...)
Writes: social/gigs/slide_01.png .. slide_NN.png  +  caption.txt

POV (per Siby, 2026-08-07): celebrate the music + tastemaker curation + back the
scene. NO unverifiable claims (never call an artist "independent" / "unsigned").
We only claim what we do (curate) and what the listener does (show up).

Curation: upcoming shows in the next ~16 days, drop club/karaoke/non-music noise,
prefer live-music signals, then take the soonest strong show from each of several
cities so the set represents the country. Text-forward poster cards (no photos in
the events feed), reusing the Radar brand system.

Local only — not committed (social/ is gitignored).
"""
import json, os, glob, re, datetime
from pathlib import Path
import sys
sys.path.insert(0, os.path.dirname(__file__))
import generate_radar as R          # reuse fonts, colours, primitives
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT  = REPO / "social" / "gigs"
N_GIGS = 5
WINDOW_DAYS = 16

# Not live music — drop these outright.
NOT_MUSIC = re.compile(
    r"karaoke|theme park|boiler room|brunch|ladies['’ ]?night|happy hour|pool party|"
    r"she deserves|open mic|comedy|stand[- ]?up|quiz|bingo|masterclass|workshop|"
    r"speed dating|kitty party|sufi night club|hookah", re.I)
# Positive live-music signals — used to rank.
LIVE = re.compile(
    r"\blive\b|concert|tour|\bft\.?\b|feat\.|project|quartet|quintet|trio|\bband\b|"
    r"unplugged|acoustic|jazz|rock|orchestra|symphony|collective|jamming|recital|"
    r"ensemble|gig|nite|night ft|weekender", re.I)

ACCENTS = [R.PINK, R.YELLOW, R.MINT, R.VIOLET, R.BLUE]

def load_events():
    rows = []
    for f in glob.glob(str(DATA / "events-*.json")):
        try: d = json.load(open(f))
        except Exception: continue
        items = d if isinstance(d, list) else d.get("events", d)
        if isinstance(items, dict): items = list(items.values())
        src = os.path.basename(f).replace("events-", "").replace(".json", "")
        for e in items:
            if isinstance(e, dict): rows.append({**e, "src": src})
    return rows

def pdate(s):
    try: return datetime.date.fromisoformat(str(s)[:10])
    except Exception: return None

def clean_name(s):
    """Drop the '| City'/sponsor tail and any non-Latin script the font can't
    render (Bengali/Tamil/Devanagari show as tofu boxes otherwise)."""
    s = s.split("|")[0].strip()
    s = re.sub(r"[^\x20-\x7E₹–—’‘“”&()]", "", s)      # keep Latin + common punctuation
    s = re.sub(r"\s+", " ", s).strip(" -–—:·")
    return s

def curate(rows, today):
    seen, cands = set(), []
    for r in rows:
        d = pdate(r.get("date")); name = (r.get("name") or "").strip()
        if not d or not name: continue
        if not (today <= d <= today + datetime.timedelta(days=WINDOW_DAYS)): continue
        if NOT_MUSIC.search(name): continue
        key = (name.lower(), r.get("city"), d)
        if key in seen: continue
        seen.add(key)
        cleaned = clean_name(name)
        if len(cleaned) < 4: continue                 # nothing renderable left
        cands.append({"name": cleaned, "venue": (r.get("venue") or "").strip(),
                      "city": (r.get("city") or "").strip(), "date": d,
                      "live": bool(LIVE.search(name))})
    # one strong show per city (spread), live-signal first, then soonest
    by_city = {}
    for c in sorted(cands, key=lambda c: (not c["live"], c["date"])):
        by_city.setdefault(c["city"], c)
    picks = sorted(by_city.values(), key=lambda c: (not c["live"], c["date"]))
    return picks[:N_GIGS]

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

def fmt_date(d):
    return d.strftime("%a %d %b").upper()

def build(picks):
    OUT.mkdir(parents=True, exist_ok=True)
    for f in glob.glob(str(OUT / "slide_*.png")): os.remove(f)
    W, H, M = R.W, R.H, R.M
    total = len(picks) + 2
    wk = datetime.date.today().strftime("%d %b %Y").upper()

    # --- Cover ---
    img = Image.new("RGB", (W, H), R.INK2); d = ImageDraw.Draw(img); R.circ(d, W-70, 120, 120, R.PINK)
    R.trk(d, (M, 320), f"GIGS ON OUR RADAR · {wk}", R.mono(30), R.PINK, 3)
    d.text((M, 440), "Live", font=R.bric(150), fill=R.WHITE)
    d.text((M, 600), "this week.", font=R.bric(150), fill=R.YELLOW)
    d.text((M, 820), "The shows we'd actually", font=R.inter(40, 600), fill=(225,222,232))
    d.text((M, 876), f"go to, across {len(set(p['city'] for p in picks))} cities.", font=R.inter(40, 600), fill=(225,222,232))
    d.text((M, 1450), "Swipe the lineup →", font=R.inter(44, 600), fill=(225,222,232))
    R.footer(d, R.PINK, R.WHITE); img.save(OUT / "slide_01.png")

    # --- Gig cards (dark poster style, cycling accent) ---
    for i, g in enumerate(picks, 2):
        acc = ACCENTS[(i-2) % len(ACCENTS)]
        img = Image.new("RGB", (W, H), R.INK2); d = ImageDraw.Draw(img)
        R.trk(d, (M, 150), f"GIG · {i:02d} / {total:02d}", R.mono(28), acc, 3)
        R.trk(d, (M, 250), g["city"].upper(), R.mono(40), acc, 4)
        # event name, wrapped, big
        name_f = R.bric(96)
        lines = wrap(d, g["name"], name_f, W - 2*M)
        if len(lines) == 3: name_f = R.bric(84); lines = wrap(d, g["name"], name_f, W - 2*M)
        y = 380
        for ln in lines:
            d.text((M, y), ln, font=name_f, fill=R.WHITE); y += int(name_f.size * 1.05)
        # venue
        d.text((M, 1240), g["venue"][:40] if g["venue"] else "Venue TBA", font=R.inter(40, 600), fill=(190,182,205))
        # big date block
        d.rectangle([M, 1360, W-M, 1520], fill=acc)
        df = R.bric(72); dt = fmt_date(g["date"])
        d.text((M + 40, 1385), dt, font=df, fill=R.INK2)
        R.footer(d, acc, R.WHITE); img.save(OUT / f"slide_{i:02d}.png")

    # --- Back-the-scene beat (gradient) ---
    img = R.grad([R.PINK, R.VIOLET, R.BLUE]); d = ImageDraw.Draw(img)
    R.trk(d, (M, 300), "WHY IT MATTERS", R.mono(28), R.YELLOW, 3)
    beat = ["1,000 streams pays", "an artist about ₹10.", "A ticket pays them", "tonight. Go."]
    for j, ln in enumerate(beat):
        d.text((M, 440 + j*130), ln, font=R.bric(88), fill=(R.YELLOW if j == 3 else R.WHITE))
    R.footer(d, R.YELLOW, R.WHITE); img.save(OUT / f"slide_{total:02d}.png")

def write_caption(picks):
    lines = [f"• {g['name']} — {g['venue']}, {g['city']} · {fmt_date(g['date'])}" for g in picks]
    cap = (
        "GIGS ON OUR RADAR \U0001F3B8  live music worth leaving the house for this week.\n\n"
        + "\n".join(lines) +
        "\n\nSave this, send it to whoever you'd go with.\n"
        "Full listings on our page. Tag the venue when you go.\n\n"
        "#livemusic #indianmusic #gigs #gigguide #musicindia #whatson #newmusic"
    )
    (OUT / "caption.txt").write_text(cap)

def main():
    rows = load_events()
    picks = curate(rows, datetime.date.today())
    if not picks:
        print("generate_gigs: no upcoming shows found."); return
    build(picks)
    write_caption(picks)
    print("generate_gigs: built", len(picks), "gigs ->", OUT)
    for g in picks: print(f"   {g['city']:12} | {fmt_date(g['date'])} | {g['name'][:44]}")

if __name__ == "__main__":
    main()
