"""hljcg API scraper - version with captcha renewal on failure"""
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

def fetch_all_with_renewal(op, verify_code, keyword, max_pages=500):
    """Fetch all pages for a keyword. Returns (items_start_idx, final_page, total, need_renewal)"""
    all_items = []
    result = try_query(op, verify_code, keyword, page=1, page_size=30)
    if result['code'] != '200':
        print(f'FAIL:{result["code"]}:{result.get("msg","")}')
        if result['code'] == '4009':
            return all_items, 0, 0, True  # captcha expired
        return all_items, 0, 0, False
    
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
                if result['code'] == '4009':
                    return all_items, page, total, True
                break
            rows = (result.get('data') or {}).get('rows', [])
            all_items.extend(rows)
            print(f'P{page}:{len(rows)}/{len(all_items)}')
            time.sleep(0.2)
        except Exception as e:
            print(f'P{page}:ERR:{e}')
            break
    return all_items, total_pages, total, False

# Main flow
keywords = ['鸡西', '鸡冠', '恒山', '鸡东', '城子河', '梨树', '麻山', '密山', '虎林', '珍宝岛', '兴凯湖']

# Try to load existing progress
progress_file = os.path.join(WORKDIR, 'hljcg_progress.json')
all_items = []
seen = set()
start_kw_idx = 0

if os.path.exists(progress_file):
    with open(progress_file, 'r', encoding='utf-8') as f:
        prog = json.load(f)
    existing_path = os.path.join(WORKDIR, 'hljcg_jixi_full.json')
    if os.path.exists(existing_path):
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        all_items = existing.get('items', [])
        for item in all_items:
            cid = item.get('contentId') or item.get('id') or item.get('title')
            seen.add(cid)
    start_kw_idx = prog.get('next_kw_idx', 0)
    print(f'RESUMING from keyword index {start_kw_idx}, {len(all_items)} items loaded')
else:
    print('STARTING fresh')

for ki in range(start_kw_idx, len(keywords)):
    kw = keywords[ki]
    
    # Get fresh captcha + code for each keyword to avoid expiry
    cj, op = download_captcha()
    print(f'CAPTCHA_DOWNLOADED for keyword: {kw}', flush=True)
    
    verify_code = sys.stdin.readline().strip()
    print(f'CODE:{verify_code}', flush=True)
    
    items, final_page, total, need_renewal = fetch_all_with_renewal(op, verify_code, kw)
    
    # If captcha expired mid-fetch, save progress and prompt for continuation
    if need_renewal:
        # Save partial results
        for item in items:
            cid = item.get('contentId') or item.get('id') or item.get('title')
            if cid not in seen:
                seen.add(cid)
                all_items.append(item)
        save_results(all_items, os.path.join(WORKDIR, 'hljcg_jixi_full.json'))
        print(f'{kw}: PARTIAL - captcha expired at page {final_page}/{total}, {len(items)} fetched, saved progress')
        
        # Re-download captcha and continue
        cj2, op2 = download_captcha()
        print(f'CAPTCHA_DOWNLOADED for keyword: {kw} (continue)', flush=True)
        verify_code2 = sys.stdin.readline().strip()
        print(f'CODE:{verify_code2}', flush=True)
        
        # Continue fetching remaining pages
        more_items = []
        total_pages = (total + 29) // 30
        for page in range(final_page, min(total_pages + 1, 501)):
            try:
                result = try_query(op2, verify_code2, kw, page=page, page_size=30)
                if result['code'] != '200':
                    print(f'P{page}:FAIL:{result["code"]}')
                    break
                rows = (result.get('data') or {}).get('rows', [])
                more_items.extend(rows)
                items.extend(rows)
                print(f'P{page}:{len(rows)}/{len(items)}')
                time.sleep(0.2)
            except Exception as e:
                print(f'P{page}:ERR:{e}')
                break
    
    # Deduplicate and add
    new = 0
    for item in items:
        cid = item.get('contentId') or item.get('id') or item.get('title')
        if cid not in seen:
            seen.add(cid)
            all_items.append(item)
            new += 1
    print(f'{kw}: {len(items)} total, {new} new, {len(all_items)} unique so far')
    
    # Save progress
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump({'next_kw_idx': ki + 1, 'total_items': len(all_items)}, f)
    save_results(all_items, os.path.join(WORKDIR, 'hljcg_jixi_full.json'))
    time.sleep(0.3)

# Final stats
budgets = sum(1 for i in all_items if i.get('budget'))
print(f'\nDone: {len(all_items)} items, {budgets} with budget')

# Cleanup progress file
os.remove(progress_file)
