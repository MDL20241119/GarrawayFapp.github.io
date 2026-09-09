"""Idempotent targeted integration. Do not replace unrelated homepage or event content."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,argparse,sys

def once(text,old,new):
    if new in text:return text
    if old not in text:raise RuntimeError('Integration anchor missing: '+old[:90])
    return text.replace(old,new,1)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source');parser.add_argument('--schedule-json');args=parser.parse_args()
    root=Path.cwd();fragment=root/'tools/planner_fragments'
    if args.source:
        dst=Path(args.source);p=dst/'app/page.tsx';s=p.read_text()
        s=once(s,'import SocialLive from "./social-live";','import SocialLive from "./social-live";\nimport RamenSpecial from "./ramen-special";')
        s=once(s,'      <section className="stats"','      <RamenSpecial />\n\n      <section className="stats"')
        s=once(s,'          <a href="#access">ACCESS</a>','          <a href="#access">ACCESS</a>\n          <a className="gf-ramen-nav" href={withBasePath("/ramen-tech-2026/")}>RAMEN TECH ↗</a>')
        p.write_text(s);(dst/'app/ramen-special.tsx').write_text((fragment/'source-component.tsx').read_text());(dst/'app/ramen-special.css').write_text((root/'ramen-special.css').read_text())
        note='\n\n## RAMEN TECH special site\n`RamenSpecial` is the homepage entrance. Keep the current main-branch `ramen-tech-2026/`, its tools and daily workflows when republishing this source. Never replace the daily catalog with an old source snapshot.\n'
        p=dst/'README.md';s=p.read_text();p.write_text(s if '## RAMEN TECH special site' in s else s+note);return
    site=root/'ramen-tech-2026';p=site/'index.html';s=p.read_text()
    if 'planner.js' not in s:
        s=once(s,'</head>','<link rel="stylesheet" href="planner.css?v=20260909p1"><script src="planner.js?v=20260909p1" defer></script></head>')
        s=once(s,'<main id="top">','<main id="top"><div class="special-breadcrumb"><a href="../">← Garraway F ホーム</a><span>RAMEN TECH 特設サイト / 非公式イベントガイド</span><a href="#garraway-featured">Garraway Fの企画</a></div>')
        s=once(s,'<section class="schedule-section wrap"',(fragment/'featured.html').read_text()+'<section class="schedule-section wrap"')
        s=once(s,'<section class="garraway-block"',(fragment/'planner.html').read_text()+'<section class="garraway-block"')
        s=s.replace('♡ マイ予定 <span id="saved-count">','♡ 興味あり <span id="saved-count">')
        s=once(s,'<div class="quick-filters">','<div class="quick-filters"><a class="chip plan-quick-link" href="#planner" data-plan-open>移動込みの予定表 <span data-plan-count>0</span></a>')
        s=s.replace('<a href="#venues">会場ガイド</a>','<a href="#planner" data-plan-open>マイスケジュール</a><a href="#garraway-featured">Garraway F</a>',1)
        start=s.index('<nav class="mobile-nav"');end=s.index('</nav>',start)+6
        s=s[:start]+'<nav class="mobile-nav" aria-label="スマートフォンメニュー"><a href="#schedule">イベント検索</a><a href="#planner" data-plan-open>予定表 <span data-plan-count>0</span></a><a href="#garraway-featured">Garraway F</a><a href="#venues">会場ガイド</a></nav><span id="mobile-saved-count" hidden>0</span>'+s[end:]
        s=once(s,'</body>','<a href="#planner" class="planner-dock" data-plan-open>移動込みの予定表 <span data-plan-count>0</span> ↗</a></body>')
        s=s.replace('app.js?v=','app.js?v=planner1-').replace('catalog.js?v=','catalog.js?v=planner1-')
        p.write_text(s)
    p=site/'app.js';s=p.read_text()
    if 'ramen:saved' not in s:
        s=once(s,'renderActive();syncURL();}','renderActive();syncURL();document.dispatchEvent(new CustomEvent("ramen:render"));}')
        s=once(s,'function save(id){','function save(id,day){')
        s=once(s,'if(d.save)save(d.save);','if(d.save)save(d.save,d.on);')
        s=s.replace('data-save="${esc(e.id)}"','data-save="${esc(e.id)}" data-on="${day}"')
        s=once(s,"toast((add?'マイ予定に保存しました'","document.dispatchEvent(new CustomEvent('ramen:saved',{detail:{id,day:day||detailDay,add}}));toast((add?'マイ予定に保存しました'")
        s=s.replace('同じイベントの全開催日が保存されます。移動時間は計算していません。','参加日ごとの移動・時間の調整は「移動込みの予定表」で確認できます。')
        s=once(s,'window.RamenGuide={data,','window.RamenGuide={data,openDetail,setSaved:(id,value)=>{value?saved.add(id):saved.delete(id);try{localStorage.setItem(KEY,JSON.stringify([...saved]));}catch{}render();},')
        s=once(s,"if(b.id==='download-saved')exportICS(events.filter(e=>saved.has(e.id)).flatMap(e=>e.dates.map(day=>({e,day}))));", "if(b.id==='download-saved'){if(window.RamenPlanner)window.RamenPlanner.exportPlan();else exportICS(events.filter(e=>saved.has(e.id)).flatMap(e=>e.dates.map(day=>({e,day}))));}")
        p.write_text(s)
    p=root/'index.html';s=p.read_text()
    if 'ramen-special.js' not in s:s=once(s,'</head>','<link rel="stylesheet" href="/GarrawayFapp.github.io/ramen-special.css?v=1"><script src="/GarrawayFapp.github.io/ramen-special.js?v=1" defer></script></head>');p.write_text(s)
    p=root/'tools/ramen_sync.py';s=p.read_text()
    if 'from ramen_geo import apply_geo' not in s:
        s=once(s,'c,actions=update_catalog(old,feeds,now);validate(c)',"c,actions=update_catalog(old,feeds,now);validate(c)\n            from ramen_geo import apply_geo\n            if 'schedule' in feeds: apply_geo(c,feeds['schedule']['venues'],now)");p.write_text(s)
    if args.schedule_json:
        from ramen_geo import apply_geo
        p=site/'catalog.js';c=json.loads(p.read_text().split('=',1)[1].strip().rstrip(';'));feed=json.loads(Path(args.schedule_json).read_text());before=[dict(e) for e in c['events']]
        apply_geo(c,feed['venues'],datetime.now(timezone(timedelta(hours=9))).isoformat(timespec='seconds'))
        assert before==c['events'],'Planner integration must not alter event records'
        p.write_text('window.RAMEN_CATALOG='+json.dumps(c,ensure_ascii=False,separators=(',',':'))+';\n')
        print('Located venues:',sum(v.get('geo',{}).get('status')=='located' for v in c['venues']))
    note='''\n\n## 特設サイト・移動込みのマイスケジュール（2026-09-09）
Garraway FトップページにRAMEN TECH特設サイトへのバナー・ナビを追加。サイト冒頭にGarraway Fの6独自企画を特集し、館内の他主催者企画を含む全枠への入口、検索結果の会場色ラベルを設置しています。参加条件や館内同時開催の要確認表示は維持します。

`planner.js` / `planner.css` は日別の選択、参加時間の調整、移動・到着・予備・空き時間のタイムライン、一覧表、予定のコピー、印刷、移動込みICSを実装。保存はブラウザ内のみで予約ではありません。新しい追加操作は指定日だけを保存します。既存の興味ありは旧仕様どおり全開催日を初回移行し、不要日は削除できます。

`tools/ramen_geo.py` は公式時間割の会場位置を施設IDへ照合し、毎朝の取得時に更新します。公開座標の不一致・未確認位置・直線5km超は自動推定しません。館内の座標が食い違うONE FUKUOKAについては施設本体の登録位置を優先します。
徒歩は直線距離×1.35÷選択速度（初期70m/分）を5分単位で切上げる計画用の目安で、実測・経路API・Googleの所要時間ではありません。同施設3分、同室0分、ほぼ同位置の異施設5分を仮置きし、予備10分を別途加えます。係数・速度・館内移動は計画上の仮定です。公共交通・車は地図リンクで確認して手入力します。道路・混雑・バリアフリー動線は取得しません。
開催情報変更、時刻未確認、中止、移動未確認、時間不足は表示して確認を促し、未解消の日のICS出力を止めます。手入力の移動時間は会場・座標が変わると無効になり再確認が必要です。選択済み参加時間が更新された開催時間の範囲外になった場合も要確認にします。外部カレンダーは自動同期されません。

`tools/ramen_verify_planner.py` は公開トップ、検索、日別選択、複数会場移動、参加時間調整、手入力、保存、要確認、ICS、印刷、320/390/768/1440pxの動作を検証します。mainのトップは既存Next成果物を変更しすぎない追加ウィジェット方式、sites-sourceは同じ案内のReactコンポーネントを追加しています。ソース再ビルド時も最新の専用ディレクトリと自動更新用tools・workflowを保持してください。
'''
    p=site/'README.md';s=p.read_text();p.write_text(s if '## 特設サイト・移動込み' in s else s+note)
if __name__=='__main__':main()
