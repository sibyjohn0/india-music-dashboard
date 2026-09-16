#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_toolkit_pages.py — turn the pulled toolkit docs into branded on-site pages.

Reads ~/Downloads/iim_toolkit/manifest.json + <slug>.txt (from fetch_toolkit_docs.py),
parses each doc's plain text into structure (headings/paragraphs/lists), and writes a
branded /toolkit/<slug>/index.html (poppy design, nav.js, schema, responsive). Guides
and checklists get the article/checklist layout; templates/agreements get the content
plus a "Make your own copy" button to the source Doc.

Run: python3 scripts/build_toolkit_pages.py
"""
import json, re, html
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = Path.home()/"Downloads"/"iim_toolkit"
OUT = REPO/"toolkit"

def esc(s): return html.escape(s, quote=False)
def slugify(t): return re.sub(r"[^a-z0-9]+","-",t.lower()).strip("-")[:60]

SMALL = {"a","an","the","and","or","but","of","to","in","on","for","at","by","with","vs","via","from","your","you"}
ACR = {"IPRS","PPL","PRO","PROS","ISRC","UPC","EP","EPS","LP","EPK","EPKS","DSP","DSPS","DIY","UGC","PR",
       "NDA","GST","PAN","TDS","FAQ","FAQS","USP","USPS","CTA","CTAS","KPI","KPIS","ROI","DM","DMS","IG","YT",
       "US","UK","EU","AI","URL","URLS","API","APIS","RSS","CD","CDS","DJ","DJS","MC","TV","FM","AM","B2B",
       "A&R","NOC","TAN","ITR","MRP","OTT","SEO","QR","PDF","CSV","AR","VR","ID","IDS","UPI","NEFT","IMPS","HD","4K","CA","P&L"}

def cap(w):
    for j,ch in enumerate(w):
        if ch.isalpha(): return w[:j]+w[j].upper()+w[j+1:].lower()
    return w

def smart_title(s):
    words=s.split(); out=[]
    for i,w in enumerate(words):
        core=re.sub(r"[^A-Za-z&]","",w)
        if core.upper() in ACR: out.append(w.upper())
        elif core.lower() in SMALL and i!=0: out.append(w.lower())
        else: out.append(cap(w))
    return " ".join(out)

def kind(title):
    t = title.lower()
    if "checklist" in t: return "checklist"
    if any(w in t for w in ["template","agreement","sheet","directory","contract","rider",
                            "itinerary","invoice","one sheet","questionnaire","audit","planner","tracker"]):
        return "template"
    return "guide"

def parse(txt, title):
    lines = txt.replace("﻿","").split("\n")
    blocks=[]; para=[]; ul=[]
    def fp():
        if para: blocks.append(("p"," ".join(para))); para.clear()
    def fu():
        if ul: blocks.append(("ul", ul[:])); ul.clear()
    for raw in lines:
        ln = raw.strip()
        if not ln:
            fp(); fu(); continue
        if len(ln)>3 and set(ln) <= set("━—–-=_·. "):   # divider line
            fp(); fu(); continue
        if "Artist Management Toolkit" in ln and "|" in ln:  # doc boilerplate subtitle
            continue
        letters=[c for c in ln if c.isalpha()]
        is_head = letters and sum(c.isupper() for c in letters)/len(letters) > 0.85 and len(ln) < 70
        if is_head:
            h = ln.strip(":")
            if h.upper() == title.upper():   # doc's own title repeated inside body -> drop it
                fp(); fu(); continue
            fp(); fu(); blocks.append(("h2", smart_title(h) if h.isupper() else h)); continue
        if ln[0] in "•-*▪◦" or ln.startswith("☐") or ln[:3] in ("[ ]","[]"):
            fp(); ul.append(re.sub(r"^[•\-*▪◦☐\[\]\s]+","",ln)); continue
        fu(); para.append(ln)
    fp(); fu()
    # drop a leading heading that just repeats the title
    if blocks and blocks[0][0]=="h2" and blocks[0][1].lower().strip()==title.lower().strip():
        blocks=blocks[1:]
    return blocks

def render_blocks(blocks, as_checklist):
    out=[]
    for typ, val in blocks:
        if typ=="h2":
            out.append(f'      <h2>{esc(val)}</h2>')
        elif typ=="p":
            if len(val)<80 and val.endswith(":"):   # a field/label line
                out.append(f'      <p><b>{esc(val)}</b></p>')
            else:
                out.append(f'      <p>{esc(val)}</p>')
        elif typ=="ul":
            if as_checklist:
                items="".join(f'<li><span class="box">✓</span><span class="txt">{esc(x)}</span></li>' for x in val)
                out.append(f'      <ul class="ck">{items}</ul>')
            else:
                items="".join(f'<li>{esc(x)}</li>' for x in val)
                out.append(f'      <ul>{items}</ul>')
    return "\n".join(out)

HEAD_CSS = open(REPO/"toolkit"/"new-release-checklist"/"index.html").read()
# pull the two <style> blocks + poppy link from the proof page to stay identical
STYLE = re.search(r'(<style>.*?</style>\s*<style id="mnav-css">.*?</style>)', HEAD_CSS, re.S).group(1)
POPPY = '<link rel="stylesheet" href="/assets/poppy.css">'

def page(doc):
    title=html.unescape(doc["title"]); did=doc["id"]; k=kind(title)
    slug=slugify(title)                        # clean URL slug (from unescaped title)
    txt=(SRC/f"{doc['slug']}.txt").read_text(encoding="utf-8", errors="ignore")  # file uses original slug
    blocks=parse(txt, title)
    if k=="template":
        # template docs are table-based fill-in forms; the text export collapses tables into
        # run-on walls. Show a clean intro + "what's inside" section list, drive to the copy button.
        intro=[]; sections=[]
        for typ,val in blocks:
            if typ=="h2": sections.append(val)
            elif typ=="p" and not sections and len(intro)<2 and len(val)>25: intro.append(val)
        body="\n".join(f'      <p>{esc(x)}</p>' for x in intro)
        sections=[s for s in sections if "₹" not in s and "_" not in s]  # drop field/total rows
        if sections:
            lis="".join(f'<li>{esc(s)}</li>' for s in sections)
            body+=f'\n      <h2>What\'s inside this template</h2>\n      <ul>{lis}</ul>'
    else:
        body=render_blocks(blocks, as_checklist=(k=="checklist"))
    url=f"https://indiemusicindia.com/toolkit/{slug}/"
    lead=("A free, ready-to-use template for independent Indian artists. Read it here, or make your own copy to fill in."
          if k=="template" else
          "A free, practical guide for independent Indian artists. Part of the Indie Music India toolkit.")
    eyebrow={"checklist":"Toolkit · Checklist","template":"Toolkit · Template","guide":"Toolkit · Guide"}[k]
    desc=f"{title}. A free {k} for independent Indian musicians, part of the Indie Music India toolkit."
    copybtn=(f'''    <div class="g-cta"><h3>Use this template</h3>
      <p>Make your own editable copy in Google Docs, fill it in, and keep it.</p>
      <a class="g-btn" href="https://docs.google.com/document/d/{did}/copy" target="_blank" rel="noopener">Make your own copy →</a></div>'''
      if k=="template" else
      '''    <div class="g-cta"><h3>Want a second pair of hands?</h3>
      <p>We work with a few independent Indian artists at a time, hands-on, one month to start, no cut of your music.</p>
      <a class="g-btn" href="/programme/">See how the programme works →</a></div>''')
    ld1='{"@context":"https://schema.org","@type":"Article","headline":%s,"description":%s,"image":"https://indiemusicindia.com/og-image.png","datePublished":"2026-09-15","dateModified":"2026-09-15","author":{"@type":"Organization","name":"Indie Music India"},"publisher":{"@type":"Organization","name":"Indie Music India","logo":{"@type":"ImageObject","url":"https://indiemusicindia.com/og-image.png"}},"mainEntityOfPage":%s}' % (json.dumps(title),json.dumps(desc),json.dumps(url))
    ld2='{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":"https://indiemusicindia.com/"},{"@type":"ListItem","position":2,"name":"Resources","item":"https://indiemusicindia.com/resources/"},{"@type":"ListItem","position":3,"name":%s,"item":%s}]}' % (json.dumps(title),json.dumps(url))
    return f'''<!DOCTYPE html>
<html lang="en-IN">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-R7EYMGZEJZ"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-R7EYMGZEJZ');</script>
  <meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(title)} · Indie Music India Toolkit</title>
  <meta name="description" content="{esc(desc)}" />
  <link rel="canonical" href="{url}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(desc)}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:type" content="article" />
  <meta property="og:image" content="https://indiemusicindia.com/og-image.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  {STYLE}
  {POPPY}
  <script type="application/ld+json">{ld1}</script>
  <script type="application/ld+json">{ld2}</script>
  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
</head>
<body>
  <header><div class="logo">◉ Indie Music India</div></header>
  <div class="mnav-burger" aria-label="Menu"><span></span><span></span><span></span></div>
  <nav class="js-primnav"><a class="tab" href="/">Home</a></nav>
  <div class="page">
    <div class="crumb"><a href="/">Home</a> › <a href="/resources/">Resources</a> › <a href="/resources/#toolkit">Toolkit</a> › {esc(title)}</div>
    <div class="g-eyebrow">{eyebrow}</div>
    <h1>{esc(title)}</h1>
    <p class="g-lead">{lead}</p>
    <article>
{body}
      <p class="g-updated">Free to use · Part of the Indie Music India toolkit · Updated September 2026</p>
    </article>
{copybtn}
  </div>
  <footer>
    <div class="footer-logo">◉ Indie Music India</div>
    <div class="footer-links"><a href="/">Home</a><a href="/resources/">Resources</a><a href="/reviewers/">Reviewers</a><a href="/tools/royalty-calculator/">Royalty calculator</a><a href="/about/">About</a></div>
  </footer>
  <script>
  document.querySelectorAll('.ck li').forEach(function(li){{li.addEventListener('click',function(){{li.classList.toggle('done');}});}});
  var b=document.querySelector('.mnav-burger');
  if(b)b.addEventListener('click',function(){{document.body.classList.toggle('mnav-open');}});
  document.addEventListener('click',function(e){{var a=e.target.closest('nav.js-primnav a');if(a)document.body.classList.remove('mnav-open');}});
  </script>
  <script src="/assets/nav.js" defer></script>
</body>
</html>
'''

def main():
    import shutil
    m=json.loads((SRC/"manifest.json").read_text())
    # clean previously-built pages (keep the hand-tuned proof)
    for d in OUT.iterdir():
        if d.is_dir() and d.name!="new-release-checklist": shutil.rmtree(d)
    built=[]
    for doc in m:
        title=html.unescape(doc["title"]); slug=slugify(title)
        if slug=="new-release-checklist": continue  # keep the hand-tuned proof
        d=OUT/slug; d.mkdir(parents=True, exist_ok=True)
        (d/"index.html").write_text(page(doc), encoding="utf-8")
        built.append((slug, kind(title), title))
    from collections import Counter
    print(f"Built {len(built)} toolkit pages -> {OUT}")
    for k,v in Counter(b[1] for b in built).items(): print(f"  {v} {k}")
    # write a slug list for sitemap wiring
    (SRC/"built_slugs.json").write_text(json.dumps([b[0] for b in built]+["new-release-checklist"]))

if __name__ == "__main__":
    main()
