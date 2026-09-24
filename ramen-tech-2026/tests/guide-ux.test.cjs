'use strict';
// Exercise the assembled controller, real catalog and DOM event handlers without a browser.
(async()=>{
const assert=(await import('node:assert/strict')).default,fs=await import('node:fs'),path=await import('node:path'),vm=await import('node:vm');
const root=path.resolve(process.argv[2]||path.join(__dirname,'..'));
const elements=new Map(),listeners=new Map(),stored=new Map();
function el(id){if(!elements.has(id))elements.set(id,{innerHTML:'',textContent:'',value:'',hidden:false,open:false,dataset:{},classList:{add(){},remove(){}},setAttribute(){},removeAttribute(){},addEventListener(){},scrollIntoView(){},focus(){},querySelector(){return el('nested')},querySelectorAll(){return []},showModal(){this.open=true},close(){this.open=false}});return elements.get(id);}
const doc={querySelector:el,querySelectorAll:()=>[],addEventListener:(name,fn)=>listeners.set(name,fn),title:''};
const context={console,URL,URLSearchParams,Intl,Date,Map,Set,Math,JSON,Number,Array,String,Object,RegExp,structuredClone,document:doc,location:{search:'?ui-test=1&date=2026-10-08',hash:'#explore',href:'https://example.test/?ui-test=1&date=2026-10-08#explore'},history:{replaceState(a,b,url){context.location.href=String(url)}},localStorage:{getItem:key=>stored.get(key)||null,setItem:(key,value)=>stored.set(key,value)},setTimeout:()=>1,clearTimeout(){},setInterval(){},requestAnimationFrame:fn=>fn(),matchMedia:()=>({matches:true})};
context.window={GUIDE_CONFIG:{preview:false},addEventListener(){},scrollTo(){},scrollY:0};
vm.createContext(context);
for(const name of ['catalog.js','catalog-identity.js','guide.js'])vm.runInContext(fs.readFileSync(path.join(root,name),'utf8'),context,{filename:name});
const app=context.window.GuideApp;
function click(dataset){listeners.get('click')({target:{closest:()=>({dataset})},preventDefault(){}});}
const data=app.getData(),event=data.events.find(e=>!e.duplicateOf&&e.dates.includes('2026-10-08')&&e.fee?.includes('要参加登録')&&app.knownTime(e,'2026-10-08'));
assert(event,'known event requiring registration exists');
click({quick:'period:afternoon'});
assert.equal(app.getFilters().period,'afternoon');
assert.match(el('#filter-summary').textContent,/10\/8.*午後/);
assert(app.occurrences().length>1);
click({quick:'fee:free'});
assert(app.occurrences().every(r=>r.e.fee.includes('無料')||r.childMatch));
assert.match(el('#event-list').innerHTML,/data-fee>無料/);
assert.match(el('#event-list').innerHTML,/data-registration-condition/);
click({clearFilter:'fee'});assert.equal(app.getFilters().fee,'all');
click({candidate:event.id});assert(app.getState().candidates.includes(event.id));
assert.equal(Object.keys(app.getState().entries).length,0,'candidate is not a plan entry');
click({add:event.id,day:'2026-10-08'});
let state=app.getState();assert.equal(Object.keys(state.entries).length,1);
assert.equal(Object.values(state.entries)[0].registration,'unknown','adding is not registering');
assert.match(el('#toast').innerHTML,/主催者サイトでの申込が必要/);
assert.match(el('#toast').innerHTML,/マイ予定を見る/);
click({action:'undo'});assert.equal(Object.keys(app.getState().entries).length,0);
assert(app.getState().candidates.includes(event.id),'undo addition preserves candidate');
const alias=data.events.find(e=>e.duplicateOf&&e.dates.includes('2026-10-08'));
if(alias){app.add(alias.id,'2026-10-08');assert(Object.values(app.getState().entries).every(x=>x.id!==alias.id));}
assert(!app.occurrences().some(r=>r.e.duplicateOf),'aliases never become extra cards');
const day='2026-10-08';
const known=data.events.filter(e=>!e.duplicateOf&&e.dates.includes(day)&&app.knownTime(e,day)&&!['check','soldout'].includes(e.status));
const toMinute=t=>Number(t.slice(0,2))*60+Number(t.slice(3));
let pair;
for(const a of known)for(const b of known){const ae=(a.slots?.[day]||[a.start,a.end])[1],bs=(b.slots?.[day]||[b.start,b.end])[0];if(a.venue===b.venue&&toMinute(bs)-toMinute(ae)>=60)pair=[a,b];}
assert(pair,'two real events leave a same-venue gap');
const plan=app.getState();plan.entries={};
for(const e of pair)plan.entries[e.id+'|'+day]={id:e.id,day,title:e.title,venue:e.venue,start:'',end:'',snapshot:app.signature(e,day),reviewed:'',registration:'unknown',partialConfirmed:false};
app.migratePreview(plan);
const itinerary=app.itinerary(day);assert(itinerary.gaps.length);assert.equal(itinerary.issues.length,0);
click({searchGap:itinerary.gaps[0].key});
assert.equal(app.getFilters().day,day);assert(app.getFilters().from);assert(app.getFilters().until);
assert.equal(app.getFilters().fee,'all','gap search does not inherit unrelated old filters');
assert.match(el('#filter-summary').textContent,/以降.*まで/);
const bad=app.getState();Object.values(bad.entries)[0].end='00:01';Object.values(bad.entries)[0].partialConfirmed=true;app.migratePreview(bad);
click({action:'export'});
assert.match(el('#export-summary').innerHTML,/保存前に、1件確認/);
assert.match(el('#export-summary').innerHTML,/この予定を確認する/);
assert.match(el('#export-summary').innerHTML,new RegExp(pair[0].title.replace(/[.*+?^${}()|[\]\\]/g,'\\$&').slice(0,20)));
assert.equal(app.exportICS(),false,'unresolved times still block calendar export');
assert(stored.has('ramen-guide-ui-test-v3'));
assert(!stored.has('ramen-guide-v3'),'test storage remains isolated');
assert.match(context.location.href,/ui-test=1/,'test navigation remains isolated after reload');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
assert(html.indexOf('guide-ux.css')>html.indexOf('live-data.css'),'interface styles load last');
assert.match(html,/classic-ui\.js\?v=20260912k4-/);
for(const id of ['filter-summary','time-context','context-garraway','candidate-toggle','event-list'])assert(html.includes('id="'+id+'"'));
console.log('Controller checks passed: filters, grouping, candidates, registration, undo, alias migration and isolated test navigation.');

})().catch(error=>{console.error(error);process.exitCode=1;});
