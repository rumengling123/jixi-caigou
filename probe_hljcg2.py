import urllib.request, json, re, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# 1. 首页找 JS bundle 路径
try:
    req = urllib.request.Request('https://hljcg.hlj.gov.cn/', headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        html = r.read().decode('utf-8', errors='ignore')
        # 找所有 <script src=...>
        scripts = re.findall(r'<script\s+src="([^"]+)"', html)
        print(f"首页 HTML: {len(html)} bytes")
        print("Script tags:")
        for s in scripts:
            print(f"  {s}")
except Exception as e:
    print(f"首页: {e}")

# 2. 尝试采购意向页面 /maincms-web/noticeInformationHlj 
try:
    req = urllib.request.Request(
        'https://hljcg.hlj.gov.cn/maincms-web/noticeInformationHlj',
        headers={'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml,application/xml'}
    )
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        html = r.read().decode('utf-8', errors='ignore')
        # 找 __NUXT__ 或 window.__INITIAL_STATE__ 等预渲染数据
        data_patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
            r'window\.__NUXT__\s*=\s*({.*?});',
            r'"rows"\s*:\s*(\[.*?\])(?=\s*[,}])',
            r'"dataList"\s*:\s*(\[.*?\])',
        ]
        for pat in data_patterns:
            matches = re.findall(pat, html, re.DOTALL)
            if matches:
                print(f"\nData found with pattern: {pat[:50]}")
                print(matches[0][:500])
        scripts2 = re.findall(r'<script\s+src="([^"]+)"', html)
        print(f"\nnoticeInformationHlj HTML: {len(html)} bytes")
        print("Script tags:")
        for s in scripts2:
            print(f"  {s}")
except Exception as e:
    print(f"noticeInformationHlj: {e}")

# 3. Try some other hljcg API patterns found from generic GPC CMS
print("\n--- GPC CMS API probes ---")
apis = [
    ('/freecms/rest/v1/notice/selectNoticeListByCondition?pageNum=1&pageSize=5&noticeType=00101', 'GET'),
    ('/freecms/rest/v1/notice/selectNoticeListByCondition?pageNum=1&pageSize=5&noticeType=00102', 'GET'),
    ('/gateway/gpc-gpcms/rest/v2/public/purchaseIntention/listPage?pageNum=1&pageSize=5', 'GET'),
    ('/gateway/gpc-gpcms/rest/v2/public/cmSeriousInfo?pageNum=1&pageSize=5', 'GET'),
]
for api, method in apis:
    try:
        url = f'https://hljcg.hlj.gov.cn{api}'
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            body = r.read().decode('utf-8', errors='ignore')
            print(f'{method} {api[:60]}: {r.status}, {len(body)}B, body: {body[:250]}')
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')[:200]
        print(f'{method} {api[:60]}: HTTP {e.code}, body: {body[:150]}')
    except Exception as e:
        print(f'{method} {api[:60]}: {e}')
