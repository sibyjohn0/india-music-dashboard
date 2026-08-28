/* analytics.js — GA4 interest + drop-off instrumentation for Indie Music India.
 * Loads after gtag. Sends custom events so we can see, per SEO landing page,
 * how far people get before they drop:
 *   - scroll_depth   (25/50/75/100 %)  -> did they read, or bounce?
 *   - cta_click      (programme / work-with-us buttons) -> did interest convert?
 *   - tool_used      (royalty calculator inputs)        -> did the tool engage them?
 *   - outbound_click (instagram / external)             -> where they leave to
 * Pageviews are already sent by the base gtag config; this adds the funnel.
 */
(function () {
  if (typeof gtag !== "function") return;
  var path = location.pathname;

  // ---- scroll depth (fires each threshold once) ----
  var hit = {};
  function onScroll() {
    var h = document.documentElement;
    var pct = (h.scrollTop || document.body.scrollTop) /
              ((h.scrollHeight - h.clientHeight) || 1) * 100;
    [25, 50, 75, 100].forEach(function (t) {
      if (pct >= t && !hit[t]) {
        hit[t] = 1;
        gtag("event", "scroll_depth", { percent: t, page_path: path });
      }
    });
  }
  window.addEventListener("scroll", function () {
    window.requestAnimationFrame(onScroll);
  }, { passive: true });

  // ---- clicks: CTAs, tools, outbound ----
  document.addEventListener("click", function (e) {
    var a = e.target.closest("a, button");
    if (!a) return;
    var href = (a.getAttribute("href") || "").trim();
    var label = (a.textContent || "").trim().slice(0, 60);

    // programme / work-with-us CTAs
    if (/programme/i.test(href) || /\b(work with us|put a real team|see how|the programme)\b/i.test(label)) {
      gtag("event", "cta_click", { cta: label || "programme", from_page: path });
    }
    // outbound (different host)
    if (/^https?:\/\//.test(href) && href.indexOf(location.host) === -1) {
      var dest = href.replace(/^https?:\/\//, "").split("/")[0];
      gtag("event", "outbound_click", { destination: dest, from_page: path });
    }
  }, true);

  // ---- royalty calculator engagement ----
  var calc = document.querySelector("#streams, #platform, input[type=range]");
  if (calc) {
    var used = false;
    document.addEventListener("input", function () {
      if (!used) { used = true; gtag("event", "tool_used", { tool: "royalty_calculator", page_path: path }); }
    }, { once: false });
  }
})();
