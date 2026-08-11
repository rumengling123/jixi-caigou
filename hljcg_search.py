"""hljcg API scraper - search by title keyword to get ALL 鸡西 results"""
import urllib.request, urllib.parse, json, gzip, http.cookiejar, time, os, sys

WORKDIR = r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
}

SITE_ID = '94c965cc-c55d-4f92-8469-d5875c68bd04'
CHANNEL = 'c5bff13f-21ca-4dac-b158-cb40accd3035'

def download_captcha():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.open(urllib.request.Request('https://hljcg.hlj.gov.cn/maincms-web/noticeInformationHlj', headers=HEADERS), timeout=10).read()
    resp = op.open(urllib.request.Request('https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/index/getVerify', headers=HEADERS), timeout=10)
    cap_data = resp.read()
    cap_path = os.path.join(WORKDIR, 'cap_now.png')
    with open(cap_path, 'wb') as f:
        f.write(cap_data)
    print(f'CAP_OK:{len(cap_data)}', flush=True)
    return cj, op

def try_query(op, verify_code, keyword='', page=1, page_size=20):
    params = {
        'title': keyword, 'region': '', 'siteId': SITE_ID, 'channel': CHANNEL,
        'currPage': str(page), 'pageSize': str(page_size), 'noticeType': '00101',
        'cityOrArea': '', 'purchaseManner': '', 'openTenderCode': '',
        'purchaser': '', 'agency': '', 'purchaseNature': '',
        'operationStartTime': '', 'operationEndTime': '',
        'verifyCode': verify_code, 'selectTimeName': 'noticeTime',
        '_t': str(int(time.time() * 1000)),
    }
    url = 'https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/info/selectInfoForIndex?' + urllib.parse.urlencode(params)
    resp = op.open(urllib.request.Request(url, headers=HEADERS), timeout=15)
    data = resp.read()
    if resp.headers.get('Content-Encoding') == 'gzip':
        data = gzip.decompress(data)
    return json.loads(data)

def save_results(items, path):
    out = {'source': 'hljcg.hlj.gov.cn', 'fetched_at': time.strftime('%Y-%m-%d %H:%M:%S'), 'total': len(items), 'items': items}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f'SAVED:{len(items)} -> {path}')

def fetch_all(op, verify_code, keyword, max_pages=500):
    all_items = []
    result = try_query(op, verify_code, keyword, page=1, page_size=30)
    if result['code'] != '200':
        print(f'FAIL:{result["code"]}:{result.get("msg","")}')
        return all_items, result
    
    total = (result.get('data') or {}).get('total', 0)
    rows = (result.get('data') or {}).get('rows', [])
    all_items.extend(rows)
    print(f'P1:{len(rows)}/{total}')
    
    total_pages = (total + 29) // 30
    for page in range(2, min(total_pages + 1, max_pages + 1)):
        try:
            result = try_query(op, verify_code, keyword, page=page, page_size=30)
            if result['code'] != '200':
                print(f'P{page}:FAIL:{result["code"]}')
                break
            rows = (result.get('data') or {}).get('rows', [])
            all_items.extend(rows)
            print(f'P{page}:{len(rows)}/{len(all_items)}')
            time.sleep(0.2)
        except Exception as e:
            print(f'P{page}:ERR:{e}')
            break
    return all_items, result

# Main flow: download captcha, wait for code, fetch all
cj, op = download_captcha()

# Read verify code
verify_code = sys.stdin.readline().strip()
print(f'CODE:{verify_code}')

# Fetch all with keyword search
all_items = []

# Search by each keyword to get complete coverage
keywords = ['鸡西', '鸡冠', '恒山', '鸡东', '城子河', '梨树', '麻山', '密山', '虎林', '珍宝岛', '兴凯湖']
seen = set()
for kw in keywords:
    items, result = fetch_all(op, verify_code, kw)
    if result.get('code') != '200':
        print(f'Captcha expired during {kw}, got {len(items)} items')
        break
    new = 0
    for item in items:
        cid = item.get('contentId') or item.get('id') or item.get('title')
        if cid not in seen:
            seen.add(cid)
            all_items.append(item)
            new += 1
    print(f'{kw}: {len(items)} total, {new} new, {len(all_items)} unique so far')
    time.sleep(0.3)

save_results(all_items, os.path.join(WORKDIR, 'hljcg_jixi_full.json'))

# Stats
budgets = sum(1 for i in all_items if i.get('budget'))
print(f'\nDone: {len(all_items)} items, {budgets} with budget')
