# Indie Music India — context brief for Claude.ai chat (mobile/web)

Paste this whole file as your first message in a new Claude.ai chat, or save it as the custom instructions on a dedicated Claude.ai Project (Projects sync across devices, so this is the better option on mobile — set it up once from the web app and it's there on your phone too).

This is written for plain Claude.ai chat, which has no file or terminal access by default. If you've connected the GitHub or Google Workspace connector in this chat, say so and Claude can act directly; otherwise treat this as a briefing to reason from and to draft things (emails, copy, plans) that you'll apply yourself.

## What this is

**indiemusicindia.com** — a free-tools-and-content site for India's independent music scene, built and run by Siby John and Karishma Changroth. Repo: `github.com/sibyjohn0/india-music-dashboard` (the same repo also hosts an unrelated single-page dashboard product, the "India Indie Music Radar" — ignore that half unless asked about it specifically).

The site: a homepage, an Artists feature page, a Radar of rising artists, a reviewer/curator database (1,167+ entries), city venue pages, a live events calendar, a news aggregator, an industry directory, a royalty calculator, ~36 long-form guides, and a paid "programme" for artists who want a team.

## Site structure, in brief

- Hand-authored pages: homepage, `/about/`, `/programme/`, `/reviewers/`, `/industry/`, `/resources/`, `/answers/`, `/radar.html`, `/artists/`, `/featured/`
- Auto-generated daily or on-demand from scripts reading JSON data files: `/venues/*`, `/live/`, `/news/`, `/guides/*`
- A shared nav component and a bright "poppy" visual theme apply across the whole site.

## Standing rules (apply these to any draft you write for this project)

- **No em dashes, ever.** Use a comma or colon.
- **Never invent facts.** No fabricated bios, numbers, fees, statistics, or sources for anything that will be published or sent to a real person. Say "I don't have a verified figure for this" rather than make one up.
- **Clean links only** in anything going to an artist or press contact — never a tracking/redirect-wrapped link, it reads as a scam.
- Keep responses concrete and specific, not generic marketing language.

## The current "feature an artist" workflow

Two intake channels feed the Featured Artists page: direct email pitches, and a Google intake form (question: "what are you looking for" — only "get featured/promoted" or "press/feature/curator" answers count as a feature request; "working with the programme" is a different, paid-service funnel, never treat those as feature requests).

Current feature-confirmation email template:

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

Each featured artist gets one factual sentence of bio (only what they themselves said, nothing invented) plus their real Spotify/YouTube/Instagram links.

## Guide-writing philosophy

Guides on this site used to be written for Google snippet-farming (short generic sections plus an FAQ block at the bottom), not to actually help a musician finish a task. The fix, applied going forward: numbered step-by-step walkthroughs for anything procedural (registering with a rights society, using a distributor portal), real current numbers pulled from the site's own live data rather than stale round figures, and honest coverage of real tactics (e.g. Instagram edit/meme-page reposting: free if they like the song, otherwise priced like any influencer rate card, never invent specific account names or prices you can't verify) instead of generic advice.

## If you're just chatting, not executing

You can draft artist outreach replies, guide content, SEO copy, or strategy for this project directly in this format. Flag anything you're uncertain about rather than stating it as fact, and keep the standing rules above in mind for anything meant to go out publicly or to a real person.
