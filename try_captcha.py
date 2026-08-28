import urllib.request, json, gzip, http.cookiejar, time, urllib.parse

for verify_code in ['0989', '0986', '0988', '0980', '6969', '6989']:
    ck = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(ck))
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0'}
    op.open(urllib.request.Request('https://hljcg.hlj.gov.cn/maincms-web/noticeInformationHlj', headers=h), timeout=10)
    r = op.open(urllib.request.Request('https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/index/getVerify', headers=h), timeout=10)
    r.read()  # consume captcha
    
    params = {'title':'','region':'230300','siteId':'94c965cc-c55d-4f92-8469-d5875c68bd04','channel':'c5bff13f-21ca-4dac-b158-cb40accd3035','currPage':'1','pageSize':'5','noticeType':'00101','cityOrArea':'','purchaseManner':'','openTenderCode':'','purchaser':'','agency':'','purchaseNature':'','operationStartTime':'','operationEndTime':'','verifyCode':verify_code,'selectTimeName':'noticeTime','_t':str(int(time.time()*1000))}
    url = 'https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/info/selectInfoForIndex?' + urllib.parse.urlencode(params)
    r2 = op.open(urllib.request.Request(url, headers=h), timeout=10)
    data = r2.read()
    if r2.headers.get('Content-Encoding') == 'gzip':
        data = gzip.decompress(data)
    j = json.loads(data)
    ok = j['code'] == '200'
    total = (j.get('data') or {}).get('total', 0)
    print(f'verify={verify_code}: code={j["code"]} total={total}')
    if ok and j.get('data'):
        rows = j['data']['rows']
        for row in rows[:3]:
            print(f'  [{row.get("regionName","")}] {row["title"][:100]} budget={row.get("budget","")}')
        break
    elif '验证码' in j.get('msg', ''):
        continue
    else:
        break
