'use strict';
(async()=>{
const {default:assert}=await import('node:assert/strict');
const fs=await import('node:fs'), path=await import('node:path'), vm=await import('node:vm');
const testModule={exports:{}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../live-data.js'),'utf8'),{module:testModule});
const {healthFor,validatePair}=testModule.exports;
const now=Date.parse('2026-09-24T12:00:00+09:00');
assert.equal(healthFor({status:'success',lastSuccessAt:'2026-09-24T11:00:00+09:00'},now),'公式データ取得済み');
assert.equal(healthFor({status:'success',lastSuccessAt:'2026-09-23T05:00:00+09:00'},now),'更新が遅れています');
assert.equal(healthFor({status:'partial',lastSuccessAt:'2026-09-24T11:00:00+09:00'},now),'一部の取得に失敗');
assert.equal(healthFor({status:'success'},now),'確認記録なし');
assert.equal(healthFor({status:'success',lastSuccessAt:'2027-01-01'},now),'確認記録なし');
assert.equal(healthFor({status:'success',lastSuccessAt:'2026-09-23T06:00:00+09:00'},now),'公式データ取得済み');
const raw=fs.readFileSync(path.join(__dirname,'../catalog.js'),'utf8');
const catalog=JSON.parse(raw.slice(raw.indexOf('=')+1).trim().replace(/;$/,''));
const s={catalogVersion:catalog.meta.catalogVersion};
assert.equal(validatePair(s,catalog),catalog);
assert.throws(()=>validatePair({...s,catalogVersion:'different'},catalog));
const duplicate=structuredClone(catalog);duplicate.events.push(duplicate.events[0]);assert.throws(()=>validatePair(s,duplicate));
const bad=structuredClone(catalog);bad.events[0].venue='missing';assert.throws(()=>validatePair(s,bad));
console.log('Freshness, failed/partial sources, publication race and invalid catalog checks passed');
const identityModule={exports:{}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../catalog-identity.js'),'utf8'),{module:identityModule});
const {mergeModel}=identityModule.exports;
const identities=[{id:'old',duplicateOf:'current'},{id:'current'}];
const model={candidates:['old','current'],entries:{
  'old|2026-10-07':{id:'old',day:'2026-10-07',start:'10:15',registration:'done',snapshot:'old'},
  'current|2026-10-07':{id:'current',day:'2026-10-07',start:'10:30',registration:'unknown',snapshot:'current'},
  'old|2026-10-08':{id:'old',day:'2026-10-08',start:'11:00',registration:'pending'},
  'missing|2026-10-08':{id:'missing',day:'2026-10-08',start:'12:00'}
}};
const merged=mergeModel(model,identities);
assert.equal(Object.keys(merged.entries).length,3);
assert.equal(merged.entries['current|2026-10-07'].start,'10:30');
assert.equal(merged.entries['current|2026-10-07'].registration,'done');
assert.equal(merged.entries['current|2026-10-08'].start,'11:00');
assert.equal(merged.candidates.join(','),'current');
assert.equal(merged.mergedEntries[0].entry.start,'10:15');
assert.equal(model.entries['old|2026-10-07'].id,'old');
assert.equal(JSON.stringify(mergeModel(merged,identities)),JSON.stringify(merged));
console.log('Saved duplicates merge without losing registration, separate dates, unknown IDs or original records');

})().catch(error=>{console.error(error);process.exitCode=1;});
