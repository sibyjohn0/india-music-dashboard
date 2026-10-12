---
name: iim-social-strategy
description: Strategic layer for Indie Music India's social presence -- growth reality, the two-audience framing, how it ties to the Artists-page feature workflow, and where the detailed content-production rules live. Use when asked about social strategy, growth, or planning what to post, before reaching for iim-reels.
tools: Read, Bash
---

# Social strategy (the "why", not the "how")

For the detailed, frequently-updated content-production rulebook (exact reel structure, hard rules, what's validated by real view data), **use the `iim-reels` skill** — don't duplicate it here, read it directly. This skill is the strategic layer above it.

## Account status

Instagram **@indiemusicindia.co** (handle "indiemusicindia" was taken), Business/Blogger account, created 2026-08-02. A Facebook Page "Indie Music India" also exists (needed for Meta ads / IG business features) but has 0 followers and several settings still need fixing (see `iim-reels` / project memory for specifics if relevant).

**There is no IG API access** — Siby posts manually, and analytics are screenshot-driven (he shares an Insights screenshot, learnings get logged). Don't assume a connector can read live IG metrics unless told otherwise.

## The core strategic reality (validated, don't relitigate without new data)

- **The real discovery engine for this business is SEO, not Instagram.** People search "best music distributor india"; they don't follow an account for art. Don't over-invest in follower-chasing at the expense of the site/guides work.
- **Reach and follows are different problems.** Wordless art posts get 5-10x the views of anything with on-screen text, but reach doesn't convert to follows. Follows come from recurring, subscribable utility (the gig calendar, the Radar, venue guides) and reshares.
- **The one proven follower-growth lever: reshares via the Featured Artists pipeline.** When an artist is featured (see `iim-feature-artist`), the feature email explicitly offers an IG collab — accepting it exposes the post to the artist's own followers. This is the main lever that's actually worked, more than organic content alone.

## Two-audience framing

The account needs to pull both **music lovers** (reach, brand, via scene/art content) and **creators/artists** (saves, funnel into the site's free tools and the programme, via how-to content). The bridge between the two: discovery of real named artists, a fan saves it as taste, the featured artist reshares it to their own fans, and other artists see it and want to be featured next. Rough target mix: ~40% discovery/celebration, ~30% scene/art, ~30% creator utility — captions written to speak to both sides at once.

## Brand reference

A public brand toolkit already exists at **indiemusicindia.com/brand/** (noindex, not meant to rank, but a real shareable page) plus a markdown download at `/brand/brand-kit.md`, and `brand/MASTER-DESIGN-SYSTEM.md` in this repo. For voice/color/type specifics also see the `iim-brand-style` skill (written from the live `assets/poppy.css`, the site's shared stylesheet) — the two should agree; if they ever diverge, treat the live CSS as ground truth and flag the brand-kit doc as stale.

## Analytics learning loop

No automated IG metrics pull (the account isn't linked to a Facebook Page in a way the Graph API can use, confirmed and parked as of 2026-08-17 — don't re-attempt this without a reason to believe that's changed). When Siby shares a real Insights screenshot, read it and log real numbers rather than estimating; don't state a follower count or view count as current fact unless it was just given to you or just screenshotted.

## Common mistakes (do / don't)

- **Don't** assume reach/views on a post predicts follower growth — they're decoupled here, confirmed by real data.
- **Don't** invent or assume current follower/view counts. **Do** ask for a fresh screenshot or check if a connector is available, since this account has no live API feed.
- **Don't** put on-screen text on an art-style post (see `iim-reels` for why) — this is a locked rule from real performance data, not a stylistic preference.
- **Don't** treat IG growth as the primary goal in isolation. **Do** connect any social push back to the feature-artist pipeline and the site's own SEO/content work, that's where the actual discovery happens.
