"""Convert hljcg data to same format as scraper.py output for build_html.py integration"""
import json, os, re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE_DIR, 'hljcg_jixi_full.json')
DST = os.path.join(BASE_DIR, 'hljcg_budget.json')

KEYWORDS = ['鸡西','鸡冠','恒山','鸡东','城子河','梨树','麻山','密山','虎林','珍宝岛','兴凯湖']
DISTRICTS = ['鸡冠区','恒山区','滴道区','梨树区','城子河区','麻山区','鸡东县','虎林市','密山市']

def extract_region(title, purchaser):
    """Try to determine district from title or purchaser"""
    for d in DISTRICTS:
        if d in title or d in purchaser:
            return d
    return '鸡西市本级'

_CAT_RULES = [
    (r'维(修|护|保)|养护|运维|值守|检修|物业|保安|保洁|托管|监理|运行维护|保养|修缮', '维保'),
    (r'软件|系统|平台|信息化|网络|数据|信息|智能|智慧|电子|数字化|小程序|APP|数据库|云(?!计|南|雾)|源代码|定制开发', '信息化软件'),
    (r'集(成|采)|一体化|综合(?!执|行|治)|弱电|安防|智能化|指挥(中心|平台)|协同(平台|作战)', '集成'),
    (r'设备|硬件|电脑|笔记本|服务器|打印机|扫描|复印|投影|大屏|LED|监控|摄像头|交换机|路由器|防火墙|存储|UPS|空调|家具|办公桌|办公椅|柜|门|窗|床|车辆|汽车|仪器|试剂|药品|医疗|机', '硬件'),
]

def classify(title):
    for pat, cat in _CAT_RULES:
        if re.search(pat, title):
            return cat
    return '其他'

def build_detail_url(i, title, purchaser, publish_date, budget_raw):
    """Build URL to our detail.html page that fetches hljcg content via API"""
    from urllib.parse import urlencode, quote
    params = {
        'noticeId': i.get('noticeId', ''),
        'title': title,
        'region': extract_region(title, purchaser),
        'budget': budget_raw or '',
        'noticeType': i.get('noticeType', ''),
        'purchaser': purchaser,
        'time': publish_date,
        'openTenderTime': i.get('openTenderTime', ''),
    }
    # Use shorter query: only pass what detail.html actually needs
    q = urlencode(params, quote_via=quote)
    return f'detail.html?{q}'

def normalize_amount(amount_str):
    """Amount is already in yuan in hljcg api, convert to 万元"""
    if not amount_str:
        return ''
    try:
        val = float(str(amount_str).replace(',','').replace(' ',''))
        # hljcg API returns amount in yuan
        return f'{val/10000:.2f}万元'
    except:
        return str(amount_str)

def parse_time(raw):
    """Parse various time formats from hljcg API"""
    if not raw:
        return ''
    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d']:
        try:
            return datetime.strptime(str(raw)[:19], fmt).strftime('%Y-%m-%d')
        except:
            continue
    return str(raw)[:10] if len(str(raw)) >= 10 else str(raw)

with open(SRC, 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data.get('items', [])

# Filter to 鸡西 only
jixi = []
for i in items:
    rn = i.get('regionName','')
    tl = i.get('title','')
    pur = i.get('purchaser','')
    if any(k in rn or k in tl or k in pur for k in KEYWORDS):
        jixi.append(i)

print(f'Filtered to {len(jixi)} 鸡西 items')

converted = []
for i in jixi:
    title = i.get('title','').strip()
    purchaser = i.get('purchaser','').strip()
    budget_raw = i.get('budget','')
    notice_type = i.get('noticeTypeName','') or '采购公告'
    publish_date = i.get('publishDate','') or i.get('publishTime','') or i.get('noticeTime','')

    item = {
        'title': title,
        'url': build_detail_url(i, title, purchaser, publish_date, budget_raw),
        'time': parse_time(publish_date),
        'buyer': purchaser,
        'type': notice_type if notice_type else '采购公告',
        'region': extract_region(title, purchaser),
        'agency': i.get('agency','') or '',
        'addr': '',
        'budget': normalize_amount(budget_raw) if budget_raw else '',
        'category': classify(title),
        'source': 'hljcg',
        'contentId': i.get('id','') or i.get('noticeId',''),
    }
    converted.append(item)

print(f'Converted {len(converted)} items')

with open(DST, 'w', encoding='utf-8') as f:
    json.dump({'source': 'hljcg.hlj.gov.cn', 'updated_at': data.get('updated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')), 'total': len(converted), 'items': converted}, f, ensure_ascii=False, indent=2)

print(f'Saved to {DST}')
print(f'File size: {os.path.getsize(DST)} bytes')

# Quick stats
budgets = sum(1 for i in converted if i.get('budget'))
categories = {}
regions = {}
for i in converted:
    c = i.get('category','')
    r = i.get('region','')
    categories[c] = categories.get(c,0)+1
    regions[r] = regions.get(r,0)+1
print(f'With budget: {budgets}')
print(f'Categories: {json.dumps(categories, ensure_ascii=False)}')
print(f'Regions: {json.dumps(regions, ensure_ascii=False)}')
