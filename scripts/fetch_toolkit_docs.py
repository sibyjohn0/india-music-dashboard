#!/usr/bin/env python3
"""fetch_toolkit_docs.py — pull the toolkit Google Docs so they can be rebuilt as
branded on-site HTML pages.

One-time browser consent (read-only Drive), reuses the client at ~/.google-mcp.
Reads the 79 doc IDs + titles from resources/index.html, exports each doc's content
(HTML + plain text) to ~/Downloads/iim_toolkit/, and writes manifest.json so the
converter knows title -> slug -> file for every doc.

Run it yourself:  ! python3 ~/music-india-dashboard/scripts/fetch_toolkit_docs.py
"""
import re, json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

REPO = Path(__file__).resolve().parent.parent
RESOURCES = REPO / "resources" / "index.html"
CLIENT = Path.home()/".google-mcp"/"credentials.json"
TOKEN = Path.home()/".google-mcp"/"tokens"/"toolkit_read.json"
OUT = Path.home()/"Downloads"/"iim_toolkit"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def creds():
    c = Credentials.from_authorized_user_file(str(TOKEN), SCOPES) if TOKEN.exists() else None
    if not c or not c.valid:
        ok = False
        if c and c.expired and c.refresh_token:
            try: c.refresh(Request()); ok = True
            except Exception: c = None
        if not ok:
            c = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES).run_local_server(port=0)
        TOKEN.parent.mkdir(parents=True, exist_ok=True); TOKEN.write_text(c.to_json())
    return c

def slugify(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:60]

def docs():
    """Yield (doc_id, title, category) parsed from the toolkit section."""
    h = RESOURCES.read_text()
    # each toolkit item: <a class="doc-item" href=".../document/d/<ID>/edit" ...> ... doc-title">TITLE ... optional doc-cat">CAT
    for m in re.finditer(r'<a class="doc-item"[^>]*document/d/([a-zA-Z0-9_-]+)[^>]*>(.*?)</a>', h, re.S):
        did = m.group(1); block = m.group(2)
        tm = re.search(r'doc-title"[^>]*>([^<]+)', block)
        cm = re.search(r'doc-cat"[^>]*>([^<]+)', block)
        title = (tm.group(1).strip() if tm else did)
        cat = (cm.group(1).strip() if cm else "")
        yield did, title, cat

def main():
    drive = build("drive", "v3", credentials=creds())
    OUT.mkdir(parents=True, exist_ok=True)
    seen, manifest = set(), []
    for did, title, cat in docs():
        if did in seen: continue
        seen.add(did)
        slug = slugify(title)
        try:
            txt = drive.files().export(fileId=did, mimeType="text/plain").execute()
            html = drive.files().export(fileId=did, mimeType="text/html").execute()
            (OUT/f"{slug}.txt").write_bytes(txt)
            (OUT/f"{slug}.html").write_bytes(html)
            manifest.append({"id": did, "title": title, "category": cat, "slug": slug,
                             "words": len((txt or b"").decode("utf-8","ignore").split())})
            print(f"  ok  {title[:50]:50}  ({manifest[-1]['words']} words)")
        except Exception as e:
            print(f"  ERR {title[:50]:50}  {str(e)[:60]}")
    (OUT/"manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nPulled {len(manifest)} docs -> {OUT}\nmanifest.json written. Tell Claude it's ready.")

if __name__ == "__main__":
    main()
