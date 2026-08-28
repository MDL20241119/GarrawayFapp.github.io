from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / 'index.html', ROOT / 'site-v5.css', ROOT / 'site-v5.js',
    ROOT / 'data' / 'instagram.json', ROOT / 'assets' / 'floor-map.svg'
]
errors: list[str] = []
for path in required:
    if not path.exists() or path.stat().st_size == 0:
        errors.append(f'Missing or empty: {path.relative_to(ROOT)}')

if not errors:
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    count = len(re.findall(r'class="futurist-card"', html))
    if count != 23:
        errors.append(f'Expected 23 futurists, found {count}')
    checks = {
        'Instagram live container': 'id="instagram-live"',
        'Facebook Page Plugin': 'facebook.com/plugins/page.php',
        'Google Maps iframe': 'google.com/maps?q=',
        'LINE registration': 'line.me/R/ti/p/@446zsnzx',
        'Floor map asset': 'assets/floor-map.svg',
        'Mobile menu': 'class="menu-toggle"',
    }
    for label, needle in checks.items():
        if needle not in html:
            errors.append(f'Missing {label}')
    data = json.loads((ROOT / 'data' / 'instagram.json').read_text(encoding='utf-8'))
    posts = data.get('posts', []) if isinstance(data, dict) else []
    if len(posts) < 6:
        errors.append(f'Instagram JSON must contain >=6 posts, found {len(posts)}')

if errors:
    print('SITE VALIDATION FAILED')
    for error in errors:
        print(f'- {error}')
    raise SystemExit(1)

print('SITE VALIDATION PASSED')
print('- Futurists: 23')
print('- Instagram latest 6: OK')
print('- Facebook EVENT: OK')
print('- Google Maps: OK')
print('- Floor map: OK')
print('- LINE / mobile navigation: OK')
