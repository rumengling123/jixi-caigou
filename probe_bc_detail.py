import requests, re
requests.packages.urllib3.disable_warnings()
s = requests.Session(); s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# 招标公告详情
r = s.get('https://www.bidchance.com/info-gonggao-1a32e6b4e9f80fecc1efc7a436e148b8.html', timeout=15)
r.encoding = 'utf-8'
txt = r.text
budget = re.findall(r'预算[金额价].*?(\d[\d.,]*)\s*万', txt)
title = re.search(r'<title>([^<]+)</title>', txt)
t1 = title.group(1) if title else "N/A"
print(f'招标公告: status={r.status_code}, size={len(txt)}, title={t1}')
print(f'  Budgets found: {budget[:5]}')
ctx_matches = re.findall(r'.{0,30}(?:预算|中标|成交)金额.{0,40}', txt)
print(f'  Context: {ctx_matches[:10]}')

# 中标公告详情
r2 = s.get('https://www.bidchance.com/info-zhongbiao-5796e768270888d9ece5f6f43840b84c.html', timeout=15)
r2.encoding = 'utf-8'
txt2 = r2.text
budget2 = re.findall(r'.{0,30}(?:预算|中标|成交)金额.{0,40}', txt2)
title2 = re.search(r'<title>([^<]+)</title>', txt2)
t2 = title2.group(1) if title2 else "N/A"
print(f'\n中标公告: status={r2.status_code}, size={len(txt2)}, title={t2}')
print(f'  Amount context: {budget2[:10]}')
