---
name: iim-feature-artist
description: Audit artist submissions (Gmail + Google Form) for indiemusicindia.com, add new artists to the Featured Artists page, and send the feature confirmation email. Use when asked to check submissions, feature an artist, or follow up on pitches.
tools: Read, Bash, Edit, mcp__claude_ai_Gmail__search_threads, mcp__claude_ai_Gmail__get_message, mcp__claude_ai_Gmail__get_thread, mcp__claude_ai_Gmail__reply, mcp__claude_ai_Gmail__send_message, mcp__claude_ai_Gmail__list_drafts, mcp__claude_ai_Gmail__get_draft, mcp__google-workspace__listForms, mcp__google-workspace__getFormResponses, WebFetch, WebSearch
---

# Feature an artist / audit submissions

## Two intake channels, do not confuse them

1. **Gmail inbox** (sibyjohn0@gmail.com). Search for pitch/submission-style emails (playlist/feature requests, "my music", a track link). For each candidate, check the **Sent** folder for whether a "You're featured on Indie Music India" reply, or a polite decline, was already sent — only act on genuinely unanswered ones.
2. **Google Form "IIM Intake Form"** — there are two forms with this exact name, account `gsheets` in the google-workspace MCP:
   - `1GSjWNz5ESvEFEe1TsAIdwxCeKiDwuy_HEGw12PJoD04`
   - `1M9FyAO6x_rFXz11qvYQB-fqX1ABmxdVGXhbuIRy-r74`
   Run `listForms` with query "intake" if these IDs ever change. Question ID `5b80bdde` ("what are you looking for") is the gate: **only** "Get my music featured or promoted" or "Press, feature, or curator" count as feature requests. "Working with you (the programme)" is a different, paid-service funnel — never auto-feature those, leave them alone entirely.
3. There is also a separate **"Submit Your Music" / Radar intake form** that feeds the automated Radar pipeline (`data/tracked_artists.json`), not the Artists page. Don't confuse the two forms or their purposes.

For each form response worth acting on, the useful fields are: name (`0a06785b` or `13e8b51f`), Spotify link (`54892e4d`), email (`236a5cac`), Instagram (`27f16336`), YouTube (`399d51fb`). **Also pull these if present, don't skip them:** genre (`1fbc8c44`, multi-select checkboxes), city (`641c2c4e`), language (`1ddb5b8d`) — the intake form already asks for all three, but earlier features lost this into prose-only bios instead of using it as structured data. Capture it properly now (see below).

## Adding the entry (city-carousel structure, final as of 2026-10-12)

`artists/index.html` is **not a flat grid, a genre chart, or a tap-to-expand chart** (all three were intermediate redesigns the same day, superseded) — final shape: grouped by **city/region** (the "map of the scene" axis), horizontally-scrollable carousels, **everything shown directly, no tap/toggle**. `.chart-section` blocks, one per city actually stated in at least one featured artist's bio (Assam, Bengaluru, Chandigarh, Gurgaon, Himachal, Kerala, Kolkata, Madhya Pradesh, Maharashtra, Mumbai, Rajasthan as of this writing).

**Section order (the one that stuck, after trying count-desc then alphabetical earlier the same day): "Across India" FIRST (not last — it's the biggest section by far), then Mumbai second, then every other real city by artist count descending with alphabetical tiebreak.** When you add a new city or a count changes, re-sort by this rule, don't just append at the end or keep it alphabetical.

Each `.chart-section` has an `id="city-SLUG"` and a sticky horizontal row of city-name chips (`.city-jump`, plain anchor links to those ids, no JS library) right above the carousels, in the same order as the sections — add/reorder a chip there for any new city. (An earlier A-Z single-letter strip was tried and replaced same-day: with only ~12 sections, 18+ of the 26 letters were always dead — don't reintroduce it.) Each section is a `.city-carousel` of `<article class="city-card">` cards.

**Ordering within a city: newest-SUBMITTED artist first, always append as the new first card.** This was deliberately chosen over "latest release date" on 2026-10-12 — release date needs a live Spotify API lookup (client-credentials token, per-artist API call) or a YouTube API call for non-Spotify artists, which is real ongoing effort for every future addition. Submission order is free: you already know it's "now" when you're adding someone. Explicitly don't go fetch release dates to decide placement — just insert at the front. (A Spotify Web API credentials pair does exist at `~/Downloads/music_db/.env` if release-date data is ever genuinely needed for something else, but it is NOT part of this workflow.)

**Exact markup for a new card**, inserted as the FIRST child inside the right city's `<div class="city-carousel">` (newest goes first, don't append at the end):

```html
<article class="city-card" id="SLUG">
  <h3 class="chart-name">NAME</h3>
  <!-- only if a clean single genre is stated: -->
  <span class="artist-tag">GENRE</span>
  <p class="chart-note">ONE factual sentence, using ONLY what the artist themselves stated. Never invent genre, achievements, or backstory.</p>
  <div class="chart-player"><iframe src="https://open.spotify.com/embed/artist/ID?utm_source=generator" width="100%" height="352" loading="lazy" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" title="NAME on Spotify"></iframe></div>
  <div class="artist-links">
    <a class="sp" href="https://open.spotify.com/artist/ID" target="_blank" rel="noopener">Spotify</a>
    <!-- real YouTube/Instagram links they actually gave, same pattern -->
  </div>
</article>
```

For a YouTube-only embed (no Spotify), use `height="315"` and `allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"` plus `allowfullscreen` — copy the exact pattern from an existing YouTube card ("Dhundh" or "Razdeep", both in "Across India").

- `SLUG` = lowercase name, non-alphanumeric runs collapsed to a single `-` (e.g. "KĀYA SOUND" → `k-ya-sound`). Must be unique sitewide on this page.
- **No city stated for this artist?** Use the "Across India" section at the bottom, still as the first card in it. **New city not yet represented?** Add a new `.chart-section` in its correct alphabetical position (not appended at the end) with an `id="city-SLUG"`, and update the A-Z strip for that letter if it was previously inert. A brand-new 1-artist city section is fine, that's an honest reflection of reach, don't force them into "Across India" just because the section would be small.
- There is no running chart-position number — only the per-section `<span class="chart-count">N</span>` badge in the `<h2>`, which **must be bumped by 1** when you add a card to that section (or set to `1` for a brand-new section).
- **Also add the artist to the `ItemList` schema** near the top of the file (`<script type="application/ld+json">` with `"@type":"ItemList"`): a `ListItem` with the next sequential `position`, `MusicGroup` name/sameAs/url (`https://indiemusicindia.com/artists/#SLUG`), and `genre` if known. Positions should reflect actual document order (city sections in their displayed order, newest-first within each) — don't just append at the end of the schema array. This was missed entirely for two artists earlier on 2026-10-12 (Jaybird, Xander Dote got added to the visual page but not the schema) — always do both in the same pass.

**If they only gave a track or album link, not an artist profile:** use `/embed/track/ID` or `/embed/album/ID` exactly, don't guess at a same-named artist's profile ID — a WebSearch for "[stage name] spotify artist" can turn up several unrelated same-named artists. If the user later supplies the correct artist-profile ID directly, prefer it and swap the embed (this happened 2026-10-12 with "Jaybird").

Verify after editing: zero em dashes, JSON-LD still valid, and **tag balance** — after any edit to this file specifically, sanity-check `<article>`/`<section>`/`<div>`/`<button>` open vs close counts match. Twice on 2026-10-12 a regex-based edit silently left stray/duplicated markup behind (once a whole leftover copy of the old grid, once a carousel-boundary regex that matched the wrong nested `</div>` and only partially reordered cards) — both only caught by counting tags or checking actual rendered order, not by eyeballing the diff. When reordering cards within a section specifically, verify the actual before/after order with a direct `grep`/`awk` on the city's section, don't just trust that a reverse() ran without checking its output — see `iim-site-overview`.

## The feature email

**Current template** (2026-10-12, overrides any earlier/longer version seen in old Sent mail):

```
Hi NAME,

You have been featured here: https://indiemusicindia.com/artists/
Get your badge here as well: https://indiemusicindia.com/featured/

We can also do an IG collab on the feature. You can send it to https://www.instagram.com/indiemusicindia.co/

If you ever want more than a feature, here's what we do and what it costs: https://indiemusicindia.com/tiers/

Best,
Siby
Indie Music India
```

**Always use clean direct links.** If replying to an existing thread, prefer `mcp__claude_ai_Gmail__reply`. If there's no inbound message to reply to (e.g. a Google Form submission with no corresponding email), use `send_message` directly with `to`/`subject`/`body` — don't use `create_draft` followed by sending the draft as-is, Gmail's draft composer auto-wraps links in `google.com/url?q=...` redirects, which looks like a scam. If a flawed draft like this already exists, send a clean `send_message` instead and just leave the bad draft inert (there is no delete-draft tool currently loaded).

## Common mistakes (do / don't)

- **Don't** auto-feature a form response just because it mentions wanting exposure. **Do** check the specific gating answer on question `5b80bdde` — "Working with you (the programme)" is a paid-service inquiry, not a feature request, even if the person is clearly a real artist with real music.
- **Don't** use `create_draft` and then send the draft as-is. **Do** check the draft body first (or just use `send_message` directly) — the draft composer wraps every link in `google.com/url?q=...` redirects, which reads as a scam. This happened on 2026-10-12: a fork-created draft for Xander Dote had wrapped links and had to be replaced with a clean `send_message` instead.
- **Don't** guess a Spotify artist-profile ID by searching the stage name — several unrelated artists often share a name. **Do** use exactly what the artist gave you (even a track/album embed if that's all you have), and only switch to an artist-profile embed if they (or the site owner) supply the correct ID directly.
- **Don't** invent bio details, genres, or achievements to make a card read more impressively. **Do** write one sentence using only what the artist themselves stated in their email or form response.
- **Don't** assume a missing `delete_draft` tool means you have to leave a bad situation unresolved. **Do** just send a clean replacement message — a stale, unsent draft sitting in Drafts is harmless.

## Verify live

After pushing, confirm the entry is actually on the deployed page — see `iim-deploy-verify`. It's collapsed by default inside its genre section, not visible as an open card; mention that explicitly if the user says they can't find it (and that the Spotify player only loads after tapping the row).
