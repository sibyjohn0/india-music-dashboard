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

For each form response worth acting on, the useful fields are: name (`0a06785b` or `13e8b51f`), Spotify link (`54892e4d`), email (`236a5cac`), Instagram (`27f16336`), YouTube (`399d51fb`).

## Adding the card

`artists/index.html` has one `.artist-grid` div of `<article class="artist-card">` blocks. New cards are appended at the end, right before the grid's closing `</div>`. Exact markup:

```html
<article class="artist-card">
  <h2>NAME</h2>
  <p class="artist-note">ONE factual sentence, using ONLY what the artist themselves stated. Never invent genre, achievements, or backstory.</p>
  <iframe src="https://open.spotify.com/embed/artist/ID?utm_source=generator" width="100%" height="352" loading="lazy" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" title="NAME on Spotify"></iframe>
  <div class="artist-links">
    <a class="sp" href="https://open.spotify.com/artist/ID" target="_blank" rel="noopener">Spotify</a>
    <!-- real YouTube/Instagram links they actually gave, same pattern -->
  </div>
</article>
```

**If they only gave a track or album link, not an artist profile:** use `/embed/track/ID` or `/embed/album/ID` exactly, don't guess at a same-named artist's profile ID — a WebSearch for "[stage name] spotify artist" can turn up several unrelated same-named artists. If the user later supplies the correct artist-profile ID directly, prefer it and swap the embed (this happened 2026-10-12 with "Jaybird").

Verify after editing: zero em dashes, JSON-LD still valid if you touched any schema (see `iim-site-overview`).

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

## Verify live

After pushing, confirm the card is actually on the deployed page — see `iim-deploy-verify`. The new card is the LAST one in the grid, easy to miss on a quick look; mention that explicitly if the user says they can't find it.
