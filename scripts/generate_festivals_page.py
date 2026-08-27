#!/usr/bin/env python3
"""Generate the server-rendered /live/ page from data/festivals.json.

"Festivals & Tours across India" — India's marquee festivals (always shown as
the search anchor) plus live festival + tour dates deduped from ticketing feeds.
Server-rendered HTML with MusicEvent JSON-LD per concrete date (targets Google
event rich-results + AI citation) and Breadcrumb schema. Runs daily in pipeline.
"""
import os, re, json, html, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "data" / "festivals.json"
OUT = REPO / "live" / "index.html"

def esc(s): return html.escape(str(s or ""), quote=True)

def fmt(iso):
    try:
        return datetime.date.fromisoformat(iso).strftime("%d %b %Y")
    except Exception:
        return ""

SRC_LABEL = {"district": "District", "bookmyshow": "BookMyShow",
             "skillboxes": "Skillboxes", "paytm": "Paytm Insider",
             "highape": "HighApe", "songkick": "Songkick"}

def date_rows(e):
    rows = []
    for d in e.get("dates", []):
        when = fmt(d["date_obj"]) if d.get("date_obj") else esc(d.get("date", ""))
        city = esc(d.get("city", ""))
        venue = esc(d.get("venue", ""))
        price = esc(d.get("price", ""))
        src = SRC_LABEL.get(d.get("source", ""), d.get("source", "").title())
        url = esc(d.get("url", ""))
        loc = " · ".join([x for x in [f"<b>{city}</b>" if city else "", venue] if x])
        tix = f'<a class="tix" href="{url}" target="_blank" rel="noopener">Tickets · {esc(src)} ↗</a>' if url else ""
        meta = " · ".join([x for x in [price] if x])
        rows.append(f'''<div class="drow">
        <div class="dwhen">{when or "Dates TBA"}</div>
        <div class="dloc">{loc}{f' <span class="dprice">{meta}</span>' if meta else ''}</div>
        {tix}
      </div>''')
    return "\n".join(rows)

def card(e):
    origin = e.get("origin", "indian")
    badge = '<span class="tag intl">International</span>' if origin == "international" else '<span class="tag ind">India</span>'
    marquee = '<span class="tag mq">Marquee festival</span>' if e.get("marquee") else ""
    sub = []
    if e.get("season"): sub.append(esc(e["season"]))
    # Marquee festivals show their canonical home city; others list matched cities.
    city_txt = e.get("home_city") if e.get("marquee") else ", ".join([c for c in e.get("cities", []) if c])
    if city_txt: sub.append(esc(city_txt))
    subline = " · ".join(sub)
    official = ""
    if e.get("official_url"):
        official = f'<a class="official" href="{esc(e["official_url"])}" target="_blank" rel="noopener">Official site ↗</a>'
    ig = ""
    if e.get("ig"):
        ig = f'<a class="official" href="https://instagram.com/{esc(e["ig"])}" target="_blank" rel="noopener">@{esc(e["ig"])}</a>'
    rows = date_rows(e)
    status = "" if e.get("dates") else f'<div class="tba">{esc(e.get("status","Dates to be announced"))} · check the official site</div>'
    return f'''  <div class="card">
    <div class="ctop">
      <h3>{esc(e["title"])}</h3>
      <div class="tags">{marquee}{badge}</div>
    </div>
    {f'<div class="csub">{subline}</div>' if subline else ''}
    <div class="links">{official}{ig}</div>
    {rows}
    {status}
  </div>'''

def schema_events(entries):
    items, pos = [], 0
    for e in entries:
        for d in e.get("dates", []):
            if not d.get("date_obj"):
                continue
            pos += 1
            loc_name = d.get("venue") or d.get("city") or "India"
            offers = ""
            if d.get("url"):
                offers = f',"offers":{{"@type":"Offer","url":{json.dumps(d["url"])},"availability":"https://schema.org/InStock"}}'
            items.append(
                '{"@type":"ListItem","position":%d,"item":{"@type":"MusicEvent","name":%s,'
                '"startDate":"%s","eventAttendanceMode":"https://schema.org/OfflineEventAttendanceMode",'
                '"eventStatus":"https://schema.org/EventScheduled",'
                '"location":{"@type":"Place","name":%s,"address":{"@type":"PostalAddress","addressLocality":%s,"addressCountry":"IN"}}%s}}'
                % (pos, json.dumps(e["title"]), d["date_obj"], json.dumps(loc_name),
                   json.dumps(d.get("city") or "India"), offers))
    return ",".join(items), pos

def build():
    d = json.load(open(SRC))
    festivals = d.get("festivals", [])
    tours = d.get("tours", [])
    c = d.get("counts", {})
    updated = fmt(d.get("generated_at", "")[:10]) or datetime.date.today().strftime("%d %b %Y")

    fest_html = "\n".join(card(e) for e in festivals) or '<p style="color:var(--muted)">Festival dates land here as they are announced.</p>'
    tour_html = "\n".join(card(e) for e in tours) or '<p style="color:var(--muted)">Tour dates land here as they are announced.</p>'
    schema, n_events = schema_events(festivals + tours)

    page = f'''<!DOCTYPE html>
<html lang="en-IN">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-R7EYMGZEJZ"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-R7EYMGZEJZ');</script>
  <meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Indian music festivals &amp; tours 2026–27: dates, venues, lineups — Indie Music India</title>
  <meta name="description" content="Live dates, venues and ticket links for India's music festivals and artist tours — NH7 Weekender, Lollapalooza India, Sunburn, Echoes of Earth, plus international acts touring India. Updated daily." />
  <link rel="canonical" href="https://indiemusicindia.com/live/" />
  <meta property="og:title" content="Indian music festivals & tours: dates, venues, lineups" />
  <meta property="og:description" content="Live festival and tour dates across India, updated daily. Tickets, venues and official links in one place." />
  <meta property="og:url" content="https://indiemusicindia.com/live/" />
  <meta property="og:type" content="website" />
  <meta property="og:image" content="https://indiemusicindia.com/og-image.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <style>*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#0d0d0f;--surface:#141418;--border:#242430;--accent:#e94560;--text:#e8e8f0;--muted:#8a8aa0}}
body{{font-family:'Inter',-apple-system,sans-serif;background:var(--bg);color:var(--text);line-height:1.6;overflow-x:hidden}}
a{{color:inherit;text-decoration:none}}
header{{display:flex;align-items:center;padding:0 32px;height:52px;background:rgba(13,13,15,.96);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100}}
.logo{{font-size:15px;font-weight:700}}
nav{{display:flex;padding:0 24px;background:var(--surface);border-bottom:1px solid var(--border);overflow-x:auto;scrollbar-width:none}}
nav::-webkit-scrollbar{{display:none}}
.tab{{color:#999;font:13px/1 'Inter',sans-serif;padding:0 16px;height:44px;display:flex;align-items:center;white-space:nowrap;flex-shrink:0;font-weight:500}}
.page{{max-width:820px;margin:0 auto;padding:34px 32px 90px}}
.crumb{{font-size:12px;color:var(--muted);margin-bottom:16px}}
.eyebrow{{font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--accent)}}
h1{{font-size:clamp(26px,4.5vw,40px);font-weight:800;letter-spacing:-1px;line-height:1.12;margin:12px 0 0}}
.lead{{font-size:16px;color:#c6c6d8;margin-top:14px;max-width:640px}}
.stat{{font-size:12px;color:var(--muted);margin-top:12px}}
h2.sec{{font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:1.2px;color:var(--accent);margin:40px 0 4px}}
.seclead{{font-size:14px;color:var(--muted);margin-bottom:14px}}
.card{{border:1px solid var(--border);border-radius:14px;padding:18px 20px;background:var(--surface);margin-bottom:12px}}
.ctop{{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap}}
.card h3{{font-size:19px;font-weight:800;letter-spacing:-.3px;line-height:1.25}}
.tags{{display:flex;gap:6px;flex-shrink:0;flex-wrap:wrap}}
.tag{{font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.5px;padding:4px 8px;border-radius:20px;white-space:nowrap}}
.tag.intl{{background:rgba(80,140,255,.14);color:#7aa8ff}}
.tag.ind{{background:rgba(233,69,96,.14);color:var(--accent)}}
.tag.mq{{background:rgba(255,190,60,.16);color:#f0b74a}}
.csub{{font-size:13px;color:var(--muted);margin-top:4px;font-weight:600}}
.links{{display:flex;gap:14px;margin:8px 0 2px;flex-wrap:wrap}}
.official{{font-size:12px;font-weight:700;color:#7aa8ff}}
.drow{{border-top:1px solid var(--border);padding:10px 0 2px;margin-top:10px}}
.dwhen{{font-size:14px;font-weight:800}}
.dloc{{font-size:13px;color:#c6c6d8;margin-top:1px}}
.dprice{{color:var(--muted);font-weight:600}}
.tix{{display:inline-block;font-size:12px;font-weight:700;color:var(--accent);margin-top:6px}}
.tba{{font-size:13px;color:var(--muted);border-top:1px solid var(--border);padding-top:10px;margin-top:10px;font-style:italic}}
.cta{{margin-top:40px;border:1px solid var(--border);border-radius:14px;padding:24px;background:var(--surface)}}
.cta h3{{font-size:18px;font-weight:800;margin-bottom:6px}}.cta p{{font-size:14px;color:var(--muted);margin-bottom:14px}}
.btn{{display:inline-block;background:var(--accent);color:#fff;font-weight:700;font-size:14px;padding:11px 22px;border-radius:8px}}
footer{{display:flex;flex-direction:column;gap:12px;padding:26px 32px;border-top:1px solid var(--border);font-size:12px;color:var(--muted);margin-top:40px}}
.footer-logo{{font-weight:800;font-size:13px}}.footer-links{{display:flex;gap:16px;flex-wrap:wrap}}
.mnav-burger{{display:none;flex-direction:column;justify-content:center;gap:5px;width:44px;height:44px;background:rgba(19,19,26,.72);border:1px solid var(--border);border-radius:11px;cursor:pointer;padding:0 11px}}
.mnav-burger span{{display:block;height:2px;width:22px;background:var(--text);border-radius:2px}}
@media(max-width:640px){{.page{{padding:24px 16px 64px}}header,nav{{padding-left:16px;padding-right:16px}}
.mnav-burger{{display:flex;position:fixed;top:9px;right:14px;z-index:300}}
nav.js-primnav{{position:fixed!important;inset:0!important;height:100dvh!important;width:100%!important;flex-direction:column!important;justify-content:center!important;align-items:center!important;gap:4px!important;background:rgba(10,10,15,.98)!important;transform:translateX(100%);transition:transform .34s;z-index:290!important;border:0!important}}
body.mnav-open nav.js-primnav{{transform:translateX(0)!important}}
nav.js-primnav a{{font-size:22px!important;font-weight:700!important;padding:14px 30px!important;height:auto!important}}}}</style>
  <link rel="stylesheet" href="/assets/poppy.css">
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"CollectionPage","name":"Indian music festivals & tours","url":"https://indiemusicindia.com/live/","description":"Live dates, venues and tickets for music festivals and artist tours across India.","isPartOf":{{"@type":"WebSite","name":"Indie Music India","url":"https://indiemusicindia.com/"}}}}</script>
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"ItemList","name":"Upcoming music events in India","numberOfItems":{n_events},"itemListElement":[{schema}]}}</script>
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Home","item":"https://indiemusicindia.com/"}},{{"@type":"ListItem","position":2,"name":"Live","item":"https://indiemusicindia.com/live/"}}]}}</script>
</head>
<body>
<button class="mnav-burger" aria-label="Menu" aria-expanded="false" onclick="var o=document.body.classList.toggle('mnav-open');this.setAttribute('aria-expanded',o)"><span></span><span></span><span></span></button>
<header><div class="logo"><a href="/">◉ Indie Music India</a><span style="display:block;font-weight:400;font-size:11px;letter-spacing:0;color:var(--muted);margin-top:2px;">Free tools &amp; data for India's independent music scene</span></div></header>
<nav class="js-primnav">
  <a class="tab" href="/">Home</a>
  <a class="tab" href="/programme/">Programme</a>
  <a class="tab" href="/about/">About</a>
  <a class="tab" href="/radar.html">Radar</a>
  <a class="tab" href="/live/">Live</a>
  <a class="tab" href="/venues/">Venues</a>
  <a class="tab" href="/news/">News</a>
  <a class="tab" href="/reviewers/">Reviewers</a>
  <a class="tab" href="/industry/">Industry</a>
  <a class="tab" href="/resources/">Resources</a>
  <a class="tab" href="/tools/royalty-calculator/">Calculator</a>
</nav>
<div class="page">
  <div class="crumb"><a href="/">Home</a> / Live</div>
  <div class="eyebrow">Festivals &amp; tours</div>
  <h1>Live music across India</h1>
  <p class="lead">Every festival and tour worth knowing about, in one place: dates, cities, venues and ticket links, from India's marquee festivals to the international acts touring here. Deduped from the ticketing platforms and updated daily.</p>
  <div class="stat">{c.get("festivals",0)} festivals · {c.get("tours",0)} tours · {c.get("international",0)} international acts · updated {updated}</div>

  <h2 class="sec">Festivals</h2>
  <div class="seclead">India's marquee festivals plus every festival with confirmed dates.</div>
{fest_html}

  <h2 class="sec">Tours &amp; concerts</h2>
  <div class="seclead">Artist tours and one-off concerts, soonest first. Multi-city tours are grouped.</div>
{tour_html}

  <div class="cta">
    <h3>Playing one of these? Or want to be?</h3>
    <p>We help independent Indian artists get heard, get paid and get on stage. The Radar tracks who's rising, and the programme is hands-on.</p>
    <a class="btn" href="/programme/">See how the programme works →</a>
  </div>
</div>
<footer>
  <div class="footer-logo">◉ Indie Music India</div>
  <div class="footer-links">
    <a href="/">Home</a><a href="/live/">Live</a><a href="/news/">News</a><a href="/radar.html">Radar</a>
    <a href="/reviewers/">Reviewers</a><a href="/industry/">Industry</a>
    <a href="https://instagram.com/indiemusicindia.co" target="_blank" rel="noopener">Instagram</a>
  </div>
  <div>Dates aggregated from public ticketing listings (District, BookMyShow, Skillboxes and more) and official festival sources. Always confirm on the official page before booking. Built by Siby John and Karishma Changroth.</div>
</footer>
<script>document.addEventListener('click',function(e){{var a=e.target.closest('nav.js-primnav a');if(a)document.body.classList.remove('mnav-open');}});document.addEventListener('keydown',function(e){{if(e.key==='Escape')document.body.classList.remove('mnav-open');}});</script>
</body>
</html>'''
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page)
    print(f"generate_festivals_page: wrote {OUT} ({len(festivals)} festivals, {len(tours)} tours, {n_events} schema events)")

if __name__ == "__main__":
    build()
