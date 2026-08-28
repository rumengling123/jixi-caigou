"""
Final working scraper for hljcg budget data from qianlima.com.
bodyData only has metadata; budget is ONLY in detail pages (/bid-NNN.html).
Strategy:
1. Extract jixi bid URLs from bodyData (structured) or HTML links (fallback)  
2. Fetch detail pages for budget amount + buyer
"""
import requests, re, json, os, time, random

requests.packages.urllib3.disable_warnings()

JIXI_KW = ['鸡西','鸡冠','恒山','鸡东','城子河','梨树','麻山','密山','虎林','珍宝岛','兴凯湖','滴道']

def strip_html(t): return re.sub(r'<[^>]+>', '', t)
def is_jixi(t): return any(k in t for k in JIXI_KW)

def extract_budget(text):
    """Extract budget/contract amount from detail page HTML. Returns formatted string."""
    if not text: return ''
    t = strip_html(text)
    
    # Try budget first
    for pat in [
        r'预算金额\s*[¥￥]?\s*(\d[\d,.]*)\s*(?:万[元]?|[元圆])',
        r'预算金额[：:]\s*[¥￥]?\s*(\d[\d,.]*)\s*(?:万[元]?|[元圆])',
        r'采购预算\s*[¥￥]?\s*(\d[\d,.]*)\s*(?:万[元]?|[元圆])',
    ]:
        m = re.search(pat, t)
        if m:
            v = m.group(1).replace(',','')
            n = float(v)
            # If already in 万元 (>500 means it's in yuan, convert)
            if n > 500: n = n / 10000
            return f'{n:.2f}万元'
    
    # Then try zhongbiao/chengjiao/hetong amount
    for pat in [
        r'中标[（(]成交[）)][金额]?\s*[：:]?\s*[¥￥]?\s*(\d[\d,.]*)\s*(?:万[元]?|[元圆])',
        r'中标金额[：:]\s*[¥￥]?\s*(\d[\d,.]*)\s*(?:万[元]?|[元圆])',
        r'成交金额[：:]\s*[¥￥]?\s*(\d[\d,.]*)\s*(?:万[元]?|[元圆])',
        r'合同金额[：:]\s*[¥￥]?\s*(\d[\d,.]*)\s*(?:万[元]?|[元圆])',
    ]:
        m = re.search(pat, t)
        if m:
            v = m.group(1).replace(',','')
            n = float(v)
            if n > 500: n = n / 10000
            return f'{n:.2f}万元'
    
    return ''

def extract_buyer(html):
    if not html: return ''
    t = strip_html(html)
    for pat in [
        r'采购单人名?\s*[：:]\s*([^\s,，。；<>（）\d]{3,30})',
        r'采购单位?\s*[：:]\s*([^\s,，。；<>（）\d]{3,30})',
        r'招标单位?\s*[：:]\s*([^\s,，。；<>（）\d]{3,30})',
        r'采购人?\s*[：:]\s*([^\s,，。；<>（）\d]{3,30})',
    ]:
        m = re.search(pat, t)
        if m:
            b = m.group(1).strip().rstrip('，,。.)）')
            if len(b)>=3: return b
    return ''

def classify_region(t):
    for kw,r in [('鸡冠','鸡冠区'),('恒山','恒山区'),('鸡东','鸡东县'),
                  ('城子河','城子河区'),('梨树','梨树区'),('麻山','麻山区'),
                  ('密山','密山市'),('虎林','虎林市'),('滴道','滴道区')]:
        if kw in t: return r
    return '鸡西市本级'

def classify_type(t):
    for kw,pt in [('意向','采购意向'),('需求','需求公示'),('合同','合同公告'),
                   ('中标','中标公告'),('成交','中标公告'),('结果','中标公告'),
                   ('验收','合同公告'),('招标','招标公告')]:
        if kw in t: return pt
    return '其他公告'

def classify_cat(t):
    t = t.lower()
    if any(k in t for k in ['维保','运维','维护','保修','保养']): return '维保集成'
    if any(k in t for k in ['软件','系统','平台','信息化','数字','智慧']): return '信息化建设'
    if any(k in t for k in ['设备','硬件','打印机','电脑','服务器','网络']): return '硬件采购'
    return '其他'

def extract_bids_from_static(html):
    """Extract bid items from bodyData array in _STATIC_DATA_"""
    items = []
    
    # Find "bodyData":[
    pos = html.find('"bodyData":[', 0)
    if pos < 0:
        pos = html.find('bodyData:[', 0)
    if pos < 0:
        return items
    
    # Skip to after [
    bracket = html.find('[', pos)
    if bracket < 0:
        return items
    pos = bracket + 1
    
    # Track brackets to find matching ]
    depth = 1; end = pos
    in_str = False; esc = False
    
    for i in range(pos, min(pos + 200000, len(html))):
        ch = html[i]
        if esc: esc = False; continue
        if ch == '\\': esc = True; continue
        if in_str:
            if ch == '"': in_str = False
            continue
        if ch == '"': in_str = True; continue
        if ch == '[': depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0: end = i; break
    
    arr_text = html[pos:end]
    
    # Find all top-level objects
    obj_starts = []
    depth = 0; in_str = False; esc = False
    
    for i, ch in enumerate(arr_text):
        if esc: esc = False; continue
        if ch == '\\': esc = True; continue
        if in_str:
            if ch == '"': in_str = False
            continue
        if ch == '"': in_str = True; continue
        if ch == '{':
            if depth == 0: obj_starts.append(i)
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0: obj_starts.append(-i)
    
    starts = [p for p in obj_starts if p >= 0]
    ends = [-p for p in obj_starts if p < 0]
    
    for s, e in zip(starts, ends):
        obj_str = arr_text[s:e+1]
        
        cid_m = re.search(r'"contentid":\s*(\d+)', obj_str)
        if not cid_m: continue
        
        item = {'contentid': cid_m.group(1)}
        
        title_m = re.search(r'"title":\s*"((?:[^"\\]|\\.)*)"', obj_str)
        item['title'] = strip_html(title_m.group(1)) if title_m else ''
        
        time_m = re.search(r'"inputtime":\s*"([^"]*)"', obj_str)
        item['inputtime'] = time_m.group(1) if time_m else ''
        
        url_m = re.search(r'"url":\s*"([^"]*)"', obj_str)
        item['url'] = url_m.group(1) if url_m else f'https://www.qianlima.com/bid-{item["contentid"]}.html'
        
        items.append(item)
    
    return items

def extract_bids_from_links(html):
    """Fallback: extract bid links from HTML <a> tags"""
    items = []
    # Find all /bid-NNN.html links
    for m in re.finditer(r'/bid-(\d+)\.html', html):
        bid_id = m.group(1)
        idx = m.start()
        # Find nearby <a> tag text
        # Look backwards for <a ...> and forwards for </a>
        pre = html[max(0,idx-500):idx]
        post = html[idx:idx+200]
        
        title_m = re.search(r'<a[^>]*>([\s\S]*?)</a>', pre + post)
        if title_m:
            title = strip_html(title_m.group(1))
            if title:
                items.append({'contentid': bid_id, 'title': title, 'inputtime': ''})
                continue
        
        # Try simpler: just get link text
        a_match = re.search(r'<a\s+[^>]*href="[^"]*bid-' + bid_id + r'[^"]*"[^>]*>([\s\S]*?)</a>', html[max(0,idx-200):idx+300])
        if a_match:
            items.append({'contentid': bid_id, 'title': strip_html(a_match.group(1)), 'inputtime': ''})
    
    return items

# ========== Main ==========
s = requests.Session(); s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'zh-CN,zh;q=0.9',
})

hot_pages = [
    (1700955,'财政局'),(520955,'政府采购'),(30955,'采购平台'),
    (3750955,'在建'),(3830955,'招标'),(2930955,'采购网'),
    (2620955,'政府'),(1940955,'公安'),(840955,'教育'),
    (80955,'交易中心'),(440955,'人社'),
]

candidates = {}  # bid_id -> basic info
seen = set()

for hot_id, label in hot_pages:
    try:
        r = s.get(f'https://www.qianlima.com/hot{hot_id}/', timeout=25)
        if r.status_code != 200:
            print(f'{label}: HTTP {r.status_code}')
            time.sleep(2); continue
        
        # Try static extraction first
        items = extract_bids_from_static(r.text)
        
        if not items:
            items = extract_bids_from_links(r.text)
            print(f'  [{label}] links: {len(items)}')
        else:
            print(f'  [{label}] static: {len(items)}')
        
        count = 0
        for item in items:
            title = item.get('title', '')
            if not title or not is_jixi(title):
                continue
            cid = item.get('contentid', '')
            if cid in seen:
                continue
            seen.add(cid)
            
            candidates[cid] = {
                'url': f'https://www.qianlima.com/bid-{cid}.html',
                'title': title,
                'region': classify_region(title),
                'time': item.get('inputtime', ''),
                'budget': '',
                'buyer': '',
                'type': classify_type(title),
                'category': classify_cat(title),
                'source': 'hljcg',
            }
            count += 1
        
        print(f'  [{label}] jixi: {count}')
        time.sleep(random.uniform(0.8, 1.5))
    except Exception as e:
        print(f'{label}: ERROR {e}')
        time.sleep(2)

print(f'\n=== Phase 1: {len(candidates)} bids ===')

# Phase 2: Detail pages
candidates_list = list(candidates.values())
budget_filled = 0

for i, item in enumerate(candidates_list):
    try:
        ses = requests.Session(); ses.verify = False
        ses.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://www.qianlima.com/',
        })
        r = ses.get(item['url'], timeout=20)
        ses.close()
        
        if r.status_code == 200:
            b = extract_budget(r.text)
            buyer = extract_buyer(r.text)
            if b: item['budget'] = b; budget_filled += 1
            if buyer and not item['buyer']: item['buyer'] = buyer
    except: pass
    
    if (i+1) % 25 == 0:
        print(f'  Detail: {i+1}/{len(candidates_list)}, budget: {budget_filled}')
    time.sleep(random.uniform(0.15, 0.4))

final = sorted(candidates_list, key=lambda x: x['time'], reverse=True)
base_dir = os.path.dirname(os.path.abspath(__file__))
output = os.path.join(base_dir, 'hljcg_budget.json')

with open(output, 'w', encoding='utf-8') as f:
    json.dump(final, f, ensure_ascii=False, indent=2)

with_b = [it for it in final if it['budget']]
print(f'\n=== Done: Total {len(final)}, Budget {len(with_b)} ===')

from collections import Counter
print(f'Types: {dict(Counter(it["type"] for it in final))}')
print(f'Regions: {dict(Counter(it["region"] for it in final))}')

for it in with_b[:15]:
    print(f"  [{it['time'][:10]}] [{it['region']}] {it['title'][:60]} | {it['budget']} | {it['buyer'][:15]}")

print(f'Saved: {output}')
