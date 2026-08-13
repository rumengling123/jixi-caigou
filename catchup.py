"""Catch up remaining keywords: 虎林, 珍宝岛, 兴凯湖"""
import json, os, sys, time, random
import requests
import urllib3
urllib3.disable_warnings()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS = ['虎林', '密山', '珍宝岛', '兴凯湖']
SITE_ID = '94c965cc-c55d-4f92-8469-d5875c68bd04'
CHANNEL_ID = 'c5bff13f-21ca-4dac-b158-cb40accd3035'
API_BASE = 'https://hljcg.hlj.gov.cn'
PAGE_SIZE = 100

# Read verify code
with open(os.path.join(BASE_DIR, 'hljcg_verify_code.txt'), 'r') as f:
    verify = f.read().strip()
print(f'Verify: {verify}')

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edg/151.0.0.0',
    'Accept': 'application/json',
    'Referer': f'{API_BASE}/maincms-web/noticeInformationHlj',
})
# Reuse WAF cookies saved by get_captcha.py so the verify code stays valid
cookie_file = os.path.join(BASE_DIR, 'hljcg_waf_cookies.json')
if os.path.exists(cookie_file):
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    for name, value in cookies.items():
        s.cookies.set(name, value, domain='hljcg.hlj.gov.cn')
    print(f'Loaded {len(cookies)} WAF cookie(s)')

# Load existing data
existing_file = os.path.join(BASE_DIR, 'hljcg_jixi_full.json')
with open(existing_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
all_items = data.get('items', [])
seen = {it.get('id','') or it.get('noticeId','') for it in all_items}
print(f'Existing: {len(all_items)} items, {len(seen)} unique IDs')

for kw in KEYWORDS:
    print(f'\nFetching: {kw}')
    page = 1
    kw_added = 0
    while True:
        params = {
            'title': kw,
            'region': '',
            'siteId': SITE_ID,
            'channel': CHANNEL_ID,
            'currPage': page,
            'pageSize': PAGE_SIZE,
            'noticeType': '00101',
            'verifyCode': verify,
            'selectTimeName': 'noticeTime',
            '_t': int(time.time() * 1000),
        }
        try:
            resp = s.get(f'{API_BASE}/gpcms/rest/web/v2/info/selectInfoForIndex',
                        params=params, verify=False, timeout=30)
            json_data = resp.json()
            code = json_data.get('code', '')
            if code == '4009':
                print(f'  Captcha expired at page {page}')
                break
            rows = json_data.get('data', {}).get('rows', [])
            total = json_data.get('data', {}).get('total', 0)
            if page == 1:
                print(f'  total={total} pages={-(-total//PAGE_SIZE)}')

            added = 0
            for it in rows:
                cid = it.get('id','') or it.get('noticeId','')
                if cid and cid not in seen:
                    seen.add(cid)
                    all_items.append(it)
                    added += 1
            kw_added += added

            if page * PAGE_SIZE >= total or not rows:
                break
            page += 1
            time.sleep(random.uniform(0.8, 1.5))
        except Exception as e:
            print(f'  ERROR: {e}')
            break
    print(f'  Added {kw_added} unique')

# Save merged
output = {
    'source': 'hljcg.hlj.gov.cn',
    'updated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
    'total': len(all_items),
    'items': all_items,
}
with open(existing_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False)
print(f'\nSaved {len(all_items)} total to hljcg_jixi_full.json ({os.path.getsize(existing_file)} bytes)')
