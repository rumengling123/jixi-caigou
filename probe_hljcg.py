import urllib.request, json, re, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# 1. config.js
try:
    req = urllib.request.Request('https://hljcg.hlj.gov.cn/static/config.js', headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
        js = r.read().decode('utf-8')
        print(f'config.js: {len(js)} bytes')
        urls = re.findall(r'https?://[^\'"]+', js)
        print("URLs in config.js:")
        for u in urls[:20]:
            print(f'  {u}')
except Exception as e:
    print(f'config.js: {e}')

# 2. chunk-vendors JS bundle - look for API patterns
try:
    req = urllib.request.Request('https://hljcg.hlj.gov.cn/js/chunk-vendors.83a9a133.js', headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        js = r.read().decode('utf-8', errors='ignore')
        print(f'\nchunk-vendors: {len(js)} bytes')
        # Search for API paths
        patterns = re.findall(r'"(/[a-zA-Z][a-zA-Z0-9/_-]*)"', js)
        api_candidates = [p for p in set(patterns) if any(k in p for k in ['notice','gateway','freecms','maincms','list','search','gpcms'])]
        print('API candidates:')
        for p in sorted(set(api_candidates))[:30]:
            print(f'  {p}')
except Exception as e:
    print(f'chunk-vendors: {e}')

# 3. app.js
try:
    req = urllib.request.Request('https://hljcg.hlj.gov.cn/js/app.dc78b6f7.js', headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        js = r.read().decode('utf-8', errors='ignore')
        print(f'\napp.js: {len(js)} bytes')
        patterns = re.findall(r'"(/[a-zA-Z][a-zA-Z0-9/_-]*)"', js)
        api_candidates = [p for p in set(patterns) if any(k in p for k in ['notice','gateway','freecms','maincms','list','search'])]
        print('API candidates:')
        for p in sorted(set(api_candidates))[:30]:
            print(f'  {p}')
except Exception as e:
    print(f'app.js: {e}')

# 4. Try specific API endpoints
print('\n--- API probes ---')
apis = [
    ('/gateway/gpc-gpcms/rest/v2/public/pageList', 'GET'),
    ('/gateway/gpc-gpcms/rest/v2/public/noticeList', 'GET'),
    ('/gateway/gpc-gpcms/rest/v2/public/purchaseIntention', 'GET'),
    ('/freecms/rest/v1/notice/selectNoticeListByCondition', 'POST'),
    ('/maincms-web/api/notice/list', 'GET'),
    ('/maincms-web/api/noticeInformationHlj', 'GET'),
]
for api, method in apis:
    try:
        url = f'https://hljcg.hlj.gov.cn{api}'
        data = None
        if method == 'POST':
            data = json.dumps({"pageNum": 1, "pageSize": 5}).encode()
        req = urllib.request.Request(url, data=data, headers={'User-Agent': UA, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            body = r.read().decode('utf-8', errors='ignore')
            print(f'{method} {api}: {r.status}, {len(body)}B, body: {body[:300]}')
    except urllib.error.HTTPError as e:
        print(f'{method} {api}: HTTP {e.code}')
    except Exception as e:
        print(f'{method} {api}: {e}')
