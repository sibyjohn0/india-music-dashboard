const DATA_URL = "data/latest.json";

// ── Formatters ────────────────────────────────────────────────
const fmt = n => n >= 1e9 ? (n/1e9).toFixed(1)+"B" : n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e3 ? (n/1e3).toFixed(1)+"K" : String(n);
const fmtInr = n => n >= 1e7 ? "₹"+(n/1e7).toFixed(1)+"Cr" : n >= 1e5 ? "₹"+(n/1e5).toFixed(1)+"L" : n >= 1e3 ? "₹"+(n/1e3).toFixed(1)+"K" : "₹"+n;
const daysAgo = iso => { const d=(Date.now()-new Date(iso))/864e5; return d<1?"Today":d<2?"Yesterday":d<30?Math.floor(d)+"d ago":d<365?Math.floor(d/30)+"mo ago":Math.floor(d/365)+"y ago"; };
const fmtDate = iso => new Date(iso).toLocaleDateString("en-IN",{day:"numeric",month:"short",year:"numeric"});
const esc = s => String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");

const PAL = ["#a78bfa","#60a5fa","#34d399","#fbbf24","#f87171","#fb923c","#e879f9","#38bdf8","#4ade80","#c084fc"];

// ── State ─────────────────────────────────────────────────────
let allVideos = [], allChannels = [];

// ── Init ──────────────────────────────────────────────────────
async function init() {
  let data;
  try {
    data = await fetch(DATA_URL).then(r => r.json());
  } catch {
    document.querySelector("main").innerHTML =
      `<div style="text-align:center;padding:80px 0;color:#555;font-size:15px">No data yet — run the fetch script to get started.</div>`;
    return;
  }

  allVideos   = (data.videos || []).sort((a,b) => (b.discovery_score||0) - (a.discovery_score||0));
  allChannels = buildChannels(allVideos);

  const fetched = new Date(data.fetched_at);
  document.getElementById("last-updated").textContent =
    "Updated " + fetched.toLocaleDateString("en-IN",{day:"numeric",month:"short",hour:"2-digit",minute:"2-digit"});
  document.getElementById("total-badge").textContent = allVideos.length + " videos";

  populateDropdowns();
  renderHeroCards(allVideos.slice(0,3));
  renderPulseList(allVideos.slice(3, 18));
  renderBreakdowns(data.genre_breakdown||[], data.language_breakdown||[]);
  renderArtistGrid(allChannels);
  renderVideoList(allVideos);
  bindTabs();
  bindArtistControls();
  bindVideoControls();
}

// ── Channel aggregation ───────────────────────────────────────
function buildChannels(videos) {
  const map = {};
  for (const v of videos) {
    const cid = v.channel_id || v.channel;
    if (!map[cid]) map[cid] = {
      id: cid, name: v.channel, thumb: v.thumbnail,
      video_count:0, total_views:0, total_velocity:0,
      total_engagement:0, total_discovery:0,
      genres:{}, languages:{}, top_video: v,
    };
    const c = map[cid];
    c.video_count++;
    c.total_views      += v.views;
    c.total_velocity   += v.velocity||0;
    c.total_engagement += v.engagement_rate||0;
    c.total_discovery  += v.discovery_score||0;
    if ((v.discovery_score||0) > (c.top_video.discovery_score||0)) c.top_video = v;
    if (v.genre)    c.genres[v.genre]       = (c.genres[v.genre]||0)+1;
    if (v.language) c.languages[v.language] = (c.languages[v.language]||0)+1;
  }
  return Object.values(map).map(c => ({
    ...c,
    avg_velocity:   Math.round(c.total_velocity/c.video_count),
    avg_engagement: Math.round((c.total_engagement/c.video_count)*100)/100,
    avg_discovery:  Math.round((c.total_discovery/c.video_count)*10)/10,
    top_genre: Object.entries(c.genres).sort((a,b)=>b[1]-a[1])[0]?.[0]||"Indie",
    top_lang:  Object.entries(c.languages).sort((a,b)=>b[1]-a[1])[0]?.[0]||"Hindi",
  })).sort((a,b) => b.avg_discovery - a.avg_discovery);
}

// ── Hero cards ────────────────────────────────────────────────
function renderHeroCards(videos) {
  const ranks = ["#1 Discovery","#2 Discovery","#3 Discovery"];
  document.getElementById("hero-cards").innerHTML = videos.map((v,i) => `
    <a href="${esc(v.url)}" target="_blank" rel="noopener" class="hero-card">
      <img src="${esc(v.thumbnail)}" alt="" loading="lazy" />
      <div class="hero-card-overlay">
        <span class="hero-rank">${ranks[i]}</span>
        <span class="hero-score">${v.discovery_score??'—'}</span>
        <div class="hero-pills">
          <span class="pill pill-genre">${esc(v.genre)}</span>
          <span class="pill pill-lang">${esc(v.language)}</span>
          ${v.is_new ? '<span class="pill pill-new">NEW</span>' : ''}
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
}

// ── Pulse list (rank 4–18) ────────────────────────────────────
function renderPulseList(videos) {
  document.getElementById("pulse-list").innerHTML = videos.map((v,i) => `
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

// ── Breakdown bars ────────────────────────────────────────────
function renderBreakdowns(genres, langs) {
  const barHtml = (items, colorClass="") => {
    const max = items[0]?.[1] || 1;
    return items.slice(0,8).map(([label,count]) => `
      <div class="bar-item">
        <div class="bar-label">${esc(label)}</div>
        <div class="bar-track"><div class="bar-fill ${colorClass}" style="width:${Math.round(count/max*100)}%"></div></div>
        <div class="bar-count">${count}</div>
      </div>`).join("");
  };
  document.getElementById("genre-bars").innerHTML = barHtml(genres);
  document.getElementById("lang-bars").innerHTML  = barHtml(langs,"green");
}

// ── Artist grid ───────────────────────────────────────────────
function renderArtistGrid(channels) {
  document.getElementById("artist-grid").innerHTML = channels.map(c => `
    <a href="https://youtube.com/channel/${esc(c.id)}" target="_blank" rel="noopener" class="artist-card">
      <img class="artist-card-thumb" src="${esc(c.top_video.thumbnail)}" alt="" loading="lazy" />
      <div class="artist-card-body">
        <div class="artist-card-name" title="${esc(c.name)}">${esc(c.name)}</div>
        <div class="artist-card-pills">
          <span class="pill pill-genre">${esc(c.top_genre)}</span>
          <span class="pill pill-lang">${esc(c.top_lang)}</span>
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
          </div>
        </div>
      </div>
    </a>`).join("");
}

// ── Video list ────────────────────────────────────────────────
function renderVideoList(videos) {
  document.getElementById("video-list").innerHTML = videos.map((v,i) => `
    <a href="${esc(v.url)}" target="_blank" rel="noopener" class="video-row">
      <div class="video-row-num">${i+1}</div>
      <img class="video-row-thumb" src="${esc(v.thumbnail)}" alt="" loading="lazy" />
      <div class="video-row-info">
        <div class="video-row-title">${esc(v.title)}</div>
        <div class="video-row-channel">${esc(v.channel)}</div>
        <div class="video-row-pills">
          <span class="pill pill-genre">${esc(v.genre)}</span>
          <span class="pill pill-lang">${esc(v.language)}</span>
          ${v.is_new ? '<span class="pill pill-new">NEW</span>' : ''}
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

// ── Populate dropdowns ────────────────────────────────────────
function populateDropdowns() {
  const genres = [...new Set(allVideos.map(v=>v.genre).filter(Boolean))].sort();
  const langs  = [...new Set(allVideos.map(v=>v.language).filter(Boolean))].sort();
  [["v-genre",genres],["a-genre",genres]].forEach(([id,opts])=> opts.forEach(g=>document.getElementById(id).add(new Option(g,g))));
  [["v-lang",langs],["a-lang",langs]].forEach(([id,opts])=> opts.forEach(l=>document.getElementById(id).add(new Option(l,l))));
}

// ── Artist controls ───────────────────────────────────────────
function bindArtistControls() {
  function apply() {
    const q   = document.getElementById("a-search").value.toLowerCase();
    const srt = document.getElementById("a-sort").value;
    const gen = document.getElementById("a-genre").value;
    const lng = document.getElementById("a-lang").value;
    let cs = allChannels.filter(c =>
      (!q || c.name.toLowerCase().includes(q)) &&
      (gen==="all" || c.top_genre===gen) &&
      (lng==="all" || c.top_lang===lng)
    );
    cs = [...cs].sort((a,b)=>(b[srt]||0)-(a[srt]||0));
    renderArtistGrid(cs);
  }
  ["a-search","a-sort","a-genre","a-lang"].forEach(id=>
    document.getElementById(id).addEventListener(id==="a-search"?"input":"change", apply));
}

// ── Video controls ────────────────────────────────────────────
function bindVideoControls() {
  function apply() {
    const q   = document.getElementById("v-search").value.toLowerCase();
    const srt = document.getElementById("v-sort").value;
    const gen = document.getElementById("v-genre").value;
    const lng = document.getElementById("v-lang").value;
    let vs = allVideos.filter(v=>
      (!q || v.title.toLowerCase().includes(q) || v.channel.toLowerCase().includes(q)) &&
      (gen==="all" || v.genre===gen) &&
      (lng==="all" || v.language===lng)
    );
    vs = [...vs].sort((a,b)=>
      srt==="published_at" ? b.published_at.localeCompare(a.published_at) : (b[srt]||0)-(a[srt]||0)
    );
    renderVideoList(vs);
  }
  ["v-search","v-sort","v-genre","v-lang"].forEach(id=>
    document.getElementById(id).addEventListener(id==="v-search"?"input":"change", apply));
}

// ── Tabs ──────────────────────────────────────────────────────
function bindTabs() {
  let trendsLoaded = false;
  document.querySelectorAll(".tab").forEach(btn =>
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(t=>t.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-"+btn.dataset.tab).classList.add("active");
      if (btn.dataset.tab==="trends" && !trendsLoaded) { trendsLoaded=true; loadTrends(); }
    })
  );
}

// ── Trends ────────────────────────────────────────────────────
async function loadTrends() {
  const now = new Date();
  const months = Array.from({length:6},(_,i)=>{
    const d = new Date(now.getFullYear(), now.getMonth()-i, 1);
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`;
  }).reverse();

  const results = await Promise.all(months.map(m=>
    fetch(`data/monthly/${m}.json`).then(r=>r.ok?r.json():null).catch(()=>null)
  ));
  const monthly = results.filter(Boolean);
  document.getElementById("trends-loading").style.display = "none";

  if (!monthly.length) {
    document.getElementById("trends-loading").style.display = "block";
    document.getElementById("trends-loading").textContent = "No monthly data yet — check back after a few daily runs.";
    return;
  }

  document.getElementById("trends-grid").style.display       = "grid";
  document.getElementById("trends-table-wrap").style.display = "block";

  const labels  = monthly.map(m=>m.month);
  const allG    = [...new Set(monthly.flatMap(m=>(m.genre_breakdown||[]).map(g=>g[0])))];
  const allL    = [...new Set(monthly.flatMap(m=>(m.language_breakdown||[]).map(l=>l[0])))];
  const getC    = (m,key,field)=>(m[field]||[]).find(x=>x[0]===key)?.[1]||0;
  const lineOpts = () => ({
    plugins:{legend:{position:"bottom",labels:{color:"#666",font:{size:10},boxWidth:10}}},
    scales:{x:{ticks:{color:"#555",font:{size:10}},grid:{color:"#1a1a1a"}},y:{ticks:{color:"#555"},grid:{color:"#1a1a1a"}}},
  });
  const barOpts = cb => ({
    plugins:{legend:{display:false}},
    scales:{x:{ticks:{color:"#555",font:{size:10}},grid:{color:"#1a1a1a"}},y:{ticks:{color:"#555",callback:cb},grid:{color:"#1a1a1a"}}},
  });

  new Chart(document.getElementById("trend-genre"),{type:"line",data:{labels,datasets:allG.map((g,i)=>({label:g,data:monthly.map(m=>getC(m,g,"genre_breakdown")),borderColor:PAL[i%PAL.length],backgroundColor:"transparent",tension:.3,pointRadius:4}))},options:lineOpts()});
  new Chart(document.getElementById("trend-lang"),{type:"line",data:{labels,datasets:allL.map((l,i)=>({label:l,data:monthly.map(m=>getC(m,l,"language_breakdown")),borderColor:PAL[(i+4)%PAL.length],backgroundColor:"transparent",tension:.3,pointRadius:4}))},options:lineOpts()});
  new Chart(document.getElementById("trend-views"),{type:"bar",data:{labels,datasets:[{data:monthly.map(m=>m.total_views||0),backgroundColor:PAL[0],borderRadius:4}]},options:barOpts(v=>fmt(v))});
  new Chart(document.getElementById("trend-count"),{type:"bar",data:{labels,datasets:[{data:monthly.map(m=>m.total_videos||0),backgroundColor:PAL[2],borderRadius:4}]},options:barOpts(v=>v)});

  document.getElementById("trends-body").innerHTML = [...monthly].reverse().map(m=>`
    <tr>
      <td><strong>${m.month}</strong></td>
      <td>${m.total_videos||0}</td>
      <td>${fmt(m.total_views||0)}</td>
      <td><span class="pill pill-genre">${(m.genre_breakdown||[])[0]?.[0]||"—"}</span></td>
      <td><span class="pill pill-lang">${(m.language_breakdown||[])[0]?.[0]||"—"}</span></td>
      <td style="color:var(--muted)">${(m.top_channels||[])[0]?.[0]||"—"}</td>
    </tr>`).join("");
}

init();
