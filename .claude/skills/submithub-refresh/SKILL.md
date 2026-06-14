---
name: submithub-refresh
description: Manually refresh the SubmitHub curator data. Use when SubmitHub data is 2-3 months old or the user says it is due for a refresh. SubmitHub uses Minimongo and cannot be auto-scraped -- this is always a manual browser-assisted process.
tools: Read, Bash, Edit
---

# SubmitHub Refresh

SubmitHub stores all 869 curator records in the browser's client-side Minimongo store, not a server API. This requires a browser session to extract.

**Last scraped:** 2026-05-25
**Next due:** ~2026-07-25

## Step 1: Open SubmitHub via Puppeteer MCP

Use the `mcp__puppeteer__puppeteer_navigate` tool to open:
```
https://submithub.com/curators
```

Wait for the page to fully load (curator cards should be visible).

## Step 2: Extract the Minimongo store

Run this in the browser console via `mcp__puppeteer__puppeteer_evaluate`:

```javascript
Browser.find({name: 'all_blogs'}).fetch()[0].data
```

This returns all curator records as a JSON array. Capture the result.

## Step 3: Download to local file

Still in the browser console, run:

```javascript
const data = Browser.find({name: 'all_blogs'}).fetch()[0].data;
const blob = new Blob([JSON.stringify(data)], {type: 'application/json'});
const a = document.createElement('a');
a.href = URL.createObjectURL(blob);
a.download = 'submithub_raw.json';
a.click();
```

File downloads to `~/Downloads/submithub_raw.json`.

## Step 4: Rebuild the SubmitHub source file

```bash
cd /Users/sibyjohn/music-india-dashboard

python3 - << 'EOF'
import json, os

with open(os.path.expanduser("~/Downloads/submithub_raw.json")) as f:
    raw = json.load(f)

# Normalise to the schema expected by merge_reviewers.py
curators = []
for r in raw:
    curators.append({
        "id": r.get("_id") or r.get("id"),
        "name": r.get("name") or r.get("blogName"),
        "url": r.get("url") or r.get("blogUrl"),
        "genre": r.get("genres", []),
        "cost": r.get("cost", 0),
        "free": r.get("cost", 1) == 0,
        "reach_rank": r.get("reachRank") or r.get("reach_rank"),
        "youtube_avg_views": r.get("youtubeAvgViews"),
        "spotify_playlist_count": r.get("spotifyPlaylistCount"),
        "tags": r.get("tags", []),
        "south_asian": any(
            t in (r.get("tags") or [])
            for t in ["south-asian", "indian", "bollywood", "hindi", "desi"]
        ),
    })

out_path = "data/reviewers/submithub.json"
with open(out_path, "w") as f:
    json.dump(curators, f, indent=2)

print(f"Wrote {len(curators)} curators to {out_path}")
EOF
```

Verify the count looks right (~863 records). If the schema has changed, inspect a few raw records and adjust the field mappings above.

## Step 5: Merge all reviewer sources

```bash
python3 scripts/merge_reviewers.py
```

Check the output count against the previous total (was 924 as of 2026-05-25).

## Step 6: Commit and push

```bash
cd /Users/sibyjohn/music-india-dashboard
git add data/reviewers/submithub.json data/reviewers.json
git commit -m "data: refresh SubmitHub curators $(date +%Y-%m-%d)"
git push
```

## Step 7: Set the next reminder

Use CronCreate to set a reminder in ~2 months. Update the memory file `project_india_music_dashboard.md` with the new "Last scraped" and "Next due" dates.

Also update the `submithub-refresh` SKILL.md "Last scraped" and "Next due" lines at the top of this file.

## Troubleshooting

**`Browser.find` is not defined:** The page hasn't finished loading, or you are not logged into SubmitHub. Log in first, then navigate to /curators and wait for cards to appear.

**Empty array returned:** The Minimongo collection name may have changed. Try:
```javascript
Object.keys(Mongo.Collection._collections)
```
Find the collection that looks like curator data and use that name instead.

**Schema mismatch in merge_reviewers.py:** Check what fields `merge_reviewers.py` expects by reading it, then adjust the normalisation script in Step 4.
