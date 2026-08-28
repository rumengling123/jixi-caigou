"""One-shot: download captcha, OCR immediately via base64 save, query API.
Flow: download captcha -> save as PNG -> wait for verify code file -> query
"""
import urllib.request, urllib.parse, json, gzip, http.cookiejar, time, sys, os, re

WORKDIR = r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi'
CAPTCHA_FILE = os.path.join(WORKDIR, 'hljcg_cap_latest.png')
CODE_FILE = os.path.join(WORKDIR, 'hljcg_verify_code.txt')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    'Accept': 'application/json, text/plain, */*',
}

SITE_ID = '94c965cc-c55d-4f92-8469-d5875c68bd04'
CHANNEL = 'c5bff13f-21ca-4dac-b158-cb40accd3035'
REGION = '230300'

def main():
    # Phase 1: Download captcha
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    # Visit homepage
    req = urllib.request.Request('https://hljcg.hlj.gov.cn/maincms-web/noticeInformationHlj', headers=HEADERS)
    op.open(req, timeout=10).read()
    
    # Get captcha
    req = urllib.request.Request('https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/index/getVerify', headers=HEADERS)
    resp = op.open(req, timeout=10)
    cap_data = resp.read()
    with open(CAPTCHA_FILE, 'wb') as f:
        f.write(cap_data)
    print(f"Captcha downloaded: {len(cap_data)} bytes")
    
    # Phase 2: Read verify code (user writes to CODE_FILE after OCR)
    # Wait up to 30 seconds
    if not os.path.exists(CODE_FILE):
        print("Waiting for verify code in hljcg_verify_code.txt...")
        for _ in range(60):
            time.sleep(1)
            if os.path.exists(CODE_FILE):
                break
    
    if not os.path.exists(CODE_FILE):
        print("Timeout waiting for verify code")
        return
    
    with open(CODE_FILE, 'r') as f:
        verify_code = f.read().strip()
    os.remove(CODE_FILE)
    print(f"Verify code: {verify_code}")
    
    # Phase 3: Query page 1 immediately with same cookie session
    params = {
        'title': '', 'region': REGION, 'siteId': SITE_ID, 'channel': CHANNEL,
        'currPage': '1', 'pageSize': '20', 'noticeType': '00101',
        'cityOrArea': '', 'purchaseManner': '', 'openTenderCode': '',
        'purchaser': '', 'agency': '', 'purchaseNature': '',
        'operationStartTime': '', 'operationEndTime': '',
        'verifyCode': verify_code, 'selectTimeName': 'noticeTime',
        '_t': str(int(time.time() * 1000)),
    }
    url = 'https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/info/selectInfoForIndex?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    resp = op.open(req, timeout=15)
    data = resp.read()
    if resp.headers.get('Content-Encoding') == 'gzip':
        data = gzip.decompress(data)
    result = json.loads(data)
    
    if result['code'] != '200':
        print(f"Query failed: code={result['code']} msg={result.get('msg','')}")
        # Save cookies for retry
        cookies = [(c.name, c.value, c.domain, c.path) for c in cj]
        with open(os.path.join(WORKDIR, 'hljcg_cookies.json'), 'w') as f:
            json.dump(cookies, f)
        return
    
    total = (result.get('data') or {}).get('total', 0)
    rows = (result.get('data') or {}).get('rows', [])
    all_items = list(rows)
    
    print(f"Page 1: {len(rows)} items, Total: {total}")
    
    # Paginate
    total_pages = (total + 19) // 20
    for page in range(2, total_pages + 1):
        params['currPage'] = str(page)
        params['_t'] = str(int(time.time() * 1000))
        url = 'https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/info/selectInfoForIndex?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=HEADERS)
        resp = op.open(req, timeout=15)
        data = resp.read()
        if resp.headers.get('Content-Encoding') == 'gzip':
            data = gzip.decompress(data)
        result = json.loads(data)
        if result['code'] != '200':
            print(f"  Page {page}: code={result['code']} - {result.get('msg','')}")
            break
        rows = (result.get('data') or {}).get('rows', [])
        all_items.extend(rows)
        print(f"  Page {page}: {len(rows)} items (total: {len(all_items)})")
        time.sleep(0.3)
    
    # Save
    output = {
        'source': 'hljcg.hlj.gov.cn',
        'region': '鸡西市',
        'fetched_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total': len(all_items),
        'items': all_items,
    }
    output_file = os.path.join(WORKDIR, 'hljcg_chicken_west.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # Stats
    budgets = sum(1 for i in all_items if i.get('budget'))
    purchasers = len(set(i.get('purchaser','') for i in all_items if i.get('purchaser')))
    types = {}
    for i in all_items:
        t = i.get('noticeTypeName', '')
        types[t] = types.get(t, 0) + 1
    
    print(f"\n=== Summary ===")
    print(f"Total items: {len(all_items)}")
    print(f"With budget: {budgets}")
    print(f"Unique purchasers: {purchasers}")
    print(f"Types: {json.dumps(types, ensure_ascii=False)}")
    print(f"Saved to: {output_file}")

if __name__ == '__main__':
    main()
