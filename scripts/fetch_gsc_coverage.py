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
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SITE = "sc-domain:indiemusicindia.com"
TOKEN = Path.home()/".google-mcp"/"tokens"/"gsc_read.json"
PAGES_CSV = Path.home()/"Downloads"/"iim_gsc"/"pages.csv"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

def creds():
    c = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if c.expired and c.refresh_token:
        c.refresh(Request())
    return c

def urls():
    # pages already surfacing in GSC + the core set, deduped
    seen = []
    if PAGES_CSV.exists():
        for row in csv.reader(open(PAGES_CSV)):
            if row and row[0].startswith("http"):
                seen.append(row[0])
    core = ["https://indiemusicindia.com/","https://indiemusicindia.com/reviewers/",
            "https://indiemusicindia.com/tools/royalty-calculator/","https://indiemusicindia.com/programme/",
            "https://indiemusicindia.com/resources/","https://indiemusicindia.com/answers/",
            "https://indiemusicindia.com/live/","https://indiemusicindia.com/venues/mumbai/"]
    out = []
    for u in seen + core:
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
    notindexed = [r for r in rows if "indexed" not in r[2].lower() or r[1]=="FAIL"]
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
