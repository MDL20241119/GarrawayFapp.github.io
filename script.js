// Garraway F photography system: people + space + conversation + serendipity.
const driveThumb=(id,w=1800)=>`https://drive.google.com/thumbnail?id=${id}&sz=w${w}`;
const heroImg=document.querySelector('.hero-photo img');
if(heroImg){heroImg.src=driveThumb('1J6Ne_puDhM-7GLyJ1b7n2AMLfLs8ai1u',2000);heroImg.alt='Garraway Fで人と人が自然につながる風景';heroImg.fetchPriority='high';}

// Serendipity: replace the older static visual with a candid people/space image.
const serendipity=document.querySelector('.statement-photo img');
if(serendipity){serendipity.src=driveThumb('1Flj3ETVCIChlwQpEvB4BbL19bT3EcQpb',1800);serendipity.alt='Garraway Fで偶然の出会いと対話が生まれる風景';}

// Facility: make the living lab visible, not just described.
const facility=document.querySelector('#facility');
if(facility&&!facility.querySelector('.facility-photo-grid')){
 const gallery=document.createElement('div');gallery.className='facility-photo-grid';
 gallery.innerHTML=`<figure class="facility-photo-main"><img src="${driveThumb('16bZEROOxM7CvTH3uOLZGiA8TSjNw8Bp3',1800)}" alt="Garraway Fの空間で活動する人々" loading="lazy"><figcaption>PEOPLE × SPACE</figcaption></figure><figure><img src="${driveThumb('1fXGYmJIcLKstmGU9TwTfHrdjC3OXh4be',1400)}" alt="Garraway Fでの自然なコミュニケーション" loading="lazy"><figcaption>CONVERSATION</figcaption></figure><figure><img src="${driveThumb('1Nbri-E3AxcDM-Drofl2_6qf9wRjEqpow',1400)}" alt="Garraway Fで生まれる活動" loading="lazy"><figcaption>ACTION</figcaption></figure>`;
 const grid=facility.querySelector('.facility-grid');if(grid)facility.insertBefore(gallery,grid);
}

const els=[...document.querySelectorAll('.person,.tiles div,.roles article')];const io=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.animate([{opacity:0,transform:'translateY(24px)'},{opacity:1,transform:'translateY(0)'}],{duration:650,easing:'cubic-bezier(.2,.8,.2,1)',fill:'both'});io.unobserve(e.target)}}),{threshold:.15});els.forEach(e=>io.observe(e));

const newsEvents=[
 {date:'2026-08-18',type:'EVENT',title:'応援カイギ'},
 {date:'2026-08-08',type:'EVENT',title:'（一社）九州インターンシップ推進協議会　事前研修会'},
 {date:'2026-08-08',type:'EVENT',title:'高校生∞チャレンジ定期交流会①「地域企業×事業承継」By林田茉優さん'},
 {date:'2026-08-07',type:'EVENT',title:'神山まるごと高専 学校説明会 in 福岡'},
 {date:'2026-07-20',type:'EVENT',title:'第2回　福岡6-3'},
 {date:'2026-07-14',type:'EVENT',title:'応援カイギ'},
 {date:'2026-07-01',type:'EVENT',title:'YOUTH HUB FUKUOKA〜福岡から、高校生の挑戦を当たり前に〜'},
 {date:'2026-06-27',type:'EVENT',title:'アントレプレナーズチャレンジ採択者キックオフ'},
 {date:'2026-05-27',type:'EVENT',title:'海外移住者はなぜ福岡に集まるのか？vol2'},
 {date:'2026-04-30',type:'EVENT',title:'ビジネス・起業家・異業種交流会'},
 {date:'2026-04-29',type:'EVENT',title:'学生ギャラ談'},
 {date:'2026-04-24',type:'EVENT',title:'アイセック福岡委員会新歓説明会'},
 {date:'2026-04-21',type:'EVENT',title:'めぐるMeet up in 九州'},
 {date:'2026-04-08',type:'EVENT',title:'なぜ海外移住者は福岡に集まるのか？ ― 移動するキャリアと都市の未来を考える対話イベント'},
 {date:'2026-04-04',type:'EVENT',title:'NEO ACADEMIA 2次選考会（招待制のため一般応募なし）'}
];
const newsPhotos=['1CPR6Fu49NVK8rPRV-7oCSRKchWc4NOq7','16YOeNzbw70jxlVz4WW9mnA90T1fx-N7x','12x-q_mGMKcqEicT9HLqtiPb8vBhnta7q'];
const newsSection=document.querySelector('#news');
if(newsSection){
 const today=new Date();today.setHours(0,0,0,0);const status=item=>new Date(item.date+'T00:00:00')>=today?'UPCOMING':'ARCHIVE';const pretty=s=>s.replaceAll('-','.');
 const head=newsSection.querySelector('.news-live-head');if(head){const desc=head.querySelector('p:not(.kicker)');if(desc)desc.textContent='Garraway Fで開催されるイベントや、日々生まれている挑戦をお届けします。';const oldLink=head.querySelector('a');if(oldLink){oldLink.textContent='LATEST EVENTS';oldLink.href='#news-list';oldLink.removeAttribute('target');}}
 if(!newsSection.querySelector('.news-photo-strip')){const strip=document.createElement('div');strip.className='news-photo-strip';strip.innerHTML=newsPhotos.map((id,i)=>`<figure><img src="${driveThumb(id,1500)}" alt="Garraway Fで生まれる${['対話','挑戦','つながり'][i]}" loading="lazy"><figcaption>${['DIALOGUE','CHALLENGE','SERENDIPITY'][i]}</figcaption></figure>`).join('');const head=newsSection.querySelector('.news-live-head');head?.after(strip);}
 const frame=newsSection.querySelector('.news-live-frame');if(frame){frame.id='news-list';frame.className='news-native-wrap';frame.innerHTML='<nav class="news-filters" aria-label="ニュース＆イベント絞り込み"><button class="is-active" data-filter="ALL">ALL</button><button data-filter="UPCOMING">UPCOMING</button><button data-filter="EVENT">EVENT</button><button data-filter="NEWS">NEWS</button><button data-filter="ARCHIVE">ARCHIVE</button></nav><div class="news-native-grid"></div>';const grid=frame.querySelector('.news-native-grid');const render=(filter='ALL')=>{const items=newsEvents.filter(item=>filter==='ALL'||item.type===filter||status(item)===filter);grid.innerHTML=items.length?items.map((item,i)=>`<article class="news-card"><div class="news-meta"><span>${String(i+1).padStart(2,'0')}</span><span>${item.type}</span></div><time datetime="${item.date}">${pretty(item.date)}</time><h3>${item.title}</h3><div class="news-card-foot"><span>${status(item)}</span><span>↗</span></div></article>`).join(''):'<p class="news-empty">該当する情報はありません。</p>';};render();frame.querySelectorAll('.news-filters button').forEach(btn=>btn.addEventListener('click',()=>{frame.querySelectorAll('button').forEach(b=>b.classList.remove('is-active'));btn.classList.add('is-active');render(btn.dataset.filter)}));}
 newsSection.dataset.preserve='native-news-events';
}