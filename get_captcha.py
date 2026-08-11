"""Download hljcg captcha image - called by daily sync cron agent"""
import requests, time, os
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edg/151.0.0.0'})

url = f'https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/index/getVerify?_t={int(time.time()*1000)}'
resp = s.get(url, verify=False, timeout=15)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'captcha_daily.png')
with open(out, 'wb') as f:
    f.write(resp.content)
print(f'Captcha saved: {len(resp.content)} bytes -> {out}')
