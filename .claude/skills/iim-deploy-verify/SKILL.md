---
name: iim-deploy-verify
description: Verify a change to indiemusicindia.com actually landed on the live GitHub Pages deploy after pushing, without manually re-checking. Use after any push to this repo's main branch.
tools: Bash
---

# Verify a GitHub Pages deploy landed

GitHub Pages takes roughly 1-3 minutes to rebuild after a push to `main`. Don't guess, don't manually re-curl every minute, don't claim something is "live" right after pushing without checking.

## The pattern

Pick a short, unique string that only exists in your change (a new ID, a new phrase, a new link target), then block on it in a **backgrounded** Bash call:

```bash
( until curl -s "https://indiemusicindia.com/PATH/" | grep -q 'UNIQUE_MARKER'; do sleep 15; done; echo "DEPLOYED" )
```

Run this with `run_in_background: true`. You'll get a notification when it completes — don't poll it manually in the foreground, and don't use a plain blocking `sleep N` (long top-level sleeps are blocked by the harness anyway).

## After it reports DEPLOYED

Spot-check the actual content, not just presence of the marker, especially for anything that changed structure (a new card, a new section) — a string match can be a false positive if e.g. the marker exists elsewhere on the page too.

## If the user says they can't find/see something that you've confirmed is live

Two likely causes, check both before assuming something is wrong:
1. **Stale CDN/browser cache** — the deploy response headers show `cache-control: max-age=600` on this site; a hard refresh (Cmd+Shift+R) usually resolves it.
2. **It's just easy to miss** — e.g. new artist cards get appended at the very end of a long grid. Say exactly where it is rather than just asserting "it's live."
