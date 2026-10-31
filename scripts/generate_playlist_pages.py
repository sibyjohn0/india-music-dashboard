#!/usr/bin/env python3
"""Generate /playlists/ (hub) + /playlists/<language>/ pages from
data/playlist_insights.json.

Server-rendered on purpose, not client-fetched: the whole reason this exists
alongside /reviewers/ is that client-rendered curator data gives Google
nothing to put in a search snippet. Real counts, real names and real
per-language text are baked into the HTML at build time here, same fix as
the /reviewers/ genre-summary section. Runs daily in the pipeline, right
after fetch_playlist_insights.py.
"""
import json, html, re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "data" / "playlist_insights.json"
PDIR = REPO / "playlists"

def esc(s): return html.escape(str(s or ""), quote=True)

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

LANGUAGES = ["Hindi", "Punjabi", "Tamil", "Telugu", "Kannada", "Malayalam",
             "Bengali", "Marathi", "Gujarati", "Urdu", "Assamese", "Odia", "Konkani"]

# Genre/mood tags, derived from each playlist's own name + description text
# (no extra API calls -- this is why the scraper stores the full description).
# The real value-add here isn't the list, it's letting an artist search
# "Punjabi love" or "Tamil rap" and land on the right playlist, not just
# browse by language.
MOOD_GENRE_KEYWORDS = {
    "love":      ["love", "romantic", "romance", "pyaar", "ishq"],
    "breakup":   ["breakup", "break up", "sad", "heartbreak", "dukh"],
    "party":     ["party", "dance", "club", "edm", "dj"],
    "chill":     ["chill", "lofi", "lo-fi", "relax", "calm"],
    "workout":   ["workout", "gym", "pump", "running"],
    "rap":       ["rap", "hip hop", "hip-hop", "hiphop", "desi hip hop"],
    "rnb":       ["r&b", "rnb", "r and b", "soul"],
    "rock":      ["rock", "alternative", "alt-rock", "grunge"],
    "pop":       ["pop", "indie pop"],
    "folk":      ["folk", "acoustic", "singer-songwriter", "singer songwriter"],
    "wedding":   ["wedding", "sangeet", "shaadi"],
    "roadtrip":  ["road trip", "roadtrip", "travel", "drive", "safar"],
    "devotional":["devotional", "bhakti", "sufi", "qawwali"],
    "study":     ["study", "focus", "instrumental", "ambient"],
    "bedroom":   ["bedroom pop", "bedroom"],
}

def tag_mood_genre(name, description):
    text = f"{name} {description}".lower()
    return [tag for tag, keys in MOOD_GENRE_KEYWORDS.items() if any(k in text for k in keys)]

# Cycle through the poppy palette's named tokens -- these are already defined
# in assets/poppy.css, not new colours, just assigning one per language so
# the grid reads as distinct places, not a name-swapped list.
LANG_COLOR = {
    "Hindi": ("--pink", "--pink-s"), "Punjabi": ("--orange", "--orange-s"),
    "Tamil": ("--blue", "--blue-s"), "Telugu": ("--mint", "--mint-s"),
    "Kannada": ("--violet", "--violet-s"), "Malayalam": ("--yellow", "--yellow-s"),
    "Bengali": ("--pink", "--pink-s"), "Marathi": ("--orange", "--orange-s"),
    "Gujarati": ("--blue", "--blue-s"), "Urdu": ("--mint", "--mint-s"),
    "Assamese": ("--violet", "--violet-s"), "Odia": ("--yellow", "--yellow-s"),
    "Konkani": ("--pink", "--pink-s"),
}

def fmt_date(iso):
    try:
        return iso[:10]
    except Exception:
        return ""

def fmt_followers(n):
    if not n:
        return None
    if n >= 1000:
        return f"{n/1000:.1f}k".replace(".0k", "k")
    return str(n)

STYLE = '''
.ppage{max-width:980px;margin:0 auto;padding:40px 24px 90px;position:relative;z-index:1}
.peyebrow{font-family:var(--font-m);font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--pink)}
.ptitle{font-family:var(--font-d);font-size:clamp(28px,5vw,46px);font-weight:800;letter-spacing:-1px;line-height:1.08;margin:10px 0 0;color:var(--ink)}
.plead{font-size:16px;color:var(--muted);max-width:620px;margin-top:14px;line-height:1.7}
.pstats{display:flex;gap:28px;flex-wrap:wrap;margin:22px 0 6px}
.pstat b{font-family:var(--font-d);font-size:26px;font-weight:800;color:var(--ink);display:block}
.pstat span{font-size:12px;color:var(--muted);font-weight:600}
.psec-title{font-family:var(--font-d);font-size:20px;font-weight:800;color:var(--ink);margin:40px 0 4px}
.psec-sub{font-size:13px;color:var(--muted);margin-bottom:16px}
.pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px}
.pcard{background:#fff;border:2px solid var(--ink);border-radius:12px;padding:16px;box-shadow:3px 3px 0 var(--ink);text-decoration:none;display:block;transition:transform .12s}
.pcard:hover{transform:translate(-2px,-2px);box-shadow:5px 5px 0 var(--ink)}
.pcard-top{height:5px;border-radius:3px;margin:-16px -16px 12px}
.pcard h3{font-family:var(--font-d);font-size:17px;font-weight:800;color:var(--ink);line-height:1.25}
.pcard p{font-size:12.5px;color:var(--muted);margin-top:4px}
.pcard .go{font-size:12px;font-weight:700;color:var(--pink);margin-top:10px;display:inline-block}
.plist{display:flex;flex-direction:column;gap:10px}
.prow{background:#fff;border:2px solid var(--ink);border-radius:12px;padding:16px 18px;display:flex;justify-content:space-between;align-items:flex-start;gap:14px;box-shadow:3px 3px 0 var(--ink)}
.prow h3{font-family:var(--font-d);font-size:16px;font-weight:800;color:var(--ink);line-height:1.3}
.prow .by{font-size:12.5px;color:var(--muted);margin-top:3px}
.prow .by a{color:var(--pink);font-weight:700;text-decoration:none}
.prow .tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.ptag{font-family:var(--font-m);font-size:10px;font-weight:700;letter-spacing:.3px;text-transform:uppercase;padding:3px 8px;border-radius:20px;background:var(--cream);border:1px solid var(--ink)}
.ptag.active{background:var(--mint-s);color:#0a5c48}
.ptag.mood{background:var(--violet-s);border-color:var(--violet)}
.psearch{background:#fff;border:2px solid var(--ink);border-radius:14px;padding:20px;box-shadow:4px 4px 0 var(--ink);margin:22px 0 40px}
.psearch-input{width:100%;font-family:'Inter',sans-serif;font-size:16px;padding:12px 16px;border:2px solid var(--ink);border-radius:10px;outline:none}
.psearch-input:focus{border-color:var(--pink)}
.psearch-row{display:flex;gap:6px;flex-wrap:wrap;margin-top:14px}
.psearch-label{font-family:var(--font-m);font-size:10px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:var(--muted);width:100%;margin-bottom:2px}
.pfilter-pill{font-size:12.5px;font-weight:600;color:var(--ink);background:var(--cream);border:1.5px solid var(--ink);border-radius:20px;padding:6px 12px;cursor:pointer;user-select:none}
.pfilter-pill.on{background:var(--pink);color:#fff;border-color:var(--pink)}
.psearch-results{margin-top:18px;display:flex;flex-direction:column;gap:10px}
.psearch-empty{font-size:13px;color:var(--muted);padding:12px 0}
.psearch-count{font-size:12.5px;color:var(--muted);margin-top:4px}
.pright{flex-shrink:0;text-align:right}
.pfollow{font-family:var(--font-d);font-size:18px;font-weight:800;color:var(--ink)}
.pfollow span{display:block;font-size:10px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.4px}
.pcontact{font-size:11px;color:#0a5c48;font-weight:700;margin-top:6px}
.pfaq h3{font-family:var(--font-d);font-size:15px;font-weight:800;color:var(--ink);margin:18px 0 4px}
.pfaq p{font-size:14px;color:var(--muted);line-height:1.7}
.plangnav{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}
.plangnav a{font-size:12.5px;font-weight:700;color:var(--ink);background:#fff;border:1.5px solid var(--ink);border-radius:20px;padding:6px 13px;text-decoration:none}
.plangnav a.cur{background:var(--pink);color:#fff;border-color:var(--pink)}
.pcrumb{font-size:12px;color:var(--muted)}.pcrumb a{color:var(--muted)}
@media(max-width:640px){.prow{flex-direction:column}.pright{text-align:left}}
'''

HEAD_EXTRA = f'<style>{STYLE}</style>'

NAV_HTML = '''<nav class="js-primnav">
  <a class="tab" href="/">Home</a>
  <a class="tab" href="/programme/">Programme</a>
  <a class="tab" href="/about/">About</a>
  <a class="tab" href="/radar.html">Radar</a>
  <a class="tab" href="/artists/">Featured Artists</a>
  <a class="tab" href="/live/">Live</a>
  <a class="tab" href="/venues/">Venues</a>
  <a class="tab" href="/reviewers/">Reviewers</a>
  <a class="tab active" href="/playlists/">Playlists</a>
  <a class="tab" href="/industry/">Industry</a>
  <a class="tab" href="/news/">News</a>
  <a class="tab" href="/tools/royalty-calculator/">Calculator</a>
</nav>'''

HEADER_HTML = '''<header><div class="logo"><a href="/">&#9673; Indie Music India</a><span style="display:block;font-weight:400;font-size:11px;letter-spacing:0;color:var(--muted);margin-top:2px;">Free tools &amp; data for India's independent music scene</span></div></header>'''

BURGER_HTML = '''<button class="mnav-burger" aria-label="Menu" aria-expanded="false" onclick="var o=document.body.classList.toggle('mnav-open');this.setAttribute('aria-expanded',o)"><span></span><span></span><span></span></button>'''

BASE_STYLE = '''*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',-apple-system,sans-serif;line-height:1.6}
a{color:inherit}
header{display:flex;align-items:center;padding:0 32px;height:52px;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100;background:rgba(255,247,238,.92);backdrop-filter:blur(8px)}
.logo{font-size:15px;font-weight:700;color:var(--ink)}
nav{display:flex;padding:0 24px;border-bottom:1px solid var(--border);overflow-x:auto;scrollbar-width:none}
nav::-webkit-scrollbar{display:none}
.tab{color:var(--muted);font:13px/1 'Inter',sans-serif;padding:0 16px;height:44px;display:flex;align-items:center;white-space:nowrap;flex-shrink:0;font-weight:500;text-decoration:none;border-bottom:2px solid transparent}
.tab.active{color:var(--ink);border-bottom-color:var(--pink);font-weight:700}
footer{display:flex;flex-direction:column;gap:12px;padding:26px 32px;border-top:1px solid var(--border);font-size:12px;color:var(--muted);margin-top:40px;position:relative;z-index:1}
.footer-logo{font-weight:800;font-size:13px;color:var(--ink)}
.footer-links{display:flex;gap:16px;flex-wrap:wrap}
.footer-links a{color:var(--muted);text-decoration:none}
.mnav-burger{display:none;flex-direction:column;justify-content:center;gap:5px;width:44px;height:44px;background:rgba(19,19,26,.72);border:1px solid var(--ink);border-radius:11px;cursor:pointer;padding:0 11px}
.mnav-burger span{display:block;height:2px;width:22px;background:#fff;border-radius:2px}
@media(max-width:640px){header,nav{padding-left:16px;padding-right:16px}
.mnav-burger{display:flex;position:fixed;top:9px;right:14px;z-index:300}
nav.js-primnav{position:fixed!important;inset:0!important;height:100dvh!important;width:100%!important;flex-direction:column!important;justify-content:center!important;align-items:center!important;gap:4px!important;background:rgba(36,27,46,.98)!important;transform:translateX(100%);transition:transform .34s;z-index:290!important;border:0!important}
body.mnav-open nav.js-primnav{transform:translateX(0)!important}
nav.js-primnav a{color:#fff!important;font-size:22px!important;font-weight:700!important;padding:14px 30px!important;height:auto!important;border:0!important}}'''

SCRIPTJS = '''<script>document.addEventListener('click',function(e){var a=e.target.closest('nav.js-primnav a');if(a)document.body.classList.remove('mnav-open');});document.addEventListener('keydown',function(e){if(e.key==='Escape')document.body.classList.remove('mnav-open');});</script>'''

def head(title, desc, canonical, extra_ld=""):
    return f'''<!DOCTYPE html>
<html lang="en-IN">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-R7EYMGZEJZ"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-R7EYMGZEJZ');</script>
  <meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}" />
  <link rel="canonical" href="{esc(canonical)}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(desc)}" />
  <meta property="og:url" content="{esc(canonical)}" />
  <meta property="og:type" content="website" />
  <meta property="og:image" content="https://indiemusicindia.com/og-image.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <style>{BASE_STYLE}</style>
  <link rel="stylesheet" href="/assets/poppy.css?v=20261001">
  {HEAD_EXTRA}
  {extra_ld}
</head>
<body>
{BURGER_HTML}
{HEADER_HTML}
{NAV_HTML}'''

FOOT = '''<footer>
  <div class="footer-logo">&#9673; Indie Music India</div>
  <div class="footer-links">
    <a href="/">Home</a><a href="/reviewers/">Reviewers</a><a href="/playlists/">Playlists</a><a href="/venues/">Venues</a><a href="/industry/">Industry</a>
    <a href="https://instagram.com/indiemusicindia.co" target="_blank" rel="noopener">Instagram</a>
  </div>
  <div>Playlist data discovered via Spotify search, updated daily. Follower counts and activity are what Spotify reports publicly; we do not run or guarantee placement on any playlist.</div>
</footer>
''' + SCRIPTJS + '''
<script src="/assets/analytics.js" defer></script>
<script src="/assets/nav.js?v=20261030" defer></script>
<script src="/assets/player.js?v=20261026" defer></script>
</body>
</html>'''


def curator_card(c):
    langs = ", ".join(c["languages"]) if c["languages"] else "Mixed"
    followers = fmt_followers(c.get("total_followers"))
    f_html = f'<p>{followers} combined followers</p>' if followers else ""
    return f'''  <a class="pcard" href="{esc(c["owner_url"] or "#")}" target="_blank" rel="noopener">
    <div class="pcard-top" style="background:var(--pink)"></div>
    <h3>{esc(c["owner_name"] or "Unnamed curator")}</h3>
    <p>{c["playlist_count"]} playlists &middot; {esc(langs)}</p>
    {f_html}
    <span class="go">Open on Spotify &rarr;</span>
  </a>'''


def playlist_row(p, recent_cutoff=None):
    followers = fmt_followers(p.get("followers"))
    f_html = f'<div class="pfollow">{followers}<span>Followers</span></div>' if followers else ""
    active = ""
    if recent_cutoff and p["last_changed_at"] >= recent_cutoff:
        active = '<span class="ptag active">Recently active</span>'
    tags = active + "".join(f'<span class="ptag">{esc(l)}</span>' for l in p["languages"][:3])
    tags += "".join(f'<span class="ptag mood">{esc(m)}</span>' for m in p.get("mg_tags", [])[:3])
    contact_html = ""
    if p.get("contact"):
        c = p["contact"]
        bits = []
        if c.get("email"):
            bits.append(c["email"])
        if c.get("phone"):
            bits.append(("WhatsApp " if c.get("whatsapp_mentioned") else "") + c["phone"])
        if bits:
            contact_html = f'<div class="pcontact">Contact in description: {esc(" / ".join(bits))}</div>'
    owner = f'<a href="{esc(p["owner_url"])}" target="_blank" rel="noopener">{esc(p["owner_name"] or "Unknown")}</a>' if p.get("owner_url") else esc(p.get("owner_name") or "Unknown")
    return f'''  <div class="prow">
    <div>
      <h3><a href="{esc(p["url"])}" target="_blank" rel="noopener" style="color:inherit;text-decoration:none">{esc(p["name"])}</a></h3>
      <div class="by">Run by {owner}</div>
      <div class="tags">{tags}</div>
      {contact_html}
    </div>
    <div class="pright">{f_html}</div>
  </div>'''


MIN_FOLLOWERS = 1000  # below this isn't a real enough audience to be worth an artist's pitch

def build():
    data = json.loads(SRC.read_text())
    all_playlists = data["playlists"]
    updated = fmt_date(data.get("generated_at", ""))

    # Quality floor: a playlist with a handful of followers isn't a
    # meaningful pitch target. Filtered here (not in the scraper) so the
    # threshold stays adjustable without re-scraping, and recomputed from
    # scratch below rather than trusting the scraper's own curator rollup,
    # since that was built from the full unfiltered set.
    playlists = [p for p in all_playlists if (p.get("followers") or 0) >= MIN_FOLLOWERS]
    playlists.sort(key=lambda p: (p.get("followers") or 0), reverse=True)
    dropped = len(all_playlists) - len(playlists)
    print(f"  Follower filter: kept {len(playlists)}/{len(all_playlists)} playlists (dropped {dropped} under {MIN_FOLLOWERS} followers)")

    for p in playlists:
        p["mg_tags"] = tag_mood_genre(p.get("name"), p.get("description"))

    curators = {}
    for p in playlists:
        oid = p.get("owner_id")
        if not oid:
            continue
        c = curators.setdefault(oid, {
            "owner_id": oid, "owner_name": p["owner_name"], "owner_url": p["owner_url"],
            "playlist_ids": [], "languages": set(), "contact": None, "total_followers": 0,
        })
        c["playlist_ids"].append(p["id"])
        c["languages"].update(p["languages"])
        c["total_followers"] += p.get("followers") or 0
        if not c["contact"] and p.get("contact"):
            c["contact"] = p["contact"]
    curators = list(curators.values())
    for c in curators:
        c["languages"] = sorted(c["languages"])
        c["playlist_count"] = len(c["playlist_ids"])
    curators.sort(key=lambda c: (-c["playlist_count"], -c["total_followers"]))

    # top-N most-recently-changed snapshot_id = our honest "active now" signal,
    # drawn only from playlists that already cleared the follower floor
    by_recent = sorted(playlists, key=lambda p: p["last_changed_at"], reverse=True)
    recent_cutoff = by_recent[min(24, len(by_recent) - 1)]["last_changed_at"] if by_recent else None

    lang_counts = {}
    for p in playlists:
        for l in p["languages"]:
            lang_counts[l] = lang_counts.get(l, 0) + 1

    # Separately, how many were ever discovered for this language before the
    # follower filter -- used to tell "we found some, none cleared the bar
    # yet" apart from "we've genuinely found nothing here", and to keep
    # already-indexed language pages alive with an honest explanation rather
    # than silently 404ing a URL we already submitted to search engines.
    lang_counts_all = {}
    for p in all_playlists:
        for l in p["languages"]:
            lang_counts_all[l] = lang_counts_all.get(l, 0) + 1

    mood_counts = {}
    for p in playlists:
        for m in p["mg_tags"]:
            mood_counts[m] = mood_counts.get(m, 0) + 1

    multi_curators = [c for c in curators if c["playlist_count"] >= 2][:12]

    # ---------------- HUB: /playlists/ ----------------
    lang_cards = "\n".join(
        f'''  <a class="pcard" href="/playlists/{slugify(lang)}/">
    <div class="pcard-top" style="background:var({LANG_COLOR[lang][0]})"></div>
    <h3>{esc(lang)}</h3>
    <p>{lang_counts.get(lang, 0)} playlists found</p>
    <span class="go">See them &rarr;</span>
  </a>''' for lang in LANGUAGES if lang_counts.get(lang, 0) > 0
    )
    recent_rows = "\n".join(playlist_row(p, recent_cutoff) for p in by_recent[:10])
    curator_cards = "\n".join(curator_card(c) for c in multi_curators)

    hub_ld = (
        '<script type="application/ld+json">{"@context":"https://schema.org","@type":"CollectionPage",'
        '"name":"India indie playlist insights","url":"https://indiemusicindia.com/playlists/",'
        '"isPartOf":{"@type":"WebSite","name":"Indie Music India","url":"https://indiemusicindia.com/"}}</script>\n'
        '  <script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":'
        '[{"@type":"ListItem","position":1,"name":"Home","item":"https://indiemusicindia.com/"},'
        '{"@type":"ListItem","position":2,"name":"Playlists","item":"https://indiemusicindia.com/playlists/"}]}</script>\n'
        '  <script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage","mainEntity":['
        '{"@type":"Question","name":"How do I get my song added to an Indian indie Spotify playlist?","acceptedAnswer":'
        '{"@type":"Answer","text":"Find a playlist in your language and genre below, check its description or the curator\'s Spotify profile for a contact, and pitch directly. Most independent curators respond to a short, genuine message more than a form submission."}},'
        '{"@type":"Question","name":"Are these official Spotify playlists?","acceptedAnswer":'
        '{"@type":"Answer","text":"No. These are independently run playlists discovered via Spotify search, built by real people and small teams, not Spotify\'s own editorial playlists or a paid placement service."}},'
        '{"@type":"Question","name":"How often is this list updated?","acceptedAnswer":'
        '{"@type":"Answer","text":"Daily. We track each playlist\'s Spotify snapshot ID, so playlists marked Recently active were genuinely edited since our last check, not just re-listed."}}]}</script>'
    )

    hub = head(
        "India Indie Playlist Insights: Real Curators, Updated Daily",
        f"{len(playlists)} independently run Spotify playlists for Indian indie music across {len([l for l in LANGUAGES if lang_counts.get(l,0)>0])} languages, with real curators and activity tracked daily. Free to browse.",
        "https://indiemusicindia.com/playlists/", hub_ld,
    )
    hub += f'''
<div class="ppage">
  <div class="pcrumb"><a href="/">Home</a> / Playlists</div>
  <div class="peyebrow">Playlist Insights</div>
  <h1 class="ptitle">Spotify playlists built by real people, not aggregators</h1>
  <p class="plead">{len(playlists)} independently run playlists for Indian indie music, discovered by searching Spotify directly, not bought from a submission service. Updated daily, so "Recently active" actually means something.</p>
  <div class="pstats">
    <div class="pstat"><b>{len(playlists)}</b><span>Playlists</span></div>
    <div class="pstat"><b>{len(curators)}</b><span>Curators</span></div>
    <div class="pstat"><b>{len([l for l in LANGUAGES if lang_counts.get(l,0)>0])}</b><span>Languages</span></div>
    <div class="pstat"><b>{len(multi_curators)}</b><span>Running 2+ playlists</span></div>
  </div>

  <div class="psearch">
    <h2 class="psec-title" style="margin-top:0">Find your playlist</h2>
    <p class="psec-sub">Search by language, mood or genre, Punjabi love, Tamil rap, Malayalam R&amp;B, whatever fits your sound.</p>
    <input class="psearch-input" id="pq" type="text" placeholder="Try &quot;punjabi love&quot; or &quot;tamil rap&quot;..." autocomplete="off">
    <div class="psearch-row" id="plang-pills">
      <div class="psearch-label">Language</div>
{"".join(f'      <span class="pfilter-pill" data-lang="{esc(l)}">{esc(l)}</span>' + chr(10) for l in LANGUAGES if lang_counts.get(l,0)>0)}    </div>
    <div class="psearch-row" id="pmood-pills">
      <div class="psearch-label">Mood / genre</div>
{"".join(f'      <span class="pfilter-pill" data-mood="{esc(m)}">{esc(m)}</span>' + chr(10) for m in sorted(mood_counts, key=lambda m: -mood_counts[m]) if mood_counts.get(m,0)>0)}    </div>
    <div class="psearch-count" id="presults-count"></div>
    <div class="psearch-results" id="presults"></div>
  </div>
  <script id="pdata" type="application/json">{json.dumps([{
      "n": p["name"], "u": p["url"], "o": p["owner_name"], "ou": p["owner_url"],
      "l": p["languages"], "m": p["mg_tags"], "f": p.get("followers") or 0,
    } for p in playlists], ensure_ascii=False, separators=(",", ":"))}</script>
  <script>
  (function(){{
    var ALL = JSON.parse(document.getElementById('pdata').textContent);
    var activeLang = null, activeMood = null;
    var q = document.getElementById('pq');
    var results = document.getElementById('presults');
    var count = document.getElementById('presults-count');
    function fmtF(n){{ if(!n) return ''; return n>=1000 ? (n/1000).toFixed(1).replace('.0','')+'k' : String(n); }}
    function render(){{
      var text = q.value.trim().toLowerCase();
      var terms = text.split(/\\s+/).filter(Boolean);
      var matches = ALL.filter(function(p){{
        if(activeLang && p.l.indexOf(activeLang)===-1) return false;
        if(activeMood && p.m.indexOf(activeMood)===-1) return false;
        if(!terms.length) return true;
        var hay = (p.n+' '+(p.o||'')+' '+p.l.join(' ')+' '+p.m.join(' ')).toLowerCase();
        return terms.every(function(t){{ return hay.indexOf(t)!==-1; }});
      }}).sort(function(a,b){{ return (b.f||0)-(a.f||0); }});
      if(!text && !activeLang && !activeMood){{ results.innerHTML=''; count.textContent=''; return; }}
      count.textContent = matches.length + (matches.length===1 ? ' playlist found' : ' playlists found');
      if(!matches.length){{ results.innerHTML = '<div class="psearch-empty">No match yet, try fewer words or a different mood.</div>'; return; }}
      results.innerHTML = matches.slice(0,30).map(function(p){{
        var tags = (p.l.slice(0,2).concat(p.m.slice(0,2))).map(function(t){{return '<span class="ptag">'+t+'</span>';}}).join('');
        var fol = fmtF(p.f) ? '<div class="pright"><div class="pfollow">'+fmtF(p.f)+'<span>Followers</span></div></div>' : '';
        return '<div class="prow"><div><h3><a href="'+p.u+'" target="_blank" rel="noopener" style="color:inherit;text-decoration:none">'+p.n+'</a></h3>'+
          '<div class="by">Run by '+(p.ou ? '<a href="'+p.ou+'" target="_blank" rel="noopener">'+(p.o||'Unknown')+'</a>' : (p.o||'Unknown'))+'</div>'+
          '<div class="tags">'+tags+'</div></div>'+fol+'</div>';
      }}).join('');
    }}
    q.addEventListener('input', render);
    document.querySelectorAll('.pfilter-pill[data-lang]').forEach(function(el){{
      el.addEventListener('click', function(){{
        var v = el.getAttribute('data-lang');
        activeLang = (activeLang===v) ? null : v;
        document.querySelectorAll('[data-lang]').forEach(function(e){{ e.classList.toggle('on', e.getAttribute('data-lang')===activeLang); }});
        render();
      }});
    }});
    document.querySelectorAll('.pfilter-pill[data-mood]').forEach(function(el){{
      el.addEventListener('click', function(){{
        var v = el.getAttribute('data-mood');
        activeMood = (activeMood===v) ? null : v;
        document.querySelectorAll('[data-mood]').forEach(function(e){{ e.classList.toggle('on', e.getAttribute('data-mood')===activeMood); }});
        render();
      }});
    }});
  }})();
  </script>

  <h2 class="psec-title">Recently active</h2>
  <p class="psec-sub">These playlists were genuinely edited since our last check (tracked via Spotify's own snapshot ID), updated {esc(updated)}.</p>
  <div class="plist">
{recent_rows}
  </div>

  <h2 class="psec-title">Browse by language</h2>
  <p class="psec-sub">Pick a language to see every playlist we've found for it, with curator contact where we could find one.</p>
  <div class="pgrid">
{lang_cards}
  </div>

  <h2 class="psec-title">Curators running multiple playlists</h2>
  <p class="psec-sub">One person or small team behind more than one list, usually the strongest single pitch target.</p>
  <div class="pgrid">
{curator_cards}
  </div>

  <div class="pfaq" style="margin-top:40px">
    <h2 class="psec-title" style="margin-top:0">About this list</h2>
    <h3>How do I get my song added to an Indian indie Spotify playlist?</h3>
    <p>Find a playlist in your language and genre below, check its description or the curator's Spotify profile for a contact, and pitch directly. Most independent curators respond to a short, genuine message more than a form submission.</p>
    <h3>Are these official Spotify playlists?</h3>
    <p>No. These are independently run playlists discovered via Spotify search, built by real people and small teams, not Spotify's own editorial playlists or a paid placement service.</p>
    <h3>How often is this list updated?</h3>
    <p>Daily. We track each playlist's Spotify snapshot ID, so playlists marked Recently active were genuinely edited since our last check, not just re-listed.</p>
  </div>

  <div class="pcta" style="margin-top:40px;padding:24px;border:2px solid var(--ink);border-radius:14px;background:#fff;box-shadow:4px 4px 0 var(--ink)">
    <h3 style="font-family:var(--font-d);font-size:18px;font-weight:800;margin-bottom:6px">Want help getting pitched, not just a list?</h3>
    <p style="font-size:14px;color:var(--muted);margin-bottom:14px">For a few artists at a time: work directly with Siby and Karishma, plus a network of specialists for release strategy, PR, social, video, design, legal and IPRS. One month to start, no commitment beyond that, and no cut of your music.</p>
    <a href="/programme/" style="display:inline-block;background:var(--pink);color:#fff;font-weight:700;font-size:14px;padding:11px 22px;border-radius:8px;text-decoration:none">Get a real team behind your music &rarr;</a>
  </div>
</div>
''' + FOOT
    PDIR.mkdir(parents=True, exist_ok=True)
    (PDIR / "index.html").write_text(hub, encoding="utf-8")

    # ---------------- PER-LANGUAGE: /playlists/<lang>/ ----------------
    for lang in LANGUAGES:
        if lang_counts_all.get(lang, 0) == 0:
            continue  # never found anything here at all, nothing to say
        lang_playlists = [p for p in playlists if lang in p["languages"]]
        lang_playlists.sort(key=lambda p: (p.get("followers") or 0), reverse=True)
        slug = slugify(lang)
        nav_chips = "\n".join(
            f'<a href="/playlists/{slugify(l)}/" class="{"cur" if l==lang else ""}">{esc(l)} ({lang_counts.get(l,0)})</a>'
            for l in LANGUAGES if lang_counts_all.get(l, 0) > 0
        )
        rows = "\n".join(playlist_row(p, recent_cutoff) for p in lang_playlists) if lang_playlists else (
            f'<div class="psearch-empty" style="font-size:14px;line-height:1.7">'
            f'We\'ve found {lang_counts_all.get(lang,0)} {esc(lang)} playlists on Spotify so far, but none have '
            f'cleared our {MIN_FOLLOWERS:,}-follower bar yet, so there is nothing honest to recommend here right now. '
            f'This list is rebuilt daily, so check back, or try the <a href="/playlists/" style="color:var(--pink);font-weight:700">full playlist list</a>.</div>'
        )
        with_contact = sum(1 for p in lang_playlists if p.get("contact"))

        page_ld = (
            '<script type="application/ld+json">{"@context":"https://schema.org","@type":"CollectionPage","name":"'
            f'{esc(lang)} indie Spotify playlists","url":"https://indiemusicindia.com/playlists/{slug}/",'
            '"isPartOf":{"@type":"WebSite","name":"Indie Music India","url":"https://indiemusicindia.com/"}}</script>\n'
            '  <script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":'
            '[{"@type":"ListItem","position":1,"name":"Home","item":"https://indiemusicindia.com/"},'
            '{"@type":"ListItem","position":2,"name":"Playlists","item":"https://indiemusicindia.com/playlists/"},'
            f'{{"@type":"ListItem","position":3,"name":"{esc(lang)}","item":"https://indiemusicindia.com/playlists/{slug}/"}}]}}</script>'
        )

        if lang_playlists:
            title = f"{lang} Indie Spotify Playlists: {len(lang_playlists)} Real Curators to Pitch"
            meta_desc = f"{len(lang_playlists)} independently run {lang} indie Spotify playlists with 1,000+ followers, curator names and contact info where available. Updated daily, free to browse."
            lead = f"{len(lang_playlists)} independently run {esc(lang)} playlists with 1,000+ followers, sorted by followers. {with_contact} have a contact we could find directly in the playlist's own description."
        else:
            title = f"{lang} Indie Spotify Playlists: None Yet Over 1,000 Followers"
            meta_desc = f"We're tracking {lang_counts_all.get(lang,0)} {lang} indie Spotify playlists, but none have cleared our 1,000-follower quality bar yet. Updated daily."
            lead = f"We've found {lang_counts_all.get(lang,0)} {esc(lang)} playlists on Spotify, but none have cleared our 1,000-follower bar yet, so there's nothing honest to list here right now."

        page = head(title, meta_desc, f"https://indiemusicindia.com/playlists/{slug}/", page_ld)
        page += f'''
<div class="ppage">
  <div class="pcrumb"><a href="/">Home</a> / <a href="/playlists/">Playlists</a> / {esc(lang)}</div>
  <div class="peyebrow">Playlist Insights &middot; {esc(lang)}</div>
  <h1 class="ptitle">{esc(lang)} indie playlists you can actually pitch</h1>
  <p class="plead">{lead}</p>
  <div class="plangnav">
{nav_chips}
  </div>
  <div class="plist">
{rows}
  </div>
  <div class="pcta" style="margin-top:40px;padding:24px;border:2px solid var(--ink);border-radius:14px;background:#fff;box-shadow:4px 4px 0 var(--ink)">
    <h3 style="font-family:var(--font-d);font-size:18px;font-weight:800;margin-bottom:6px">Want help getting pitched, not just a list?</h3>
    <p style="font-size:14px;color:var(--muted);margin-bottom:14px">For a few artists at a time: work directly with Siby and Karishma, plus a network of specialists for release strategy, PR, social, video, design, legal and IPRS. One month to start, no commitment beyond that, and no cut of your music.</p>
    <a href="/programme/" style="display:inline-block;background:var(--pink);color:#fff;font-weight:700;font-size:14px;padding:11px 22px;border-radius:8px;text-decoration:none">Get a real team behind your music &rarr;</a>
  </div>
</div>
''' + FOOT
        (PDIR / slug).mkdir(parents=True, exist_ok=True)
        (PDIR / slug / "index.html").write_text(page, encoding="utf-8")

    print(f"generate_playlist_pages: wrote hub + {len([l for l in LANGUAGES if lang_counts.get(l,0)>0])} language pages to {PDIR}")


if __name__ == "__main__":
    build()
