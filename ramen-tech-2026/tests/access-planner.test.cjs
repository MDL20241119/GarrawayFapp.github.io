(async()=>{
const {default:fs}=await import('node:fs'),{default:vm}=await import('node:vm'),{default:assert}=await import('node:assert/strict'),{join}=await import('node:path');
const window={};for(const file of ['flight-data.js','flight-monthly.js'])vm.runInNewContext(fs.readFileSync(join(__dirname,'../'+file),'utf8'),{window});vm.runInNewContext(fs.readFileSync(join(__dirname,'../access-planner.js'),'utf8'),{window,document:{readyState:'loading',addEventListener(){}},localStorage:{getItem(){throw new Error('blocked')}},URLSearchParams,Date,Math,Number,JSON});
const t=window.RamenTrip;let count=0;
for(const city of ['tokyo','osaka'])for(const mode of ['air','rail'])for(const kind of ['outbound','return']){
 const list=t.services(city,mode,kind,'2026-10-07');assert.ok(list.length>=7);assert.equal(new Set(list.map(s=>s.id)).size,list.length);
 for(const s of list){assert.ok(t.minutes(s.arr)>t.minutes(s.dep),s.id);assert.ok(s.operator);count++;}
 assert.equal(t.services(city,mode,kind,'2026-10-25').length,0);
}
assert.equal(t.validDay('2026-02-30'),false);assert.equal(t.minutes('24:05'),null);
assert.equal(t.cleanPref({city:'garbage',mode:'garbage',eventBuffer:0},'outbound').eventBuffer,0);
assert.equal(t.cleanPref(null,'return').airBuffer,60);
const venue={id:'garraway',name:'Garraway F',geo:{status:'located',lat:33.5861432,lng:130.3977762}};
for(const mode of ['air','rail']){
 const out=t.cityRoute(venue,mode,'outbound'),back=t.cityRoute(venue,mode,'return');assert.equal(out.minutes,back.minutes);assert.equal(out.steps.length,3);assert.equal(out.station,'天神駅');
}
assert.equal(t.cityRoute({name:'会場未定'},'air','outbound').minutes,null);
assert.equal(t.cityRoute({name:'会場未定'},'air','outbound',47).minutes,47);
const route=t.cityRoute(venue,'air','outbound');
const c={threshold:600-route.minutes-25-15,kind:'outbound',route,buffer:25,p:{mode:'air'}};
assert.equal(t.assess({dep:'06:45',arr:'08:35'},c).ok,true);
assert.equal(t.assess({dep:'07:30',arr:'09:25'},c).ok,false);
const back={threshold:1200+route.minutes+60+15,kind:'return',route,buffer:60,p:{mode:'air'}};
assert.equal(t.services('tokyo','air','return','2026-10-07').filter(s=>t.assess(s,back).ok).length,0);
assert.equal(t.assess({dep:'07:00',arr:'08:40'},{...back,threshold:-60}).night,true);
const event=(key,day,start,end,invalid=false)=>({key,day,start,end,invalid,e:{title:key,status:'published'}});
const dates={'2026-10-07':[event('first','2026-10-07',600,700),event('long','2026-10-07',500,1300)],'2026-10-09':[event('unknown','2026-10-09',500,1400,true),event('last','2026-10-09',600,900)]};
const app={getState:()=>({entries:{a:{day:'2026-10-09'},b:{day:'2026-10-07'}}}),itinerary:day=>({rows:dates[day]})};
const targets=t.targets(app);assert.equal(targets.outbound.key,'long');assert.equal(targets.return.key,'last');assert.equal(targets.unresolved,1);
const sameday={getState:()=>({entries:{a:{day:'2026-10-07'}}}),itinerary:()=>({rows:dates['2026-10-07']})};assert.equal(t.targets(sameday).return.key,'long');
const corrected=t.services('osaka','rail','return','2026-10-07').find(s=>s.name==='ひかり682号');assert.equal(corrected.dep,'20:52');
assert.equal(t.services('osaka','rail','outbound','2026-10-07').find(s=>s.name==='さくら741号').dep,'06:25');
// Both endpoints and exact October adjustments are checked against the official sources.
const hnd=t.services('tokyo','air','outbound','2026-10-07','HND');
assert.equal(hnd.length,56);assert.equal(hnd.find(s=>s.name==='JAL 303').arr,'08:15');
assert.equal(hnd.find(s=>s.name==='JAL 335').dep,'19:30');
const itm=t.services('osaka','air','outbound','2026-10-07','ITM');
assert.equal(itm.length,11);assert.equal(itm.find(s=>s.name==='JAL 2051').dep,'07:20');assert.equal(itm.find(s=>s.name==='JAL 2051').arr,'08:30');
assert.equal(itm.find(s=>s.name==='JAL 2053').arr,'10:55');
const narita=day=>t.services('tokyo','air','outbound',day,'NRT');
assert.equal(narita('2026-10-07').find(s=>s.name==='MM 359').dep,'12:50');
assert.equal(narita('2026-10-08').find(s=>s.name==='MM 359').dep,'12:40');
assert.ok(t.services('tokyo','air','outbound','2026-10-07','CTS').some(s=>s.name==='SKY 774'));
assert.ok(!t.services('tokyo','air','outbound','2026-10-08','CTS').some(s=>s.name==='SKY 774'));
assert.ok(t.services('tokyo','air','outbound','2026-10-08','CTS').some(s=>s.name==='SKY 772'));
assert.ok(!t.services('tokyo','air','outbound','2026-10-02','NKM').some(s=>s.name==='JAL 4393'));
assert.ok(t.services('tokyo','air','outbound','2026-10-07','NKM').some(s=>s.name==='JAL 4393'));
for(let date=1;date<=24;date++)for(const kind of ['outbound','return']){
 const all=t.services('tokyo','air',kind,'2026-10-'+String(date).padStart(2,'0'),'ALL');
 assert.equal(new Set(all.map(s=>s.id)).size,all.length,'No duplicate physical flight on the same date');
 for(const s of all)assert.ok(t.minutes(s.dep)<t.minutes(s.arr),s.id);
}
const sep=t.services('tokyo','air','outbound','2026-09-12','ALL');
assert.equal(Object.keys(window.RamenFlightData.airports).length,53);
assert.ok(sep.some(s=>s.carrier==='GK'));assert.ok(sep.some(s=>s.carrier==='JAL'));
const overnight=sep.find(s=>s.airport==='KUL'&&s.depDiff==='前日');assert.ok(overnight);assert.equal(t.assess(overnight,{threshold:600}).ok,false);
assert.equal(t.services('tokyo','air','outbound','2026-10-07','ICN').length,0,'No September data used for October');
assert.equal(t.services('tokyo','air','outbound','2026-09-11','HND').length,0,'No unsupported date extrapolation');
const shared=t.services('tokyo','air','outbound','2026-10-07','AXJ').find(s=>(s.shares||[]).some(x=>x.carrier==='JAL'));
assert.ok(shared);assert.ok(t.flightMatches(shared,'JAL'));assert.ok(t.flightMatches(shared,'ANA'));
assert.equal(t.services('tokyo','air','outbound','2026-10-01','AXJ').length,1,'Physical flight cancellation applies to all codeshares');
const railContext={p:{mode:'rail',city:'osaka'},kind:'outbound',origin:'新大阪駅',terminal:'博多駅'};
assert.equal(t.endpoints(railContext).from,'新大阪駅');assert.equal(t.endpoints(railContext).to,'博多駅');
console.log(`PASS: ${count} timetable rows, airport/rail routes, multi-day event selection, connection limits, late-night transfer, unknown venues, dates and corrupt storage.`);

})().catch(error=>{console.error(error);process.exitCode=1;});
