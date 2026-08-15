#!/usr/bin/env python3
"""Pull Instagram insights for @indiemusicindia.co via the Graph API and append
to social/IG_INSIGHTS.json (per-post reach/views/saves/shares/comments).

Needs a Business/Creator account linked to a Facebook Page, and:
  IG_ACCESS_TOKEN  — long-lived token with instagram_basic + instagram_manage_insights
  IG_USER_ID       — the Instagram Business account id (numeric)

Run: IG_ACCESS_TOKEN=... IG_USER_ID=... python3 scripts/fetch_ig_insights.py
Safe to run on a schedule; it just snapshots current numbers.
"""
import os, json, sys, urllib.request, urllib.parse, datetime
from pathlib import Path

TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
USER  = os.environ.get("IG_USER_ID", "")
OUT   = Path(__file__).resolve().parent.parent / "social" / "IG_INSIGHTS.json"
BASE  = "https://graph.facebook.com/v21.0"

def api(path, params):
    params = {**params, "access_token": TOKEN}
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())

def main():
    if not TOKEN or not USER:
        print("ERROR: set IG_ACCESS_TOKEN and IG_USER_ID env vars.", file=sys.stderr); sys.exit(1)
    # recent media
    media = api(f"{USER}/media", {"fields": "id,caption,media_type,permalink,timestamp", "limit": 30})
    rows = []
    for m in media.get("data", []):
        mid = m["id"]
        # reels use "reels" metrics; images use impressions/reach. Try the common set.
        metrics = "reach,saved,shares,comments,likes,total_interactions,plays"
        vals = {}
        try:
            ins = api(f"{mid}/insights", {"metric": metrics})
            for v in ins.get("data", []):
                vals[v["name"]] = v.get("values", [{}])[0].get("value")
        except Exception as e:
            vals["_error"] = str(e)[:120]
        cap = (m.get("caption") or "").split("\n")[0][:60]
        rows.append({"id": mid, "type": m.get("media_type"), "when": m.get("timestamp"),
                     "caption": cap, "permalink": m.get("permalink"), **vals})
    snap = {"fetched": datetime.datetime.utcnow().isoformat()+"Z", "posts": rows}
    hist = []
    if OUT.exists():
        try: hist = json.load(open(OUT))
        except Exception: hist = []
    hist.append(snap)
    json.dump(hist[-60:], open(OUT, "w"), indent=2, ensure_ascii=False)  # keep last 60 snapshots
    print(f"fetched {len(rows)} posts -> {OUT}")
    # quick scoreboard, sorted by reach
    rows.sort(key=lambda r: -(r.get("reach") or 0))
    for r in rows[:12]:
        print(f"  reach={r.get('reach','?'):>6}  saved={r.get('saved','?'):>4}  "
              f"shares={r.get('shares','?'):>4}  {r['caption']}")

if __name__ == "__main__":
    main()
