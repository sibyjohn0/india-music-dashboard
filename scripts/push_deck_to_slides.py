#!/usr/bin/env python3
"""push_deck_to_slides.py — upload the .pptx to Drive AS a native Google Slides.

One-time browser consent (uses the Google client already at ~/.google-mcp), then
converts the deck to Google Slides so a teammate can open it and drag-and-drop.
Token is cached, so re-running after a rebuild just re-uploads with no new consent.

Run it yourself (interactive login):  ! python3 scripts/push_deck_to_slides.py
"""
import sys, json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

REPO = Path(__file__).resolve().parent.parent
PPTX = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO/"social"/"decks"/"IIM-Artist-Working-Deck.pptx"
CLIENT = Path.home()/".google-mcp"/"credentials.json"
TOKEN = Path.home()/".google-mcp"/"tokens"/"deck_push.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
SLIDES_MIME = "application/vnd.google-apps.presentation"
PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

def creds():
    c = None
    if TOKEN.exists():
        c = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not c or not c.valid:
        if c and c.expired and c.refresh_token:
            c.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES)
            c = flow.run_local_server(port=0)
        TOKEN.parent.mkdir(parents=True, exist_ok=True)
        TOKEN.write_text(c.to_json())
    return c

def main():
    if not PPTX.exists():
        sys.exit(f"Not found: {PPTX}  (run build_deck.py first)")
    drive = build("drive", "v3", credentials=creds())
    meta = {"name": "IIM — Artist Working Deck (Template Kit)", "mimeType": SLIDES_MIME}
    media = MediaFileUpload(str(PPTX), mimetype=PPTX_MIME, resumable=True)
    f = drive.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()
    fid = f["id"]
    drive.permissions().create(fileId=fid, body={"type": "anyone", "role": "writer"}).execute()
    print("\n✅ Google Slides ready (anyone with link can edit):")
    print(f"   {f.get('webViewLink') or f'https://docs.google.com/presentation/d/{fid}/edit'}\n")

if __name__ == "__main__":
    main()
