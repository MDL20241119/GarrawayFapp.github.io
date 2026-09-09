"""Check the actual served files and browser behavior after each refresh."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.request
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='https://mobilitydlab.com/GarrawayFapp.github.io/ramen-tech-2026/')
parser.add_argument('--attempts', type=int, default=24)
parser.add_argument('--out', default='ramen-daily-verification')
args = parser.parse_args()
root = Path('ramen-tech-2026')
out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
status = json.loads((root / 'sync-status.json').read_text())
catalog = json.loads((root / 'catalog.js').read_text().split('=', 1)[1].strip().rstrip(';'))
files = ['index.html', 'app.js', 'catalog.js', 'sync-status.json', 'sync-status.js', 'auto-update.js', 'auto-update.css', 'assets/tonkotsu.svg']
report = {'url': args.url, 'attemptedAt': status['attemptedAt'], 'status': status['status'], 'checks': [], 'errors': []}
for attempt in range(args.attempts):
    try:
        for name in files:
            request = urllib.request.Request(args.url + name + '?verify=' + str(time.time_ns()), headers={'User-Agent': 'RAMEN guide publication verifier', 'Cache-Control': 'no-cache'})
            with urllib.request.urlopen(request, timeout=25) as response:
                actual = response.read()
            assert actual == (root / name).read_bytes(), 'Published file differs: ' + name
        break
    except Exception as exc:
        print('Publication check:', str(exc), flush=True)
        if attempt == args.attempts - 1:
            raise
        time.sleep(10)
report['checks'].append('All eight served files match the updated repository files')
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 390, 'height': 1000}, reduced_motion='reduce', accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(15000)
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        page.goto(args.url + '?date=any', wait_until='networkidle')
        page.wait_for_function('!!window.RamenGuide && !!window.RAMEN_SYNC_STATUS')
        assert page.evaluate('RAMEN_CATALOG.events.length') == len(catalog['events'])
        assert page.locator('#stat-venues').inner_text() == str(catalog['meta']['venueCount'])
        assert page.locator('.mascot-disclaimer').inner_text() == '非公式キャラ'
        assert page.locator('#auto-update').is_visible()
        assert page.evaluate('RAMEN_SYNC_STATUS.attemptedAt') == status['attemptedAt']
        if status['status'] == 'success':
            assert page.locator('#auto-health').inner_text() == '公式データ取得済み'
        report['checks'].append('Catalog counts, actual check time, status panel and unofficial mascot label')
        for q in ['ＡＩ', 'ギャラウェイ', '交流 天神']:
            page.locator('#search').fill(q)
            page.wait_for_timeout(350)
            assert page.evaluate('RamenGuide.filtered().length') > 0, q
        report['checks'].append('Full-width, venue alias and multi-keyword searches')
        page.evaluate('RamenGuide.reset(); RamenGuide.change({venue:"garraway",day:"7",known:true})')
        page.locator('.save-button').first.click()
        assert page.locator('#saved-count').inner_text() == '1'
        page.reload(wait_until='networkidle')
        assert page.locator('#saved-count').inner_text() == '1'
        report['checks'].append('Saved plans survive reload after the data refresh')
        for width in [320, 390, 768, 1440]:
            page.set_viewport_size({'width': width, 'height': 1000})
            page.wait_for_timeout(100)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Overflow: ' + str(width)
            page.locator('#auto-update').scroll_into_view_if_needed()
            page.screenshot(path=str(out / ('update-' + str(width) + '.png')))
        report['checks'].append('No horizontal overflow at 320, 390, 768 and 1440px')
        assert not report['errors'], report['errors']
        browser.close()
finally:
    report['verifiedAtUTC'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    report['catalogSHA256'] = hashlib.sha256((root / 'catalog.js').read_bytes()).hexdigest()
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
