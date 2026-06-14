---
name: debug-pipeline
description: Diagnose and fix failures in the India Indie Music Radar daily pipeline. Use when a pipeline run has failed, data files look stale, or the GitHub Actions job is red.
tools: Read, Bash, Edit
---

# Debug Pipeline

Diagnose failures in the India Indie Music Radar daily data pipeline.

## Step 1: Read the status file first

```bash
cat /Users/sibyjohn/music-india-dashboard/data/pipeline-status.json | python3 -m json.tool
```

Check `overall` key. If it is not `ok`, look at `sources` for which script failed and what the error was.

## Step 2: Check the last GitHub Actions run

If the status file is not recent or is missing, check the Actions tab at github.com/sibyjohn0/india-music-dashboard/actions to see which step failed and read its logs.

## Step 3: Diagnose by source

### fetch_youtube.py failures

Common causes:
- `YOUTUBE_API_KEY` secret missing or expired -- check GitHub repo secrets
- Quota exhausted (10,000 units/day). Quota resets midnight Pacific. Check if Phase 1+2 searches exceeded 8,500 unit cap
- API response changed -- check for `keyError` or unexpected JSON shape in logs

Run locally to reproduce:
```bash
cd /Users/sibyjohn/music-india-dashboard
YOUTUBE_API_KEY=your_key python3 scripts/fetch_youtube.py
```

### enrich_lastfm.py failures

- `LASTFM_API_KEY` missing or rate-limited
- Last.fm API has no daily quota, but rate limit is ~5 requests/second

### fetch_spotify.py / fetch_reviewers_spotify.py failures

- `SPOTIFY_CLIENT_ID` or `SPOTIFY_CLIENT_SECRET` missing or expired
- Client credentials flow -- tokens expire after 1 hour but are auto-refreshed per run

### fetch_social.py failures (Buzz tab)

- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` not yet added to GitHub secrets
- Add them at: github.com/sibyjohn0/india-music-dashboard/settings/secrets/actions
- App type must be "script" -- create at reddit.com/prefs/apps

### build_radar.py failures

- Depends on `data/latest.json` and `data/lastfm_enrichment.json` existing
- If `latest.json` is empty or missing, fetch_youtube.py failed upstream

### merge_reviewers.py failures

- Check that all five source files exist under `data/reviewers/`: `editorial.json`, `podcasts.json`, `spotify_curators.json`, `submithub.json`, `youtube.json`
- A missing source file means the corresponding fetch script failed

## Step 4: Run a single script locally

Each script is standalone. Run whichever failed:

```bash
cd /Users/sibyjohn/music-india-dashboard
pip install -r requirements.txt

# Set required env vars, then:
python3 scripts/fetch_youtube.py
python3 scripts/enrich_lastfm.py
python3 scripts/build_radar.py
python3 scripts/generate_insights.py
python3 scripts/fetch_spotify.py
python3 scripts/fetch_social.py
```

Or run the full pipeline:
```bash
python3 scripts/pipeline.py
# With reviewer refresh:
python3 scripts/pipeline.py --reviewers
```

## Step 5: Check data freshness

```bash
ls -lt /Users/sibyjohn/music-india-dashboard/data/*.json | head -10
# History files:
ls -lt /Users/sibyjohn/music-india-dashboard/data/history/ | head -5
```

If today's history file is missing, fetch_youtube.py did not complete successfully.

## Step 6: Verify the frontend after a fix

```bash
cd /Users/sibyjohn/music-india-dashboard
python3 -m http.server 8000
# Open http://localhost:8000 and check each tab loads data
```

Open browser console and check for JS errors. The frontend reads JSON files directly -- a malformed JSON file will cause a silent fetch failure.

## Critical constraints to remember

- Do NOT manually edit `data/channels.json` -- it is grown organically by Phase 5 of fetch_youtube.py
- `data/tracked_artists.json` must come from `build_radar.py`, not Last.fm geo data
- Blocklists (`MAJOR_LABELS`, `MAINSTREAM_ARTISTS`) are checked against channel name and tags only
