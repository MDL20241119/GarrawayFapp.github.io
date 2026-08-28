(() => {
  'use strict';

  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[char]));

  const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return '';
    return new Intl.DateTimeFormat('ja-JP', {
      month: '2-digit',
      day: '2-digit'
    }).format(date).replaceAll('/', '.');
  };

  const renderInstagram = async () => {
    const container = document.getElementById('instagram-live');
    if (!container) return;

    try {
      const response = await fetch(`data/instagram.json?ts=${Date.now()}`, {
        cache: 'no-store'
      });
      if (!response.ok) throw new Error(`Instagram feed HTTP ${response.status}`);

      const raw = await response.json();
      const data = typeof raw.content === 'string' ? JSON.parse(raw.content) : raw;
      const posts = Array.isArray(data.posts) ? data.posts.slice(0, 4) : [];
      if (posts.length === 0) throw new Error('Instagram feed is empty');

      container.innerHTML = posts.map((post, index) => {
        const caption = String(post.caption ?? '').replace(/\s+/g, ' ').trim();
        const excerpt = caption.length > 58 ? `${caption.slice(0, 58)}…` : caption;
        const image = escapeHtml(post.image || '');
        const permalink = escapeHtml(post.permalink || 'https://www.instagram.com/garrawayf_lounge/');
        const date = formatDate(post.timestamp);
        const number = String(index + 1).padStart(2, '0');

        return `
          <a class="instagram-post instagram-post-${index + 1}" href="${permalink}" target="_blank" rel="noopener">
            <div class="instagram-media">
              <img src="${image}" alt="Garraway F Instagram NEWS ${number}" loading="lazy">
              <span class="instagram-number">${number}</span>
            </div>
            <div class="instagram-copy">
              <time>${escapeHtml(date)}</time>
              <p>${escapeHtml(excerpt)}</p>
            </div>
          </a>`;
      }).join('');
    } catch (error) {
      console.error('Instagram feed failed:', error);
      container.innerHTML = `
        <a class="instagram-fallback" href="https://www.instagram.com/garrawayf_lounge/" target="_blank" rel="noopener">
          <b>NEWS / INSTAGRAM</b>
          <span>Instagramで最新NEWSを見る ↗</span>
        </a>`;
    }
  };

  const animatePeople = () => {
    const cards = [...document.querySelectorAll('.portrait-roles article')];
    if (!('IntersectionObserver' in window)) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.animate([
          { opacity: 0, transform: 'translateY(18px)' },
          { opacity: 1, transform: 'translateY(0)' }
        ], {
          duration: 500,
          easing: 'cubic-bezier(.2,.8,.2,1)',
          fill: 'both'
        });
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.12 });

    cards.forEach((card) => observer.observe(card));
  };

  renderInstagram();
  animatePeople();
})();
