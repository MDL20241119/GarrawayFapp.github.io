import json, os, urllib.parse, urllib.request
TOKEN=os.environ['X_BEARER_TOKEN']
USERNAME=os.environ.get('X_USERNAME','garraway_f')
def get(url):
    req=urllib.request.Request(url,headers={'Authorization':f'Bearer {TOKEN}','User-Agent':'GarrawayF-feed/1.0'})
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
user=get('https://api.x.com/2/users/by/username/'+urllib.parse.quote(USERNAME))['data']
uid=user['id']
params=urllib.parse.urlencode({'max_results':'10','exclude':'retweets,replies','tweet.fields':'created_at,public_metrics,attachments','expansions':'attachments.media_keys','media.fields':'type,url,preview_image_url,width,height'})
raw=get(f'https://api.x.com/2/users/{uid}/tweets?{params}')
media={m['media_key']:m for m in raw.get('includes',{}).get('media',[])}
posts=[]
for t in raw.get('data',[])[:6]:
    imgs=[]
    for key in t.get('attachments',{}).get('media_keys',[]):
        m=media.get(key,{})
        u=m.get('url') or m.get('preview_image_url')
        if u: imgs.append({'url':u,'type':m.get('type','')})
    posts.append({'id':t['id'],'text':t.get('text',''),'created_at':t.get('created_at',''),'url':f'https://x.com/{USERNAME}/status/{t["id"]}','media':imgs,'metrics':t.get('public_metrics',{})})
os.makedirs('data',exist_ok=True)
with open('data/x.json','w',encoding='utf-8') as f:json.dump({'account':USERNAME,'posts':posts},f,ensure_ascii=False,indent=2)
