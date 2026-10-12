# Indie Music India — full context brief for Claude.ai chat (mobile/web)

Paste this whole file as your first message in a new Claude.ai chat, or save it as custom instructions on a dedicated Claude.ai Project (Projects sync across devices — set it up once on web, it's there on mobile too).

Plain Claude.ai chat has no file or terminal access by default. If the GitHub or Google Workspace connector is enabled in this chat, say so and Claude can read/act directly; otherwise treat this as a full briefing to reason from and to draft things (emails, copy, plans, content) that you apply yourself afterward, in Claude Code or by hand.

## Who and what

**Siby John** and **Karishma Changroth** run **Indie Music India** (indiemusicindia.com), a free-tools-and-content site plus a paid artist-development programme for India's independent music scene. Siby: thirteen years inside platforms deciding which music gets seen — Marketing Manager at YouTube India (2022-2025, 400+ artists/labels), now Senior Creator Manager at LinkedIn. That bio line appears as the byline on every guide page.

Business model: nearly everything on the site is free (tools, database, guides, the Radar, features). The paid part is "the programme" (`/programme/`, pricing at `/tiers/`) — a small number of artists at a time get Siby and Karishma plus a specialist network (release strategy, PR, social, video, design, legal, IPRS), one month to start, no cut of the artist's music ever.

**Repo:** `github.com/sibyjohn0/india-music-dashboard`, local path (if you have CLI/connector access) `/Users/sibyjohn/music-india-dashboard`. This repo also hosts an unrelated single-page dashboard product, "India Indie Music Radar" (its own `index.html`/`app.js`/`style.css`/`data/*`, documented separately in the repo's root `CLAUDE.md`) — ignore that half unless specifically asked about it.

## Full site map

| Section | What it is |
|---|---|
| `/` | Homepage |
| `/artists/` | Featured Artists — curated spotlight, Spotify-embed cards, `ItemList` schema, ~36 artists as of 2026-10-12 |
| `/radar.html` | Daily-updated list of rising independent Indian artists (automated pipeline, YouTube/Last.fm/Spotify data) |
| `/reviewers/` | Database of 1,167 reviewers/curators/playlists: 16 editorial outlets, 48 podcasts, 240 YouTube channels, 863 on SubmitHub (77 free, rest cost SubmitHub credits), 17 tagged South Asian |
| `/venues/` + `/venues/<city>/` | Live venue listings for Mumbai, Delhi, Bengaluru, Hyderabad, Pune, Goa — regenerated daily from scraped data |
| `/live/` | Festivals & tours calendar, regenerated daily |
| `/news/` | Aggregated Indian music news, regenerated daily |
| `/industry/` | Directory of India-first labels and booking agencies |
| `/guides/*` | ~36 long-form how-to/explainer articles (see "Guides" below) |
| `/answers/` | Hub linking into the guides |
| `/resources/` | Toolkit hub: templates, the reading list, newsletters, links to everything free |
| `/toolkit/*` | ~90 individual free templates/checklists (budgets, split sheets, release checklists, etc.) |
| `/tools/royalty-calculator/` | Free Spotify/Apple/JioSaavn/YouTube per-stream royalty estimator |
| `/programme/`, `/tiers/` | The paid offering and its pricing |
| `/featured/` | The "Featured on Indie Music India" badge artists can embed on their own site/EPK |
| `/roadmap/` | A separate interactive ₹10k roadmap tool/app, has its own nav, links back to the main site |
| `/playbook/` | A long-form strategy document for artists |
| `/start/`, `/submit/` | Intake forms (programme inquiries and music submissions respectively) |
| `/about/` | About Siby and Karishma |

## Guides — philosophy and what's been fixed

Guides were originally written for Google's "People Also Ask" snippet capture: short generic H2 sections, then an FAQ block, nothing that actually walks a musician through finishing a task. Starting 2026-10-12 this is being systematically rewritten. The pattern:

1. **Numbered step-by-step walkthroughs** for anything genuinely procedural (registering with a rights society, using a distributor portal) — researched and verified against real current sources, never invented. Example: the IPRS copyright-registration guide now has a verified 6-step join process plus an embedded, vetted YouTube walkthrough.
2. **Real current numbers from the site's own live data**, not stale rounded claims — e.g. the playlist-pitching guide now cites the actual current reviewer-DB breakdown (see table above) instead of a vague "1,100+."
3. **Honest coverage of real but under-discussed tactics** — e.g. Instagram edit/meme-page promotion (artists piggybacking on edit accounts' reach via trending-audio reposts) was covered nowhere on the site until added to the promotion guide: some repost for free if they like a song, many price it like any influencer rate card by follower count, treat "guaranteed reach" DMs with the same suspicion as pay-for-play playlist scams. Never invent specific account names or prices that can't be verified.
4. The FAQ block and its schema stay — it has real search value — it just isn't allowed to be the only substantial content anymore.

This rewrite is being rolled out across all ~36 guides in batches (process-heavy guides, money/royalty-explainer guides, promotion/branding/city-scene guides).

## The "feature an artist" workflow

Two intake channels, kept separate:
1. **Direct email pitches** to Siby — check whether a reply was already sent before acting.
2. **A Google intake form** with a gating question, "what are you looking for" — only answers like "get featured/promoted" or "press/feature/curator" count as a feature request. "Working with the programme" is the separate paid-service funnel; **never** auto-feature those responses, they're asking for something else entirely.

There's also a third, unrelated form that feeds the Radar pipeline automatically — not the Artists page.

**Current feature-confirmation email** (as of 2026-10-12, short version, supersedes any older/longer template you might see in old sent mail):

> Hi NAME,
>
> You have been featured here: https://indiemusicindia.com/artists/
> Get your badge here as well: https://indiemusicindia.com/featured/
>
> We can also do an IG collab on the feature. You can send it to https://www.instagram.com/indiemusicindia.co/
>
> If you ever want more than a feature, here's what we do and what it costs: https://indiemusicindia.com/tiers/
>
> Best,
> Siby
> Indie Music India

Each card on the Artists page gets: the artist's real name/stage name, ONE factual bio sentence using only what the artist themselves stated (never invented genre, achievements, or backstory), a Spotify embed (artist profile preferred; track/album embed if that's all they gave — never guess a same-named artist's profile ID instead of the one actually given), and their real other links (YouTube/Instagram).

## SEO / indexing state (as of 2026-10-12)

35 of 36 guides are "Submitted and indexed" in Google Search Console. The one exception, the Bengaluru scene guide, was "crawled but not indexed" because it had only 1 inbound internal link versus its sibling city guides' 2 — fixed by linking all 6 city guides from the resources page; Google just hasn't recrawled it yet as of this writing (there's no way to force an instant recrawl via the API, only Search Console's manual "Request Indexing" button can speed that up). Reviewer-DB and venue-page content was also de-templatized where near-duplicate boilerplate across sibling pages was likely suppressing ranking.

## Mobile / navigation QC (as of 2026-10-12)

A full audit across every page template (hand-authored, guide-generated, venue-generated, toolkit, legacy pages like `/playbook/` and `/roadmap/`) found the shared mobile nav fully consistent everywhere, no horizontal overflow, all embeds (Spotify, YouTube, the royalty calculator) scaling correctly. `/playbook/`, flagged broken in an earlier session (dark theme, illegible text), is confirmed fixed. Re-check periodically rather than assuming this holds forever, especially after any navigation or theme change.

## Brand: visual and voice

**Palette** ("poppy" theme, from the live stylesheet): warm cream background `#FFF7EE`, near-black ink `#241B2E` (used for both text and borders), primary accent pink `#FF4D8D`, plus mint `#1FCF9E`, amber `#FF9130`, yellow `#FFD23F`, blue `#3AA0FF`, violet `#8B5CF6`, muted grey-purple `#6B6076` for secondary text. Each core color has a soft pastel-tint variant used for card/tag backgrounds.

**Type**: Bricolage Grotesque (headlines/display), Inter (body text), Space Mono (uppercase eyebrows/tags/labels/buttons).

**Signature visual motif**: hard-edged cards, a solid 2px dark border plus a flat, zero-blur, offset drop shadow in a solid color (e.g. shifted 4px right and down) — a "sticker/zine" look, never a soft blurred shadow. This is the single most distinctive, recognizable part of the visual identity; don't substitute a generic soft-shadow rounded card, it reads as off-brand immediately.

**Voice**: direct, second-person, plain declarative sentences, no corporate hype ("industry-leading," "unlock your potential") or vague motivational filler ("the algorithm"), willing to state an unflattering truth about money or odds before any upside, specific real numbers over vague claims, short sentences, contractions are fine, India-specific detail (rupee figures, Indian platforms and cities) stated plainly rather than generic global advice. Example real lines: "Copyright exists the moment you create a song, but collecting what you are owed takes a few deliberate steps. Here is the plain version." / "1,000 streams pays you about ₹50 to ₹80. Nobody says that out loud."

**Imagery**: no stock photography, no generic music-note/soundwave clip art. Real Spotify/YouTube embeds of real artists/content are the primary imagery on content pages. The homepage hero is an animated logo video, not a photo.

## Social strategy

Instagram **@indiemusicindia.co** (Business/Blogger account, created 2026-08-02). No live API feed — Siby posts manually and shares analytics as screenshots when he has them; never state a current follower/view count as fact unless freshly given.

**The real discovery engine for this business is SEO, not Instagram** — people search "best music distributor india," they don't follow an account for art content. Don't over-index on IG growth as the goal.

Validated reality: wordless art posts get far more views than anything with on-screen text on them, but that reach doesn't convert into follows. Follows come from recurring utility content (gig calendar, Radar, venue guides) and especially from **reshares when a newly-featured artist collabs on their feature post** — this is the one proven growth lever, and it's directly tied to the artist-feature workflow above, not a separate content treadmill.

Two-audience framing: content needs to pull both music lovers (reach/brand, via scene and art posts) and creators (saves/funnel, via how-to content), bridged by discovery of real named artists. Rough mix: ~40% discovery/celebration, ~30% scene/art, ~30% creator utility.

A public brand toolkit page already exists at indiemusicindia.com/brand/ if you need a shareable reference.

## Common mistakes to not repeat

- **A `grep` across only `.html` files will miss links injected by the shared JavaScript nav component** — it looked like `/artists/` had zero internal links sitewide until the actual `.js` file was checked; it was linked all along, just not in the static pre-JS HTML. Always check both when assessing "is this page actually linked from anywhere."
- **Gmail's draft composer auto-wraps links in `google.com/url?q=...` redirects**, which reads as a scam to a recipient. Always double check outgoing links are clean, direct URLs before anything is actually sent.
- **Don't guess a Spotify artist ID from a same-named search result** when the person hasn't given you their own profile link — several same-named artists often exist; use what they actually gave you (even if it's only a track/album link), or ask.
- **Never fabricate a figure, bio detail, video citation, or price** for anything public-facing. If you can't verify it, say so explicitly rather than writing confident-sounding filler.
- **Automated/heuristic checks (contrast scoring, "no video embeds found," etc.) can produce false positives.** Verify with an actual look (a screenshot, reading the real file) before reporting something as broken.

## Standing content rules

- **No em dashes, ever** — use a comma or colon.
- **Clean links only**, never tracking/redirect-wrapped, in anything going to a real person.
- Keep responses concrete and specific to this project's real numbers and real content, not generic marketing language.
- Flag uncertainty explicitly rather than stating an unverified claim as fact.

## If you're just chatting, not executing

Draft artist outreach replies, guide content, SEO copy, or strategy directly in this format, applying everything above. If you don't have a connector and can't verify something live (today's exact reviewer-DB count, a page's current indexing status, etc.), say that plainly rather than reusing a number from this brief as if it were freshly checked — this document is a snapshot from 2026-10-12, not a live feed.
