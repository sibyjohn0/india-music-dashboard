#!/usr/bin/env python3
"""
build_venues.py — Aggregate the ticketing-feed events into a per-venue dataset
for the /venues/ SEO pages ("Live music venues in <city>").

Curation layer over the existing event fetchers (no new scraping). For each of
the six metros it lists the venues that actually host live music, each with its
upcoming gigs, price range and locality — the raw material for a venue page +
MusicVenue schema, and the internal-linking loop with /live/.

Output: data/venues.json
"""
import os, re, json, glob
from datetime import date

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "venues.json")
TODAY = date.today()

# The six metros + the localities/mislabels that roll up into each.
METROS = {
    "Mumbai":    ["mumbai", "bombay", "navi mumbai", "thane", "mulund", "andheri",
                  "bandra", "lower parel", "worli", "ncpa", "juhu", "khar"],
    "Delhi":     ["delhi", "new delhi", "gurugram", "gurgaon", "noida", "okhla",
                  "ncr", "greater noida", "dwarka", "saket"],
    "Bengaluru": ["bengaluru", "bangalore", "koramangala", "indiranagar", "whitefield",
                  "hsr", "jayanagar", "electronic city"],
    "Hyderabad": ["hyderabad", "gachibowli", "kondapur", "madhapur", "jubilee hills",
                  "hitech city", "hitec city", "banjara hills", "secunderabad"],
    "Pune":      ["pune", "kalyani nagar", "koregaon", "viman nagar", "hinjewadi"],
    "Goa":       ["goa", "calangute", "anjuna", "vagator", "panjim", "panaji", "mapusa",
                  "candolim", "morjim", "assagao", "siolim", "baga"],
}
# Longest-first so "navi mumbai" wins over "mumbai".
METRO_LOOKUP = sorted(
    [(tok, metro) for metro, toks in METROS.items() for tok in toks],
    key=lambda p: -len(p[0]))

SLUG = {"Mumbai": "mumbai", "Delhi": "delhi", "Bengaluru": "bengaluru",
        "Hyderabad": "hyderabad", "Pune": "pune", "Goa": "goa"}

JUNK_VENUE = re.compile(r"^\s*$|venue to be announced|to be announced|^tba$|"
                        r"multiple venues|^online|^various", re.I)

# A venue name that is really just a city/locality (bad feed data) — not a venue.
PLACE_ONLY = set(t for toks in METROS.values() for t in toks) | {
    "gurugram", "gurgaon", "noida", "new delhi", "navi mumbai", "bengaluru"}

def is_place_only(venue):
    return venue.strip().lower() in PLACE_ONLY

# Locality words to lift out of a venue name for the "area" line.
AREA_WORDS = set(w for toks in METROS.values() for w in toks) | {
    "hsr layout", "hsr", "jubilee hills", "banjara hills", "jp nagar", "mg road",
    "brigade road", "church street", "connaught place", "hauz khas", "cyber hub"}


def norm_city(city, venue):
    blob = f"{city} {venue}".lower()
    for tok, metro in METRO_LOOKUP:
        if re.search(rf"\b{re.escape(tok)}\b", blob):
            return metro
    return None


def parse_date(raw):
    if not raw:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(raw))
    if m:
        try:
            return date(int(m[1]), int(m[2]), int(m[3])).isoformat()
        except ValueError:
            return None
    return None


def area_of(venue, city):
    low = venue.lower()
    for a in sorted(AREA_WORDS, key=len, reverse=True):
        if a not in ("goa",) and re.search(rf"\b{re.escape(a)}\b", low) and a != city.lower():
            return a.title()
    return ""


def price_str(lo, hi):
    def n(v):
        try:
            v = int(float(str(v)));  return v if v > 0 else None
        except (TypeError, ValueError):
            return None
    lo, hi = n(lo), n(hi)
    if lo and hi and hi > lo: return f"₹{lo:,}–₹{hi:,}"
    if lo: return f"from ₹{lo:,}"
    if hi: return f"from ₹{hi:,}"
    return ""


def build():
    venues = {}   # (metro, venue) -> data
    for f in glob.glob(os.path.join(DATA, "events-*.json")):
        src = os.path.basename(f).replace("events-", "").replace(".json", "")
        try:
            d = json.load(open(f))
        except Exception:
            continue
        arr = d.get("events", []) if isinstance(d, dict) else (d if isinstance(d, list) else [])
        for e in arr:
            venue = (e.get("venue") or "").strip()
            if not venue or JUNK_VENUE.search(venue) or is_place_only(venue):
                continue
            metro = norm_city(e.get("city", ""), venue)
            if not metro:
                continue
            iso = parse_date(e.get("date"))
            if iso and iso < TODAY.isoformat():
                continue
            key = (metro, venue)
            v = venues.setdefault(key, {"name": venue, "city": metro,
                                        "area": area_of(venue, metro), "gigs": []})
            v["gigs"].append({
                "name": (e.get("name") or "").strip(),
                "date": iso, "url": (e.get("url") or "").strip(),
                "price": price_str(e.get("price_min"), e.get("price_max")),
                "source": src,
            })

    # Finalize per city.
    by_city = {m: [] for m in METROS}
    for (metro, _), v in venues.items():
        gigs = sorted([g for g in v["gigs"] if g["name"]],
                      key=lambda g: (g["date"] is None, g["date"] or "9999"))
        # de-dup identical gig names (same tour, multiple feed rows)
        seen, uniq = set(), []
        for g in gigs:
            k = g["name"].lower()
            if k in seen:
                continue
            seen.add(k); uniq.append(g)
        if not uniq:
            continue
        prices = [g["price"] for g in uniq if g["price"]]
        v["gigs"] = uniq
        v["shows"] = len(uniq)
        v["next_date"] = next((g["date"] for g in uniq if g["date"]), None)
        by_city[metro].append(v)

    for metro in by_city:
        by_city[metro].sort(key=lambda v: (-v["shows"], v["next_date"] is None, v["next_date"] or "9999"))

    out = {
        "generated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(),
        "cities": {SLUG[m]: {"name": m, "venue_count": len(by_city[m]),
                             "show_count": sum(v["shows"] for v in by_city[m]),
                             "venues": by_city[m][:40]}
                   for m in METROS},
    }
    json.dump(out, open(OUT, "w"), indent=2, ensure_ascii=False)
    tot_v = sum(c["venue_count"] for c in out["cities"].values())
    tot_s = sum(c["show_count"] for c in out["cities"].values())
    print(f"build_venues: {tot_v} venues, {tot_s} upcoming shows across {len(METROS)} metros")
    for slug, c in out["cities"].items():
        print(f"  {c['name']:10} {c['venue_count']:3} venues, {c['show_count']:3} shows"
              f"  | top: {', '.join(v['name'][:22] for v in c['venues'][:3])}")


if __name__ == "__main__":
    build()
