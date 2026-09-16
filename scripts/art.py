"""Small original SVG illustrations; no external images or drawing API."""
from html import escape
FONT='system-ui,Segoe UI,Microsoft YaHei,PingFang SC,sans-serif'

def text(x,y,value,size=20,color='#203b38',weight='400'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(str(value))}</text>'

def frame(body,h=420,title='小呱的明信片'):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{h}" viewBox="0 0 1000 {h}" role="img" aria-label="{escape(title)}"><title>{escape(title)}</title><g font-family="{FONT}">{body}</g></svg>'

def frog(x=190,y=300,scale=1):
    return f'''<g transform="translate({x} {y}) scale({scale})">
    <ellipse cy="68" rx="88" ry="12" fill="#193c36" opacity=".14"/>
    <rect x="42" y="-3" width="40" height="59" rx="14" fill="#c48753" stroke="#73552f" stroke-width="3"/>
    <ellipse cy="17" rx="64" ry="51" fill="#6fac65"/>
    <ellipse cy="29" rx="44" ry="31" fill="#e8efb2"/>
    <ellipse cy="-22" rx="73" ry="44" fill="#92c77c"/>
    <circle cx="-40" cy="-54" r="26" fill="#92c77c"/><circle cx="40" cy="-54" r="26" fill="#92c77c"/>
    <ellipse cx="-40" cy="-56" rx="15" ry="19" fill="#fffbed"/><ellipse cx="40" cy="-56" rx="15" ry="19" fill="#fffbed"/>
    <ellipse cx="-36" cy="-54" rx="6" ry="10" fill="#203b38"/><ellipse cx="44" cy="-54" rx="6" ry="10" fill="#203b38"/>
    <ellipse cx="-49" cy="-13" rx="12" ry="6" fill="#eea79b"/><ellipse cx="49" cy="-13" rx="12" ry="6" fill="#eea79b"/>
    <path d="M-17 -17 Q0 -2 17 -17" fill="none" stroke="#355845" stroke-width="3" stroke-linecap="round"/>
    <path d="M-49 14 Q0 33 49 14 L43 29 Q0 44 -43 29Z" fill="#eab864"/>
    <path d="M30 27 L45 56 L27 60 L17 32Z" fill="#eab864"/>
    <ellipse cx="-42" cy="61" rx="28" ry="12" fill="#6fac65"/><ellipse cx="42" cy="61" rx="28" ry="12" fill="#6fac65"/>
    </g>'''

def postcard(entry, count, energy):
    kind=entry['scene']; sky={'snow':'#e4eff4','desert':'#f9ecd1','sea':'#ddf3f2','forest':'#e8f2dd'}.get(kind,'#e4f0e9')
    bg=f'<rect width="1000" height="430" rx="24" fill="#fcfaf3"/><rect width="480" height="430" rx="24" fill="{sky}"/>'
    bg+='<circle cx="390" cy="83" r="38" fill="#f6d37b"/><path d="M0 225 L110 92 L213 237 L320 116 L480 262 V430 H0Z" fill="#96b5a6"/><path d="M0 260 L155 184 L294 278 L420 222 L480 254 V430 H0Z" fill="#c1d4b1"/>'
    if kind in ('sea','lake'):
        bg+='<path d="M0 280 Q120 260 240 292 T480 290 V430 H0Z" fill="#99c6c5"/><path d="M310 320h90m-105 30h128m-90 30h70" stroke="#eaf8ed" stroke-width="3"/>'
    if kind=='desert':
        bg+='<path d="M0 250 Q130 140 290 285 T480 260 V430 H0Z" fill="#e0b983"/><path d="M0 320 Q180 220 480 345 V430 H0Z" fill="#ecd2a2"/>'
    if kind=='snow':
        bg+='<path d="M62 151 L110 92 L157 155 L128 145 L109 157 L91 138Z" fill="#fff"/><path d="M0 300Q250 230 480 300V430H0Z" fill="#fafdfc"/>'
    if kind in ('forest','city'):
        for x in (45,345,405):
            bg+=f'<path d="M{x} 220v75" stroke="#826a4e" stroke-width="8"/><ellipse cx="{x}" cy="205" rx="33" ry="47" fill="#6b997a"/>'
    bg+=frog(215,323,1.05)
    bg+=text(33,44,'小 呱 的 慢 旅 行',16,'#45645b','600')
    bg+=text(530,58,entry['date']+'  ·  虚拟旅行',16,'#71837a')
    bg+=text(528,116,entry['place'],37,weight='700')+text(530,150,entry['spot'],20,'#708377')
    diary=entry['diary']
    for n in range(0,len(diary),20): bg+=text(530,201+n//20*31,diary[n:n+20],19)
    bg+=text(530,323,'今日纪念品：'+entry['souvenir'],18,'#8a6637')
    bg+=text(530,366,f'第 {count} 张明信片    ·    体力 {energy}/100',17,'#6a7c72')
    bg+='<rect x="890" y="23" width="70" height="77" rx="5" stroke="#789d88" stroke-width="2" stroke-dasharray="4 4" fill="none"/>'+text(905,68,'呱',31,'#789d88')
    return frame(bg,430,entry['date']+' 小呱在'+entry['place'])

def hero():
    b='<rect width="1000" height="250" rx="24" fill="#173f3c"/><circle cx="920" cy="-60" r="230" fill="#285a50"/><circle cx="740" cy="260" r="130" fill="#204b43"/>'
    b+=text(52,56,'欢迎来到我的 GitHub 小乐园',18,'#bad9bf')+text(48,120,'捡游戏 · 养小呱 · 拆盲盒',39,'#fff8e8','700')
    b+=text(52,173,'给日常留一点小惊喜。',22,'#d8e8d5')+text(52,214,'Steam 游戏雷达  /  旅行明信片  /  贪吃蛇  /  每日网站',15,'#a7c9b4')+frog(876,163,.8)
    return frame(b,250,'我的 GitHub 小乐园')

def footprints(history):
    recent=history[-8:]; w=1000; body='<rect width="1000" height="145" rx="18" fill="#f1f5ee"/>'+text(24,32,'最近的旅行足迹 · 路线示意',15,'#6a7c72')
    for i,e in enumerate(recent):
        x=66+i*123
        if i:body+=f'<path d="M{x-107} 73H{x-17}" stroke="#b1c8b0" stroke-width="3" stroke-dasharray="5 4"/>'
        body+=f'<circle cx="{x}" cy="73" r="12" fill="#6f9c78"/>'+text(x-28,108,e['place'],14)+text(x-23,129,e['date'][5:],12,'#819181')
    return frame(body,145,'小呱旅行足迹')
