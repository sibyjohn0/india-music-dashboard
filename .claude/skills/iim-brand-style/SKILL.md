---
name: iim-brand-style
description: Visual brand (colors, type, signature motifs) and voice/tone guidelines for indiemusicindia.com. Use whenever writing or designing anything for this site or its social accounts -- copy, new pages, images, social posts.
tools: Read, Bash, Edit, Write
---

# Brand: visual + voice

Source of truth for every color/font value below: `assets/poppy.css` (the shared stylesheet loaded on nearly every page). Re-read it directly if you need a token not listed here, don't guess.

## Palette ("poppy" theme)

```
--bg / --cream:  #FFF7EE   (warm cream page background)
--ink / --text / --border: #241B2E   (near-black, used for text AND borders/outlines)
--accent / --pink: #FF4D8D   (primary accent, used for links, CTAs, highlights)
--mint / --green: #1FCF9E
--amber / --orange: #FF9130
--yellow: #FFD23F
--blue: #3AA0FF
--violet: #8B5CF6
--muted: #6B6076   (secondary/muted text)
--surface / --card-bg: #FFFFFF
```
Each core color has a soft "-s" tint variant (`--pink-s:#FFE1EC`, `--mint-s:#D2F6EC`, `--yellow-s:#FFF3CE`, `--blue-s:#DCEEFF`, `--orange-s:#FFE7D0`, `--violet-s:#EDE4FF`) used for card/tag backgrounds.

## Typography

- **Display font** (`--font-d`): Bricolage Grotesque, weights 600/700/800 — headlines, h1/h2, logo.
- **Body font** (`--font-b`): Inter, weights 400-700 — all body copy.
- **Mono/label font** (`--font-m`): Space Mono, weights 400/700 — eyebrows, tags, buttons, filter labels, uppercase micro-labels.
- All three loaded via one Google Fonts `@import` at the top of `poppy.css`.

## Signature visual motifs

- **Hard-edged cards**: 2px solid `--ink` border, offset drop shadow in flat color, no blur — e.g. `box-shadow:4px 4px 0 var(--ink)`. This "sticker/zine" shadow (solid color, hard offset, zero blur) is the site's most distinctive recurring visual signature — don't substitute a soft/blurred shadow, it reads as generic AI-template design instead of this brand.
- Rounded corners throughout (`border-radius`) but always paired with the hard 2px border + flat offset shadow, never one without the other.
- Uppercase, letter-spaced mono-font labels for eyebrows/tags/filters (e.g. `.g-eyebrow`, `.filter-label`).
- CTAs: solid `--ink` background, white text, or `--accent` background, paired with an arrow (→).

## Voice and tone

Read a few real examples before writing new copy, don't reconstruct the voice from this description alone:
- "Copyright exists the moment you create a song, but collecting what you are owed takes a few deliberate steps. Here is the plain version." (`guides/register-music-copyright-iprs-india/`)
- "You don't need a marketing budget to promote music. You need the right channels and a plan. Here's what actually works in India." (`guides/how-to-promote-music-in-india/`)
- "1,000 streams pays you about ₹50 to ₹80. Nobody says that out loud, because everyone's selling you a playlist pitch or a PR campaign that leaves you exactly where you started." (homepage)

Characteristics: direct, second-person, plain declarative sentences, no corporate or inflated language ("industry-leading," "unlock your potential"), willing to state the unflattering truth about money/odds before the upside, specific numbers over vague claims, short sentences, no em dashes (ever — use a comma or colon), contractions are fine ("don't," "here's"), India-specific context stated plainly (rupee figures, Indian platforms, Indian cities) rather than generic global advice.

**Never:** hype language, "the algorithm," vague motivational filler, invented statistics, or an upsell that doesn't acknowledge the free alternative already exists.

## Imagery

- No stock-photo aesthetic. The homepage hero uses an animated logo video, not a photo.
- Guide pages use a `.g-hero` image slot sparingly (e.g. `/assets/guide-heroes/green-room.jpg`) — not every guide has or needs one.
- Spotify/YouTube embeds are the primary "imagery" on content pages (artist cards, video walkthroughs) — real embeds of real content, not illustrations or AI-generated images.
- If you ever need to generate a new graphic for this brand (a social post, an OG image), use the palette and hard-shadow card motif above, Bricolage Grotesque for any headline text in the image, and keep it specific to real content (a real artist, a real stat) rather than generic music-note/soundwave clip art.

## Common mistakes (do / don't)

- **Don't** default to a soft blurred drop shadow or a generic rounded-card-with-no-border look when designing anything new for this brand. **Do** use the hard-edged 2px border + flat offset shadow, that's the actual signature, not a stylistic afterthought.
- **Don't** write upbeat/hype marketing copy. **Do** match the plain, specific, sometimes bluntly honest voice shown in the examples above.
- **Don't** invent a color or font not in this list. **Do** re-check `assets/poppy.css` directly if unsure.
