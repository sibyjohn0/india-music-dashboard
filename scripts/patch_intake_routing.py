#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_intake_routing.py — one form for programme AND promotion leads.

Adds an explicit "Get my music featured or promoted" reason to the routing question
and branches it (and the programme option) into the music section so we capture the
artist's links/details; the other reasons still skip to the final ask. Categorisation
stays on the routing answer. Edits the live form in place (same URL).

Run: python3 scripts/patch_intake_routing.py
"""
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CLIENT = Path.home()/".google-mcp"/"credentials.json"
TOKEN = Path.home()/".google-mcp"/"tokens"/"forms_write.json"
SCOPES = ["https://www.googleapis.com/auth/forms.body"]
FID = "1GSjWNz5ESvEFEe1TsAIdwxCeKiDwuy_HEGw12PJoD04"

ROUTING = [  # (value, target section title)
    ("Working with you (the programme)", "Your music"),
    ("Get my music featured or promoted", "Your music"),
    ("A specific question or advice", "Last thing"),
    ("Partnership or brand", "Last thing"),
    ("Press or curator", "Last thing"),
    ("Something else", "Last thing"),
]

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

def main():
    svc = build("forms", "v1", credentials=creds())
    items = svc.forms().get(formId=FID).execute().get("items", [])
    sec = {it.get("title"): it["itemId"] for it in items if "pageBreakItem" in it}
    routing = next((it for it in items if it.get("title","").startswith("What are you reaching out about")), None)
    if not routing:
        print("routing question not found"); return
    ri = items.index(routing)
    opts = [{"value": v, "goToSectionId": sec[t]} for v, t in ROUTING]
    svc.forms().batchUpdate(formId=FID, body={"requests": [{"updateItem": {
        "item": {"itemId": routing["itemId"], "questionItem": {"question": {
            "required": True, "choiceQuestion": {"type": "RADIO", "options": opts}}}},
        "location": {"index": ri},
        "updateMask": "questionItem.question.choiceQuestion.options"}}]}).execute()
    print("Routing updated. Options now:")
    for v, t in ROUTING: print(f"  - {v}  -> {t}")

if __name__ == "__main__":
    main()
