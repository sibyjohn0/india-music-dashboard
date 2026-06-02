#!/usr/bin/env python3
"""
analyze_venues.py — Build per-city venue rankings with growth tracking.

Reads all events-*.json sources, merges them, computes per-city venue
show counts. Compares with last snapshot to compute week-over-week growth.

Writes:
  data/venue-insights.json  — current rankings + growth per city
  data/venue-history.json   — rolling 8-snapshot history (updated in place)
"""

import json, os, re, glob
from datetime import datetime, timezone, timedelta
from pathlib import Path

DATA_DIR    = Path(__file__).parent.parent / "data"
OUT_INSIGHTS = DATA_DIR / "venue-insights.json"
OUT_HISTORY  = DATA_DIR / "venue-history.json"

CITY_ALIAS = {
    # Bangalore
    "bengaluru": "Bangalore", "bangalore city": "Bangalore",
    # Delhi NCR — all fold into Delhi
    "new delhi": "Delhi", "gurugram": "Delhi", "gurgaon": "Delhi",
    "delhi/ncr": "Delhi", "delhi ncr": "Delhi", "delhi (ncr)": "Delhi",
    "noida": "Delhi", "ghaziabad": "Delhi",
    "dlf cyberhub, gurugram": "Delhi",
    # Mumbai suburbs → Mumbai
    "navi mumbai": "Mumbai", "vile parle": "Mumbai", "andheri": "Mumbai",
    "dadar": "Mumbai", "bandra": "Mumbai", "borivali(w)": "Mumbai",
    "thane": "Mumbai", "matunga": "Mumbai",
    # Kolkata localities
    "southern avenue, kolkata": "Kolkata",
    # Hyderabad localities
    "lb nagar": "Hyderabad", "madhapur": "Hyderabad",
    # Kochi
    "cochin": "Kochi",
    # Pune localities
    "karve nagar, pune": "Pune", "karve nagar": "Pune",
    # Hyderabad: Birla Science Centre is in Hyderabad
    "birla science centre": "Hyderabad",
}
CITY_NAMES = {
    "bangalore","bengaluru","mumbai","delhi","hyderabad","chennai",
    "pune","kolkata","goa","kochi","cochin","india","new delhi",
}


def norm_city(c):
    return CITY_ALIAS.get((c or "").strip().lower(), (c or "").strip()) or "Other"


def _is_tour_or_date(v):
    if re.search(r'\b20\d{2}\b', v): return True
    if re.search(r'\bTour\b', v, re.IGNORECASE): return True
    months = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
    if re.match(rf'^\d+(?:st|nd|rd|th)?\s+{months}', v, re.IGNORECASE): return True
    return False


def extract_venue_from_name(name):
    n = name or ""
    def is_city(v): return v.lower().strip() in CITY_NAMES
    def clean(v):
        v = re.sub(r'\s*\([^)]*\)\s*$', '', v).strip()
        v = re.sub(r'\s+[-–|:]\s+.+$', '', v).strip()
        v = re.sub(r'\s+(?:Bengaluru|Bangalore|Mumbai|Delhi|Hyderabad|Chennai|Pune|Kolkata|Goa|Kochi)$',
                   '', v, flags=re.IGNORECASE).strip()
        return v
    m = re.search(r'\bat\.?\s+(.+)$', n, re.IGNORECASE)
    if m:
        v = clean(m.group(1))
        if 2 < len(v) <= 60 and not is_city(v) and not _is_tour_or_date(v):
            return v
    m = re.match(r'^([A-Za-z0-9 &\'\-]{4,30}?)\s+presents?\s+', n, re.IGNORECASE)
    if m:
        v = m.group(1).strip()
        if len(v) > 3 and not re.search(r'\s+x\s+|&amp;', v, re.IGNORECASE) and not is_city(v):
            return v
    sep = " || " if " || " in n else " | "
    if sep in n:
        last = n.split(sep)[-1]
        last = re.sub(r'\s*\([^)]*\)\s*$', '', last).strip()
        if len(last) > 2 and not re.match(r'^\d+\s*([ap]m)?$', last, re.IGNORECASE) \
                and not is_city(last) and not _is_tour_or_date(last):
            return last
    return ""


def get_venue(e):
    raw = (e.get("venue") or e.get("venue_name") or
           extract_venue_from_name(e.get("name") or e.get("title") or "") or "")
    return re.sub(
        r'\s+(?:Bengaluru|Bangalore|Mumbai|Delhi|Hyderabad|Chennai|Pune|Kolkata|Goa|Kochi)$',
        '', raw, flags=re.IGNORECASE
    ).strip()


def load_events():
    all_events, seen = [], set()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for path in sorted(DATA_DIR.glob("events-*.json")):
        try:
            d = json.loads(path.read_text())
        except Exception:
            continue
        evs = d if isinstance(d, list) else d.get("events", [])
        for e in evs:
            # Deduplicate same as app.js
            key = f"{(e.get('name') or e.get('title') or '').lower().strip()}|{e.get('date','') or ''}|{(e.get('city') or '').lower()}"
            if key in seen:
                continue
            seen.add(key)
            # Filter to upcoming (within 90 days, not past)
            date_str = e.get("date", "")
            if date_str and date_str < today:
                continue
            all_events.append(e)

    return all_events


def build_venue_counts(events):
    """Return {city: {venue_name: {shows, price_min, price_max, next_date}}}"""
    from collections import defaultdict

    city_venues = defaultdict(lambda: defaultdict(lambda: {"shows": 0, "prices": [], "dates": []}))

    for e in events:
        city = norm_city(e.get("city") or "")
        if not city or city == "Other":
            continue
        vname = get_venue(e)
        if not vname:
            vname = "Venue TBC"

        entry = city_venues[city][vname]
        entry["shows"] += 1
        for p in [e.get("price_min"), e.get("min_price"), e.get("price_max"), e.get("max_price")]:
            if p is not None and isinstance(p, (int, float)) and p >= 0:
                entry["prices"].append(int(p))
        if e.get("date"):
            entry["dates"].append(e["date"])

    # Convert to serialisable dicts
    result = {}
    for city, venues in city_venues.items():
        result[city] = {}
        for vname, v in venues.items():
            prices = v["prices"]
            dates  = sorted(v["dates"])
            result[city][vname] = {
                "shows":     v["shows"],
                "price_min": min(prices) if prices else None,
                "price_max": max(prices) if prices else None,
                "next_date": dates[0] if dates else None,
            }
    return result


def load_history():
    if OUT_HISTORY.exists():
        try:
            return json.loads(OUT_HISTORY.read_text())
        except Exception:
            pass
    return []


def save_history(history, current_snapshot):
    week = datetime.now(timezone.utc).strftime("%Y-W%V")
    # Replace same-week entry if exists, otherwise append
    history = [h for h in history if h.get("week") != week]
    history.append({"week": week, "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "cities": current_snapshot})
    # Keep last 8 snapshots
    history = history[-8:]
    OUT_HISTORY.write_text(json.dumps(history, indent=2))


def compute_growth(current, history):
    """Map venue -> growth vs last snapshot. Returns {city: {venue: growth_int_or_None}}"""
    if not history:
        return {}
    last = history[-1].get("cities", {})
    result = {}
    for city, venues in current.items():
        last_city = last.get(city, {})
        result[city] = {}
        for vname, v in venues.items():
            prev = last_city.get(vname)
            if prev is not None:
                result[city][vname] = v["shows"] - prev.get("shows", 0)
            else:
                result[city][vname] = None  # new venue, no baseline
    return result


def build_insights(current_counts, growth_map, generated_at):
    """Build the venue-insights.json structure."""
    cities = {}
    for city, venues in current_counts.items():
        ranked = sorted(
            [(vname, v) for vname, v in venues.items() if vname != "Venue TBC"],
            key=lambda x: -x[1]["shows"]
        )
        city_growth = growth_map.get(city, {})

        venue_list = []
        for vname, v in ranked:
            g = city_growth.get(vname)
            venue_list.append({
                "name":      vname,
                "shows":     v["shows"],
                "price_min": v["price_min"],
                "price_max": v["price_max"],
                "next_date": v["next_date"],
                "growth":    g,  # int or None
            })

        tbc_entry = venues.get("Venue TBC")
        cities[city] = {
            "total_shows": sum(v["shows"] for v in venues.values()),
            "venues":      venue_list,
            "unlisted_shows": tbc_entry["shows"] if tbc_entry else 0,
        }

    return {
        "generated_at": generated_at,
        "snapshot_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "cities": cities,
    }


def main():
    print("Analyzing venue data...")
    generated_at = datetime.now(timezone.utc).isoformat()

    events = load_events()
    print(f"  Loaded {len(events)} upcoming events")

    current = build_venue_counts(events)
    total_venues = sum(len(v) for v in current.values())
    print(f"  {total_venues} venues across {len(current)} cities")

    history = load_history()
    growth  = compute_growth(current, history)

    new_venues = sum(
        1 for city in growth.values() for g in city.values() if g is None
    )
    growing = sum(
        1 for city in growth.values() for g in city.values() if g and g > 0
    )
    print(f"  Growth data: {growing} venues gaining shows, {new_venues} new venues (no baseline)")

    insights = build_insights(current, growth, generated_at)
    OUT_INSIGHTS.write_text(json.dumps(insights, indent=2))
    print(f"  Written venue-insights.json ({len(insights['cities'])} cities)")

    save_history(history, current)
    h = load_history()
    print(f"  venue-history.json updated ({len(h)} snapshots)")


if __name__ == "__main__":
    main()
