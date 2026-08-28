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

  const renderFacebookEvent = () => {
    const frame = $('.facebook-frame');
    if (!frame) return;

    if (!$('#facebook-native-style')) {
      const style = document.createElement('style');
      style.id = 'facebook-native-style';
      style.textContent = `
        .facebook-frame{padding:0!important;min-height:700px!important;background:#fff!important;display:block!important;overflow:hidden!important}
        .facebook-native{min-height:700px;display:grid;grid-template-rows:minmax(330px,1.05fr) minmax(310px,.95fr);background:#fff}
        .facebook-native-media{position:relative;overflow:hidden;border-bottom:1px solid #070707;background:#dcecff}
        .facebook-native-media img{width:100%;height:100%;object-fit:cover;object-position:50% 46%;display:block}
        .facebook-native-badge{position:absolute;left:18px;top:18px;padding:8px 11px;background:#086bdd;color:#fff;border:1px solid #070707;font:700 9px 'Archivo','Noto Sans JP',sans-serif;letter-spacing:.1em}
        .facebook-native-copy{padding:clamp(28px,3.4vw,48px);display:flex;flex-direction:column;justify-content:center;background:#f49bc0}
        .facebook-native-copy .facebook-meta{margin:0 0 18px;color:#086bdd;font:700 9px 'Archivo','Noto Sans JP',sans-serif;letter-spacing:.12em}
        .facebook-native-copy h4{margin:0;font:900 clamp(36px,3.8vw,58px)/.92 'Archivo Black','Noto Sans JP',sans-serif;letter-spacing:-.06em}
        .facebook-native-copy>p:not(.facebook-meta){max-width:430px;margin:22px 0 0;font-size:12px;font-weight:700;line-height:1.85}
        .facebook-native-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:28px}
        .facebook-native-actions a{min-height:48px;padding:0 16px;display:inline-flex;align-items:center;border:1px solid #070707;background:#fff;font:700 9px 'Archivo','Noto Sans JP',sans-serif;letter-spacing:.05em}
        .facebook-native-actions a:first-child{background:#086bdd;color:#fff}
        .facebook-native-actions a:hover,.facebook-native-actions a:focus-visible{background:#070707;color:#fff}
        @media(max-width:820px){
          .facebook-frame,.facebook-native{min-height:0!important}
          .facebook-native{grid-template-rows:290px auto}
          .facebook-native-copy{padding:28px 18px 32px}
          .facebook-native-copy h4{font-size:40px}
          .facebook-native-copy>p:not(.facebook-meta){font-size:11px}
          .facebook-native-actions{display:grid;grid-template-columns:1fr;margin-top:22px}
          .facebook-native-actions a{justify-content:center}
        }
      `;
      document.head.appendChild(style);
    }

    frame.innerHTML = `<article class="facebook-native" aria-label="GarrawayF Facebook EVENT">
      <div class="facebook-native-media">
        <img src="https://drive.google.com/thumbnail?id=1N0iRILiombzt5W6BO8uz6jOG7yfnB8x9&sz=w1600" alt="GarrawayFで開催されるイベントの様子" loading="lazy" decoding="async">
        <span class="facebook-native-badge">FACEBOOK / EVENT</span>
      </div>
      <div class="facebook-native-copy">
        <p class="facebook-meta">UPCOMING / REGISTRATION / EVENT REPORT</p>
        <h4>次の出会いに、<br>参加する。</h4>
        <p>開催予定、参加募集、当日の変更、イベントレポートは、GarrawayF公式Facebookで随時更新しています。</p>
        <div class="facebook-native-actions">
          <a href="https://www.facebook.com/garrawayf/events" target="_blank" rel="noopener">最新EVENTを見る ↗</a>
          <a href="https://www.facebook.com/garrawayf/" target="_blank" rel="noopener">Facebookページへ ↗</a>
        </div>
      </div>
    </article>`;
    installImageFallbacks(frame);
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

  installImageFallbacks();
  reveal();
  renderFacebookEvent();
  renderInstagram();
})();
