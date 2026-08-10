"""
Parse bidchance listing titles to extract buyer, area, budget info
Build data in format compatible with build_html.py
"""
import json, re, os

with open(r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi\bidchance_all.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

# 鸡西区县列表
area_keywords = [
    ('鸡冠区', '鸡冠区'), ('恒山区', '恒山区'), ('鸡东县', '鸡东县'),
    ('城子河区', '城子河区'), ('梨树区', '梨树区'), ('麻山区', '麻山区'),
    ('密山市', '密山市'), ('虎林市', '虎林市'), ('滴道区', '滴道区'),
    ('鸡西市', '鸡西市'),
]

def extract_area(title, list_area):
    """Extract area from title"""
    for kw, name in area_keywords:
        if kw in title:
            return name
    # Fall back to list_area if it's specific
    if list_area and list_area != '鸡西市':
        return list_area
    return '鸡西市'

def extract_buyer(title):
    """Extract procurement unit from title"""
    # Pattern: "XXX2026年度政府采购意向公告(第N批)-"
    m = re.match(r'^(.+?)(?:2026|2025|2024)年度政府采购意向公告', title)
    if m:
        buyer = m.group(1).strip()
        # Remove trailing "的"
        buyer = buyer.rstrip('的').strip()
        return buyer
    
    # Pattern: just starts with procurement unit name
    m = re.match(r'^(.+?)(?:2026|2025)年度政府采购意向', title)
    if m:
        return m.group(1).strip()
    
    # If no match, return first part before "2026"
    m = re.match(r'^(.+?)(?:2026|2025)', title)
    if m:
        return m.group(1).strip()
    
    return ''

# Also parse the bidchance listing data to link to hljcg if possible
# The info-yugao detail pages give more data, but they're cloudflare-protected
# We can use web_search for budget data on key items

items = []
for r in raw:
    title = r['title']
    area = extract_area(title, r.get('area', ''))
    buyer = extract_buyer(title)
    
    item = {
        'title': title,
        'url': r['url'],
        'buyer': buyer,
        'region': area,
        'type': '采购意向',
        'time': '',  # to be filled from detail or parsed
        'agency': '黑龙江省政府采购网(转载)',  # hljcg source
        'addr': '黑龙江省',
        'budget': '',
        'category': '采购意向',
        'source': 'hljcg-bidchance',
        'source_label': '采购意向(转载)',
    }
    items.append(item)

# Filter to only items with "意向"
yixiang = [it for it in items if '意向' in it['title'] or it['type'] == '采购意向']
print(f'Total items: {len(items)}, 意向 items: {len(yixiang)}')

# Group by area
from collections import Counter
areas = Counter(it['region'] for it in yixiang)
print('\nBy area:')
for a, c in areas.most_common():
    print(f'  {a}: {c}')

# Group by buyer (top 20)
buyers = Counter(it['buyer'] for it in yixiang if it['buyer'])
print(f'\nTop buyers:')
for b, c in buyers.most_common(20):
    print(f'  {b}: {c}')

# Save
output = r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi\hjlcg意向解析.json'
with open(output, 'w', encoding='utf-8') as f:
    json.dump(yixiang, f, ensure_ascii=False, indent=2)
print(f'\nSaved {len(yixiang)} items to {output}')

# Sample
print('\nSample items:')
for it in yixiang[:5]:
    print(f'  [{it["region"]}] {it["buyer"]}: {it["title"][:60]}')
