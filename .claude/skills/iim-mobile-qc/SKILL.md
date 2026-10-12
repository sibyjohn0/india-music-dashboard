---
name: iim-mobile-qc
description: Audit indiemusicindia.com for mobile viewport issues and navigation consistency across page templates. Use when asked to check mobile experience, nav consistency, or run a visual QC sweep. Read-only -- report findings, don't fix in the same pass unless asked.
tools: Read, Bash, mcp__puppeteer__puppeteer_navigate, mcp__puppeteer__puppeteer_evaluate, mcp__puppeteer__puppeteer_screenshot
---

# Mobile / nav-consistency QC

Per this project's MCP hygiene rule: use **puppeteer** for this, not claude-in-chrome or playwright.

## Page templates to sample (2-3 pages each, not every URL)

1. Hand-authored full-nav: `/`, `/about/`, `/programme/`, `/reviewers/`, `/industry/`, `/resources/`, `/answers/`, `/radar.html`, `/artists/`, `/featured/`
2. Guide-generated (`build_guides.py`): e.g. `/guides/how-to-release-a-song-in-india/`
3. Venue-generated (`generate_venue_pages.py`): `/venues/`, `/venues/mumbai/`
4. `/live/`, `/news/` (daily-generated)
5. Toolkit (`build_toolkit_pages.py`, minimal single-"Home" static nav **by design**, not a bug): e.g. `/toolkit/new-release-checklist/`
6. Special/legacy: `/playbook/`, `/roadmap/` (separate interactive app, check it still links back to the main site), `/start/`, `/submit/`, `/deep-dive/`, `/tools/royalty-calculator/`

## Checks, at ~375x812 viewport

- Burger menu opens/closes, resulting mobile nav list matches other pages exactly (same items, order — the canonical list as of 2026-10-12 is `Home, Programme, Discover▾(Radar/Featured Artists/Live/Venues/News), Tools▾(Guides/Reviewers/Industry/Royalty Calculator), About`)
- No horizontal overflow: `document.documentElement.scrollWidth === document.documentElement.clientWidth` via `puppeteer_evaluate`
- Text legibility/contrast, especially on any page you know carries pre-poppy-theme dead CSS
- Tap target size on real interactive controls (not `<input type="range">` tracks, which are always visually thin by design, that's not a bug)
- iframes (Spotify/YouTube embeds, the royalty calculator) scale inside their container, don't get cut off or overflow

## Known false-positive trap

An automated contrast-walk (comparing computed text color against the nearest non-transparent ancestor background in the DOM) can misreport a page as unreadable when it isn't — it picked the wrong ancestor's background rule versus what's actually painted. **Always confirm any flagged contrast/legibility issue with an actual `puppeteer_screenshot`** before reporting it as a bug. This produced a false "dark-on-dark unreadable" flag on `/playbook/`'s mobile nav overlay on 2026-10-12 that a screenshot immediately disproved.

## Status as of 2026-10-12

Full sweep across 20 pages found zero confirmed bugs: nav fully consistent everywhere, no overflow anywhere, `/playbook/` (previously flagged broken in an earlier session) confirmed fixed, `/roadmap/` confirmed has a working link home. Re-run this skill periodically rather than assuming that result holds forever, especially after any nav.js or generator-script change.

## Report format

Prioritized list: confirmed bugs (page + exact issue + screenshot reference) vs. pages confirmed fine. Keep it tight. Don't fix anything in this pass unless explicitly asked — this is a reporting skill.
