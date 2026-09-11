/* Event-first trip planner. Published timetable snapshots, never live availability.
 * Checked 2026-09-11. ANA: 2026-07-01–10-24 PDFs, October rows only.
 * JR Central: N700S-every.pdf, regular services from 2026-03-14, selected direct trains.
 * Keep validity, operator and source disclosure next to the timetable.
 */
'use strict';
(()=>{
const AIR={
 tokyo:{
  outbound:`239,06:20,08:10,W;3841,06:35,08:30,S;1075,06:45,08:35,A;241,07:30,09:25,A;243,08:10,10:00,A;245,08:45,10:35,A;3843,09:20,11:15,S;247,09:40,11:30,A;249,10:15,12:10,A;3845,10:15,12:10,S;251,11:30,13:20,A;3847,12:20,14:15,S;253,12:35,14:30,A;3849,13:15,15:10,S;255,13:30,15:20,A;257,14:25,16:15,A;259,15:00,16:55,A;261,15:40,17:35,A;3851,15:55,17:50,S;263,16:20,18:20,A;265,17:00,19:05,A;267,18:00,19:55,A;3853,18:30,20:25,S;269,19:00,20:50,A;271,19:20,21:15,A;273,19:35,21:30,A;3855,19:55,21:50,S`,
  return:`240,07:00,08:40,A;3840,07:00,08:40,S;242,07:50,09:30,A;244,08:40,10:25,A;3842,09:10,11:00,S;1076,09:30,11:10,A;246,10:15,12:00,A;248,10:50,12:35,A;250,11:25,13:10,A;3844,11:50,13:40,S;252,12:25,14:10,A;3846,12:50,14:40,S;254,13:05,14:50,A;256,14:15,16:00,A;3848,14:15,16:05,S;258,15:20,17:10,A;3850,15:55,17:45,S;260,16:20,18:10,A;262,17:10,19:00,A;264,17:45,19:35,A;266,18:30,20:15,A;3852,19:00,20:45,S;268,19:15,21:00,A;270,19:55,21:40,A;272,20:45,22:25,A;3854,21:05,22:45,S;274,21:15,23:00,W`
 },
 osaka:{
  outbound:`3167,07:15,08:30,I;421,08:10,09:25,A;423,09:20,10:35,W;3169,10:40,11:55,I;425,14:25,15:40,W;427,17:05,18:25,W;429,20:10,21:30,A`,
  return:`420,07:10,08:15,A;3168,09:00,10:10,I;424,10:50,12:05,W;3170,12:35,13:45,I;426,16:15,17:30,W;428,17:45,18:55,A;430,19:10,20:30,W`
 }
};
// Nozomi: number, Tokyo departure, Shin-Osaka departure, Hakata arrival.
const RAIL_DOWN=`1,06:00,08:24,10:52;3,06:15,08:41,11:09;5,06:33,09:02,11:30;7,06:48,09:17,11:45;9,07:12,09:41,12:09;11,07:30,10:02,12:30;13,07:48,10:17,12:45;15,08:12,10:41,13:09;17,08:30,11:02,13:30;19,09:12,11:41,14:09;21,09:30,12:02,14:30;23,10:12,12:41,15:09;25,10:30,13:02,15:30;27,11:12,13:41,16:09;29,11:30,14:02,16:30;31,12:12,14:41,17:09;33,12:30,15:02,17:30;35,13:12,15:41,18:09;37,13:30,16:02,18:30;39,14:12,16:41,19:09;41,14:30,17:02,19:30;43,15:12,17:41,20:09;45,15:30,18:02,20:30;47,16:12,18:41,21:09;49,16:30,19:02,21:30;51,16:48,19:17,21:45;53,17:12,19:41,22:09;55,17:30,20:02,22:30;57,18:12,20:41,23:09;59,18:51,21:23,23:51`;
// Nozomi: number, Hakata departure, Shin-Osaka arrival, Tokyo arrival.
const RAIL_UP=`2,06:00,08:28,10:57;4,06:36,09:04,11:33;6,07:15,09:43,12:15;8,07:36,10:04,12:33;10,08:00,10:28,12:57;12,08:15,10:43,13:15;14,08:36,11:04,13:33;16,09:15,11:43,14:15;18,09:36,12:04,14:33;20,10:15,12:43,15:15;22,10:36,13:04,15:33;24,11:15,13:43,16:15;26,11:36,14:04,16:33;28,12:15,14:43,17:15;30,12:36,15:04,17:33;32,13:15,15:43,18:15;34,13:36,16:04,18:33;36,14:15,16:43,19:15;38,14:36,17:04,19:33;40,15:00,17:28,19:57;42,15:15,17:43,20:15;44,15:36,18:04,20:33;46,16:00,18:28,20:57;48,16:15,18:43,21:15;52,17:00,19:28,21:57;54,17:15,19:43,22:15;56,17:36,20:04,22:33;58,18:03,20:31,22:57;60,18:18,20:46,23:12;62,18:36,21:04,23:32;64,19:00,21:21,23:45`;
const OSAKA_EXTRA={outbound:`みずほ601号,06:00,08:28;さくら741号,06:25,09:04;のぞみ101号,07:11,09:39;みずほ603号,07:23,09:51;みずほ605号,07:50,10:18;のぞみ103号,07:56,10:24`,return:`みずほ610号,19:15,21:37;のぞみ106号,19:30,21:58;みずほ612号,19:48,22:16;のぞみ108号,20:01,22:28;さくら772号,20:18,22:53;ひかり682号,20:52,23:32;みずほ614号,21:09,23:37`};
const SOURCE={
 tokyo:'https://www.ana.co.jp/guide/plan/airinfo/dom-timetable/pdf/timetable_tokyo_20260701_20261024.pdf',
 osaka:'https://www.ana.co.jp/guide/plan/airinfo/dom-timetable/pdf/timetable_osaka_20260701_20261024.pdf',
 rail:'https://railway.jr-central.co.jp/pwd/_pdf/N700S-every.pdf',
 subway:'https://subway.city.fukuoka.lg.jp/schedule/index.php',
 airport:'https://www.fukuoka-airport.jp/access/subway.html',
 hakata:'https://subway.city.fukuoka.lg.jp/eki/stations/hakata.php'
};
const KEY='garraway_ramen_access_v3';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const minutes=s=>/^\d{2}:\d{2}$/.test(s||'')&&+s.slice(0,2)<24&&+s.slice(3)<60?+s.slice(0,2)*60+(+s.slice(3)):null;
const clock=n=>String(Math.floor(((n%1440)+1440)%1440/60)).padStart(2,'0')+':'+String(((n%1440)+1440)%60).padStart(2,'0');
const validDay=d=>/^2026-\d{2}-\d{2}$/.test(d||'')&&!Number.isNaN(Date.parse(d))&&new Date(d+'T12:00:00Z').toISOString().slice(0,10)===d;
const ordinal=d=>Date.parse(d+'T00:00:00Z')/86400000;
const dateLabel=d=>d?`${+d.slice(5,7)}/${+d.slice(8)}（${'日月火水木金土'[new Date(d+'T12:00:00Z').getUTCDay()]}）`:'';
const at=(n,day)=>{const delta=Math.floor(n/1440);return (delta?dateLabel(new Date((ordinal(day)+delta)*86400000).toISOString().slice(0,10))+' ':'')+clock(n);};
const rows=s=>s.split(';').map(r=>r.split(','));
const number=(v,d,min=0,max=240)=>v!==''&&v!==null&&v!==undefined&&Number.isFinite(+v)?Math.max(min,Math.min(max,Math.round(+v))):d;
const duration=n=>n>=60?`${Math.floor(n/60)}時間${n%60?`${n%60}分`:''}`:`${n}分`;
const link=(label,url)=>`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${label} ↗</a>`;
function services(city,mode,kind,day){
 if(!validDay(day)||day<'2026-10-01'||day>'2026-10-24')return [];
 let list;
 if(mode==='air')list=rows(AIR[city][kind]).map(([n,dep,arr,op])=>({id:'NH'+n,name:'ANA（NH）'+n+'便',dep,arr,operator:{A:'ANA',W:'ANAウィングス',S:'スターフライヤー',I:'IBEXエアラインズ'}[op]}));
 else {
  list=rows(kind==='outbound'?RAIL_DOWN:RAIL_UP).map(([n,a,b,c])=>({id:'N'+n,name:'のぞみ'+n+'号',dep:kind==='outbound'?(city==='tokyo'?a:b):a,arr:kind==='outbound'?c:(city==='tokyo'?c:b),operator:'新幹線・直通'}));
  if(city==='osaka')list.push(...rows(OSAKA_EXTRA[kind]).map(([name,dep,arr])=>({id:name,name,dep,arr,operator:'新幹線・直通'})));
 }
 return list.sort((a,b)=>minutes(a.dep)-minutes(b.dep));
}
function cleanPref(raw,kind){
 const p=raw&&typeof raw==='object'?raw:{};
 return {city:p.city==='osaka'?'osaka':'tokyo',mode:p.mode==='rail'?'rail':'air',day:validDay(p.day)?p.day:'',eventBuffer:number(p.eventBuffer,15),airBuffer:number(p.airBuffer,kind==='outbound'?25:60),railBuffer:number(p.railBuffer,kind==='outbound'?10:20),manualCity:number(p.manualCity,null,1),manualTarget:typeof p.manualTarget==='string'?p.manualTarget:'',selected:typeof p.selected==='string'?p.selected:'',selectionDay:validDay(p.selectionDay)?p.selectionDay:'',selectionTarget:typeof p.selectionTarget==='string'?p.selectionTarget:''};
}
function readPrefs(){
 let p={};try{p=JSON.parse(localStorage.getItem(KEY)||'{}')||{};}catch{}
 if(!p.outbound&&!p.return){try{const old=JSON.parse(localStorage.getItem('garraway_ramen_access_v2')||'{}')||{};for(const kind of ['outbound','return'])p[kind]={city:old[kind+'City'],mode:old[kind+'Mode']};}catch{}}
 return {outbound:cleanPref(p.outbound,'outbound'),return:cleanPref(p.return,'return')};
}
let prefs=readPrefs(),active='outbound',showAll=false,storageOK=true,lastSignature='',raf=0,root;
const persist=()=>{try{localStorage.setItem(KEY,JSON.stringify(prefs));storageOK=true;}catch{storageOK=false;}};
function targets(app=window.GuideApp){
 if(!app?.getState||!app.itinerary)return {outbound:null,return:null,unresolved:0};
 const state=app.getState(),days=[...new Set(Object.values(state.entries||{}).map(e=>e.day))].filter(validDay).sort();
 const all=days.flatMap(day=>app.itinerary(day).rows),ready=all.filter(r=>!r.invalid&&Number.isFinite(r.start)&&Number.isFinite(r.end)&&r.e?.status!=='cancelled'&&!r.e?.calendarBlocked);
 return {outbound:ready.slice().sort((a,b)=>ordinal(a.day)-ordinal(b.day)||a.start-b.start)[0]||null,return:ready.slice().sort((a,b)=>ordinal(b.day)-ordinal(a.day)||b.end-a.end)[0]||null,unresolved:all.length-ready.length};
}
const targetSig=t=>t?JSON.stringify([t.key,t.day,t.start,t.end,t.e?.title,t.venue?.id,t.venue?.geo]):'';
const place=v=>v?.geo?.address||v?.address||[v?.name,'福岡'].filter(Boolean).join(' ');
const mapURL=(from,to,mode='transit')=>'https://www.google.com/maps/dir/?'+new URLSearchParams({api:'1',origin:from,destination:to,travelmode:mode});
function distance(a,b){const rad=Math.PI/180;const q=Math.sin((b.lat-a.lat)*rad/2)**2+Math.cos(a.lat*rad)*Math.cos(b.lat*rad)*Math.sin((b.lng-a.lng)*rad/2)**2;return 6371000*2*Math.atan2(Math.sqrt(q),Math.sqrt(1-q));}
// An intentionally simple route with no subway transfers. Walking is a planning
// estimate (straight-line distance × 1.35, 70m/min, rounded up to five minutes).
function cityRoute(venue,mode,kind,manual=null){
 const hub=mode==='air'?'福岡空港（国内線）':'博多駅';
 const dest=venue?.name||'イベント会場',from=kind==='outbound'?hub:place(venue),to=kind==='outbound'?place(venue):hub;
 const url=mapURL(from,to),geo=venue?.geo;
 if(manual!==null)return {minutes:manual,steps:[{title:`${kind==='outbound'?hub:dest} → ${kind==='outbound'?dest:hub}`,note:'地図で確認して入力した市内移動時間',minutes:manual}],url,manual:true};
 if(!geo||geo.status!=='located'||!Number.isFinite(geo.lat)||!Number.isFinite(geo.lng))return {minutes:null,steps:[],url};
 const hakata={lat:33.5902,lng:130.4206},tenjin={lat:33.5913,lng:130.3992};
 const dh=distance(geo,hakata),dt=distance(geo,tenjin),station=dh<900?'博多駅':dt<1200?'天神駅':null;
 if(!station)return {minutes:null,steps:[],url};
 const walk=Math.max(5,Math.ceil((station==='博多駅'?dh:dt)*1.35/70/5)*5),steps=[];
 if(mode==='rail'&&station==='博多駅')steps.push({title:kind==='outbound'?`博多駅 → ${dest}`:`${dest} → 博多駅`,note:'改札から地図を見ながら徒歩・館内移動',minutes:walk});
 else {
  const ride=station==='博多駅'?5:mode==='air'?11:6;
  const board=kind==='outbound'?(mode==='air'?'福岡空港駅':'博多駅'):station;
  const alight=kind==='outbound'?station:(mode==='air'?'福岡空港駅':'博多駅');
  const entry={title:`${board}で地下鉄へ`,note:kind==='outbound'?(mode==='air'?'国内線の南側からB2Fへ。到着口／北からは右方向へ。':'新幹線改札を出て「地下鉄 空港線」の案内へ。'): '空港線の改札へ。乗車方向を確認。',minutes:10};
  const train={title:`${board} → ${alight}`,note:`地下鉄 空港線・${kind==='outbound'?'姪浜・唐津方面':'福岡空港行き'}／乗り換えなし`,minutes:ride};
  const foot={title:kind==='outbound'?`${station} → ${dest}`:`${dest} → ${station}`,note:venue.id==='garraway'?(kind==='outbound'?'徒歩で今泉・西鉄天神CLASSへ／会場は3F':'西鉄天神CLASS 3Fから天神駅へ徒歩'):'地上への移動・徒歩・館内移動の目安',minutes:walk};
  steps.push(...(kind==='outbound'?[entry,train,foot]:[foot,entry,train]));
 }
 return {minutes:steps.reduce((s,x)=>s+x.minutes,0),steps,url,station,manual:false};
}
function context(kind,ts=targets()){
 const p=prefs[kind],target=ts[kind],day=p.day||target?.day||'2026-10-07',route=cityRoute(target?.venue,p.mode,kind,p.manualTarget===targetSig(target)?p.manualCity:null);
 const terminal=p.mode==='air'?'福岡空港':'博多駅',origin=p.mode==='air'?(p.city==='tokyo'?'羽田空港':'伊丹空港'):(p.city==='tokyo'?'東京駅':'新大阪駅');
 const buffer=p.mode==='air'?p.airBuffer:p.railBuffer;
 const targetMinute=target?(ordinal(target.day)-ordinal(day))*1440+(kind==='outbound'?target.start:target.end):null;
 const total=route.minutes===null?null:route.minutes+buffer+p.eventBuffer;
 const threshold=targetMinute===null||total===null?null:targetMinute+(kind==='outbound'?-total:total);
 return {p,kind,target,day,route,terminal,origin,buffer,targetMinute,total,threshold,services:services(p.city,p.mode,kind,day)};
}
function assess(service,c){
 if(c.threshold===null)return {ok:false,unknown:true,label:'予定・経路を確認'};
 const slack=c.kind==='outbound'?c.threshold-minutes(service.arr):minutes(service.dep)-c.threshold;
 // Estimate on the same day as the transport. Overnight stays need their own hotel route.
 const night=!!c.route.station&&!(c.p.mode==='rail'&&c.route.station==='博多駅')&&(c.kind==='outbound'?minutes(service.arr)+c.buffer>23*60:minutes(service.dep)-c.buffer-c.route.minutes<6*60);
 return {ok:slack>=0&&!night,slack,night,label:slack<0?`${duration(-slack)}不足`:night?'地下鉄の始発・終電を確認':`余裕 ${duration(slack)}`};
}
function selected(c){return c.p.selectionDay===c.day?c.services.find(s=>s.id===c.p.selected):null;}
function choiceStale(c){return !!c.p.selected&&(c.p.selectionTarget!==targetSig(c.target)||!selected(c));}
function field(label,name,value,type='number',extra=''){return `<label class="tp-field"><span>${label}</span><input data-pref="${name}" type="${type}" value="${esc(value??'')}" ${type==='number'?'min="0" max="240" step="1"':''} ${extra}></label>`;}
function routeHTML(c){
 const {route,terminal,p,kind,target}=c;
 const end=target?.venue?.name||'会場未確認';
 const steps=route.steps.map((s,i)=>`<li><span class="tp-step-num">${i+1}</span><div><strong>${esc(s.title)}</strong><p>${esc(s.note)}</p></div><b>約${s.minutes}分</b></li>`).join('');
 return `<section class="tp-route"><div class="tp-section-title"><h3>${kind==='outbound'?terminal+'から会場へ':'会場から'+terminal+'へ'}</h3>${route.minutes!==null?`<span class="tp-pill">市内移動 約${route.minutes}分</span>`:''}</div>${steps?`<ol class="tp-route-steps">${steps}</ol>`:`<p class="tp-note">${target?esc(end)+'の経路は未確認です。地図で所要時間を確認し、「時間を調整」から市内移動時間を入力してください。':'イベントをマイ予定に追加すると、会場までの動線が表示されます。'}</p>`}<div class="tp-links">${target?link('この経路を地図で確認',route.url):''}${link(p.mode==='air'?'空港の地下鉄乗り場':'博多駅の構内図',SOURCE[p.mode==='air'?'airport':'hakata'])}${link('地下鉄の時刻表',SOURCE.subway)}</div><p class="tp-fine">徒歩・駅移動・待ち時間は目安です。徒歩は会場位置からの概算。${p.mode==='air'?'国内線ターミナルを利用するルートです。':''}</p></section>`;
}
function scheduleHTML(c){
 const {kind,p,services:list}=c,available=list.filter(s=>assess(s,c).ok);
 const ordered=available.slice().sort((a,b)=>kind==='outbound'?minutes(b.dep)-minutes(a.dep):minutes(a.dep)-minutes(b.dep));
 const current=selected(c),recommend=ordered.slice(0,3),display=showAll||c.threshold===null?list:recommend;
 if(current&&!display.some(s=>s.id===current.id))display.unshift(current);
 const outbound=kind==='outbound',from=outbound?c.origin:c.terminal,to=outbound?c.terminal:c.origin;
 return `<section class="tp-timetable"><div class="tp-section-title"><h3>${p.mode==='air'?'飛行機':'新幹線'}の時刻表</h3><span class="tp-pill">${esc(dateLabel(c.day))}</span></div><p class="tp-line-label">${esc(from)} <span aria-hidden="true">→</span> ${esc(to)}</p><p class="tp-note">${p.mode==='air'?'ANA便名で掲載（共同運航便を含む）。JALなど他社便は公式検索へ。':'直通の定期列車を抜粋。臨時列車・乗り継ぎ便は公式検索へ。'} ${link('元の公式時刻表PDF',SOURCE[p.mode==='air'?p.city:'rail'])}</p>${!list.length?'<p class="tp-alert">この日付の時刻表は掲載していません。掲載期間は2026年10月1日〜24日です。公式サイトで日付を指定して確認してください。</p>':c.threshold!==null?`<p class="tp-result-count">${available.length?`掲載${list.length}件のうち <strong>${available.length}件</strong>が時間条件に合います。${showAll?'':outbound?'遅く出発できる順に表示しています。':'早く出発できる順に表示しています。'}`:'掲載候補には、時間条件に合う便・列車がありません。前泊・翌日帰着、交通手段の変更、他社便も検討してください。'}</p>`:'<p class="tp-note">時刻表は閲覧できます。イベントと経路が決まると、時間条件に合う候補を選べます。</p>'}${list.length?`<div class="tp-table-wrap" tabindex="0" aria-label="${p.mode==='air'?'飛行機':'新幹線'}の時刻表"><table><caption class="tp-sr-only">${esc(dateLabel(c.day)+' '+from+'から'+to+'の時刻表')}</caption><thead><tr><th scope="col">${p.mode==='air'?'便名・運航会社':'列車名'}</th><th scope="col">出発</th><th scope="col">到着</th><th scope="col">時間の判定</th><th scope="col">選択</th></tr></thead><tbody>${display.map(s=>{const a=assess(s,c),is=current?.id===s.id;return `<tr class="${is?'tp-picked':''}"><th scope="row">${esc(s.name)}<small>${esc(s.operator)}・${duration(minutes(s.arr)-minutes(s.dep))}</small></th><td class="tp-time">${s.dep}</td><td class="tp-time">${s.arr}</td><td><span class="tp-status ${a.ok?'tp-ok':'tp-check'}">${esc(a.label)}</span></td><td><button type="button" data-select-service="${esc(s.id)}" aria-pressed="${is}" ${!a.ok?'disabled':''}>${is?'✓ 選択済み':p.mode==='air'?'この便を選ぶ':'この列車を選ぶ'}</button></td></tr>`;}).join('')||'<tr><td colspan="5">候補がありません。「すべての時刻を見る」から比較できます。</td></tr>'}</tbody></table></div><button class="tp-show-all" type="button" data-show-all aria-expanded="${showAll}">${showAll?'時間条件に合う候補に戻る':`すべての時刻を見る（${list.length}件）`}</button>`:''}<div class="tp-links">${p.mode==='air'?link('ANAで日時・空席を確認','https://www.ana.co.jp/')+link('JALの時刻表','https://www.jal.co.jp/jp/ja/dom/route/time/')+link('福岡空港の全社時刻表','https://www.fukuoka-airport.jp/flight/schedule/'):link('JR東海の時刻検索','https://railway.jr-central.co.jp/jikoku/')+link('スマートEXで予約を確認','https://smart-ex.jp/')}</div><p class="tp-fine">2026/9/11確認。${p.mode==='air'?'ANAの7/1〜10/24ダイヤから10月の時刻を掲載。':'JR東海の2026/3/14改正・定期列車時刻表から抜粋。'} 時刻は日本時間。運航日・時刻変更・空席は公式サイトで最終確認してください。選択は予約ではありません。</p></section>`;
}
function timelineHTML(c){
 const s=selected(c);if(!s)return '';
 const a=assess(s,c),out=c.kind==='outbound',t=c.target;
 if(!t)return '<p class="tp-alert">予定を追加して、選択した便との接続を再確認してください。</p>';
 const lines=[],add=(time,title,note='')=>lines.push({time,title,note});
 if(t.day!==c.day){
  if(!out)add(c.targetMinute,'最後のイベント終了',t.e?.title||t.x?.title);
  if(!out)add(minutes(s.dep)-c.buffer,c.terminal+'に到着する目安','宿泊先からの経路は別途確認');
  add(minutes(s.dep),(out?c.origin:c.terminal)+'を出発',s.name);
  add(minutes(s.arr),(out?c.terminal:c.origin)+'に到着');
  if(out)add(c.targetMinute,'最初のイベント','宿泊先から会場への経路は別途確認／'+(t.e?.title||t.x?.title));
 }else if(out){
  add(minutes(s.dep),c.origin+'を出発',s.name);
  add(minutes(s.arr),c.terminal+'に到着',c.p.mode==='air'?`降機・荷物受け取り 約${c.buffer}分`:`改札まで 約${c.buffer}分`);
  let time=minutes(s.arr)+c.buffer;
  for(const step of c.route.steps){add(time,step.title,`約${step.minutes}分／${step.note}`);time+=step.minutes;}
  if(c.route.minutes!==null)add(time,'会場に到着予定',`受付・余裕 ${c.p.eventBuffer}分を確保`);
  add(c.targetMinute,'最初のイベント',t.e?.title||t.x?.title);
 }else{
  const depart=minutes(s.dep)-c.buffer-(c.route.minutes||0);
  add(c.targetMinute,'最後のイベント終了',t.e?.title||t.x?.title);
  add(depart,'会場を出る目安',`終了後の余裕 ${c.p.eventBuffer}分を含めて判定`);
  let time=depart;
  for(const step of c.route.steps){add(time,step.title,`約${step.minutes}分／${step.note}`);time+=step.minutes;}
  add(minutes(s.dep)-c.buffer,c.terminal+'に到着する目安',`出発${c.buffer}分前。${c.p.mode==='air'?'荷物預け・保安検査・搭乗口への移動':'新幹線改札・ホームへの移動'}を済ませる`);
  add(minutes(s.dep),c.terminal+'を出発',s.name);
  add(minutes(s.arr),c.origin+'に到着');
 }
 return `<section class="tp-itinerary"><div class="tp-section-title"><h3>選んだ便での${out?'行き':'帰り'}の行程</h3><button type="button" data-clear-service>選択を解除</button></div>${choiceStale(c)?'<p class="tp-alert">イベント・会場・日付が変わりました。最新の予定で再計算しています。時刻表から便を選び直してください。</p>':''}${!a.ok?`<p class="tp-alert">接続を見直してください：${esc(a.label)}</p>`:''}${t.day!==c.day?'<p class="tp-alert">別の日の移動です。宿泊先への経路・宿泊先から会場への移動は、この直行ルートには含みません。</p>':''}<ol class="tp-timeline">${lines.map(l=>`<li><time>${esc(at(l.time,c.day))}</time><div><strong>${esc(l.title)}</strong>${l.note?`<p>${esc(l.note)}</p>`:''}</div></li>`).join('')}</ol><p class="tp-fine">地下鉄と徒歩の時刻は目安です。便・列車以外の発着時刻は実際の時刻表ではありません。</p></section>`;
}
function summaryHTML(ts){
 return ['outbound','return'].map(kind=>{const c=context(kind,ts),s=selected(c),a=s?assess(s,c):null;return `<button type="button" class="tp-summary-card ${active===kind?'tp-active':''}" data-trip-tab="${kind}" aria-pressed="${active===kind}"><span>${kind==='outbound'?'行き｜このイベントに間に合う':'帰り｜このイベント後に帰る'}</span><strong>${s?`${esc(dateLabel(c.day))} ${s.dep} → ${s.arr}`:kind==='outbound'?'行きの便を選ぶ':'帰りの便を選ぶ'}</strong><small>${s?esc(s.name+' ／ '+(choiceStale(c)?'予定変更・要確認':a.label)):kind==='outbound'?'最初のイベントから逆算':'最後のイベントから逆算'}</small></button>`;}).join('');
}
function render(){
 if(!root)return;
 const ts=targets(),c=context(active,ts),{p,target,kind}=c,out=kind==='outbound';
 const focus=root.contains(document.activeElement)?document.activeElement:null;
 const focusKey=focus?.dataset.pref;
 const detailsOpen=root.querySelector('[data-settings]')?.open;
 root.innerHTML=`<header class="tp-head"><p>TRIP PLANNER / 往復アクセス</p><h2>イベントが決まったら、<br class="tp-mobile-break">行き方・帰り方を選ぼう。</h2><p>マイ予定の全日程から、最初と最後のイベントに合わせて逆算します。</p></header><div class="tp-inner"><div class="tp-summary" role="group" aria-label="行きと帰り">${summaryHTML(ts)}</div><div class="tp-target"><span class="tp-kicker">${out?'最初のイベント':'最後のイベント'}</span>${target?`<p><b>${esc(dateLabel(target.day))} ${clock(out?target.start:target.end)} ${out?'開始':'終了'}</b></p><h3>${esc(target.e?.title||target.x?.title)}</h3><p>${esc(target.venue?.name||'会場未確認')}</p>`:'<h3>まずはイベントをマイ予定に追加</h3><p>参加する時間が決まると、移動の候補と会場までの行程が表示されます。</p><a href="#explore" data-screen="explore">イベントを探す →</a>'}${ts.unresolved?`<p class="tp-alert">時刻・開催情報が未確定の${ts.unresolved}件は逆算に含めていません。マイ予定で確認してください。</p>`:''}</div><div class="tp-controls"><label class="tp-field"><span>${out?'出発エリア':'帰着エリア'}</span><select data-pref="city"><option value="tokyo" ${p.city==='tokyo'?'selected':''}>東京（羽田／東京駅）</option><option value="osaka" ${p.city==='osaka'?'selected':''}>大阪（伊丹／新大阪駅）</option></select></label>${field(out?'福岡へ移動する日':'福岡から帰る日','day',c.day,'date','min="2026-01-01" max="2026-12-31"')}<fieldset class="tp-mode"><legend>交通手段・福岡の玄関口</legend><div><button type="button" data-mode="air" aria-pressed="${p.mode==='air'}">✈ 飛行機<small>福岡空港</small></button><button type="button" data-mode="rail" aria-pressed="${p.mode==='rail'}">新幹線<small>博多駅</small></button></div></fieldset></div>${target&&p.day&&p.day!==target.day?`<p class="tp-note">${out?'前泊':'翌日以降の帰着'}も検討できます。<button type="button" data-reset-day>イベント当日に戻す</button></p>`:''}${routeHTML(c)}<details class="tp-settings" data-settings ${detailsOpen?'open':''}><summary>時間を調整する <span>荷物・乗り換え・受付の余裕</span></summary><div class="tp-settings-grid">${field(out?(p.mode==='air'?'降機・荷物受け取り（分）':'新幹線を降りて改札まで（分）'):(p.mode==='air'?'空港に出発何分前に着く？':'博多駅に出発何分前に着く？'),p.mode==='air'?'airBuffer':'railBuffer',c.buffer)}${field(out?'受付・開始前の余裕（分）':'終了後の余裕（分）','eventBuffer',p.eventBuffer)}${field('市内移動の合計を手入力（分）','manualCity',p.manualTarget===targetSig(target)?p.manualCity:null,'number','placeholder="空欄なら自動計算"')}</div><p class="tp-fine">市内移動の手入力は、地図で確認した徒歩・待ち時間・乗車時間の合計を入力。空港・駅での余裕は別に加算します。初期値は計画用の目安です。</p></details>${c.threshold!==null?`<div class="tp-deadline"><span>${out?c.terminal+'への到着リミット':c.terminal+'を出発できる目安'}</span><strong>${esc(at(c.threshold,c.day))}<small>${out?'まで':'以降'}</small></strong><p>${out?'開始から':'終了に'} 市内移動${c.route.minutes}分 ＋ ${p.mode==='air'?'空港':'駅'}で${c.buffer}分 ＋ イベント${out?'前':'後'}${p.eventBuffer}分 ${out?'を引いて計算':'を足して計算'}</p></div>`:''}${scheduleHTML(c)}${timelineHTML(c)}<p class="tp-storage" role="status">${storageOK?'条件と選んだ便は、この端末に自動保存されます。':'この端末には保存できませんでした。選択内容はこの画面を開いている間だけ保持されます。'}</p></div>`;
 if(focusKey)root.querySelector(`[data-pref="${focusKey}"]`)?.focus({preventScroll:true});
 lastSignature=JSON.stringify(ts);
}
function resetSelection(p){p.selected='';p.selectionDay='';p.selectionTarget='';}
function handleChange(e){
 const name=e.target.dataset.pref;if(!name)return;
 const p=prefs[active];
 if(name==='day'&&!validDay(e.target.value))return;
 if(name==='city'){p.city=e.target.value;resetSelection(p);}
 else if(name==='day'){p.day=e.target.value;resetSelection(p);}
 else {p[name]=number(e.target.value,name==='manualCity'?null:15,name==='manualCity'?1:0);if(name==='manualCity')p.manualTarget=targetSig(targets()[active]);}
 persist();showAll=false;render();
}
function handleClick(e){
 const b=e.target.closest('button');if(!b||!root.contains(b))return;
 if(b.dataset.tripTab){active=b.dataset.tripTab;showAll=false;render();root.querySelector(`[data-trip-tab="${active}"]`)?.focus({preventScroll:true});return;}
 const p=prefs[active];
 if(b.dataset.mode){p.mode=b.dataset.mode;p.manualCity=null;resetSelection(p);showAll=false;}
 else if(b.hasAttribute('data-show-all')){showAll=!showAll;render();root.querySelector('[data-show-all]')?.focus({preventScroll:true});return;}
 else if(b.dataset.selectService){const c=context(active),s=c.services.find(x=>x.id===b.dataset.selectService);if(!s||!assess(s,c).ok)return;p.selected=s.id;p.selectionDay=c.day;p.selectionTarget=targetSig(c.target);}
 else if(b.hasAttribute('data-clear-service'))resetSelection(p);
 else if(b.hasAttribute('data-reset-day')){p.day='';resetSelection(p);}
 else return;
 persist();render();
 if(b.dataset.selectService){root.querySelector('.tp-itinerary')?.scrollIntoView({behavior:'smooth',block:'nearest'});root.querySelector('[data-clear-service]')?.focus({preventScroll:true});}
}
function placeAfterPlanContent(planner){
 const content=document.querySelector('#plan-content')||document.querySelector('#plan-empty');
 if(content&&content.nextElementSibling!==planner)content.after(planner);
 return !!content;
}
function refresh(){cancelAnimationFrame(raf);raf=requestAnimationFrame(()=>{if(JSON.stringify(targets())!==lastSignature)render();});}
function mount(){
 if(root||!document.querySelector('#screen-plan'))return;
 root=document.createElement('section');root.id='access-planner';root.className='access-planner';root.setAttribute('aria-label','トリッププランナー');
 if(!placeAfterPlanContent(root))document.querySelector('#screen-plan').append(root);
 root.addEventListener('change',handleChange);root.addEventListener('click',handleClick);render();
 // Observe only the host's plan, never our own render output (prevents render loops).
 const observer=new MutationObserver(refresh);
 for(const id of ['plan-content','plan-empty']){const el=document.getElementById(id);if(el)observer.observe(el,{subtree:true,childList:true,characterData:true});}
 document.addEventListener('click',e=>{if(!root.contains(e.target))refresh();});
 window.addEventListener('storage',e=>{if(e.key===KEY){prefs=readPrefs();render();}else if(e.key==='ramen-guide-v3')refresh();});
}
// Small pure API for verifying timetable/connection arithmetic independently of the UI.
window.RamenTrip={services,targets,cityRoute,assess,minutes,clock,validDay,cleanPref};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
})();
