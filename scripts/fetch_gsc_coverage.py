#!/usr/bin/env python3
"""fetch_gsc_coverage.py — GSC index-coverage check via the URL Inspection API.

For each important URL, reports whether Google has it indexed, its coverage state
("Submitted and indexed", "Crawled - currently not indexed", etc.), last crawl, and
any robots/canonical issues. Flags anything not indexed. Reuses the read-only token
from fetch_gsc.py (~/.google-mcp/tokens/gsc_read.json).

Run:  python3 scripts/fetch_gsc_coverage.py
"""
import csv, sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SITE = "sc-domain:indiemusicindia.com"
TOKEN = Path.home()/".google-mcp"/"tokens"/"gsc_read.json"
PAGES_CSV = Path.home()/"Downloads"/"iim_gsc"/"pages.csv"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

CLIENT = Path.home()/".google-mcp"/"credentials.json"
def creds():
    c = Credentials.from_authorized_user_file(str(TOKEN), SCOPES) if TOKEN.exists() else None
    if not c or not c.valid:
        ok=False
        if c and c.expired and c.refresh_token:
            try: c.refresh(Request()); ok=True
            except Exception: c=None
        if not ok:
            c = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES).run_local_server(port=0)
        TOKEN.write_text(c.to_json())
    return c

import re
SITEMAP = Path(__file__).resolve().parent.parent / "sitemap.xml"
def urls():
    # every URL in the sitemap (complete indexing picture), deduped, order preserved
    out = []
    if SITEMAP.exists():
        for u in re.findall(r"<loc>(.*?)</loc>", SITEMAP.read_text()):
            if u not in out: out.append(u)
    return out

def main():
    svc = build("searchconsole", "v1", credentials=creds())
    rows = []
    for u in urls():
        try:
            r = svc.urlInspection().index().inspect(
                body={"inspectionUrl": u, "siteUrl": SITE}).execute()
            s = r.get("inspectionResult", {}).get("indexStatusResult", {})
            rows.append((u, s.get("verdict","?"), s.get("coverageState","?"),
                         s.get("robotsTxtState","?"), (s.get("lastCrawlTime","") or "never")[:10],
                         s.get("googleCanonical","")))
        except Exception as e:
            rows.append((u, "ERROR", str(e)[:60], "", "", ""))
    # report
    def is_indexed(cov): c=cov.lower(); return "indexed" in c and "not indexed" not in c
    notindexed = [r for r in rows if not is_indexed(r[2]) or r[1]=="FAIL"]
    print(f"URL INDEX COVERAGE  ({len(rows)} pages)\n"+"="*70)
    for u,v,cov,rob,crawl,canon in rows:
        flag = "  <-- CHECK" if ("indexed" not in cov.lower() or v=="FAIL") else ""
        print(f"[{v:7}] {cov:34} {crawl}  {u.replace('https://indiemusicindia.com','')}{flag}")
    print("="*70)
    print(f"Indexed OK: {len(rows)-len(notindexed)} / {len(rows)}   |   Needs attention: {len(notindexed)}")
    if notindexed:
        print("\nNOT INDEXED / ISSUES:")
        for u,v,cov,rob,crawl,canon in notindexed:
            print(f"  {u}\n    state: {cov} | verdict: {v} | robots: {rob} | canonical: {canon}")

if __name__ == "__main__":
    main()
