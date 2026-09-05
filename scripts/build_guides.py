#!/usr/bin/env python3
"""build_guides.py — stamp out SEO guide pages from a content spec.

Matches the existing /guides/ template exactly (Article + BreadcrumbList + FAQ
JSON-LD, author E-E-A-T block, nav, poppy.css, analytics.js). One-shot builder
for the long-tail keyword batch. Re-runnable; overwrites its own pages only.
"""
import json, html, os
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
TODAY = "2026-08-31"

def esc(s): return html.escape(str(s), quote=True)

# --- Where to set expectations, and where to stay quiet ----------------------
# Reference pages answer a fact (what an ISRC is, what streaming pays). A reader
# there wants the answer, not a pitch — so they get one honest line, no sales box.
# Every other guide is a decision page (how to promote, become independent, get
# management) where the reader is weighing whether to get help — those carry the
# full, expectation-setting CTA. Same promise everywhere it appears: a few artists
# at a time, founder-led, one month to start, no cut. Consistent, not scattered.
REFERENCE = {
    "isrc-code-india", "register-music-copyright-iprs-india",
    "caller-tune-hello-tune-india", "spotify-pay-per-stream-india",
    "how-much-indian-artists-earn-spotify", "best-music-distributor-india",
    "free-music-distribution-india", "publish-music-in-india",
    "music-platforms-independent-artists-india",
    "independent-music-scene-mumbai", "independent-music-scene-bengaluru",
    "independent-music-scene-delhi",
}

# The one canonical description of what the programme actually is. Mirrors the
# home hero and /programme/ so the promise reads the same wherever it turns up.
CTA_BODY = ("For a few artists at a time: work directly with Siby and Karishma, "
            "plus a network of specialists for release strategy, PR, social, video, "
            "design, legal and IPRS. One month to start, no commitment beyond that, "
            "and no cut of your music.")

def cta_block(g):
    """Decision pages get the full expectation-setting box; reference pages get a
    single honest line so the pitch lands where it matters and nowhere else."""
    if g["slug"] in REFERENCE:
        return ('  <div class="g-softcta">Free to read, no sign-up. When you want a team on '
                'your releases, <a href="/programme/">the programme</a> is founder-led, one '
                'month to start, and never takes a cut of your music.</div>')
    return (f'  <div class="g-cta">\n'
            f'    <h3>{esc(g.get("cta_h","Want a team behind your releases?"))}</h3>\n'
            f'    <p>{CTA_BODY}</p>\n'
            f'    <a class="g-btn" href="/programme/">See how the programme works →</a>\n'
            f'  </div>')

NAV = """<nav class="js-primnav">
  <a class="tab" href="/">Home</a>
  <a class="tab" href="/programme/">Programme</a>
  <a class="tab" href="/about/">About</a>
  <a class="tab" href="/radar.html">Radar</a>
  <a class="tab" href="/live/">Live</a>
  <a class="tab" href="/venues/">Venues</a>
  <a class="tab" href="/news/">News</a>
  <a class="tab" href="/reviewers/">Reviewers</a>
  <a class="tab" href="/industry/">Industry</a>
  <a class="tab" href="/answers/">Answers</a>
</nav>"""

AUTHOR = ('By <a href="/about/" style="color:var(--accent);font-weight:600">Siby John</a>, '
          'thirteen years inside the platforms that decide which music gets seen: Marketing '
          'Manager at YouTube India from 2022 to 2025, working with 400+ artists and labels, '
          'now Senior Creator Manager at LinkedIn. Reviewed 31 August 2026.')

STYLE = open(REPO/"guides/best-music-distributor-india/index.html").read()
STYLE = STYLE[STYLE.index("<style>"):STYLE.index('<link rel="stylesheet" href="/assets/poppy.css">')]

def render_body(sections):
    out = []
    for s in sections:
        out.append(f"<h2>{esc(s['h2'])}</h2>")
        for item in s["body"]:
            if isinstance(item, dict) and "ul" in item:
                out.append("<ul>" + "".join(f"<li>{li}</li>" for li in item["ul"]) + "</ul>")
            else:
                out.append(f"<p>{item}</p>")
    return "\n".join(out)

def render_faq_html(faq):
    rows = []
    for q, a in faq:
        rows.append(f'<h3 style="font-size:17px;font-weight:800;margin:20px 0 6px">{esc(q)}</h3><p>{a}</p>')
    return "\n".join(rows)

def build(g):
    url = f"https://indiemusicindia.com/guides/{g['slug']}/"
    article_ld = {"@context":"https://schema.org","@type":"Article","headline":g["title"],
        "description":g["desc"],"image":"https://indiemusicindia.com/og-image.png",
        "datePublished":TODAY,"dateModified":TODAY,
        "author":{"@type":"Organization","name":"Indie Music India"},
        "publisher":{"@type":"Organization","name":"Indie Music India","logo":{"@type":"ImageObject","url":"https://indiemusicindia.com/og-image.png"}},
        "mainEntityOfPage":url}
    crumb_ld = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"Home","item":"https://indiemusicindia.com/"},
        {"@type":"ListItem","position":2,"name":"Answers","item":"https://indiemusicindia.com/answers/"},
        {"@type":"ListItem","position":3,"name":g["title"],"item":url}]}
    faq_ld = {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a_plain}}
        for (q,_a),(a_plain) in zip(g["faq"], [strip(a) for _q,a in g["faq"]])]}
    page = f"""<!DOCTYPE html>
<html lang="en-IN">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-R7EYMGZEJZ"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-R7EYMGZEJZ');</script>
  <meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(g['title'])}</title>
  <meta name="description" content="{esc(g['desc'])}" />
  <link rel="canonical" href="{url}" />
  <meta property="og:title" content="{esc(g['title'])}" />
  <meta property="og:description" content="{esc(g['desc'])}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:type" content="article" />
  <meta property="og:image" content="https://indiemusicindia.com/og-image.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  {STYLE}
  <style>.g-softcta{{margin-top:38px;font-size:14px;color:var(--muted);line-height:1.65;border-left:3px solid var(--accent);padding:2px 0 2px 15px}}.g-softcta a{{color:var(--accent);font-weight:600}}</style>
  <link rel="stylesheet" href="/assets/poppy.css">
  <script type="application/ld+json">{json.dumps(article_ld)}</script>
  <script type="application/ld+json">{json.dumps(crumb_ld)}</script>
  <script type="application/ld+json">{json.dumps(faq_ld)}</script>
</head>
<body>
<button class="mnav-burger" aria-label="Menu" aria-expanded="false" onclick="var o=document.body.classList.toggle('mnav-open');this.setAttribute('aria-expanded',o)"><span></span><span></span><span></span></button>
<header><div class="logo"><a href="/">◉ Indie Music India</a><span style="display:block;font-weight:400;font-size:11px;letter-spacing:0;color:var(--muted);margin-top:2px;">Free tools &amp; data for India's independent music scene</span></div></header>
{NAV}
<div class="page">
  <div class="crumb"><a href="/">Home</a> › <a href="/answers/">Answers</a> › {esc(g['title'])}</div>
  <div class="g-eyebrow">Guide · {esc(g['cat'])}</div>
  <h1>{esc(g['title'])}</h1>
  <p class="g-lead">{g['lead']}</p>
  <div style="font-size:13px;color:var(--muted);margin-top:14px">{AUTHOR}</div>
  <div class="tldr"><b>Short answer</b><p>{g['tldr']}</p></div>
  <article>
{render_body(g['sections'])}
  </article>
  <section id="related" style="margin-top:36px">
    <h2>People also ask</h2>
{render_faq_html(g['faq'])}
  </section>
{cta_block(g)}
  <div class="g-updated">Last updated {TODAY}. Free to read. Part of <a href="/answers/" style="color:var(--accent)">Answers</a> by Indie Music India.</div>
</div>
<footer>
  <div class="footer-logo">◉ Indie Music India</div>
  <div class="footer-links">
    <a href="/">Home</a><a href="/programme/">Programme</a><a href="/about/">About</a>
    <a href="/radar.html">Radar</a><a href="/live/">Live</a><a href="/venues/">Venues</a>
    <a href="/reviewers/">Reviewers</a><a href="/answers/">Answers</a>
  </div>
  <div>Built by Siby John and Karishma Changroth · Free to use</div>
</footer>
<script>document.addEventListener('click',function(e){{var a=e.target.closest('nav.js-primnav a');if(a)document.body.classList.remove('mnav-open');}});document.addEventListener('keydown',function(e){{if(e.key==='Escape')document.body.classList.remove('mnav-open');}});</script>
  <script src="/assets/analytics.js" defer></script>
  <script src="/assets/nav.js" defer></script>
</body>
</html>"""
    d = REPO/"guides"/g['slug']
    d.mkdir(parents=True, exist_ok=True)
    (d/"index.html").write_text(page)
    return g['slug']

def strip(h):
    import re
    return re.sub(r"<[^>]+>", "", h).replace("&amp;","&").strip()

from guides_content import GUIDES
if __name__ == "__main__":
    for g in GUIDES:
        print("wrote guides/" + build(g) + "/")
