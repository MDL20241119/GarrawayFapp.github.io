'use strict';
(()=>{
  const INTERVAL=5*60*1000, MAX_AGE=3*60*60*1000;
  const stamp=value=>Date.parse(value||'');
  function healthFor(status,now=Date.now()){
    const checked=stamp(status?.lastSuccessAt);
    if(!Number.isFinite(checked)||checked>now+60000)return '確認記録なし';
    if(now-checked>MAX_AGE)return '更新が遅れています';
    return status.status==='success'?'公式データ取得済み':status.status==='partial'?'一部の取得に失敗':'前回の確認済みデータを表示';
  }
  function validatePair(status,catalog){
    if(!status||!catalog?.meta||!Array.isArray(catalog.events)||!Array.isArray(catalog.venues))throw Error('データ形式を確認できません');
    if(!catalog.events.length||catalog.events.length>5000||catalog.meta.catalogVersion!==status.catalogVersion)throw Error('配信の切替中です');
    const ids=new Set(),venues=new Set(catalog.venues.map(v=>v.id));
    for(const e of catalog.events){
      if(typeof e.id!=='string'||ids.has(e.id)||typeof e.title!=='string'||!Array.isArray(e.dates)||!e.dates.length||!Array.isArray(e.notes)||!venues.has(e.venue)||!['event','session'].includes(e.kind))throw Error('イベント情報を確認できません');
      if(!e.dates.every(d=>/^2026-\d{2}-\d{2}$/.test(d)&&Number.isFinite(Date.parse(d))))throw Error('開催日を確認できません');
      ids.add(e.id);
    }
    if(!Number.isFinite(stamp(catalog.meta.catalogVersion)))throw Error('確認日時を読み取れません');
    return catalog;
  }
  if(typeof module==='object'&&module.exports)module.exports={healthFor,validatePair};
  if(typeof document==='undefined'||!window.GuideApp||window.GUIDE_CONFIG?.preview)return;
  const box=document.createElement('aside');box.id='live-data';box.className='live-data';box.setAttribute('aria-label','スケジュールの更新状況');
  box.innerHTML='<div class="live-data-head"><strong>公式スケジュールを毎時確認</strong><button type="button" id="live-check">最新データを確認 ↻</button></div><p id="live-health" class="live-data-status" role="status" aria-live="polite">更新状況を確認中</p><p id="live-date"></p><p id="live-message">閲覧中も5分ごとに確認します。</p><details><summary>確認した公式サイト・更新内容</summary><div id="live-sources"></div><p>公式登録・公式タイムテーブルを毎時取得。配信には時間差があります。個別主催者ページの補足は別途確認し、開催情報が食い違う場合は要確認と表示します。外部カレンダーに書き出した予定は自動更新されません。</p><div id="live-changes" class="live-data-updates"></div><p><a href="https://www.ramentech.jp/#program" target="_blank" rel="noopener noreferrer">公式イベント一覧 ↗</a>　<a href="https://ramentech2026.aishain.com/" target="_blank" rel="noopener noreferrer">公式タイムテーブル ↗</a></p></details>';
  const anchor=document.querySelector('#screen-explore .search-area');if(!anchor)return;anchor.before(box);
  const el=id=>document.getElementById(id);
  const format=value=>Number.isFinite(stamp(value))?new Intl.DateTimeFormat('ja-JP',{timeZone:'Asia/Tokyo',month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(value))+'（日本時間）':'確認記録なし';
  let status=window.RAMEN_SYNC_STATUS||null, busy=false, pending=null, onlineError=false;
  function show(){
    const label=healthFor(status), current=window.GuideApp.getData();
    box.dataset.health=onlineError||label!=='公式データ取得済み'?'warning':'success';
    el('live-health').textContent=onlineError?'配信データを確認できませんでした':label;
    el('live-date').textContent='表示データの取得：'+format(current.meta.fetchedAt)+' ／ 両公式サイトの最終取得成功：'+format(status?.lastSuccessAt);
    el('live-message').textContent=pending?'新しい情報があります。入力・詳細画面を閉じると反映します。':onlineError?'現在のデータを保持しています。通信回復後に再確認します。':label==='公式データ取得済み'?'閲覧中も5分ごとに確認。保存した予定の開催情報が変わると「マイ予定」に表示します。':'取得できなかった情報は保持しています。来場前に公式の案内をご確認ください。';
    el('live-sources').replaceChildren();
    for(const [key,src] of Object.entries(status?.sources||{})){
      const p=document.createElement('p');p.textContent=(key==='members'?'公式登録':'公式タイムテーブル')+'：'+(src.ok?'取得成功':'取得失敗')+' / '+(src.count??'未確認')+'件 / '+format(src.lastSuccessAt);el('live-sources').append(p);
    }
    el('live-changes').replaceChildren();
    const changes=status?.changes||[];
    for(const item of changes.filter(x=>current.events.some(e=>e.id===x.id&&!e.duplicateOf)).slice(0,8)){
      const a=document.createElement('a');a.href='?date=any&event='+encodeURIComponent(item.id)+'#explore';a.textContent=(item.type==='new'?'追加：':'更新：')+item.title;el('live-changes').append(a);
    }
    document.querySelectorAll('[data-source-date]').forEach(e=>e.textContent='公式データ取得：'+format(current.meta.fetchedAt));
  }
  function canApply(){return !document.querySelector('dialog[open]')&&!document.activeElement?.matches('input,textarea,select,[contenteditable="true"]');}
  function applyPending(){
    if(!pending||!canApply())return;
    window.GuideApp.replaceCatalog(pending);pending=null;show();
  }
  async function check(){
    if(busy||document.hidden)return;
    busy=true;el('live-check').disabled=true;
    try{
      const suffix='?check='+Date.now(), opts={cache:'no-store',signal:AbortSignal.timeout(15000)};
      const response=await fetch('sync-status.json'+suffix,opts);if(!response.ok)throw Error('status unavailable');
      const nextStatus=await response.json(), current=window.GuideApp.getData();
      if(nextStatus.catalogVersion!==current.meta.catalogVersion){
        const result=await fetch('catalog.json'+suffix,{cache:'no-store',signal:AbortSignal.timeout(15000)});if(!result.ok)throw Error('catalog unavailable');
        const next=validatePair(nextStatus,await result.json());
        if(stamp(next.meta.catalogVersion)<stamp(current.meta.catalogVersion))throw Error('古い配信データを検出');
        pending=next;
      }
      status=nextStatus;window.RAMEN_SYNC_STATUS=status;onlineError=false;applyPending();show();
    }catch{onlineError=true;show();}
    finally{busy=false;el('live-check').disabled=false;}
  }
  el('live-check').addEventListener('click',check);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)check();});
  window.addEventListener('online',check);
  document.addEventListener('focusout',()=>setTimeout(applyPending,0));
  document.querySelectorAll('dialog').forEach(d=>d.addEventListener('close',applyPending));
  setInterval(()=>{applyPending();if(!document.hidden)show();},30000);
  setInterval(check,INTERVAL);show();check();
})();
