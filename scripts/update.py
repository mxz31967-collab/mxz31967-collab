"""Build a Chinese GitHub profile from real Steam reads and a tiny virtual pet."""
import argparse, hashlib, json, os, random
from pathlib import Path
from datetime import datetime, timezone, timedelta
from html import escape
from urllib.parse import urlencode
import steam, art

ROOT=Path(__file__).resolve().parents[1]
OWNER='mxzspace'
REPO=f'https://github.com/{OWNER}/{OWNER}'
RAW=f'https://raw.githubusercontent.com/{OWNER}/{OWNER}/main'
CN=timezone(timedelta(hours=8))
ACTIONS=('更新主页','喂小呱','明天休息','明天出发')

def read(path,default):
    p=ROOT/path
    return json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else default

def save(path,value):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def daily_frog(previous,today,action='更新主页'):
    f=json.loads(json.dumps(previous))
    f.setdefault('name','小呱');f.setdefault('energy',90);f.setdefault('history',[])
    f.setdefault('travel_count',0)
    status='主页已更新。'
    if f.get('day') != today:
        rest=f.get('rest_next',False) or f['energy'] < 25
        if rest:
            entry={'date':today,'place':'在家','spot':'荷叶小屋','souvenir':'休息日印章','diary':'泡一杯热茶，把收来的纪念品摆好。今天先好好休息，明天再看远方。','scene':'lake','rest':True}
            f['energy']=min(100,f['energy']+45)
        else:
            places=read(Path('data/destinations.json'),[])
            # A shuffled cycle visits each destination once before repeats.
            order=list(range(len(places)));random.Random('小呱第'+str(f['travel_count']//len(places))+'轮').shuffle(order)
            p=places[order[f['travel_count']%len(places)]]
            entry=dict(zip(('place','spot','souvenir','diary','scene'),p));entry.update(date=today,rest=False)
            f['travel_count']+=1;f['energy']=max(0,f['energy']-18)
        f['history'].append(entry);f['day']=today;f['rest_next']=False
    if action=='喂小呱':
        if f.get('fed_day')==today:status='小呱今天已经吃过饭团啦，明天再来吧。'
        else:f['energy']=min(100,f['energy']+30);f['fed_day']=today;status='小呱吃到了饭团，体力恢复了！'
    elif action=='明天休息':f['rest_next']=True;status='已给小呱安排明天在家休息。'
    elif action=='明天出发':f['rest_next']=False;status='已安排明天继续旅行；体力不足时会自动休息。'
    f['message']=status
    return f

def daily_box(previous,today,pool):
    if previous.get('date')==today:return previous
    used=list(previous.get('cycle_used',[]))
    available=[w for w in pool if w['url'] not in used]
    if not available:available=pool;used=[]
    seed=int(hashlib.sha256(('盲盒'+today).encode()).hexdigest(),16)
    choice=random.Random(seed).choice(available)
    return {'date':today,'site':choice,'cycle_used':used+[choice['url']]}

def safe(value):
    # HTML text is used in README so untrusted game names cannot add links/images.
    return escape(str(value)).replace('\n',' ').replace('\r',' ')

def section(title,section):
    out=f'### {title}\n\n'
    if not section.get('ok'):
        last=section.get('success_at','还没有成功读取')
        out+=f'> 这次没读到最新数据。下面是上次的结果（{safe(last)}），领取前先到商店确认。\n\n'
    else:out+=f'检查时间：{safe(section["checked_at"])}（北京时间）\n\n'
    offers=section.get('offers',[])
    if not offers:
        return out+('这次没查到，明天再看看。\n\n' if section.get('ok') else '还没读到结果，稍后再试。\n\n')
    for o in offers:
        url=f'https://store.steampowered.com/app/{int(o["id"])}/?cc=cn&amp;l=schinese'
        label='游戏附加内容，可能需要本体' if o.get('dlc') else ('领取后永久保留' if o['kind']=='keep' else '限时试玩，结束后通常需要购买')
        out+=f'<p><strong>{safe(o["name"])}</strong> · {label}<br>{safe(o["note"])}<br><a href="{url}">去 Steam 看看 →</a></p>\n\n'
    return out

def issue_link(action):
    return REPO+'/issues/new?'+urlencode({'title':action,'body':'标题已经填好，直接点绿色的「Submit new issue」（提交）。\n等这条记录自动关闭，再回首页刷新。'})

def render(state):
    f=state['frog'];e=f['history'][-1];box=state['box'];site=box['site'];day=f['day']
    assets=ROOT/'assets';assets.mkdir(exist_ok=True)
    welcome=art.hero()
    welcome_version=hashlib.sha256(welcome.encode('utf-8')).hexdigest()[:12]
    (assets/'welcome.svg').write_text(welcome,encoding='utf-8')
    (assets/f'welcome-{welcome_version}.svg').write_text(welcome,encoding='utf-8')
    (assets/'frog.svg').write_text(art.postcard(e,len(f['history']),f['energy']),encoding='utf-8')
    (assets/'footprints.svg').write_text(art.footprints(f['history']),encoding='utf-8')
    # Today's card can reflect feeding; previous days remain archived.
    (ROOT/'postcards'/f'{day}.svg').write_text(art.postcard(e,len(f['history']),f['energy']),encoding='utf-8')
    frog_version=hashlib.sha256((assets/'frog.svg').read_bytes()).hexdigest()[:12]
    (assets/f'frog-{frog_version}.svg').write_bytes((assets/'frog.svg').read_bytes())
    diary='# 小呱的旅行相册\n\n留着小呱一路带回来的明信片。\n\n[回首页](https://github.com/'+OWNER+')\n\n'
    for old in reversed(f['history']):
        card_version=hashlib.sha256((ROOT/'postcards'/f'{old["date"]}.svg').read_bytes()).hexdigest()[:12]
        (assets/f'frog-{card_version}.svg').write_bytes((ROOT/'postcards'/f'{old["date"]}.svg').read_bytes())
        diary+=f'## {old["date"]} · {old["place"]}\n\n![{old["place"]}](assets/frog-{card_version}.svg)\n\n{old["diary"]}\n\n纪念品：{old["souvenir"]}\n\n'
    (ROOT/'旅行相册.md').write_text(diary,encoding='utf-8')
    status=f'北京时间 {state["updated_at"]}'
    md=f'''<p align="center"><img src="{RAW}/assets/welcome-{welcome_version}.svg" alt="我的首页" width="100%"></p>

<p align="center"><a href="#steam">🎮 捡游戏</a>　·　<a href="#frog">🐸 看小呱</a>　·　<a href="#box">🎁 拆盲盒</a>　·　<a href="#snake">🐍 看贪吃蛇</a>　·　<a href="{REPO}/blob/main/使用指南.md">📖 操作备忘</a></p>

> 上次更新：{status} · 每天 08:17 自动更新。

<a id="steam"></a>
## 🎮 Steam 免费游戏雷达

有想玩的就点进商店，记得在活动结束前领取。

'''
    md+=section('🎁 限时领取 · 永久保留',state.get('steam',{}).get('keep',{}))
    md+=section('⏳ 免费周末 · 限时试玩',state.get('steam',{}).get('trial',{}))
    md+='国区商店结果，可能有遗漏；领取资格和截止时间以登录后的 Steam 页面为准。\n\n'
    md+=f'''<a id="frog"></a>
## 🐸 小呱的慢旅行

![小呱今天的明信片]({RAW}/assets/frog-{frog_version}.svg)

**体力：{f['energy']}/100**　·　**旅行：{f['travel_count']} 次**　·　**明天：{'在家休息' if f.get('rest_next') else '体力够就出发'}**

今天{'已喂过' if f.get('fed_day') == day else '还没喂'}。

[🍙 喂小呱]({issue_link('喂小呱')})　[🏡 明天休息]({issue_link('明天休息')})　[🎒 明天出发]({issue_link('明天出发')})　[📮 翻旅行相册]({REPO}/blob/main/旅行相册.md)

<sub>点完操作，还要在下一页点绿色的「Submit new issue」（提交），再回来刷新。每天喂一次就够，不喂也会自己休息。</sub>

![最近的旅行足迹]({RAW}/assets/footprints.svg?v={day})

<a id="box"></a>
## 🎁 今日网站盲盒

**{box['date']}**　·　提示：**{site['hint']}**

<details>
<summary>拆开看看</summary>

### {site['name']}

**{site['tag']}** · {site['how']}

[🚀 打开今天的网站]({site['url']})

每天换一个，一轮抽完再重复。遇到英文就用浏览器翻译。

</details>

<a id="snake"></a>
## 🐍 我的贡献贪吃蛇

'''
    if (assets/'snake.svg').exists():
        snake_version=hashlib.sha256((assets/'snake.svg').read_bytes()).hexdigest()[:12]
        (assets/f'snake-{snake_version}.svg').write_bytes((assets/'snake.svg').read_bytes())
        (assets/f'snake-dark-{snake_version}.svg').write_bytes((assets/'snake-dark.svg').read_bytes())
        md+=f'''<picture>
  <source media="(prefers-color-scheme: dark)" srcset="{RAW}/assets/snake-dark-{snake_version}.svg">
  <img alt="贪吃蛇正在吃我的真实 GitHub 贡献格子" src="{RAW}/assets/snake-{snake_version}.svg" width="100%">
</picture>

更新于 {state.get('snake_day','等待更新')} · 看看最近的贡献格子。
'''
    else:md+='动画还没生成，等下一次更新。\n'
    md+=f'''
<sub>动画来源：<a href="https://github.com/Platane/snk">Platane/snk</a></sub>

---

[操作备忘]({REPO}/blob/main/使用指南.md)　|　[运行记录]({REPO}/actions)　|　[现在更新一次]({issue_link('更新主页')})

'''
    (ROOT/'README.md').write_text(md,encoding='utf-8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--render-only',action='store_true');p.add_argument('--snake-complete',action='store_true');a=p.parse_args()
    now=datetime.now(CN);today=now.date().isoformat();state=read(Path('data/state.json'),{})
    if not a.render_only:
        mode=os.getenv('PLAY_ACTION','更新主页') or '更新主页'
        if mode not in ACTIONS:raise ValueError('不支持的操作')
        state['frog']=daily_frog(state.get('frog',{}),today,mode)
        state['box']=daily_box(state.get('box',{}),today,read(Path('data/websites.json'),[]))
        if mode == '更新主页':
            state['steam']=steam.refresh(state.get('steam',{}))
        state['updated_at']=now.strftime('%Y-%m-%d %H:%M')
    if a.snake_complete:state['snake_day']=today
    render(state);save(Path('data/state.json'),state)
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as out:out.write('snake='+('true' if state.get('snake_day')!=today or not (ROOT/'assets/snake.svg').exists() else 'false')+'\n')
    print(json.dumps({'message':state['frog']['message'],'date':today,'cards':len(state['frog']['history']),
        'steam':{k:{'ok':v.get('ok'), 'count':len(v.get('offers',[]))} for k,v in state.get('steam',{}).items()}},ensure_ascii=False))
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as out:out.write(f'### 更新结果\n\n{state["frog"]["message"]}\n\n[打开个人主页](https://github.com/{OWNER})\n')

if __name__=='__main__':main()
