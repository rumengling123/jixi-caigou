"""Download captcha, wait for verify code file, query hljcg API - all in one session."""
import urllib.request, urllib.parse, json, gzip, http.cookiejar, time, os, sys

WORKDIR = r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi'
CAPTCHA_FILE = os.path.join(WORKDIR, 'cap_now.png')
CODE_FILE = os.path.join(WORKDIR, 'verify_code.txt')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
}

SITE_ID = '94c965cc-c55d-4f92-8469-d5875c68bd04'
CHANNEL = 'c5bff13f-21ca-4dac-b158-cb40accd3035'
REGION = '230300'

# Remove old code file
if os.path.exists(CODE_FILE):
    os.remove(CODE_FILE)

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Visit homepage
op.open(urllib.request.Request('https://hljcg.hlj.gov.cn/maincms-web/noticeInformationHlj', headers=HEADERS), timeout=10).read()

# Download captcha
resp = op.open(urllib.request.Request('https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/index/getVerify', headers=HEADERS), timeout=10)
with open(CAPTCHA_FILE, 'wb') as f:
    f.write(resp.read())
print(f"CAPTCHA_READY:{CAPTCHA_FILE}")

# Wait for verify code file (up to 90 seconds)
for i in range(90):
    if os.path.exists(CODE_FILE):
        break
    time.sleep(1)

if not os.path.exists(CODE_FILE):
    print("Timeout")
    sys.exit(1)

with open(CODE_FILE, 'r') as f:
    verify_code = f.read().strip()
print(f"CODE:{verify_code}")

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
resp = op.open(urllib.request.Request(url, headers=HEADERS), timeout=15)
data = resp.read()
if resp.headers.get('Content-Encoding') == 'gzip':
    data = gzip.decompress(data)
result = json.loads(data)

if result['code'] != '200':
    print(f"FAIL:{result['code']}:{result.get('msg','')}")
    sys.exit(1)

total = (result.get('data') or {}).get('total', 0)
rows = (result.get('data') or {}).get('rows', [])
all_items = list(rows)
print(f"P1:{len(rows)}/{total}")

total_pages = (total + 19) // 20
for page in range(2, total_pages + 1):
    params['currPage'] = str(page)
    params['_t'] = str(int(time.time() * 1000))
    url = 'https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/info/selectInfoForIndex?' + urllib.parse.urlencode(params)
    resp = op.open(urllib.request.Request(url, headers=HEADERS), timeout=15)
    data = resp.read()
    if resp.headers.get('Content-Encoding') == 'gzip':
        data = gzip.decompress(data)
    r2 = json.loads(data)
    if r2['code'] != '200':
        print(f"P{page}:FAIL:{r2['code']}")
        break
    r = (r2.get('data') or {}).get('rows', [])
    all_items.extend(r)
    print(f"P{page}:{len(r)}/{len(all_items)}")
    time.sleep(0.3)

out = {
    'source': 'hljcg.hlj.gov.cn',
    'fetched_at': time.strftime('%Y-%m-%d %H:%M:%S'),
    'total': len(all_items),
    'items': all_items,
}
out_path = os.path.join(WORKDIR, 'hljcg_jixi.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"DONE:{len(all_items)} items -> {out_path}")
