# Intuitive Navigation Redesign

**Date:** 2026-05-22  
**Status:** Approved for implementation

## Problem

The dashboard has 6 tabs with unclear distinctions. Discover vs Browse and Artists vs Radar serve overlapping purposes that confuse first-time and returning visitors. Filter bars on every tab expose 6–7 dropdowns by default, creating an intimidating wall of controls. Metric labels (score, velocity) are unexplained.

## Approach: Merge to 4 tabs + 3 cross-tab fixes

### 1. Navigation: 6 tabs → 4 tabs

| Old | New | Change |
|-----|-----|--------|
| Discover | Discover | Absorbs Browse; hero + full list in one scroll |
| Browse | — | Removed as standalone tab |
| Artists | Artists | Absorbs Radar; gains Last.fm data on cards |
| Radar | — | Removed as standalone tab |
| Trends | Trends | No change |
| Buzz | Buzz | No change |

Each tab gets a one-line descriptor beneath its label in the nav bar:
- Discover: "Top picks + full list"
- Artists: "Profiles + listener data"
- Trends: "Monthly charts + insights"
- Buzz: "Reddit + news"

### 2. Discover tab (merged with Browse)

**Layout (top to bottom):**
1. Filter bar — Language + Genre dropdowns visible by default; all other controls (sort, time window, engagement floor, new-only toggle) behind a "+ More filters" expander
2. "Today's top picks" section — hero cards (top 3) + pulse list (4–18), unchanged
3. Horizontal divider: "All N videos — sort & filter below"
4. Full video list — search input + sort select + time window select visible; remaining filters come from the shared "+ More" state above

The Language and Genre selects at the top apply to both the curated section and the full list — changing either re-renders hero cards, pulse list, and the full video list simultaneously. Sort and time window in the list section are list-specific and do not affect the curated section.

The "+ More filters" panel collapses when the user switches tabs (state does not persist across tab changes).

**Score label:** The discovery score number gets a visible "score" label next to it inline (was unlabelled).

### 3. Artists tab (merged with Radar)

**Artist card additions:**
- Trend badge (▲ rising / ✦ new / — stable / ▼ falling) in top-right of card thumbnail area
- Last.fm row below the YouTube stats row:
  - India listeners (formatted: 12.4K)
  - Global listeners (formatted: 84K global)
  - "Not yet on Last.fm" for artists with no Last.fm match — explicit, not blank

**Filter bar changes:**
- Visible by default: search input + Language + Trend (all/rising/new/stable/falling)
- Behind "+ More": Genre, sort, engagement floor, video count, multi-platform toggle

**Collab bar:** Unchanged structure. Add right-aligned hint text: "Cards highlight matching artists" so purpose is self-evident on first visit.

### 4. Cross-tab: Collapsed filter bars

Every tab's filter bar shows 2–3 controls by default. All remaining controls collapse into a "+ More ▾" button that expands inline. Applies to Discover, Artists, Trends, Buzz.

Default visible per tab:
- Discover: Language, Genre (+ More: sort, time window, engagement floor, new-only)
- Artists: search, Language, Trend (+ More: Genre, sort, engagement floor, video count, multi-platform)
- Trends: month range (+ More: genre toggles, language toggles)
- Buzz: Language (+ More: platform, artist-only toggle)

### 5. Cross-tab: Metric tooltips

Add tooltip on hover (desktop) / tap (mobile) to the following label elements:

| Label | Tooltip text |
|-------|-------------|
| score / discovery | Ranks how likely a video is to break through: weights engagement rate, view velocity, and recency. Higher = more momentum. |
| engagement | Likes + comments divided by views. Higher means the audience is actively responding, not just watching passively. |
| velocity / /day | Average views per day since publish. Shows whether a track is still gaining traction or has peaked. |
| India listeners | Monthly listeners on Last.fm tracked to India. Updates daily. |
| rising / new / stable / falling | Trend vs the previous 30-day window based on Last.fm listener movement. |

Tooltip implementation: CSS `title` attribute for desktop hover is acceptable as a first pass; a lightweight custom tooltip (dark pill, appears above the label) is preferred for mobile coverage.

## Out of scope

- Trends tab content: no changes to charts or insights section
- Buzz tab content: no changes to feed layout or Reddit data
- Intent picker (welcome screen): kept as-is; Guide button not added (tab subtitles make it redundant)
- Data pipeline: no changes

## Files affected

| File | Change |
|------|--------|
| `index.html` | Remove `#tab-browse` and `#tab-radar` panes; add tab subtitles to nav; add tooltip attributes to metric labels |
| `app.js` | Merge Browse render/filter logic into Discover tab; merge Radar render into Artist cards; update `goTab` references; update filter bar collapse logic |
| `style.css` | Tab subtitle styles; collapsed filter bar styles; tooltip styles; Last.fm row on artist card |

## Acceptance criteria

- Navigating to the site shows 4 tabs, each with a subtitle
- Clicking Discover shows hero cards + pulse list + a divider + full sortable video list below
- Clicking Artists shows artist cards with trend badge + Last.fm row; artists without Last.fm show "Not yet on Last.fm"
- Every tab's filter bar shows 2–3 controls by default; "+ More" expands the rest
- Hovering/tapping "score", "engagement", "velocity" shows plain-English tooltip
- All existing filter/sort functionality still works (just reorganised)
- Browse and Radar tabs no longer exist in the nav
- Score label is visible on hero cards, pulse list items, and video list rows (not just a bare number)
- Changing Language or Genre in the Discover filter bar re-renders both the hero section and the full list below the divider
