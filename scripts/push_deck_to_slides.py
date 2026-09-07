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
IDFILE = Path.home()/".google-mcp"/"tokens"/"deck_file_id.txt"
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

def fix_fonts(cr, fid):
    """PPTX import carries the font NAME but Google won't load a non-default
    webfont (Bricolage Grotesque) until it's set via the API. Re-assert it so it
    actually renders for every viewer. Inter/Space Mono are default and fine."""
    sl = build("slides", "v1", credentials=cr)
    pres = sl.presentations().get(presentationId=fid).execute()
    reqs = []
    def walk(els):
        for e in els:
            sh = e.get("shape"); oid = e.get("objectId")
            if sh and "text" in sh:
                for te in sh["text"].get("textElements", []):
                    tr = te.get("textRun")
                    if tr and tr.get("style", {}).get("fontFamily") == "Bricolage Grotesque":
                        en = te.get("endIndex")
                        if en is None: continue
                        reqs.append({"updateTextStyle": {"objectId": oid,
                            "textRange": {"type": "FIXED_RANGE", "startIndex": te.get("startIndex", 0), "endIndex": en},
                            "style": {"fontFamily": "Bricolage Grotesque", "bold": True}, "fields": "fontFamily"}})
            if "elementGroup" in e: walk(e["elementGroup"]["children"])
    for p in pres["slides"]: walk(p.get("pageElements", []))
    for i in range(0, len(reqs), 200):
        sl.presentations().batchUpdate(presentationId=fid, body={"requests": reqs[i:i+200]}).execute()
    return len(reqs)

def main():
    if not PPTX.exists():
        sys.exit(f"Not found: {PPTX}  (run build_deck.py first)")
    cr = creds()
    drive = build("drive", "v3", credentials=cr)
    media = MediaFileUpload(str(PPTX), mimetype=PPTX_MIME, resumable=True)
    existing = IDFILE.read_text().strip() if IDFILE.exists() else None
    if existing:  # update in place, keeps the same link
        f = drive.files().update(fileId=existing, media_body=media, fields="id,webViewLink").execute()
        action = "updated"
    else:
        meta = {"name": "IIM — Artist Working Deck (Template Kit)", "mimeType": SLIDES_MIME}
        f = drive.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()
        drive.permissions().create(fileId=f["id"], body={"type": "anyone", "role": "writer"}).execute()
        action = "created"
    fid = f["id"]
    IDFILE.write_text(fid)
    n = fix_fonts(cr, fid)
    print(f"\n✅ Google Slides {action} (anyone with link can edit); Bricolage re-asserted on {n} runs:")
    print(f"   {f.get('webViewLink') or f'https://docs.google.com/presentation/d/{fid}/edit'}\n")

if __name__ == "__main__":
    main()
