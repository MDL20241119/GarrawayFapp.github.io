'use strict';
(()=>{
  const catalog=window.RAMEN_CATALOG;if(!catalog)return;
  const box=document.createElement('aside');box.id='auto-update';box.className='wrap auto-update';box.setAttribute('aria-label','自動更新の状況');
  box.innerHTML='<div class="auto-head"><strong>毎朝 6:00 自動更新</strong><span id="auto-health" role="status">更新状況を確認中</span></div><p id="auto-checked"></p><p id="auto-message"></p><button id="auto-reload" type="button" hidden>新しい情報を読み込む ↻</button><details><summary>更新状況・今回の変更を見る</summary><div id="auto-sources"></div><div id="auto-changes"></div><p class="auto-scope">自動更新の対象は、公式登録サイトと公式タイムテーブルの公開データです。個別主催者ページの補足とGarraway Fの独自企画は自動上書きせず、詳細画面に個別確認日を表示します。保存済みのGoogleカレンダー・ICSは自動更新されません。</p><a href="https://github.com/MDL20241119/GarrawayFapp.github.io/actions/workflows/ramen-daily-update.yml" target="_blank" rel="noopener noreferrer">更新処理の実行履歴 ↗</a></details>';
  const anchor=document.querySelector('.intro-strip');if(anchor)anchor.after(box);else document.getElementById('schedule')?.before(box);
  const el=id=>document.getElementById(id);
  const format=value=>{const d=new Date(value);return value&&!Number.isNaN(d.getTime())?new Intl.DateTimeFormat('ja-JP',{timeZone:'Asia/Tokyo',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}).format(d)+'（日本時間）':'成功記録なし';};
  function show(s){
    if(!s)return;
    const old=s.lastSuccessAt&&(Date.now()-new Date(s.lastSuccessAt).getTime()>30*3600000);
    const newer=s.catalogVersion&&s.catalogVersion!==catalog.meta.catalogVersion;
    const good=s.status==='success'&&!old;
    box.dataset.health=good?'success':'warning';
    el('auto-health').textContent=old?'更新が遅れています':good?'公式データ取得済み':s.status==='partial'?'一部の取得に失敗':'前回のデータを表示';
    el('auto-checked').textContent='両データの最終取得成功：'+format(s.lastSuccessAt);
    el('auto-message').textContent=newer?'新しいデータがあります。下のボタンで検索画面を更新してください。':good?'毎朝6:00に取得を開始。失敗時は6:35に再試行します。処理・配信には時間差があります。':'取得できなかった情報は消さずに保持しています。来場前に主催者の案内をご確認ください。';
    el('auto-reload').hidden=!newer;
    const sources=el('auto-sources');sources.replaceChildren();
    for(const [key,r] of Object.entries(s.sources||{})){
      const p=document.createElement('p');p.textContent=(key==='members'?'公式登録':'公式時間割')+'：'+(r.ok?'取得成功':'取得失敗')+(Number.isInteger(r.count)?' / '+r.count+'件':'')+' / 最終成功 '+format(r.lastSuccessAt);sources.append(p);
    }
    const updates=el('auto-changes');updates.replaceChildren();
    const p=document.createElement('p');const changes=s.changes||[];p.textContent=changes.length?'今回の追加・内容更新：'+changes.length+'枠':'今回、掲載内容に変更はありません。';updates.append(p);
    for(const c of changes.slice(0,12)){
      const a=document.createElement('a');a.className='auto-change';a.href='?date=any&event='+encodeURIComponent(c.id)+'#schedule';a.textContent=(c.type==='new'?'［追加］':'［更新］')+c.title;updates.append(a);
    }
    if(changes.length>12){const p=document.createElement('p');p.textContent='ほか'+(changes.length-12)+'枠。詳細は実行履歴で確認できます。';updates.append(p);}
    const scope=el('source-scope');if(scope)scope.textContent='公開登録'+catalog.meta.registrationEvents+'件と公式時間割'+catalog.meta.timetableSlots+'枠を取得・照合し、独自企画・個別主催者による補足を含む'+catalog.events.length+'枠を掲載。自動取得の状況はページ上部、個別の確認日は詳細画面をご確認ください。';
  }
  el('auto-reload').addEventListener('click',()=>location.reload());
  show(window.RAMEN_SYNC_STATUS);
  async function check(){try{const r=await fetch('sync-status.json?t='+Date.now(),{cache:'no-store'});if(r.ok)show(await r.json());}catch{if(!window.RAMEN_SYNC_STATUS)el('auto-health').textContent='更新状況を取得できませんでした';}}
  check();setInterval(()=>{if(!document.hidden)check();},600000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)check();});
})();
