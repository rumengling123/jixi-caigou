import json
from collections import Counter

with open(r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi\hljcg_jixi.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
items = data['items']
keywords = ['鸡西','鸡冠','恒山','鸡东','城子河','梨树','麻山','密山','虎林','珍宝岛','兴凯湖']
jixi = []
for i in items:
    rn = i.get('regionName', '')
    tl = i.get('title', '')
    pur = i.get('purchaser', '')
    if any(k in rn or k in tl or k in pur for k in keywords):
        jixi.append(i)
print('Total fetched:', len(items))
print('Jixi-related:', len(jixi))

regions = Counter(i.get('regionName', '未知') for i in jixi)
print('Regions (top 20):')
for r, c in sorted(regions.items(), key=lambda x: -x[1])[:20]:
    print(f'  {r}: {c}')

print('\nWith budget:', sum(1 for i in jixi if i.get('budget')))
print('Unique purchasers:', len(set(i.get('purchaser','') for i in jixi if i.get('purchaser'))))

# Show a few samples
print('\nSample items:')
for i in jixi[:5]:
    print(f'  [{i.get("regionName")}] {i.get("title","")[:80]} | budget={i.get("budget")} | purchaser={i.get("purchaser")}')
