"""Download hljcg JS bundles and extract API endpoints from compressed code"""
import urllib.request
import re
import json

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Step 1: Download config.js
cfg_url = 'https://hljcg.hlj.gov.cn/gpcms-center-web/static/config.js'
resp = urllib.request.urlopen(urllib.request.Request(cfg_url, headers=HEADERS), timeout=15)
cfg = resp.read().decode('utf-8')
print(f"config.js: {len(cfg)} bytes")
# Extract all keys
patterns = re.findall(r'([A-Z_]+)\s*:\s*["\']([^"\']*)["\']', cfg)
for k, v in patterns:
    print(f"  {k} = {v}")

# Step 2: Get index page to find current JS bundle names
idx_url = 'https://hljcg.hlj.gov.cn/maincms-web/noticeInformationHlj'
resp = urllib.request.urlopen(urllib.request.Request(idx_url, headers=HEADERS), timeout=15)
html = resp.read().decode('utf-8')
scripts = re.findall(r'src="([^"]+\.js[^"]*)"', html)
print(f"\nScripts on page ({len(scripts)}):")
for s in scripts:
    print(f"  {s}")

# Step 3: Download app.js (the main application bundle)
app_url = None
for s in scripts:
    if '/app.' in s:
        app_url = s if s.startswith('http') else f'https://hljcg.hlj.gov.cn{s}'
        break

if app_url:
    print(f"\nDownloading {app_url}...")
    resp = urllib.request.urlopen(urllib.request.Request(app_url, headers=HEADERS), timeout=30)
    app_js = resp.read().decode('utf-8')
    print(f"  Size: {len(app_js)} bytes")
    
    # Search for API paths - look for common patterns
    # Pattern: url strings containing /gpcms/ /gateway/ /freecms/
    api_matches = re.findall(r'["\']((?:/gpcms/|/gateway/|/freecms/)[^"\']{5,})["\']', app_js)
    unique_apis = sorted(set(api_matches))
    print(f"\nFound {len(unique_apis)} API paths in app.js:")
    for api in unique_apis[:50]:
        print(f"  {api}")
    
    # Also look for POST endpoints and parameter patterns
    important = [a for a in unique_apis if any(kw in a.lower() for kw in ['select', 'list', 'query', 'search', 'notice', 'page'])]
    print(f"\nImportant endpoints ({len(important)}):")
    for api in important:
        print(f"  {api}")
else:
    print("No app.js found!")

# Step 4: Download chunk-vendors for additional API patterns
for s in scripts:
    if 'chunk-vendors' in s and not 'legacy' in s:
        vendors_url = s if s.startswith('http') else f'https://hljcg.hlj.gov.cn{s}'
        print(f"\nDownloading {vendors_url}...")
        resp = urllib.request.urlopen(urllib.request.Request(vendors_url, headers=HEADERS), timeout=120)
        vendors_js = resp.read().decode('utf-8', errors='ignore')
        print(f"  Size: {len(vendors_js)} bytes")
        
        # Look for function names related to API calls
        func_matches = re.findall(r'(selectInfoList|selectNotice|noticeList|selectInfo|getNotice|queryNotice|selectPage|selectList|getInfoList)[A-Za-z]*', vendors_js)
        unique_funcs = sorted(set(func_matches))
        print(f"\n  Notice-related functions: {unique_funcs}")
        
        api_matches2 = re.findall(r'["\']((?:/gpcms/|/gateway/|/freecms/)[^"\']{5,})["\']', vendors_js)
        unique_apis2 = sorted(set(api_matches2))
        print(f"\n  API paths in vendors: {len(unique_apis2)}")
        for api in unique_apis2[:40]:
            print(f"    {api}")
        break
