"""Download captcha, read verify code from stdin, query hljcg API"""
import urllib.request, urllib.parse, json, gzip, http.cookiejar, time, sys, os

WORKDIR = r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    'Accept': 'application/json, text/plain, */*',
}

SITE_ID = '94c965cc-c55d-4f92-8469-d5875c68bd04'
CHANNEL = 'c5bff13f-21ca-4dac-b158-cb40accd3035'
REGION = '230300'

def main():
    verify_code = sys.argv[1] if len(sys.argv) > 1 else None
    
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    # Visit homepage
    req = urllib.request.Request('https://hljcg.hlj.gov.cn/maincms-web/noticeInformationHlj', headers=HEADERS)
    op.open(req, timeout=10).read()
    
    # Download captcha immediately
    req = urllib.request.Request('https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/index/getVerify', headers=HEADERS)
    resp = op.open(req, timeout=10)
    cap_data = resp.read()
    cap_path = os.path.join(WORKDIR, 'hljcg_cap_now.png')
    with open(cap_path, 'wb') as f:
        f.write(cap_data)
    print(f"CAPTCHA:{cap_path}:{len(cap_data)}")
    
    if not verify_code:
        verify_code = sys.stdin.readline().strip()
    
    print(f"Using code: {verify_code}")
    
    # Query immediately
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
        print(f"FAIL: code={result['code']} msg={result.get('msg','')}")
        return
    
    total = (result.get('data') or {}).get('total', 0)
    rows = (result.get('data') or {}).get('rows', [])
    all_items = list(rows)
    print(f"Page 1: {len(rows)} rows, Total: {total}")
    
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
            print(f"  Page {page}: {result['code']} - {result.get('msg','')}")
            break
        rows = (result.get('data') or {}).get('rows', [])
        all_items.extend(rows)
        print(f"  Page {page}: {len(rows)} rows (total {len(all_items)})")
        time.sleep(0.3)
    
    output = {
        'source': 'hljcg.hlj.gov.cn',
        'fetched_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total': len(all_items),
        'items': all_items,
    }
    out_path = os.path.join(WORKDIR, 'hljcg_chicken_west.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"SAVED: {out_path} ({len(all_items)} items)")

if __name__ == '__main__':
    main()
