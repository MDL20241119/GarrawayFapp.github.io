'use strict';
(() => {
  const data = JSON.parse(document.getElementById('event-data').textContent);
  const byId = new Map(data.map(event => [event.id, event]));
  const cards = Array.from(document.querySelectorAll('.event-card'));
  const area = document.getElementById('area');
  const period = document.getElementById('period');
  const dialog = document.getElementById('event-dialog');
  const periods = {all:['2026-09-21','2026-10-21'],before:['2026-09-21','2026-09-30'],early:['2026-10-01','2026-10-06'],ramen:['2026-10-07','2026-10-11'],after:['2026-10-12','2026-10-21']};
  let mood = 'all';
  let opener = null;
  const esc = value => String(value ?? '').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const sourceLink = (url,label) => `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`;
  function filter() {
    const [start,end] = periods[period.value] || periods.all;
    let count = 0;
    cards.forEach(card => {
      const event = byId.get(card.id);
      const localDates = area.value === 'all' ? null : event.areaDates?.[area.value];
      const dateMatch = localDates ? localDates.some(date => date >= start && date <= end) : event.start <= end && event.end >= start;
      const show = (mood === 'all' || event.category === mood) && (area.value === 'all' || event.areas.includes(area.value)) && dateMatch;
      card.hidden = !show;
      if (show) count++;
    });
    document.getElementById('result-count').innerHTML = `<b>${count}</b> 件の寄り道`;
    document.getElementById('empty').hidden = count !== 0;
    document.getElementById('clear-filters').hidden = mood === 'all' && area.value === 'all' && period.value === 'all';
  }
  document.querySelectorAll('[data-mood]').forEach(button => button.addEventListener('click',() => {
    mood = button.dataset.mood;
    document.querySelectorAll('[data-mood]').forEach(item => item.setAttribute('aria-pressed',String(item === button)));
    filter();
  }));
  area.addEventListener('change',filter);
  period.addEventListener('change',filter);
  document.getElementById('clear-filters').addEventListener('click',() => {
    mood='all';area.value='all';period.value='all';
    document.querySelectorAll('[data-mood]').forEach(item=>item.setAttribute('aria-pressed',String(item.dataset.mood==='all')));
    filter();
  });
  function imageFailure(img) {
    img.hidden=true;
    img.parentElement.classList.add('image-unavailable');
  }
  document.querySelectorAll('img').forEach(img=>{
    img.addEventListener('error',()=>imageFailure(img));
    if(img.complete && !img.naturalWidth) imageFailure(img);
  });
  function openEvent(id,button) {
    const e=byId.get(id);if(!e)return;
    opener=button;
    document.getElementById('dialog-inner').classList.remove('image-unavailable');
    const sourceKind = {official:'主催者・公式案内',media:'メディアの開催紹介',tourism:'観光情報の開催案内'}[e.sourceKind];
    document.getElementById('dialog-inner').innerHTML=`<figure class="dialog-media"><img class="dialog-photo" src="${esc(e.image.url)}" alt="${esc(e.image.alt)}"><figcaption class="image-disclosure"><strong>AI生成イメージ</strong>実際の会場・出演者・作品・商品・景観の写真ではありません。</figcaption></figure><div class="dialog-content"><p class="section-kicker">${esc(e.areaLabel)} / ${esc(e.categoryLabel)}</p><h2 id="dialog-title">${esc(e.hook)}</h2><p class="dialog-name">${esc(e.name)}</p><p class="dialog-description">${esc(e.description)}</p><dl class="detail-grid"><div><dt>開催日</dt><dd>${esc(e.dateLabel)}</dd></div><div><dt>時間・参加条件</dt><dd>${esc(e.admission)}</dd></div><div class="detail-wide"><dt>会場</dt><dd>${esc(e.venue)}</dd></div><div class="detail-wide"><dt>福岡からの行き方</dt><dd>${esc(e.access)}</dd></div></dl><div class="dialog-links"><a href="${esc(e.source)}" target="_blank" rel="noopener noreferrer">${esc(e.sourceLabel || '公式情報・参加方法を見る')} ↗</a><a href="${esc(e.map)}" target="_blank" rel="noopener noreferrer">会場の地図・経路 ↗</a></div>${e.note?`<p class="dialog-notice">${esc(e.note)}</p>`:''}<section class="dialog-sources" aria-label="開催情報の出典"><h3>情報出典 <small>${esc(sourceKind)}</small></h3><p>${sourceLink(e.source,e.sourceName)}</p>${e.additionalSource?`<p>${sourceLink(e.additionalSource,e.additionalSourceName)}</p>`:''}<p>開催情報の確認日：${esc(e.checked)}<br>最新の開催状況・料金・予約条件は主催者の案内をご確認ください。</p></section><p class="dialog-credit">${esc(e.image.credit)} ／ 画像制作日：${esc(e.image.created)}<br>画像制作日は開催情報の再確認日ではありません。</p></div>`;
    const img=dialog.querySelector('img');img.addEventListener('error',()=>imageFailure(img));
    dialog.showModal();
    document.getElementById('close-dialog').focus();
  }
  document.querySelectorAll('[data-event]').forEach(button=>button.addEventListener('click',ev=>{ev.preventDefault();openEvent(button.dataset.event,button);}));
  document.getElementById('close-dialog').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('click',ev=>{if(ev.target===dialog){const rect=dialog.getBoundingClientRect();if(ev.clientX<rect.left||ev.clientX>rect.right||ev.clientY<rect.top||ev.clientY>rect.bottom)dialog.close();}});
  dialog.addEventListener('close',()=>{if(opener?.isConnected)opener.focus({preventScroll:true});});
  filter();
})();
