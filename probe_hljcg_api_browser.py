"""从 hljcg 的 Vue JS bundle 中提取 API 端点"""
import urllib.request
import re
import json

# 下载 app.js
app_url = 'https://hljcg.hlj.gov.cn/gpcms-center-web/static/js/app.dc78b6f7.js'
print(f"Fetching {app_url}")
req = urllib.request.Request(app_url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=30)
app_js = resp.read().decode('utf-8')

# 搜索 API 模式
patterns = [
    r'/gpcms/rest/[a-zA-Z0-9/_\-]+',
    r'/gateway/[a-zA-Z0-9/_\-]+',
    r'/freecms/[a-zA-Z0-9/_\-]+',
    r'/maincms-web/[a-zA-Z0-9/_\-]+',
    r'api/[a-zA-Z0-9/_\-]+',
]

all_apis = set()
for pat in patterns:
    matches = re.findall(pat, app_js)
    for m in matches:
        # 过滤掉过短的反斜杠噪音
        if len(m) > 20 and not m.endswith('/') and '\\\\' not in m:
            all_apis.add(m)

print(f"Found {len(all_apis)} unique APIs in app.js:")
for api in sorted(all_apis)[:50]:
    print(f"  {api}")

# 也下载 chunk-vendors
vendors_url = 'https://hljcg.hlj.gov.cn/gpcms-center-web/static/js/chunk-vendors.83a9a133.js'
print(f"\nFetching {vendors_url}")
req2 = urllib.request.Request(vendors_url, headers={'User-Agent': 'Mozilla/5.0'})
resp2 = urllib.request.urlopen(req2, timeout=60)
vendors_js = resp2.read().decode('utf-8')

for pat in patterns:
    matches = re.findall(pat, vendors_js)
    for m in matches:
        if len(m) > 20 and not m.endswith('/') and '\\\\' not in m:
            all_apis.add(m)

print(f"\nTotal unique APIs from both bundles: {len(all_apis)}")
for api in sorted(all_apis)[:80]:
    print(f"  {api}")
