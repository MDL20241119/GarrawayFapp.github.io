"""Project official venue coordinates onto guide facility IDs; never geocode private venues."""
import math
from ramen_sync import resolve_venue
SOURCE='https://ramentech2026.aishain.com/api/schedule'
CANONICAL={'one6':'one-fukuoka','cic':'cic','garraway':'venue-b3d1cff0-23f4-4b6a-8037-982dd828a353'}
EXCLUDED={'private','tbd','city','kyushu-venues','v-9c4fea060c'}
def distance(a,b):
    r=math.pi/180;x=(b['lat']-a['lat'])*r;y=(b['lng']-a['lng'])*r
    q=math.sin(x/2)**2+math.cos(a['lat']*r)*math.cos(b['lat']*r)*math.sin(y/2)**2
    return 12742000*math.atan2(math.sqrt(q),math.sqrt(max(0,1-q)))
def apply_geo(catalog,source,checked_at):
    lookup={v['id']:v for v in catalog['venues']};groups={}
    for raw in source:
        if not isinstance(raw,dict):continue
        lat,lng=raw.get('lat'),raw.get('lng')
        if not isinstance(lat,(float,int)) or not isinstance(lng,(float,int)) or not (20<lat<46 and 120<lng<155):continue
        # A combined/ambiguous facility label is not an exact destination.
        if 'Zero-Ten Park HALL THE KEGO' in raw.get('name',''):continue
        ident=resolve_venue(raw.get('name',''),dict(lookup),raw.get('address',''))
        if ident not in lookup or ident in EXCLUDED:continue
        groups.setdefault(ident,[]).append(raw)
    for v in catalog['venues']:
        group=groups.get(v['id'],[])
        if not group:
            if 'geo' in v:v['geo']['status']='unavailable'
            continue
        chosen=next((x for x in group if x['id']==CANONICAL.get(v['id'])),None)
        spread=max((distance(a,b) for a in group for b in group),default=0)
        if not chosen and spread>80:
            v['geo']={'status':'conflict','source':SOURCE,'checkedAt':checked_at,'note':'同一施設の公開座標に80mを超える不一致があり自動推定しません。'}
            continue
        chosen=chosen or group[0]
        v['geo']={'status':'located','lat':chosen['lat'],'lng':chosen['lng'],'address':chosen.get('address',''),
                  'source':SOURCE,'sourceVenueId':chosen['id'],'checkedAt':checked_at,
                  'note':'公開会場位置。入口・実際の歩行経路を示すものではありません。'+(' 館内部屋の異なる座標より施設本体の登録位置を採用。' if spread>80 else '')}
    return catalog
