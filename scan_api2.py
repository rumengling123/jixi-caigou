"""Deep scan of hljcg JS bundle for API endpoints using broader patterns"""
import urllib.request
import re
import gzip
from io import BytesIO

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Encoding': 'gzip, deflate',
}

# Download app.js 
url = 'https://hljcg.hlj.gov.cn/gpcms-center-web/static/js/app.dc78b6f7.js'
print(f"Downloading {url}...")
req = urllib.request.Request(url, headers=HEADERS)
resp = urllib.request.urlopen(req, timeout=30)
data = resp.read()
if resp.headers.get('Content-Encoding') == 'gzip':
    data = gzip.decompress(data)
app_js = data.decode('utf-8', errors='ignore')
print(f"  Size: {len(app_js)} chars")

# Broader patterns - look for any URL-like strings
# Some JS bundles use template literals or concatenation
patterns = [
    # URL fragments
    r'["\']([^"\']*(?:gpcms|gateway|freecms|maincms|notice|selectInfo|selectNotice|selectList|getInfo|getNotice|queryInfo)[^"\']*)["\']',
    # Template literals with backtick  
    r'`([^`]*(?:gpcms|gateway|freecms|notice|select)[^`]*)`',
    # All quoted strings (limit to reasonable length)
    r'["\']/((?:gpcms|gateway|freecms|maincms)[^"\']{3,100})["\']',
]

all_api = set()
for pat in patterns:
    for m in re.finditer(pat, app_js):
        val = m.group(1)
        if len(val) > 5:
            all_api.add(val)

print(f"\n=== app.js API strings ({len(all_api)}) ===")
for a in sorted(all_api)[:60]:
    print(f"  {a[:120]}")

# Also scan for axios/service calls
print("\n=== axios/service patterns in app.js ===")
for m in re.finditer(r'(?:axios|service|api|request)\s*\.\s*(?:get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']', app_js):
    print(f"  {m.group(1)}")

# Scan for url: or path: patterns  
print("\n=== url:/path: patterns in app.js ===")
for m in re.finditer(r'(?:url|path|baseURL|baseUrl)\s*[:=]\s*["\']([^"\']{5,})["\']', app_js):
    val = m.group(1)
    if len(val) < 200:
        print(f"  {val[:150]}")
