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

## Adding the entry (chart structure, rebuilt 2026-10-12)

`artists/index.html` is **no longer a flat grid**. It's a genre-grouped countdown chart: `.chart-section` blocks (Hip-hop & Rap, Pop, Indie-pop, Rock & Alternative, Electronic, Folk & Roots, plus a "More voices on the scene" catch-all for anyone without one clean stated genre), each containing an `<ol class="chart-list">` of tap-to-expand `<li class="chart-row">` rows. All text (name, bio, links) is static HTML for SEO; the Spotify/YouTube iframe is injected by JS on first tap, not present in the markup.

**Exact markup for a new row**, inserted into the right genre's `<ol class="chart-list">` (append at the end of that section; if genre is unknown/mixed, use the "More voices on the scene" section at the bottom):

```html
<li class="chart-row" id="SLUG">
  <button type="button" class="chart-row-head" aria-expanded="false" aria-controls="panel-SLUG">
    <span class="chart-num">NN</span>
    <span class="chart-name">NAME</span>
    <!-- only in "More voices": <span class="artist-tag">GENRE</span> -->
    <!-- only if the artist's own bio/form answer states a city: -->
    <span class="chart-city">CITY</span>
    <span class="chart-chevron" aria-hidden="true">+</span>
  </button>
  <div class="chart-panel" id="panel-SLUG">
    <p class="chart-note">ONE factual sentence, using ONLY what the artist themselves stated. Never invent genre, achievements, or backstory.</p>
    <div class="chart-player" data-src="https://open.spotify.com/embed/artist/ID?utm_source=generator" data-title="NAME on Spotify"></div>
    <div class="artist-links">
      <a class="sp" href="https://open.spotify.com/artist/ID" target="_blank" rel="noopener">Spotify</a>
      <!-- real YouTube/Instagram links they actually gave, same pattern -->
    </div>
  </div>
</li>
```

- `SLUG` = lowercase name, non-alphanumeric runs collapsed to a single `-` (e.g. "KĀYA SOUND" → `k-ya-sound`). Must be unique sitewide on this page.
- `chart-num` is just the running position within the full page (continues across sections), not a real popularity ranking — never imply it's chart-position-by-popularity, there's no data backing that.
- Renumber every row after the insertion point if you're inserting mid-list rather than appending at a section's end (sequential numbers must stay in order). Easiest to just append at the very end of the target section to avoid renumbering.
- **Also add the artist to the `ItemList` schema** near the top of the file (`<script type="application/ld+json">` with `"@type":"ItemList"`): a `ListItem` with `position` (next number), `MusicGroup` name/sameAs/url (`https://indiemusicindia.com/artists/#SLUG`), and `genre` if known. This was missed for two artists on 2026-10-12 (Jaybird, Xander Dote got added to the visual page but not the schema) — don't repeat that, always do both in the same pass.
- For the YouTube-only embed type (no Spotify), copy the `data-src`/iframe-injection pattern from an existing YouTube row (e.g. "Dhundh" or "Razdeep") — the page's JS auto-detects `youtube.com` in the src and uses the right height/allow attributes.

**If they only gave a track or album link, not an artist profile:** use `/embed/track/ID` or `/embed/album/ID` exactly, don't guess at a same-named artist's profile ID — a WebSearch for "[stage name] spotify artist" can turn up several unrelated same-named artists. If the user later supplies the correct artist-profile ID directly, prefer it and swap the embed (this happened 2026-10-12 with "Jaybird").

Verify after editing: zero em dashes, JSON-LD still valid, and **tag balance** — after any edit to this file specifically, sanity-check `<article>`/`<section>`/`<li>`/`<div>`/`<button>` open vs close counts match (a botched regex edit on 2026-10-12 left 37 stray leftover `<article>` elements duplicating the whole old grid underneath the new chart; only caught by counting tags, not by eyeballing the diff). See `iim-site-overview`.

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
