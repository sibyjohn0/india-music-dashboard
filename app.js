const DATA_URL        = "data/latest.json";
const LFM_URL         = "data/lastfm_enrichment.json";
const TRACKER_URL     = "data/tracked_artists.json";
const INSIGHTS_URL    = "data/insights.json";
const SOCIAL_URL      = "data/social.json";
const SPOTIFY_URL     = "data/spotify_enrichment.json";
const EVENTS_URL      = "data/events-paytm.json";
const EVENTS_URL_SK   = "data/events-songkick.json";
const EVENTS_URL_DT   = "data/events-district.json";
const EVENTS_URL_BMS  = "data/events-bookmyshow.json";
const EVENTS_URL_SBX  = "data/events-skillboxes.json";
const EVENTS_URL_FB   = "data/live-events.json";
const EVENTS_URL_HA   = "data/events-highape.json";
const REVIEWERS_URL       = "data/reviewers.json";
const VENUE_INSIGHTS_URL  = "data/venue-insights.json";

const LS_MY_GENRE = "iir_my_genre";
const LS_MY_LANG  = "iir_my_lang";
const LS_SAVED    = "iir_saved_artists";

// ── Analytics helper ─────────────────────────────────────────────────────────
function track(event, params) {
  if (typeof gtag === 'function') gtag('event', event, params || {});
}

// ── Formatters ────────────────────────────────────────────────────────────────
const fmt    = n => n>=1e9?(n/1e9).toFixed(1)+"B":n>=1e6?(n/1e6).toFixed(1)+"M":n>=1e3?(n/1e3).toFixed(1)+"K":String(n);
const fmtInr = n => n>=1e7?"₹"+(n/1e7).toFixed(1)+"Cr":n>=1e5?"₹"+(n/1e5).toFixed(1)+"L":n>=1e3?"₹"+(n/1e3).toFixed(1)+"K":"₹"+n;
const daysAgo= iso=>{const d=(Date.now()-new Date(iso))/864e5;return d<1?"Today":d<2?"Yesterday":d<30?Math.floor(d)+"d ago":d<365?Math.floor(d/30)+"mo ago":Math.floor(d/365)+"y ago";};
const esc    = s => String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");

const PAL = ["#a78bfa","#60a5fa","#34d399","#fbbf24","#f87171","#fb923c","#e879f9","#38bdf8","#4ade80","#c084fc"];
const LANG_COLORS = {
  Tamil:"#f87171", Telugu:"#fb923c", Kannada:"#fbbf24", Malayalam:"#34d399",
  Bengali:"#38bdf8", Punjabi:"#a78bfa", Marathi:"#e879f9", "Hindi Indie":"#60a5fa",
  Hindi:"#f472b6", English:"#4ade80", Various:"#888"
};

// ── State ─────────────────────────────────────────────────────────────────────
let allVideos=[], allChannels=[], lfmData={}, trackerData=null, spotifyData={};
let _trendsLoaded=false, _buzzLoaded=false, _insightsData=null, _socialData=null;
let _eventsData=null, _reviewersData=null, _venueInsights=null, _sourceData=null;

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  let data, insightsData = null, socialData = null;
  try {
    const NC = {cache:"no-cache"};
    const [ytRes, lfmRes, trackerRes, insightsRes, socialRes, spotifyRes, eventsRes, eventsSkRes, eventsDtRes, eventsBmsRes, eventsSbxRes, eventsFbRes, eventsHaRes, reviewersRes, venueInsightsRes] = await Promise.allSettled([
      fetch(DATA_URL, NC).then(r=>r.json()),
      fetch(LFM_URL,  NC).then(r=>r.json()).catch(()=>null),
      fetch(TRACKER_URL, NC).then(r=>r.json()).catch(()=>null),
      fetch(INSIGHTS_URL, NC).then(r=>r.json()).catch(()=>null),
      fetch(SOCIAL_URL,  NC).then(r=>r.json()).catch(()=>null),
      fetch(SPOTIFY_URL, NC).then(r=>r.json()).catch(()=>null),
      fetch(EVENTS_URL, NC).then(r=>r.json()).catch(()=>null),
      fetch(EVENTS_URL_SK, NC).then(r=>r.json()).catch(()=>null),
      fetch(EVENTS_URL_DT, NC).then(r=>r.json()).catch(()=>null),
      fetch(EVENTS_URL_BMS, NC).then(r=>r.json()).catch(()=>null),
      fetch(EVENTS_URL_SBX, NC).then(r=>r.json()).catch(()=>null),
      fetch(EVENTS_URL_FB, NC).then(r=>r.json()).catch(()=>null),
      fetch(EVENTS_URL_HA, NC).then(r=>r.json()).catch(()=>null),
      fetch(REVIEWERS_URL, NC).then(r=>r.json()).catch(()=>null),
      fetch(VENUE_INSIGHTS_URL, NC).then(r=>r.json()).catch(()=>null),
    ]);
    data = ytRes.value;
    if (lfmRes.status==="fulfilled" && lfmRes.value) lfmData = lfmRes.value.artists||{};
    if (trackerRes.status==="fulfilled") trackerData = trackerRes.value;
    insightsData = (insightsRes.status==="fulfilled" && insightsRes.value) ? insightsRes.value : null;
    socialData   = (socialRes.status==="fulfilled"   && socialRes.value)   ? socialRes.value   : null;
    if (spotifyRes?.status==="fulfilled" && spotifyRes.value) spotifyData = spotifyRes.value.enrichment||{};
    // Events: merge all sources, deduplicate by name+date+city
    const _extractEvents = d => {
      if (!d) return [];
      if (Array.isArray(d)) return d;
      if (Array.isArray(d.events)) return d.events;
      if (d.cities) return Object.values(d.cities).filter(Array.isArray).flat();
      return [];
    };
    // Track per-source counts for platform summary
    _sourceData = [
      { label: "BookMyShow", res: eventsBmsRes },
      { label: "Skillboxes", res: eventsSbxRes },
      { label: "District",   res: eventsDtRes },
      { label: "HighApe",    res: eventsHaRes },
      { label: "Paytm",      res: eventsRes },
    ].map(s => ({
      label: s.label,
      count: (s.res.status === "fulfilled" && s.res.value) ? _extractEvents(s.res.value).length : 0,
      ok:    s.res.status === "fulfilled" && !!s.res.value,
    }));
    const _rawEvents = [eventsRes, eventsSkRes, eventsDtRes, eventsBmsRes, eventsSbxRes, eventsFbRes, eventsHaRes]
      .filter(r => r.status === "fulfilled" && r.value)
      .flatMap(r => _extractEvents(r.value));
    const _seen = new Set();
    const _merged = _rawEvents.filter(e => {
      const key = `${(e.name||e.title||"").toLowerCase().trim()}|${e.date||""}|${(e.city||"").toLowerCase()}`;
      if (_seen.has(key)) return false;
      _seen.add(key);
      return true;
    });
    _eventsData = _merged.length > 0 ? { events: _merged } : null;
    _reviewersData   = (reviewersRes.status==="fulfilled"     && reviewersRes.value) ? reviewersRes.value     : null;
    _venueInsights   = (venueInsightsRes.status==="fulfilled" && venueInsightsRes.value) ? venueInsightsRes.value : null;
  } catch {
    document.querySelector("main").innerHTML =
      `<div style="text-align:center;padding:80px 0;color:#555;font-size:15px">No data yet — run the fetch script.</div>`;
    return;
  }

  allVideos   = (data.videos||[]).sort((a,b)=>(b.discovery_score||0)-(a.discovery_score||0));
  allChannels = buildChannels(allVideos);

  document.getElementById("last-updated").textContent =
    "Updated "+new Date(data.fetched_at).toLocaleDateString("en-IN",{day:"numeric",month:"short",hour:"2-digit",minute:"2-digit"});
  document.getElementById("total-badge").textContent = allVideos.length+" videos";

  populateDropdowns();
  loadPreferences();
  renderDiscover(allVideos);
  renderBreakingThisWeek();
  renderTodayEvents(_eventsData);
  renderTrendsEvents(_eventsData, _venueInsights, _sourceData);
  renderTodayReviewers(_reviewersData);
  renderTrendingGenre(allVideos);
  // breakdown bars removed — data lives in Trends tab
  renderArtistGrid(allChannels);
  renderVideoList(allVideos);
  bindTabs(insightsData, socialData);
  bindDiscoverControls();
  bindArtistControls();
  initArtistDrawer();
  initMetricTips();
  initArtistLog();
  initDiscoverFilterToggle();
  // Jump to tab if arriving via hash
  const _hash = window.location.hash.replace('#', '');
  if (['artists','trends','buzz'].includes(_hash)) goTab(_hash);

  document.getElementById("trends-toggle-btn").addEventListener("click", function() {
    const panel = document.getElementById("trends-analytics");
    const open  = panel.style.display !== "none";
    panel.style.display = open ? "none" : "block";
    this.textContent = open ? "Monthly charts & data ▾" : "Monthly charts & data ▴";
    if (!open && !_trendsLoaded) {
      _trendsLoaded = true; loadTrends(); if (_insightsData) renderInsights(_insightsData);
    }
  });
}

// ── Channel aggregation ───────────────────────────────────────────────────────
function buildChannels(videos) {
  const map = {};
  for (const v of videos) {
    const cid = v.channel_id||v.channel;
    if (!map[cid]) map[cid] = {
      id:cid, name:v.channel, thumb:v.thumbnail,
      video_count:0, total_views:0, total_velocity:0,
      total_engagement:0, total_discovery:0,
      genres:{}, languages:{}, top_video:v, latest_pub:v.published_at,
    };
    const c = map[cid];
    c.video_count++;
    c.total_views      += v.views;
    c.total_velocity   += v.velocity||0;
    c.total_engagement += v.engagement_rate||0;
    c.total_discovery  += v.discovery_score||0;
    if ((v.discovery_score||0)>(c.top_video.discovery_score||0)) c.top_video=v;
    if (v.published_at > c.latest_pub) c.latest_pub = v.published_at;
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
      latest_pub:          c.latest_pub||null,
    };
  }).sort((a,b)=>b.avg_discovery-a.avg_discovery);
}

// ── Dropdown population ───────────────────────────────────────────────────────
function populateDropdowns() {
  const genres = [...new Set(allVideos.map(v=>v.genre).filter(Boolean))].sort();
  const langs  = [...new Set(allVideos.map(v=>v.language).filter(Boolean))].sort();
  [["d-genre",genres],["a-genre",genres]].forEach(([id,opts])=>
    opts.forEach(g=>document.getElementById(id)?.add(new Option(g,g))));
  [["d-lang",langs],["a-lang",langs]].forEach(([id,opts])=>
    opts.forEach(l=>document.getElementById(id)?.add(new Option(l,l))));
}

// ── Discover ──────────────────────────────────────────────────────────────────
function renderDiscover(videos) {
  // Dedupe: max 2 per channel, take up to 6 candidates (show 3 initially on mobile)
  const seen = {}; const deduped = [];
  for (const v of videos) {
    const key = v.channel_id || v.channel;
    if ((seen[key] || 0) < 2) { deduped.push(v); seen[key] = (seen[key]||0)+1; }
    if (deduped.length >= 6) break;
  }
  const top3     = deduped.slice(0,3);
  const overflow = deduped.slice(3);

  const newCount = videos.filter(v => v.is_new).length;
  const newChip  = newCount > 0 ? ` <span class="hero-new-chip">${newCount} new</span>` : "";
  const heroLabel = document.getElementById("d-hero-label");
  if (heroLabel) heroLabel.innerHTML =
    (videos.length === allVideos.length ? "Top finds" : `Top finds — ${videos.length} matching`) + newChip;

  const cardHTML = (v, i) => `
    <a href="${esc(v.url)}" target="_blank" rel="noopener" class="hero-card">
      <img src="${esc(v.thumbnail)}" alt="" loading="lazy" />
      <div class="hero-card-overlay">
        <span class="hero-rank">#${i+1}</span>
        <div class="hero-pills">
          <span class="pill pill-genre">${esc(v.genre)}</span>
          <span class="pill pill-lang">${esc(v.language)}</span>
          ${v.is_new?'<span class="pill pill-new">NEW</span>':''}
        </div>
        <div class="hero-title">${esc(v.title)}</div>
        <div class="hero-channel">${esc(v.channel)} · ${daysAgo(v.published_at)} · ${fmt(v.views)} views</div>
      </div>
    </a>`;

  const heroCards = document.getElementById("hero-cards");
  if (heroCards) heroCards.innerHTML = top3.map((v,i) => cardHTML(v,i)).join("");

  // Show more button for overflow cards (mainly useful on mobile)
  const showMoreBtn = document.getElementById("hero-show-more");
  if (showMoreBtn) {
    if (overflow.length > 0) {
      showMoreBtn.style.display = "";
      showMoreBtn.textContent = `Show ${overflow.length} more ▾`;
      showMoreBtn.onclick = () => {
        heroCards.innerHTML += overflow.map((v,i) => cardHTML(v, i+3)).join("");
        showMoreBtn.style.display = "none";
      };
    } else {
      showMoreBtn.style.display = "none";
    }
  }
}

function bindDiscoverControls() {
  const newBtn = document.getElementById("d-new-only");
  newBtn.addEventListener("click",()=>{
    const on = newBtn.dataset.on==="true";
    newBtn.dataset.on = String(!on);
    newBtn.classList.toggle("active", !on);
    applyDiscover();
  });
  ["d-lang","d-genre","v-sort"].forEach(id=>
    document.getElementById(id).addEventListener("change", applyDiscover));
  let _searchTimer;
  document.getElementById("v-search").addEventListener("input", e => {
    applyVideos();
    clearTimeout(_searchTimer);
    _searchTimer = setTimeout(() => {
      const q = e.target.value.trim();
      if (q.length > 2) track('search', { search_term: q });
    }, 800);
  });
  ["v-window","v-min-eng"].forEach(id=>
    document.getElementById(id).addEventListener("change", applyVideos));
  initMoreToggle("d-more-btn", "d-more");

  document.getElementById("video-list").addEventListener("click", e => {
    const row = e.target.closest(".video-row");
    if (!row) return;
    const title = row.querySelector(".video-row-title")?.textContent || "";
    const channel = row.querySelector(".video-row-channel")?.textContent || "";
    track('video_click', { video_title: title, artist_name: channel });
  });
}

function applyDiscover() {
  const lang    = document.getElementById("d-lang").value;
  const genre   = document.getElementById("d-genre").value;
  const srt     = document.getElementById("v-sort").value;
  const newOnly = document.getElementById("d-new-only").dataset.on==="true";
  let vs = allVideos.filter(v=>
    (lang==="all"  || v.language===lang) &&
    (genre==="all" || v.genre===genre) &&
    (!newOnly || v.is_new)
  );
  vs = [...vs].sort((a,b)=>
    srt==="published_at"?b.published_at.localeCompare(a.published_at):(b[srt]||0)-(a[srt]||0));
  renderDiscover(vs);
  applyVideos();
}

// ── Breaking this week (channel subscriber growth from history files) ─────────
async function renderBreakingThisWeek() {
  const wrap = document.getElementById("breaking-cards");
  if (!wrap) return;

  // Find today and 7 days ago dates
  const now     = new Date();
  const todayStr = now.toISOString().slice(0,10);
  const weekAgo  = new Date(now - 7 * 864e5);

  // Find available history files: today and nearest older file
  const candidates = [];
  for (let i=0; i<=2; i++) {
    const d = new Date(now - i*864e5);
    candidates.push(d.toISOString().slice(0,10));
  }

  let latestSnap = null, oldSnap = null;
  for (const dateStr of candidates) {
    const r = await fetch(`data/history/${dateStr}.json`, {cache:"no-cache"}).catch(()=>null);
    if (r && r.ok) { try { latestSnap = await r.json(); break; } catch {} }
  }

  // Try to get a snapshot from ~7 days ago
  for (let daysBack = 6; daysBack <= 9; daysBack++) {
    const d = new Date(now - daysBack * 864e5);
    const dateStr = d.toISOString().slice(0,10);
    const r = await fetch(`data/history/${dateStr}.json`, {cache:"no-cache"}).catch(()=>null);
    if (r && r.ok) { try { oldSnap = await r.json(); break; } catch {} }
  }

  // Build growth map from channels.json data by comparing video counts or use latest.json
  // History files contain videos array — compute per-channel view totals
  if (!latestSnap || !latestSnap.videos || !latestSnap.videos.length) {
    wrap.innerHTML = `<div class="breaking-loading">No history data yet — will populate after a few daily runs.</div>`;
    return;
  }

  // Aggregate views per channel in latest snapshot
  const latestByChannel = {};
  for (const v of latestSnap.videos) {
    const cid = v.channel_id || v.channel;
    if (!latestByChannel[cid]) latestByChannel[cid] = {name: v.channel, views: 0, count: 0, language: v.language, genre: v.genre};
    latestByChannel[cid].views += v.views || 0;
    latestByChannel[cid].count++;
  }

  // Aggregate views per channel in old snapshot
  const oldByChannel = {};
  if (oldSnap && oldSnap.videos) {
    for (const v of oldSnap.videos) {
      const cid = v.channel_id || v.channel;
      if (!oldByChannel[cid]) oldByChannel[cid] = {views: 0};
      oldByChannel[cid].views += v.views || 0;
    }
  }

  // Compute growth — sort by views delta
  const growth = Object.entries(latestByChannel).map(([cid, cur]) => {
    const old = oldByChannel[cid];
    const delta = old ? cur.views - old.views : cur.views;
    const pct   = old && old.views > 0 ? Math.round(delta / old.views * 100) : null;
    return { cid, name: cur.name, language: cur.language, genre: cur.genre, delta, pct, totalViews: cur.views };
  }).filter(c => c.delta > 0)
    .sort((a,b) => b.delta - a.delta)
    .slice(0,3);

  if (!growth.length) {
    // Fallback: show top 3 channels by avg discovery score from current data
    const top3 = allChannels.slice(0, 3);
    if (!top3.length) {
      wrap.innerHTML = `<div class="breaking-loading">No channel data available yet.</div>`;
      return;
    }
    wrap.innerHTML = top3.map(c => `<div class="breaking-card">
      <div class="breaking-card-top">
        <div class="breaking-card-name" title="${esc(c.name)}">${esc(c.name)}</div>
        <span class="breaking-platform-icon" title="YouTube">▶</span>
      </div>
      <div class="breaking-card-pill">
        <span class="pill pill-genre">${esc(c.top_genre||"Indie")}</span>
        <span class="pill pill-lang">${esc(c.top_lang||"")}</span>
      </div>
      <div class="breaking-growth">Top scorer this week</div>
      <div class="breaking-growth-label">Discovery score: ${c.avg_discovery}</div>
    </div>`).join("");
    return;
  }

  const PLATFORM_ICON = "▶"; // YouTube
  wrap.innerHTML = growth.map(c => {
    const growthLabel = c.delta > 0
      ? `+${fmt(c.delta)} views this week`
      : `${fmt(c.delta)} views this week`;
    const pctLabel = c.pct !== null ? ` (+${c.pct}%)` : "";
    return `<div class="breaking-card">
      <div class="breaking-card-top">
        <div class="breaking-card-name" title="${esc(c.name)}">${esc(c.name)}</div>
        <span class="breaking-platform-icon" title="YouTube">${PLATFORM_ICON}</span>
      </div>
      <div class="breaking-card-pill">
        <span class="pill pill-genre">${esc(c.genre||"Indie")}</span>
        <span class="pill pill-lang">${esc(c.language||"")}</span>
      </div>
      <div class="breaking-growth">${growthLabel}${pctLabel}</div>
      <div class="breaking-growth-label">compared to last week</div>
    </div>`;
  }).join("");
}

// ── Trending genre signal ─────────────────────────────────────────────────────
function renderTrendingGenre(videos) {
  const el = document.getElementById("today-trending-genre");
  if (!el || !videos.length) return;
  const topVideos = videos.slice(0, 20);
  const genreCounts = {};
  const genreLangCounts = {};
  for (const v of topVideos) {
    if (v.genre) {
      genreCounts[v.genre] = (genreCounts[v.genre]||0)+1;
      const key = [v.language, v.genre].filter(Boolean).join(" ");
      if (key) genreLangCounts[key] = (genreLangCounts[key]||0)+1;
    }
  }
  // Prefer the most common language+genre combo if it's clear
  const topCombo = Object.entries(genreLangCounts).sort((a,b)=>b[1]-a[1])[0];
  const topGenre = Object.entries(genreCounts).sort((a,b)=>b[1]-a[1])[0];
  if (topCombo && topCombo[1] >= 3) {
    el.innerHTML = `<span class="trending-genre-pill">${esc(topCombo[0])} is moving this week</span>`;
  } else if (topGenre) {
    el.innerHTML = `<span class="trending-genre-pill">${esc(topGenre[0])} is moving this week</span>`;
  }
}

// ── Today: Events section ─────────────────────────────────────────────────────
function renderTodayEvents(data) {
  const el = document.getElementById("today-events");
  if (!el) return;

  // Flatten events from either {cities:{...}} or {events:[...]} or array structures
  const events = [];
  if (data && data.cities) {
    for (const city of Object.values(data.cities)) {
      if (Array.isArray(city)) {
        for (const ev of city) events.push(ev);
      }
    }
  } else if (data && Array.isArray(data.events)) {
    events.push(...data.events);
  } else if (Array.isArray(data)) {
    events.push(...data);
  }

  // Filter to upcoming events (today or future, within 90 days)
  const now = Date.now();
  const upcoming = events.filter(e => {
    if (!e.date) return true;
    const d = new Date(e.date);
    return d >= now - 864e5 && d <= now + 90 * 864e5;
  }).sort((a, b) => {
    if (!a.date) return 1;
    if (!b.date) return -1;
    return new Date(a.date) - new Date(b.date);
  }).slice(0, 4);

  if (!upcoming.length) {
    el.innerHTML = `<div class="act-empty">No upcoming shows found — check back soon</div>`;
    return;
  }

  el.innerHTML = `<div class="events-grid">${upcoming.map(e => {
    const url   = e.url || e.link || "https://insider.in";
    const name  = e.name || e.title || e.event || "Upcoming show";
    const city  = e.city || e.venue_city || "";
    const venue = e.venue || e.venue_name || "";
    const priceMin = e.price_min || e.min_price;
    const priceMax = e.price_max || e.max_price;
    const priceLabel = priceMin
      ? (priceMax && priceMax !== priceMin ? `₹${priceMin}–₹${priceMax}` : `from ₹${priceMin}`)
      : (e.price ? `₹${e.price}` : "");
    const date = e.date
      ? new Date(e.date).toLocaleDateString("en-IN", {day:"numeric", month:"short", weekday:"short"})
      : "";
    const metaParts = [date, venue, city, priceLabel].filter(Boolean);
    return `<a class="event-card" href="${esc(url)}" target="_blank" rel="noopener">
      <div class="event-card-name">${esc(name)}</div>
      ${metaParts.length ? `<div class="event-card-meta">${esc(metaParts.join(" · "))}</div>` : ""}
    </a>`;
  }).join("")}</div>`;
}

// ── Trends: Upcoming Shows full list ─────────────────────────────────────────
function renderTrendsEvents(data, venueInsights, sourceData) {
  const el      = document.getElementById("shows-list");
  const pillsEl = document.getElementById("shows-city-pills");
  if (!el) return;

  // Platform source summary
  const platformEl = document.getElementById("platform-summary");
  if (platformEl && sourceData) {
    platformEl.innerHTML = sourceData.map(s => {
      const cls = s.count > 0 ? "platform-pill active" : "platform-pill dead";
      return `<span class="${cls}">${s.label} <strong>${s.count > 0 ? s.count : "—"}</strong></span>`;
    }).join("");
  }

  const events = [];
  if (data && Array.isArray(data.events)) events.push(...data.events);
  else if (data && data.cities) {
    for (const city of Object.values(data.cities)) {
      if (Array.isArray(city)) events.push(...city);
    }
  } else if (Array.isArray(data)) events.push(...data);

  const now = Date.now();
  const upcoming = events.filter(e => {
    if (!e.date) return true;
    const d = new Date(e.date);
    return d >= now - 864e5 && d <= now + 90 * 864e5;
  }).sort((a, b) => {
    if (!a.date) return 1; if (!b.date) return -1;
    return new Date(a.date) - new Date(b.date);
  });

  if (!upcoming.length) {
    el.innerHTML = `<div class="act-empty">No upcoming shows found — check back soon</div>`;
    return;
  }

  const CITIES = new Set(["bangalore","bengaluru","mumbai","delhi","hyderabad","chennai","pune","kolkata","goa","kochi","cochin","india"]);
  const CITY_ALIAS = {
    "bengaluru":"Bangalore","bangalore city":"Bangalore",
    "new delhi":"Delhi","gurugram":"Delhi","gurgaon":"Delhi",
    "delhi/ncr":"Delhi","delhi ncr":"Delhi","delhi (ncr)":"Delhi",
    "noida":"Delhi","ghaziabad":"Delhi","dlf cyberhub, gurugram":"Delhi",
    "navi mumbai":"Mumbai","vile parle":"Mumbai","andheri":"Mumbai",
    "dadar":"Mumbai","bandra":"Mumbai","borivali(w)":"Mumbai","thane":"Mumbai","matunga":"Mumbai",
    "southern avenue, kolkata":"Kolkata",
    "lb nagar":"Hyderabad","madhapur":"Hyderabad",
    "cochin":"Kochi",
    "karve nagar, pune":"Pune","karve nagar":"Pune",
    "lb nagar":"Hyderabad","madhapur":"Hyderabad",
    "southern avenue, kolkata":"Kolkata",
    "dlf cyberhub, gurugram":"Delhi",
  };
  const normCity = c => CITY_ALIAS[(c||"").toLowerCase()] || c;
  const isTourOrDate = v => /\b20\d{2}\b/.test(v) || /\bTour\b/i.test(v) || /^\d+(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)/i.test(v);

  const cityCounts = {};
  for (const e of upcoming) {
    const c = normCity(e.city || "Other");
    cityCounts[c] = (cityCounts[c] || 0) + 1;
  }
  const extractVenue = name => {
    const n = name || "";
    const isCity = v => CITIES.has(v.toLowerCase().trim());
    const normaliseVenue = v => v
      .replace(/\s*\([^)]*\)\s*$/, "")
      .replace(/\s+[-–|:]\s+.+$/, "")
      .replace(/\s+(?:Bengaluru|Bangalore|Mumbai|Delhi|Hyderabad|Chennai|Pune|Kolkata|Goa|Kochi)$/i, "")
      .trim();
    const mAt = n.match(/\bat\.?\s+(.+)$/i);
    if (mAt) { const v = normaliseVenue(mAt[1]); if (v.length > 2 && v.length <= 60 && !isCity(v)) return v; }
    const mPr = n.match(/^([A-Za-z0-9 &'\-]{4,30}?)\s+presents?\s+/i);
    if (mPr) { const v = mPr[1].trim(); if (v.length > 3 && !/\s+x\s+/i.test(v) && !isCity(v)) return v; }
    const sep = n.includes(" || ") ? " || " : " | ";
    if (n.includes(sep)) {
      const last = n.split(sep).pop().replace(/\s*\([^)]*\)\s*$/, "").trim();
      if (last.length > 2 && !/^\d+\s*([ap]m)?$/i.test(last) && !isCity(last) && !isTourOrDate(last)) return last;
    }
    return "";
  };

  const getVenue = e => {
    const raw = e.venue || e.venue_name || extractVenue(e.name || e.title || "") || "";
    return raw.replace(/\s+(?:Bengaluru|Bangalore|Mumbai|Delhi|Hyderabad|Chennai|Pune|Kolkata|Goa|Kochi)$/i, "").trim();
  };

  let activeCity = "all";

  const median = arr => {
    if (!arr.length) return null;
    const s = [...arr].sort((a, b) => a - b);
    const m = Math.floor(s.length / 2);
    return s.length % 2 ? s[m] : Math.round((s[m-1] + s[m]) / 2);
  };

  const CITY_COLORS = {
    "Bangalore":"#a78bfa","Mumbai":"#60a5fa","Delhi":"#34d399",
    "Hyderabad":"#fbbf24","Chennai":"#f87171","Pune":"#fb923c",
    "Goa":"#e879f9","Kolkata":"#38bdf8","Kochi":"#4ade80",
  };

  const venuePriceLabel = (evs) => {
    const vals = evs.flatMap(e => [e.price_min ?? e.min_price, e.price_max ?? e.max_price])
      .filter(p => p != null && p >= 0);
    if (!vals.length) return "Free entry";
    const lo = Math.min(...vals), hi = Math.max(...vals);
    if (lo === 0 && hi === 0) return "Free entry";
    if (lo === hi) return `₹${lo}`;
    if (lo === 0) return `Free – ₹${hi}`;
    return `₹${lo} – ₹${hi}`;
  };

  const sceneSummary = (list) => {
    const venues = new Set(list.map(e => (e.venue || e.venue_name || "") + "|" + (e.city || "")));
    const ticketPrices = list.map(e => e.price_min ?? e.min_price)
      .filter(p => p != null && Number(p) > 0).map(Number);
    const med = median(ticketPrices);
    const medStr = med != null ? ` · median ₹${med.toLocaleString("en-IN")}` : "";
    return `${venues.size} venue${venues.size !== 1 ? "s" : ""} · ${list.length} show${list.length !== 1 ? "s" : ""}${medStr}`;
  };

  const growthBadge = g => {
    if (g === null || g === undefined) return `<span class="venue-growth new">New</span>`;
    if (g > 0)  return `<span class="venue-growth up">+${g}</span>`;
    if (g < 0)  return `<span class="venue-growth down">${g}</span>`;
    return `<span class="venue-growth flat">—</span>`;
  };

  const drawVenues = () => {
    // ── All-cities summary view ──────────────────────────────────────────────
    if (activeCity === "all") {
      const cityMap = {};
      for (const e of upcoming) {
        const c = normCity(e.city || "Other");
        if (!cityMap[c]) cityMap[c] = { events: [], ticketed: 0, prices: [], venues: {} };
        cityMap[c].events.push(e);
        const p = e.price_min ?? e.min_price;
        if (p != null && Number(p) > 0) {
          cityMap[c].ticketed++;
          cityMap[c].prices.push(Number(p));
        }
        const vn = getVenue(e);
        if (vn && !/^(venue\s*tbc|tba|to be announced|venue to be (confirmed|announced))$/i.test(vn)) {
          cityMap[c].venues[vn] = (cityMap[c].venues[vn] || 0) + 1;
        }
      }
      const cityEntries = Object.entries(cityMap)
        .filter(([c]) => c !== "Other")
        .sort(([, a], [, b]) => b.events.length - a.events.length);
      const totalShows = cityEntries.reduce((s, [, c]) => s + c.events.length, 0);

      // City composition bar
      const barSegs = cityEntries.map(([city, s]) => {
        const pct = totalShows ? (s.events.length / totalShows * 100).toFixed(1) : 0;
        const col = CITY_COLORS[city] || "#888";
        return `<div style="flex:${pct};background:${col}" title="${city}: ${s.events.length} shows (${pct}%)"></div>`;
      }).join("");
      const compBar = `<div class="composition-bar">${barSegs}</div>`;

      const cityRows = cityEntries.map(([city, s]) => {
          const med = median(s.prices);
          const priceStr = med != null ? `median ₹${med.toLocaleString("en-IN")}` : "Free";
          const col = CITY_COLORS[city] || "#888";
          const topV = Object.entries(s.venues).sort((a, b) => b[1] - a[1])[0];
          const topVenueHtml = topV
            ? `<div class="city-row-top-venue">${esc(topV[0])} <span class="city-row-top-count">${topV[1]} shows</span></div>`
            : "";
          return `<div class="city-row" onclick="selectCity('${esc(city)}')">
            <span class="city-row-dot" style="background:${col}"></span>
            <div class="city-row-body">
              <div class="city-row-main">
                <div class="city-row-name">${esc(city)}</div>
                <div class="city-row-meta">
                  <span class="city-row-count">${s.events.length} shows</span>
                  <span class="city-row-sep">·</span>
                  <span class="city-row-ticketed">${s.ticketed} ticketed</span>
                  <span class="city-row-sep">·</span>
                  <span class="city-row-price">${priceStr}</span>
                </div>
              </div>
              ${topVenueHtml}
            </div>
            <div class="city-row-arrow">→</div>
          </div>`;
        }).join("");
      el.innerHTML = `${compBar}<div class="city-summary">${cityRows}</div>`;
      return;
    }

    // ── City drill-down: venue cards ─────────────────────────────────────────
    const list = upcoming.filter(e => normCity(e.city || "Other") === activeCity);

    const venueMap = {};
    for (const e of list) {
      const vname = getVenue(e) || "Venue TBC";
      const key   = vname + "|" + normCity(e.city || "");
      if (!venueMap[key]) venueMap[key] = { name: vname, city: normCity(e.city || ""), events: [] };
      venueMap[key].events.push(e);
    }

    const named   = Object.values(venueMap).filter(v => v.name !== "Venue TBC");
    const unnamed = Object.values(venueMap).filter(v => v.name === "Venue TBC");
    const unnamedCount = unnamed.reduce((s, v) => s + v.events.length, 0);

    // Look up growth from venue-insights
    const ciVenues = venueInsights?.cities?.[activeCity]?.venues || [];
    const insightMap = Object.fromEntries(ciVenues.map(v => [v.name, v]));

    const cards = named
      .sort((a, b) => b.events.length - a.events.length)
      .map(v => {
        const count   = v.events.length;
        const price   = venuePriceLabel(v.events);
        const next    = v.events[0];
        const nextDate = next?.date
          ? new Date(next.date).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" })
          : "";
        const hot = count >= 3 ? " venue-card--hot" : "";
        const insight = insightMap[v.name];
        const badge = insight ? growthBadge(insight.growth) : "";
        return `<a class="venue-card${hot}" href="${esc(next?.url || "#")}" target="_blank" rel="noopener">
          <div class="venue-card-top-row">
            <div class="venue-card-name">${esc(v.name)}</div>
            ${badge}
          </div>
          <div class="venue-card-stats">
            <span class="venue-stat-count">${count} show${count !== 1 ? "s" : ""}</span>
            <span class="venue-stat-price">${esc(price)}</span>
          </div>
          ${nextDate ? `<div class="venue-card-next">Next: ${esc(nextDate)}</div>` : ""}
        </a>`;
      }).join("");

    const moreNote = unnamedCount > 0
      ? `<div class="venue-more">+ ${unnamedCount} more show${unnamedCount !== 1 ? "s" : ""} at unlisted venues — <a href="https://www.skillboxes.com/events" target="_blank" rel="noopener">see all on Skillboxes</a></div>`
      : "";

    // Venue composition bar for city view
    const sortedNamed = [...named].sort((a, b) => b.events.length - a.events.length);
    const totalVenueEvts = sortedNamed.reduce((s, v) => s + v.events.length, 0);
    const venueBarSegs = sortedNamed.map((v, i) => {
      const pct = totalVenueEvts ? (v.events.length / totalVenueEvts * 100).toFixed(1) : 0;
      return `<div style="flex:${pct};background:${PAL[i % PAL.length]}" title="${v.name}: ${v.events.length} shows"></div>`;
    }).join("");
    const venueBar = sortedNamed.length > 1
      ? `<div class="composition-bar">${venueBarSegs}</div>`
      : "";

    el.innerHTML = `
      <div class="venue-summary">${esc(sceneSummary(list))}</div>
      ${venueBar}
      <div class="venue-grid">${cards}</div>
      ${moreNote}`;
  };

  // Normalise city counts for pills (merged cities)
  const normCityCounts = {};
  for (const e of upcoming) {
    const c = normCity(e.city || "Other");
    if (c !== "Other") normCityCounts[c] = (normCityCounts[c] || 0) + 1;
  }

  const selectCity = (city) => {
    if (pillsEl) {
      pillsEl.querySelectorAll(".city-pill").forEach(b => {
        b.classList.toggle("active", b.dataset.city === city);
      });
    }
    activeCity = city;
    drawVenues();
  };
  window.selectCity = selectCity;

  if (pillsEl) {
    pillsEl.innerHTML =
      `<button class="city-pill active" data-city="all">All cities</button>` +
      Object.entries(normCityCounts).sort((a, b) => b[1] - a[1]).slice(0, 8)
        .map(([c, n]) => `<button class="city-pill" data-city="${esc(c)}">${esc(c)} · ${n}</button>`)
        .join("");
    pillsEl.querySelectorAll(".city-pill").forEach(btn => {
      btn.addEventListener("click", () => selectCity(btn.dataset.city));
    });
  }

  drawVenues();
}

// ── Today: Reviewers section ──────────────────────────────────────────────────
function renderTodayReviewers(data) {
  const el = document.getElementById("today-reviewers");
  if (!el) return;

  let reviewers = [];
  if (Array.isArray(data)) reviewers = data;
  else if (data && Array.isArray(data.reviewers)) reviewers = data.reviewers;

  // Pick 4 active reviewers, varied by category
  const active = reviewers.filter(r => r.active !== false);
  // Try to get variety: editorial, podcast, playlist/spotify, blog
  const byCategory = {};
  for (const r of active) {
    const cat = r.category || "editorial";
    if (!byCategory[cat]) byCategory[cat] = [];
    byCategory[cat].push(r);
  }
  const sample = [];
  const order = ["editorial", "podcast", "spotify_curator", "youtube"];
  for (const cat of order) {
    if (sample.length >= 4) break;
    if (byCategory[cat] && byCategory[cat].length) sample.push(byCategory[cat][0]);
  }
  // Fill remaining slots from any category
  for (const r of active) {
    if (sample.length >= 4) break;
    if (!sample.includes(r)) sample.push(r);
  }

  if (!sample.length) {
    el.innerHTML = `<div class="act-empty">Reviewer data loading…</div>`;
    return;
  }

  const PLATFORM_LABEL = {
    editorial: "Blog / Editorial",
    podcast: "Podcast",
    spotify_curator: "Playlist",
    youtube: "YouTube",
  };

  el.innerHTML = `<div class="reviewers-grid">${sample.map(r => {
    const genres    = (r.genres||[]).slice(0, 2).join(", ") || "Various genres";
    const platform  = PLATFORM_LABEL[r.category] || "Blog";
    const pitchLink = (r.pitch_to||[])[0]?.contact
      ? (r.pitch_to[0].contact.startsWith("http") ? r.pitch_to[0].contact : `mailto:${r.pitch_to[0].contact}`)
      : (r.url || "#");
    return `<div class="reviewer-card">
      <div class="reviewer-card-top">
        <div class="reviewer-card-name">${esc(r.name)}</div>
        <span class="reviewer-platform-pill">${esc(platform)}</span>
      </div>
      <div class="reviewer-card-genres">${esc(genres)}</div>
      <a class="reviewer-card-cta" href="${esc(pitchLink)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Pitch →</a>
    </div>`;
  }).join("")}</div>`;
}

// ── Discover filter toggle ────────────────────────────────────────────────────
function initDiscoverFilterToggle() {
  const btn    = document.getElementById("discover-filter-toggle");
  const bar    = document.getElementById("discover-filter-bar");
  const label  = document.getElementById("d-list-label");
  const vlist  = document.getElementById("video-list");
  if (!btn || !bar) return;
  btn.addEventListener("click", () => {
    const open = bar.style.display !== "none";
    bar.style.display    = open ? "none" : "flex";
    if (label) label.style.display = open ? "none" : "";
    if (vlist) vlist.style.display = open ? "none" : "";
    btn.textContent = open ? "Filter & sort ▾" : "Filter & sort ▴";
  });
}

// ── Breakdown bars ────────────────────────────────────────────────────────────

// ── Collab scoring ────────────────────────────────────────────────────────────
function collabFit(c) {
  const myGenre = document.getElementById("c-my-genre")?.value || "";
  const myLang  = document.getElementById("c-my-lang")?.value  || "";
  if (!myGenre && !myLang) return { type: "none", score: c.avg_discovery };
  const sameGenre = myGenre && c.top_genre === myGenre;
  const sameLang  = myLang  && c.top_lang  === myLang;
  let type  = "none";
  let bonus = 0;
  if (sameGenre && sameLang) { type = "both";  bonus = 30; }
  else if (sameGenre)        { type = "genre"; bonus = 20; }
  else if (sameLang)         { type = "lang";  bonus = 15; }
  return { type, score: c.avg_discovery + bonus };
}

// ── Artist grid ───────────────────────────────────────────────────────────────
function renderArtistGrid(channels) {
  if (!channels.length) {
    document.getElementById("artist-grid").innerHTML =
      `<div class="empty-state">No artists match your filters.</div>`;
    return;
  }
  document.getElementById("artist-grid").innerHTML = channels.map(c=>{
    const sp  = spotifyData[c.name] || {};
    const fit = collabFit(c);
    const spLink = sp.spotify_url
      ? `<a class="spotify-badge" href="${esc(sp.spotify_url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">♫ Spotify</a>`
      : "";
    const spFollowers = sp.followers > 0
      ? `<div>${fmt(sp.followers)} sp. followers</div>` : "";
    const fitBadge = fit.type !== "none"
      ? `<span class="collab-fit-badge collab-${fit.type}">${fit.type==="both"?"Strong fit":fit.type==="genre"?"Genre match":"Language match"}</span>`
      : "";
    // Signals row: what makes them worth reaching out to
    const signals = [];
    if (c.video_count >= 2)    signals.push(`${c.video_count} videos`);
    if (c.avg_engagement >= 3) signals.push(`${c.avg_engagement}% eng`);
    if (c.multiplatform)       signals.push("Last.fm");
    if (sp.spotify_url)        signals.push("Spotify");
    if (c.lfm_india_rank)      signals.push(`#${c.lfm_india_rank} India`);

    const savedClass = getSavedArtists().includes(c.id) ? " saved-artist" : "";
    const TREND_TIP = "Trend vs the previous 30-day window based on Last.fm listener movement.";
    const trendBadge = c.trend
      ? `<span class="artist-card-trend trend-badge ${TREND_CLS[c.trend]} metric-tip" data-tip="${TREND_TIP}">${TREND_ICON[c.trend]} ${c.trend}</span>`
      : "";
    const lfmRow = c.lfm_listeners > 0
      ? `<div class="artist-lfm-row">
           <span class="lfm-india metric-tip" data-tip="Monthly listeners on Last.fm tracked to India. Updates daily.">${c.lfm_india_listeners > 0 ? fmt(c.lfm_india_listeners)+" India" : ""}</span>
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
        <div class="artist-card-body">
          <div class="artist-card-name" title="${esc(c.name)}">${esc(c.name)}</div>
          <div class="artist-card-pills">
            <span class="pill pill-genre">${esc(c.top_genre)}</span>
            <span class="pill pill-lang">${esc(c.top_lang)}</span>
            ${fitBadge}
          </div>
          <div class="artist-card-meta">${c.video_count} video${c.video_count!==1?"s":""} · ${fmt(c.total_views)} views</div>
        </div>
      </div>
    </div>`;
  }).join("");
}

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

function bindArtistControls() {
  const apply = applyArtistFilter;
  const mpBtn = document.getElementById("a-multiplatform");
  mpBtn.addEventListener("click",()=>{
    const on = mpBtn.dataset.on==="true";
    mpBtn.dataset.on = String(!on);
    mpBtn.classList.toggle("active",!on);
    apply();
  });
  ["c-my-genre","c-my-lang"].forEach(id=>
    document.getElementById(id)?.addEventListener("change", e => {
      savePreference(id === "c-my-genre" ? LS_MY_GENRE : LS_MY_LANG, e.target.value);
      apply();
    }));
  ["a-search","a-sort","a-genre","a-lang","a-min-eng","a-min-videos","a-trend"].forEach(id=>
    document.getElementById(id).addEventListener(id==="a-search"?"input":"change", apply));
  initMoreToggle("a-more-btn", "a-more");
}

// ── Video list ────────────────────────────────────────────────────────────────
function renderVideoList(videos) {
  if (!videos.length) {
    document.getElementById("video-list").innerHTML =
      `<div class="empty-state">No videos match your filters.</div>`;
    return;
  }
  document.getElementById("video-list").innerHTML = videos.map((v,i)=>`
    <a href="${esc(v.url)}" target="_blank" rel="noopener" class="video-row">
      <div class="video-row-num">${i+1}</div>
      <img class="video-row-thumb" src="${esc(v.thumbnail)}" alt="" loading="lazy" />
      <div class="video-row-info">
        <div class="video-row-title">${esc(v.title)}</div>
        <div class="video-row-channel">${esc(v.channel)}</div>
        <div class="video-row-pills">
          <span class="pill pill-genre">${esc(v.genre)}</span>
          <span class="pill pill-lang">${esc(v.language)}</span>
          ${v.is_new?'<span class="pill pill-new">NEW</span>':''}
        </div>
      </div>
      <div class="video-row-metrics">
        <div class="video-score">${v.discovery_score??'—'}</div>
        <div class="video-row-sub">${fmt(v.views)} views · ${daysAgo(v.published_at)}</div>
      </div>
    </a>`).join("");
}


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

// ── Radar ─────────────────────────────────────────────────────────────────────
const TREND_ICON = {new:"✦", rising:"▲", stable:"─", falling:"▼"};
const TREND_CLS  = {new:"trend-new", rising:"trend-up", stable:"trend-flat", falling:"trend-dn"};


// ── Tabs ──────────────────────────────────────────────────────────────────────
const TAB_CONTEXT = {
  discover: "New releases and top picks — scored 0–100 on engagement, daily view growth, and recency",
  artists:  "Browse and filter artists by language and genre — use Collab Finder to spot potential collaborators",
  trends:   "Upcoming shows across cities and artists newly added to the radar",
  buzz:     "Reddit threads and press coverage mentioning Indian indie artists",
  industry: "Labels, booking agencies, and music companies — who's signing and how to approach them"
};

function goTab(name) {
  document.querySelectorAll('.filter-more').forEach(p => { p.hidden = true; });
  document.querySelectorAll('.more-btn').forEach(b => { if (b.textContent.startsWith('−')) b.textContent = '+ More ▾'; });
  dismissWelcome();
  document.querySelectorAll(".subtab").forEach(t=>t.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach(t=>t.classList.remove("active"));
  const btn = document.querySelector(`.subtab[data-tab="${name}"]`);
  if (btn) btn.classList.add("active");
  const pane = document.getElementById("tab-"+name);
  if (pane) pane.classList.add("active");
  const ctx = document.getElementById("tab-context");
  if (ctx && TAB_CONTEXT[name]) ctx.textContent = TAB_CONTEXT[name];
  track('tab_switch', { tab_name: name });
  // Trends: artist log is always ready; charts load on first toggle expand
  if (name==="buzz"&&!_buzzLoaded){
    _buzzLoaded=true; renderBuzz(_socialData);
  }
  if (name==="industry") {
    const frame = document.getElementById('industry-frame');
    if (frame && !frame.src) frame.src = 'industry/?embed=1';
  }
}

function bindTabs(insightsData, socialData) {
  _insightsData=insightsData; _socialData=socialData;
  document.querySelectorAll(".subtab").forEach(btn=>
    btn.addEventListener("click",()=>goTab(btn.dataset.tab))
  );
}

function initWelcome() {
  // Removed — welcome modal no longer exists in the DOM
  return;

  const LANGS  = ["Tamil","Telugu","Kannada","Malayalam","Bengali","Punjabi","Marathi","Hindi","English","All"];
  const GENRES = ["Indie","Folk / Acoustic","Hip Hop / Rap","Indie Pop","Rock / Alt","Electronic","R&B / Soul","Lo-Fi","Classical/Fusion"];
  let pendingTab=null, selectedLang=null, selectedGenre=null;

  function buildChips(id, items, useLangColor) {
    const c = document.getElementById(id); if (!c) return;
    c.innerHTML = items.map(v => {
      const col = useLangColor ? (LANG_COLORS[v]||"#888") : null;
      return `<button class="w-chip" data-val="${v}"${col?` style="--lc:${col}"`:""}>${v}</button>`;
    }).join("");
  }
  buildChips("ws-lang-chips",       LANGS,  true);
  buildChips("ws-artist-lang-chips", LANGS.filter(l=>l!=="All"), true);
  buildChips("ws-genre-chips",      GENRES, false);

  function showStep(id) {
    document.querySelectorAll(".welcome-step").forEach(s=>s.style.display="none");
    document.getElementById(id).style.display="block";
  }

  function applyAndGo(tab, lang, genre) {
    const l = lang && lang!=="All" ? lang : null;
    if (l)     localStorage.setItem(LS_MY_LANG, l);
    if (genre) localStorage.setItem(LS_MY_GENRE, genre);
    dismissWelcome();
    if (allVideos.length > 0) {
      if (l)     ["c-my-lang","d-lang","a-lang","v-lang"].forEach(id=>{const e=document.getElementById(id);if(e)e.value=l;});
      if (genre) ["c-my-genre","d-genre","a-genre","v-genre"].forEach(id=>{const e=document.getElementById(id);if(e)e.value=genre;});
      if (tab==="artists") {
        const as=document.getElementById("a-sort"); if(as) as.value="collab_score";
      }
      applyDiscover(); applyArtistFilter();
    }
    goTab(tab);
    if (tab==="artists") {
      setTimeout(()=>{
        const cb=document.getElementById("collab-bar");
        if(cb){cb.classList.add("collab-hl");setTimeout(()=>cb.classList.remove("collab-hl"),1800);}
      },350);
    }
  }

  // Step 1 tiles
  el.querySelectorAll(".intent-tile").forEach(tile=>
    tile.addEventListener("click",()=>{
      pendingTab=tile.dataset.tab;
      if (pendingTab==="buzz") { applyAndGo("buzz",null,null); return; }
      if (pendingTab==="artists") { showStep("ws-artist"); return; }
      document.getElementById("ws-lang-heading").textContent =
        pendingTab==="trends" ? "Which scene are you following?" : "What are you into?";
      showStep("ws-lang");
    })
  );

  // Step 2a: tap a language chip → instant go
  document.getElementById("ws-lang-chips").addEventListener("click", e=>{
    const chip=e.target.closest(".w-chip"); if(!chip) return;
    applyAndGo(pendingTab, chip.dataset.val, null);
  });

  // Step 2b: genre chip selection
  document.getElementById("ws-genre-chips").addEventListener("click", e=>{
    const chip=e.target.closest(".w-chip"); if(!chip) return;
    document.querySelectorAll("#ws-genre-chips .w-chip").forEach(c=>c.classList.remove("active"));
    chip.classList.add("active"); selectedGenre=chip.dataset.val;
  });
  // Step 2b: lang chip selection
  document.getElementById("ws-artist-lang-chips").addEventListener("click", e=>{
    const chip=e.target.closest(".w-chip"); if(!chip) return;
    document.querySelectorAll("#ws-artist-lang-chips .w-chip").forEach(c=>c.classList.remove("active"));
    chip.classList.add("active"); selectedLang=chip.dataset.val;
  });
  // Step 2b: CTA
  document.getElementById("ws-artist-go")
    .addEventListener("click",()=>applyAndGo("artists", selectedLang, selectedGenre));

  // Back buttons
  document.getElementById("ws-back-lang").addEventListener("click",()=>showStep("ws-1"));
  document.getElementById("ws-back-artist").addEventListener("click",()=>showStep("ws-1"));

  // Skip
  document.getElementById("welcome-skip")
    .addEventListener("click",()=>{dismissWelcome();goTab("discover");});
}

function dismissWelcome() {
  const el = document.getElementById("welcome");
  if (!el||!el.classList.contains("is-open")) return;
  el.style.opacity="0";
  setTimeout(()=>{el.classList.remove("is-open");el.style.opacity="";},240);
  localStorage.setItem("iimr_ob","1");
}

// ── Trends ────────────────────────────────────────────────────────────────────
let trendCharts = {};
let monthlyData = [];
let hiddenGenres = new Set();
let hiddenLangs  = new Set();

async function loadTrends() {
  const monthCount = parseInt(document.getElementById("t-months").value)||6;
  const now   = new Date();
  const months= Array.from({length:monthCount},(_,i)=>{
    const d=new Date(now.getFullYear(),now.getMonth()-i,1);
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`;
  }).reverse();

  const results = await Promise.all(months.map(m=>
    fetch(`data/monthly/${m}.json`,{cache:"no-cache"}).then(r=>r.ok?r.json():null).catch(()=>null)
  ));
  monthlyData = results.filter(Boolean);
  document.getElementById("trends-loading").style.display="none";
  if (!monthlyData.length) {
    document.getElementById("trends-loading").style.display="block";
    document.getElementById("trends-loading").textContent="No monthly data yet — check back after a few daily runs.";
    return;
  }
  document.getElementById("trends-table-wrap").style.display="block";
  if (monthlyData.length >= 2) {
    document.getElementById("trends-grid").style.display="grid";
    document.getElementById("t-more-btn").style.display="";
    buildTrendToggles();
    drawTrendCharts();
  } else {
    document.getElementById("trends-grid").style.display="none";
    document.getElementById("t-more-btn").style.display="none";
    document.getElementById("trends-chart-note").style.display="block";
  }
}

function buildTrendToggles() {
  const allG = [...new Set(monthlyData.flatMap(m=>(m.genre_breakdown||[]).map(g=>g[0])))];
  const allL = [...new Set(monthlyData.flatMap(m=>(m.language_breakdown||[]).map(l=>l[0])))];
  document.getElementById("t-genre-toggles").innerHTML =
    allG.map((g,i)=>`<button class="pill-toggle active" data-type="genre" data-val="${esc(g)}" style="--tc:${PAL[i%PAL.length]}">${esc(g)}</button>`).join("");
  document.getElementById("t-lang-toggles").innerHTML =
    allL.map((l,i)=>`<button class="pill-toggle active" data-type="lang" data-val="${esc(l)}" style="--tc:${PAL[(i+4)%PAL.length]}">${esc(l)}</button>`).join("");
  document.querySelectorAll(".pill-toggle").forEach(btn=>btn.addEventListener("click",()=>{
    btn.classList.toggle("active");
    const set = btn.dataset.type==="genre" ? hiddenGenres : hiddenLangs;
    if (!btn.classList.contains("active")) set.add(btn.dataset.val); else set.delete(btn.dataset.val);
    drawTrendCharts();
  }));
  document.getElementById("t-months").addEventListener("change",()=>{
    monthlyData=[]; hiddenGenres=new Set(); hiddenLangs=new Set();
    loadTrends();
  });
  initMoreToggle("t-more-btn", "t-more");
}

function drawTrendCharts() {
  Object.values(trendCharts).forEach(c=>c.destroy());
  trendCharts = {};
  const labels = monthlyData.map(m=>m.month);
  const allG   = [...new Set(monthlyData.flatMap(m=>(m.genre_breakdown||[]).map(g=>g[0])))].filter(g=>!hiddenGenres.has(g));
  const allL   = [...new Set(monthlyData.flatMap(m=>(m.language_breakdown||[]).map(l=>l[0])))].filter(l=>!hiddenLangs.has(l));
  const getC   = (m,key,field)=>(m[field]||[]).find(x=>x[0]===key)?.[1]||0;
  const lineOpts = ()=>({
    plugins:{legend:{position:"bottom",labels:{color:"#666",font:{size:10},boxWidth:10}}},
    scales:{x:{ticks:{color:"#555",font:{size:10}},grid:{color:"#1a1a1a"}},y:{ticks:{color:"#555"},grid:{color:"#1a1a1a"}}},
  });
  const barOpts = cb=>({
    plugins:{legend:{display:false}},
    scales:{x:{ticks:{color:"#555",font:{size:10}},grid:{color:"#1a1a1a"}},y:{ticks:{color:"#555",callback:cb},grid:{color:"#1a1a1a"}}},
  });
  trendCharts.genre = new Chart(document.getElementById("trend-genre"),{type:"line",data:{labels,datasets:allG.map((g,i)=>({label:g,data:monthlyData.map(m=>getC(m,g,"genre_breakdown")),borderColor:PAL[i%PAL.length],backgroundColor:"transparent",tension:.3,pointRadius:4}))},options:lineOpts()});
  trendCharts.lang  = new Chart(document.getElementById("trend-lang"), {type:"line",data:{labels,datasets:allL.map((l,i)=>({label:l,data:monthlyData.map(m=>getC(m,l,"language_breakdown")),borderColor:PAL[(i+4)%PAL.length],backgroundColor:"transparent",tension:.3,pointRadius:4}))},options:lineOpts()});
  trendCharts.views = new Chart(document.getElementById("trend-views"),{type:"bar",data:{labels,datasets:[{data:monthlyData.map(m=>m.total_views||0),backgroundColor:PAL[0],borderRadius:4}]},options:barOpts(v=>fmt(v))});
  trendCharts.count = new Chart(document.getElementById("trend-count"),{type:"bar",data:{labels,datasets:[{data:monthlyData.map(m=>m.total_videos||0),backgroundColor:PAL[2],borderRadius:4}]},options:barOpts(v=>v)});
  document.getElementById("trends-body").innerHTML=[...monthlyData].reverse().map(m=>`
    <tr>
      <td><strong>${m.month}</strong></td>
      <td>${m.total_videos||0}</td>
      <td>${fmt(m.total_views||0)}</td>
      <td><span class="pill pill-genre">${(m.genre_breakdown||[])[0]?.[0]||"—"}</span></td>
      <td><span class="pill pill-lang">${(m.language_breakdown||[])[0]?.[0]||"—"}</span></td>
      <td style="color:var(--muted)">${(m.top_channels||[])[0]?.[0]||"—"}</td>
    </tr>`).join("");
}

// ── Language Insights ─────────────────────────────────────────────────────────
function renderInsights(data) {
  const wrap = document.getElementById("insights-wrap");
  const grid = document.getElementById("insights-grid");
  const meta = document.getElementById("insights-meta");
  if (!wrap || !grid) return;

  const days = data.days_of_data || 0;
  const from = data.date_range?.from || "";
  const to   = data.date_range?.to   || "";
  meta.textContent = `${days} day${days!==1?"s":""} of data · ${from}${from!==to?" → "+to:""}`;

  const langs = data.languages || {};
  const LANG_ORDER = ["Tamil","Telugu","Kannada","Malayalam","Bengali","Punjabi","Marathi","Hindi","English"];

  grid.innerHTML = LANG_ORDER.map(lang => {
    const ins = langs[lang];
    if (!ins || ins.status === "no data yet") {
      return `<div class="insight-card insight-empty">
        <div class="insight-lang" style="--lc:${LANG_COLORS[lang]||'#666'}">${lang}</div>
        <div class="insight-narrative">No data yet — will populate as daily runs accumulate.</div>
      </div>`;
    }
    const col   = LANG_COLORS[lang] || "#666";
    const topArtists = (ins.top_artists || []).slice(0, 4);
    const genres = (ins.genre_breakdown || []).slice(0, 5);
    const maxG   = genres[0]?.day_appearances || 1;

    // Genre sub-insights: show top artist per genre
    const genreCards = Object.entries(ins.genre_insights || {}).slice(0, 4).map(([g, gi]) => {
      const top = gi.top_artists?.[0];
      return `<div class="insight-genre-row">
        <span class="pill pill-genre">${esc(g)}</span>
        <span class="insight-genre-artist">${top ? esc(top.name) : "—"}</span>
        <span class="insight-genre-days">${gi.day_appearances}d</span>
      </div>`;
    }).join("");

    return `<div class="insight-card" style="--lc:${col}">
      <div class="insight-card-top">
        <div class="insight-lang" style="--lc:${col}">${lang}</div>
        <span class="insight-dominant">${esc(ins.dominant_genre)}</span>
      </div>
      <p class="insight-narrative">${esc(ins.narrative)}</p>
      <div class="insight-section-label">Top recurring artists</div>
      <div class="insight-artists">
        ${topArtists.map(a=>`
          <div class="insight-artist-row">
            <span class="insight-artist-name">${esc(a.name)}</span>
            <span class="insight-artist-stat">${a.appearances}d · ${fmt(a.avg_views)} avg views · ${a.avg_eng}% eng</span>
          </div>`).join("")}
      </div>
      ${genreCards ? `<div class="insight-section-label">By genre</div><div class="insight-genres">${genreCards}</div>` : ""}
      <div class="insight-genre-bars">
        ${genres.map(({genre:g, day_appearances:c})=>`
          <div class="bar-item">
            <div class="bar-label">${esc(g)}</div>
            <div class="bar-track"><div class="bar-fill" style="width:${Math.round(c/maxG*100)}%;background:${col}"></div></div>
            <div class="bar-count">${c}d</div>
          </div>`).join("")}
      </div>
    </div>`;
  }).join("");

  wrap.style.display = "block";
}

// ── Buzz / Social ─────────────────────────────────────────────────────────────
let buzzData = null;

function renderBuzz(data) {
  buzzData = data;
  const loading = document.getElementById("buzz-loading");
  const content = document.getElementById("buzz-content");

  if (!data || (!data.artist_posts?.length && !data.feed?.length)) {
    loading.innerHTML = `<div style="max-width:400px;margin:0 auto;text-align:center">
      <div style="font-size:28px;margin-bottom:12px">📡</div>
      <div style="font-size:15px;font-weight:600;color:var(--text);margin-bottom:8px">Reddit coverage coming soon</div>
      <div style="font-size:13px;line-height:1.6">This tab will surface Reddit threads and press mentions about Indian indie artists. While it's being set up, try <button onclick="goTab('discover')" style="background:none;border:none;color:var(--accent);cursor:pointer;font-size:13px;padding:0;text-decoration:underline">Discover</button> or <button onclick="goTab('artists')" style="background:none;border:none;color:var(--accent);cursor:pointer;font-size:13px;padding:0;text-decoration:underline">Artists</button> to find what's moving right now.</div>
    </div>`;
    return;
  }

  loading.style.display = "none";
  content.style.display  = "block";

  // Populate language filter
  const bLang = document.getElementById("b-lang");
  const langs = [...new Set([
    ...(data.artist_posts||[]).map(p=>p.language),
    ...(data.feed||[]).map(p=>p.language),
  ])].filter(Boolean).sort();
  langs.forEach(l => {
    const o = document.createElement("option"); o.value = l; o.textContent = l;
    bLang.appendChild(o);
  });

  // Auto-apply saved language preference
  const savedLang = localStorage.getItem(LS_MY_LANG);
  if (savedLang && [...bLang.options].some(o => o.value === savedLang)) {
    bLang.value = savedLang;
  }

  // Remove Reddit option if no Reddit posts exist in this data
  const hasReddit = [...(data.artist_posts||[]), ...(data.feed||[])].some(p => p.platform === "reddit");
  if (!hasReddit) {
    const bPlatform = document.getElementById("b-platform");
    const redditOpt = [...bPlatform.options].find(o => o.value === "reddit");
    if (redditOpt) redditOpt.remove();
  }

  applyBuzzFilters(data);

  document.getElementById("b-lang").addEventListener("change", ()=>applyBuzzFilters(buzzData));
  document.getElementById("b-platform").addEventListener("change", ()=>applyBuzzFilters(buzzData));
  document.getElementById("b-artist-only").addEventListener("click", function(){
    this.dataset.on = this.dataset.on==="true" ? "false" : "true";
    this.classList.toggle("active", this.dataset.on==="true");
    applyBuzzFilters(buzzData);
  });
}

function applyBuzzFilters(data) {
  if (!data) return;
  const lang       = document.getElementById("b-lang").value;
  const platform   = document.getElementById("b-platform").value;
  const artistOnly = document.getElementById("b-artist-only").dataset.on === "true";

  const filter = p =>
    (lang==="all" || p.language===lang) &&
    (platform==="all" || p.platform===platform);

  const artistPosts = (data.artist_posts||[]).filter(filter);
  const feedPosts   = artistOnly ? [] : (data.feed||[]).filter(filter)
    .sort((a, b) => (b.date || "").localeCompare(a.date || ""));

  renderBuzzArtistSection(artistPosts);
  renderBuzzFeed(feedPosts);
}

function renderBuzzArtistSection(posts) {
  const blocks = document.getElementById("buzz-artist-blocks");
  const count  = document.getElementById("buzz-artist-count");

  count.textContent = posts.length || "";

  if (!posts.length) {
    blocks.innerHTML = `<div class="buzz-artist-empty">No tracked artists in coverage this period.</div>`;
    return;
  }

  const byArtist = {};
  for (const p of posts) {
    if (!byArtist[p.artist]) byArtist[p.artist] = [];
    byArtist[p.artist].push(p);
  }

  blocks.innerHTML = Object.entries(byArtist).map(([artist, ps]) => `
    <div class="buzz-artist-block">
      <div class="buzz-artist-chip">${esc(artist)}<span class="buzz-chip-count">${ps.length}</span></div>
      <div class="buzz-posts">
        ${ps.map(p => buzzCardHTML(p)).join("")}
      </div>
    </div>`).join("");
}

function formatBuzzDateGroup(d) {
  if (!d) return "Unknown";
  const [y, m, day] = d.split("-").map(Number);
  const today = new Date();
  const dt    = new Date(y, m - 1, day);
  const base  = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const diff  = Math.round((base - dt) / 86400000);
  if (diff === 0) return "Today";
  if (diff === 1) return "Yesterday";
  return dt.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
}

function groupedBuzzHTML(posts) {
  const groups = [], groupMap = {};
  for (const p of posts) {
    const label = formatBuzzDateGroup(p.date);
    if (!groupMap[label]) { const g={label,posts:[]}; groups.push(g); groupMap[label]=g; }
    groupMap[label].posts.push(p);
  }
  return groups.map(g=>`
    <div class="buzz-date-group">
      <div class="buzz-date-hd">${esc(g.label)}</div>
      <div class="buzz-date-cards">${g.posts.map(p=>buzzCardHTML(p)).join("")}</div>
    </div>`).join("");
}

function renderBuzzFeed(posts) {
  const feed  = document.getElementById("buzz-feed");
  const count = document.getElementById("buzz-feed-count");

  count.textContent = posts.length;
  if (!posts.length) { feed.innerHTML = `<div class="buzz-artist-empty">No articles match this filter.</div>`; return; }

  const PAGE = 30;
  const rem = posts.length - PAGE;
  feed.innerHTML = groupedBuzzHTML(posts.slice(0, PAGE)) +
    (rem > 0 ? `<button class="buzz-show-more">Show ${rem} more articles</button>` : "");

  if (rem > 0) {
    feed.querySelector(".buzz-show-more").addEventListener("click", () => {
      feed.innerHTML = groupedBuzzHTML(posts);
    });
  }
}

function buzzCardHTML(p) {
  const langColor = LANG_COLORS[p.language] || "#666";
  const source = p.platform === "reddit"
    ? `r/${esc(p.subreddit||"reddit")}`
    : p.platform === "twitter" ? "Twitter"
    : esc(p.subreddit || "News");
  const scoreHtml = p.score > 0
    ? `<span class="buzz-dot">·</span><span class="buzz-score">▲ ${p.score}</span>` : "";

  return `<a class="buzz-card" href="${esc(p.url)}" target="_blank" rel="noopener">
    <div class="buzz-title">${esc(p.title)}</div>
    <div class="buzz-byline">
      <span class="buzz-source">${source}</span>
      <span class="buzz-dot">·</span>
      <span class="buzz-lang-pill" style="--lc:${langColor}">${esc(p.language||"")}</span>
      ${scoreHtml}
    </div>
  </a>`;
}

init();

// ── Personalization ───────────────────────────────────────────────────────────
function loadPreferences() {
  const g = localStorage.getItem(LS_MY_GENRE);
  const l = localStorage.getItem(LS_MY_LANG);
  if (g) ["c-my-genre","d-genre","a-genre","v-genre"].forEach(id=>{
    const el=document.getElementById(id); if(el) el.value=g;
  });
  if (l) ["c-my-lang","d-lang","a-lang","v-lang"].forEach(id=>{
    const el=document.getElementById(id); if(el) el.value=l;
  });
  if (g || l) { applyDiscover(); applyArtistFilter(); }
}

function savePreference(key, val) {
  if (val && val !== "all") localStorage.setItem(key, val);
  else localStorage.removeItem(key);
}

function initArtistLog() {
  const langs  = [...new Set(allChannels.map(c=>c.top_lang))].filter(Boolean).sort();
  const genres = [...new Set(allChannels.map(c=>c.top_genre))].filter(Boolean).sort();
  langs.forEach(l  => document.getElementById("al-lang").add(new Option(l,l)));
  genres.forEach(g => document.getElementById("al-genre").add(new Option(g,g)));
  ["al-lang","al-genre","al-sort"].forEach(id =>
    document.getElementById(id).addEventListener("change", renderArtistLog));
  renderArtistLog();
}

function renderArtistLog() {
  const lang  = document.getElementById("al-lang").value;
  const genre = document.getElementById("al-genre").value;
  const sort  = document.getElementById("al-sort").value;
  let cs = allChannels.filter(c =>
    (lang==="all"  || c.top_lang===lang) &&
    (genre==="all" || c.top_genre===genre)
  );
  if (sort==="frequent")    cs = [...cs].sort((a,b)=>b.video_count-a.video_count);
  else if (sort==="score")  cs = [...cs].sort((a,b)=>b.avg_discovery-a.avg_discovery);
  else                      cs = [...cs].sort((a,b)=>(b.latest_pub||"").localeCompare(a.latest_pub||""));
  document.getElementById("al-meta").textContent = `${cs.length} artist${cs.length!==1?"s":""}`;
  document.getElementById("artist-log-body").innerHTML = cs.map(c => {
    const badge = c.trend
      ? `<span class="trend-badge ${TREND_CLS[c.trend]}">${TREND_ICON[c.trend]} ${c.trend}</span>`
      : `<span style="color:var(--muted)">—</span>`;
    return `<tr>
      <td><a href="https://youtube.com/channel/${esc(c.id)}" target="_blank" rel="noopener" class="al-name">${esc(c.name)}</a></td>
      <td><span class="pill pill-lang">${esc(c.top_lang)}</span></td>
      <td><span class="pill pill-genre">${esc(c.top_genre)}</span></td>
      <td class="al-num">${c.video_count}</td>
      <td class="al-recency">${daysAgo(c.latest_pub)}</td>
      <td class="al-score">${c.avg_discovery}</td>
      <td>${badge}</td>
    </tr>`;
  }).join("");
}

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

function initMetricTips() {
  document.querySelector('main').addEventListener('click', e => {
    const tip = e.target.closest('.metric-tip');
    document.querySelectorAll('.metric-tip.tip-open')
      .forEach(el => el.classList.remove('tip-open'));
    if (tip) { e.stopPropagation(); tip.classList.add('tip-open'); }
  });
}

function getSavedArtists() {
  try { return JSON.parse(localStorage.getItem(LS_SAVED) || "[]"); } catch { return []; }
}

function toggleSaveArtist(channelId) {
  const saved = getSavedArtists();
  const idx = saved.indexOf(channelId);
  if (idx === -1) saved.push(channelId);
  else saved.splice(idx, 1);
  localStorage.setItem(LS_SAVED, JSON.stringify(saved));
  const nowSaved = idx === -1;
  track('artist_save', { action: nowSaved ? 'save' : 'unsave', channel_id: channelId });
  return nowSaved;
}

// ── Artist Drawer ─────────────────────────────────────────────────────────────
function initArtistDrawer() {
  const drawer  = document.getElementById("artist-drawer");
  const overlay = document.getElementById("drawer-overlay");
  const closeBtn= document.getElementById("drawer-close");
  if (!drawer) return;

  overlay.addEventListener("click", closeDrawer);
  closeBtn.addEventListener("click", closeDrawer);
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeDrawer(); });
}

function openArtistDrawer(channel) {
  const drawer = document.getElementById("artist-drawer");
  if (!drawer) return;
  track('artist_drawer_open', { artist_name: channel.name, genre: channel.top_genre, language: channel.top_lang });

  const sp      = spotifyData[channel.name] || {};
  const saved   = getSavedArtists();
  const isSaved = saved.includes(channel.id);
  const videos  = allVideos.filter(v => (v.channel_id || v.channel) === channel.id)
                           .sort((a, b) => (b.discovery_score||0) - (a.discovery_score||0));
  const topVideo = videos[0] || channel.top_video;
  const ytChLink = `https://youtube.com/channel/${esc(channel.id)}`;

  // Header
  document.getElementById("drawer-name").textContent = channel.name;
  document.getElementById("drawer-pills").innerHTML = `
    <span class="pill pill-genre">${esc(channel.top_genre)}</span>
    <span class="pill pill-lang">${esc(channel.top_lang)}</span>
    ${channel.multiplatform ? '<span class="pill" style="background:#a78bfa22;color:#a78bfa;border-color:#a78bfa44">Multi-platform</span>' : ""}
  `;

  // Save button
  const saveBtn = document.getElementById("drawer-save");
  saveBtn.textContent = isSaved ? "♥ Saved" : "♡ Save";
  saveBtn.className = "drawer-save-btn" + (isSaved ? " saved" : "");
  saveBtn.onclick = () => {
    const nowSaved = toggleSaveArtist(channel.id);
    saveBtn.textContent = nowSaved ? "♥ Saved" : "♡ Save";
    saveBtn.className = "drawer-save-btn" + (nowSaved ? " saved" : "");
  };

  // Embed top video or thumbnail link
  const embedWrap = document.getElementById("drawer-embed");
  if (topVideo?.id) {
    embedWrap.innerHTML = `<iframe
      src="https://www.youtube.com/embed/${esc(topVideo.id)}?modestbranding=1&rel=0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      allowfullscreen loading="lazy"></iframe>`;
  } else if (topVideo?.thumbnail) {
    embedWrap.innerHTML = `<a class="drawer-embed-placeholder" href="${esc(topVideo.url||ytChLink)}" target="_blank" rel="noopener">
      <img src="${esc(topVideo.thumbnail)}" style="width:100%;height:100%;object-fit:cover;position:absolute;inset:0;" alt="" />
    </a>`;
  } else {
    embedWrap.innerHTML = `<a class="drawer-embed-placeholder" href="${esc(ytChLink)}" target="_blank" rel="noopener">
      <span class="drawer-embed-play">▶</span>
      <span>Open YouTube channel</span>
    </a>`;
  }

  // Stats row
  document.getElementById("drawer-stats").innerHTML = `
    <div class="drawer-stat">
      <div class="drawer-stat-val">${channel.avg_discovery}</div>
      <div class="drawer-stat-lbl">Discovery</div>
    </div>
    <div class="drawer-stat">
      <div class="drawer-stat-val">${channel.avg_engagement}%</div>
      <div class="drawer-stat-lbl">Engagement</div>
    </div>
    <div class="drawer-stat">
      <div class="drawer-stat-val">${fmt(channel.avg_velocity)}</div>
      <div class="drawer-stat-lbl">Views/day</div>
    </div>
  `;

  // Platform links
  let platforms = `
    <a class="drawer-platform-link drawer-platform-yt" href="${esc(ytChLink)}" target="_blank" rel="noopener">▶ YouTube</a>
  `;
  if (sp.spotify_url) {
    platforms += `<a class="drawer-platform-link drawer-platform-sp" href="${esc(sp.spotify_url)}" target="_blank" rel="noopener">♫ Spotify</a>`;
  }
  if (sp.followers > 0) {
    platforms += `<span class="drawer-platform-link" style="cursor:default;opacity:.7">${fmt(sp.followers)} Spotify followers</span>`;
  }
  platforms += `<button class="drawer-platform-link drawer-platform-copy" onclick="copyChannelLink('${esc(ytChLink)}', this)">⎘ Copy link</button>`;
  document.getElementById("drawer-platforms").innerHTML = platforms;

  // Video list
  document.getElementById("drawer-videos").innerHTML = videos.map(v => `
    <a class="drawer-video-row" href="${esc(v.url)}" target="_blank" rel="noopener">
      <img class="drawer-video-thumb" src="${esc(v.thumbnail)}" alt="" loading="lazy" />
      <div class="drawer-video-info">
        <div class="drawer-video-title">${esc(v.title)}</div>
        <div class="drawer-video-meta">
          <span>${fmt(v.views)} views</span>
          <span class="hi">${v.engagement_rate}% eng</span>
          <span>${daysAgo(v.published_at)}</span>
        </div>
      </div>
      <div class="drawer-video-score">${v.discovery_score}</div>
    </a>`).join("") || `<div style="color:var(--muted);font-size:13px">No videos in current window</div>`;

  drawer.classList.add("open");
  drawer.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
}

function closeDrawer() {
  const drawer = document.getElementById("artist-drawer");
  if (!drawer) return;
  // Clear iframe to stop video playback
  const embed = document.getElementById("drawer-embed");
  if (embed) embed.innerHTML = "";
  drawer.classList.remove("open");
  drawer.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
}

function copyChannelLink(url, btn) {
  navigator.clipboard.writeText(url).then(() => {
    btn.textContent = "✓ Copied";
    btn.classList.add("copied");
    setTimeout(() => { btn.textContent = "⎘ Copy link"; btn.classList.remove("copied"); }, 2000);
  }).catch(() => {
    btn.textContent = "⎘ " + url;
  });
}
