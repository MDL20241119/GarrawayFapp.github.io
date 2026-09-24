"""Connect the production v3 guide to the dated JSON snapshot after bundle assembly."""
import argparse, json, re
from pathlib import Path

def prepare(root):
    catalog = json.loads((root/'catalog.js').read_text().split('=',1)[1].strip().rstrip(';'))
    (root/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,separators=(',',':'))+'\n')
    version = re.sub(r'\D','',catalog['meta'].get('catalogVersion',''))[:14] or '20260924'
    js = (root/'guide.js').read_text()
    js = js.replace('const allDays=', 'let allDays=')
    js = js.replace('D.events.flatMap(e=>e.dates.filter(d=>matches(e,d))', 'D.events.filter(e=>!e.duplicateOf).flatMap(e=>e.dates.filter(d=>matches(e,d))')
    js = js.replace('時刻情報が不一致', '開催情報を要確認')
    js = js.replace('確認時刻：${esc(sourceDate)}', "公式データ取得：${esc(e.autoCheckedAt||'自動取得対象外')}<br>補足情報の個別確認：${esc(e.checkedAt||'未確認')}")
    js = js.replace("raw.candidates.filter(id=>typeof id==='string'&&EV.has(id))", "raw.candidates.filter(id=>typeof id==='string'&&EV.has(id)).map(id=>EV.get(id).duplicateOf||id)")
    js = js.replace('このガイドは配信時点の保存データを表示し、閲覧中に自動取得は行いません。', '公式登録・公式タイムテーブルを毎時確認し、閲覧中も5分ごとに配信データを確認します。取得・配信には時間差があります。')
    js = js.replace('このプレビューは保存データを使い、自動取得処理を実行しません。', '公式登録・公式タイムテーブルを毎時確認し、閲覧中も5分ごとに配信データを確認します。取得・配信には時間差があります。')
    old='D=next;window.RAMEN_CATALOG=next;rebuildIndexes();renderCurrent();'
    new="D=next;window.RAMEN_CATALOG=next;rebuildIndexes();allDays=[...new Set(D.events.filter(e=>!e.duplicateOf).flatMap(e=>e.dates))].sort();counts();renderCurrent();"
    if old not in js and new not in js:
        raise ValueError('Guide catalog integration changed; review before publishing')
    js=js.replace(old,new)
    (root/'guide.js').write_text(js)
    html=(root/'index.html').read_text()
    if 'live-data.js' not in html:
        html=html.replace('</head>','<link rel="stylesheet" href="live-data.css"><script src="sync-status.js" defer></script><script src="live-data.js" defer></script></head>')
    for name in ['catalog.js','guide.js','sync-status.js','live-data.js','live-data.css']:
        html=re.sub(re.escape(name)+r'(?:\?v=[^"\s]+)?',name+'?v='+version,html)
    (root/'index.html').write_text(html)
    assert 'live-data.js?v=' in html and 'filter(e=>!e.duplicateOf).flatMap' in js

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--site',required=True);args=parser.parse_args();prepare(Path(args.site))
