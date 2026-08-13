"""Download captcha + save WAF cookies so a separate process can reuse the same session."""
import requests, time, os, json
import urllib3
urllib3.disable_warnings()

BASE = os.path.dirname(os.path.abspath(__file__))

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    'Accept': 'application/json, text/plain, */*',
})

# 1. visit homepage to establish WAF session
s.get('https://hljcg.hlj.gov.cn/maincms-web/noticeInformationHlj', verify=False, timeout=15)

# 2. download captcha
url = f'https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/index/getVerify?_t={int(time.time()*1000)}'
resp = s.get(url, verify=False, timeout=15)

out = os.path.join(BASE, 'captcha_daily.png')
with open(out, 'wb') as f:
    f.write(resp.content)

# 3. save cookies (HWWAFSESID etc.) for reuse
cookie_file = os.path.join(BASE, 'hljcg_waf_cookies.json')
cookies = {c.name: c.value for c in s.cookies}
with open(cookie_file, 'w', encoding='utf-8') as f:
    json.dump(cookies, f)

print(f'Captcha saved: {len(resp.content)} bytes -> {out}')
print(f'Cookies saved: {cookies}')
