#!/usr/bin/env python3
"""fetch_analytics.py — read the IIM website analytics Google Sheet (all tabs) to CSV.

One-time browser consent (read-only Sheets scope), reuses the Google client already
at ~/.google-mcp. Dumps every tab to ~/Downloads/iim_analytics/<tab>.csv so it can be
analysed. Token cached, so re-runs need no consent.

Run it yourself:  ! python3 ~/music-india-dashboard/scripts/fetch_analytics.py
"""
import csv, sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SHEET_ID = "1_IA0lMMJqqs8veweS3mXo-atBm7_oRGREANeU_W5iRU"
CLIENT = Path.home()/".google-mcp"/"credentials.json"
TOKEN = Path.home()/".google-mcp"/"tokens"/"sheets_read.json"
OUTDIR = Path.home()/"Downloads"/"iim_analytics"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def creds():
    c = Credentials.from_authorized_user_file(str(TOKEN), SCOPES) if TOKEN.exists() else None
    if not c or not c.valid:
        if c and c.expired and c.refresh_token:
            c.refresh(Request())
        else:
            c = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES).run_local_server(port=0)
        TOKEN.parent.mkdir(parents=True, exist_ok=True); TOKEN.write_text(c.to_json())
    return c

def main():
    sh = build("sheets", "v4", credentials=creds())
    meta = sh.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print("SHEET:", meta["properties"]["title"])
    for s in meta["sheets"]:
        title = s["properties"]["title"]
        vals = sh.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=title).execute().get("values", [])
        safe = "".join(ch if ch.isalnum() else "_" for ch in title)[:50]
        with open(OUTDIR/f"{safe}.csv", "w", newline="") as f:
            csv.writer(f).writerows(vals)
        print(f"  {title}: {len(vals)} rows -> {OUTDIR/(safe+'.csv')}")

if __name__ == "__main__":
    main()
