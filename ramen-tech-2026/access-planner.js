/* Intercity access planner: flight / shinkansen -> Fukuoka -> event day. */
'use strict';
(()=>{
  const KEY='garraway_ramen_access_v1';
  const presets={
    tokyo_air:{mode:'air',origin:'東京（羽田）',terminal:'福岡空港',localMode:'地下鉄・徒歩',localMinutes:'20'},
    tokyo_rail:{mode:'rail',origin:'東京駅',terminal:'博多駅',localMode:'地下鉄・徒歩',localMinutes:'15'},
    osaka_air:{mode:'air',origin:'大阪（伊丹・関西）',terminal:'福岡空港',localMode:'地下鉄・徒歩',localMinutes:'20'},
    osaka_rail:{mode:'rail',origin:'新大阪駅',terminal:'博多駅',localMode:'地下鉄・徒歩',localMinutes:'15'}
  };
  const official={
    air:[
      ['ANA 時刻表','https://www.ana.co.jp/ja/jp/guide/plan/airinfo/dom-timetable/'],
      ['JAL 時刻表','https://www.jal.co.jp/jp/ja/dom/route/time/']
    ],
    rail:[
      ['新幹線 時刻表','https://railway.jr-central.co.jp/pwd/_pdf/N700S-every.pdf'],
      ['JR東海 アクセス検索','https://railway.jr-central.co.jp/cgi-bin/timetable/tokainr.cgi'],
      ['スマートEX','https://smart-ex.jp/']
    ]
  };
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const load=()=>{try{return JSON.parse(localStorage.getItem(KEY)||'null')}catch{return null}};
  const save=v=>localStorage.setItem(KEY,JSON.stringify(v));
  const style=document.createElement('style');
  style.textContent=`
  .access-planner{margin:18px 0 26px;border:2px solid #111;border-radius:5px;background:#fff;overflow:hidden}.access-head{display:flex;justify-content:space-between;gap:18px;align-items:center;padding:15px 18px;background:#ffe248;border-bottom:2px solid #111}.access-head h2{font-size:20px;margin:0;font-weight:900}.access-head p{margin:3px 0 0;font-size:12px}.access-body{padding:18px}.access-presets{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}.access-presets button{min-height:42px;border:1px solid #111;background:#fff;border-radius:4px;padding:8px 12px;font-weight:800}.access-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.access-field{display:flex;flex-direction:column;gap:6px}.access-field label{font-size:11px;font-weight:900;letter-spacing:.3px}.access-field input,.access-field select{min-height:44px;border:1px solid #111;border-radius:4px;padding:8px 10px;font-size:14px;background:#fff}.access-span2{grid-column:span 2}.access-links{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}.access-links a{display:inline-flex;align-items:center;min-height:40px;padding:7px 11px;border:1px solid #111;border-radius:4px;font-size:12px;font-weight:800;background:#fff}.access-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}.access-actions button{min-height:46px;border:1px solid #111;border-radius:4px;padding:9px 14px;font-weight:900}.access-save{background:#111;color:#fff}.access-clear{background:#fff}.access-summary{margin:0 0 22px;border:2px solid #111;border-radius:5px;background:#fff;overflow:hidden}.access-summary-head{padding:10px 14px;background:#1892f5;color:#fff;font-weight:900;font-size:13px}.access-route{display:grid;grid-template-columns:90px minmax(0,1fr);gap:14px;padding:15px 16px;border-top:1px solid #bbb}.access-route:first-of-type{border-top:0}.access-time{font-size:20px;font-weight:950;letter-spacing:-.5px}.access-route h3{font-size:16px;margin:0 0 3px;font-weight:900}.access-route p{margin:0;font-size:13px;color:#444}.access-badge{display:inline-block;border:1px solid #111;border-radius:3px;padding:2px 6px;font-size:11px;font-weight:800;background:#ffe248;margin-left:7px}.access-note{padding:10px 15px;font-size:11px;color:#555;border-top:1px solid #ccc;background:#f7f7f7}
  @media(max-width:800px){.access-grid{grid-template-columns:1fr 1fr}.access-span2{grid-column:span 2}.access-head{align-items:flex-start;flex-direction:column}.access-route{grid-template-columns:72px minmax(0,1fr)}.access-time{font-size:18px}}
  @media(max-width:480px){.access-grid{grid-template-columns:1fr}.access-span2{grid-column:span 1}.access-route{grid-template-columns:1fr;gap:5px}.access-presets{display:grid;grid-template-columns:1fr 1fr}.access-presets button{font-size:12px}}
  `;
  document.head.appendChild(style);

  function template(){
    const v=load()||{mode:'air',origin:'東京（羽田）',terminal:'福岡空港',localMode:'地下鉄・徒歩',localMinutes:'20'};
    return `<section class="access-planner" id="access-planner"><div class="access-head"><div><p class="eyebrow">BEFORE FUKUOKA / ACCESS</p><h2>福岡までのアクセスも、マイ予定に。</h2><p>飛行機・新幹線の時刻と、福岡到着後の移動まで一続きで保存できます。</p></div></div><div class="access-body">
      <div class="access-presets"><button type="button" data-access-preset="tokyo_air">東京→福岡｜飛行機</button><button type="button" data-access-preset="tokyo_rail">東京→博多｜新幹線</button><button type="button" data-access-preset="osaka_air">大阪→福岡｜飛行機</button><button type="button" data-access-preset="osaka_rail">新大阪→博多｜新幹線</button></div>
      <div class="access-grid">
        <div class="access-field"><label>交通手段</label><select data-access="mode"><option value="air" ${v.mode==='air'?'selected':''}>✈ 飛行機</option><option value="rail" ${v.mode==='rail'?'selected':''}>🚄 新幹線</option></select></div>
        <div class="access-field"><label>日付</label><input type="date" data-access="date" value="${esc(v.date||'2026-10-07')}"></div>
        <div class="access-field"><label>出発地</label><input data-access="origin" value="${esc(v.origin||'')}"></div>
        <div class="access-field"><label>福岡側の到着地</label><input data-access="terminal" value="${esc(v.terminal||'')}"></div>
        <div class="access-field"><label>便名・列車名</label><input data-access="service" placeholder="例：ANA 253 / のぞみ 15号" value="${esc(v.service||'')}"></div>
        <div class="access-field"><label>出発時刻</label><input type="time" data-access="depart" value="${esc(v.depart||'')}"></div>
        <div class="access-field"><label>到着時刻</label><input type="time" data-access="arrive" value="${esc(v.arrive||'')}"></div>
        <div class="access-field"><label>福岡着後の移動</label><select data-access="localMode"><option ${v.localMode==='地下鉄・徒歩'?'selected':''}>地下鉄・徒歩</option><option ${v.localMode==='タクシー'?'selected':''}>タクシー</option><option ${v.localMode==='バス'?'selected':''}>バス</option><option ${v.localMode==='徒歩'?'selected':''}>徒歩</option><option ${v.localMode==='未定'?'selected':''}>未定</option></select></div>
        <div class="access-field"><label>福岡着後の移動時間（分）</label><input type="number" min="0" max="240" data-access="localMinutes" value="${esc(v.localMinutes||'')}"></div>
        <div class="access-field access-span2"><label>移動先</label><input data-access="localDestination" placeholder="例：Garraway F / 最初のイベント会場" value="${esc(v.localDestination||'Garraway F')}"></div>
        <div class="access-field access-span2"><label>メモ</label><input data-access="memo" placeholder="座席・ターミナル・予約番号など" value="${esc(v.memo||'')}"></div>
      </div>
      <div class="access-links" data-access-links></div>
      <div class="access-actions"><button type="button" class="access-save" data-access-save>このアクセスをマイ予定に保存</button><button type="button" class="access-clear" data-access-clear>削除</button></div>
    </div></section>`;
  }
  function collect(root){const o={};root.querySelectorAll('[data-access]').forEach(el=>o[el.dataset.access]=el.value);return o}
  function links(root){
    const mode=root.querySelector('[data-access="mode"]')?.value||'air';
    root.querySelector('[data-access-links]').innerHTML=(official[mode]||[]).map(([n,u])=>`<a href="${u}" target="_blank" rel="noopener">${n} ↗</a>`).join('');
  }
  function renderSummary(){
    const screen=document.querySelector('#screen-plan');if(!screen)return;
    let old=screen.querySelector('.access-summary');if(old)old.remove();
    const v=load();if(!v||(!v.depart&&!v.arrive&&!v.service))return;
    const anchor=screen.querySelector('.plan-daybar')||screen.querySelector('.page-heading');if(!anchor)return;
    const duration=Number(v.localMinutes||0);let localArr='';
    if(v.arrive&&duration){const [h,m]=v.arrive.split(':').map(Number);const t=h*60+m+duration;localArr=String(Math.floor(t/60)%24).padStart(2,'0')+':'+String(t%60).padStart(2,'0')}
    const box=document.createElement('section');box.className='access-summary';
    box.innerHTML=`<div class="access-summary-head">FUKUOKA ACCESS / 福岡までのアクセス</div><div class="access-route"><div class="access-time">${esc(v.depart||'--:--')}</div><div><h3>${v.mode==='air'?'✈ 飛行機':'🚄 新幹線'} ${esc(v.origin||'出発地')} → ${esc(v.terminal||'福岡')} ${v.service?`<span class="access-badge">${esc(v.service)}</span>`:''}</h3><p>${esc(v.date||'')}　到着 ${esc(v.arrive||'未入力')}</p></div></div><div class="access-route"><div class="access-time">${esc(v.arrive||'--:--')}</div><div><h3>${esc(v.terminal||'福岡')} → ${esc(v.localDestination||'次の目的地')}</h3><p>${esc(v.localMode||'移動')} ${duration?`・約${duration}分`:''}${localArr?`　到着目安 ${localArr}`:''}</p></div></div>${v.memo?`<div class="access-note">メモ：${esc(v.memo)}</div>`:''}<div class="access-note">時刻表は変更される場合があります。便・列車の最新情報は各交通事業者の公式サイトで確認してください。</div>`;
    anchor.after(box);
  }
  function mount(){
    const screen=document.querySelector('#screen-plan');if(!screen||screen.querySelector('#access-planner'))return;
    const heading=screen.querySelector('.page-heading')||screen.firstElementChild;
    const wrap=document.createElement('div');wrap.innerHTML=template();const planner=wrap.firstElementChild;
    heading?.after(planner);links(planner);renderSummary();
    planner.addEventListener('change',e=>{if(e.target.matches('[data-access="mode"]')){const mode=e.target.value;planner.querySelector('[data-access="terminal"]').value=mode==='air'?'福岡空港':'博多駅';links(planner)}});
    planner.addEventListener('click',e=>{
      const preset=e.target.closest('[data-access-preset]');if(preset){const p=presets[preset.dataset.accessPreset];Object.entries(p).forEach(([k,v])=>{const el=planner.querySelector(`[data-access="${k}"]`);if(el)el.value=v});links(planner);return}
      if(e.target.closest('[data-access-save]')){save(collect(planner));renderSummary();e.target.textContent='保存しました ✓';setTimeout(()=>e.target.textContent='このアクセスをマイ予定に保存',1200)}
      if(e.target.closest('[data-access-clear]')){localStorage.removeItem(KEY);planner.querySelectorAll('input').forEach(i=>{if(i.type!=='date')i.value=''});renderSummary()}
    });
  }
  const obs=new MutationObserver(()=>mount());obs.observe(document.documentElement,{childList:true,subtree:true});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
})();
