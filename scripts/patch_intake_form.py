#!/usr/bin/env python3
"""patch_intake_form.py — make the phone question required and add a WhatsApp question.

Edits the existing intake form in place (keeps the same responder link). Reuses the
cached forms.body token from create_intake_form.py.

Run: python3 scripts/patch_intake_form.py
"""
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CLIENT = Path.home()/".google-mcp"/"credentials.json"
TOKEN = Path.home()/".google-mcp"/"tokens"/"forms_write.json"
INFO = Path.home()/"Downloads"/"iim_intake_form.json"
SCOPES = ["https://www.googleapis.com/auth/forms.body"]

def creds():
    c = Credentials.from_authorized_user_file(str(TOKEN), SCOPES) if TOKEN.exists() else None
    if not c or not c.valid:
        ok = False
        if c and c.expired and c.refresh_token:
            try: c.refresh(Request()); ok = True
            except Exception: c = None
        if not ok:
            c = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES).run_local_server(port=0)
        TOKEN.write_text(c.to_json())
    return c

def find(items, pred):
    return next((i for i, it in enumerate(items) if pred(it.get("title", ""))), None)

def main():
    fid = json.loads(INFO.read_text())["formId"]
    svc = build("forms", "v1", credentials=creds())
    items = svc.forms().get(formId=fid).execute().get("items", [])

    # 1) phone required + rename, add WhatsApp questions (contiguous inserts, one batch)
    if any("same number you use for WhatsApp" in it.get("title", "") for it in items):
        print("WhatsApp question already present; skipping phone/WhatsApp step.")
    else:
        pi = find(items, lambda t: t.lower().startswith("phone"))
        if pi is None:
            print("Phone question not found; skipping phone/WhatsApp step.")
        else:
            svc.forms().batchUpdate(formId=fid, body={"requests": [
                {"updateItem": {
                    "item": {"itemId": items[pi]["itemId"], "title": "Phone number",
                             "questionItem": {"question": {"required": True, "textQuestion": {"paragraph": False}}}},
                    "location": {"index": pi}, "updateMask": "title,questionItem.question.required"}},
                {"createItem": {"item": {"title": "Is this the same number you use for WhatsApp?",
                    "questionItem": {"question": {"required": True, "choiceQuestion": {
                        "type": "RADIO", "options": [{"value": "Yes"}, {"value": "No"}]}}}},
                    "location": {"index": pi + 1}}},
                {"createItem": {"item": {"title": "If it's different, your WhatsApp number",
                    "questionItem": {"question": {"required": False, "textQuestion": {"paragraph": False}}}},
                    "location": {"index": pi + 2}}},
            ]}).execute()
            print("Patched: phone is now required, WhatsApp question added after it.")

    # 2) add the "drop a track" field after the Spotify/Apple link (fresh lookup)
    items = svc.forms().get(formId=fid).execute().get("items", [])
    if any(t.startswith("Drop a track") for t in (it.get("title", "") for it in items)):
        print("Track-drop question already present; nothing to add.")
    else:
        si = find(items, lambda t: t.startswith("Spotify or Apple"))
        if si is None:
            print("Spotify/Apple field not found; skipping track step.")
        else:
            svc.forms().batchUpdate(formId=fid, body={"requests": [
                {"createItem": {"item": {"title": ("Drop a track or two you want us to hear (paste a link: "
                    "SoundCloud, YouTube, Google Drive, a Spotify or Apple track, etc.)"),
                    "questionItem": {"question": {"required": False, "textQuestion": {"paragraph": True}}}},
                    "location": {"index": si + 1}}},
            ]}).execute()
            print("Patched: track-drop field added after the Spotify/Apple link.")

    # 3) add per-platform follower fields after the "current audience" question (fresh lookup)
    items = svc.forms().get(formId=fid).execute().get("items", [])
    if any(t.startswith("Spotify monthly listeners") for t in (it.get("title", "") for it in items)):
        print("Follower fields already present; nothing to add.")
    else:
        ai = find(items, lambda t: t.startswith("Roughly your current audience"))
        if ai is None:
            print("Audience field not found; skipping follower step.")
        else:
            followers = ["Spotify monthly listeners", "Instagram followers", "YouTube subscribers",
                         "Followers on any other platforms (Apple Music, JioSaavn, X, etc.)"]
            reqs = [{"createItem": {"item": {"title": t,
                "questionItem": {"question": {"required": False, "textQuestion": {"paragraph": False}}}},
                "location": {"index": ai + 1 + n}}} for n, t in enumerate(followers)]
            svc.forms().batchUpdate(formId=fid, body={"requests": reqs}).execute()
            print("Patched: per-platform follower fields added after the audience question.")

if __name__ == "__main__":
    main()
