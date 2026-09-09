"""Browser verification of the actual scheduler, travel assumptions and homepage entrance."""
import argparse,json,time,threading,functools
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base');parser.add_argument('--output',default='planner-verification');args=parser.parse_args()
    out=Path(args.output);out.mkdir(exist_ok=True);report={'checks':[],'errors':[]}
    server=None
    if args.base:base=args.base.rstrip('/')+'/'
    else:
        class Handler(SimpleHTTPRequestHandler):
            def log_message(self,*args):pass
            def translate_path(self,path):
                if path.startswith('/GarrawayFapp.github.io/'):path=path[len('/GarrawayFapp.github.io'):]
                return super().translate_path(path)
        server=ThreadingHTTPServer(('127.0.0.1',8765),functools.partial(Handler,directory=str(Path.cwd())))
        threading.Thread(target=server.serve_forever,daemon=True).start();base='http://127.0.0.1:8765/GarrawayFapp.github.io/'
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True);context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce',accept_downloads=True);page=context.new_page();page.set_default_timeout(20000)
        page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(base,wait_until='networkidle');page.wait_for_selector('#gf-ramen-special');page.wait_for_timeout(1000)
        assert page.locator('#gf-ramen-special').count()==1
        assert 'ramen-tech-2026/' in page.locator('#gf-ramen-special .gf-special-links a').first.get_attribute('href')
        assert page.locator('.gf-ramen-nav').count()==1
        page.locator('#gf-ramen-special').scroll_into_view_if_needed();page.screenshot(path=str(out/'homepage-1440.png'))
        report['checks'].append('Homepage special-site banner and nav; original Next page remains interactive')
        page.goto(base+'ramen-tech-2026/',wait_until='networkidle');page.wait_for_function('!!window.RamenPlanner')
        assert page.locator('.mascot-disclaimer').inner_text()=='非公式キャラ'
        assert page.locator('#garraway-highlights article').count()==6
        assert page.locator('#garraway-feature-count').inner_text()==str(page.evaluate('RAMEN_CATALOG.events.filter(e=>e.venue==="garraway").length'))
        for q in ['ＡＩ','ギャラウェイ','交流 天神']:
            page.locator('#search').fill(q);page.wait_for_timeout(220);assert page.evaluate('RamenGuide.filtered().length')>0
        page.evaluate('RamenGuide.reset()')
        page.locator('[data-plan-add="coffee-7"]').first.click()
        page.evaluate('RamenGuide.change({venue:"one6",day:"7"})')
        page.locator('[data-plan-add="event-lab-to-impact-gx-vol4-in"]').first.click()
        form=page.locator('form[data-visit="event-lab-to-impact-gx-vol4-in|2026-10-07"]')
        form.locator('..').locator('summary').click();form.locator('[name=start]').fill('12:30');form.locator('[name=end]').fill('13:30');form.locator('[type=submit]').click()
        page.locator('[data-plan-add="welcome-7"]').first.click()
        assert page.evaluate('RamenPlanner.itinerary("2026-10-07").ordered.length')==3
        assert page.evaluate('RamenPlanner.itinerary("2026-10-07").legs.length')==2
        assert page.evaluate('RamenPlanner.itinerary("2026-10-07").warnings.length')==0
        assert page.evaluate('RamenPlanner.itinerary("2026-10-07").legs.every(l=>l.duration>0&&l.available>=0)')
        report['checks'].append('Selecting days builds ordered event, inter-venue walking, arrival, buffer and free-time blocks')
        with page.expect_download() as download:page.locator('[data-plan-export]').click()
        download.value.save_as(str(out/'selected-day-with-travel.ics'))
        text=(out/'selected-day-with-travel.ics').read_text();assert text.count('BEGIN:VEVENT')==7
        assert 'STATUS:TENTATIVE' in text and '徒歩・目安' in text
        report['checks'].append('ICS contains 3 selected events, 2 travel blocks and 2 buffer blocks in JST-converted UTC')
        page.locator('[data-leg-mode]').first.select_option('transit')
        assert page.evaluate('RamenPlanner.itinerary("2026-10-07").unknown')==1
        page.locator('[data-leg-minutes]').first.fill('18');page.locator('[data-leg-minutes]').first.dispatch_event('change')
        assert page.evaluate('RamenPlanner.itinerary("2026-10-07").legs[0].manual')
        assert page.evaluate('RamenPlanner.itinerary("2026-10-07").legs[0].duration')==18
        page.reload(wait_until='networkidle');page.wait_for_function('!!window.RamenPlanner')
        assert page.evaluate('Object.keys(RamenPlanner.model.entries).length')==3
        assert page.evaluate('RamenPlanner.itinerary("2026-10-07").legs[0].duration')==18
        assert page.evaluate('RamenPlanner.model.entries["event-lab-to-impact-gx-vol4-in|2026-10-07"].start')=='12:30'
        report['checks'].append('Partial participation and manual transit time persist after HTTPS reload; no fabricated transit estimate')
        page.locator('[data-leg-minutes]').first.fill('80');page.locator('[data-leg-minutes]').first.dispatch_event('change')
        assert page.evaluate('RamenPlanner.itinerary("2026-10-07").legs[0].available')<0
        assert page.locator('#plan-alert').is_visible()
        page.locator('[data-plan-export]').click();assert '確認' in page.locator('#toast').inner_text()
        report['checks'].append('Impossible connection warns and stops calendar export')
        page.locator('[data-leg-mode]').first.select_option('walking')
        page.evaluate('RamenPlanner.toggle("event-global-women-impact-x-colive-fukuok","2026-10-06")')
        assert page.evaluate('Object.keys(RamenPlanner.model.entries).filter(k=>k.startsWith("event-global-women")).length')==1
        assert page.evaluate('RamenPlanner.itinerary("2026-10-06").ordered.length')==1
        report['checks'].append('Date-specific source slots override empty event-level start/end values')
        unknown=page.evaluate('RAMEN_CATALOG.events.filter(e=>e.dates.length>1).flatMap(e=>e.dates.map(day=>({id:e.id,day}))).find(x=>!RamenGuide.canCalendar(RAMEN_CATALOG.events.find(e=>e.id===x.id),x.day))')
        assert unknown is not None, 'A genuine unknown-time fixture must exist'
        page.evaluate('(x)=>RamenPlanner.toggle(x.id,x.day)',unknown)
        assert page.evaluate('(x)=>RamenPlanner.itinerary(x.day).unresolved.some(r=>r.e.id===x.id)',unknown)
        page.evaluate('(x)=>RamenPlanner.remove(x.id+"|"+x.day)',unknown)
        page.evaluate('RamenPlanner.remove("event-global-women-impact-x-colive-fukuok|2026-10-06")')
        report['checks'].append('Multi-day event selects only the chosen date; unpublished times are kept outside timed itinerary')
        page.evaluate('RAMEN_CATALOG.events.find(e=>e.id==="coffee-7").title+="（変更テスト）";RamenPlanner.open()')
        assert page.evaluate('RamenPlanner.itinerary("2026-10-07").all.some(r=>r.changed)')
        page.locator('[data-plan-ack="coffee-7|2026-10-07"]').click()
        assert not page.evaluate('RamenPlanner.itinerary("2026-10-07").all.find(r=>r.e.id==="coffee-7").changed')
        page.evaluate('RAMEN_CATALOG.events.find(e=>e.id==="coffee-7").title=RAMEN_CATALOG.events.find(e=>e.id==="coffee-7").title.replace("（変更テスト）","");RamenPlanner.open()')
        page.locator('[data-plan-ack="coffee-7|2026-10-07"]').click()
        report['checks'].append('Source changes are detected and require user acknowledgement')
        for width in [320,390,768,1440]:
            page.set_viewport_size({'width':width,'height':1000});page.wait_for_timeout(120)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),width
            page.evaluate('scrollTo({top:document.querySelector("#garraway-featured").offsetTop-80,behavior:"instant"})');page.wait_for_timeout(120);page.screenshot(path=str(out/f'featured-{width}.png'))
            page.evaluate('scrollTo({top:document.querySelector("#planner").offsetTop-80,behavior:"instant"})');page.wait_for_timeout(120);page.screenshot(path=str(out/f'planner-{width}.png'))
            page.locator('#plan-timeline').screenshot(path=str(out/f'timeline-{width}.png'))
            assert page.locator('.planner-dock').is_hidden()
        report['checks'].append('320/390/768/1440px layouts, in-planner dock hidden, no document overflow')
        page.locator('[data-plan-view="table"]').click();assert page.locator('#plan-table-view').is_visible()
        assert page.locator('#plan-table-body tr').count()==5
        page.locator('[data-plan-view="timeline"]').click()
        page.evaluate('document.body.classList.add("printing-plan")');page.emulate_media(media='print')
        assert page.locator('#planner').is_visible() and not page.locator('.hero').is_visible()
        page.emulate_media(media='screen');page.evaluate('document.body.classList.remove("printing-plan")')
        report['checks'].append('Timetable view and planner-only printing')
        assert not report['errors'],report['errors']
        browser.close()
    if server:server.shutdown()
    report['base']=base;report['result']='success';(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
