#!/usr/bin/env python3
"""
fetch_events_thumpn.py — Pull live events from thumpN (thumpn.com).

thumpN is a new (2026, beta) AI-native discovery/ticketing platform. It has no
public listings API; its homepage widget endpoint
(/api/config/web/home/widgets?category=<cat>) returns a small curated set of
event cards behind a Cloudflare JS challenge. So we drive a real browser with
Playwright to clear Cloudflare, then fetch the widget JSON from inside the page
and extract the event cards.

Card fields available: title, venue ("Venue Name: City"), dateLabel ("4 Jul"),
primaryLabel (ticketing partner). No ticket URL / price is exposed, and the feed
is geo-defaulted, so this is a light SUPPLEMENT to the main ticketing feeds, not
a comprehensive source. Output matches the other events-*.json files so
build_festivals.py and build_venues.py pick it up automatically.

Output: data/events-thumpn.json
GitHub Actions note: requires `playwright install chromium` (already in workflow).
"""
import json, os, re, sys
from datetime import datetime, timezone, date, timedelta
from pathlib import Path

REPO = Path(__file__).parent.parent
OUT = REPO / "data" / "events-thumpn.json"
TODAY = date.today()

CATEGORIES = ["music", "festivals", "nightlife"]
BASE = "https://thumpn.com/"
API = "/api/config/web/home/widgets?category="

MONTHS = {m[:3].lower(): i for i, m in enumerate(
    ["", "January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"]) if m}

# In-page JS: fetch each category's widgets and flatten the event cards.
EXTRACT_JS = """
async (cats) => {
  const out = [];
  for (const c of cats) {
    try {
      const j = await fetch('/api/config/web/home/widgets?category=' + c,
                            {headers:{'Accept':'application/json'}}).then(r => r.json());
      (function scan(o){
        if (!o || typeof o !== 'object') return;
        if (o.title && o.venue !== undefined && !o.children) {
          out.push({title:o.title, venue:o.venue||'', date:o.dateLabel||'',
                    partner:o.primaryLabel||'', category:c});
        }
        Object.values(o).forEach(scan);
      })(j);
    } catch (e) {}
  }
  // de-dup by title+venue
  return [...new Map(out.map(e => [e.title + '|' + e.venue, e])).values()];
}
"""


def parse_date(label):
    """'4 Jul' -> ISO, inferring the year as the next plausible occurrence."""
    if not label:
        return None
    m = re.match(r"(\d{1,2})\s+([A-Za-z]{3})", label.strip())
    if not m:
        return None
    day = int(m.group(1)); mon = MONTHS.get(m.group(2).lower())
    if not mon:
        return None
    try:
        d = date(TODAY.year, mon, day)
    except ValueError:
        return None
    # Rolled well into the past (>~6.5 months) -> it's next year's edition.
    if (TODAY - d).days > 200:
        try:
            d = date(TODAY.year + 1, mon, day)
        except ValueError:
            return None
    return d.isoformat()


def split_venue_city(venue):
    """'BudBee Restobar 104: Bengaluru' -> ('BudBee Restobar 104', 'Bengaluru')."""
    if ":" in venue:
        left, right = venue.rsplit(":", 1)
        return left.strip(), right.strip()
    return venue.strip(), ""


def partner_of(label):
    low = (label or "").lower()
    for p in ("district", "bookmyshow", "skillbox", "paytm", "insider", "zomato"):
        if p in low:
            return p
    return "thumpn"


def load_last():
    if OUT.exists():
        try:
            return json.load(open(OUT))
        except Exception:
            pass
    return None


def scrape():
    from playwright.sync_api import sync_playwright
    events = []
    with sync_playwright() as pw:
        # Headed (not headless): thumpN's Cloudflare blocks the API XHR in headless
        # mode. In CI this runs under xvfb (see pipeline.yml) so a display exists.
        browser = pw.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
            viewport={"width": 1280, "height": 900}, locale="en-US")
        page = ctx.new_page()
        try:
            page.goto(BASE, wait_until="domcontentloaded", timeout=45_000)
        except Exception as e:
            print(f"  goto failed: {e}", file=sys.stderr)
            browser.close(); return None
        # Wait for the Cloudflare "Just a moment..." challenge to clear.
        for _ in range(20):
            title = (page.title() or "").lower()
            if "just a moment" not in title and "attention required" not in title:
                break
            page.wait_for_timeout(1500)
        else:
            print("  Cloudflare challenge did not clear (headless likely blocked).", file=sys.stderr)
            browser.close(); return None
        page.wait_for_timeout(1500)
        try:
            raw = page.evaluate(EXTRACT_JS, CATEGORIES)
        except Exception as e:
            print(f"  evaluate failed: {e}", file=sys.stderr)
            browser.close(); return None
        browser.close()

    for e in raw or []:
        venue, city = split_venue_city(e.get("venue", ""))
        events.append({
            "name": e.get("title", "").strip(),
            "venue": venue,
            "city": city,
            "date": parse_date(e.get("date", "")),
            "time": "",
            "price_min": None,
            "price_max": None,
            "url": "",  # thumpN cards expose no direct ticket URL
            "source": "thumpn",
            "ticket_partner": partner_of(e.get("partner", "")),
            "category": e.get("category", ""),
        })
    return events


def main():
    try:
        events = scrape()
    except ImportError:
        print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium",
              file=sys.stderr)
        sys.exit(1)

    fetched_at = datetime.now(timezone.utc).isoformat()
    if not events:
        last = load_last()
        if last and last.get("events"):
            print(f"  thumpN returned nothing — preserving last known ({len(last['events'])} events).")
            sys.exit(0)
        json.dump({"events": [], "fetched_at": fetched_at, "total": 0,
                   "note": "thumpN returned no events (Cloudflare block or empty feed)."},
                  open(OUT, "w"), indent=2, ensure_ascii=False)
        print("  Wrote empty placeholder.")
        return

    # keep only dated future events + undated (drop clearly-past)
    kept = [e for e in events if not e["date"] or e["date"] >= TODAY.isoformat()]
    out = {"events": kept, "fetched_at": fetched_at, "total": len(kept),
           "source": "thumpN", "note": "Curated feed; no ticket URL/price exposed."}
    json.dump(out, open(OUT, "w"), indent=2, ensure_ascii=False)
    print(f"OK: events-thumpn.json — {len(kept)} events ({len(events)} raw) at {fetched_at}")
    for e in kept[:8]:
        print(f"  {e['date'] or 'TBA':10} {e['city'][:12]:12} {e['name'][:40]:40} @ {e['venue'][:24]}")


if __name__ == "__main__":
    main()
