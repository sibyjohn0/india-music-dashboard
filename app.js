const DATA_URL = "data/latest.json";

function fmt(n) {
  if (n >= 1e9) return (n / 1e9).toFixed(1) + "B";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return String(n);
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

let allVideos = [];

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
        <div>Run the GitHub Action or <code>python scripts/fetch_youtube.py</code> to fetch data.</div>
      </div>`;
    return;
  }

  allVideos = data.videos || [];
  const fetched = new Date(data.fetched_at);

  document.getElementById("last-updated").textContent =
    "Updated " + fetched.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
  document.getElementById("total-badge").textContent = allVideos.length + " videos";

  renderStats(data);
  renderTopCards(allVideos.slice(0, 3));
  renderCharts(allVideos.slice(0, 15));
  renderTagCloud(data.top_keywords || []);
  renderTable(allVideos);
  bindControls();
}

function renderStats(data) {
  const videos = data.videos;
  const totalViews = videos.reduce((s, v) => s + v.views, 0);
  const avgEng = videos.reduce((s, v) => s + v.engagement_rate, 0) / (videos.length || 1);
  const trending = videos.filter(v => v.source === "trending_chart").length;
  const newest = videos.reduce((a, b) => a.published_at > b.published_at ? a : b, videos[0]);

  const stats = [
    { label: "Total Videos", value: videos.length, sub: `${trending} from trending chart` },
    { label: "Combined Views", value: fmt(totalViews), sub: "across all tracked videos" },
    { label: "Avg Engagement", value: avgEng.toFixed(2) + "%", sub: "(likes + comments) / views" },
    { label: "Most Recent Upload", value: newest ? daysAgo(newest.published_at) : "—", sub: newest ? fmtDate(newest.published_at) : "" },
    { label: "Top Views", value: fmt(videos[0]?.views || 0), sub: videos[0]?.title?.slice(0, 30) + "…" || "" },
  ];

  document.getElementById("stats-row").innerHTML = stats.map(s => `
    <div class="stat-card">
      <div class="stat-label">${s.label}</div>
      <div class="stat-value">${s.value}</div>
      <div class="stat-sub">${s.sub}</div>
    </div>`).join("");
}

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
          <div class="top-card-stat"><span>Likes </span>${fmt(v.likes)}</div>
          <div class="top-card-stat"><span>Eng </span>${v.engagement_rate}%</div>
        </div>
      </div>
    </a>`).join("");
}

function renderCharts(videos) {
  const labels = videos.map(v => v.title.length > 22 ? v.title.slice(0, 22) + "…" : v.title);
  const palette = ["#ff3b3b", "#ff5252", "#ff7043", "#ff8a65", "#ffa07a",
                   "#3b82f6", "#60a5fa", "#93c5fd", "#22c55e", "#4ade80",
                   "#facc15", "#fb923c", "#e879f9", "#a78bfa", "#34d399"];

  new Chart(document.getElementById("views-chart"), {
    type: "bar",
    data: {
      labels,
      datasets: [{ data: videos.map(v => v.views), backgroundColor: palette, borderRadius: 4 }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#888", font: { size: 10 } }, grid: { color: "#222" } },
        y: { ticks: { color: "#888", callback: v => fmt(v) }, grid: { color: "#222" } },
      },
    },
  });

  new Chart(document.getElementById("eng-chart"), {
    type: "bar",
    data: {
      labels,
      datasets: [{ data: videos.map(v => v.engagement_rate), backgroundColor: palette, borderRadius: 4 }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#888", font: { size: 10 } }, grid: { color: "#222" } },
        y: { ticks: { color: "#888", callback: v => v + "%" }, grid: { color: "#222" } },
      },
    },
  });
}

function renderTagCloud(keywords) {
  const max = keywords[0]?.count || 1;
  document.getElementById("tag-cloud").innerHTML = keywords.map(({ tag, count }) => {
    const ratio = count / max;
    const cls = ratio > 0.6 ? "tag-lg" : ratio > 0.3 ? "tag-md" : "tag-sm";
    return `<span class="tag ${cls}" title="${count} videos">${tag} <span style="opacity:.5">${count}</span></span>`;
  }).join("");
}

function renderTable(videos) {
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
      <td class="num">${fmt(v.likes)}</td>
      <td class="num">${fmt(v.comments)}</td>
      <td class="num eng-rate">${v.engagement_rate}%</td>
      <td><span class="source-pill ${v.source === "trending_chart" ? "source-trend" : "source-kw"}">
        ${v.source === "trending_chart" ? "Trending" : "Keyword"}
      </span></td>
    </tr>`).join("");
}

function bindControls() {
  function applyFilters() {
    const q = document.getElementById("search").value.toLowerCase();
    const sortBy = document.getElementById("sort-by").value;
    const src = document.getElementById("filter-source").value;

    let videos = allVideos.filter(v => {
      const matchQ = !q || v.title.toLowerCase().includes(q) || v.channel.toLowerCase().includes(q);
      const matchSrc = src === "all" || v.source === src;
      return matchQ && matchSrc;
    });

    videos = [...videos].sort((a, b) => {
      if (sortBy === "published_at") return b.published_at.localeCompare(a.published_at);
      return b[sortBy] - a[sortBy];
    });

    renderTable(videos);
  }

  document.getElementById("search").addEventListener("input", applyFilters);
  document.getElementById("sort-by").addEventListener("change", applyFilters);
  document.getElementById("filter-source").addEventListener("change", applyFilters);
}

init();
