# Indie Music India — Master Design System
**v2.0 · October 2026 · the single source of truth for everything we make**

This governs every surface: website, product/dashboard, social, email and outreach, decks, documents, and print. When anything conflicts, this wins. It supersedes the social-only brand kit (v1.1).

- Name: **Indie Music India** · Handle: **@indiemusicindia.co** · Site: **indiemusicindia.com**
- Contact: sibyjohn0@gmail.com · WhatsApp +91 99600 25559
- Assets: `assets/brand/` (logo lockups + mark), `assets/fonts/`, `assets/logo-anim.mp4`, `assets/poppy.css` (web tokens)

---

## 1. Foundation

**What we are.** Free tools and guides, plus a paid Artist Development Programme, for independent Indian musicians and the people around them (managers, labels, curators, brands).

**What we are about.** Everything *around* the music: the economics, the identity, the network, the release. Not the music theory, the business of being an artist in India.

**Our edge.** Credibility from named, dated sources plus India-specific truth that is expensive to fake. We help through free resources first, paid second.

**Brand personality.** Clear, warm, premium, honest. We are the one who hears the unheard. We champion the scene, we never talk down to it.

---

## 2. Logo

### 2.1 The mark
File: `logo/mark.png` (a pink vinyl / target with a centre dot and equaliser ticks). Use the file, do not redraw it.

### 2.2 Lockups
- **Horizontal** (`lockup-horizontal.png`): mark left, "Indie Music India" set in Bricolage 800 (three stacked lines) right. Use in headers, wide spaces, reel end-cards.
- **Vertical** (`lockup-vertical.png`): mark above the stacked wordmark. Use for avatars, centred placements, square spaces.
- **Mark alone**: favicons, app icons, stickers, the ◉ watermark on content.
- **Handle lockup**: the ◉ mark + `@indiemusicindia.co` in Space Mono, bottom-left of social assets.

### 2.3 Animation
`assets/logo-anim.mp4` (836×500, 30fps, ~5.3s). The mark spins and settles while the wordmark reveals, landing on the **horizontal lockup**.
- **Where it plays:** homepage load (plays **once**, does not loop), and as the **end-card on every Reel**.
- **Guardrails:** play once and rest on the static lockup; never loop it in-feed as filler; never speed-ramp, reverse, add extra effects, or re-time it; always on a cream ground; use the supplied file, never recreate the motion.

### 2.4 Usage guardrails (all logo forms)
- **Clear space:** keep free space on all sides of at least the height of the centre dot (for the full lockup, at least the mark's ring width).
- **Minimum size:** mark no smaller than 32px on screen / 10mm in print; horizontal lockup no smaller than 120px wide (wordmark stays legible).
- **Backgrounds:** place on cream `#FFF7EE`, ink `#241B2E`, white, or a calm photo area. On busy photos, sit it on a solid chip or the card.
- **Always:** place the real PNG. Keep proportions locked. Keep the pink + ink colourway.
- **Never:** recolour, add gradients to it, distort or stretch, rotate, outline, add drop-shadows beyond the built-in one, crop the rings, re-typeset the wordmark in another font, or let an AI render/redraw it. If you cannot use the real file, use text instead.

---

## 3. Colour

| Token | Hex | Role |
|---|---|---|
| Cream | `#FFF7EE` | Primary ground (light) |
| Ink | `#241B2E` | Text, borders, dark ground |
| Pink | `#FF4D8D` | Primary accent |
| Pink (AA text) | `#D8005E` | Pink used as text/controls on cream (passes 4.5:1) |
| Orange | `#FF9130` | Accent |
| Yellow | `#FFD23F` | Accent, eyebrow pills |
| Violet | `#8B5CF6` | Accent |
| Blue | `#3AA0FF` | Accent |
| Mint | `#1FCF9E` | Accent |
| Muted | `#6B6076` | Secondary text |
| White | `#FFFFFF` | Card/surface fill |

Soft tints exist for each accent (`--pink-s` etc.) for backgrounds.

**Gradients (diagonal, 3-stop):** sunset `pink→violet→blue` · grape `orange→pink→violet` · mint `mint→blue→violet`.

**Rules.** Ground is cream (light) or ink (dark/guides). **One accent or gradient per tile.** Contrast: ink text on cream/yellow/mint; cream text on ink/violet/blue/pink. **Never** yellow-on-cream or ink-on-violet. When pink is text or a control on cream, use `#D8005E` for AA contrast.

---

## 4. Typography

- **Bricolage Grotesque 800** — headlines, cover lines, big numbers. Tracking -2%.
- **Inter 400–600** — all body and reading. Line length ~65 characters.
- **Space Mono Bold, UPPERCASE, +14–18% tracking** — eyebrows, kickers, counters, the handle, tags. Never body text.

All three are free (Google Fonts, OFL). Repo copies in `assets/fonts/`. In Google Slides, add Bricolage Grotesque once via Font ▸ More fonts.

**Type scale (web, px):** display 96/72 · h1 56 · h2 40 · h3 28 · body 18–20 · small 15 · label 13 (mono, caps). Scale down proportionally on mobile.

---

## 5. Visual language

- **Cards/tiles:** 2px ink border + a **hard offset shadow** (6px on web, ~8px on 1080px social). Neo-brutalist, never soft blur.
- **Eyebrow pill:** a rounded/elliptical chip, usually yellow, ink border, Space Mono uppercase label. Sits above the headline.
- **Headline pattern:** two lines, line 1 ink, line 2 pink (the house "turn").
- **Corner circles:** accent discs bleeding off top-right and bottom-left. Never over text.
- **The ◉ mark + handle** bottom-left on content.
- **Three social archetypes:** bright promo tile · dark "FREE GUIDE" carousel cover · gradient CTA.
- Candy stickers, confetti, coins, equaliser motifs are allowed as light accents, never clutter.

---

## 6. Motion

- **Logo animation:** see 2.3.
- **Imagery (reels):** slow Ken Burns push (3–6% over the hold), gentle drift. Cross-dissolves ~0.35s. Premium and calm, never frantic.
- **Web:** entrance fades and small hover lifts on cards; nothing bouncy.
- **Timing:** ease-out for entrances, 150–300ms for UI.
- **Reduced motion:** honour `prefers-reduced-motion` everywhere; drop Ken Burns and parallax, keep static frames.

---

## 7. Tone of voice

**Voice.** Clear over clever · specific (real names, numbers, steps) · India-first (rupees, IPRS, JioSaavn) · sourced (name a source, date evergreen numbers, ranges not false precision) · honest · warm · premium not hypey · qualitative about performance.

**Hard rules.**
- **No em dashes.** Use a comma, a colon, or rewrite.
- Never "the algorithm", "engagement velocity", "distribution cycle", or hype words.
- Never "unit economics" — say "money in vs money back".
- Explain things by what people actually do (why they share, show up, pass it on), not by platform mechanics.

**The colour rule (what makes it ours).** Write the **instance, not the category**. Replace every abstract claim with one concrete, sensory example someone who was there would use.
- "Loyal fans" → "the fans who'd show up in the rain."
- "Streaming pays little" → "it pays once, then forgets you exist."
- "Gigs have hidden costs" → "you're paying for your own parking."

Two tests before anything ships: (1) Could another account or an AI have written this? If yes, kill it. (2) Did I write the category or the instance? Replace the category with the example. Lead with the most vivid concrete line, even if you wrote it as the closer.

**Lanes.** Receipts (sourced data / how-to) · Real Talk (classy, motivating, insider) · Signal (a considered, sourced news take, never the hot take).

**Say this, not that.** "a sold-out room" not "high engagement" · "the fans who show up" not "your audience base" · "money in vs money back" not "unit economics" · "it pays once then forgets you" not "low per-stream rates."

---

## 8. Photography & imagery

- **Real scenes win.** Specific, textured, real-India moments: gig crowds, DJ booths, dive bars, record stores, a yellow Kolkata taxi, instruments in hand. These consistently outperform.
- **Avoid:** generic scenics (sunrises, empty seas), dark muddy frames, and anything that reads as stock.
- Leave footage **natural** — no heavy colour grade or filter. Light polish only.
- No AI-rendered logos, faces, or text in imagery. AI (Veo etc.) is a **visual bed only**; overlay real brand text yourself.
- People are welcome in documentary scene shots; for the "object in the wrong place" art pieces, no faces.

---

## 9. Applications

### 9.1 Web / product (indiemusicindia.com, the Radar dashboard)
Driven by `assets/poppy.css`. Cream ground, ink text, candy accents, bordered cards with hard shadows, Space Mono eyebrows. One accent per section. Mobile-first, single breakpoint at 640px. AA contrast (use `#D8005E` for pink text). Honour reduced-motion.

### 9.2 Social
- **Reel:** 1080×1920. Hook in the first 1–2s. Photo background + the cream card (eyebrow pill, ink+pink headline), ◉ + handle in a free corner, ending on the logo animation. 7–25s, export silent, add trending audio in-app. Keep text in the safe zone (top ~14% / bottom ~20% are covered by the IG UI).
- **Carousel:** 1080×1350. Dark "FREE GUIDE" cover (kicker + headline + "SWIPE →") → cream teaching slides (label · counter · title · body · handle) → gradient CTA.
- **Single tile:** 1080×1440 (3:4), 165px side safe margins (clean across grid, feed, and the 9:16 boost/story crop).
- **Caption formula:** line 1 = the exact search phrase; then value; close "Save this" (educational) or a soft CTA (promo); 4–6 tight hashtags; alt text = the headline. No "link in bio" on educational posts.
- **Cadence:** ~5 Reels + 2 carousels + daily Stories + 1 artist feature weekly. Batch-produce. Optimise saves/shares/DMs, not follower count.

### 9.3 Email & outreach
Plain, warm, signed by a person. Lead with the specific reason for writing. Ink text on white/cream, one pink link accent, the horizontal lockup small at top or in the signature. No heavy templates. Same voice rules.

### 9.4 Presentations & decks
Cream or ink slides, one idea per slide, Bricolage headline + Space Mono eyebrow + Inter body. Big honest numbers. Mark bottom-corner. Same contrast rules.

### 9.5 Documents (guides, playbooks, PDFs)
Inter body at ~65 characters, Bricolage headings, Space Mono labels, pink section rules. Cover uses a lockup. Footer: handle + site.

### 9.6 Merch & print
Mark or vertical lockup, pink + ink on cream or ink. Keep clear space and minimum sizes. CMYK/spot: match pink and ink as closely as possible; never substitute a different pink.

---

## 10. Content & performance principles

- **Photo-backed beats text-only.** Never ship a plain text slide or reel.
- **Specific real-India scenes win** (observed: 126–238 views) vs generic scenics (28) and dark frames (58) and text-only cards (45–49).
- **Lead with a contrarian, true line a photo can prove.**
- **Sourcing standard:** every factual claim names a verifiable source; ranges not false precision; "last verified" date on evergreen numbers; AI drafts, a human verifies every stat and India claim.
- **What earns a post:** save-worthy (checklist, comparison, real number, genuine laugh); India-specific over generic; one idea per post; show, don't claim.

**LOCKED FACT — Spotify India payout (verified Sept 2026):** ~₹0.05–0.08/stream → 1,000 India streams ≈ ₹50–80; 1M ≈ ₹50,000–80,000. India per-stream: Apple ₹0.55–0.85, YouTube Music ₹0.40–0.60, JioSaavn ₹0.05–0.10. International (Spotify) ≈ ₹0.25–0.42. Sources: Ditto, Chartlex, Grootin, TuneCore. Never quote a per-stream number that contradicts this.

---

## 11. Accessibility

- Text contrast ≥ 4.5:1 (use `#D8005E` when pink is text on cream). Large display text ≥ 3:1.
- Never signal meaning by colour alone.
- Visible keyboard focus states on web.
- Honour `prefers-reduced-motion`.
- Alt text on every image; captions carry the message so sound-off still works.

---

## 12. Do & Don't

**Do:** place the real logo on an approved ground with clear space · lead with the concrete instance · one accent or gradient per tile · high-contrast type · photo-backed social · cite and date sources · feature real artists · overlay brand text yourself · add trending audio in-app · honour reduced motion.

**Don't:** recolour/distort/AI-render the logo or loop its animation as filler · use em dashes, "the algorithm", hype words, or "unit economics" · yellow-on-cream or ink-on-violet · post 1:1 or 4:5 social · ship text-only or dark muddy frames · quote a per-stream number that contradicts the locked figure · put "link in bio" on educational content · chase follower count over saves/shares/DMs.

---

## 13. Governance

This document is versioned. Propose changes with a reason; update the version and date on change. The live reference is `/brand/` on the site and the Claude artifact "Indie Music India — Brand Toolkit." Assets of record live in `assets/brand/` and `assets/fonts/`.
