const els=[...document.querySelectorAll('.person,.tiles div,.roles article')];const io=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.animate([{opacity:0,transform:'translateY(24px)'},{opacity:1,transform:'translateY(0)'}],{duration:650,easing:'cubic-bezier(.2,.8,.2,1)',fill:'both'});io.unobserve(e.target)}}),{threshold:.15});els.forEach(e=>io.observe(e));

// Native NEWS & EVENTS module.
// This intentionally does NOT embed or depend on the legacy garrawayf.com display.
// Add/update items in this data array to operate the new site independently.
const newsEvents=[
 {date:'2026.08.18',type:'EVENT',title:'応援カイギ'},
 {date:'2026.08.08',type:'EVENT',title:'（一社）九州インターンシップ推進協議会　事前研修会'},
 {date:'2026.08.08',type:'EVENT',title:'高校生∞チャレンジ定期交流会①「地域企業×事業承継」By林田茉優さん'},
 {date:'2026.08.07',type:'EVENT',title:'神山まるごと高専 学校説明会 in 福岡'},
 {date:'2026.07.20',type:'EVENT',title:'第2回　福岡6-3'},
 {date:'2026.07.14',type:'EVENT',title:'応援カイギ'},
 {date:'2026.07.01',type:'EVENT',title:'YOUTH HUB FUKUOKA〜福岡から、高校生の挑戦を当たり前に〜'},
 {date:'2026.06.27',type:'EVENT',title:'アントレプレナーズチャレンジ採択者キックオフ'},
 {date:'2026.05.27',type:'EVENT',title:'海外移住者はなぜ福岡に集まるのか？vol2'},
 {date:'2026.04.30',type:'EVENT',title:'ビジネス・起業家・異業種交流会'},
 {date:'2026.04.29',type:'EVENT',title:'学生ギャラ談'},
 {date:'2026.04.24',type:'EVENT',title:'アイセック福岡委員会新歓説明会'},
 {date:'2026.04.21',type:'EVENT',title:'めぐるMeet up in 九州'},
 {date:'2026.04.08',type:'EVENT',title:'なぜ海外移住者は福岡に集まるのか？ ― 移動するキャリアと都市の未来を考える対話イベント'},
 {date:'2026.04.04',type:'EVENT',title:'NEO ACADEMIA 2次選考会（招待制のため一般応募なし）'}
];

const newsSection=document.querySelector('#news');
if(newsSection){
 const head=newsSection.querySelector('.news-live-head');
 if(head){
  const desc=head.querySelector('p:not(.kicker)');
  if(desc) desc.textContent='Garraway Fで開催されるイベントや、日々生まれている挑戦をお届けします。';
  const oldLink=head.querySelector('a');
  if(oldLink){oldLink.textContent='LATEST EVENTS';oldLink.href='#news-list';}
 }
 const frame=newsSection.querySelector('.news-live-frame');
 if(frame){
  frame.id='news-list';
  frame.innerHTML=`<div class="news-native-toolbar"><span>NEWS / EVENTS</span><span>${newsEvents.length} STORIES</span></div><div class="news-native-grid">${newsEvents.map((item,i)=>`<article class="news-card"><div class="news-meta"><span>${String(i+1).padStart(2,'0')}</span><span>${item.type}</span></div><time>${item.date}</time><h3>${item.title}</h3><span class="news-arrow">↗</span></article>`).join('')}</div>`;
 }
 newsSection.dataset.preserve='native-news-events';
}
