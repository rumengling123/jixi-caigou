"""
bidchance.com - 抓取所有鸡西子区县采购意向公告
Cross-platform (Windows + Linux GitHub Actions)
"""
import requests, re, json, time, os
requests.packages.urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def fetch(url):
    r = s.get(url, timeout=30)
    if r.status_code != 200:
        return None
    r.encoding = 'gbk'
    return r.text

base = 'http://heilongjiang.bidchance.com'
all_results = []

areas = {
    '230300': '鸡西市',
    '230302': '鸡冠区', '230303': '恒山区', '230304': '滴道区',
    '230305': '梨树区', '230306': '城子河区', '230307': '麻山区',
    '230321': '鸡东县', '230381': '虎林市', '230382': '密山市',
}

for area_code, area_name in areas.items():
    page = 1
    while True:
        url = f'{base}/tsp_{area_code}_8_03_0_{page}.html'
        html = fetch(url)
        if not html:
            print(f'{area_name} page {page}: HTTP error')
            break
        
        links = re.findall(r'<a[^>]*href="([^"]*info-yugao[^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)
        if not links:
            print(f'{area_name} page {page}: no links')
            break
        
        count = 0
        for href, text in links:
            text = re.sub(r'<[^>]+>', '', text).strip()
            text = text.replace('\r','').replace('\n','').replace('\t','')
            all_results.append({
                'title': text,
                'url': 'https:' + href if href.startswith('//') else href,
                'area': area_name,
                'page': page
            })
            count += 1
        
        print(f'{area_name} page {page}: {count}')
        if f'/tsp_{area_code}_8_03_0_{page+1}.html' not in html:
            print(f'{area_name}: last page')
            break
        page += 1
        time.sleep(0.4)
        if page > 30:
            break

seen = {}
unique = []
for r in all_results:
    if r['url'] not in seen:
        seen[r['url']] = True
        unique.append(r)

print(f'\n=== Total unique: {len(unique)} ===')
yixiang = [r for r in unique if '意向' in r['title']]
print(f'With "意向": {len(yixiang)}')

base_dir = os.path.dirname(os.path.abspath(__file__))
output = os.path.join(base_dir, 'bidchance_all.json')
with open(output, 'w', encoding='utf-8') as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)
print(f'Saved to {output}')
