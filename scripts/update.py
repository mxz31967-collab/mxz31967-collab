"""Build a Chinese GitHub profile from real Steam reads and a tiny virtual pet."""
import argparse, hashlib, json, os, random
from pathlib import Path
from datetime import datetime, timezone, timedelta
from html import escape
from urllib.parse import urlencode
import steam, art

ROOT=Path(__file__).resolve().parents[1]
OWNER='mxz31967-collab'
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
        out+=f'> 本轮读取失败，下面可能是旧结果。上次成功：{safe(last)}。请到商店核对，勿当作正在生效的优惠。\n\n'
    else:out+=f'检查时间：{safe(section["checked_at"])}（北京时间）\n\n'
    offers=section.get('offers',[])
    if not offers:
        return out+('当前监测范围内暂未发现此类活动。\n\n' if section.get('ok') else '暂时没有可展示的已验证数据。\n\n')
    for o in offers:
        url=f'https://store.steampowered.com/app/{int(o["id"])}/?cc=cn&amp;l=schinese'
        label='游戏附加内容，可能需要本体' if o.get('dlc') else ('领取后永久保留' if o['kind']=='keep' else '限时试玩，结束后通常需要购买')
        out+=f'<p><strong>{safe(o["name"])}</strong> · {label}<br>{safe(o["note"])}<br><a href="{url}">打开 Steam 中文商店 →</a></p>\n\n'
    return out

def issue_link(action):
    return REPO+'/issues/new?'+urlencode({'title':action,'body':'点击下方绿色的「Submit new issue」（提交）按钮即可。\n机器人只接受主页主人发起的操作；完成后会自动关闭这条记录。'})

def render(state):
    f=state['frog'];e=f['history'][-1];box=state['box'];site=box['site'];day=f['day']
    assets=ROOT/'assets';assets.mkdir(exist_ok=True)
    (assets/'welcome.svg').write_text(art.hero(),encoding='utf-8')
    (assets/'frog.svg').write_text(art.postcard(e,len(f['history']),f['energy']),encoding='utf-8')
    (assets/'footprints.svg').write_text(art.footprints(f['history']),encoding='utf-8')
    # Today's card can reflect feeding; previous days remain archived.
    (ROOT/'postcards'/f'{day}.svg').write_text(art.postcard(e,len(f['history']),f['energy']),encoding='utf-8')
    frog_version=hashlib.sha256((assets/'frog.svg').read_bytes()).hexdigest()[:12]
    (assets/f'frog-{frog_version}.svg').write_bytes((assets/'frog.svg').read_bytes())
    diary='# 小呱的旅行相册\n\n这是一只程序养的小青蛙，旅行、纪念品和日记都是虚拟内容。\n\n[返回个人主页](https://github.com/'+OWNER+')\n\n'
    for old in reversed(f['history']):
        card_version=hashlib.sha256((ROOT/'postcards'/f'{old["date"]}.svg').read_bytes()).hexdigest()[:12]
        (assets/f'frog-{card_version}.svg').write_bytes((ROOT/'postcards'/f'{old["date"]}.svg').read_bytes())
        diary+=f'## {old["date"]} · {old["place"]}\n\n![{old["place"]}](assets/frog-{card_version}.svg)\n\n{old["diary"]}\n\n纪念品：{old["souvenir"]}\n\n'
    (ROOT/'旅行相册.md').write_text(diary,encoding='utf-8')
    status=f'北京时间 {state["updated_at"]}'
    md=f'''<p align="center"><img src="{RAW}/assets/welcome.svg" alt="我的 GitHub 小乐园" width="100%"></p>

<p align="center"><a href="#steam">🎮 捡游戏</a>　·　<a href="#frog">🐸 看小呱</a>　·　<a href="#box">🎁 拆盲盒</a>　·　<a href="#snake">🐍 看贪吃蛇</a>　·　<a href="{REPO}/blob/main/使用指南.md">📖 中文使用指南</a></p>

> 最近更新：{status}。平时打开这个主页就能看；Steam 活动需要你自己到商店领取或启动试玩。

<a id="steam"></a>
## 🎮 Steam 免费游戏雷达

只看 Steam。优先显示商店提供的中文名；没有中文名时保留原名，玩法与领取提示仍是中文。

'''
    md+=section('🎁 限时领取 · 永久保留',state.get('steam',{}).get('keep',{}))
    md+=section('⏳ 免费周末 · 限时试玩',state.get('steam',{}).get('trial',{}))
    md+='> 数据来自 Steam 国区公开商店：限免搜索与官方推荐栏，每 6 小时检查。不是全站无遗漏监测；优惠可能提前结束或有地区限制，以你登录后的商店为准。商店显示的截止时间按原文保留，不擅自换算时区。\n\n'
    md+=f'''<a id="frog"></a>
## 🐸 小呱的慢旅行

![小呱今天的明信片]({RAW}/assets/frog-{frog_version}.svg)

**体力：{f['energy']}/100**　·　**旅行：{f['travel_count']} 次**　·　**明天：{'在家休息' if f.get('rest_next') else '体力够就出发'}**

{f['message']}

[🍙 喂小呱]({issue_link('喂小呱')})　[🏡 明天休息]({issue_link('明天休息')})　[🎒 明天出发]({issue_link('明天出发')})　[📮 翻旅行相册]({REPO}/blob/main/旅行相册.md)

<sub>喂食或安排旅行：点入口，再点绿色的「Submit new issue」（提交）。仅主页主人可操作，通常稍等一会就会更新。每天只能喂一次；不喂也会自动休息。小呱是虚拟宠物，日记由程序从旅行素材中生成。</sub>

![最近的旅行足迹]({RAW}/assets/footprints.svg?v={day})

<a id="box"></a>
## 🎁 今日网站盲盒

**{box['date']}**　·　提示：**{site['hint']}**

<details>
<summary>✨ 点这里拆开今天的盲盒</summary>

### {site['name']}

**{site['tag']}** · {site['how']}

[🚀 打开今天的网站]({site['url']})

每天一个，整轮抽完之前不重复。外部网站可能含英文菜单，先照上面的中文说明玩就行。

</details>

<a id="snake"></a>
## 🐍 会吃格子的贪吃蛇

'''
    if (assets/'snake.svg').exists():
        snake_version=hashlib.sha256((assets/'snake.svg').read_bytes()).hexdigest()[:12]
        (assets/f'snake-{snake_version}.svg').write_bytes((assets/'snake.svg').read_bytes())
        (assets/f'snake-dark-{snake_version}.svg').write_bytes((assets/'snake-dark.svg').read_bytes())
        md+=f'''<picture>
  <source media="(prefers-color-scheme: dark)" srcset="{RAW}/assets/snake-dark-{snake_version}.svg">
  <img alt="贪吃蛇正在吃我的真实 GitHub 贡献格子" src="{RAW}/assets/snake-{snake_version}.svg" width="100%">
</picture>

最近生成：{state.get('snake_day','等待更新')}。这是根据 GitHub 贡献图生成的动画，每天更新；不是键盘控制的小游戏。
'''
    else:md+='动画正在准备，第一次云端生成后会自动出现在这里。\n'
    md+=f'''
<sub>动画使用开源项目 <a href="https://github.com/Platane/snk">Platane/snk</a>；只读取 GitHub 提供的贡献格子，不会伪造贡献。</sub>

---

**第一次玩 GitHub？** [点这里看中文使用指南]({REPO}/blob/main/使用指南.md)　|　[查看自动更新记录]({REPO}/actions)　|　[立即更新主页]({issue_link('更新主页')})

<sub>每天的小惊喜，慢慢来就好。</sub>
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
