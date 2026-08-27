#!/usr/bin/env python3
"""
build_festivals.py — Classify + dedupe the ticketing-feed events into a clean
"Festivals & Tours" dataset, merged with the curated marquee registry.

Reads all data/events-*.json (District, BookMyShow, Skillboxes, Paytm, ...),
keeps only festivals + notable artist tours (drops club nights, cruises,
comedy, kids shows, etc.), then:
  - dedupes multi-city tours (Papon x5, Krishna Das x4) into ONE entry with
    all dates/cities  <-- the core value-add
  - merges data/festivals_registry.json so marquee festivals (NH7, Lolla,
    Sunburn, Echoes of Earth...) always appear, enriched with official links
    and lineup when a live feed confirms an edition
  - flags entries new since the last run (for the "just announced" social play)

Output: data/festivals.json  (consumed by generate_festivals_page.py + social)

No new scraping: this is a curation layer over the existing event fetchers.
"""
import os, re, json, glob
from datetime import datetime, date, timezone

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
OUT  = os.path.join(DATA, "festivals.json")
REGISTRY = os.path.join(DATA, "festivals_registry.json")

TODAY = date.today()

# --- classification ----------------------------------------------------------
# Drop these outright even if they contain "festival"/"tour".
EXCLUDE = re.compile(
    r"\b(comedy|stand[\s-]?up|open mic|open-mic|karaoke|quiz night|pub quiz|"
    r"brunch|cruise|kids?|children|toddler|workshop|masterclass|bootcamp|"
    r"screening|watch party|ladies night|singles|speed dating|costume|"
    r"halloween party|horrorcon|comic con|cosplay|pet |dog |puppy|"
    r"flea market|expo|webinar|meetup|networking)\b", re.I)

# Keep as a festival.
FESTIVAL_RE = re.compile(r"\b(festival|weekender|fest|carnival|mahotsav|utsav|fiesta)\b", re.I)
# Keep as a tour / notable single-artist gig.
TOUR_RE = re.compile(r"\b(tour|live in concert|world tour|india tour|unplugged|on tour|live in )\b", re.I)

# --- international vs Indian-focused (for the SEO split: top 50 intl / top 25 Indian) ---
# These are INDIAN ticketing feeds, so the correct default is "indian". An entry is
# "international" only on a clear signal: a global-franchise festival or a known
# touring international act (the acts that drive "<artist> India tour" searches).
INTL_FRANCHISE = re.compile(r"\b(lollapalooza|sunburn|supersonic|tomorrowland)\b", re.I)
INTL_ARTISTS = re.compile(
    r"\b(gorillaz|chet faker|opeth|fred again|dua lipa|coldplay|ed sheeran|maroon 5|"
    r"guns n'? roses|bryan adams|alan walker|martin garrix|marshmello|dj snake|lauv|"
    r"the script|onerepublic|one republic|imagine dragons|backstreet boys|khalid|"
    r"post malone|travis scott|kanye|\bye\b|dixon|tale of us|ben b[oö]hmer|boris brejcha|"
    r"anyma|domi|jd beck|jacob collier|john mayer|louis tomlinson|charlie puth|"
    r"shawn mendes|glass animals|cigarettes after sex|arctic monkeys|the lumineers|"
    r"thirty seconds to mars|scorpions|iron maiden|metallica|megadeth|sabaton|"
    r"lamb of god|bring me the horizon|azyr|afro yoki|chainsmokers|nucleya b2b|"
    r"black coffee|carl cox|david guetta|hardwell|armin van buuren|deadmau5)\b", re.I)

CAP_INTL = 50    # top international tours + festivals
CAP_INDIAN = 25  # top Indian-focused


def origin_of(title):
    if INTL_FRANCHISE.search(title) or INTL_ARTISTS.search(title):
        return "international"
    return "indian"

MONTHS = {m.lower(): i for i, m in enumerate(
    ["", "January","February","March","April","May","June","July","August",
     "September","October","November","December"])}
MONTHS.update({m[:3].lower(): i for m, i in list(MONTHS.items()) if m})


def parse_date(raw):
    """Return (iso_str, date_obj) best-effort. date_obj None if unparseable."""
    if not raw:
        return raw, None
    raw = str(raw).strip()
    # ISO YYYY-MM-DD
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", raw)
    if m:
        try:
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return d.isoformat(), d
        except ValueError:
            return raw, None
    # "21 Nov Sat" / "24 October" / "29 Aug Sat"
    m = re.match(r"(\d{1,2})\s+([A-Za-z]+)", raw)
    if m:
        day = int(m.group(1)); mon = MONTHS.get(m.group(2).lower())
        if mon:
            yr = TODAY.year if mon >= TODAY.month else TODAY.year + 1
            try:
                d = date(yr, mon, day)
                return d.isoformat(), d
            except ValueError:
                return raw, None
    return raw, None


def load_events():
    out = []
    for f in glob.glob(os.path.join(DATA, "events-*.json")):
        src = os.path.basename(f).replace("events-", "").replace(".json", "")
        try:
            d = json.load(open(f))
        except Exception:
            continue
        arr = d.get("events", []) if isinstance(d, dict) else (d if isinstance(d, list) else [])
        for e in arr:
            name = (e.get("name") or "").strip()
            if not name:
                continue
            out.append({
                "name": name,
                "venue": (e.get("venue") or "").strip(),
                "city": (e.get("city") or "").strip(),
                "raw_date": e.get("date") or "",
                "time": e.get("time") or "",
                "price_min": e.get("price_min"),
                "price_max": e.get("price_max"),
                "url": e.get("url") or "",
                "source": src,
            })
    return out


def classify(name):
    if EXCLUDE.search(name):
        return None
    if FESTIVAL_RE.search(name):
        return "festival"
    if TOUR_RE.search(name):
        return "tour"
    return None


# City tokens to strip when building a dedupe key for multi-city tours.
CITY_TOKENS = ["mumbai","bombay","delhi","new delhi","ncr","gurugram","gurgaon",
    "bengaluru","bangalore","chennai","kolkata","calcutta","hyderabad","pune",
    "goa","kochi","jaipur","ahmedabad","chandigarh","shillong","guwahati","kullu"]


def tour_key(name):
    """Normalize an event name into a key that collapses per-city variants."""
    k = name.lower()
    k = re.split(r"[|\-–—]", k)[0]                 # drop "| Bengaluru" / "- Mumbai" suffixes
    k = re.sub(r"\bshow\s*\d+\b", "", k)           # "Show 2"
    k = re.sub(r"\b(20\d{2})\b", "", k)            # year
    for c in CITY_TOKENS:
        k = re.sub(rf"\b{re.escape(c)}\b", "", k)
    k = re.sub(r"[^a-z0-9 ]", " ", k)
    k = re.sub(r"\s+", " ", k).strip()
    return k


def clean_title(name):
    """Human-facing title: strip trailing city/pipe segments."""
    t = re.split(r"\s*[|]\s*", name)[0]
    t = re.sub(r"\s*[-–—]\s*(" + "|".join(CITY_TOKENS) + r")\b.*$", "", t, flags=re.I)
    return t.strip() or name.strip()


def price_str(pmin, pmax):
    def norm(v):
        try:
            v = int(float(str(v)))
            return v if v > 0 else None
        except (TypeError, ValueError):
            return None
    lo, hi = norm(pmin), norm(pmax)
    if lo and hi and hi > lo:
        return f"₹{lo:,}–₹{hi:,}"
    if lo:
        return f"from ₹{lo:,}"
    if hi:
        return f"from ₹{hi:,}"
    return ""


def build():
    reg = json.load(open(REGISTRY)).get("festivals", [])
    # (alias, registry-name) pairs, longest-first so specific aliases win.
    alias_pairs = sorted(
        [(a.lower(), rf["name"]) for rf in reg for a in rf.get("aliases", [])],
        key=lambda p: -len(p[0]))

    def registry_hit(name):
        low = name.lower()
        for a, rn in alias_pairs:
            if a in low:
                return rn
        return None

    events = load_events()
    groups = {}   # key -> entry
    for e in events:
        kind = classify(e["name"])
        if not kind and registry_hit(e["name"]) and not EXCLUDE.search(e["name"]):
            kind = "festival"   # marquee festival names lack generic keywords ("Echoes of Earth")
        if not kind:
            continue
        iso, dobj = parse_date(e["raw_date"])
        # Drop clearly-past dates (keep undated — they may be TBA/upcoming).
        if dobj and dobj < TODAY:
            continue
        key = (kind, tour_key(e["name"]))
        g = groups.setdefault(key, {
            "title": clean_title(e["name"]),
            "type": kind,
            "dates": [],
            "_titles": set(),
        })
        g["_titles"].add(e["name"])
        g["dates"].append({
            "date": iso, "date_obj": dobj.isoformat() if dobj else None,
            "city": e["city"], "venue": e["venue"], "time": e["time"],
            "price": price_str(e["price_min"], e["price_max"]),
            "url": e["url"], "source": e["source"],
        })

    # Finalize each group.
    entries = []
    for (kind, key), g in groups.items():
        dts = sorted(g["dates"], key=lambda d: (d["date_obj"] is None, d["date_obj"] or ""))
        cities = sorted({d["city"] for d in dts if d["city"]})
        soonest = next((d["date_obj"] for d in dts if d["date_obj"]), None)
        entries.append({
            "title": g["title"], "type": kind, "key": key,
            "cities": cities, "dates": dts,
            "soonest": soonest, "marquee": False,
            "official_url": "", "ig": "", "season": "", "tags": [],
        })

    # --- merge curated registry -------------------------------------------------
    matched_keys = set()
    for rf in reg:
        aliases = sorted([a.lower() for a in rf.get("aliases", [])], key=len, reverse=True)
        hit = None
        # Try the most specific alias first ("sunburn festival" before bare "sunburn"),
        # and among matches prefer a dated, soonest entry over a TBA/club-night one.
        for a in aliases:
            cands = [en for en in entries
                     if a in (en["title"] + " " + " ".join(en["cities"])).lower() or a in en["key"]]
            if cands:
                cands.sort(key=lambda en: (not en.get("dates"), en["soonest"] is None, en["soonest"] or "9999"))
                hit = cands[0]
                break
        if hit:
            hit.update({"marquee": True, "official_url": rf["official_url"],
                        "ig": rf.get("ig", ""), "season": rf.get("season", ""),
                        "tags": rf.get("tags", []), "title": rf["name"], "type": "festival",
                        "home_city": rf.get("city", "")})
            matched_keys.add(rf["name"])
        else:
            # Marquee festival with no confirmed edition yet — show as anchor.
            entries.append({
                "title": rf["name"], "type": "festival", "key": rf["name"].lower(),
                "cities": [rf.get("city", "")], "dates": [],
                "soonest": None, "marquee": True, "status": "dates TBA",
                "official_url": rf["official_url"], "ig": rf.get("ig", ""),
                "season": rf.get("season", ""), "tags": rf.get("tags", []),
                "home_city": rf.get("city", ""),
            })

    # --- detect new-since-last-run (for "just announced") ----------------------
    prev_keys = set()
    if os.path.exists(OUT):
        try:
            old = json.load(open(OUT))
            prev_keys = set(old.get("_all_keys", []))
        except Exception:
            pass
    all_keys = [e["key"] for e in entries]
    # Only real (dated) entries count as announcements, not TBA placeholders.
    new_this_run = [e["title"] for e in entries
                    if e["key"] not in prev_keys and e.get("dates")]

    # Tag origin (international vs indian-focused) for the SEO split.
    for e in entries:
        e["origin"] = origin_of(e["title"])

    festivals = [e for e in entries if e["type"] == "festival"]
    tours     = [e for e in entries if e["type"] == "tour"]
    # Sort: marquee first, then soonest date, then title.
    festivals.sort(key=lambda e: (not e["marquee"], e["soonest"] is None, e["soonest"] or "9999", e["title"].lower()))
    tours.sort(key=lambda e: (e["soonest"] is None, e["soonest"] or "9999", e["title"].lower()))

    # SEO caps: keep top 50 international + top 25 Indian-focused across the combined
    # set (marquee festivals are always kept regardless of cap).
    combined = festivals + tours
    kept, n_intl, n_ind = [], 0, 0
    for e in sorted(combined, key=lambda e: (not e.get("marquee"), e["soonest"] is None, e["soonest"] or "9999")):
        if e.get("marquee"):
            kept.append(e); continue
        if e["origin"] == "international" and n_intl < CAP_INTL:
            kept.append(e); n_intl += 1
        elif e["origin"] == "indian" and n_ind < CAP_INDIAN:
            kept.append(e); n_ind += 1
    keep_keys = {id(e) for e in kept}
    festivals = [e for e in festivals if id(e) in keep_keys]
    tours     = [e for e in tours if id(e) in keep_keys]

    for e in festivals + tours:
        e.pop("_titles", None)

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {"festivals": len(festivals), "tours": len(tours),
                   "marquee": sum(1 for e in festivals if e["marquee"]),
                   "international": sum(1 for e in festivals + tours if e["origin"] == "international"),
                   "indian": sum(1 for e in festivals + tours if e["origin"] == "indian"),
                   "new_this_run": len(new_this_run)},
        "festivals": festivals,
        "tours": tours,
        "new_this_run": new_this_run,
        "_all_keys": all_keys,
    }
    os.makedirs(DATA, exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=2, ensure_ascii=False)
    print(f"build_festivals: {len(festivals)} festivals ({out['counts']['marquee']} marquee), "
          f"{len(tours)} tours, {len(new_this_run)} new")
    for e in (festivals + tours)[:12]:
        when = e["soonest"] or e.get("status", "TBA")
        print(f"  [{e['type']}] {when}  {e['title'][:50]:50} {'/'.join(e['cities'])[:40]}")


if __name__ == "__main__":
    build()
