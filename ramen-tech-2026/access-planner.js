/* Event-first intercity access helper: find outbound/return options around selected events. */
'use strict';
(()=>{
  const KEY='garraway_ramen_access_v2';
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const load=()=>{try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch{return {}}};
  const save=v=>localStorage.setItem(KEY,JSON.stringify(v));
  const official={
    air:[['ANA','https://www.ana.co.jp/ja/jp/guide/plan/airinfo/dom-timetable/'],['JAL','https://www.jal.co.jp/jp/ja/dom/route/time/']],
    rail:[['JR東海 時刻検索','https://railway.jr-central.co.jp/cgi-bin/timetable/tokainr.cgi'],['スマートEX','https://smart-ex.jp/']]
  };
  const presets={tokyo:{label:'東京',airOrigin:'羽田空港',railOrigin:'東京駅'},osaka:{label:'大阪',airOrigin:'伊丹空港',railOrigin:'新大阪駅'}};
  const style=document.createElement('style');style.textContent=`
  .access-planner{margin:34px 0 26px;border:2px solid #111;border-radius:5px;background:#fff;overflow:hidden}.access-head{padding:15px 18px;background:#ffe248;border-bottom:2px solid #111}.access-head h2{font-size:20px;margin:0;font-weight:900}.access-head p{margin:4px 0 0;font-size:12px}.access-tabs{display:flex;border-bottom:1px solid #111}.access-tabs button{flex:1;min-height:46px;border:0;border-right:1px solid #111;background:#fff;font-weight:900}.access-tabs button:last-child{border-right:0}.access-tabs button[aria-pressed=true]{background:#1892f5;color:#fff}.access-body{padding:18px}.access-intro{font-size:13px;margin-bottom:14px}.access-row{display:grid;grid-template-columns:1.2fr .9fr .9fr;gap:12px;align-items:end}.access-field{display:flex;flex-direction:column;gap:6px}.access-field label{font-size:11px;font-weight:900}.access-field select,.access-field input{min-height:44px;border:1px solid #111;border-radius:4px;padding:8px 10px;background:#fff}.access-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}.access-actions button,.access-actions a{min-height:44px;display:inline-flex;align-items:center;border:1px solid #111;border-radius:4px;padding:8px 12px;font-weight:900;background:#fff}.access-actions .primary{background:#111;color:#fff}.access-result{margin-top:16px;border-top:1px dashed #777;padding-top:14px}.access-result h3{font-size:15px;margin:0 0 6px}.access-result p{font-size:12px;color:#444;margin:3px 0}.access-summary{margin:28px 0 0;border:1px solid #111;border-radius:4px;overflow:hidden}.access-summary-head{background:#1892f5;color:#fff;padding:9px 12px;font-size:12px;font-weight:900}.access-summary-body{padding:12px 14px;font-size:13px}.access-summary-body strong{font-size:15px}.access-links{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.access-links a{font-size:12px;font-weight:800;text-decoration:underline}.access-note{font-size:11px;color:#555;margin-top:8px}
  @media(max-width:700px){.access-row{grid-template-columns:1fr}.access-tabs{position:sticky;top:78px;z-index:2}}
  `;document.head.appendChild(style);

  function getPlannedEvents(){
    const cards=[...document.querySelectorAll('#screen-plan .plan-event')];
    return cards.map(card=>({title:card.querySelector('h3')?.textContent?.trim()||'イベント',time:card.querySelector('.plan-time')?.textContent?.trim()||'',venue:card.querySelector('.venue-button')?.textContent?.trim()||''}));
  }
  function pickTarget(kind){const ev=getPlannedEvents();return kind==='outbound'?ev[0]:ev[ev.length-1]}
  function template(){
    return `<section class="access-planner" id="access-planner"><div class="access-head"><p class="eyebrow">TRIP PLANNER</p><h2>行きたいイベントから、往復を逆算。</h2><p>マイ予定を組んだあとに、間に合う行き方／帰れる便を探します。</p></div><div class="access-tabs"><button type="button" data-trip-tab="outbound" aria-pressed="true">行き｜このイベントに間に合う</button><button type="button" data-trip-tab="return" aria-pressed="false">帰り｜このイベント後に帰る</button></div><div class="access-body" data-trip-body></div></section>`}
  function renderBody(root,kind){
    const v=load();const target=pickTarget(kind);const city=v[kind+'City']||'tokyo';const mode=v[kind+'Mode']||'air';const p=presets[city];
    const targetLabel=target?`${target.title} ${target.time}`:(kind==='outbound'?'最初のイベントを予定に追加してください':'最後のイベントを予定に追加してください');
    const terminal=mode==='air'?'福岡空港':'博多駅';const origin=mode==='air'?p.airOrigin:p.railOrigin;
    root.querySelector('[data-trip-body]').innerHTML=`<p class="access-intro"><strong>${kind==='outbound'?'到着基準':'出発基準'}：</strong> ${esc(targetLabel)}</p><div class="access-row"><div class="access-field"><label>${kind==='outbound'?'出発エリア':'帰着エリア'}</label><select data-trip-city><option value="tokyo" ${city==='tokyo'?'selected':''}>東京</option><option value="osaka" ${city==='osaka'?'selected':''}>大阪</option></select></div><div class="access-field"><label>交通手段</label><select data-trip-mode><option value="air" ${mode==='air'?'selected':''}>✈ 飛行機</option><option value="rail" ${mode==='rail'?'selected':''}>🚄 新幹線</option></select></div><div class="access-field"><label>${kind==='outbound'?'余裕時間（分）':'イベント後の余裕（分）'}</label><input type="number" min="0" max="240" value="${esc(v[kind+'Buffer']||'60')}" data-trip-buffer></div></div><div class="access-result"><h3>検索の考え方</h3><p>${kind==='outbound'?`${esc(origin)} → ${esc(terminal)} → 最初のイベント会場へ。イベント開始時刻から、福岡市内移動＋余裕時間を引いて検索します。`:`最後のイベント終了 → ${esc(terminal)} → ${esc(origin)}。会場から駅／空港までの移動＋余裕時間を足して検索します。`}</p><div class="access-actions"><button class="primary" type="button" data-trip-save>${kind==='outbound'?'この条件を保存':'帰り条件を保存'}</button>${official[mode].map(([n,u])=>`<a href="${u}" target="_blank" rel="noopener">${n}で検索 ↗</a>`).join('')}</div><p class="access-note">時刻表そのものは固定せず、最新の公式検索結果から選ぶ設計です。</p></div>`;
    root.querySelector('[data-trip-city]').addEventListener('change',e=>{v[kind+'City']=e.target.value;save(v);renderBody(root,kind)});
    root.querySelector('[data-trip-mode]').addEventListener('change',e=>{v[kind+'Mode']=e.target.value;save(v);renderBody(root,kind)});
    root.querySelector('[data-trip-save]').addEventListener('click',()=>{v[kind+'City']=root.querySelector('[data-trip-city]').value;v[kind+'Mode']=root.querySelector('[data-trip-mode]').value;v[kind+'Buffer']=root.querySelector('[data-trip-buffer]').value;v[kind+'Target']=target||null;save(v);renderSummary();});
  }
  function renderSummary(){
    const screen=document.querySelector('#screen-plan');if(!screen)return;screen.querySelectorAll('.access-summary').forEach(x=>x.remove());const v=load();const planner=screen.querySelector('#access-planner');if(!planner)return;
    const bits=[];if(v.outboundTarget)bits.push(`<div><strong>行き：</strong>${esc(v.outboundTarget.title)} に間に合う ${presets[v.outboundCity||'tokyo'].label}発・${v.outboundMode==='rail'?'新幹線':'飛行機'}を検索</div>`);if(v.returnTarget)bits.push(`<div><strong>帰り：</strong>${esc(v.returnTarget.title)} の後に帰れる ${presets[v.returnCity||'tokyo'].label}行き・${v.returnMode==='rail'?'新幹線':'飛行機'}を検索</div>`);if(!bits.length)return;
    const box=document.createElement('section');box.className='access-summary';box.innerHTML=`<div class="access-summary-head">TRIP PLAN / 往復アクセス</div><div class="access-summary-body">${bits.join('')}<div class="access-note">便・列車は公式検索で最新時刻を確認し、選んだ内容をマイ予定へ反映してください。</div></div>`;planner.before(box);
  }
  function placeAtBottom(planner){
    const screen=document.querySelector('#screen-plan');if(!screen||!planner)return;
    const footer=screen.querySelector('.plan-actions,.plan-footer,.screen-actions');
    if(footer&&footer.parentElement===screen)screen.insertBefore(planner,footer);else screen.appendChild(planner);
  }
  function mount(){
    const screen=document.querySelector('#screen-plan');if(!screen)return;
    let planner=screen.querySelector('#access-planner');
    if(!planner){const wrap=document.createElement('div');wrap.innerHTML=template();planner=wrap.firstElementChild;placeAtBottom(planner);let kind='outbound';renderBody(planner,kind);planner.addEventListener('click',e=>{const tab=e.target.closest('[data-trip-tab]');if(!tab)return;kind=tab.dataset.tripTab;planner.querySelectorAll('[data-trip-tab]').forEach(b=>b.setAttribute('aria-pressed',String(b===tab)));renderBody(planner,kind)});}
    else placeAtBottom(planner);
    renderSummary();
  }
  const obs=new MutationObserver(()=>mount());obs.observe(document.documentElement,{childList:true,subtree:true});if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
})();
