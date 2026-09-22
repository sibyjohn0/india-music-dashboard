#!/usr/bin/env python3
"""create_intake_form.py — build the Indie Music India qualification intake Google Form.

One-time browser consent (Forms scope), reuses the client at ~/.google-mcp. Creates a
sectioned, branching form: identity, music background, psychographics, demographics, and
spending power. Only people choosing "Working with you (the programme)" get the full
deep-dive; brands / press / quick questions jump straight to the ask. Writes the responder
+ edit URLs to ~/Downloads/iim_intake_form.json so Claude can wire the link into the site.

Run it yourself:  ! python3 ~/music-india-dashboard/scripts/create_intake_form.py
"""
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

CLIENT = Path.home()/".google-mcp"/"credentials.json"
TOKEN = Path.home()/".google-mcp"/"tokens"/"forms_write.json"
OUT = Path.home()/"Downloads"/"iim_intake_form.json"
SCOPES = ["https://www.googleapis.com/auth/forms.body"]

ROUTING = ["Working with you (the programme)", "Get my music featured or promoted",
           "A specific question or advice", "Partnership or brand", "Press or curator",
           "Something else"]
# these routes go into the deep-dive (music section); the rest skip to the final ask
MUSIC_ROUTES = {"Working with you (the programme)", "Get my music featured or promoted"}

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

def txt(title, paragraph=False, required=False):
    return {"title": title, "questionItem": {"question": {
        "required": required, "textQuestion": {"paragraph": paragraph}}}}

def choice(title, options, required=False, checkbox=False):
    return {"title": title, "questionItem": {"question": {
        "required": required, "choiceQuestion": {
            "type": "CHECKBOX" if checkbox else "RADIO",
            "options": [{"value": o} for o in options]}}}}

def section(title, desc=""):
    it = {"title": title, "pageBreakItem": {}}
    if desc: it["description"] = desc
    return it

def main():
    svc = build("forms", "v1", credentials=creds())
    form = svc.forms().create(body={"info": {
        "title": "Reach out to Indie Music India",
        "documentTitle": "IIM Intake Form",
    }}).execute()
    fid = form["formId"]

    # ordered items; remember index of the routing question and the "Last thing" section
    items = []
    items.append(("routing", choice("What are you reaching out about?", ROUTING, required=True)))
    items += [
        (None, txt("Your name", required=True)),
        (None, txt("Your email", required=True)),
        (None, txt("Phone number", required=True)),
        (None, choice("Is this the same number you use for WhatsApp?", ["Yes", "No"], required=True)),
        (None, txt("If it's different, your WhatsApp number")),
        (None, choice("Your role", ["Artist", "Band member", "Manager or artist team",
                                     "Label or agency", "Brand", "Press or curator", "Other"])),
        (None, txt("Artist, project, or organisation name")),
        (None, choice("Where are you based?",
                      ["Mumbai", "Delhi NCR", "Bengaluru", "Hyderabad", "Chennai", "Kolkata",
                       "Pune", "Another city in India", "Outside India"])),
        (None, txt("Spotify or Apple Music link")),
        (None, txt("Drop a track or two you want us to hear (paste a link: SoundCloud, YouTube, "
                   "Google Drive, a Spotify or Apple track, etc.)", paragraph=True)),
        (None, txt("YouTube channel")),
        (None, txt("Instagram handle or link")),
        (None, txt("Any other social or music links (website, SoundCloud, JioSaavn, press, etc.)", paragraph=True)),
    ]
    items.append((None, section("Your music",
        "A quick picture of where you are as an artist. Rough answers are fine.")))
    items += [
        (None, choice("What genre or style? (tick all that apply)",
                      ["Hip-hop / Rap", "Indie / Alternative", "Pop", "R&B / Soul", "Electronic / EDM",
                       "Rock / Metal", "Folk / Acoustic", "Classical / Fusion", "Regional / Film",
                       "Something else"], checkbox=True)),
        (None, choice("What languages do you make music in? (tick all that apply)",
                      ["Hindi", "English", "Punjabi", "Tamil", "Telugu", "Malayalam", "Kannada",
                       "Bengali", "Marathi", "Instrumental / no lyrics", "Other"], checkbox=True)),
        (None, choice("How long have you been making music?",
                      ["Under a year", "1 to 3 years", "3 to 5 years", "5 to 10 years", "10+ years"])),
        (None, choice("Your background (tick all that apply)",
                      ["Self-taught", "Formally trained", "From a music family",
                       "Music is my full-time focus", "I make music alongside a job or studies"],
                      checkbox=True)),
        (None, choice("How many songs have you released?", ["None yet", "1 to 3", "4 to 10", "More than 10"])),
        (None, choice("Do you play live?", ["Regularly", "Occasionally", "Not yet"])),
        (None, choice("Roughly your current audience",
                      ["Just starting out", "Under 1,000 monthly listeners", "1,000 to 10,000",
                       "10,000 to 100,000", "Over 100,000"])),
        (None, choice("Spotify monthly listeners",
                      ["None yet", "Under 1,000", "1,000 to 10,000", "10,000 to 50,000",
                       "50,000 to 500,000", "Over 500,000"])),
        (None, choice("Instagram followers",
                      ["Under 500", "500 to 2,000", "2,000 to 10,000", "10,000 to 50,000",
                       "50,000 to 250,000", "Over 250,000"])),
        (None, choice("YouTube subscribers",
                      ["None yet", "Under 1,000", "1,000 to 10,000", "10,000 to 100,000",
                       "100,000 to 1M", "Over 1M"])),
        (None, txt("Anything notable on other platforms? (Apple Music, JioSaavn, X, etc.)")),
    ]
    items.append((None, section("Where you're headed",
        "This tells us what you actually want, so we don't push you toward the wrong thing.")))
    items += [
        (None, choice("What do you want from your music?",
                      ["A full-time career", "A serious part-time pursuit", "To get heard more widely",
                       "I just love making it", "Still figuring it out"])),
        (None, txt("What would \"making it\" look like for you?", paragraph=True)),
        (None, choice("Your biggest challenge right now (tick all that apply)",
                      ["Getting heard", "Money and royalties", "Releasing consistently", "Live shows",
                       "Branding and identity", "Knowing what to do next", "Something else"], checkbox=True)),
        (None, choice("How do you think about spending on your career?",
                      ["I invest where it clearly helps", "I'm careful, mostly do it myself",
                       "I've been burned paying for things before", "I don't have much to spend yet"])),
        (None, choice("How much time can you put in each week?",
                      ["Under 5 hours", "5 to 15 hours", "15 to 30 hours", "It's full-time for me"])),
    ]
    items.append((None, section("Budget and fit",
        "Ranges are fine. This helps us suggest something realistic, not upsell you.")))
    items += [
        (None, choice("What do you currently earn from music per month?",
                      ["Nothing yet", "Under Rs 10,000", "Rs 10,000 to 50,000", "Rs 50,000 to 2 lakh",
                       "Over 2 lakh", "Prefer not to say"])),
        (None, choice("Roughly what could you put toward your music career each month right now?",
                      ["Under Rs 5,000", "Rs 5,000 to 15,000", "Rs 15,000 to 40,000",
                       "Rs 40,000 to 1 lakh", "Over 1 lakh", "Not sure yet"])),
        (None, choice("Have you paid for any of these before? (tick all that apply)",
                      ["Distribution", "PR or playlist pitching", "A music video", "Artwork or branding",
                       "A manager or consultant", "Paid ads", "None yet"], checkbox=True)),
        (None, choice("For working with us, what kind of investment are you comfortable with?",
                      ["Just exploring for now", "Free tools only", "A few thousand a month",
                       "A serious monthly retainer", "Depends on the plan"])),
        (None, choice("Your age range (optional)",
                      ["Under 18", "18 to 24", "25 to 34", "35 to 44", "45+", "Prefer not to say"])),
        (None, choice("Gender (optional)", ["Woman", "Man", "Non-binary", "Prefer to self-describe",
                                            "Prefer not to say"])),
    ]
    items.append(("last", section("Last thing",
        "The most useful part: tell us what you actually need.")))
    items += [
        (None, txt("What do you need from us? Give us the ask, and any context that helps us give a useful answer.",
                   paragraph=True, required=True)),
        (None, choice("Timeline", ["Right now", "In the next few weeks", "Just planning ahead", "No rush"])),
        (None, choice("How did you find us?",
                      ["Instagram", "Google search", "A friend or another artist",
                       "A guide or tool on the site", "YouTube", "Somewhere else"])),
        (None, txt("Anything else you want us to know?", paragraph=True)),
    ]

    # build create requests; description first
    requests = [{"updateFormInfo": {"info": {"description":
        ("Tell us what you need and we'll come back with something useful. This helps us "
         "understand who you are and how we can help, so the first reply is a real answer, "
         "not a round of questions. It takes a few minutes if you're asking about the programme, "
         "less for anything else.")}, "updateMask": "description"}}]
    routing_reqpos = last_reqpos = None
    for i, (tag, it) in enumerate(items):
        requests.append({"createItem": {"item": it, "location": {"index": i}}})
        if tag == "routing": routing_reqpos = len(requests) - 1
        if tag == "last":    last_reqpos = len(requests) - 1

    resp = svc.forms().batchUpdate(formId=fid, body={"requests": requests}).execute()
    replies = resp.get("replies", [])

    # branching: quick paths skip straight to "Last thing"; programme continues into the deep-dive
    try:
        routing_item = replies[routing_reqpos]["createItem"]["itemId"]
        last_section = replies[last_reqpos]["createItem"]["itemId"]
        opts = []
        for v in ROUTING:
            if v in MUSIC_ROUTES:
                opts.append({"value": v, "goToAction": "NEXT_SECTION"})
            else:
                opts.append({"value": v, "goToSectionId": last_section})
        svc.forms().batchUpdate(formId=fid, body={"requests": [{"updateItem": {
            "item": {"itemId": routing_item, "questionItem": {"question": {
                "required": True, "choiceQuestion": {"type": "RADIO", "options": opts}}}},
            "location": {"index": 0},
            "updateMask": "questionItem.question.choiceQuestion.options"}}]}).execute()
        branched = True
    except Exception as e:
        branched = False
        print(f"(branching skipped: {str(e)[:80]} — form still works as a linear form)")

    info = {"formId": fid, "responderUri": form.get("responderUri"),
            "editUri": f"https://docs.google.com/forms/d/{fid}/edit", "branching": branched}
    OUT.write_text(json.dumps(info, indent=2))
    print("Form created" + (" with branching." if branched else "."))
    print("  Fill-in (public):", info["responderUri"])
    print("  Edit:            ", info["editUri"])
    print(f"\nSaved to {OUT}. Tell Claude it's ready to wire into the site.")

if __name__ == "__main__":
    main()
