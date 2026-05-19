const DATA_URL  = "data/latest.json";
const LFM_URL   = "data/lastfm_enrichment.json";

// ── Formatters ────────────────────────────────────────────────
function fmt(n) {
  if (n >= 1e9) return (n / 1e9).toFixed(1) + "B";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return String(n);
}
function fmtInr(n) {
  if (n >= 1e7) return "₹" + (n / 1e7).toFixed(1) + "Cr";
  if (n >= 1e5) return "₹" + (n / 1e5).toFixed(1) + "L";
  if (n >= 1e3) return "₹" + (n / 1e3).toFixed(1) + "K";
  return "₹" + n;
}
function daysAgo(iso) {
  const d = (Date.now() - new Date(iso)) / 864e5;
  if (d < 1) return "Today";
  if (d < 2) return "Yesterday";
  if (d < 30) return Math.floor(d) + "d ago";
  if (d < 365) return Math.floor(d / 30) + "mo ago";
  return Math.floor(d / 365) + "y ago";
}
function fmtDate(iso) {
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}
function fmtDelta(delta, isNew) {
  if (isNew) return `<span class="delta-new">NEW</span>`;
  if (!delta) return `<span style="color:#444">—</span>`;
  return `<span class="delta-pos">+${fmt(delta)}</span>`;
}

// ── State ─────────────────────────────────────────────────────
let allVideos = [], allChannels = [], lfmData = {};

// ── Chart palette ─────────────────────────────────────────────
const PAL = ["#a78bfa","#60a5fa","#34d399","#facc15","#f87171",
             "#fb923c","#e879f9","#38bdf8","#4ade80","#fbbf24",
             "#c084fc","#67e8f9","#86efac","#fca5a5","#fdba74"];

// ── Init ──────────────────────────────────────────────────────
async function init() {
  let data;
  try {
    const [ytRes, lfmRes] = await Promise.allSettled([fetch(DATA_URL), fetch(LFM_URL)]);
    data = await ytRes.value.json();
    if (lfmRes.status === "fulfilled") {
      const lfm = await lfmRes.value.json();
      lfmData = lfm.artists || {};
    }
  } catch {
    document.querySelector("main").innerHTML = `
      <div style="text-align:center;padding:80px 0;color:#888">
        <div style="font-size:40px;margin-bottom:16px">📡</div>
        <div style="font-size:18px;font-weight:600;margin-bottom:8px">No data yet</div>
        <div>Run: <code>YOUTUBE_API_KEY=... python3 scripts/fetch_youtube.py</code></div>
      </div>`;
    return;
  }

  allVideos = (data.videos || []).sort((a,b) => b.discovery_score - a.discovery_score);
  allChannels = buildChannels(allVideos);

  const fetched = new Date(data.fetched_at);
  document.getElementById("last-updated").textContent =
    "Updated " + fetched.toLocaleDateString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
  document.getElementById("total-badge").textContent = allVideos.length + " indie videos";

  populateFilters(data);
  renderStats(data);
  renderTopCards(allVideos.slice(0, 3));
  renderCharts(data);
  renderTagCloud(data.top_keywords || []);
  renderChannelTable(allChannels);
  renderVideoTable(allVideos);
  bindTabs();
  bindVideoControls();
  bindChannelControls();
}

// ── Populate filter dropdowns ─────────────────────────────────
function populateFilters(data) {
  const genres = [...new Set(allVideos.map(v => v.genre).filter(Boolean))].sort();
  const langs  = [...new Set(allVideos.map(v => v.language).filter(Boolean))].sort();

  [["filter-genre", genres], ["ch-genre", genres]].forEach(([id, opts]) => {
    const sel = document.getElementById(id);
    opts.forEach(g => sel.add(new Option(g, g)));
  });
  [["filter-lang", langs], ["ch-lang", langs]].forEach(([id, opts]) => {
    const sel = document.getElementById(id);
    opts.forEach(l => sel.add(new Option(l, l)));
  });
}

// ── Channel aggregation ───────────────────────────────────────
function buildChannels(videos) {
  const map = {};
  for (const v of videos) {
    const cid = v.channel_id || v.channel;
    if (!map[cid]) {
      map[cid] = {
        id: cid, name: v.channel,
        video_count: 0, total_views: 0,
        total_velocity: 0, total_earnings: 0, total_engagement: 0, total_discovery: 0,
        views_delta: 0, top_video: v,
        genres: {}, languages: {},
      };
    }
    const c = map[cid];
    c.video_count++;
    c.total_views   += v.views;
    c.total_velocity+= v.velocity || 0;
    c.total_earnings+= v.earnings_est_inr || 0;
    c.total_engagement += v.engagement_rate || 0;
    c.views_delta    += v.views_delta || 0;
    c.total_discovery+= v.discovery_score || 0;
    if (v.discovery_score > (c.top_video.discovery_score||0)) c.top_video = v;
    if (v.genre)    c.genres[v.genre]       = (c.genres[v.genre] || 0) + 1;
    if (v.language) c.languages[v.language] = (c.languages[v.language] || 0) + 1;
  }
  return Object.values(map).map(c => {
    const lfm = lfmData[c.name] || {};
    return {
      ...c,
      avg_velocity:       Math.round(c.total_velocity / c.video_count),
      avg_engagement:     Math.round((c.total_engagement / c.video_count) * 100) / 100,
      avg_discovery:      Math.round((c.total_discovery / c.video_count) * 10) / 10,
      top_genre:          Object.entries(c.genres).sort((a,b)=>b[1]-a[1])[0]?.[0] || "Indie",
      top_lang:           Object.entries(c.languages).sort((a,b)=>b[1]-a[1])[0]?.[0] || "Hindi",
      lfm_listeners:      lfm.global_listeners || 0,
      lfm_india_listeners:lfm.india_listeners  || 0,
      lfm_india_rank:     lfm.india_rank        || null,
    };
  }).sort((a, b) => b.avg_discovery - a.avg_discovery);
}

// ── Stats row ─────────────────────────────────────────────────
function renderStats(data) {
  const vs = data.videos;
  const totalViews    = vs.reduce((s, v) => s + v.views, 0);
  const totalEarnings = vs.reduce((s, v) => s + (v.earnings_est_inr || 0), 0);
  const avgEng        = vs.reduce((s, v) => s + v.engagement_rate, 0) / (vs.length || 1);
  const topVelocity   = [...vs].sort((a, b) => (b.velocity||0) - (a.velocity||0))[0];
  const newToday      = vs.filter(v => v.is_new).length;
  const topGenre      = (data.genre_breakdown || [])[0];
  const topLang       = (data.language_breakdown || [])[0];

  const topDisc = allVideos[0];
  const stats = [
    { label: "Artists Found",       value: allChannels.length,             sub: "independent channels" },
    { label: "Videos Tracked",      value: vs.length,                      sub: "last 90 days, no major labels" },
    { label: "Top Discovery",       value: topDisc ? topDisc.discovery_score : "—", sub: topDisc?.channel || "" },
    { label: "Avg Engagement",      value: avgEng.toFixed(2) + "%",         sub: "above 2% = highly engaged audience" },
    { label: "New Today",           value: newToday,                        sub: "not seen in previous run" },
    { label: "Top Genre",           value: topGenre?.[0] || "—",            sub: `${topGenre?.[1] || 0} videos` },
    { label: "Top Language",        value: topLang?.[0] || "—",             sub: `${topLang?.[1] || 0} videos` },
  ];

  document.getElementById("stats-row").innerHTML = stats.map(s => `
    <div class="stat-card">
      <div class="stat-label">${s.label}</div>
      <div class="stat-value">${s.value}</div>
      <div class="stat-sub">${s.sub}</div>
    </div>`).join("");
}

// ── Top cards (by velocity) ───────────────────────────────────
function renderTopCards(videos) {
  const labels = ["🔭 Top Discovery", "✨ #2 Discovery", "⚡ #3 Discovery"];
  document.getElementById("top-cards").innerHTML = videos.map((v, i) => `
    <a href="${v.url}" target="_blank" rel="noopener" class="top-card ${i===0?"rank-1":""}">
      <img src="${v.thumbnail}" alt="" loading="lazy" />
      <div class="top-card-body">
        <div class="top-card-rank">${labels[i]}</div>
        <div class="top-card-title">${v.title}</div>
        <div class="top-card-channel">${v.channel} · ${daysAgo(v.published_at)}</div>
        <div class="top-card-tags">
          <span class="pill pill-genre">${v.genre}</span>
          <span class="pill pill-lang">${v.language}</span>
        </div>
        <div class="top-card-stats">
          <div class="top-card-stat"><span>Score </span><strong>${v.discovery_score}</strong></div>
          <div class="top-card-stat"><span>Engagement </span>${v.engagement_rate}%</div>
          <div class="top-card-stat"><span>Views </span>${fmt(v.views)}</div>
        </div>
      </div>
    </a>`).join("");
}

// ── Charts ────────────────────────────────────────────────────
function renderCharts(data) {
  const vs = data.videos;

  // Velocity top 15
  const topVel = [...vs].sort((a,b)=>(b.velocity||0)-(a.velocity||0)).slice(0,15);
  new Chart(document.getElementById("velocity-chart"), {
    type: "bar",
    data: { labels: topVel.map(v => v.title.slice(0,20)+"…"), datasets: [{ data: topVel.map(v=>v.velocity||0), backgroundColor: PAL, borderRadius: 4 }] },
    options: chartOpts(v => fmt(v)+"/d"),
  });

  // Genre doughnut
  const genres = data.genre_breakdown || [];
  new Chart(document.getElementById("genre-chart"), {
    type: "doughnut",
    data: { labels: genres.map(g=>g[0]), datasets: [{ data: genres.map(g=>g[1]), backgroundColor: PAL, borderWidth: 0 }] },
    options: { plugins: { legend: { position: "right", labels: { color: "#aaa", font: { size: 11 } } } } },
  });

  // Language doughnut
  const langs = data.language_breakdown || [];
  new Chart(document.getElementById("lang-chart"), {
    type: "doughnut",
    data: { labels: langs.map(l=>l[0]), datasets: [{ data: langs.map(l=>l[1]), backgroundColor: PAL.slice(5), borderWidth: 0 }] },
    options: { plugins: { legend: { position: "right", labels: { color: "#aaa", font: { size: 11 } } } } },
  });

  // Views top 15
  const top15 = vs.slice(0,15);
  new Chart(document.getElementById("views-chart"), {
    type: "bar",
    data: { labels: top15.map(v=>v.title.slice(0,20)+"…"), datasets: [{ data: top15.map(v=>v.views), backgroundColor: PAL, borderRadius: 4 }] },
    options: chartOpts(v => fmt(v)),
  });
}

function chartOpts(tickFmt) {
  return {
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: "#888", font: { size: 10 } }, grid: { color: "#1a1a1a" } },
      y: { ticks: { color: "#888", callback: tickFmt }, grid: { color: "#1a1a1a" } },
    },
  };
}

// ── Tag cloud ─────────────────────────────────────────────────
function renderTagCloud(keywords) {
  const max = keywords[0]?.count || 1;
  document.getElementById("tag-cloud").innerHTML = keywords.map(({ tag, count }) => {
    const r = count / max;
    const cls = r > 0.6 ? "tag-lg" : r > 0.3 ? "tag-md" : "tag-sm";
    return `<span class="tag ${cls}">${tag} <span style="opacity:.4">${count}</span></span>`;
  }).join("");
}

// ── Channel table ─────────────────────────────────────────────
function renderChannelTable(channels) {
  document.getElementById("channel-body").innerHTML = channels.map((c, i) => `
    <tr>
      <td style="color:#444;font-size:12px">${i+1}</td>
      <td>
        <div class="video-cell">
          <img class="video-thumb" src="${c.top_video.thumbnail}" alt="" loading="lazy" />
          <div class="video-info">
            <a href="https://youtube.com/channel/${c.id}" target="_blank" rel="noopener">${c.name}</a>
            <div class="video-channel">${c.video_count} video${c.video_count>1?"s":""} · <a href="${c.top_video.url}" target="_blank" rel="noopener" style="color:#666">${c.top_video.title.slice(0,38)}…</a></div>
          </div>
        </div>
      </td>
      <td class="num">${c.video_count}</td>
      <td class="num">${fmt(c.total_views)}</td>
      <td class="num velocity">${fmt(c.avg_velocity)}<span style="color:#555;font-size:11px">/d</span></td>
      <td class="num earnings">${fmtInr(c.total_earnings)}</td>
      <td class="num eng-rate">${c.avg_engagement}%</td>
      <td class="num disc-score">${c.avg_discovery}</td>
      <td class="num">${c.lfm_listeners ? fmt(c.lfm_listeners) : '<span style="color:#444">—</span>'}</td>
      <td class="num">${c.lfm_india_rank ? `<span class="india-rank">#${c.lfm_india_rank}</span>` : '<span style="color:#444">—</span>'}</td>
      <td><span class="pill pill-genre">${c.top_genre}</span></td>
    </tr>`).join("");
}

// ── Video table ───────────────────────────────────────────────
function renderVideoTable(videos) {
  document.getElementById("table-body").innerHTML = videos.map((v, i) => `
    <tr>
      <td style="color:#444;font-size:12px">${i+1}</td>
      <td>
        <div class="video-cell">
          <img class="video-thumb" src="${v.thumbnail}" alt="" loading="lazy" />
          <div class="video-info">
            <a href="${v.url}" target="_blank" rel="noopener">${v.title}</a>
            <div class="video-channel">${v.channel}</div>
          </div>
        </div>
      </td>
      <td class="num disc-score">${v.discovery_score}</td>
      <td class="num">${fmt(v.views)}</td>
      <td class="num">${fmtDelta(v.views_delta, v.is_new)}</td>
      <td class="num eng-rate">${v.engagement_rate}%</td>
      <td class="num velocity">${fmt(v.velocity||0)}<span style="color:#555;font-size:11px">/d</span></td>
      <td class="num" title="${fmtDate(v.published_at)}">${daysAgo(v.published_at)}</td>
      <td><span class="pill pill-genre">${v.genre}</span></td>
      <td><span class="pill pill-lang">${v.language}</span></td>
    </tr>`).join("");
}

// ── Video controls ────────────────────────────────────────────
function bindVideoControls() {
  function apply() {
    const q   = document.getElementById("search").value.toLowerCase();
    const srt = document.getElementById("sort-by").value;
    const gen = document.getElementById("filter-genre").value;
    const lng = document.getElementById("filter-lang").value;

    let vs = allVideos.filter(v =>
      (!q   || v.title.toLowerCase().includes(q) || v.channel.toLowerCase().includes(q)) &&
      (gen === "all" || v.genre    === gen) &&
      (lng === "all" || v.language === lng)
    );
    vs = [...vs].sort((a, b) =>
      srt === "published_at" ? b.published_at.localeCompare(a.published_at) :
      (b[srt]||0) - (a[srt]||0)
    );
    renderVideoTable(vs);
  }
  ["search","sort-by","filter-genre","filter-lang"].forEach(id =>
    document.getElementById(id).addEventListener(id==="search"?"input":"change", apply)
  );
}

// ── Channel controls ──────────────────────────────────────────
function bindChannelControls() {
  function apply() {
    const q   = document.getElementById("ch-search").value.toLowerCase();
    const srt = document.getElementById("ch-sort").value;
    const gen = document.getElementById("ch-genre").value;
    const lng = document.getElementById("ch-lang").value;

    let cs = allChannels.filter(c =>
      (!q   || c.name.toLowerCase().includes(q)) &&
      (gen === "all" || c.top_genre === gen) &&
      (lng === "all" || c.top_lang  === lng)
    );
    cs = [...cs].sort((a, b) => (b[srt]||0) - (a[srt]||0));
    renderChannelTable(cs);
  }
  ["ch-search","ch-sort","ch-genre","ch-lang"].forEach(id =>
    document.getElementById(id).addEventListener(id==="ch-search"?"input":"change", apply)
  );
}

// ── Trends ────────────────────────────────────────────────────
async function loadTrends() {
  // Try to load up to 6 monthly files
  const now = new Date();
  const months = [];
  for (let i = 0; i < 6; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    months.unshift(`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`);
  }

  const results = await Promise.all(months.map(m =>
    fetch(`data/monthly/${m}.json`).then(r => r.ok ? r.json() : null).catch(() => null)
  ));
  const monthly = results.filter(Boolean);

  document.getElementById("trends-loading").style.display = "none";

  if (monthly.length === 0) {
    document.getElementById("trends-loading").style.display = "block";
    document.getElementById("trends-loading").textContent = "No monthly data yet — check back after the first daily run.";
    return;
  }

  document.getElementById("trends-charts").style.display  = "grid";
  document.getElementById("trends-charts2").style.display = "grid";
  document.getElementById("trends-table-wrap").style.display = "block";

  const labels = monthly.map(m => m.month);

  // All genres/langs seen across months
  const allGenres = [...new Set(monthly.flatMap(m => (m.genre_breakdown||[]).map(g=>g[0])))];
  const allLangs  = [...new Set(monthly.flatMap(m => (m.language_breakdown||[]).map(l=>l[0])))];

  function getCount(month, breakdown, key) {
    const entry = (month[breakdown]||[]).find(x => x[0] === key);
    return entry ? entry[1] : 0;
  }

  // Genre line chart
  new Chart(document.getElementById("trend-genre-chart"), {
    type: "line",
    data: {
      labels,
      datasets: allGenres.map((g, i) => ({
        label: g,
        data: monthly.map(m => getCount(m, "genre_breakdown", g)),
        borderColor: PAL[i % PAL.length],
        backgroundColor: "transparent",
        tension: 0.3, pointRadius: 4,
      })),
    },
    options: trendOpts(),
  });

  // Language line chart
  new Chart(document.getElementById("trend-lang-chart"), {
    type: "line",
    data: {
      labels,
      datasets: allLangs.map((l, i) => ({
        label: l,
        data: monthly.map(m => getCount(m, "language_breakdown", l)),
        borderColor: PAL[(i + 5) % PAL.length],
        backgroundColor: "transparent",
        tension: 0.3, pointRadius: 4,
      })),
    },
    options: trendOpts(),
  });

  // Total views bar
  new Chart(document.getElementById("trend-views-chart"), {
    type: "bar",
    data: {
      labels,
      datasets: [{ label: "Total Views", data: monthly.map(m => m.total_views||0), backgroundColor: PAL[0], borderRadius: 4 }],
    },
    options: chartOpts(v => fmt(v)),
  });

  // Video count bar
  new Chart(document.getElementById("trend-count-chart"), {
    type: "bar",
    data: {
      labels,
      datasets: [{ label: "Videos", data: monthly.map(m => m.total_videos||0), backgroundColor: PAL[2], borderRadius: 4 }],
    },
    options: chartOpts(v => v),
  });

  // Monthly table
  document.getElementById("trends-table-body").innerHTML = [...monthly].reverse().map(m => {
    const topGenre = (m.genre_breakdown||[])[0]?.[0] || "—";
    const topLang  = (m.language_breakdown||[])[0]?.[0] || "—";
    const topArtist= (m.top_channels||[])[0]?.[0] || "—";
    return `<tr>
      <td><strong>${m.month}</strong></td>
      <td class="num">${m.total_videos||0}</td>
      <td class="num">${fmt(m.total_views||0)}</td>
      <td><span class="pill pill-genre">${topGenre}</span></td>
      <td><span class="pill pill-lang">${topLang}</span></td>
      <td style="color:var(--muted);font-size:12px">${topArtist}</td>
    </tr>`;
  }).join("");
}

function trendOpts() {
  return {
    plugins: { legend: { position: "bottom", labels: { color: "#888", font: { size: 10 }, boxWidth: 10 } } },
    scales: {
      x: { ticks: { color: "#888", font: { size: 10 } }, grid: { color: "#1a1a1a" } },
      y: { ticks: { color: "#888" }, grid: { color: "#1a1a1a" } },
    },
  };
}

// ── Tabs ──────────────────────────────────────────────────────
function bindTabs() {
  let trendsLoaded = false;
  document.querySelectorAll(".tab").forEach(btn =>
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
      if (btn.dataset.tab === "trends" && !trendsLoaded) {
        trendsLoaded = true;
        loadTrends();
      }
    })
  );
}

init();
