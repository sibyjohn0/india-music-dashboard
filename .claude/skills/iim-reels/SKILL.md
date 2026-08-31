---
name: iim-reels
description: Build Indie Music India Instagram reels and posts — the locked art/content visual system, reel structure, voice, and hard rules. Use when creating any IIM social reel, post, carousel, or caption (art pieces, The Radar, venues, gigs, YouTube rising, info/playbook).
---

# IIM Reels & Posts

The Indie Music India content system. Three content legs, each with a job:
- **Art** (object-in-wrong-place images) → gets **remembered** (identity). ~1 in 4 posts.
- **Discovery** (Radar / YouTube rising / venues) → gets **reshared** (tag the artists/venues). The reach lever.
- **Info** (release playbook etc.) → gets **saved** (utility).

Validated: the first art post (red chair in empty teal pool) became the highest-viewed post on the channel. But art doesn't earn saves/shares — discovery + info do. Balance accordingly.

## WHAT ACTUALLY WORKS — validated by views (2026-08, ~57 followers)

The data is unambiguous. Wordless art beats everything with text by 5-10x:

| Format | Views |
|---|---|
| Wordless art (single arresting object, NO on-screen text) | **400–650** (pool chair 650, telephone 548, gas 495, lamp 408) |
| Branded value carousels (Radar / venues / "5 things") | **313–476** (consistent) |
| Photo + positioning/"what we offer" text | **64–213** (worst) |
| **Art reel WITH text cards** (payphone, 4 message frames) | **26** (floor — text cards actively tank) |

**THE LOCKED RULE: art reels carry ZERO on-screen text. Not an emotional line, not a brand card, nothing.** The moment text appears it reads as an ad and gets skipped. The message goes in the CAPTION only. This overrides the older "art hook → emotional line → end frame" structure below — do NOT put text/brand cards on art reels anymore.

**Reach ≠ follows.** These reels get 650 views and 0 new followers (proven). Art = reach/brand ambiance, cheap and repeatable. Follows come from the *useful recurring* content people subscribe FOR (gig calendar, Radar, venue guides). And the real discovery engine for this business is SEO, not IG — people search "best music distributor india"; they don't follow art. Don't over-invest in IG follower-chasing.

## HARD RULES (never break)

1. **No "Swipe" / "Swipe →" on a reel** — reels don't swipe, that's carousels only.
2. **No `@indiemusicindia.co` footer on content frames** — IG already shows the handle; it's redundant clutter. Brand lands ONLY on the dedicated ◉ end frame (art reels) or the cover/CTA (info/YouTube reels).
3. **Text in the 9:16 safe zone**: keep content between y≈230 and y≈1230, left of x≈900. The top and bottom bands get covered by the Reels UI.
4. **No em dashes** anywhere (user rule).
5. **Never claim "independent / no-label / unsigned"** about any artist — unverifiable, kills credibility.

## Voice

Concrete and true, never grand. "So many nights on an album no one's heard yet" NOT "a whole life." IMI = the one who hears the unheard. Brand-lines for end frames: "We're listening" / "We hear you" / "Play it anyway" / "The scene sees you." Captions end with an invitation ("Working on something no one's heard yet? Drop it below. We hear you.") = community + reach.

## Art image recipe (generate in Google Gemini, NOT Flux — Flux gives mood not concept)

One everyday human-touched object; exactly ONE unusual thing (usually the wrong PLACE, kept fully believable/photoreal); the object carries a real-world CHARGE the place activates (danger/faith/value/time — e.g. gas cylinder = the bomb, in a public space; tiffin in a boardroom = the day job); ONE bold saturated colour + hard COMPLEMENTARY clash (object vs environment); strong geometry + depth; vary the environment every time (NOT foggy pale landscapes, NOT empty tiled corridors — those repeat).

HARD: no people, no faces (reads AI/cheap), NO recolouring living things, no animals, must feel like a real photograph. The environment must be UNLIKELY (a place the object could never naturally be), not just wrongly coloured.

## Reel structure

**Art reel (CURRENT, data-validated):** the PURE image, one slow continuous ~4.5s Ken Burns push, and NOTHING else. No text card, no emotional line, no end frame. Words live in the caption. (The older "art hook → emotional line → ◉ end frame" version tanked at 26 views — do not use it.)

**Discovery/info reel:** cover (topic, no "Swipe") → content slides (Radar artists / YouTube thumbnails / info steps, cycling accents) → CTA card ("Save this / Subscribe & share / We hear you").

## Build details

- Renderer: bespoke python + `imageio` / `imageio-ffmpeg` (bundled ffmpeg; system ffmpeg not installed). 1080x1920, 30fps, no audio (add trending audio in IG app). Ken Burns push + 0.4s cross-dissolves.
- Fonts: `~/music-india-dashboard/assets/fonts/` — BricolageGrotesque (display), Inter (body), SpaceMono-Bold (labels/mono). Indian scripts render from /System/Library/Fonts/Supplemental (Kohinoor=Devanagari, Tamil Sangam MN, KohinoorBangla, etc.).
- Brand tokens: INK bg (24,18,34), PINK accent (255,77,141), CREAM (236,231,219), YELLOW (255,210,63), MINT/VIOLET/BLUE for cycling accents. ◉ mark = pink-filled ring with cream centre.
- `scripts/render_reel.py` turns any folder of slide_*.png into a reel. `scripts/treat.py` = print-craft (duotone/halftone/grain) for art.
- Outputs land in `~/Downloads/{Images,Videos,Documents}` (Downloads auto-organises by type). Drive: per-post subfolders under "IIM Radar Posts" parent (id 18S9NrfPbqS_116oYlvu0ygxroAWzGJ5A); upload via google-workspace `uploadFileToDrive` (reads only from ~/Downloads etc., stage there first).

## Data sources (discovery)

- The Radar: `scripts/generate_radar.py` (2 English + 3 distinct Indian languages, Last.fm listeners for presence — Spotify followers are all 0 for our tier).
- Venues: `scripts/generate_venues.py "<City>"` (ranked, `data/venue_handles.json` namespaced by city).
- YouTube rising: `data/latest.json` (velocity+thumbnails). Pipeline filters non-music (categoryId==10) + DJ/folk/lyric junk, but still needs hand-curation — pick verified indie acts, like the Radar.

Always tag featured artists/venues in the caption — their reshares are the main reach lever past the cold-start wall.

## No-repeat rule (never feature the same thing twice)

`data/featured_log.json` is the persistent ledger of everything already featured: `{radar: [...], venues: {city: [...]}, topics: [...]}`. `scripts/featured_log.py` reads/writes it.
- `generate_radar.py` and `generate_venues.py` auto-exclude anything in the log, and auto-record their picks each run (use `--preview` to build without recording).
- For any OTHER social content (info reels, art themes, etc.), check `featured_topics()` first and `record_topic("slug")` after, so no topic/theme repeats either.
- The rule: nothing an audience has already seen from us comes up again. New artists, new venues, new topics, every time.
