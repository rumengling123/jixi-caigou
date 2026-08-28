import requests, re
requests.packages.urllib3.disable_warnings()
s = requests.Session(); s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

base = 'http://heilongjiang.bidchance.com'

# 检查招标公告(type=02)和 中标公告(type=05)列表页是否含预算
for type_code, label in [('02', '招标公告'), ('05', '中标公告')]:
    url = f'{base}/tsp_230300_8_{type_code}_0_1.html'
    r = s.get(url, timeout=15)
    r.encoding = 'gbk'
    
    # 查看条目摘要 - 每条记录的区域
    items = re.findall(r'<a[^>]*href="[^"]*"[^>]*>([^<]+)</a>', r.text)
    print(f'\n=== {label} (type={type_code}) ===')
    print(f'Total links found: {len(items)}')
    # 只显示含鸡西/预算/金额的
    for i, item in enumerate(items[:30]):
        item = item.strip()
        if item and len(item) > 5:
            print(f'  [{i}] {item[:120]}')
    
    # 找金额相关文本
    money = re.findall(r'[\d,.]+\s*万[元]?', r.text)
    print(f'\nMoney values found: {money[:20]}')
    
    # 找更多上下文（非链接里的文本）
    snippets = re.findall(r'<td[^>]*class="[^"]*"[^>]*>(.*?)</td>', r.text, re.DOTALL)
    for snip in snippets[:5]:
        clean = re.sub(r'<[^>]+>', ' ', snip).strip()
        if len(clean) > 10:
            print(f'  Snippet: {clean[:200]}')
