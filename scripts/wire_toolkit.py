#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wire_toolkit.py — point the site at the new on-site toolkit pages.

1. Rewrites resources/index.html: each toolkit doc-item that linked to a Google Doc
   now links to its on-site /toolkit/<slug>/ page (internal, no target/rel).
2. Adds every /toolkit/<slug>/ URL to sitemap.xml.

Run after build_toolkit_pages.py.  python3 scripts/wire_toolkit.py
"""
import json, re, html
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = Path.home()/"Downloads"/"iim_toolkit"
RES = REPO/"resources"/"index.html"
SITEMAP = REPO/"sitemap.xml"

def slugify(t): return re.sub(r"[^a-z0-9]+","-",t.lower()).strip("-")[:60]

def main():
    m = json.loads((SRC/"manifest.json").read_text())
    id2slug = {d["id"]: slugify(html.unescape(d["title"])) for d in m}

    # 1. repoint resources doc-item links -> on-site pages
    r = RES.read_text()
    n = 0
    def repl(mo):
        nonlocal n
        did = mo.group(1)
        if did in id2slug:
            n += 1
            return f'<a class="doc-item" href="/toolkit/{id2slug[did]}/">'
        return mo.group(0)
    r = re.sub(r'<a class="doc-item" href="https://docs\.google\.com/document/d/([a-zA-Z0-9_-]+)/edit"[^>]*>', repl, r)
    RES.write_text(r)
    print(f"resources: repointed {n} toolkit links to /toolkit/")

    # 2. add toolkit URLs to sitemap
    slugs = sorted(set(id2slug.values()))
    sm = SITEMAP.read_text()
    existing = set(re.findall(r'/toolkit/([^/]+)/</loc>', sm))
    rows = "".join(
        f'  <url><loc>https://indiemusicindia.com/toolkit/{s}/</loc>'
        f'<lastmod>2026-09-15</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>\n'
        for s in slugs if s not in existing)
    if rows:
        sm = sm.replace("</urlset>", rows + "</urlset>")
        SITEMAP.write_text(sm)
    print(f"sitemap: added {len([s for s in slugs if s not in existing])} toolkit URLs "
          f"(total toolkit in sitemap now {len(existing)+len([s for s in slugs if s not in existing])})")

if __name__ == "__main__":
    main()
