/* Restore the original masthead. All v3 IDs, actions, planner and storage remain unchanged. */
'use strict';
(()=>{
  const hero=document.querySelector('.compact-hero');
  if(!hero||hero.dataset.classic==='20260910c2')return;
  const initialHash=location.hash;
  hero.dataset.classic='20260910c2';hero.classList.add('classic-hero');
  hero.innerHTML=`<div class="classic-hero-top"><span>FUKUOKA, JAPAN</span><span>GARRAWAY F EDITION</span></div><div class="classic-hero-grid"><div class="classic-hero-copy"><p class="eyebrow">ONE CITY. ENDLESS CONNECTIONS.</p><h1 id="explore-title">RAMEN<br>TECH<span>.</span></h1><p class="classic-jp">福岡を、まるごと一杯。</p><p class="classic-description">気になるイベントへ。まだ知らない誰かへ。<br>街じゅうの出会いを、自分だけの一日に。</p><div class="classic-hero-actions"><button class="button yellow" type="button" data-classic-search>スケジュールを探す <span>↗</span></button><button class="classic-textlink" type="button" data-screen="map">会場から選ぶ ↗</button></div></div><div class="classic-hero-art"><span class="classic-sticker">HEY,<br>LET’S GO!</span><img src="assets/tonkotsu.svg" width="660" height="640" fetchpriority="high" alt="笑顔で手を振るラーメンの非公式キャラクター"><span class="classic-mascot-note">非公式キャラ</span><span class="classic-art-label">ORIGINAL TONKOTSU MASCOT / UNOFFICIAL</span></div></div><div class="classic-hero-bottom"><p class="classic-festival-date">10.07<span>WED</span><b>—</b>11<span>SUN</span></p><p class="classic-festival-caption">2026年10月7日（水）— 11日（日）<br><small>関連日程：9/30〜10/6・10/12〜14も掲載</small></p></div>`;
  const crumb=document.createElement('div');crumb.className='classic-breadcrumb';crumb.innerHTML='<a href="../">← Garraway F ホーム</a><span>RAMEN TECH 2026 非公式回遊ガイド</span>';hero.before(crumb);
  const ticker=document.createElement('div');ticker.className='classic-ticker';ticker.setAttribute('aria-hidden','true');ticker.innerHTML='<span>GOOD PEOPLE. GREAT IDEAS. NEXT CHALLENGE. ↗</span>'.repeat(4);hero.after(ticker);
  const title=document.createElement('div');title.className='classic-search-heading';title.id='classic-search';title.innerHTML='<div><p class="eyebrow">01 / FIND YOUR NEXT.</p><h2>次は、どこ行く？</h2></div><p>日付・会場・時間帯で、迷わず探す。<br>検索結果から、そのままマイ予定へ。</p>';document.querySelector('.search-area').before(title);
  const meta=document.querySelector('meta[name="theme-color"]');if(meta)meta.content='#1892F5';
  const jump=()=>{if(document.querySelector('#screen-explore')?.hidden)return;window.scrollTo({top:Math.max(0,window.scrollY+title.getBoundingClientRect().top-(document.querySelector('.site-header')?.getBoundingClientRect().height||65)-12),behavior:'instant'});};
  document.addEventListener('click',ev=>{const b=ev.target.closest('button,a');if(!b)return;if(b.hasAttribute('data-classic-search')){ev.preventDefault();window.GuideApp?.displayScreen('explore',{scroll:false});requestAnimationFrame(jump);}else if(b.dataset.screen==='explore'&&b.closest('nav')){requestAnimationFrame(jump);}});
  // Search deeplinks keep their utility: no need to scroll past the restored masthead.
  if(initialHash==='#schedule'||(new URLSearchParams(location.search).has('q')&&!new URLSearchParams(location.search).has('event'))){requestAnimationFrame(jump);}
})();
