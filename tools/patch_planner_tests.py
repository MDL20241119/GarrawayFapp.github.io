"""Keep browser fixtures aligned with real date-specific official time slots."""
from pathlib import Path
p=Path('tools/ramen_verify_planner.py')
s=p.read_text()
old="        assert page.evaluate('RamenPlanner.itinerary(\"2026-10-06\").unresolved.length')==1\n"
new="""        assert page.evaluate('RamenPlanner.itinerary("2026-10-06").ordered.length')==1
        report['checks'].append('Date-specific source slots override empty event-level start/end values')
        unknown=page.evaluate('RAMEN_CATALOG.events.filter(e=>e.dates.length>1).flatMap(e=>e.dates.map(day=>({id:e.id,day}))).find(x=>!RamenGuide.canCalendar(RAMEN_CATALOG.events.find(e=>e.id===x.id),x.day))')
        assert unknown is not None, 'A genuine unknown-time fixture must exist'
        page.evaluate('(x)=>RamenPlanner.toggle(x.id,x.day)',unknown)
        assert page.evaluate('(x)=>RamenPlanner.itinerary(x.day).unresolved.some(r=>r.e.id===x.id)',unknown)
        page.evaluate('(x)=>RamenPlanner.remove(x.id+"|"+x.day)',unknown)
"""
if old in s:s=s.replace(old,new,1)
elif new not in s:raise RuntimeError('Unexpected browser test structure')
p.write_text(s)
