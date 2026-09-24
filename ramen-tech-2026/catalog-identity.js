'use strict';
(()=>{
  function canonicalId(events,id){
    const index=new Map(events.map(e=>[e.id,e])),seen=new Set();
    while(index.get(id)?.duplicateOf&&index.has(index.get(id).duplicateOf)&&!seen.has(id)){
      seen.add(id);id=index.get(id).duplicateOf;
    }
    return id;
  }
  function mergeModel(model,events){
    const result={...model,entries:{},mergedEntries:[...(model.mergedEntries||[])]};
    result.candidates=[...new Set((model.candidates||[]).map(id=>canonicalId(events,id)))];
    const rank={unknown:0,notrequired:1,pending:2,done:3};
    // Prefer the saved canonical entry when both old and current IDs were saved.
    const entries=Object.entries(model.entries||{}).sort((a,b)=>Number(canonicalId(events,a[1].id)!==a[1].id)-Number(canonicalId(events,b[1].id)!==b[1].id));
    for(const [oldKey,entry] of entries){
      const id=canonicalId(events,entry.id),key=id+'|'+entry.day;
      if(!result.entries[key])result.entries[key]={...entry,id};
      else {
        const saved=result.entries[key];
        if((rank[entry.registration]||0)>(rank[saved.registration]||0))saved.registration=entry.registration;
        const archived={key:oldKey,entry:{...entry}};
        if(!result.mergedEntries.some(x=>JSON.stringify(x)===JSON.stringify(archived)))result.mergedEntries.push(archived);
      }
    }
    return result;
  }
  const api={canonicalId,mergeModel};
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(typeof window==='object')window.RamenIdentity=api;
})();
