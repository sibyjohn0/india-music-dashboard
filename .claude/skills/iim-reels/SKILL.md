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

**Art reel:** art hook (slow Ken Burns push-in on the PURE image, no text on it) → cross-dissolve → ONE emotional line on a solid card in a colour PULLED from the image → ◉ end frame (pink-filled-ring mark on INK + a brand-line + handle).

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
