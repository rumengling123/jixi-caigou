"""Download captcha from hljcg, then user provides code to query API"""
import urllib.request, json, gzip, http.cookiejar, time, urllib.parse, sys

ck = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(ck))
h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0'}

# Step 1: Homepage for cookie
op.open(urllib.request.Request('https://hljcg.hlj.gov.cn/maincms-web/noticeInformationHlj', headers=h), timeout=10)

# Step 2: Download captcha
r = op.open(urllib.request.Request('https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/index/getVerify', headers=h), timeout=10)
captcha_data = r.read()
captcha_path = r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi\captcha_now.png'
with open(captcha_path, 'wb') as f:
    f.write(captcha_data)
print(f"Captcha saved to {captcha_path} ({len(captcha_data)} bytes)")

# Step 3: Read verify code from argument
if len(sys.argv) > 1:
    verify_code = sys.argv[1]
else:
    verify_code = input("Enter captcha code: ")

# Step 4: Query API  
params = {
    'title': '', 'region': '230300',
    'siteId': '94c965cc-c55d-4f92-8469-d5875c68bd04',
    'channel': 'c5bff13f-21ca-4dac-b158-cb40accd3035',
    'currPage': '1', 'pageSize': '5',
    'noticeType': '00101', 'cityOrArea': '',
    'purchaseManner': '', 'openTenderCode': '',
    'purchaser': '', 'agency': '', 'purchaseNature': '',
    'operationStartTime': '', 'operationEndTime': '',
    'verifyCode': verify_code,
    'selectTimeName': 'noticeTime',
    '_t': str(int(time.time() * 1000)),
}
url = 'https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/info/selectInfoForIndex?' + urllib.parse.urlencode(params)
r2 = op.open(urllib.request.Request(url, headers=h), timeout=10)
data = r2.read()
if r2.headers.get('Content-Encoding') == 'gzip':
    data = gzip.decompress(data)
j = json.loads(data)
print(f"code={j['code']} msg={j['msg']}")
if j['code'] == '200':
    total = (j.get('data') or {}).get('total', 0)
    print(f"Total: {total}")
    rows = (j.get('data') or {}).get('rows', [])
    for row in rows[:5]:
        print(f"  [{row.get('regionName','')}] {row['title'][:120]}")
        print(f"    budget={row.get('budget','')} purchaser={row.get('purchaser','')} agency={row.get('agency','')}")
