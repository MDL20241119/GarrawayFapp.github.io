#!/usr/bin/env python3
"""Refresh the RAMEN guide from public structured feeds. Standard library only.
Never execute remote JavaScript, infer unknown times, remove a disappeared event,
or overwrite the six locally authored Garraway F events.
"""
from __future__ import annotations
import argparse, copy, hashlib, html, json, os, re, sys, time, unicodedata
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen

SOURCES = {'members': 'https://members.ramentech.jp/', 'schedule': 'https://ramentech2026.aishain.com/api/schedule'}
TIMETABLE = 'https://ramentech2026.aishain.com/'
JST = timezone(timedelta(hours=9))
NOTE = '[自動確認] '
MANUAL = {'coffee-7', 'coffee-8', 'coffee-9', 'welcome-7', 'connect-8', 'next-9'}
PLACEHOLDERS = {'tbd', 'private', 'city', 'kyushu-venues'}
# Explicitly reviewed duplicates from the original September 9 catalog.
OMIT = {'members-the-gathering-2', 'ed382dc8-4d5a-44d1-9f71-4ade86019b91'}

def norm(value):
    return re.sub(r'[^\w\u3040-\u30ff\u4e00-\u9fff]', '', unicodedata.normalize('NFKC', str(value or '')).lower())

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def safe_url(value):
    value = str(value or '').strip()
    return value if urlparse(value).scheme in ('https', 'http') and len(value) <= 3000 else ''

def clean(value, limit=2000):
    return html.unescape(str(value or ''))[:limit].strip()

def iso_day(value):
    value = str(value or '')
    if not re.fullmatch(r'2026-\d{2}-\d{2}', value):
        return None
    try:
        d = date.fromisoformat(value)
        return value if date(2026, 9, 1) <= d <= date(2026, 11, 30) else None
    except ValueError:
        return None

def times(start, end):
    valid = lambda t: t if re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', str(t or '')) else None
    s, e = valid(start), valid(end)
    if (s, e) == ('00:00', '23:59'):
        return None, None  # upstream placeholder, NOT a confirmed all-day event
    return s, e

def member_record(raw):
    required = ('slug', 'name', 'eventStartDate', 'eventEndDate')
    if not all(k in raw for k in required):
        raise ValueError('Registration schema changed: required fields missing')
    days = [d for d in (raw.get('multiDates') or []) if iso_day(d)]
    if not days:
        first, last = iso_day(raw['eventStartDate']), iso_day(raw['eventEndDate'])
        if not first or not last:
            return None
        a, b = date.fromisoformat(first), date.fromisoformat(last)
        if not 0 <= (b-a).days <= 62:
            raise ValueError('Unexpected event date range')
        days = [(a+timedelta(days=i)).isoformat() for i in range((b-a).days+1)]
    start, end = times(raw.get('eventStartTime'), raw.get('eventEndTime'))
    return dict(key=str(raw.get('client', ''))+'/'+str(raw['slug']), slug=str(raw['slug']),
                title=clean(raw['name'], 500), dates=sorted(set(days)), start=start, end=end,
                location=clean(raw.get('location')), url=safe_url(raw.get('url')),
                tags=[clean(x, 100) for x in raw.get('tags', []) if isinstance(x, str)],
                free=raw.get('isFree') is True, active=raw.get('isActive') is not False,
                ticket=clean(raw.get('ticketStatus'), 100), description=clean(raw.get('description')))

def parse_members(text):
    found = re.search(r'window\.jsEvents\s*=\s*', text)
    if not found:
        raise ValueError('Public registration list could not be located')
    raw, _ = json.JSONDecoder().raw_decode(text[found.end():])
    if not isinstance(raw, list) or not raw or len(raw)>5000:
        raise ValueError('Invalid registration list')
    records = [member_record(r) for r in raw if isinstance(r, dict)]
    records = [r for r in records if r is not None]
    if len({r['key'] for r in records}) != len(records):
        raise ValueError('Duplicate registration identifiers')
    return records

def parse_schedule(text):
    raw = json.loads(text)
    if not isinstance(raw, dict) or not isinstance(raw.get('sessions'), list) or not isinstance(raw.get('venues'), list):
        raise ValueError('Timetable schema changed')
    venues = {str(v['id']): v for v in raw['venues'] if isinstance(v, dict) and v.get('id') and v.get('name')}
    sessions = []
    for s in raw['sessions']:
        if not all(k in s for k in ('id', 'title', 'date', 'venueId', 'startsAt', 'endsAt')):
            raise ValueError('Timetable session fields changed')
        if not iso_day(s['date']):
            continue
        if str(s['venueId']) not in venues:
            raise ValueError('Timetable contains an unknown venue ID')
        start, end = times(s['startsAt'], s['endsAt'])
        v = venues[str(s['venueId'])]
        sessions.append(dict(key=str(s['id']), title=clean(s['title'], 500), dates=[s['date']],
                             start=start, end=end, venueKey=str(s['venueId']), location=clean(v['name']),
                             address=clean(v.get('address')), url=safe_url(s.get('url')),
                             tags=[clean(t, 100) for t in s.get('tags', []) if isinstance(t, str)],
                             speaker=clean(s.get('speaker'), 500), company=clean(s.get('company'), 500),
                             description=clean(s.get('description'))))
    if len({x['key'] for x in sessions}) != len(sessions):
        raise ValueError('Duplicate timetable identifiers')
    return {'records': sessions, 'venues': list(venues.values())}

def get_text(url):
    errors=[]
    for attempt in range(3):
        try:
            req=Request(url, headers={'User-Agent':'Mozilla/5.0 (RAMEN City Guide daily public schedule refresh)', 'Accept':'application/json,text/html;q=0.9'})
            with urlopen(req, timeout=35) as res:
                if urlparse(res.url).hostname != urlparse(url).hostname:
                    raise ValueError('Unexpected cross-domain feed redirect')
                content=res.read(8_000_001)
                if len(content)>8_000_000:
                    raise ValueError('Feed exceeds safe size')
                return content.decode('utf-8-sig')
        except Exception as exc:
            errors.append(type(exc).__name__+': '+str(exc)[:200])
            if attempt < 2: time.sleep(2**attempt)
    raise RuntimeError(errors[-1])

def category(title, tags):
    t=' '.join([title]+tags).lower()
    for pattern, cat in [(r'ピッチ|pitch','ピッチ'), (r'\bai\b|生成ai|エンジニア|hackathon|deeptech|ディープテック','AI・技術'),
                         (r'アート|design|デザイン|creator','アート・デザイン'),(r'教育|education|student','教育'),
                         (r'wellness|sauna|run\b|ヨガ|サウナ|ランニング','体験・ウェルネス'),
                         (r'meetup|交流|lounge|party|network|gathering','交流')]:
        if re.search(pattern,t): return cat
    return 'ビジネス・共創'

# Facility identity is separate from a room. Match specific floors/rooms first.
ALIASES = [('awabar','awabar'),('博多舟','boat'),('ohoripark','ohori'),('weworktenjin','wework-tenjin'),('fukuokadaimyogardencitypark','gardenpark'),('福岡大名ガーデンシティパーク','gardenpark'),('未定','tbd'),('onefukuokabldg4','tsutaya'),('garraway','garraway'),('ギャラウェイ','garraway'),('cic','cic'),
 ('fukuokagrowthnext','fgn'),('awabar','awabar'),('horizonstage','daimyo'),('frontierstage','daimyo'),('openpitchstage','daimyo'),
 ('大名カンファレンス','daimyo'),('daimyoconference','daimyo'),('recコーヒー','rec'),('reccoffee','rec'),
 ('ワンビルスカイロビー','one6'),('terracehall','one6'),('terraceroom','one6'),('presentationroom','one6'),('skylobby','one6'),
 ('onefukuoka','one6'),('天神ビジネスセンター','tbc'),('fukuokainnovationlab','fil'),
 ('wework天神','wework-tenjin'),('wework博多','wework-hakata'),('weworkhakata','wework-hakata'),
 ('tkpガーデンシティpremium天神ブリック','tkp-brick'),('tkpガーデンシティpremium天神スカイ','tkp-sky'),
 ('fabbit','fabbit'),('elgarla','elgala'),('エルガーラ','elgala'),('cirq福岡','cirq-fukuoka'),('cirqシルク福岡','cirq-fukuoka'),
 ('cirqシルク天神北','cirq-tenjin'),('cirq天神北','cirq-tenjin'),('kegoclub','kego'),
 ('zerotenparkhall','zero-hall'),('artistcafe','artist'),('大濠公園','ohori'),('舞鶴公園','maizuru'),
 ('engineercafe','engineer'),('unitedlab','unitedlab'),('fusic','fusic'),('サーブコープ','servcorp'),('servcorp','servcorp'),
 ('growthⅰ','growth1'),('growth1','growth1'),('sevenxseven','seven'),('inn the park','inthepark'),
 ('innthepark','inthepark'),('in the park','inthepark'),('salt','salt'),('蔦屋書店','tsutaya'),
 ('会場未定','tbd'),('会場未公表','tbd'),('参加確定者','private'),('bay','bay'),('リッツ','ritz'),('ritz','ritz')]

def resolve_venue(location, venues, address=''):
    n=norm(location)
    if not n: return 'tbd'
    # Both places explicitly named: do not silently collapse them to one.
    if 'artistcafe' in n and '舞鶴公園' in n: return 'kyushu-venues'
    if n=='fukuoka': return 'v-9c4fea060c'
    if '福岡市内' in n and '複数' in n: return 'city'
    for token, ident in ALIASES:
        if norm(token) in n and ident in venues:
            return ident
    for v in venues.values():
        if n==norm(v['name']):return v['id']
    ident='auto-venue-'+hashlib.sha256(n.encode()).hexdigest()[:12]
    if ident not in venues:
        area=next((a for a in ['天神','大名','博多','今泉','西中洲','糸島'] if a in location+address),'その他')
        venues[ident]={'id':ident,'name':clean(location,200),'area':area,'website':'','address':address,
                       'roles':[],'source':TIMETABLE,'note':'公開登録・時間割から自動追加。利用条件は主催者にご確認ください。','eventCount':0}
    return ident

def fresh_event(ident, raw, venue, origin, kind):
    return dict(id=ident,title=raw['title'],dates=raw['dates'],start=raw['start'],end=raw['end'],
                venue=venue,room='',kind=kind,origin=origin,url=raw['url'],
                source=SOURCES['members'] if kind=='event' else TIMETABLE,
                tags=raw.get('tags',[]),fee='参加条件を確認',status='published',notes=[],
                category=category(raw['title'],raw.get('tags',[])))

def update_catalog(original, feeds, now):
    c=copy.deepcopy(original); events={e['id']:e for e in c['events']}; venues={v['id']:v for v in c['venues']}
    seen={'members':set(),'schedule':set()}; mapping={}; member_for={}; member_venues={}; schedule_for={}; review_notes={}; actions=[]
    before={e['id']:copy.deepcopy(e) for e in c['events']}
    for e in events.values():
        e.setdefault('checkedAt',original['meta'].get('checkedAt','2026-09-09'))
        if e['id'] in MANUAL: continue
        sync=e.setdefault('sync',{})
        if 'editorialReview' not in sync:
            sync['editorialReview']=e.get('status')=='check' and any(not n.startswith((NOTE,'時刻の表記不一致：','会場表記不一致：')) for n in e.get('notes',[]))
            sync['manualBlock']=bool(e.get('calendarBlocked') and sync['editorialReview'])
        for key in sync.get('memberKeys',[]):mapping[('members',key)]=e['id']
        for key in sync.get('scheduleKeys',[]):mapping[('schedule',key)]=e['id']
        if e['id'].startswith('slot-'):mapping[('schedule',e['id'][5:])]=e['id']
        for u in e.get('alsoSources',[]):
            sid=parse_qs(urlparse(u).query).get('session',[''])[0]
            if sid:mapping[('schedule',sid)]=e['id']
    def touched(e, source, raw):
        sync=e.setdefault('sync',{}); field='memberKeys' if source=='members' else 'scheduleKeys'
        sync[field]=sorted(set(sync.get(field,[])+[raw['key']]))
        sync.setdefault('seenAt',{})[source]=now
        sync.setdefault('hashes',{})[source+':'+raw['key']]=digest(raw)
        e['autoCheckedAt']=now; seen[source].add(e['id'])
    for r in feeds.get('members',[]):
        ident=mapping.get(('members',r['key']))
        if not ident and 'event-'+r['slug'] in events:ident='event-'+r['slug']
        if not ident:
            # Client is included to avoid collisions between two organizers' slugs.
            ident='event-auto-'+hashlib.sha256(r['key'].encode()).hexdigest()[:14]
        if ident in MANUAL: continue
        venue=resolve_venue(r['location'],venues)
        new=ident not in events
        if new:events[ident]=fresh_event(ident,r,venue,'公式登録','event')
        e=events[ident]; oldhash=e.get('sync',{}).get('hashes',{}).get('members:'+r['key'])
        curated=e.get('source') not in (SOURCES['members'],TIMETABLE)
        if not curated:
            e.update(title=r['title'],dates=r['dates'],url=r['url'] or e.get('url',''),tags=r['tags'])
            # Keep explicit previously reviewed room/facility aliases unless location changed.
            previous=e.get('sync',{}).get('memberLocation')
            if new or (previous is not None and previous!=r['location']):e['venue']=venue
            if r['start'] and r['end']:
                e['start'],e['end']=r['start'],r['end'];e.pop('slots',None)
            elif oldhash and oldhash!=digest(r):
                e['start'],e['end']=r['start'],r['end'];e.pop('slots',None)
            if r['free']:e['fee']='無料・参加方法は主催者案内を確認'
            elif e.get('sync',{}).get('registrationFree'):e['fee']='参加条件を確認'
        elif oldhash and oldhash!=digest(r):
            e.setdefault('sync',{})['needsEditorialReview']=True
            e['status']='check';e['calendarBlocked']=True
        e.setdefault('sync',{})['memberLocation']=r['location']
        e['sync']['registrationFree']=r['free']
        if oldhash!=digest(r):
            for key in ('speaker','company','description'):
                if r.get(key):e[key]=r[key]
        touched(e,'members',r);member_for[ident]=r;member_venues[ident]=e['venue']
    for r in feeds.get('schedule',{}).get('records',[]):
        if r['key'] in OMIT: continue
        ident=mapping.get(('schedule',r['key']))
        if not ident and r['key'].startswith('members-') and 'event-'+r['key'][8:] in events:
            ident='event-'+r['key'][8:]
        if not ident:
            matches=[e['id'] for e in events.values() if e['id'] not in MANUAL and norm(e['title'])==norm(r['title']) and set(r['dates'])&set(e['dates'])]
            if len(matches)==1:ident=matches[0]
        if not ident:ident='slot-'+r['key']
        if ident in MANUAL:continue
        venue=resolve_venue(r['location'],venues,r.get('address',''))
        new=ident not in events
        if new:events[ident]=fresh_event(ident,r,venue,'公式時間割','session')
        e=events[ident];oldhash=e.get('sync',{}).get('hashes',{}).get('schedule:'+r['key'])
        if e['kind']=='session' or (ident not in member_for and e.get('origin')=='公式時間割'):
            if new or oldhash!=digest(r):
                e.update(title=r['title'],dates=r['dates'],start=r['start'],end=r['end'],room=r['location'])
                e.pop('slots',None)
                # Existing mappings were manually grouped into facilities. Preserve on bootstrap.
                if new or oldhash:e['venue']=venue
                if r['url'] and (new or oldhash or not e.get('url')):e['url']=r['url']
                for key in ('speaker','company','description'):
                    if r.get(key):e[key]=r[key]
                if new:e['tags']=r.get('tags',[])
        touched(e,'schedule',r);schedule_for.setdefault(ident,[]).append((r,venue))
    # Reconcile event-level fields without confusing a child session with its parent.
    for ident,e in events.items():
        if ident in MANUAL: continue
        got=[src for src in seen if ident in seen[src]]
        if not got: continue
        oldnotes=list(e.get('notes',[]))
        e['notes']=[n for n in oldnotes if not n.startswith(NOTE) and not n.startswith(('時刻の表記不一致：','会場表記不一致：'))] if len(feeds)==2 else oldnotes
        other_review=e.get('sync',{}).get('editorialReview') or any(('要確認' in n or '確認が必要' in n or '主催者確認' in n) for n in e['notes'])
        # Recompute only automatic conflict flags; preserve editorial restrictions.
        if len(feeds)==2 and e.get('status')=='check' and not other_review and not e.get('sync',{}).get('manualBlock'):
            e['status']='published';e.pop('calendarBlocked',None)
        if e.get('sync',{}).get('needsEditorialReview'):
            e['notes'].append(NOTE+'登録情報に変更があります。個別主催者の補足情報と再照合が必要です。');e['status']='check';e['calendarBlocked']=True
        r=member_for.get(ident)
        if r:
            if re.search(r'中止|cancelled|canceled',r['title']+' '+r['ticket'],re.I):
                e['status']='cancelled';e['calendarBlocked']=True;e['notes'].append(NOTE+'公開情報に中止の記載があります。')
            elif re.search(r'完売|満席|sold[ -]?out',r['title']+' '+r['ticket'],re.I):e['status']='soldout'
            elif not r['active'] or re.search(r'販売終了|受付終了|closed',r['ticket'],re.I):
                e['status']='check';e['notes'].append(NOTE+'受付終了または非アクティブの表示です。開催中止とは限りません。')
            elif e.get('status') in ('soldout','cancelled'):
                e['status']='published';e.pop('calendarBlocked',None)
            if r['location']:
                mv=member_venues[ident]
                for sr,sv in schedule_for.get(ident,[]):
                    if mv!=sv and mv not in PLACEHOLDERS and sv not in PLACEHOLDERS:
                        e['status']='check';e['notes'].append(NOTE+'会場表記が不一致：登録「'+r['location'][:100]+'」／時間割「'+sr['location']+'」。')
                        e['calendarBlocked']=True
            for sr,sv in schedule_for.get(ident,[]):
                if not sr['start'] or not sr['end']: continue
                if sr['dates'][0] not in e['dates']:
                    e['status']='check';e['calendarBlocked']=True;e['notes'].append(NOTE+'登録と時間割の開催日が異なります。主催者案内を確認してください。');continue
                if r['start'] and r['end'] and (r['start'],r['end'])!=(sr['start'],sr['end']):
                    e['status']='check';e['calendarBlocked']=True
                    e['notes'].append(NOTE+f"時刻表記が不一致：登録 {r['start']}–{r['end']}／時間割 {sr['start']}–{sr['end']}。")
                elif not r['start'] and e.get('source')==SOURCES['members']:
                    if len(e['dates'])==1:e['start'],e['end']=sr['start'],sr['end']
                    else:e.setdefault('slots',{})[sr['dates'][0]]=[sr['start'],sr['end']]
        e['notes']=list(dict.fromkeys(e['notes']))
    # Never quietly discard a canceled, withdrawn, or temporarily missing record.
    for e in events.values():
        if e['id'] in MANUAL:continue
        keys=e.get('sync',{})
        for source,field in [('members','memberKeys'),('schedule','scheduleKeys')]:
            if source in feeds and keys.get(field) and e['id'] not in seen[source]:
                message=NOTE+('公式登録' if source=='members' else '公式時間割')+'の最新一覧に見当たりません。前回情報を保持しています。開催・掲載状況を確認してください。'
                if message not in e['notes']:e['notes'].append(message)
                e['status']='check';e['calendarBlocked']=True
    for e in events.values():
        previous=before.get(e['id'])
        # Only user-visible changes, not a new successful check, count as an update.
        visible=lambda x:{k:v for k,v in x.items() if k not in ('sync','checkedAt','autoCheckedAt','updatedAt','updateType')}
        if previous is None or visible(previous)!=visible(e):
            e['updatedAt']=now;e['updateType']='new' if previous is None else 'changed'
            actions.append({'id':e['id'],'title':e['title'],'type':e['updateType']})
        if e['id'] in MANUAL:assert visible(e)==visible(before[e['id']]), 'Manual event changed'
    c['events']=list(events.values());used={e['venue'] for e in c['events']}
    c['venues']=[v for v in venues.values() if not v['id'].startswith('auto-venue-') or v['id'] in used]
    counts=Counter(e['venue'] for e in c['events'])
    for v in c['venues']:v['eventCount']=counts[v['id']]
    c['meta'].update(eventCount=sum(e['kind']=='event' for e in c['events']),sessionCount=sum(e['kind']=='session' for e in c['events']),
                     venueCount=sum(v['id'] not in PLACEHOLDERS for v in c['venues']))
    if 'members' in feeds:c['meta']['registrationEvents']=len(feeds['members'])
    if 'schedule' in feeds:
        c['meta']['timetableSlots']=len(feeds['schedule']['records']);c['meta']['timetableVenueEntries']=len(feeds['schedule']['venues'])
    return c,actions

def validate(c):
    ids=[e['id'] for e in c['events']];vs={v['id'] for v in c['venues']}
    assert len(ids)==len(set(ids)) and 1<=len(ids)<=5000
    for e in c['events']:
        assert e['title'] and e['venue'] in vs and e['dates']
        assert all(iso_day(d) for d in e['dates'])
        assert e['kind'] in ('event','session') and isinstance(e['notes'],list)
        assert e.get('url','')==safe_url(e.get('url',''))
        for d in e['dates']:
            s,t=e.get('slots',{}).get(d,[e.get('start'),e.get('end')])
            assert (s,t)==times(s,t), f"Invalid or placeholder time: {e['id']}"
    assert MANUAL<=set(ids),'Required local events disappeared'

def install_ui(site):
    p=site/'index.html';text=p.read_text()
    if 'auto-update.js' not in text:
        text=text.replace('</head>','<link rel="stylesheet" href="auto-update.css?v=1"><script src="sync-status.js?v=1" defer></script><script src="auto-update.js?v=1" defer></script></head>')
    text=text.replace('情報確認：<span data-updated>','公式データ取得：<span data-updated>')
    text=text.replace('このガイドは保存時点の情報です。','公開登録・時間割を毎朝自動取得。')
    text=text.replace('情報はスナップショットで、常時自動同期ではありません。','公開登録・公式時間割は毎朝6:00（日本時間）に取得を開始します。GitHubの混雑で遅延する場合があります。個別主催者ページの補足・独自企画は別途確認が必要です。')
    p.write_text(text)
    p=site/'app.js';text=p.read_text()
    text=text.replace("function statusLabel(e){", "function statusLabel(e){if(e.status==='cancelled')return '<span class=\"label warn\">中止表記</span>';") if "e.status==='cancelled'" not in text else text
    text=text.replace("'情報確認日：'+data.meta.checkedAt", "'個別確認日：'+(e.checkedAt||data.meta.checkedAt)")
    text=text.replace('${esc(data.meta.checkedAt)}<br>出典：','${esc(e.checkedAt||data.meta.checkedAt)}${e.autoCheckedAt?\'<br>登録・時間割の自動確認：\'+esc(e.autoCheckedAt.replace(\'T\',\' \')):\'\'}<br>出典：')
    p.write_text(text)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--site',default='ramen-tech-2026');parser.add_argument('--fixtures');args=parser.parse_args()
    site=Path(args.site);now=datetime.now(JST).isoformat(timespec='seconds');day=now[:10]
    raw=(site/'catalog.js').read_text();old=json.loads(raw.split('=',1)[1].strip().rstrip(';'))
    statuspath=site/'sync-status.json';previous=json.loads(statuspath.read_text()) if statuspath.exists() else {}
    report={'attemptedAt':now,'lastSuccessAt':previous.get('lastSuccessAt'),'schedule':'毎朝6:00（日本時間）／失敗時6:35再試行',
            'sources':{},'changes':[],'status':'pending','catalogVersion':old['meta'].get('catalogVersion','initial')}
    feeds={}
    for source,url in SOURCES.items():
        prior=previous.get('sources',{}).get(source,{})
        try:
            text=(Path(args.fixtures)/(source+('.html' if source=='members' else '.json'))).read_text() if args.fixtures else get_text(url)
            value=parse_members(text) if source=='members' else parse_schedule(text)
            count=len(value) if source=='members' else len(value['records'])
            oldcount=prior.get('count',old['meta'].get('registrationEvents' if source=='members' else 'timetableSlots',0))
            if count<max(5,int(oldcount*0.60)) or count>5000:raise ValueError(f'Feed size anomaly: {oldcount} -> {count}. Old data preserved.')
            feeds[source]=value
            report['sources'][source]={'url':url,'ok':True,'count':count,'lastSuccessAt':now}
        except Exception as exc:
            report['sources'][source]={'url':url,'ok':False,'count':prior.get('count'), 'lastSuccessAt':prior.get('lastSuccessAt'),
                                       'error':type(exc).__name__+': '+str(exc)[:240]}
    if feeds:
        try:
            c,actions=update_catalog(old,feeds,now);validate(c)
            from ramen_geo import apply_geo
            if 'schedule' in feeds: apply_geo(c,feeds['schedule']['venues'],now)
            c['meta']['notice']='公開登録・公式時間割を毎朝自動取得。独自企画・個別主催者による補足は確認日を別記。未公表企画の完全性は保証しません。'
            c['meta']['catalogVersion']=now;c['meta']['fetchedAt']=now
            if len(feeds)==2:c['meta']['checkedAt']=day
            encoded='window.RAMEN_CATALOG='+json.dumps(c,ensure_ascii=False,separators=(',',':'))+';\n'
            tmp=site/'catalog.js.tmp';tmp.write_text(encoded);tmp.replace(site/'catalog.js')
            report['changes']=actions;report['catalogVersion']=now
            report['status']='success' if len(feeds)==2 else 'partial'
            report['catalogCount']=len(c['events']);report['venueCount']=c['meta']['venueCount']
            if len(feeds)==2:report['lastSuccessAt']=now
        except Exception as exc:
            report['status']='failed';report['validationError']=type(exc).__name__+': '+str(exc)[:300]
    else:report['status']='failed'
    # Status is published even when every feed fails; never fake a successful check.
    report['scope']='公式登録・公式時間割の公開構造化データを更新。個別主催者サイトの本文とGarraway F独自企画は自動上書きしません。'
    statuspath.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (site/'sync-status.js').write_text('window.RAMEN_SYNC_STATUS='+json.dumps(report,ensure_ascii=False,separators=(',',':'))+';\n')
    install_ui(site)
    p=site/'index.html';text=p.read_text();version=re.sub(r'\D','',now)[:14]
    for name in ['catalog.js','app.js','sync-status.js']:
        text=re.sub(re.escape(name)+r'(?:\?v=[^\"\s]+)?',name+'?v='+version,text)
    p.write_text(text)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    out=os.environ.get('GITHUB_OUTPUT')
    if out:
        with open(out,'a') as f:f.write('health='+report['status']+'\n')
    summary=os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary,'a') as f:
            f.write('# RAMEN guide daily refresh\n\n'+now+'\n\nStatus: '+report['status']+'\n\n')
            for src,r in report['sources'].items():f.write(f"- {src}: {'OK' if r['ok'] else 'FAILED'}, records={r.get('count')}, last success={r.get('lastSuccessAt')}\n")
            f.write('\nChanges: '+str(len(report['changes']))+'\n')
    return 0  # The workflow publishes health, then fails visibly for partial/failed results.

if __name__=='__main__':sys.exit(main())
