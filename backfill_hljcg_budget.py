"""
抓取 bidchance 详情页预算金额（含 hljcg 鸡西招标/中标公告）
详情页虽被 Cloudflare 保护，但 HTTP 短连接初次请求通常能过
"""
import requests, re, json, os, time, random
from concurrent.futures import ThreadPoolExecutor, as_completed

requests.packages.urllib3.disable_warnings()

INPUT_FILE = r"C:\Users\Admin\.qclaw\workspace\ccgp_jixi\hljcg_budget.json"
OUTPUT_FILE = r"C:\Users\Admin\.qclaw\workspace\ccgp_jixi\hljcg_budget_full.json"

items = json.loads(open(INPUT_FILE, encoding='utf-8').read())
print(f"Total items to process: {len(items)}")

def fetch_detail(item, idx):
    url = item['url']
    # Add random delay to avoid rate limiting
    time.sleep(random.uniform(0.5, 2.0))
    
    try:
        s = requests.Session()
        s.verify = False
        s.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
        })
        
        r = s.get(url, timeout=15)
        if r.status_code == 521:
            return idx, item, None  # Cloudflare block
        
        if r.status_code != 200:
            return idx, item, None
        
        r.encoding = 'utf-8'
        html = r.text
        
        # Extract budget from detail page
        budget = ''
        
        # Pattern 1: 预算金额：XX万元
        m = re.search(r'预算金额[：:]\s*(\d[\d,.]*)\s*万', html)
        if m:
            budget = m.group(1).replace(',', '') + '万元'
        
        # Pattern 2: 中标金额
        if not budget:
            m = re.search(r'中标金额[：:]\s*(\d[\d,.]*)\s*万', html)
            if m:
                budget = m.group(1).replace(',', '') + '万元'
        
        # Pattern 3: 成交金额
        if not budget:
            m = re.search(r'成交金额[：:]\s*(\d[\d,.]*)\s*万', html)
            if m:
                budget = m.group(1).replace(',', '') + '万元'
        
        # Pattern 4: 合同金额
        if not budget:
            m = re.search(r'合同金额[：:]\s*(\d[\d,.]*)\s*万', html)
            if m:
                budget = m.group(1).replace(',', '') + '万元'
        
        # Pattern 5: 金额:纯数字
        if not budget:
            m = re.search(r'(?:预算|中标|成交|合同)\s*[金额价][：:]\s*[¥￥]?\s*(\d[\d,.]*)\s*[万]', html)
            if m:
                budget = m.group(1).replace(',', '') + '万元'
        
        # Pattern 6: ¥符号金额
        if not budget:
            m = re.search(r'[¥￥]\s*(\d[\d,.]*)\s*万', html)
            if m:
                budget = m.group(1).replace(',', '') + '万元'
        
        # Extract buyer from detail
        buyer = ''
        m = re.search(r'采购[单人名][位称]{0,2}[：:]\s*([^<\s]{2,30})', html)
        if m:
            buyer = m.group(1).strip()
        if not buyer:
            m = re.search(r'招标[单人名][位称]{0,2}[：:]\s*([^<\s]{2,30})', html)
            if m:
                buyer = m.group(1).strip()
        
        item['budget'] = budget
        item['buyer'] = buyer or item.get('buyer', '')
        
        s.close()
        return idx, item, budget
    except Exception as e:
        return idx, item, None

# Process in batches
results = []
batch_size = 10
start = 0
while start < len(results) or start == 0:
    if start == 0:
        batch = items
    else:
        batch = items[start:start+batch_size]
        if not batch:
            break
    
    # Use ThreadPoolExecutor for this batch
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(fetch_detail, it, i): i for i, it in enumerate(batch)}
        for f in as_completed(futures):
            idx, item, budget = f.result()
            if budget:
                print(f'  [{idx}] BUDGET: {item["title"][:60]} | {budget}')
            else:
                print(f'  [{idx}] NO budget: {item["title"][:60]}')
    
    break  # Only one batch for now
    
print(f'\nProcessed: {len(results)}')

# Save results
with_budget = [it for it in items if it.get('budget')]
print(f'Total: {len(items)}, With budget: {len(with_budget)}')

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
print(f'Saved to {OUTPUT_FILE}')
