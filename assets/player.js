/* player.js: site-wide radio bar: "Indie Music India Radio".
 *
 * One Spotify playlist, one lead track per featured artist, playing from a
 * bar docked right below the site header. Self-contained like nav.js:
 * injects its own CSS, needs no markup beyond
 * <script src="/assets/player.js" defer>.
 *
 * Uses position:fixed, not sticky: every page's <body> has overflow-x:hidden,
 * which silently breaks position:sticky for descendants in most browsers.
 * The site's own <header>, declared sticky in each page's CSS, is affected
 * too: it looks pinned at scroll position zero but actually scrolls away
 * normally once you scroll (unnoticed on its own, since a non-sticky header
 * just looks like a normal header).
 *
 * An earlier version of this fix also force-pinned the header via inline
 * position:fixed, so it would never scroll away. That solved the overlap
 * but left two bars (header + player, ~136px) permanently stuck on screen
 * at all times, which read as heavier chrome than the brand wants.
 *
 * Current approach: leave the header alone (it keeps scrolling away like it
 * already does everywhere else on the site) and instead track scroll so the
 * player's own `top` glides from "just below the header" down to "0" as the
 * header scrolls out of view, then stays pinned there. Only one bar (84px)
 * is ever permanently on screen, and the player never drifts independently
 * of where the header visually is, which is what caused it to end up
 * floating over random page content before.
 *
 * STATUS: live, playing the "Indie Music India Radio" playlist. Clearing
 * PLAYLIST_ID below reverts to a "launching soon" placeholder bar.
 */
(function () {
  var PLAYLIST_ID = '6O93d2mQY8MpPOK6hJlMru'; // "Indie Music India Radio"

  function injectCSS() {
    if (document.getElementById('iim-player-css')) return;
    var css = [
      '#iim-player{position:fixed;left:0;right:0;z-index:150;background:#241B2E;border-top:3px solid #FF4D8D;border-bottom:3px solid #FF4D8D;display:flex;align-items:center;gap:12px;padding:0 14px;height:84px;box-shadow:0 2px 0 rgba(0,0,0,.08)}',
      '#iim-player.is-collapsed{display:none}',
      '#iim-player-space{height:84px}',
      '#iim-player-space.is-collapsed{height:0}',
      '#iim-player .pdot{width:8px;height:8px;border-radius:50%;background:#FF4D8D;flex:0 0 auto;animation:iim-pulse 1.8s ease-in-out infinite}',
      '@media(prefers-reduced-motion:reduce){#iim-player .pdot{animation:none}}',
      '@keyframes iim-pulse{0%,100%{opacity:1}50%{opacity:.35}}',
      '#iim-player .plabel{font-family:\'Space Mono\',ui-monospace,monospace;font-size:11px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:#fff;white-space:nowrap;flex:0 0 auto}',
      '#iim-player .pmsg{font-family:\'Inter\',system-ui,sans-serif;font-size:13px;color:#C9C2D6;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1 1 auto}',
      '#iim-player .pframe-wrap{flex:1 1 auto;min-width:0;height:80px;overflow:hidden;border-radius:8px}',
      '#iim-player .pframe-wrap iframe{display:block;width:100%;height:80px;border:0}',
      '#iim-player .pclose{flex:0 0 auto;width:28px;height:28px;border-radius:50%;background:none;border:1.5px solid #574C63;color:#C9C2D6;font-size:14px;line-height:1;cursor:pointer;display:flex;align-items:center;justify-content:center}',
      '#iim-player .pclose:hover{border-color:#FF4D8D;color:#fff}',
      '#iim-player-reopen{position:fixed;right:16px;bottom:16px;z-index:250;width:44px;height:44px;border-radius:50%;background:#241B2E;border:2px solid #FF4D8D;color:#fff;font-size:16px;cursor:pointer;display:none;align-items:center;justify-content:center;box-shadow:3px 3px 0 #FF4D8D}',
      '#iim-player-reopen.is-visible{display:flex}',
      '@media(max-width:640px){#iim-player,#iim-player-space{height:88px}#iim-player{padding:0 10px;gap:8px}#iim-player .plabel{display:none}#iim-player .pmsg{font-size:12px}}'
    ].join('');
    var s = document.createElement('style');
    s.id = 'iim-player-css';
    s.textContent = css;
    document.head.appendChild(s);
  }

  function build() {
    var header = document.querySelector('header');
    var headerHeight = header ? header.getBoundingClientRect().height : 0;

    var bar = document.createElement('div');
    bar.id = 'iim-player';
    bar.style.top = headerHeight + 'px';

    var space = document.createElement('div');
    space.id = 'iim-player-space';

    var dot = document.createElement('span');
    dot.className = 'pdot';
    bar.appendChild(dot);

    var label = document.createElement('span');
    label.className = 'plabel';
    label.textContent = 'IIM Radio';
    bar.appendChild(label);

    if (PLAYLIST_ID) {
      var wrap = document.createElement('div');
      wrap.className = 'pframe-wrap';
      var iframe = document.createElement('iframe');
      iframe.src = 'https://open.spotify.com/embed/playlist/' + PLAYLIST_ID + '?utm_source=generator&theme=0';
      iframe.loading = 'lazy';
      iframe.allow = 'autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture';
      iframe.title = 'Indie Music India Radio on Spotify';
      wrap.appendChild(iframe);
      bar.appendChild(wrap);
    } else {
      var msg = document.createElement('span');
      msg.className = 'pmsg';
      msg.textContent = 'Launching soon: one track per featured artist, playing on every page.';
      bar.appendChild(msg);
    }

    var close = document.createElement('button');
    close.type = 'button';
    close.className = 'pclose';
    close.setAttribute('aria-label', 'Hide radio bar');
    close.textContent = '×';
    bar.appendChild(close);

    var reopen = document.createElement('button');
    reopen.type = 'button';
    reopen.id = 'iim-player-reopen';
    reopen.setAttribute('aria-label', 'Show radio bar');
    reopen.textContent = '▶';

    if (header && header.parentNode) {
      header.insertAdjacentElement('afterend', space);
    } else {
      document.body.insertBefore(space, document.body.firstChild);
    }
    document.body.appendChild(bar);
    document.body.appendChild(reopen);

    function collapse() {
      bar.classList.add('is-collapsed');
      space.classList.add('is-collapsed');
      reopen.classList.add('is-visible');
      try { sessionStorage.setItem('iim_player_collapsed', '1'); } catch (e) {}
    }
    function expand() {
      bar.classList.remove('is-collapsed');
      space.classList.remove('is-collapsed');
      reopen.classList.remove('is-visible');
      try { sessionStorage.removeItem('iim_player_collapsed'); } catch (e) {}
    }
    close.addEventListener('click', collapse);
    reopen.addEventListener('click', expand);

    try {
      if (sessionStorage.getItem('iim_player_collapsed') === '1') collapse();
    } catch (e) {}

    // Glide the bar's top from headerHeight down to 0 as the (non-sticky)
    // header scrolls out of view, so the player always sits exactly where
    // the header visually ends, never drifting over scrolled content.
    var ticking = false;
    function updatePos() {
      var y = window.pageYOffset || document.documentElement.scrollTop || 0;
      bar.style.top = Math.max(0, headerHeight - y) + 'px';
    }
    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () { updatePos(); ticking = false; });
    }, { passive: true });
    updatePos();
  }

  function init() {
    if (document.getElementById('iim-player')) return;
    injectCSS();
    build();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
