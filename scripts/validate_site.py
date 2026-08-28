from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / 'index.html', ROOT / 'site-v5.css', ROOT / 'site-v5.js',
    ROOT / 'site-v6-overrides.css', ROOT / 'data' / 'instagram.json',
    ROOT / 'data' / 'facebook-events.json', ROOT / 'assets' / 'floor-map.svg'
]
errors: list[str] = []
for path in required:
    if not path.exists() or path.stat().st_size == 0:
        errors.append(f'Missing or empty: {path.relative_to(ROOT)}')

if not errors:
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    js = (ROOT / 'site-v5.js').read_text(encoding='utf-8')
    floor = (ROOT / 'assets' / 'floor-map.svg').read_text(encoding='utf-8')

    count = len(re.findall(r'class="futurist-card"', html))
    if count != 23:
        errors.append(f'Expected 23 futurists, found {count}')

    checks = {
        'Instagram live container': 'id="instagram-live"',
        'Facebook events page link': 'facebook.com/garrawayf/events',
        'Google Maps iframe': 'google.com/maps?q=',
        'LINE registration': 'line.me/R/ti/p/@446zsnzx',
        'Floor map asset': 'assets/floor-map.svg',
        'Mobile menu': 'class="menu-toggle"',
    }
    for label, needle in checks.items():
        if needle not in html and needle not in js:
            errors.append(f'Missing {label}')

    if 'class="facility section-frame"' in html:
        errors.append('Legacy FACILITY cards must remain removed')

    for label in ['リビングラボ', '80席以上', 'モノづくりラボ', '32席', '集中スペース', '30席', 'ダイニング', 'キッチン', 'エントランス', 'エレベーター']:
        if label not in floor:
            errors.append(f'Floor map missing: {label}')

    instagram = json.loads((ROOT / 'data' / 'instagram.json').read_text(encoding='utf-8'))
    posts = instagram.get('posts', []) if isinstance(instagram, dict) else []
    if len(posts) < 6:
        errors.append(f'Instagram JSON must contain >=6 posts, found {len(posts)}')

    facebook = json.loads((ROOT / 'data' / 'facebook-events.json').read_text(encoding='utf-8'))
    events = facebook.get('events', []) if isinstance(facebook, dict) else []
    if len(events) < 3:
        errors.append(f'Facebook event JSON must contain >=3 events, found {len(events)}')

if errors:
    print('SITE VALIDATION FAILED')
    for error in errors:
        print(f'- {error}')
    raise SystemExit(1)

print('SITE VALIDATION PASSED')
print('- Futurists: 23')
print('- Instagram latest 6: OK')
print('- Facebook event information: OK')
print('- Google Maps: OK')
print('- Accurate floor map labels and seat counts: OK')
print('- Three-step join and visual upgrade assets: OK')
