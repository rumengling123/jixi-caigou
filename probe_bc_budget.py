import requests, re
requests.packages.urllib3.disable_warnings()
s = requests.Session(); s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})
base = 'http://heilongjiang.bidchance.com'

# 抓招标公告(type=02) 和 中标公告(type=05) 列表
for type_code, label in [('02', '招标公告'), ('05', '中标公告')]:
    results = []
    page = 1
    while page <= 3:
        url = f'{base}/tsp_230300_8_{type_code}_0_{page}.html'
        r = s.get(url, timeout=15)
        if r.status_code != 200:
            break
        r.encoding = 'gbk'
        links = re.findall(r'<a[^>]*href="(//www\.bidchance\.com/info-[^"]*)"[^>]*>(.*?)</a>', r.text, re.DOTALL)
        if not links:
            break
        for href, text in links:
            text = re.sub(r'<[^>]+>', '', text).strip()
            text = text.replace('\r','').replace('\n','').replace('\t','')
            if len(text) > 10:
                results.append(text)
        page += 1
    
    print(f'\n=== {label} (type={type_code}), {len(results)} titles ===')
    for i, t in enumerate(results[:20]):
        # Check for budget info in title
        budget_hint = ''
        budget_m = re.search(r'(\d[\d.]*)\s*万', t)
        if budget_m:
            budget_hint = f' [预算: {budget_m.group(1)}万]'
        print(f'  [{i}] {t[:120]}{budget_hint}')
