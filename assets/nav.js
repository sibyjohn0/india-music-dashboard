/* nav.js — one shared primary nav for the whole site.
 *
 * Why this exists: the top nav had grown to ~12 tabs and drifted out of sync
 * page to page. This rebuilds the SAME five-item nav everywhere from one list,
 * grouping the content pages under Discover and the free tools under Tools, so a
 * first-time visitor sees five clear choices instead of a wall of tabs.
 *
 * Desktop: Discover / Tools open on hover or click. Mobile: they live inside the
 * existing full-screen burger menu as tap-to-expand accordions. Self-contained —
 * injects its own CSS (matched to the poppy theme) and needs no markup changes
 * beyond a <script src="/assets/nav.js" defer> tag. Replaces whatever <nav
 * class="js-primnav"> is on the page, so it also fixes the page-to-page drift.
 */
(function () {
  var NAV = [
    { label: 'Home', href: '/' },
    { label: 'Discover', children: [
      { label: 'Radar', href: '/radar.html' },
      { label: 'Live', href: '/live/' },
      { label: 'Venues', href: '/venues/' },
      { label: 'News', href: '/news/' }
    ] },
    { label: 'Tools', children: [
      { label: 'Guides', href: '/answers/' },
      { label: 'Reviewers', href: '/reviewers/' },
      { label: 'Industry', href: '/industry/' },
      { label: 'Royalty Calculator', href: '/tools/royalty-calculator/' }
    ] },
    { label: 'Programme', href: '/programme/' },
    { label: 'About', href: '/about/' }
  ];

  // Map the current path to the nav item that should read as active. Prefixes,
  // longest-meaningful-first; /guides/* and /answers/ both light up Guides,
  // /resources/ lights up Tools (it lives in the footer, not the top row).
  function activeFor(path) {
    path = path.replace(/index\.html$/, '');
    if (path === '/' || path === '') return { top: 'Home' };
    var M = [
      ['/radar', 'Discover', 'Radar'], ['/live', 'Discover', 'Live'],
      ['/venues', 'Discover', 'Venues'], ['/news', 'Discover', 'News'],
      ['/tools/royalty-calculator', 'Tools', 'Royalty Calculator'],
      ['/answers', 'Tools', 'Guides'], ['/guides/', 'Tools', 'Guides'],
      ['/reviewers', 'Tools', 'Reviewers'], ['/industry', 'Tools', 'Industry'],
      ['/resources', 'Tools', null],
      ['/programme', 'Programme', null], ['/about', 'About', null]
    ];
    for (var i = 0; i < M.length; i++) {
      if (path.indexOf(M[i][0]) === 0) return { top: M[i][1], child: M[i][2] };
    }
    return {};
  }

  function build(nav) {
    var act = activeFor(location.pathname);
    nav.innerHTML = '';
    NAV.forEach(function (item) {
      if (item.children) {
        var grp = document.createElement('div');
        grp.className = 'navgrp';
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'tab navgrp-btn' + (act.top === item.label ? ' active' : '');
        btn.setAttribute('aria-expanded', 'false');
        btn.setAttribute('aria-haspopup', 'true');
        btn.innerHTML = item.label + '<span class="navcaret" aria-hidden="true">▾</span>';
        var menu = document.createElement('div');
        menu.className = 'navgrp-menu';
        menu.setAttribute('role', 'menu');
        item.children.forEach(function (c) {
          var a = document.createElement('a');
          a.className = 'tab' + (act.child === c.label ? ' active' : '');
          a.href = c.href;
          a.textContent = c.label;
          a.setAttribute('role', 'menuitem');
          menu.appendChild(a);
        });
        grp.appendChild(btn);
        grp.appendChild(menu);
        nav.appendChild(grp);
      } else {
        var link = document.createElement('a');
        link.className = 'tab' + (act.top === item.label ? ' active' : '');
        link.href = item.href;
        link.textContent = item.label;
        nav.appendChild(link);
      }
    });
  }

  function wire(nav) {
    var groups = [].slice.call(nav.querySelectorAll('.navgrp'));
    function closeAll(except) {
      groups.forEach(function (g) {
        if (g !== except) g.querySelector('.navgrp-btn').setAttribute('aria-expanded', 'false');
      });
    }
    groups.forEach(function (g) {
      var btn = g.querySelector('.navgrp-btn');
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var open = btn.getAttribute('aria-expanded') === 'true';
        closeAll(g);
        btn.setAttribute('aria-expanded', open ? 'false' : 'true');
      });
      g.addEventListener('mouseenter', function () {
        if (window.innerWidth > 640) { closeAll(g); btn.setAttribute('aria-expanded', 'true'); }
      });
      g.addEventListener('mouseleave', function () {
        if (window.innerWidth > 640) btn.setAttribute('aria-expanded', 'false');
      });
    });
    document.addEventListener('click', function (e) { if (!e.target.closest('.navgrp')) closeAll(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeAll(); });
    // Tapping a real link inside the mobile overlay closes it.
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a.tab')) document.body.classList.remove('mnav-open');
    });
  }

  function injectCSS() {
    if (document.getElementById('navgrp-css')) return;
    var css = [
      '.js-primnav .navgrp{position:relative;display:inline-flex;align-items:center}',
      '.js-primnav .navgrp-btn{font-family:var(--font-m,"Space Mono",monospace);color:var(--ink,#241B2E);background:none;border:2px solid transparent;border-radius:999px;height:auto;margin:8px 2px;padding:7px 14px;font-weight:700;font-size:13px;cursor:pointer;display:inline-flex;align-items:center;gap:6px;line-height:1}',
      '.js-primnav .navgrp-btn:hover{background:#fff;border-color:var(--ink,#241B2E)}',
      '.js-primnav .navgrp-btn.active{background:var(--ink,#241B2E);color:#fff;border-color:var(--ink,#241B2E)}',
      '.js-primnav .navcaret{font-size:.7em;transition:transform .18s}',
      '.js-primnav .navgrp-btn[aria-expanded="true"] .navcaret{transform:rotate(180deg)}',
      '.js-primnav .navgrp-menu{position:absolute;top:calc(100% - 6px);left:6px;min-width:196px;background:#fff;border:2px solid var(--ink,#241B2E);border-radius:14px;box-shadow:4px 4px 0 var(--ink,#241B2E);padding:8px;z-index:600;display:none;flex-direction:column;gap:2px}',
      '.js-primnav .navgrp-btn[aria-expanded="true"]+.navgrp-menu{display:flex}',
      '.js-primnav .navgrp-menu a.tab{margin:0;border-radius:9px;padding:9px 13px;white-space:nowrap;display:flex;align-items:center;justify-content:flex-start}',
      '.js-primnav .navgrp-menu a.tab:hover{background:var(--yellow-s,#FFF3CE);border-color:transparent}',
      /* 5 items fit without scrolling, so let the dropdown escape the bar; lift
         the nav above sibling sections (poppy gives every body child z-index:1) */
      '@media(min-width:641px){nav.js-primnav{overflow:visible!important;position:relative;z-index:200}}',
      '@media(max-width:640px){',
      '.js-primnav .navgrp{flex-direction:column;align-items:center;width:100%}',
      '.js-primnav .navgrp-btn{font-size:20px;margin:6px 0}',
      '.js-primnav .navgrp-menu{position:static;box-shadow:none;border:0;background:none;padding:0;min-width:0;align-items:center;gap:0}',
      '.js-primnav .navgrp-menu a.tab{font-size:16px!important;opacity:.85;padding:9px 20px!important;justify-content:center}',
      '}'
    ].join('');
    var s = document.createElement('style');
    s.id = 'navgrp-css';
    s.textContent = css;
    document.head.appendChild(s);
  }

  function init() {
    var nav = document.querySelector('nav.js-primnav');
    if (!nav) return;
    injectCSS();
    build(nav);
    wire(nav);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
