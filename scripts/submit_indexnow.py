#!/usr/bin/env python3
"""submit_indexnow.py — notify IndexNow (Bing/Yandex + partners) of the site's URLs.

Reads every <loc> in sitemap.xml and submits them in one IndexNow POST so new/changed
pages get crawled sooner. Key file must be live at the site root (it is:
/5570c9a3e95a49e587a509eda7662b24.txt).

Run: python3 scripts/submit_indexnow.py
"""
import json, re, urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOST = "indiemusicindia.com"
KEY = "5570c9a3e95a49e587a509eda7662b24"
ENDPOINT = "https://api.indexnow.org/indexnow"

def main():
    sm = (REPO/"sitemap.xml").read_text()
    urls = re.findall(r"<loc>(.*?)</loc>", sm)
    body = json.dumps({
        "host": HOST,
        "key": KEY,
        "keyLocation": f"https://{HOST}/{KEY}.txt",
        "urlList": urls,
    }).encode()
    req = urllib.request.Request(ENDPOINT, data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"IndexNow: HTTP {r.status} for {len(urls)} URLs "
                  f"({sum('/toolkit/' in u for u in urls)} toolkit)")
    except urllib.error.HTTPError as e:
        # IndexNow returns 200/202 on success; 4xx bodies explain rejections
        print(f"IndexNow: HTTP {e.code} — {e.read().decode()[:200]}")

if __name__ == "__main__":
    main()
