"""Try multiple verify code guesses against hljcg"""
import urllib.request, json, gzip, http.cookiejar, time, urllib.parse

def try_code(verify_code):
    ck = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(ck))
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0'}
    op.open(urllib.request.Request('https://hljcg.hlj.gov.cn/maincms-web/noticeInformationHlj', headers=h), timeout=10)
    r = op.open(urllib.request.Request('https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/index/getVerify', headers=h), timeout=10)
    r.read()
    params = {'title':'','region':'230300','siteId':'94c965cc-c55d-4f92-8469-d5875c68bd04','channel':'c5bff13f-21ca-4dac-b158-cb40accd3035','currPage':'1','pageSize':'3','noticeType':'00101','cityOrArea':'','purchaseManner':'','openTenderCode':'','purchaser':'','agency':'','purchaseNature':'','operationStartTime':'','operationEndTime':'','verifyCode':verify_code,'selectTimeName':'noticeTime','_t':str(int(time.time()*1000))}
    url = 'https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/info/selectInfoForIndex?' + urllib.parse.urlencode(params)
    r2 = op.open(urllib.request.Request(url, headers=h), timeout=10)
    data = r2.read()
    if r2.headers.get('Content-Encoding') == 'gzip':
        data = gzip.decompress(data)
    j = json.loads(data)
    return j

# Try guesses
guesses = ['1880', '1886', '1888', '1889', '7880', '7889', 'J880', 'j880']
for code in guesses:
    try:
        j = try_code(code)
        total = (j.get('data') or {}).get('total', 0)
        ok = j['code'] == '200'
        print(f'{code}: code={j["code"]} total={total}')
        if ok:
            rows = (j.get('data') or {}).get('rows', [])
            for row in rows[:3]:
                print(f'  [{row.get("regionName","")}] {row["title"][:100]}')
                print(f'    budget={row.get("budget","")} purchaser={row.get("purchaser","")}')
            break
        elif '验证码' not in j.get('msg', ''):
            break
    except Exception as e:
        print(f'{code}: ERROR {e}')
