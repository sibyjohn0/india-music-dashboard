---
name: iim-seo-check
description: Check Google Search Console indexing/coverage and traffic for indiemusicindia.com, and fix common causes of non-indexed or low-ranking pages. Use when asked to check SEO, indexing, rankings, or "why isn't X showing up in search".
tools: Read, Bash, Edit, WebSearch
---

# SEO / Search Console check

## Auth

OAuth token is cached at `~/.google-mcp/tokens/gsc_read.json`, credentials at `~/.google-mcp/credentials.json`. Both existing scripts reuse this token automatically — no login flow needed unless the token has expired.

## Two existing scripts

- `scripts/fetch_gsc.py` — analytics: impressions, clicks, queries, top pages. Fast.
- `scripts/fetch_gsc_coverage.py` — URL Inspection API, one call per URL in `sitemap.xml` (140+ URLs). **Takes ~15-16 minutes real time** and buffers all output until the full loop finishes — zero incremental visibility. Always run this in the background and block on the process, don't poll manually:
  ```bash
  python3 scripts/fetch_gsc_coverage.py > /tmp/coverage.txt 2>&1 &
  PID=$!
  # then, in a separate backgrounded Bash call:
  ( while ps -p $PID > /dev/null 2>&1; do sleep 10; done; echo DONE )
  ```
- For a faster, targeted check of one section (e.g. just `/guides/`), write a small variant that filters `sitemap.xml` URLs by substring before the inspect loop — see the pattern used 2026-10-12, it cut a 36-URL check down to a few minutes instead of 16.

## Coverage states, what they mean

- **Submitted and indexed** — fine, nothing to do.
- **Crawled - currently not indexed** — Google crawled it and chose not to index it. Usually a real signal: weak internal-link equity (few/no inbound links) or near-duplicate/templated content versus sibling pages. Fix the root cause (see below), then wait for Google's own recrawl schedule — **there is no API call to force a recrawl**, only the Search Console UI's manual "Request Indexing" button can accelerate it.
- **Discovered - currently not indexed** — known via sitemap, not yet crawled. Normal for new pages, not usually a problem.
- **URL is unknown to Google** — not yet discovered at all. Check it's actually in `sitemap.xml` and linked from somewhere.
- Occasional `ERROR` / `HttpError 500` on one URL is a transient Search Console API hiccup, not a real signal — just recheck that one URL later.

## Diagnosing "crawled but not indexed"

1. **Check internal link count into the page, from BOTH sources:**
   ```bash
   grep -rl 'href="/path/to/page/"' --include="*.html" . | grep -v node_modules | wc -l
   grep -rl 'path/to/page' --include="*.js" . | wc -l
   ```
   Running the `--include="*.html"` grep alone gives a false negative for anything injected by `assets/nav.js` — always check both. See `iim-site-overview` for the 2026-10-12 case where this exact mistake produced a wrong "zero internal links" conclusion.
2. **Check for near-duplicate content** against sibling pages (e.g. all 6 city venue pages sharing one boilerplate lead paragraph with only the city name swapped — this suppressed ranking even though word count and schema were fine). Fix by writing real, verified per-entity distinguishing content into the generator, not the output HTML.
3. **Fix the root cause in the generator script if the page is generated**, or in the hand-authored source page if not. Re-run the generator, verify output, commit, push (see `iim-site-overview` for the git workflow).

## Common mistakes (do / don't)

- **Don't** expect `fetch_gsc_coverage.py` to show incremental progress — it buffers all output and prints nothing until the entire loop (one API call per URL, ~140 URLs, ~15-16 minutes) finishes. **Do** run it in the background and block on the process, don't assume it's hung just because nothing printed for several minutes, but also don't run it in the foreground and wait idle.
- **Don't** treat a single `ERROR` / `HttpError 500` on one URL as a real signal. **Do** treat it as a transient API hiccup and just recheck that one URL later.
- **Don't** expect a fix to show up in the coverage check right after you push. **Do** remember Google recrawls on its own schedule (days to weeks) — confirm your fix is live on the actual page instead, and treat GSC coverage state as a lagging indicator.
- **Don't** conclude a page has no internal links just because a `grep --include="*.html"` search found none. **Do** also check `assets/nav.js` and any other `.js` file — see `iim-site-overview`.

## After a fix

Don't expect the coverage check to reflect the fix immediately — Google recrawls on its own schedule (days to weeks), not on your push. Confirm the fix is live on the actual deployed page (`iim-deploy-verify`), and treat the GSC coverage state as lagging indicator, not immediate feedback.
