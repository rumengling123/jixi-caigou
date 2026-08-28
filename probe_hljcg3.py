import urllib.request, json, re, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# 1. config.js at correct path
try:
    req = urllib.request.Request('https://hljcg.hlj.gov.cn/gpcms-center-web/static/config.js', headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        config = r.read().decode('utf-8')
        print(f'config.js: {len(config)} bytes')
        print(config[:2000])
except Exception as e:
    print(f'config.js: {e}')

# 2. SPA: 首页 2585 bytes 壳 - 找 JS chunk/app bundle 引用  
# 可能是 webpack 动态加载方式
try:
    req = urllib.request.Request('https://hljcg.hlj.gov.cn/gpcms-center-web/', headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        html = r.read().decode('utf-8', errors='ignore')
        # 找所有非标准引用方式
        all_js = re.findall(r'["\']([^"\']*\.js[^"\']*)["\']', html)
        print(f'\nIndex HTML: {len(html)} bytes')
        print('JS refs found:', all_js)
        # 打印完整 HTML
        print('\n--- FULL HTML ---')
        print(html[:3000])
except Exception as e:
    print(f'Index: {e}')

# 3. Try freecms with different paths
print('\n--- freecms probes ---')
for path in [
    '/freecms/site/hlj/ggxx/index.html',
    '/freecms/site/hlj/index.html',
    '/freecms/site/hlj/',
]:
    try:
        req = urllib.request.Request(f'https://hljcg.hlj.gov.cn{path}', headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            body = r.read().decode('utf-8', errors='ignore')
            print(f'{path}: {r.status}, {len(body)}B')
    except Exception as e:
        print(f'{path}: {e}')
