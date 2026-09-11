"""Render the editorial page from checked event records. No live scraping at runtime."""
import html
import json
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent
events = json.loads((ROOT / 'events.json').read_text())
e = lambda value: html.escape(str(value), quote=True)
by_id = {item['id']: item for item in events}
assert len(by_id) == len(events)
for item in events:
    assert item['start'] <= item['end'] and item['start'] <= '2026-10-21' and item['end'] >= '2026-09-21'
    for key in ['source', 'image']:
        assert item.get(key), (item['id'], key)
    item['map'] = 'https://www.google.com/maps/search/?' + urlencode({'api': '1', 'query': item['mapQuery']})
    asset = ROOT / item['image']['url']
    assert item['image']['url'].startswith('images/') and asset.is_file()
    content = asset.read_bytes()
    assert len(content) > 100 and content[:4] == b'RIFF' and content[8:12] == b'WEBP', item['id']

def cover(item, lead=False):
    css = 'cover-lead' if lead else 'cover-side'
    return f'''<a class="{css}" href="#{e(item['id'])}" data-event="{e(item['id'])}" aria-label="{e(item['name'])}の見どころを見る"><img src="{e(item['image']['url'])}" alt="{e(item['image']['alt'])}" width="1200" height="800" {'fetchpriority="high"' if lead else 'loading="eager"'} referrerpolicy="no-referrer"><span class="cover-arrow" aria-hidden="true">↗</span><div class="cover-copy"><span class="cover-label">{e(item['areaLabel'])} · {e(item['stamp'])}</span><h2>{e(item['hook'])}</h2><p>{e(item['name'])}</p></div></a>'''

def card(item, index):
    source_label = '開催案内 ↗' if item.get('sourceLabel') else '公式サイト ↗'
    return f'''<article class="event-card" id="{e(item['id'])}"><a class="card-media" href="{e(item['source'])}" target="_blank" rel="noopener noreferrer" data-event="{e(item['id'])}" aria-label="{e(item['name'])}の見どころ・行き方"><img src="{e(item['image']['url'])}" alt="{e(item['image']['alt'])}" loading="lazy" decoding="async" width="900" height="630" style="object-fit:{e(item['image'].get('fit','cover'))};background:#18212a" referrerpolicy="no-referrer"><span class="date-stamp"><small>2026 / EVENT DATE</small>{e(item['stamp'])}</span><span class="photo-tag">{e(item['image']['label'])}</span></a><div class="card-meta"><span>{e(item['areaLabel'])}</span><span class="card-category">{e(item['categoryLabel'])}</span></div><h3 class="card-hook">{e(item['hook'])}</h3><p class="card-name">{e(item['name'])}</p><p class="card-venue">{e(item['venue'])}</p>{f'<p class="card-status">{e(item["status"])}</p>' if item.get('status') else ''}<div class="card-action"><button class="detail-button" data-event="{e(item['id'])}" aria-label="{e(item['name'])}の見どころ・行き方を開く">見どころ・行き方 <span aria-hidden="true">↗</span></button><a href="{e(item['source'])}" target="_blank" rel="noopener noreferrer">{source_label}</a></div></article>'''

def credit(item):
    im = item['image']
    license_text = f' / <a href="{e(im["licenseUrl"])}" target="_blank" rel="noopener noreferrer">{e(im["license"])}</a>（表示枠に合わせてトリミング）' if im.get('licenseUrl') else ''
    return f'<li>{e(item["name"])}：<a href="{e(im["source"])}" target="_blank" rel="noopener noreferrer">{e(im["credit"])}</a> — {e(im["label"])}{license_text}</li>'

category_names = [('all','すべて'),('music','音楽'),('art','アート・建築'),('food','食とお酒'),('festival','祭り・灯り'),('walk','まち歩き'),('sport','スポーツ')]
buttons = ''.join(f'<button type="button" data-mood="{key}" aria-pressed="{str(key=="all").lower()}">{label}</button>' for key,label in category_names)
cards = '\n'.join(card(item,index) for index,item in enumerate(events))
credits = '\n'.join(credit(item) for item in events)
data = json.dumps(events,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
page = f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#ffdf28"><meta name="referrer" content="strict-origin-when-cross-origin"><meta name="garraway-kyushu-version" content="20260911k1"><title>福岡に来たら、九州まで遊ぼう。｜九州の秋 2026｜Garraway F</title><meta name="description" content="2026年9月21日〜10月21日、RAMEN TECHの前後に出会いたい福岡・九州の音楽、アート、祭り、食のイベント。写真と見どころ、開催日、行き方で旅の寄り道を見つけるGarraway F編集の特集。"><link rel="canonical" href="https://garrawayf.github.io/ramen-tech-2026/kyushu/"><link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect x='1' y='1' width='30' height='30' rx='8' fill='%23ffdf28' stroke='%23111313' stroke-width='2'/%3E%3Ctext x='7' y='24' font-family='Arial' font-weight='bold' font-size='23'%3ER.%3C/text%3E%3C/svg%3E"><link rel="stylesheet" href="kyushu.css?v=20260911k1"><script src="kyushu.js?v=20260911k1" defer></script></head>
<body><a href="#main" class="skip">本文へ移動</a><header class="masthead"><a class="brand" href="../"><span class="brand-mark" aria-hidden="true">R.</span><span>RAMEN TECH 2026<small>非公式回遊ガイド｜Garraway F</small></span></a><nav aria-label="主要メニュー"><a class="nav-main" href="../#explore">イベントを探す</a><a href="./" aria-current="page">九州の秋</a><a class="plan-link" href="../#plan">マイ予定へ ↗</a></nav></header>
<main id="main" class="wrap"><div class="issue"><span>GARRAWAY F / KYUSHU AUTUMN ISSUE</span><a href="../">← 回遊ガイド</a></div><section aria-labelledby="page-title"><div class="intro"><h1 id="page-title">福岡に来たら、<br><span>九州まで遊ぼう。</span></h1><aside><p>ライブに、アートに、祭りに。<br>予定の前後に、忘れられない寄り道を。</p><div class="issue-date">09.21 <small>MON</small> — 10.21 <small>WED / 2026</small></div></aside></div><div class="cover">{cover(by_id['nagasaki-kunchi'],True)}<div class="cover-stack">{cover(by_id['afaf'])}{cover(by_id['sunset'])}</div></div><p class="photo-note cover-source">写真は過去開催の様子・会場イメージです。出典は各イベントの詳細へ。</p><div class="period-note"><p>RAMEN TECH本会期は10/7〜11。前後10日に、Garraway Fの関連期間に合わせた9/21〜26も加えて紹介。掲載イベントの全会期は、各カード・詳細に表示しています。</p><a href="#discover">秋の寄り道を見つける ↓</a></div></section>
<section id="discover" aria-labelledby="discover-title"><p class="section-kicker">PICK YOUR NEXT EXPERIENCE</p><div class="section-heading"><h2 id="discover-title">その日、どこで遊ぶ？</h2><p>福岡でふらっと。九州へ、ひと足。</p></div><div class="filter-panel"><div class="filters-top"><div class="moods" role="group" aria-label="楽しみ方で絞り込み">{buttons}</div></div><div class="filters-bottom"><label>エリア<select id="area"><option value="all">九州すべて</option><option value="fukuoka">福岡</option><option value="saga">佐賀</option><option value="nagasaki">長崎</option><option value="oita">大分</option><option value="kumamoto">熊本</option><option value="miyazaki">宮崎</option></select></label><label>滞在期間<select id="period"><option value="all">9/21〜10/21 すべて</option><option value="before">9/21〜9/30</option><option value="early">10/1〜10/6</option><option value="ramen">10/7〜10/11 本会期</option><option value="after">10/12〜10/21</option></select></label><span class="result" id="result-count" role="status" aria-live="polite"><b>{len(events)}</b> 件の寄り道</span><button type="button" class="clear" id="clear-filters" hidden>絞り込みを解除</button></div></div><div class="cards" id="event-grid">{cards}</div><div class="empty" id="empty" hidden><h3>この条件のイベントは、まだ掲載がありません。</h3><p>エリアや期間を変えて、次の寄り道を探してみてください。</p></div></section>
<section class="closing" aria-labelledby="closing-title"><div><p class="section-kicker">MAKE IT A TRIP.</p><h2 id="closing-title">出会いのあとにも、<br>旅は続く。</h2><p>RAMEN TECHの予定と往復の移動を、トリッププランナーで。</p></div><a href="../#plan">マイ予定・トリッププランナーへ ↗</a></section>
<details class="credits"><summary>掲載情報・写真の出典について</summary><p>Garraway Fが編集する非公式の旅の特集です。2026年9月11日時点で公開されている日程から選び、イベントごとに開催案内をリンクしています。すべてのイベントを網羅するものではありません。開催変更、料金、予約、残席、休館日は主催者の案内でご確認ください。</p><p>福岡の企画選びには <a href="https://www.fukuoka-now.com/ja/guides/fukuoka-autumn-guide/" target="_blank" rel="noopener noreferrer">Fukuoka Now「福岡秋のガイド2026」</a> も参照しています。紹介文はこの特集のために編集。主催者情報と日程が異なる場合は主催者発表を優先しています。</p><p>写真は過去開催、会場、主催者の告知ビジュアルです。2026年の開催後写真ではありません。画像の権利は各権利者に帰属します。閲覧用に画像サイズを調整しています。写真の利用許諾を第三者へ付与するものではありません。</p><ul>{credits}</ul><p>この特集のイベントは、RAMEN TECHのマイ予定には直接追加されません。各開催案内で参加方法をご確認ください。</p></details>
<footer class="site-footer"><span>RAMEN TECH 2026 非公式回遊ガイド｜Garraway F<br>KYUSHU AUTUMN / EDITED SEPTEMBER 11, 2026</span><a href="../">RAMEN TECH回遊ガイドへ戻る ↗</a></footer></main><dialog id="event-dialog" aria-labelledby="dialog-title"><button type="button" class="dialog-close" id="close-dialog" aria-label="閉じる">×</button><div id="dialog-inner"></div></dialog><script type="application/json" id="event-data">{data}</script><noscript><p class="wrap">写真と公式サイトへのリンクからご覧ください。絞り込みと詳細表示にはJavaScriptを使用します。</p></noscript></body></html>'''
(ROOT / 'index.html').write_text(page, encoding='utf-8')
print(f'Rendered {len(events)} events, {len(set(item["image"]["url"] for item in events))} images')
