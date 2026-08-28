(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[char]));

  const menu = $('.menu-toggle');
  const nav = $('#main-nav');
  if (menu && nav) {
    menu.addEventListener('click', () => {
      const open = menu.getAttribute('aria-expanded') === 'true';
      menu.setAttribute('aria-expanded', String(!open));
      nav.classList.toggle('is-open', !open);
    });
    $$('#main-nav a').forEach((link) => link.addEventListener('click', () => {
      menu.setAttribute('aria-expanded', 'false');
      nav.classList.remove('is-open');
    }));
  }

  const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return '';
    return new Intl.DateTimeFormat('ja-JP', { month: '2-digit', day: '2-digit' })
      .format(date).replaceAll('/', '.');
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
        const date = escapeHtml(formatDate(post.timestamp));
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

  const applyFinalStyles = () => {
    if (document.getElementById('floor-events-final-style')) return;
    const style = document.createElement('style');
    style.id = 'floor-events-final-style';
    style.textContent = `
      .facebook-events-frame{min-height:700px;padding:0!important;display:grid!important;grid-template-rows:minmax(500px,1fr) auto;align-items:stretch;background:#fff}
      .facebook-events-frame iframe{display:block;width:100%;max-width:500px;height:520px;margin:0 auto;border:0;background:#fff}
      .facebook-event-fallback{padding:24px 26px;border-top:1px solid #070707;background:#ffd7e5}
      .facebook-event-fallback>span{color:#086bdd;font-family:'Archivo','Noto Sans JP',sans-serif;font-size:9px;font-weight:700;letter-spacing:.1em}
      .facebook-event-fallback h4{margin:14px 0 12px;font-family:'Archivo Black','Noto Sans JP',sans-serif;font-size:clamp(31px,3.1vw,48px);line-height:.92;letter-spacing:-.055em}
      .facebook-event-fallback p{margin:0;font-size:11px;line-height:1.75}
      .facebook-event-fallback a{display:inline-flex;margin-top:18px;padding:12px 15px;background:#086bdd;color:#fff;font-family:'Archivo','Noto Sans JP',sans-serif;font-size:9px;font-weight:700}
      .space-media{height:260px;overflow:hidden;background:#eee}
      .space-wide .space-media{height:620px}
      .space-media>img{display:block;width:100%;height:100%;object-fit:cover;object-position:50% 50%}
      .space-media-duo{display:grid;grid-template-columns:1fr 1fr}
      .space-media-duo>img+img{border-left:1px solid #070707}
      @media(max-width:820px){
        .facebook-events-frame{min-height:650px;grid-template-rows:470px auto}
        .facebook-events-frame iframe{height:470px}
        .facebook-event-fallback{padding:20px 16px}
        .facebook-event-fallback h4{font-size:36px}
        .space-wide .space-media{height:320px}
        .space-media{height:190px}
      }
    `;
    document.head.appendChild(style);
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

  applyFinalStyles();
  installImageFallbacks();
  reveal();
  renderInstagram();
})();
