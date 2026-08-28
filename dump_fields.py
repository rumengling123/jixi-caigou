import json
h = json.load(open(r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi\hljcg_jixi_full.json', 'r', encoding='utf-8'))
item = h['items'][0]
# Print all fields that might relate to URL/detail navigation
for k, v in item.items():
    if isinstance(v, str) and len(v) < 200:
        print(f'{k}: {v}')
    elif isinstance(v, str):
        print(f'{k}: {v[:80]}...')
    else:
        print(f'{k}: {v}')
