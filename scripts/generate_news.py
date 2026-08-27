#!/usr/bin/env python3
"""Generate the server-rendered /news/ page from data/news-rss.json.

Aggregates the latest from Indian music publications (Wild City, Homegrown,
Rolling Stone India) into a clean "wire" — headline, source, date, summary,
link out. Server-rendered HTML (not client JS) so it is SEO- and AI-citation-
friendly, with ItemList + BreadcrumbList schema. Runs in the daily pipeline.

Light relevance filter drops obvious non-music items (film/awards/obits) that
the broader feeds carry. Never copies full articles — headline + snippet + link
out only.
"""
import json, os, re, html, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "data" / "news-rss.json"
OUT = REPO / "news" / "index.html"

# Drop obvious non-music-scene items the broad feeds carry.
DROP = re.compile(r"\b(oscar|box office|movie|film review|actor|actress|"
                  r"dead at|obituary|passes away|trailer|web series|netflix|"
                  r"bollywood film|hollywood)\b", re.I)

def esc(s): return html.escape(s or "", quote=True)

def load():
    try:
        d = json.load(open(SRC))
    except Exception:
        return [], None
    arts = d.get("articles", [])
    arts = [a for a in arts if a.get("title") and a.get("url")
            and not DROP.search(a.get("title", "") + " " + a.get("summary", ""))]
    # newest first
    arts.sort(key=lambda a: a.get("published_at", ""), reverse=True)
    return arts, d.get("fetched_at")

def fmt_date(iso):
    try:
        return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%d %b %Y")
    except Exception:
        return ""

def build():
    arts, fetched = load()
    items_html, schema_items = [], []
    for i, a in enumerate(arts, 1):
        title = esc(a["title"].strip())
        pub = esc(a.get("publication", ""))
        url = esc(a["url"])
        date = fmt_date(a.get("published_at", ""))
        summ = esc((a.get("summary", "") or "")[:180].strip())
        items_html.append(f'''    <a class="news-item" href="{url}" target="_blank" rel="noopener">
      <div class="news-meta">{pub}{" · " + date if date else ""}</div>
      <div class="news-title">{title}</div>
      {f'<div class="news-sum">{summ}…</div>' if summ else ''}
    </a>''')
        schema_items.append(
            f'{{"@type":"ListItem","position":{i},"url":"{url}","name":{json.dumps(a["title"])}}}')
    updated = fmt_date(fetched) if fetched else datetime.date.today().strftime("%d %b %Y")
    items = "\n".join(items_html) if items_html else '<p style="color:var(--muted)">Fresh headlines land here every day.</p>'
    schema = ",".join(schema_items)

    page = f'''<!DOCTYPE html>
<html lang="en-IN">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-R7EYMGZEJZ"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-R7EYMGZEJZ');</script>
  <meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Indian music news: what's moving in the scene — Indie Music India</title>
  <meta name="description" content="The latest Indian music news, aggregated daily from Wild City, Homegrown, Rolling Stone India and more. What's moving in the independent scene, in one place." />
  <link rel="canonical" href="https://indiemusicindia.com/news/" />
  <meta property="og:title" content="Indian music news: what's moving in the scene" />
  <meta property="og:description" content="The latest Indian music news, aggregated daily, in one place." />
  <meta property="og:url" content="https://indiemusicindia.com/news/" />
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
.page{{max-width:720px;margin:0 auto;padding:34px 32px 90px}}
.crumb{{font-size:12px;color:var(--muted);margin-bottom:16px}}
.eyebrow{{font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--accent)}}
h1{{font-size:clamp(26px,4.5vw,38px);font-weight:800;letter-spacing:-1px;line-height:1.14;margin:12px 0 0}}
.lead{{font-size:16px;color:#c6c6d8;margin-top:14px;max-width:600px}}
.updated{{font-size:12px;color:var(--muted);margin-top:10px}}
.wire{{margin-top:26px;display:flex;flex-direction:column;gap:2px}}
.news-item{{display:block;padding:16px 0;border-bottom:1px solid var(--border)}}
.news-item:hover .news-title{{color:var(--accent)}}
.news-meta{{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;color:var(--muted)}}
.news-title{{font-size:18px;font-weight:800;letter-spacing:-.2px;margin:5px 0 4px;line-height:1.3;transition:color .15s}}
.news-sum{{font-size:14px;color:#b6b6c8}}
.cta{{margin-top:36px;border:1px solid var(--border);border-radius:14px;padding:24px;background:var(--surface)}}
.cta h3{{font-size:18px;font-weight:800;margin-bottom:6px}}
.cta p{{font-size:14px;color:var(--muted);margin-bottom:14px}}
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
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"CollectionPage","name":"Indian music news","url":"https://indiemusicindia.com/news/","description":"The latest Indian music news, aggregated daily from Indian music publications.","isPartOf":{{"@type":"WebSite","name":"Indie Music India","url":"https://indiemusicindia.com/"}}}}</script>
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"ItemList","itemListOrder":"https://schema.org/ItemListOrderDescending","numberOfItems":{len(arts)},"itemListElement":[{schema}]}}</script>
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Home","item":"https://indiemusicindia.com/"}},{{"@type":"ListItem","position":2,"name":"News","item":"https://indiemusicindia.com/news/"}}]}}</script>
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
  <a class="tab" href="/news/">News</a>
  <a class="tab" href="/reviewers/">Reviewers</a>
  <a class="tab" href="/industry/">Industry</a>
  <a class="tab" href="/resources/">Resources</a>
  <a class="tab" href="/answers/">Answers</a>
  <a class="tab" href="/tools/royalty-calculator/">Calculator</a>
</nav>
<div class="page">
  <div class="crumb"><a href="/">Home</a> / News</div>
  <div class="eyebrow">On the wire</div>
  <h1>What's moving in Indian music</h1>
  <p class="lead">The latest stories from India's music press, pulled daily and filtered down to what's actually about the scene here, not the global pop feed. Tap any headline to read the full story at the source.</p>
  <div class="updated">Updated {updated}</div>
  <div class="wire">
{items}
  </div>
  <div class="cta">
    <h3>Want to be on our radar?</h3>
    <p>The Radar tracks rising independent Indian artists daily, and we run a hands-on development programme for a few.</p>
    <a class="btn" href="/programme/">See how the programme works →</a>
  </div>
</div>
<footer>
  <div class="footer-logo">◉ Indie Music India</div>
  <div class="footer-links">
    <a href="/">Home</a><a href="/programme/">Programme</a><a href="/radar.html">Radar</a>
    <a href="/reviewers/">Reviewers</a><a href="/industry/">Industry</a><a href="/answers/">Answers</a>
    <a href="https://instagram.com/indiemusicindia.co" target="_blank" rel="noopener">Instagram</a>
  </div>
  <div>News aggregated from public RSS feeds, headlines link to the original source. Built by Siby John and Karishma Changroth.</div>
</footer>
<script>document.addEventListener('click',function(e){{var a=e.target.closest('nav.js-primnav a');if(a)document.body.classList.remove('mnav-open');}});document.addEventListener('keydown',function(e){{if(e.key==='Escape')document.body.classList.remove('mnav-open');}});</script>
</body>
</html>'''
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page)
    print(f"generate_news: wrote {OUT} ({len(arts)} items)")

if __name__ == "__main__":
    build()
