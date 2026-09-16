"""Steam-only radar. Public store reads; never logs in or claims games."""
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

STORE = 'https://store.steampowered.com'
CN = timezone(timedelta(hours=8))
SESSION = requests.Session()
SESSION.headers['User-Agent'] = 'Mozilla/5.0 (compatible; PersonalSteamRadar/1.0)'
SESSION.mount('https://', HTTPAdapter(max_retries=Retry(total=2, backoff_factor=0.5, status_forcelist=[429,500,502,503,504])))

def get(path, **params):
    r = SESSION.get(STORE + path, params={'cc':'cn', 'l':'schinese', **params}, timeout=(8,25))
    r.raise_for_status()
    r.encoding = 'utf-8'
    return r

def appid(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.hostname != 'store.steampowered.com':
        return None
    m = re.fullmatch(r'/app/(\d+)(?:/[^/]*)?/?', u.path)
    return m.group(1) if m else None

def parse_search(payload):
    if not isinstance(payload, dict) or 'results_html' not in payload or 'total_count' not in payload:
        raise ValueError('Steam 搜索结构变化')
    soup = BeautifulSoup(payload['results_html'], 'html.parser')
    rows = soup.select('a.search_result_row')
    if int(payload['total_count']) > 0 and not rows:
        raise ValueError('Steam 搜索未返回可识别条目')
    result = []
    for row in rows:
        key = appid(row.get('href',''))
        pct = row.select_one('.discount_pct')
        if key and pct and pct.get_text(strip=True) in ('-100%', '100%'):
            result.append(key)
    return result

def purchase_offer(html, kind):
    soup = BeautifulSoup(html, 'html.parser')
    areas = soup.select('.game_area_purchase_game')
    if not areas:
        raise ValueError('商店购买区域无法识别，可能是地区或年龄限制')
    for area in areas:
        text = area.get_text(' ', strip=True)
        if kind == 'keep':
            # Do not infer ownership from zero price: trials and F2P are different.
            note = area.select_one('.game_purchase_discount_quantity')
            if note and re.search(r'免费保留|keep it forever|keep forever|keep for free|free to keep', note.get_text(' ',strip=True), re.I):
                return re.sub(r'\s+', ' ', note.get_text(' ',strip=True)).replace(' (?)','')[:260]
        elif re.search(r'免费周末|免费试玩|免费畅玩.*(?:剩余|截止)|play for free[^.]*!|free weekend',text,re.I):
            return '限时试玩，结束后通常需要购买；具体结束时间见商店页面。'
    return None

def details(key):
    item = get('/api/appdetails', appids=key).json().get(key,{})
    if not item.get('success'):
        raise ValueError('Steam 商品资料暂不可用')
    return item['data']

def keep_offers():
    keys = set()
    for start in range(0,500,100):
        payload = get('/search/results/', query='', start=start, count=100, specials=1, maxprice='free', infinite=1).json()
        keys.update(parse_search(payload))
        if start + 100 >= int(payload['total_count']):
            break
    else:
        raise ValueError('结果过多，需调整分页范围')
    offers=[]
    for key in sorted(keys):
        d = details(key)
        # Ignore movies, software, soundtracks and demos; game DLC can be free too.
        if d.get('type') not in ('game','dlc'):
            continue
        note = purchase_offer(get('/app/'+key+'/').text,'keep')
        if note:
            offers.append({'id':key, 'name':d['name'], 'kind':'keep', 'note':note,
                           'url':STORE+'/app/'+key+'/?cc=cn&l=schinese', 'dlc':d.get('type')=='dlc'})
    return offers

def trial_candidates(payload):
    if not isinstance(payload,dict) or 'specials' not in payload:
        raise ValueError('Steam 推荐栏结构变化')
    found = {}
    for section in payload.values():
        if not isinstance(section,dict):
            continue
        for item in section.get('items',[]):
            text = ' '.join(str(item.get(k,'')) for k in ('name','body','header','subheader'))
            if not re.search(r'free weekend|play for free|免费周末|免费试玩', text, re.I):
                continue
            key = appid(item.get('url',''))
            if not key and str(item.get('id','')).isdigit() and item.get('type') == 0:
                key = str(item['id'])
            if key:
                found[key]=item
    return found

def trial_offers():
    # English is used internally to detect stable campaign labels; UI stays Chinese.
    payload = get('/api/featuredcategories/', l='english').json()
    offers=[]
    for key,item in trial_candidates(payload).items():
        d = details(key)
        if d.get('type') != 'game':
            continue
        # The official featured campaign explicitly says Free Weekend / Play For Free.
        expiry=item.get('discount_expiration')
        if expiry and int(expiry) <= int(datetime.now(timezone.utc).timestamp()):
            continue
        offers.append({'id':key,'name':d['name'],'kind':'trial',
            'note':'Steam 官方推荐栏标为限时试玩；结束时间和地区资格请打开商店确认。',
            'url':STORE+'/app/'+key+'/?cc=cn&l=schinese'})
    return offers

def update_section(previous, fetch, now):
    try:
        return {'ok':True,'checked_at':now,'success_at':now,'offers':fetch()}
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        # Keep last-known records visibly stale, never turn network failure into "no offers".
        return {**previous, 'ok':False,'checked_at':now,'error':type(exc).__name__,
                'offers':previous.get('offers',[])}

def refresh(previous):
    now = datetime.now(CN).strftime('%Y-%m-%d %H:%M')
    return {'keep':update_section(previous.get('keep',{}),keep_offers,now),
            'trial':update_section(previous.get('trial',{}),trial_offers,now)}
