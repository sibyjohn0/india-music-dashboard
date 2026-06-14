# India Indie Music Radar — CLAUDE.md

## Project overview

Live dashboard: https://sibyjohn0.github.io/india-music-dashboard/
Reviewer DB: https://sibyjohn0.github.io/india-music-dashboard/reviewers.html
GitHub repo: github.com/sibyjohn0/india-music-dashboard
Owner: sibyjohn0@gmail.com

Pure vanilla JS/HTML/CSS frontend (no build step). Three root files: `index.html`, `app.js`, `style.css`. Data is JSON files under `data/`, produced by Python scripts in `scripts/` and committed by GitHub Actions.

## Running locally

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

No install needed for frontend. For scripts, `pip install -r requirements.txt`.

## Pipeline architecture

### Daily (GitHub Actions, cron `0 1 * * *` = 6:30 AM IST)

`scripts/pipeline.py` runs these in order:

1. `fetch_youtube.py` → `data/latest.json`, `data/history/YYYY-MM-DD.json`, `data/monthly/YYYY-MM.json`, `data/channels.json`
2. `enrich_lastfm.py` → `data/lastfm_enrichment.json`
3. `build_radar.py` → `data/tracked_artists.json`
4. `generate_insights.py` → `data/insights.json`
5. `fetch_spotify.py` → `data/spotify_enrichment.json`
6. `fetch_social.py` → `data/social.json`

### Weekly (Sundays, same action with `--reviewers` flag)

- `fetch_reviewers_editorial.py` (DuckDuckGo, no creds)
- `fetch_reviewers_podcasts.py` (iTunes API, no creds)
- `fetch_reviewers_spotify.py` (SPOTIFY_CLIENT_ID/SECRET)
- `fetch_reviewers_youtube.py` (YOUTUBE_API_KEY, ~8,000/10,000 quota)
- `merge_reviewers.py` → `data/reviewers.json`

Reviewer sub-sources live in `data/reviewers/`: `editorial.json`, `podcasts.json`, `spotify_curators.json`, `submithub.json`, `youtube.json`.

### SubmitHub (manual only, every 2-3 months)

SubmitHub uses Meteor.js/Minimongo — all 869 curator records live in the browser's client-side store, not a server API. Cannot be auto-scraped.

**How to refresh:**
1. Open submithub.com/curators via Puppeteer MCP
2. Run in browser console: `Browser.find({name: 'all_blogs'}).fetch()[0].data`
3. Download blob to `~/Downloads/submithub_raw.json` (blob URL trick: new Blob + anchor click)
4. Run inline Python to rebuild `data/reviewers/submithub.json`
5. Run `python scripts/merge_reviewers.py`
6. Commit and push, then set a new CronCreate reminder ~2 months out

Last scraped: 2026-05-25. Next due: ~2026-07-25 (CronCreate reminder set).

## Key constants (fetch_youtube.py)

| Constant | Value | Purpose |
|---|---|---|
| SEARCH_MAX_RESULTS | 50 | Candidates per query (API max) |
| MIN_VIEWS | 300 | Low floor — indie acts debut under 1k |
| MAX_VIEWS | 5,000,000 | Excludes established artists |
| TARGET_PER_LANGUAGE | 25 | Target videos per language after balancing |
| MAX_PER_CHANNEL | 3 | Max videos per channel per language |
| LOOKBACK_DAYS | 90 | Rolling window |
| Quota cap | 8,500 units | Phase 1+2 searches stop here |

## Critical design constraints

**Channel registry (`data/channels.json`):** Phase 0 polls registered channels' upload playlists (1 unit each vs 100 for search). Phase 5 grows it organically from daily finds. Do NOT manually seed this file.

**Radar tab:** `data/tracked_artists.json` MUST come from `build_radar.py` (indie-only filter). Do NOT replace it with Last.fm `geo.getTopArtists` — that returns mainstream acts.

**Blocklists in fetch_youtube.py:** `MAJOR_LABELS` and `MAINSTREAM_ARTISTS` are checked against channel name and tags only (not description). Any change to blocklist logic needs a full re-run to verify it doesn't let mainstream acts through.

## Frontend tabs

- Discover — top picks + full video list (feeds from `latest.json`)
- Artists — profiles + listener data (feeds from `tracked_artists.json` + `lastfm_enrichment.json`)
- Trends — monthly charts + insights (feeds from `insights.json`, uses Chart.js)
- Buzz — Reddit social posts (feeds from `social.json` — currently 0 posts, needs Reddit OAuth secrets)
- Reviewers (`/reviewers.html`) — filterable by category, free/paid, South Asian, cost, search

## GitHub secrets required

| Secret | Used by |
|---|---|
| YOUTUBE_API_KEY | fetch_youtube.py, fetch_reviewers_youtube.py |
| LASTFM_API_KEY | enrich_lastfm.py |
| SPOTIFY_CLIENT_ID | fetch_spotify.py, fetch_reviewers_spotify.py |
| SPOTIFY_CLIENT_SECRET | fetch_spotify.py, fetch_reviewers_spotify.py |
| REDDIT_CLIENT_ID | fetch_social.py (Buzz tab — not yet added) |
| REDDIT_CLIENT_SECRET | fetch_social.py (Buzz tab — not yet added) |

## CCR routine

Weekly routine ID: `trig_01DbtLcfJQrCd5SKth7j63gb` — Sundays 9 AM UTC.

Auth note: CCR `sources` with a git URL requires GitHub account linked via /web-setup. Workaround: set `sources: []` and have the agent clone via PAT in step 1 (`git clone https://{token}@github.com/...`). This bypasses the GitHub account requirement.

## Reviewer database stats (as of 2026-05-25)

- Total: 924 reviewers (editorial 16, podcast 45, submithub 863, youtube 0, spotify_curator 0)
- 138 free to submit, 786 paid via SubmitHub credits (~$1/credit)
- 17 curators tagged south-asian (highest priority for Indian indie)
- reach_rank (0-100) on 862/863 SubmitHub entries

## Pipeline status file

`data/pipeline-status.json` tracks per-source status. Check `overall` key first. Failed sources appear with `status` not in `['ok', 'success', None]`.

## What not to do

- Do not use a framework or build step — the frontend is intentionally zero-dependency vanilla JS.
- Do not commit API keys or secrets to the repo.
- Do not manually edit `data/channels.json` — it is managed organically by the pipeline.
- Do not replace `tracked_artists.json` with Last.fm geo data.
