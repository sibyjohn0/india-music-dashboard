const DATA_URL = "data/latest.json";

// ── Formatters ───────────────────────────────────────────────
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
  const diff = (Date.now() - new Date(iso)) / 864e5;
  if (diff < 1) return "Today";
  if (diff < 2) return "Yesterday";
  if (diff < 30) return Math.floor(diff) + "d ago";
  if (diff < 365) return Math.floor(diff / 30) + "mo ago";
  return Math.floor(diff / 365) + "y ago";
}

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

function fmtDelta(delta, isNew) {
  if (isNew) return `<span class="delta-new">NEW</span>`;
  if (delta === null || delta === undefined) return `<span style="color:#555">—</span>`;
  if (delta === 0) return `<span style="color:#555">—</span>`;
  return `<span class="delta-pos">+${fmt(delta)}</span>`;
}

// ── State ────────────────────────────────────────────────────
let allVideos = [];
let allChannels = [];

// ── Init ─────────────────────────────────────────────────────
async function init() {
  let data;
  try {
    const res = await fetch(DATA_URL);
    data = await res.json();
  } catch {
    document.querySelector("main").innerHTML = `
      <div style="text-align:center;padding:80px 0;color:#888">
        <div style="font-size:40px;margin-bottom:16px">📡</div>
        <div style="font-size:18px;font-weight:600;margin-bottom:8px">No data yet</div>
        <div>Run the GitHub Action or <code>YOUTUBE_API_KEY=... python3 scripts/fetch_youtube.py</code></div>
      </div>`;
    return;
  }

  allVideos = data.videos || [];
  allChannels = buildChannels(allVideos);

  const fetched = new Date(data.fetched_at);
  document.getElementById("last-updated").textContent =
    "Updated " + fetched.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
  document.getElementById("total-badge").textContent = allVideos.length + " videos";

  renderStats(data);
  renderTopCards(allVideos.slice(0, 3));
  renderCharts(allVideos);
  renderTagCloud(data.top_keywords || []);
  renderChannelTable(allChannels);
  renderVideoTable(allVideos);
  bindTabs();
  bindVideoControls();
  bindChannelControls();
}

// ── Channel aggregation ──────────────────────────────────────
function buildChannels(videos) {
  const map = {};
  for (const v of videos) {
    const cid = v.channel_id || v.channel;
    if (!map[cid]) {
      map[cid] = {
        id: cid,
        name: v.channel,
        thumbnail: v.thumbnail,
        category: v.category,
        video_count: 0,
        total_views: 0,
        total_velocity: 0,
        total_earnings: 0,
        total_engagement: 0,
        views_delta: 0,
        top_video: v,
      };
    }
    const c = map[cid];
    c.video_count++;
    c.total_views += v.views;
    c.total_velocity += v.velocity || 0;
    c.total_earnings += v.earnings_est_inr || 0;
    c.total_engagement += v.engagement_rate || 0;
    c.views_delta += v.views_delta || 0;
    if (v.views > c.top_video.views) c.top_video = v;
    if (v.category === "indie") c.category = "indie"; // any indie video = indie channel
  }
  return Object.values(map).map(c => ({
    ...c,
    avg_velocity: Math.round(c.total_velocity / c.video_count),
    avg_engagement: Math.round((c.total_engagement / c.video_count) * 100) / 100,
  })).sort((a, b) => b.total_views - a.total_views);
}

// ── Stats row ────────────────────────────────────────────────
function renderStats(data) {
  const videos = data.videos;
  const totalViews = videos.reduce((s, v) => s + v.views, 0);
  const totalEarnings = videos.reduce((s, v) => s + (v.earnings_est_inr || 0), 0);
  const avgEng = videos.reduce((s, v) => s + v.engagement_rate, 0) / (videos.length || 1);
  const trending = videos.filter(v => v.source === "trending_chart").length;
  const newToday = videos.filter(v => v.is_new).length;
  const topVelocity = [...videos].sort((a, b) => (b.velocity || 0) - (a.velocity || 0))[0];

  const stats = [
    { label: "Total Videos", value: videos.length, sub: `${trending} from trending chart` },
    { label: "Indie / Independent", value: data.indie_count, sub: `${data.mainstream_count} mainstream` },
    { label: "Combined Views", value: fmt(totalViews), sub: "across all tracked videos" },
    { label: "Est. Total Earnings", value: fmtInr(totalEarnings), sub: "~₹80/1K views (India CPM)" },
    { label: "Avg Engagement", value: avgEng.toFixed(2) + "%", sub: "(likes + comments) ÷ views" },
    { label: "Fastest Rising", value: topVelocity ? fmt(topVelocity.velocity) + "/day" : "—", sub: topVelocity?.title?.slice(0, 28) + "…" || "" },
    { label: "New Today", value: newToday, sub: "not seen yesterday" },
  ];

  document.getElementById("stats-row").innerHTML = stats.map(s => `
    <div class="stat-card">
      <div class="stat-label">${s.label}</div>
      <div class="stat-value">${s.value}</div>
      <div class="stat-sub">${s.sub}</div>
    </div>`).join("");
}

// ── Top 3 cards ──────────────────────────────────────────────
function renderTopCards(videos) {
  const labels = ["🥇 #1 Trending", "🥈 #2 Trending", "🥉 #3 Trending"];
  document.getElementById("top-cards").innerHTML = videos.map((v, i) => `
    <a href="${v.url}" target="_blank" rel="noopener" class="top-card ${i === 0 ? "rank-1" : ""}">
      <img src="${v.thumbnail}" alt="" loading="lazy" />
      <div class="top-card-body">
        <div class="top-card-rank">${labels[i]}</div>
        <div class="top-card-title">${v.title}</div>
        <div class="top-card-channel">${v.channel} · ${daysAgo(v.published_at)}</div>
        <div class="top-card-stats">
          <div class="top-card-stat"><span>Views </span>${fmt(v.views)}</div>
          <div class="top-card-stat"><span>Velocity </span>${fmt(v.velocity)}/d</div>
          <div class="top-card-stat"><span>Est. </span>${fmtInr(v.earnings_est_inr)}</div>
        </div>
      </div>
    </a>`).join("");
}

// ── Charts ───────────────────────────────────────────────────
const palette = ["#ff3b3b","#ff5252","#ff7043","#ff8a65","#ffa07a",
                 "#3b82f6","#60a5fa","#93c5fd","#22c55e","#4ade80",
                 "#facc15","#fb923c","#e879f9","#a78bfa","#34d399"];

function renderCharts(videos) {
  const top15 = videos.slice(0, 15);
  const topVel = [...videos].sort((a, b) => (b.velocity || 0) - (a.velocity || 0)).slice(0, 15);
  const labels15 = top15.map(v => v.title.length > 20 ? v.title.slice(0, 20) + "…" : v.title);
  const labelsVel = topVel.map(v => v.title.length > 20 ? v.title.slice(0, 20) + "…" : v.title);

  new Chart(document.getElementById("views-chart"), {
    type: "bar",
    data: { labels: labels15, datasets: [{ data: top15.map(v => v.views), backgroundColor: palette, borderRadius: 4 }] },
    options: chartOpts(v => fmt(v)),
  });

  new Chart(document.getElementById("velocity-chart"), {
    type: "bar",
    data: { labels: labelsVel, datasets: [{ data: topVel.map(v => v.velocity || 0), backgroundColor: palette, borderRadius: 4 }] },
    options: chartOpts(v => fmt(v) + "/d"),
  });
}

function chartOpts(tickFmt) {
  return {
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: "#888", font: { size: 10 } }, grid: { color: "#222" } },
      y: { ticks: { color: "#888", callback: tickFmt }, grid: { color: "#222" } },
    },
  };
}

// ── Tag cloud ────────────────────────────────────────────────
function renderTagCloud(keywords) {
  const max = keywords[0]?.count || 1;
  document.getElementById("tag-cloud").innerHTML = keywords.map(({ tag, count }) => {
    const r = count / max;
    const cls = r > 0.6 ? "tag-lg" : r > 0.3 ? "tag-md" : "tag-sm";
    return `<span class="tag ${cls}" title="${count} videos">${tag} <span style="opacity:.5">${count}</span></span>`;
  }).join("");
}

// ── Channel table ─────────────────────────────────────────────
function renderChannelTable(channels) {
  document.getElementById("channel-body").innerHTML = channels.map((c, i) => `
    <tr>
      <td style="color:#555;font-size:12px">${i + 1}</td>
      <td>
        <div class="video-cell">
          <img class="video-thumb" src="${c.top_video.thumbnail}" alt="" loading="lazy" />
          <div class="video-info">
            <a href="https://youtube.com/channel/${c.id}" target="_blank" rel="noopener">${c.name}</a>
            <div class="video-channel">${c.video_count} video${c.video_count > 1 ? "s" : ""} tracked · top: <a href="${c.top_video.url}" target="_blank" rel="noopener" style="color:#888">${c.top_video.title.slice(0, 35)}…</a></div>
          </div>
        </div>
      </td>
      <td class="num">${c.video_count}</td>
      <td class="num">${fmt(c.total_views)}</td>
      <td class="num">${fmt(c.avg_velocity)}<span style="color:#555;font-size:11px">/d</span></td>
      <td class="num">${fmtInr(c.total_earnings)}</td>
      <td class="num eng-rate">${c.avg_engagement}%</td>
      <td><span class="source-pill ${c.category === "indie" ? "source-indie" : "source-main"}">${c.category === "indie" ? "Indie" : "Mainstream"}</span></td>
    </tr>`).join("");
}

// ── Video table ───────────────────────────────────────────────
function renderVideoTable(videos) {
  document.getElementById("table-body").innerHTML = videos.map((v, i) => `
    <tr>
      <td style="color:#555;font-size:12px">${i + 1}</td>
      <td>
        <div class="video-cell">
          <img class="video-thumb" src="${v.thumbnail}" alt="" loading="lazy" />
          <div class="video-info">
            <a href="${v.url}" target="_blank" rel="noopener">${v.title}</a>
            <div class="video-channel">${v.channel}</div>
          </div>
        </div>
      </td>
      <td class="num" title="${fmtDate(v.published_at)}">${daysAgo(v.published_at)}</td>
      <td class="num">${fmt(v.views)}</td>
      <td class="num">${fmtDelta(v.views_delta, v.is_new)}</td>
      <td class="num velocity">${fmt(v.velocity || 0)}<span style="color:#555;font-size:11px">/d</span></td>
      <td class="num earnings">${fmtInr(v.earnings_est_inr || 0)}</td>
      <td class="num eng-rate">${v.engagement_rate}%</td>
      <td><span class="source-pill ${v.category === "indie" ? "source-indie" : "source-main"}">${v.category === "indie" ? "Indie" : "Mainstream"}</span></td>
    </tr>`).join("");
}

// ── Controls ──────────────────────────────────────────────────
function bindVideoControls() {
  function apply() {
    const q = document.getElementById("search").value.toLowerCase();
    const sortBy = document.getElementById("sort-by").value;
    const cat = document.getElementById("filter-category").value;
    const src = document.getElementById("filter-source").value;

    let videos = allVideos.filter(v => {
      const mq = !q || v.title.toLowerCase().includes(q) || v.channel.toLowerCase().includes(q);
      const mc = cat === "all" || v.category === cat;
      const ms = src === "all" || v.source === src;
      return mq && mc && ms;
    });

    videos = [...videos].sort((a, b) => {
      if (sortBy === "published_at") return b.published_at.localeCompare(a.published_at);
      if (sortBy === "views_delta") return (b.views_delta || 0) - (a.views_delta || 0);
      return (b[sortBy] || 0) - (a[sortBy] || 0);
    });

    renderVideoTable(videos);
  }

  ["search", "sort-by", "filter-category", "filter-source"].forEach(id =>
    document.getElementById(id).addEventListener(id === "search" ? "input" : "change", apply)
  );
}

function bindChannelControls() {
  function apply() {
    const q = document.getElementById("ch-search").value.toLowerCase();
    const sortBy = document.getElementById("ch-sort").value;
    const cat = document.getElementById("ch-filter").value;

    let channels = allChannels.filter(c => {
      const mq = !q || c.name.toLowerCase().includes(q);
      const mc = cat === "all" || c.category === cat;
      return mq && mc;
    });

    channels = [...channels].sort((a, b) => (b[sortBy] || 0) - (a[sortBy] || 0));
    renderChannelTable(channels);
  }

  ["ch-search", "ch-sort", "ch-filter"].forEach(id =>
    document.getElementById(id).addEventListener(id === "ch-search" ? "input" : "change", apply)
  );
}

// ── Tabs ──────────────────────────────────────────────────────
function bindTabs() {
  document.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
    });
  });
}

init();
