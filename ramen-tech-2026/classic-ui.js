/* Restore the original masthead. All v3 IDs, actions, planner and storage remain unchanged. */
'use strict';
(()=>{
  const hero=document.querySelector('.compact-hero');
  if(!hero||hero.dataset.classic==='20260910c3')return;
  const initialHash=location.hash;
  hero.dataset.classic='20260910c3';hero.classList.add('classic-hero');
  hero.innerHTML=`<div class="classic-hero-top"><span>FUKUOKA, JAPAN</span><span>GARRAWAY F EDITION</span></div><div class="classic-hero-grid"><div class="classic-hero-copy"><p class="eyebrow">ONE CITY. ENDLESS CONNECTIONS.</p><h1 id="explore-title">RAMEN<br>TECH<span>.</span></h1><p class="classic-jp">福岡を、まるごと一杯。</p><p class="classic-description">気になるイベントへ。まだ知らない誰かへ。<br>街じゅうの出会いを、自分だけの一日に。</p><div class="classic-hero-actions"><button class="button yellow" type="button" data-classic-search>スケジュールを探す <span>↗</span></button><button class="classic-textlink" type="button" data-screen="map">会場から選ぶ ↗</button></div></div><div class="classic-hero-art"><span class="classic-sticker">HEY,<br>LET’S GO!</span><img src="assets/tonkotsu.svg" width="660" height="640" fetchpriority="high" alt="笑顔で手を振るラーメンの非公式キャラクター"><span class="classic-mascot-note">非公式キャラ</span><span class="classic-art-label">ORIGINAL TONKOTSU MASCOT / UNOFFICIAL</span></div></div><div class="classic-hero-bottom"><p class="classic-festival-date">10.07<span>WED</span><b>—</b>11<span>SUN</span></p><p class="classic-festival-caption">2026年10月7日（水）— 11日（日）<br><small>関連日程：9/30〜10/6・10/12〜14も掲載</small></p></div>`;
  const crumb=document.createElement('div');crumb.className='classic-breadcrumb';crumb.innerHTML='<a href="../">← Garraway F ホーム</a><span>RAMEN TECH 2026 非公式回遊ガイド</span>';hero.before(crumb);
  const ticker=document.createElement('div');ticker.className='classic-ticker';ticker.setAttribute('aria-hidden','true');ticker.innerHTML='<span>GOOD PEOPLE. GREAT IDEAS. NEXT CHALLENGE. ↗</span>'.repeat(4);hero.after(ticker);
  const title=document.createElement('div');title.className='classic-search-heading';title.id='classic-search';title.innerHTML='<div><p class="eyebrow">01 / FIND YOUR NEXT.</p><h2>次は、どこ行く？</h2></div><p>日付・会場・時間帯で、迷わず探す。<br>検索結果から、そのままマイ予定へ。</p>';document.querySelector('.search-area').before(title);
  const meta=document.querySelector('meta[name="theme-color"]');if(meta)meta.content='#1892F5';
  const style=document.createElement('style');style.textContent='.plan-fallback-map{margin-top:22px}.fallback-osm{height:320px;background:#eef1ec}.fallback-osm iframe{display:block;width:100%;height:100%;border:0}@media(max-width:800px){.plan-map-aside{order:-1}.plan-fallback-map{margin-top:18px}.fallback-osm{height:280px}}';document.head.appendChild(style);
  const jump=()=>{if(document.querySelector('#screen-explore')?.hidden)return;window.scrollTo({top:Math.max(0,window.scrollY+title.getBoundingClientRect().top-(document.querySelector('.site-header')?.getBoundingClientRect().height||65)-12),behavior:'instant'});};
  const fallbackMap=()=>{
    const screen=document.querySelector('#screen-plan');
    if(!screen||screen.hidden)return;
    if(screen.querySelector('.plan-map-aside .map-panel'))return;
    const empty=document.querySelector('#plan-empty');
    if(!empty)return;
    let box=empty.querySelector('.plan-fallback-map');
    if(!box){
      box=document.createElement('section');box.className='plan-fallback-map map-panel';box.setAttribute('aria-label','マイ予定の会場マップ');
      box.innerHTML=`<div class="map-heading"><div><p class="eyebrow">MY ROUTE / MAP</p><h2>マイ予定の会場マップ</h2><p>予定を追加すると、訪問順の番号とルートがここに表示されます。</p></div><button class="button secondary" data-screen="map">全会場マップを見る ↗</button></div><div class="fallback-osm"><iframe title="福岡・天神周辺の地図" loading="lazy" src="https://www.openstreetmap.org/export/embed.html?bbox=130.387%2C33.575%2C130.415%2C33.600&amp;layer=mapnik" referrerpolicy="strict-origin-when-cross-origin"></iframe></div><div class="map-status">福岡・天神周辺を表示しています。イベントを予定に追加すると、訪問会場だけの地図に切り替わります。</div>`;
      empty.appendChild(box);
    }
  };
  const watchPlan=new MutationObserver(()=>requestAnimationFrame(fallbackMap));
  ['plan-empty','plan-content'].forEach(id=>{const el=document.getElementById(id);if(el)watchPlan.observe(el,{childList:true,subtree:true});});
  document.addEventListener('click',ev=>{const b=ev.target.closest('button,a');if(!b)return;if(b.hasAttribute('data-classic-search')){ev.preventDefault();window.GuideApp?.displayScreen('explore',{scroll:false});requestAnimationFrame(jump);}else if(b.dataset.screen==='explore'&&b.closest('nav')){requestAnimationFrame(jump);}else if(b.dataset.screen==='plan'){setTimeout(fallbackMap,0);}});
  if(initialHash==='#schedule'||(new URLSearchParams(location.search).has('q')&&!new URLSearchParams(location.search).has('event'))){requestAnimationFrame(jump);}
  setTimeout(fallbackMap,0);
})();
