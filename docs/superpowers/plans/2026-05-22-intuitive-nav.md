# Intuitive Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge 6 tabs to 4, add tab subtitles, collapse filter bars, and add metric tooltips to make the India Indie Music Radar dashboard intuitive for first-time visitors.

**Architecture:** Pure vanilla JS/HTML/CSS, no build step. Three files change: `index.html` (structure), `app.js` (logic), `style.css` (presentation). No test runner — verification uses `python3 -m http.server 8000` and browser console assertions after each task.

**Tech Stack:** Vanilla JS ES6+, Chart.js (Trends only, unchanged), Inter font, GitHub Pages hosting.

---

## Verification setup

Run once before starting:

```bash
cd /Users/sibyjohn/music-india-dashboard
python3 -m http.server 8000
```

Open `http://localhost:8000` in a browser. Keep it open throughout — each task ends with a browser check.

---

## Task 1: Remove Browse and Radar tabs, add subtitles to nav

**Files:**
- Modify: `index.html:22-29` (nav) and `index.html:188-252` (Browse + Radar panes)
- Modify: `style.css:31-33` (tab styles)

- [ ] **Step 1: Replace nav buttons in index.html**

Replace the entire `<nav>` block (lines 22–29):

```html
  <nav>
    <button class="tab active" data-tab="discover">
      <span class="tab-label">Discover</span>
      <span class="tab-sub">Top picks + full list</span>
    </button>
    <button class="tab" data-tab="artists">
      <span class="tab-label">Artists</span>
      <span class="tab-sub">Profiles + listener data</span>
    </button>
    <button class="tab" data-tab="trends">
      <span class="tab-label">Trends</span>
      <span class="tab-sub">Monthly charts + insights</span>
    </button>
    <button class="tab" data-tab="buzz">
      <span class="tab-label">Buzz</span>
      <span class="tab-sub">Reddit + news</span>
    </button>
  </nav>
```

- [ ] **Step 2: Remove Browse tab pane from index.html**

Delete the entire `<!-- ── BROWSE ──` section (the `<div id="tab-browse"...>` block and its contents).

- [ ] **Step 3: Remove Radar tab pane from index.html**

Delete the entire `<!-- ── RADAR ──` section (the `<div id="tab-radar"...>` block and its contents).

- [ ] **Step 4: Add tab subtitle styles to style.css**

Add after the `.tab.active { ... }` rule (line 33):

```css
.tab { display: flex; flex-direction: column; align-items: center; gap: 3px; }
.tab-label { font-size: 13px; }
.tab-sub { font-size: 10px; font-weight: 400; color: #3a3a3a; line-height: 1; transition: color .15s; }
.tab.active .tab-sub { color: var(--accent); opacity: 0.7; }
.tab:hover .tab-sub { color: var(--muted); }
```

- [ ] **Step 5: Verify in browser**

Open `http://localhost:8000`. Run in console:

```js
const tabs = document.querySelectorAll('.tab');
console.assert(tabs.length === 4, 'Should have 4 tabs');
console.assert(!document.getElementById('tab-browse'), 'Browse pane should be gone');
console.assert(!document.getElementById('tab-radar'), 'Radar pane should be gone');
console.assert(document.querySelector('.tab-sub'), 'Tab subtitles should exist');
```

Expected: 4 assertions pass. Nav shows 4 tabs each with a subtitle line.

- [ ] **Step 6: Commit**

```bash
git add index.html style.css
git commit -m "feat: merge to 4 tabs with nav subtitles — remove Browse and Radar"
```

---

## Task 2: Extend channel objects with trend and India listener data

**Files:**
- Modify: `app.js:78-113` (`buildChannels` function)

- [ ] **Step 1: Replace `buildChannels` in app.js**

Replace the entire `buildChannels` function (from `function buildChannels(videos) {` to its closing `}`):

```js
function buildChannels(videos) {
  const map = {};
  for (const v of videos) {
    const cid = v.channel_id||v.channel;
    if (!map[cid]) map[cid] = {
      id:cid, name:v.channel, thumb:v.thumbnail,
      video_count:0, total_views:0, total_velocity:0,
      total_engagement:0, total_discovery:0,
      genres:{}, languages:{}, top_video:v,
    };
    const c = map[cid];
    c.video_count++;
    c.total_views      += v.views;
    c.total_velocity   += v.velocity||0;
    c.total_engagement += v.engagement_rate||0;
    c.total_discovery  += v.discovery_score||0;
    if ((v.discovery_score||0)>(c.top_video.discovery_score||0)) c.top_video=v;
    if (v.genre)    c.genres[v.genre]       = (c.genres[v.genre]||0)+1;
    if (v.language) c.languages[v.language] = (c.languages[v.language]||0)+1;
  }
  const trackerMap = {};
  (trackerData?.artists||[]).forEach(a => { trackerMap[a.name.toLowerCase()] = a; });
  return Object.values(map).map(c=>{
    const lfm     = lfmData[c.name]||{};
    const tracker = trackerMap[c.name.toLowerCase()];
    return {
      ...c,
      avg_velocity:        Math.round(c.total_velocity/c.video_count),
      avg_engagement:      Math.round((c.total_engagement/c.video_count)*100)/100,
      avg_discovery:       Math.round((c.total_discovery/c.video_count)*10)/10,
      top_genre:           Object.entries(c.genres).sort((a,b)=>b[1]-a[1])[0]?.[0]||"Indie",
      top_lang:            Object.entries(c.languages).sort((a,b)=>b[1]-a[1])[0]?.[0]||"Hindi",
      lfm_listeners:       lfm.global_listeners||0,
      lfm_india_listeners: tracker?.latest_india_listeners||0,
      lfm_india_rank:      lfm.india_rank||null,
      trend:               tracker?.trend||null,
      multiplatform:       !!tracker,
    };
  }).sort((a,b)=>b.avg_discovery-a.avg_discovery);
}
```

- [ ] **Step 2: Verify in browser console**

Reload `http://localhost:8000`. Run:

```js
const ch = allChannels[0];
console.assert('trend' in ch, 'channel should have trend field');
console.assert('lfm_india_listeners' in ch, 'channel should have lfm_india_listeners field');
console.log('Sample channel:', ch.name, '| trend:', ch.trend, '| india listeners:', ch.lfm_india_listeners);
```

Expected: no assertion errors. Console shows channel name with trend (may be null for channels not in tracker) and india listeners.

- [ ] **Step 3: Commit**

```bash
git add app.js
git commit -m "feat: extend channel objects with trend badge and India listener data"
```

---

## Task 3: Add trend badge and Last.fm row to artist cards

**Files:**
- Modify: `app.js` — `renderArtistGrid` function
- Modify: `style.css` — add artist card Last.fm styles

- [ ] **Step 1: Add Last.fm + trend CSS to style.css**

Add after the `.artist-card-inner { cursor: pointer; }` rule (near end of file):

```css
/* ── Artist card — Last.fm row ── */
.artist-card-thumb-wrap { position: relative; }
.artist-card-trend {
  position: absolute; top: 6px; right: 6px;
  font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 20px;
}
.artist-lfm-row {
  display: flex; gap: 8px; align-items: center; flex-wrap: wrap;
  margin-top: 8px; padding-top: 8px;
  border-top: 1px solid var(--border);
  font-size: 11px;
}
.lfm-india { color: var(--accent); font-weight: 600; }
.lfm-global { color: var(--muted); }
.lfm-none { color: var(--muted); font-style: italic; }
```

- [ ] **Step 2: Update `renderArtistGrid` in app.js**

Inside `renderArtistGrid`, find the template literal that builds each card. Replace:

```js
    return `
    <div class="artist-card ${fit.type!=="none"?"artist-card-fit artist-card-"+fit.type:""}${savedClass}"
         onclick="openArtistDrawer(allChannels.find(x=>x.id==='${esc(c.id)}'))">
      <div class="artist-card-inner">
        <img class="artist-card-thumb" src="${esc(c.top_video.thumbnail||'')}" alt="" loading="lazy" />
```

with:

```js
    const TREND_TIP = "Trend vs the previous 30-day window based on Last.fm listener movement.";
    const trendBadge = c.trend
      ? `<span class="artist-card-trend trend-badge ${TREND_CLS[c.trend]} metric-tip" data-tip="${TREND_TIP}">${TREND_ICON[c.trend]} ${c.trend}</span>`
      : "";
    const lfmRow = c.lfm_listeners > 0
      ? `<div class="artist-lfm-row">
           <span class="lfm-india">${c.lfm_india_listeners > 0 ? fmt(c.lfm_india_listeners)+" India" : ""}</span>
           <span class="lfm-global">${fmt(c.lfm_listeners)} global · Last.fm</span>
         </div>`
      : `<div class="artist-lfm-row"><span class="lfm-none">Not yet on Last.fm</span></div>`;
    return `
    <div class="artist-card ${fit.type!=="none"?"artist-card-fit artist-card-"+fit.type:""}${savedClass}"
         onclick="openArtistDrawer(allChannels.find(x=>x.id==='${esc(c.id)}'))">
      <div class="artist-card-inner">
        <div class="artist-card-thumb-wrap">
          <img class="artist-card-thumb" src="${esc(c.top_video.thumbnail||'')}" alt="" loading="lazy" />
          ${trendBadge}
        </div>
```

Then inside the same card template, find the signals div and add `${lfmRow}` after it:

```js
          ${signals.length ? `<div class="artist-signals">${signals.map(s=>`<span class="signal-tag">${esc(s)}</span>`).join("")}</div>` : ""}
          ${lfmRow}
```

- [ ] **Step 3: Verify in browser**

Reload. Click Artists tab. Run in console:

```js
const cards = document.querySelectorAll('.artist-card');
console.assert(cards.length > 0, 'Artist cards should render');
const lfmRows = document.querySelectorAll('.artist-lfm-row');
console.assert(lfmRows.length === cards.length, 'Every card should have an lfm row');
console.log('Cards with trend badge:', document.querySelectorAll('.artist-card-trend').length);
```

Expected: cards render, every card has an lfm row, some cards show trend badges.

- [ ] **Step 4: Commit**

```bash
git add app.js style.css
git commit -m "feat: add trend badge and Last.fm row to artist cards"
```

---

## Task 4: Add Trend filter to Artists tab, collapse advanced filters

**Files:**
- Modify: `index.html` — Artists filter bar
- Modify: `app.js` — `applyArtistFilter`, `bindArtistControls`
- Modify: `style.css` — More expander styles

- [ ] **Step 1: Add More expander CSS to style.css**

Add after the `.toggle-btn.active { ... }` rule:

```css
/* ── More/Less filter expander ── */
.more-btn {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; color: var(--muted); padding: 9px 14px;
  font-size: 13px; font-family: inherit; cursor: pointer;
  transition: color .15s, border-color .15s; white-space: nowrap;
}
.more-btn:hover { color: var(--text); border-color: #444; }
.filter-more {
  display: flex; gap: 10px; flex-wrap: wrap;
  width: 100%; padding-top: 4px;
}
.filter-more[hidden] { display: none !important; }
```

- [ ] **Step 2: Replace Artists filter bar in index.html**

Replace the Artists `<div class="filter-bar">` block (the one inside `#tab-artists`, below the collab bar):

```html
      <div class="filter-bar">
        <input type="text" id="a-search" placeholder="Search artist…" />
        <select id="a-lang"><option value="all">All Languages</option></select>
        <select id="a-trend">
          <option value="all">All Trends</option>
          <option value="new">New</option>
          <option value="rising">Rising</option>
          <option value="stable">Stable</option>
          <option value="falling">Falling</option>
        </select>
        <button class="more-btn" id="a-more-btn">+ More ▾</button>
        <div class="filter-more" id="a-more" hidden>
          <select id="a-genre"><option value="all">All Genres</option></select>
          <select id="a-sort">
            <option value="collab_score">Sort: Collab Fit</option>
            <option value="avg_discovery">Sort: Discovery Score</option>
            <option value="avg_engagement">Sort: Engagement</option>
            <option value="avg_velocity">Sort: Velocity</option>
            <option value="total_views">Sort: Total Views</option>
            <option value="video_count">Sort: Videos</option>
          </select>
          <select id="a-min-eng">
            <option value="0">Any Engagement</option>
            <option value="1">1%+ Engagement</option>
            <option value="2">2%+ Engagement</option>
            <option value="5">5%+ Engagement</option>
          </select>
          <select id="a-min-videos">
            <option value="1">Any Video Count</option>
            <option value="2">2+ Videos</option>
            <option value="3">3+ Videos</option>
            <option value="5">5+ Videos</option>
          </select>
          <button class="toggle-btn" id="a-multiplatform" data-on="false">Multi-platform Only</button>
        </div>
      </div>
```

- [ ] **Step 3: Add hint text to collab bar in index.html**

Inside the collab bar `<div class="collab-legend">`, add after the last Language match span:

```html
          <span class="collab-hint">Cards highlight matching artists</span>
```

Add to style.css:

```css
.collab-hint { font-size: 11px; color: var(--muted); font-style: italic; margin-left: 6px; }
```

- [ ] **Step 4: Add `initMoreToggle` utility function to app.js**

Add this function after the `savePreference` function (near end of file):

```js
function initMoreToggle(btnId, panelId) {
  const btn   = document.getElementById(btnId);
  const panel = document.getElementById(panelId);
  if (!btn || !panel) return;
  btn.addEventListener('click', () => {
    const isOpen = !panel.hidden;
    panel.hidden = isOpen;
    btn.textContent = isOpen ? '+ More ▾' : '− Less ▲';
  });
}
```

- [ ] **Step 5: Update `applyArtistFilter` in app.js**

Replace the existing `applyArtistFilter` function:

```js
function applyArtistFilter() {
  const q      = document.getElementById("a-search").value.toLowerCase();
  const srt    = document.getElementById("a-sort").value;
  const gen    = document.getElementById("a-genre").value;
  const lng    = document.getElementById("a-lang").value;
  const trend  = document.getElementById("a-trend").value;
  const minEng = parseFloat(document.getElementById("a-min-eng").value)||0;
  const minVid = parseInt(document.getElementById("a-min-videos").value)||1;
  const mpOnly = document.getElementById("a-multiplatform").dataset.on==="true";
  let cs = allChannels.filter(c=>
    (!q         || c.name.toLowerCase().includes(q)) &&
    (gen==="all"|| c.top_genre===gen) &&
    (lng==="all"|| c.top_lang===lng) &&
    (trend==="all"|| c.trend===trend) &&
    c.avg_engagement >= minEng &&
    c.video_count    >= minVid &&
    (!mpOnly || c.multiplatform)
  );
  if (srt === "collab_score") {
    cs = [...cs].sort((a,b) => collabFit(b).score - collabFit(a).score);
  } else {
    cs = [...cs].sort((a,b)=>(b[srt]||0)-(a[srt]||0));
  }
  renderArtistGrid(cs);
}
```

- [ ] **Step 6: Update `bindArtistControls` in app.js to bind trend + More toggle**

Replace the `["a-search","a-sort","a-genre","a-lang","a-min-eng","a-min-videos"].forEach(...)` line with:

```js
  ["a-search","a-sort","a-genre","a-lang","a-min-eng","a-min-videos","a-trend"].forEach(id=>
    document.getElementById(id).addEventListener(id==="a-search"?"input":"change", apply));
  initMoreToggle("a-more-btn", "a-more");
```

- [ ] **Step 7: Verify in browser**

Reload. Click Artists tab. Run:

```js
console.assert(document.getElementById('a-trend'), 'Trend select should exist');
console.assert(document.getElementById('a-more'), 'More panel should exist');
console.assert(document.getElementById('a-more').hidden, 'More panel should be hidden by default');
// Change trend filter
document.getElementById('a-trend').value = 'rising';
document.getElementById('a-trend').dispatchEvent(new Event('change'));
console.log('Cards after rising filter:', document.querySelectorAll('.artist-card').length);
```

Expected: trend filter renders without error. "+ More ▾" button toggles the advanced filters.

- [ ] **Step 8: Commit**

```bash
git add index.html app.js style.css
git commit -m "feat: add trend filter to artists, collapse advanced filters behind More"
```

---

## Task 5: Restructure Discover tab HTML — add full video list section

**Files:**
- Modify: `index.html` — Discover tab pane and its filter bar

- [ ] **Step 1: Replace Discover filter bar in index.html**

Replace the Discover `<div class="filter-bar">` block (inside `#tab-discover`):

```html
      <div class="filter-bar">
        <select id="d-lang"><option value="all">All Languages</option></select>
        <select id="d-genre"><option value="all">All Genres</option></select>
        <button class="more-btn" id="d-more-btn">+ More ▾</button>
        <div class="filter-more" id="d-more" hidden>
          <select id="d-sort">
            <option value="discovery_score">Sort: Score</option>
            <option value="engagement_rate">Sort: Engagement</option>
            <option value="velocity">Sort: Velocity</option>
            <option value="views">Sort: Views</option>
          </select>
          <select id="v-min-eng">
            <option value="0">Any Engagement</option>
            <option value="1">1%+ Engagement</option>
            <option value="2">2%+ Engagement</option>
            <option value="5">5%+ Engagement</option>
          </select>
          <button class="toggle-btn" id="d-new-only" data-on="false">New Only</button>
        </div>
      </div>
```

- [ ] **Step 2: Add divider, list controls, and video list to Discover pane in index.html**

Add the following after the closing `</div>` of `.discover-body` (still inside `#tab-discover`):

```html
      <div class="discover-divider">
        <span id="d-list-label">All videos</span> — sort &amp; filter below
      </div>
      <div class="list-controls">
        <input type="text" id="v-search" placeholder="Search title or artist…" />
        <select id="v-sort">
          <option value="discovery_score">Sort: Discovery Score</option>
          <option value="engagement_rate">Sort: Engagement</option>
          <option value="velocity">Sort: Velocity</option>
          <option value="published_at">Sort: Newest</option>
          <option value="views_delta">Sort: 24h Growth</option>
          <option value="views">Sort: Views</option>
        </select>
        <select id="v-window">
          <option value="0">All Time</option>
          <option value="7">Last 7 Days</option>
          <option value="14">Last 14 Days</option>
          <option value="30">Last 30 Days</option>
        </select>
      </div>
      <div class="video-list" id="video-list"></div>
```

- [ ] **Step 3: Add divider and list-controls CSS to style.css**

Add after the `.discover-body { ... }` rule:

```css
.discover-divider {
  display: flex; align-items: center; gap: 14px;
  color: var(--muted); font-size: 12px;
  margin: 36px 0 18px;
}
.discover-divider::before,
.discover-divider::after { content: ''; flex: 1; height: 1px; background: var(--border); }
.list-controls {
  display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap;
}
.list-controls input {
  flex: 1; min-width: 200px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; color: var(--text); padding: 9px 14px;
  font-size: 13px; font-family: inherit; outline: none;
  transition: border-color .15s;
}
.list-controls input:focus { border-color: var(--accent); }
.list-controls select {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; color: var(--text); padding: 9px 14px;
  font-size: 13px; font-family: inherit; outline: none;
  transition: border-color .15s;
}
.list-controls select:focus { border-color: var(--accent); }
```

- [ ] **Step 4: Verify in browser**

Reload. Click Discover tab. Run:

```js
console.assert(document.getElementById('v-search'), 'Search input should exist in Discover');
console.assert(document.getElementById('video-list'), 'video-list container should exist in Discover');
console.assert(document.querySelector('.discover-divider'), 'Divider should exist');
```

Expected: Discover tab shows hero cards + pulse list + divider + empty list section (list not wired yet — that's Task 6).

- [ ] **Step 5: Commit**

```bash
git add index.html style.css
git commit -m "feat: add full video list section to Discover tab"
```

---

## Task 6: Wire unified Discover filter — lang/genre apply to both sections

**Files:**
- Modify: `app.js` — `renderDiscover`, `applyDiscover`, `applyVideos`, `bindDiscoverControls`, `init`

- [ ] **Step 1: Update `renderDiscover` to add visible score label to hero cards**

In `renderDiscover`, find the hero card template. Replace:

```js
        <span class="hero-score">${v.discovery_score??'—'}</span>
```

with:

```js
        <span class="hero-score">${v.discovery_score??'—'}<span class="hero-score-lbl">score</span></span>
```

Add to style.css inside the `/* ── Discover hero ──*/` section:

```css
.hero-score-lbl { font-size: 9px; font-weight: 400; opacity: 0.7; margin-left: 3px; vertical-align: middle; }
```

- [ ] **Step 2: Update `applyVideos` to read from `d-lang` and `d-genre`**

Replace the existing `applyVideos` function:

```js
function applyVideos() {
  const q      = document.getElementById("v-search").value.toLowerCase();
  const srt    = document.getElementById("v-sort").value;
  const lang   = document.getElementById("d-lang").value;
  const genre  = document.getElementById("d-genre").value;
  const win    = parseInt(document.getElementById("v-window").value)||0;
  const minEng = parseFloat(document.getElementById("v-min-eng").value)||0;
  const newOnly= document.getElementById("d-new-only").dataset.on==="true";
  const cutoff = win ? Date.now() - win*864e5 : 0;
  let vs = allVideos.filter(v=>
    (!q         || v.title.toLowerCase().includes(q)||v.channel.toLowerCase().includes(q)) &&
    (genre==="all"|| v.genre===genre) &&
    (lang==="all" || v.language===lang) &&
    (!cutoff    || new Date(v.published_at)>=cutoff) &&
    v.engagement_rate >= minEng &&
    (!newOnly   || v.is_new)
  );
  vs = [...vs].sort((a,b)=>
    srt==="published_at"?b.published_at.localeCompare(a.published_at):(b[srt]||0)-(a[srt]||0));
  document.getElementById("d-list-label").textContent =
    vs.length === allVideos.length ? `All ${allVideos.length} videos` : `${vs.length} matching`;
  renderVideoList(vs);
}
```

- [ ] **Step 3: Update `applyDiscover` to also trigger `applyVideos`**

In `applyDiscover`, add `applyVideos();` as the last line of the function body, before the closing `}`.

- [ ] **Step 4: Update `bindDiscoverControls` to bind all new controls and More toggle**

Replace the existing `bindDiscoverControls` function:

```js
function bindDiscoverControls() {
  const newBtn = document.getElementById("d-new-only");
  newBtn.addEventListener("click",()=>{
    const on = newBtn.dataset.on==="true";
    newBtn.dataset.on = String(!on);
    newBtn.classList.toggle("active", !on);
    applyDiscover();
  });
  ["d-lang","d-genre","d-sort"].forEach(id=>
    document.getElementById(id).addEventListener("change", applyDiscover));
  document.getElementById("v-search").addEventListener("input", applyVideos);
  ["v-sort","v-window","v-min-eng"].forEach(id=>
    document.getElementById(id).addEventListener("change", applyVideos));
  initMoreToggle("d-more-btn", "d-more");
}
```

- [ ] **Step 5: Remove `bindVideoControls` call from `init` in app.js**

In the `init` function, find and remove the line:

```js
  bindVideoControls();
```

- [ ] **Step 6: Render the video list on initial page load**

In the `init` function, find the line `renderVideoList(allVideos);` and keep it (it now renders into `#video-list` inside the Discover tab — that container now exists after Task 5).

- [ ] **Step 7: Verify in browser**

Reload. Click Discover tab. Run:

```js
const rows = document.querySelectorAll('.video-row');
console.assert(rows.length > 0, 'Video list should render in Discover tab');
// Change language filter
document.getElementById('d-lang').value = 'Tamil';
document.getElementById('d-lang').dispatchEvent(new Event('change'));
const heroCards = document.querySelectorAll('.hero-card');
const videoRows = document.querySelectorAll('.video-row');
console.assert(heroCards.length <= 3, 'Hero section should still show');
console.assert(videoRows.length > 0, 'Video list should update with Tamil filter');
```

Expected: full video list appears below the divider. Changing Language in the top bar updates both hero cards and the list. Search, sort, and time window filter the list only.

- [ ] **Step 8: Commit**

```bash
git add app.js
git commit -m "feat: wire unified Discover filter — lang/genre update hero and full list together"
```

---

## Task 7: Collapse Trends and Buzz filter bars

**Files:**
- Modify: `index.html` — Trends and Buzz filter bars
- Modify: `app.js` — `buildTrendToggles`, `renderBuzz`

- [ ] **Step 1: Replace Trends filter bar in index.html**

Replace the Trends `<div class="filter-bar">` block (inside `#tab-trends`):

```html
      <div class="filter-bar">
        <select id="t-months">
          <option value="6">Last 6 Months</option>
          <option value="3">Last 3 Months</option>
          <option value="12">Last 12 Months</option>
        </select>
        <button class="more-btn" id="t-more-btn">+ More ▾</button>
        <div class="filter-more" id="t-more" hidden>
          <div class="toggle-group" id="t-genre-toggles"></div>
          <div class="toggle-group" id="t-lang-toggles"></div>
        </div>
      </div>
```

- [ ] **Step 2: Replace Buzz filter bar in index.html**

Replace the Buzz `<div class="filter-bar">` block (inside `#tab-buzz`):

```html
      <div class="filter-bar">
        <select id="b-lang"><option value="all">All Languages</option></select>
        <button class="more-btn" id="b-more-btn">+ More ▾</button>
        <div class="filter-more" id="b-more" hidden>
          <select id="b-platform">
            <option value="all">All Sources</option>
            <option value="reddit">Reddit</option>
            <option value="news">News</option>
          </select>
          <button class="toggle-btn" id="b-artist-only" data-on="false">Artist Mentions Only</button>
        </div>
      </div>
```

- [ ] **Step 3: Init More toggle in `buildTrendToggles` in app.js**

At the end of `buildTrendToggles`, before the closing `}`, add:

```js
  initMoreToggle("t-more-btn", "t-more");
```

- [ ] **Step 4: Init More toggle in `renderBuzz` in app.js**

At the end of `renderBuzz`, before the closing `}`, add:

```js
  initMoreToggle("b-more-btn", "b-more");
```

- [ ] **Step 5: Reset all More panels when switching tabs**

In `goTab`, add at the very start of the function body (before `dismissWelcome()`):

```js
  document.querySelectorAll('.filter-more').forEach(p => { p.hidden = true; });
  document.querySelectorAll('.more-btn').forEach(b => { if (b.textContent.startsWith('−')) b.textContent = '+ More ▾'; });
```

- [ ] **Step 6: Verify in browser**

Click Trends tab. Run:

```js
console.assert(document.getElementById('t-more').hidden, 'Trends More panel should be hidden by default');
document.getElementById('t-more-btn').click();
console.assert(!document.getElementById('t-more').hidden, 'Trends More panel should open on click');
// Switch to Buzz tab
document.querySelector('.tab[data-tab="buzz"]').click();
console.assert(document.getElementById('t-more').hidden, 'Trends More panel should reset on tab switch');
```

Expected: all More panels start hidden, toggle on button click, reset when switching tabs.

- [ ] **Step 7: Commit**

```bash
git add index.html app.js
git commit -m "feat: collapse Trends and Buzz filter bars behind More expander"
```

---

## Task 8: Metric tooltips

**Files:**
- Modify: `style.css` — tooltip CSS
- Modify: `app.js` — tooltip spans in render functions + `initMetricTips`

- [ ] **Step 1: Add tooltip CSS to style.css**

Add at the end of the file:

```css
/* ── Metric tooltips ── */
.metric-tip {
  border-bottom: 1px dashed #444;
  cursor: help;
  position: relative;
}
.metric-tip::after {
  content: attr(data-tip);
  position: absolute;
  bottom: calc(100% + 7px);
  left: 50%;
  transform: translateX(-50%);
  background: #1e1e1e;
  border: 1px solid var(--border);
  color: #ccc;
  font-size: 11px;
  font-weight: 400;
  line-height: 1.5;
  padding: 7px 11px;
  border-radius: 8px;
  width: 220px;
  white-space: normal;
  text-align: left;
  pointer-events: none;
  opacity: 0;
  transition: opacity .15s;
  z-index: 50;
  text-transform: none;
  letter-spacing: 0;
}
.metric-tip:hover::after,
.metric-tip.tip-open::after { opacity: 1; }
```

- [ ] **Step 2: Add `initMetricTips` to app.js**

Add this function after `initMoreToggle`:

```js
function initMetricTips() {
  document.querySelector('main').addEventListener('click', e => {
    const tip = e.target.closest('.metric-tip');
    document.querySelectorAll('.metric-tip.tip-open')
      .forEach(el => el.classList.remove('tip-open'));
    if (tip) { e.stopPropagation(); tip.classList.add('tip-open'); }
  });
}
```

Call it once at the end of `init()`, after `initArtistDrawer();`:

```js
  initMetricTips();
```

- [ ] **Step 3: Add tooltip spans to pulse list in `renderDiscover`**

In the pulse-item template inside `renderDiscover`, replace:

```js
      <div class="pulse-right">
        <div class="pulse-score">${v.discovery_score??'—'}</div>
        <div class="pulse-score-label">score</div>
      </div>
```

with:

```js
      <div class="pulse-right">
        <div class="pulse-score">${v.discovery_score??'—'}</div>
        <div class="pulse-score-label"><span class="metric-tip" data-tip="Ranks how likely a video is to break through: weights engagement rate, view velocity, and recency. Higher = more momentum.">score</span></div>
      </div>
```

- [ ] **Step 4: Add tooltip spans to video list rows in `renderVideoList`**

In the video-row template inside `renderVideoList`, replace:

```js
        <div class="video-score-sub">score</div>
        <div class="video-metrics-row">
          <span class="hi">${v.engagement_rate}%</span>
          <span class="bl">${fmt(v.velocity)}/d</span>
```

with:

```js
        <div class="video-score-sub"><span class="metric-tip" data-tip="Ranks how likely a video is to break through: weights engagement rate, view velocity, and recency. Higher = more momentum.">score</span></div>
        <div class="video-metrics-row">
          <span class="hi metric-tip" data-tip="Likes + comments divided by views. Higher means the audience is actively responding, not just watching passively.">${v.engagement_rate}%</span>
          <span class="bl metric-tip" data-tip="Average views per day since publish. Shows whether a track is still gaining traction or has peaked.">${fmt(v.velocity)}/d</span>
```

- [ ] **Step 5: Add tooltip spans to artist card in `renderArtistGrid`**

In the artist card template inside `renderArtistGrid`, replace:

```js
          <div class="artist-stat-label">discovery</div>
```

with:

```js
          <div class="artist-stat-label"><span class="metric-tip" data-tip="Ranks how likely a video is to break through: weights engagement rate, view velocity, and recency. Higher = more momentum.">discovery</span></div>
```

And replace the meta div line with velocity:

```js
              <div>${fmt(c.total_views)} views · ${fmt(c.avg_velocity)}/day</div>
```

with:

```js
              <div>${fmt(c.total_views)} views · <span class="metric-tip" data-tip="Average views per day since publish. Shows whether a track is still gaining traction or has peaked.">${fmt(c.avg_velocity)}/day</span></div>
```

Also add a tooltip to the Last.fm India listeners label. In the `lfmRow` const (added in Task 3), replace:

```js
      const lfmRow = c.lfm_listeners > 0
        ? `<div class="artist-lfm-row">
             <span class="lfm-india">${c.lfm_india_listeners > 0 ? fmt(c.lfm_india_listeners)+" India" : ""}</span>
             <span class="lfm-global">${fmt(c.lfm_listeners)} global · Last.fm</span>
           </div>`
```

with:

```js
      const lfmRow = c.lfm_listeners > 0
        ? `<div class="artist-lfm-row">
             <span class="lfm-india metric-tip" data-tip="Monthly listeners on Last.fm tracked to India. Updates daily.">${c.lfm_india_listeners > 0 ? fmt(c.lfm_india_listeners)+" India" : ""}</span>
             <span class="lfm-global">${fmt(c.lfm_listeners)} global · Last.fm</span>
           </div>`
```

- [ ] **Step 6: Verify in browser**

Reload. Click Discover tab. Run:

```js
const tips = document.querySelectorAll('.metric-tip');
console.assert(tips.length > 0, 'Metric tip spans should exist');
// Simulate hover via class (CSS hover can't be triggered from console)
tips[0].classList.add('tip-open');
console.assert(tips[0].classList.contains('tip-open'), 'tip-open class should be added');
setTimeout(() => {
  const style = window.getComputedStyle(tips[0], '::after');
  console.log('Tooltip opacity:', style.opacity); // should be 1 when tip-open
}, 100);
```

Also manually hover over "score" labels in pulse list and video rows — tooltip should appear above the label.

- [ ] **Step 7: Commit**

```bash
git add app.js style.css
git commit -m "feat: add metric tooltips for score, engagement, velocity, India listeners"
```

---

## Task 9: Remove dead code and final cleanup

**Files:**
- Modify: `app.js` — remove unused functions, clean up references

- [ ] **Step 1: Remove `renderRadar`, `bindRadarControls`, `applyRadar` from app.js**

Delete the three functions (lines ~413–517 in original file):
- `const TREND_ICON = ...` and `const TREND_CLS = ...` — **keep these**, they are reused by `renderArtistGrid`
- `function renderRadar(artists) { ... }` — delete
- `function bindRadarControls() { ... }` — delete
- `function applyRadar() { ... }` — delete

- [ ] **Step 2: Remove `bindVideoControls` from app.js**

Delete the `bindVideoControls` function entirely (logic was folded into `bindDiscoverControls` in Task 6).

- [ ] **Step 3: Remove radar-related calls from `init` in app.js**

Remove these lines from `init`:
```js
  if (trackerData) renderRadar(trackerData.artists||[]);
  if (trackerData) bindRadarControls();
```

- [ ] **Step 4: Remove radar CSS from style.css**

Delete the `/* ── Radar tab ──*/` block (`.radar-body`, `.radar-grid`, `.radar-card`, `.radar-card-top`, `.radar-card-name`, `.radar-pills`, `.radar-stats`, `.radar-stat`, `.radar-stat-lbl`, `.radar-badges`, `.radar-rank`, `.radar-growth`, `.growth-pos`, `.growth-neg`, `.radar-yt-link`, `.radar-stat-val.muted`).

Keep `.trend-badge`, `.trend-new`, `.trend-up`, `.trend-flat`, `.trend-dn` — they are reused by artist cards.

- [ ] **Step 5: Remove radar responsive rules from style.css**

Delete `.radar-body { grid-template-columns: 1fr; }`, `.radar-grid { grid-template-columns: 1fr; }` from both `@media` blocks.

- [ ] **Step 6: Final browser acceptance check**

Reload `http://localhost:8000`. Run all acceptance checks:

```js
// 4 tabs with subtitles
console.assert(document.querySelectorAll('.tab').length === 4, '4 tabs');
console.assert(document.querySelector('.tab-sub'), 'Tab subtitles present');

// No Browse or Radar panes
console.assert(!document.getElementById('tab-browse'), 'No Browse tab');
console.assert(!document.getElementById('tab-radar'), 'No Radar tab');

// Discover shows hero + list
document.querySelector('.tab[data-tab="discover"]').click();
console.assert(document.querySelectorAll('.hero-card').length > 0, 'Hero cards present');
console.assert(document.querySelectorAll('.video-row').length > 0, 'Video list present');
console.assert(document.querySelector('.discover-divider'), 'Divider present');

// Artists has trend badge and lfm row
document.querySelector('.tab[data-tab="artists"]').click();
console.assert(document.querySelectorAll('.artist-lfm-row').length > 0, 'Last.fm rows on cards');

// Filter bars default to collapsed
console.assert(document.getElementById('d-more').hidden, 'Discover More hidden');
console.assert(document.getElementById('a-more').hidden, 'Artists More hidden');

// Metric tips present
console.assert(document.querySelectorAll('.metric-tip').length > 0, 'Metric tips present');

console.log('All acceptance checks passed');
```

- [ ] **Step 7: Push to GitHub Pages**

```bash
git push origin main
```

Open `https://sibyjohn0.github.io/india-music-dashboard/` and verify the live site matches.

- [ ] **Step 8: Commit any remaining cleanup**

```bash
git add app.js style.css
git commit -m "chore: remove dead Radar/Browse code after tab consolidation"
```
