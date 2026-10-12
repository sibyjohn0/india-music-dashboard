---
name: iim-guide-qc
description: Rewrite a guides/*/index.html page from SEO-snippet-farming shape into an actual walkthrough that helps a musician finish a task. Use when asked to improve, QC, or rewrite a guide page, or when a guide reads as generic/templated.
tools: Read, Bash, Edit, WebSearch, WebFetch, mcp__youtube-data__getVideoDetails
---

# Guide content QC / rewrite

## The problem this fixes

Most `guides/*/index.html` pages were written for Google's "People Also Ask" snippet capture, not to help a musician actually finish the task: short H2-prose-H2-prose sections, then a bolted-on FAQ block at the bottom, no steps, no media, no sense of progress. Reference implementation (read before starting): `guides/register-music-copyright-iprs-india/index.html`, rewritten 2026-10-12.

## What to change, and what not to

- Keep the page shell exactly as-is: `<h1>`, `.g-lead`, `.tldr` box, head/meta/schema, nav, footer. Only touch the `<article>` body and, if genuinely warranted, add to (never gut) the FAQ section.
- Keep the `FAQPage` JSON-LD and "People also ask" section — it has real snippet value. Just don't let it be the only substantial content on the page.

## 1. Numbered steps for anything procedural

Where a section describes a bureaucratic/procedural task (registering for something, using a portal, filling a form), convert flat prose into:
```html
<ol style="margin:0 0 14px 20px;color:#574C63;font-size:16px;display:flex;flex-direction:column;gap:10px">
<li><b>Step label.</b> Detail.</li>
...
</ol>
```
**Research the real current process first** (WebSearch, WebFetch the official source if it's not blocking automated fetches, cross-check a second independent source). Never invent a step, fee, or portal name. If you can't verify something confidently, leave it as careful prose rather than publish false precision — e.g. "a nominal one-time fee" is fine when no source gives a verified number; don't make one up.

## 2. Verified video embeds, only where they genuinely help

Good candidates: anything with a confusing bureaucratic UI (government/society portals, distributor dashboards). Not every guide needs one — don't force it.

Process: WebSearch for a candidate, then **always verify via `mcp__youtube-data__getVideoDetails`** before embedding — check view count isn't near-zero, title actually matches the topic, channel looks credible (a real music-business education channel, not a random upload). Prefer Indian-context channels for Indian bureaucratic processes.

Embed pattern (copy exactly):
```html
<div style="position:relative;padding-bottom:56.25%;height:0;border-radius:12px;overflow:hidden;margin:0 0 14px">
<iframe src="https://www.youtube-nocookie.com/embed/VIDEO_ID" title="EXACT VIDEO TITLE" loading="lazy" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
</div>
```

## 3. Cross-link live site data instead of vague/stale claims

Don't write "a database of 1,100+ reviewers" from memory — read `data/reviewers.json` yourself and cite the current real numbers (as of 2026-10-12: 1,167 total, 381 free to pitch directly = 16 editorial + 48 podcast + 240 YouTube + 77 free SubmitHub, 17 tagged South Asian — re-verify, don't trust this snapshot blindly since the pipeline updates it). Link to `/reviewers/`, `/radar.html`, `/artists/`, `/venues/`, `/live/` only where the guide's actual topic touches that data — don't force a link that doesn't fit.

## 4. Known content gap worth checking for

As of 2026-10-12, no guide anywhere on the site covered Instagram edit/meme-page promotion (artists piggybacking on edit accounts' reach via trending-audio reposts, paid or free) until it was added to `guides/how-to-promote-music-in-india/index.html`. If a promotion-adjacent guide still lacks this and it's genuinely relevant, consider a short, honest mention: some pages repost for free if they like a song, many run it as a paid placement priced like any influencer rate card by follower count, treat "guaranteed reach" DMs with the same suspicion as pay-for-play playlists. Don't invent specific account names or price figures, you won't be able to verify them.

## After every page

1. Update `dateModified` in the Article JSON-LD and the visible "Last updated"/"Reviewed" date text to today.
2. `python3 -c "import re,json; [json.loads(s) for s in re.findall(r'<script type=\"application/ld\+json\">(.*?)</script>', open('PATH').read(), re.S)]; print('ok')"`
3. `grep -c $'\xe2\x80\x94\|\xe2\x80\x93' PATH` must print `0`.

## Git workflow

Commit in small batches (every 3-4 pages), `git fetch origin main && git rebase origin/main` before every push, retry on rejection. See `iim-site-overview` for the full pattern — this matters more here than usual since multiple QC passes may run in parallel across different guide batches.
