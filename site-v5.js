(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[char]));

  const loadVisualUpgrade = () => {
    if (!document.querySelector('link[data-gf-v6]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'site-v6-overrides.css?v=20260829-hero-events-floor-join-01';
      link.dataset.gfV6 = 'true';
      document.head.appendChild(link);
    }
    if (!document.querySelector('link[data-floor-poster-v7]')) {
      const floorLink = document.createElement('link');
      floorLink.rel = 'stylesheet';
      floorLink.href = 'floor-poster-v7.css?v=20260829-photo-poster-01';
      floorLink.dataset.floorPosterV7 = 'true';
      document.head.appendChild(floorLink);
    }
  };

  const setupMenu = () => {
    const menu = $('.menu-toggle');
    const nav = $('#main-nav');
    if (!menu || !nav) return;
    menu.addEventListener('click', () => {
      const open = menu.getAttribute('aria-expanded') === 'true';
      menu.setAttribute('aria-expanded', String(!open));
      nav.classList.toggle('is-open', !open);
    });
    $$('#main-nav a').forEach((link) => link.addEventListener('click', () => {
      menu.setAttribute('aria-expanded', 'false');
      nav.classList.remove('is-open');
    }));
  };

  const formatPostDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return '';
    return new Intl.DateTimeFormat('ja-JP', { month: '2-digit', day: '2-digit' })
      .format(date).replaceAll('/', '.');
  };

  const formatEventDate = (value) => {
    const date = new Date(`${value}T00:00:00+09:00`);
    if (Number.isNaN(date.getTime())) return { year: '', md: value };
    return {
      year: String(date.getFullYear()),
      md: `${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`
    };
  };

  const renderInstagram = async () => {
    const container = $('#instagram-live');
    if (!container) return;
    try {
      const response = await fetch(`data/instagram.json?ts=${Date.now()}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`Instagram feed HTTP ${response.status}`);
      const raw = await response.json();
      const data = typeof raw.content === 'string' ? JSON.parse(raw.content) : raw;
      const posts = Array.isArray(data.posts) ? data.posts.slice(0, 6) : [];
      if (!posts.length) throw new Error('Instagram feed is empty');
      container.innerHTML = posts.map((post, index) => {
        const caption = String(post.caption ?? '').replace(/\s+/g, ' ').trim();
        const excerpt = caption.length > 72 ? `${caption.slice(0, 72)}…` : caption;
        const image = escapeHtml(post.image || '');
        const permalink = escapeHtml(post.permalink || 'https://www.instagram.com/garrawayf_lounge/');
        const date = escapeHtml(formatPostDate(post.timestamp));
        const number = String(index + 1).padStart(2, '0');
        return `<a class="instagram-post" href="${permalink}" target="_blank" rel="noopener">
          <div class="instagram-media"><img src="${image}" alt="GarrawayF Instagram NEWS ${number}" loading="lazy" decoding="async"><span class="instagram-number">${number}</span></div>
          <div class="instagram-copy"><time>${date}</time><p>${escapeHtml(excerpt)}</p></div>
        </a>`;
      }).join('');
      installImageFallbacks(container);
    } catch (error) {
      console.error('Instagram feed failed:', error);
      container.innerHTML = `<a class="feed-fallback" href="https://www.instagram.com/garrawayf_lounge/" target="_blank" rel="noopener"><b>Instagram NEWS</b><span>Instagramで最新投稿を見る ↗</span></a>`;
    }
  };

  const defaultEvents = [
    { date: '2026-09-05', status: 'UPCOMING', title: '高校生∞チャレンジ 定期交流会②「社会起業家5名が大集合！」', category: '交流会 / SOCIAL ENTREPRENEURSHIP', url: 'https://www.facebook.com/garrawayf/events' },
    { date: '2026-08-18', status: 'ARCHIVE', title: '応援カイギ', category: 'COMMUNITY / CHALLENGE', url: 'https://www.facebook.com/garrawayf/events' },
    { date: '2026-08-08', status: 'ARCHIVE', title: '（一社）九州インターンシップ推進協議会 事前研修会', category: 'LEARNING / INTERNSHIP', url: 'https://www.facebook.com/garrawayf/events' }
  ];

  const renderFacebookEvents = async () => {
    const frame = $('.facebook-frame');
    if (!frame) return;
    let events = defaultEvents;
    let eventsPage = 'https://www.facebook.com/garrawayf/events';
    try {
      const response = await fetch(`data/facebook-events.json?ts=${Date.now()}`, { cache: 'no-store' });
      if (response.ok) {
        const data = await response.json();
        if (Array.isArray(data.events) && data.events.length) events = data.events.slice(0, 3);
        if (data.events_page) eventsPage = data.events_page;
      }
    } catch (error) {
      console.warn('Facebook event data fallback:', error);
    }

    const cards = events.map((event) => {
      const date = formatEventDate(event.date);
      const status = String(event.status || 'EVENT').toUpperCase();
      return `<article class="facebook-event-card" data-status="${escapeHtml(status)}">
        <div class="facebook-event-date"><b>${escapeHtml(date.md)}</b><span>${escapeHtml(date.year)} / ${escapeHtml(status)}</span></div>
        <div class="facebook-event-body"><small>${escapeHtml(event.category || 'FACEBOOK EVENT')}</small><h5>${escapeHtml(event.title)}</h5><a href="${escapeHtml(event.url || eventsPage)}" target="_blank" rel="noopener">詳細・参加情報を見る ↗</a></div>
      </article>`;
    }).join('');

    const encodedPage = encodeURIComponent('https://www.facebook.com/garrawayf/');
    frame.innerHTML = `<section class="facebook-events-native" aria-label="GarrawayF Facebookイベント情報">
      <header class="facebook-events-intro"><p>FACEBOOK / EVENT INFORMATION</p><h4>参加できる、<br>次の機会。</h4></header>
      <div class="facebook-events-list">${cards}</div>
      <div>
        <div class="facebook-events-actions"><a href="${escapeHtml(eventsPage)}" target="_blank" rel="noopener">Facebookイベントページを開く ↗</a><a href="https://www.facebook.com/garrawayf/" target="_blank" rel="noopener">公式Facebookを見る ↗</a></div>
        <details class="facebook-events-embed"><summary>Facebookイベントページを、この画面で表示</summary><iframe title="GarrawayF Facebookイベントページ" src="https://www.facebook.com/plugins/page.php?href=${encodedPage}&tabs=events&width=500&height=500&small_header=false&adapt_container_width=true&hide_cover=false&show_facepile=true" width="500" height="500" loading="lazy" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe></details>
      </div>
    </section>`;
  };

  const enhanceJoin = () => {
    const icons = $$('.join-icon');
    if (icons.length < 3) return;
    icons[0].innerHTML = `<svg viewBox="0 0 128 104" aria-hidden="true"><rect x="15" y="8" width="58" height="88" rx="7" fill="none" stroke="currentColor" stroke-width="3"/><line x1="30" y1="18" x2="58" y2="18" stroke="currentColor" stroke-width="3"/><circle cx="44" cy="85" r="3" fill="currentColor"/><path d="M62 31h45v34H83l-12 10 2-10H62z" fill="#fff" stroke="currentColor" stroke-width="3"/><text x="69" y="53" fill="currentColor" font-family="Arial" font-size="12" font-weight="700">LINE</text></svg>`;
    icons[1].innerHTML = `<svg viewBox="0 0 128 104" aria-hidden="true"><path d="M16 28h83v16c-8 0-12 6-12 12s4 12 12 12v16H16V68c8 0 12-6 12-12s-4-12-12-12z" fill="none" stroke="#070707" stroke-width="3"/><line x1="57" y1="30" x2="57" y2="82" stroke="#070707" stroke-width="3" stroke-dasharray="7 6"/><circle cx="96" cy="72" r="22" fill="#fff" stroke="#fff" stroke-width="3"/><path d="M86 72l7 7 14-17" fill="none" stroke="#f49bc0" stroke-width="4"/></svg>`;
    icons[2].innerHTML = `<svg viewBox="0 0 128 104" aria-hidden="true"><circle cx="32" cy="70" r="14" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="96" cy="70" r="14" fill="none" stroke="currentColor" stroke-width="3"/><path d="M12 101c1-17 8-26 20-26s19 9 20 26M76 101c1-17 8-26 20-26s19 9 20 26" fill="none" stroke="currentColor" stroke-width="3"/><path d="M39 12h50c10 0 17 7 17 16v15c0 9-7 16-17 16H67L54 70l3-11H39c-10 0-17-7-17-16V28c0-9 7-16 17-16z" fill="#fff" stroke="currentColor" stroke-width="3"/><circle cx="53" cy="35" r="3" fill="currentColor"/><circle cx="65" cy="35" r="3" fill="currentColor"/><circle cx="77" cy="35" r="3" fill="currentColor"/></svg>`;
  };

  const enhanceFloorPoster = async () => {
    const floor = $('#floor');
    const wrap = floor ? $('.floor-map-wrap', floor) : null;
    if (!floor || !wrap || wrap.dataset.posterReady === 'true') return;
    wrap.dataset.posterReady = 'true';
    wrap.classList.add('floor-poster-wrap');
    const oldGrid = $('.space-grid', floor);
    if (oldGrid) oldGrid.hidden = true;

    const kitchenPlaceholder = `data:image/svg+xml;charset=UTF-8,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180"><rect width="320" height="180" fill="#ffe2bd"/><text x="160" y="90" text-anchor="middle" font-family="Arial" font-size="20" font-weight="700" fill="#111">KITCHEN & DINING</text></svg>')}`;
    wrap.innerHTML = `<section class="floor-poster" aria-label="GarrawayF スペース紹介フロアマップ">
      <header class="floor-poster-header"><div><p>FLOOR MAP / TENJIN CLASS 3F</p><h3>GarrawayF</h3><strong>［ スペース紹介 ］</strong></div></header>
      <div class="floor-poster-callouts floor-poster-callouts-top">
        <figure class="floor-photo-card floor-photo-living"><div class="floor-photo-media"><img src="https://drive.google.com/thumbnail?id=1J6Ne_puDhM-7GLyJ1b7n2AMLfLs8ai1u&sz=w1400" alt="リビングラボで対話する人々" loading="lazy"></div><figcaption><b>リビングラボ（80席以上）</b><span>人が集まり、問いを立て、対話と共創を始める中心空間。</span></figcaption></figure>
        <figure class="floor-photo-card floor-photo-studio"><div class="floor-photo-media"><img src="https://garrawayf.com/wp-content/themes/garrawayf/assets/img_renew/img_studio.webp" alt="撮影・配信スタジオ" loading="lazy"></div><figcaption><b>スタジオ</b><span>撮影・配信・収録に対応した発信のための空間。</span></figcaption></figure>
      </div>
      <div class="floor-plan-frame"><img src="assets/floor-map.svg?v=20260829-photo-poster-01" alt="GarrawayF 天神CLASS 3階 フロアマップ"></div>
      <div class="floor-poster-callouts floor-poster-callouts-bottom">
        <figure class="floor-photo-card floor-photo-kitchen"><div class="floor-photo-media"><img data-kitchen-photo src="${kitchenPlaceholder}" alt="キッチン・ダイニング" loading="lazy"></div><figcaption><b>ダイニング／キッチン</b><span>食事や休憩をきっかけに、自然な会話と交流が生まれる。</span></figcaption></figure>
        <figure class="floor-photo-card floor-photo-build"><div class="floor-photo-media"><img src="https://drive.google.com/thumbnail?id=1I1AH-oFoy_R9UFkeXY9aQed7FqXLrqv2&sz=w1200" alt="モノづくりラボでアイデアを可視化する様子" loading="lazy"></div><figcaption><b>モノづくりラボ（32席）</b><span>アイデアを可視化し、試作・開発を進める共創空間。</span></figcaption></figure>
        <figure class="floor-photo-card floor-photo-street"><div class="floor-photo-media"><img src="https://drive.google.com/thumbnail?id=16bZEROOxM7CvTH3uOLZGiA8TSjNw8Bp3&sz=w1200" alt="Serendipity Streetで生まれる交流" loading="lazy"></div><figcaption><b>Serendipity Street</b><span>移動の途中にも、偶然の出会いと会話が生まれる通り。</span></figcaption></figure>
        <figure class="floor-photo-card floor-photo-focus"><div class="floor-photo-media"><img src="https://garrawayf.com/wp-content/themes/garrawayf/assets/img_renew/img_coworking.webp" alt="集中スペース" loading="lazy"></div><figcaption><b>集中スペース（30席）</b><span>個人で深く考え、作業や学習に集中できる静かな空間。</span></figcaption></figure>
      </div>
      <p class="floor-poster-note">エントランスはエレベーターの上部。Serendipity Streetを通って、各スペースへつながります。※レイアウトは変更になる場合があります。</p>
    </section>`;

    try {
      const response = await fetch(`assets/kitchen-thumb.b64?ts=${Date.now()}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`Kitchen image HTTP ${response.status}`);
      const b64 = (await response.text()).trim();
      const kitchen = $('[data-kitchen-photo]', wrap);
      if (kitchen && b64) kitchen.src = `data:image/jpeg;base64,${b64}`;
    } catch (error) {
      console.warn('Kitchen photo fallback:', error);
    }
    installImageFallbacks(wrap);
  };

  const fallbackSvg = `data:image/svg+xml;charset=UTF-8,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 1000"><rect width="800" height="1000" fill="#dcecff"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-size="44" font-weight="700" fill="#086bdd">GARRAWAYF</text></svg>')}`;
  function installImageFallbacks(root = document) {
    $$('img', root).forEach((img) => {
      if (img.dataset.fallbackBound) return;
      img.dataset.fallbackBound = '1';
      img.addEventListener('error', () => {
        if (img.src === fallbackSvg) return;
        img.src = fallbackSvg;
      }, { once: true });
    });
  }

  const reveal = () => {
    const nodes = $$('[data-reveal]');
    if (!('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      nodes.forEach((node) => node.classList.add('is-visible'));
      return;
    }
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -5% 0px' });
    nodes.forEach((node) => observer.observe(node));
  };

  loadVisualUpgrade();
  setupMenu();
  enhanceJoin();
  enhanceFloorPoster();
  installImageFallbacks();
  reveal();
  renderInstagram();
  renderFacebookEvents();
})();
