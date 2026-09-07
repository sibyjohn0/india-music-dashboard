#!/usr/bin/env python3
"""fetch_gsc.py — pull Google Search Console data for indiemusicindia.com.

One-time browser consent (read-only Search Console), reuses the Google client at
~/.google-mcp. Dumps the impressions/clicks trend, top queries, and top pages to
~/Downloads/iim_gsc/*.csv, and prints a summary (recent 28 days vs the 28 before,
so the impressions drop is visible). Token cached; re-runs need no consent.

Run it yourself:  ! python3 ~/music-india-dashboard/scripts/fetch_gsc.py
"""
import csv
from datetime import date, timedelta
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SITE = "sc-domain:indiemusicindia.com"          # domain property
CLIENT = Path.home()/".google-mcp"/"credentials.json"
TOKEN = Path.home()/".google-mcp"/"tokens"/"gsc_read.json"
OUTDIR = Path.home()/"Downloads"/"iim_gsc"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

def creds():
    c = Credentials.from_authorized_user_file(str(TOKEN), SCOPES) if TOKEN.exists() else None
    if not c or not c.valid:
        if c and c.expired and c.refresh_token:
            c.refresh(Request())
        else:
            c = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES).run_local_server(port=0)
        TOKEN.parent.mkdir(parents=True, exist_ok=True); TOKEN.write_text(c.to_json())
    return c

def query(svc, start, end, dims, limit=25000):
    rows = svc.searchanalytics().query(siteUrl=SITE, body={
        "startDate": start.isoformat(), "endDate": end.isoformat(),
        "dimensions": dims, "rowLimit": limit,
    }).execute().get("rows", [])
    return rows

def dump(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(header)
        for r in rows: w.writerow(r)

def main():
    svc = build("searchconsole", "v1", credentials=creds())
    OUTDIR.mkdir(parents=True, exist_ok=True)
    end = date.today() - timedelta(days=3)          # GSC lags ~2-3 days
    start = end - timedelta(days=89)
    mid = end - timedelta(days=27)                   # last 28 days = mid..end

    # daily trend
    daily = query(svc, start, end, ["date"])
    dump(OUTDIR/"daily.csv", ["date","clicks","impressions","ctr","position"],
         [[r["keys"][0], r["clicks"], r["impressions"], round(r["ctr"],4), round(r["position"],1)] for r in daily])

    # queries + pages (last 90d)
    q = query(svc, start, end, ["query"])
    dump(OUTDIR/"queries.csv", ["query","clicks","impressions","ctr","position"],
         [[r["keys"][0], r["clicks"], r["impressions"], round(r["ctr"],4), round(r["position"],1)] for r in q])
    p = query(svc, start, end, ["page"])
    dump(OUTDIR/"pages.csv", ["page","clicks","impressions","ctr","position"],
         [[r["keys"][0], r["clicks"], r["impressions"], round(r["ctr"],4), round(r["position"],1)] for r in p])

    # recent 28 vs previous 28 (to see the drop)
    def totals(s, e):
        rows = query(svc, s, e, ["date"])
        return sum(r["impressions"] for r in rows), sum(r["clicks"] for r in rows)
    recent = totals(mid, end)
    prev = totals(mid - timedelta(days=28), mid - timedelta(days=1))

    print(f"SITE: {SITE}   window: {start} to {end}")
    print(f"  last 28d : {recent[0]:>7} impressions, {recent[1]:>4} clicks")
    print(f"  prev 28d : {prev[0]:>7} impressions, {prev[1]:>4} clicks")
    if prev[0]:
        print(f"  change   : impressions {(recent[0]-prev[0])/prev[0]*100:+.0f}%")
    print(f"  queries: {len(q)}   pages: {len(p)}   -> {OUTDIR}")

if __name__ == "__main__":
    main()
