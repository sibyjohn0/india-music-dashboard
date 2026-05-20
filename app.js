const DATA_URL      = "data/latest.json";
const LFM_URL       = "data/lastfm_enrichment.json";
const TRACKER_URL   = "data/tracked_artists.json";
const INSIGHTS_URL  = "data/insights.json";
const SOCIAL_URL    = "data/social.json";
const SPOTIFY_URL   = "data/spotify_enrichment.json";

// ── Formatters ────────────────────────────────────────────────────────────────
const fmt    = n => n>=1e9?(n/1e9).toFixed(1)+"B":n>=1e6?(n/1e6).toFixed(1)+"M":n>=1e3?(n/1e3).toFixed(1)+"K":String(n);
const fmtInr = n => n>=1e7?"₹"+(n/1e7).toFixed(1)+"Cr":n>=1e5?"₹"+(n/1e5).toFixed(1)+"L":n>=1e3?"₹"+(n/1e3).toFixed(1)+"K":"₹"+n;
const daysAgo= iso=>{const d=(Date.now()-new Date(iso))/864e5;return d<1?"Today":d<2?"Yesterday":d<30?Math.floor(d)+"d ago":d<365?Math.floor(d/30)+"mo ago":Math.floor(d/365)+"y ago";};
const esc    = s => String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");

const PAL = ["#a78bfa","#60a5fa","#34d399","#fbbf24","#f87171","#fb923c","#e879f9","#38bdf8","#4ade80","#c084fc"];
const LANG_COLORS = {
  Tamil:"#f87171", Telugu:"#fb923c", Kannada:"#fbbf24", Malayalam:"#34d399",
  Bengali:"#38bdf8", Punjabi:"#a78bfa", Marathi:"#e879f9", "Hindi Indie":"#60a5fa",
  English:"#4ade80", Various:"#666"
};

// ── State ─────────────────────────────────────────────────────────────────────
let allVideos=[], allChannels=[], lfmData={}, trackerData=null, spotifyData={};

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  let data, insightsData = null, socialData = null;
  try {
    const NC = {cache:"no-cache"};
    const [ytRes, lfmRes, trackerRes, insightsRes, socialRes, spotifyRes] = await Promise.allSettled([
      fetch(DATA_URL, NC).then(r=>r.json()),
      fetch(LFM_URL,  NC).then(r=>r.json()).catch(()=>null),
      fetch(TRACKER_URL, NC).then(r=>r.json()).catch(()=>null),
      fetch(INSIGHTS_URL, NC).then(r=>r.json()).catch(()=>null),
      fetch(SOCIAL_URL,  NC).then(r=>r.json()).catch(()=>null),
      fetch(SPOTIFY_URL, NC).then(r=>r.json()).catch(()=>null),
    ]);
    data = ytRes.value;
    if (lfmRes.status==="fulfilled" && lfmRes.value) lfmData = lfmRes.value.artists||{};
    if (trackerRes.status==="fulfilled") trackerData = trackerRes.value;
    insightsData = (insightsRes.status==="fulfilled" && insightsRes.value) ? insightsRes.value : null;
    socialData   = (socialRes.status==="fulfilled"   && socialRes.value)   ? socialRes.value   : null;
    if (spotifyRes?.status==="fulfilled" && spotifyRes.value) spotifyData = spotifyRes.value.enrichment||{};
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
  renderDiscover(allVideos);
  renderBreakdowns(data.genre_breakdown||[], data.language_breakdown||[]);
  renderArtistGrid(allChannels);
  renderVideoList(allVideos);
  if (trackerData) renderRadar(trackerData.artists||[]);
  bindTabs(insightsData, socialData);
  bindDiscoverControls();
  bindArtistControls();
  bindVideoControls();
  if (trackerData) bindRadarControls();
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
  const trackerNames = new Set((trackerData?.artists||[]).map(a=>a.name.toLowerCase()));
  return Object.values(map).map(c=>{
    const lfm = lfmData[c.name]||{};
    return {
      ...c,
      avg_velocity:    Math.round(c.total_velocity/c.video_count),
      avg_engagement:  Math.round((c.total_engagement/c.video_count)*100)/100,
      avg_discovery:   Math.round((c.total_discovery/c.video_count)*10)/10,
      top_genre:       Object.entries(c.genres).sort((a,b)=>b[1]-a[1])[0]?.[0]||"Indie",
      top_lang:        Object.entries(c.languages).sort((a,b)=>b[1]-a[1])[0]?.[0]||"Hindi",
      lfm_listeners:   lfm.global_listeners||0,
      lfm_india_rank:  lfm.india_rank||null,
      multiplatform:   trackerNames.has(c.name.toLowerCase()),
    };
  }).sort((a,b)=>b.avg_discovery-a.avg_discovery);
}

// ── Dropdown population ───────────────────────────────────────────────────────
function populateDropdowns() {
  const genres = [...new Set(allVideos.map(v=>v.genre).filter(Boolean))].sort();
  const langs  = [...new Set(allVideos.map(v=>v.language).filter(Boolean))].sort();
  [["d-genre",genres],["v-genre",genres],["a-genre",genres]].forEach(([id,opts])=>
    opts.forEach(g=>document.getElementById(id).add(new Option(g,g))));
  [["d-lang",langs],["v-lang",langs],["a-lang",langs]].forEach(([id,opts])=>
    opts.forEach(l=>document.getElementById(id).add(new Option(l,l))));
  if (trackerData) {
    const rLangs = [...new Set(trackerData.artists.map(a=>a.language))].sort();
    const rGenres= [...new Set(trackerData.artists.map(a=>a.genre))].sort();
    rLangs.forEach(l=>document.getElementById("r-lang").add(new Option(l,l)));
    rGenres.forEach(g=>document.getElementById("r-genre").add(new Option(g,g)));
  }
}

// ── Discover ──────────────────────────────────────────────────────────────────
function renderDiscover(videos) {
  // De-duplicate by channel: max 2 per channel in the Discover view
  // so one prolific uploader can't flood hero + pulse slots
  const seen = {}; const deduped = [];
  for (const v of videos) {
    const key = v.channel_id || v.channel;
    if ((seen[key] || 0) < 2) { deduped.push(v); seen[key] = (seen[key]||0)+1; }
    if (deduped.length >= 21) break;
  }
  const top = deduped.slice(0,3);
  const rest= deduped.slice(3,18);
  const ranks = ["#1 Discovery","#2 Discovery","#3 Discovery"];
  document.getElementById("hero-cards").innerHTML = top.map((v,i)=>`
    <a href="${esc(v.url)}" target="_blank" rel="noopener" class="hero-card">
      <img src="${esc(v.thumbnail)}" alt="" loading="lazy" />
      <div class="hero-card-overlay">
        <span class="hero-rank">${ranks[i]}</span>
        <span class="hero-score">${v.discovery_score??'—'}</span>
        <div class="hero-pills">
          <span class="pill pill-genre">${esc(v.genre)}</span>
          <span class="pill pill-lang">${esc(v.language)}</span>
          ${v.is_new?'<span class="pill pill-new">NEW</span>':''}
        </div>
        <div class="hero-title">${esc(v.title)}</div>
        <div class="hero-channel">${esc(v.channel)} · ${daysAgo(v.published_at)}</div>
        <div class="hero-stats">
          <span><strong>${v.engagement_rate}%</strong> engagement</span>
          <span><strong>${fmt(v.views)}</strong> views</span>
          <span><strong>${fmt(v.velocity)}</strong>/day</span>
        </div>
      </div>
    </a>`).join("");
  document.getElementById("pulse-list").innerHTML = rest.map((v,i)=>`
    <a href="${esc(v.url)}" target="_blank" rel="noopener" class="pulse-item">
      <div class="pulse-rank">${i+4}</div>
      <img class="pulse-thumb" src="${esc(v.thumbnail)}" alt="" loading="lazy" />
      <div class="pulse-info">
        <div class="pulse-title">${esc(v.title)}</div>
        <div class="pulse-channel">${esc(v.channel)}</div>
        <div class="pulse-meta">
          <span class="hi">${v.engagement_rate}% eng</span>
          <span>${fmt(v.views)} views</span>
          <span>${daysAgo(v.published_at)}</span>
        </div>
      </div>
      <div class="pulse-right">
        <div class="pulse-score">${v.discovery_score??'—'}</div>
        <div class="pulse-score-label">score</div>
      </div>
    </a>`).join("");
}

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
}

function applyDiscover() {
  const lang    = document.getElementById("d-lang").value;
  const genre   = document.getElementById("d-genre").value;
  const srt     = document.getElementById("d-sort").value;
  const newOnly = document.getElementById("d-new-only").dataset.on==="true";
  let vs = allVideos.filter(v=>
    (lang==="all"  || v.language===lang) &&
    (genre==="all" || v.genre===genre) &&
    (!newOnly || v.is_new)
  );
  vs = [...vs].sort((a,b)=>
    srt==="published_at"?b.published_at.localeCompare(a.published_at):(b[srt]||0)-(a[srt]||0));
  document.getElementById("d-hero-label").textContent =
    vs.length===allVideos.length ? "Today's Top Finds" : `Top Finds — ${vs.length} matching`;
  renderDiscover(vs);
}

// ── Breakdown bars ────────────────────────────────────────────────────────────
function renderBreakdowns(genres, langs) {
  const barHtml = (items, colorClass="") => {
    const max = items[0]?.[1]||1;
    return items.slice(0,8).map(([label,count])=>`
      <div class="bar-item">
        <div class="bar-label">${esc(label)}</div>
        <div class="bar-track"><div class="bar-fill ${colorClass}" style="width:${Math.round(count/max*100)}%"></div></div>
        <div class="bar-count">${count}</div>
      </div>`).join("");
  };
  document.getElementById("genre-bars").innerHTML = barHtml(genres);
  document.getElementById("lang-bars").innerHTML  = barHtml(langs,"green");
}

// ── Artist grid ───────────────────────────────────────────────────────────────
function renderArtistGrid(channels) {
  if (!channels.length) {
    document.getElementById("artist-grid").innerHTML =
      `<div class="empty-state">No artists match your filters.</div>`;
    return;
  }
  document.getElementById("artist-grid").innerHTML = channels.map(c=>{
    const sp = spotifyData[c.name] || {};
    const spLink = sp.spotify_url
      ? `<a class="spotify-badge" href="${esc(sp.spotify_url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">♫ Spotify</a>`
      : "";
    const spFollowers = sp.followers > 0
      ? `<div>${fmt(sp.followers)} sp. followers</div>` : "";
    return `
    <a href="https://youtube.com/channel/${esc(c.id)}" target="_blank" rel="noopener" class="artist-card">
      <img class="artist-card-thumb" src="${esc(c.top_video.thumbnail||'')}" alt="" loading="lazy" />
      <div class="artist-card-body">
        <div class="artist-card-name" title="${esc(c.name)}">${esc(c.name)}</div>
        <div class="artist-card-pills">
          <span class="pill pill-genre">${esc(c.top_genre)}</span>
          <span class="pill pill-lang">${esc(c.top_lang)}</span>
          ${c.multiplatform?'<span class="pill pill-new">LFM</span>':''}
          ${spLink}
        </div>
        <div class="artist-card-stats">
          <div>
            <div class="artist-stat-score">${c.avg_discovery}</div>
            <div class="artist-stat-label">discovery</div>
          </div>
          <div class="artist-meta">
            <div>${c.avg_engagement}% eng</div>
            <div>${fmt(c.total_views)} views</div>
            <div>${c.video_count} video${c.video_count>1?"s":""}</div>
            ${spFollowers}
            ${c.lfm_india_rank?`<div class="india-rank-sm">#${c.lfm_india_rank} India</div>`:''}
          </div>
        </div>
      </div>
    </a>`;
  }).join("");
}

function bindArtistControls() {
  function apply() {
    const q      = document.getElementById("a-search").value.toLowerCase();
    const srt    = document.getElementById("a-sort").value;
    const gen    = document.getElementById("a-genre").value;
    const lng    = document.getElementById("a-lang").value;
    const minEng = parseFloat(document.getElementById("a-min-eng").value)||0;
    const minVid = parseInt(document.getElementById("a-min-videos").value)||1;
    const mpOnly = document.getElementById("a-multiplatform").dataset.on==="true";
    let cs = allChannels.filter(c=>
      (!q         || c.name.toLowerCase().includes(q)) &&
      (gen==="all"|| c.top_genre===gen) &&
      (lng==="all"|| c.top_lang===lng) &&
      c.avg_engagement >= minEng &&
      c.video_count    >= minVid &&
      (!mpOnly || c.multiplatform)
    );
    cs = [...cs].sort((a,b)=>(b[srt]||0)-(a[srt]||0));
    renderArtistGrid(cs);
  }
  const mpBtn = document.getElementById("a-multiplatform");
  mpBtn.addEventListener("click",()=>{
    const on = mpBtn.dataset.on==="true";
    mpBtn.dataset.on = String(!on);
    mpBtn.classList.toggle("active",!on);
    apply();
  });
  ["a-search","a-sort","a-genre","a-lang","a-min-eng","a-min-videos"].forEach(id=>
    document.getElementById(id).addEventListener(id==="a-search"?"input":"change", apply));
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
        <div class="video-score-sub">score</div>
        <div class="video-metrics-row">
          <span class="hi">${v.engagement_rate}%</span>
          <span class="bl">${fmt(v.velocity)}/d</span>
          <span>${fmt(v.views)}</span>
          <span>${daysAgo(v.published_at)}</span>
        </div>
      </div>
    </a>`).join("");
}

function bindVideoControls() {
  const newBtn = document.getElementById("v-new-only");
  newBtn.addEventListener("click",()=>{
    const on = newBtn.dataset.on==="true";
    newBtn.dataset.on=String(!on);
    newBtn.classList.toggle("active",!on);
    applyVideos();
  });
  ["v-search","v-sort","v-genre","v-lang","v-window","v-min-eng"].forEach(id=>
    document.getElementById(id).addEventListener(id==="v-search"?"input":"change", applyVideos));
}

function applyVideos() {
  const q      = document.getElementById("v-search").value.toLowerCase();
  const srt    = document.getElementById("v-sort").value;
  const gen    = document.getElementById("v-genre").value;
  const lng    = document.getElementById("v-lang").value;
  const win    = parseInt(document.getElementById("v-window").value)||0;
  const minEng = parseFloat(document.getElementById("v-min-eng").value)||0;
  const newOnly= document.getElementById("v-new-only").dataset.on==="true";
  const cutoff = win ? Date.now() - win*864e5 : 0;
  let vs = allVideos.filter(v=>
    (!q         || v.title.toLowerCase().includes(q)||v.channel.toLowerCase().includes(q)) &&
    (gen==="all"|| v.genre===gen) &&
    (lng==="all"|| v.language===lng) &&
    (!cutoff    || new Date(v.published_at)>=cutoff) &&
    v.engagement_rate >= minEng &&
    (!newOnly   || v.is_new)
  );
  vs = [...vs].sort((a,b)=>
    srt==="published_at"?b.published_at.localeCompare(a.published_at):(b[srt]||0)-(a[srt]||0));
  renderVideoList(vs);
}

// ── Radar ─────────────────────────────────────────────────────────────────────
const TREND_ICON = {new:"✦", rising:"▲", stable:"─", falling:"▼"};
const TREND_CLS  = {new:"trend-new", rising:"trend-up", stable:"trend-flat", falling:"trend-dn"};

function renderRadar(artists) {
  if (!artists.length) {
    document.getElementById("radar-grid").innerHTML =
      `<div class="empty-state">No tracked artists yet — run tracker.py discover + export.</div>`;
    return;
  }
  document.getElementById("radar-grid").innerHTML = artists.map(a=>{
    const col   = LANG_COLORS[a.language]||"#666";
    const trend = a.trend||"new";
    const rankBadge = a.latest_india_rank
      ? `<span class="radar-rank">#${a.latest_india_rank} India</span>` : "";
    const growthBadge = a.growth_pct!=null
      ? `<span class="radar-growth ${a.growth_pct>=0?"growth-pos":"growth-neg"}">${a.growth_pct>=0?"+":""}${a.growth_pct}%</span>` : "";
    return `
    <div class="radar-card" style="--lang-col:${col}">
      <div class="radar-card-top">
        <div class="radar-card-name">${esc(a.name)}</div>
        <span class="trend-badge ${TREND_CLS[trend]}">${TREND_ICON[trend]} ${trend}</span>
      </div>
      <div class="radar-pills">
        <span class="pill" style="background:${col}22;color:${col};border-color:${col}44">${esc(a.language)}</span>
        <span class="pill pill-genre">${esc(a.genre)}</span>
      </div>
      <div class="radar-stats">
        <div class="radar-stat">
          <div class="radar-stat-val">${a.latest_india_listeners>0?fmt(a.latest_india_listeners):"—"}</div>
          <div class="radar-stat-lbl">India listeners</div>
        </div>
        <div class="radar-stat">
          <div class="radar-stat-val">${fmt(a.latest_global_listeners)}</div>
          <div class="radar-stat-lbl">Global</div>
        </div>
      </div>
      <div class="radar-badges">${rankBadge}${growthBadge}</div>
    </div>`;
  }).join("");

  // Language breakdown bars
  const byLang = {};
  artists.forEach(a=>{ byLang[a.language]=(byLang[a.language]||0)+1; });
  const maxL = Math.max(...Object.values(byLang));
  document.getElementById("radar-lang-bars").innerHTML = Object.entries(byLang)
    .sort((a,b)=>b[1]-a[1]).map(([l,c])=>`
    <div class="bar-item">
      <div class="bar-label">${esc(l)}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.round(c/maxL*100)}%;background:${LANG_COLORS[l]||"#666"}"></div></div>
      <div class="bar-count">${c}</div>
    </div>`).join("");

  // Trend breakdown
  const byTrend = {new:0,rising:0,stable:0,falling:0};
  artists.forEach(a=>{ byTrend[a.trend||"new"]++; });
  const maxT = Math.max(...Object.values(byTrend));
  const trendCols = {new:"#a78bfa",rising:"#34d399",stable:"#60a5fa",falling:"#f87171"};
  document.getElementById("radar-trend-bars").innerHTML = Object.entries(byTrend)
    .filter(([,c])=>c>0).map(([t,c])=>`
    <div class="bar-item">
      <div class="bar-label">${TREND_ICON[t]} ${t}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.round(c/maxT*100)}%;background:${trendCols[t]}"></div></div>
      <div class="bar-count">${c}</div>
    </div>`).join("");
}

function bindRadarControls() {
  const chartBtn = document.getElementById("r-chart-only");
  chartBtn.addEventListener("click",()=>{
    const on = chartBtn.dataset.on==="true";
    chartBtn.dataset.on=String(!on);
    chartBtn.classList.toggle("active",!on);
    applyRadar();
  });
  ["r-search","r-lang","r-genre","r-sort","r-trend"].forEach(id=>
    document.getElementById(id).addEventListener(id==="r-search"?"input":"change", applyRadar));
}

function applyRadar() {
  if (!trackerData) return;
  const q         = document.getElementById("r-search").value.toLowerCase();
  const lang      = document.getElementById("r-lang").value;
  const genre     = document.getElementById("r-genre").value;
  const srt       = document.getElementById("r-sort").value;
  const trend     = document.getElementById("r-trend").value;
  const chartOnly = document.getElementById("r-chart-only").dataset.on==="true";
  let as = trackerData.artists.filter(a=>
    (!q         || a.name.toLowerCase().includes(q)) &&
    (lang==="all" || a.language===lang) &&
    (genre==="all"|| a.genre===genre) &&
    (trend==="all"|| a.trend===trend) &&
    (!chartOnly || a.latest_india_rank)
  );
  as = [...as].sort((a,b)=>{
    if (srt==="latest_india_rank") return (a.latest_india_rank||999)-(b.latest_india_rank||999);
    if (srt==="growth_pct") return (b.growth_pct||0)-(a.growth_pct||0);
    return (b[srt]||0)-(a[srt]||0);
  });
  renderRadar(as);
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
function bindTabs(insightsData, socialData) {
  let trendsLoaded = false, buzzLoaded = false;
  document.querySelectorAll(".tab").forEach(btn=>
    btn.addEventListener("click",()=>{
      document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(t=>t.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-"+btn.dataset.tab).classList.add("active");
      if (btn.dataset.tab==="trends"&&!trendsLoaded){
        trendsLoaded=true;
        loadTrends();
        if (insightsData) renderInsights(insightsData);
      }
      if (btn.dataset.tab==="buzz"&&!buzzLoaded){
        buzzLoaded=true;
        renderBuzz(socialData);
      }
    })
  );
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
  document.getElementById("trends-grid").style.display="grid";
  document.getElementById("trends-table-wrap").style.display="block";
  buildTrendToggles();
  drawTrendCharts();
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
    loading.textContent = "No social data yet — run scripts/fetch_social.py to populate.";
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
  const feedPosts   = artistOnly ? [] : (data.feed||[]).filter(filter);

  renderBuzzArtistSection(artistPosts);
  renderBuzzFeed(feedPosts);
}

function renderBuzzArtistSection(posts) {
  const hd     = document.getElementById("buzz-artist-hd");
  const blocks = document.getElementById("buzz-artist-blocks");
  const count  = document.getElementById("buzz-artist-count");

  if (!posts.length) {
    hd.style.display = "none";
    blocks.innerHTML = "";
    return;
  }
  hd.style.display = "flex";
  count.textContent = posts.length;

  // Group by artist
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

function renderBuzzFeed(posts) {
  const hd    = document.getElementById("buzz-feed-hd");
  const feed  = document.getElementById("buzz-feed");
  const count = document.getElementById("buzz-feed-count");

  hd.style.display = posts.length ? "flex" : "none";
  count.textContent = posts.length;
  feed.innerHTML = posts.map(p => buzzCardHTML(p)).join("");
}

function buzzCardHTML(p) {
  const platformLabel = p.platform === "reddit"
    ? `r/${esc(p.subreddit||"reddit")}`
    : `twitter.com`;
  const platformClass = p.platform === "reddit" ? "buzz-platform-reddit" : "buzz-platform-twitter";
  const score = p.score > 0
    ? `<span class="buzz-score">▲ ${p.score}</span>` : "";
  const langColor = LANG_COLORS[p.language] || "#666";

  return `<a class="buzz-card" href="${esc(p.url)}" target="_blank" rel="noopener">
    <div class="buzz-card-header">
      <span class="buzz-platform ${platformClass}">${platformLabel}</span>
      ${score}
      <span class="buzz-lang-pill" style="--lc:${langColor}">${esc(p.language||"")}</span>
      <span class="buzz-date">${esc(p.date||"")}</span>
    </div>
    <div class="buzz-title">${esc(p.title)}</div>
    ${p.snippet ? `<div class="buzz-snippet">${esc(p.snippet)}</div>` : ""}
  </a>`;
}

init();
