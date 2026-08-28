import subprocess, json
BASE = r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi'
# 直接从 git 读取 fcfcc4a 版本的完整数据（6112 条），避免 PowerShell 重定向加 BOM
out = subprocess.run(['git', 'show', 'fcfcc4a:hljcg_jixi_full.json'],
                     cwd=BASE, capture_output=True)
raw = out.stdout
# 去掉可能的 BOM
if raw.startswith(b'\xef\xbb\xbf'):
    raw = raw[3:]
d = json.loads(raw.decode('utf-8'))
items = d.get('items', [])
print('fcfcc4a items:', len(items))
# 与当前数据合并（当前数据可能含 8-13 新增的更新条目），去重键 id/noticeId
import collections
cur = json.load(open(BASE + r'\hljcg_jixi_full.json', encoding='utf-8'))
cur_items = cur.get('items', [])
print('current items:', len(cur_items))

seen = {}
for it in items:
    cid = it.get('id') or it.get('noticeId')
    if cid:
        seen[cid] = it
# 当前数据覆盖（更新的条目优先，因为 8-13 抓的是最新）
for it in cur_items:
    cid = it.get('id') or it.get('noticeId')
    if cid:
        seen[cid] = it

merged = list(seen.values())
print('merged unique:', len(merged))

out_data = {
    'source': 'hljcg.hlj.gov.cn',
    'updated_at': max(d.get('updated_at',''), cur.get('updated_at','')),
    'total': len(merged),
    'items': merged,
}
with open(BASE + r'\hljcg_jixi_full.json', 'w', encoding='utf-8') as f:
    json.dump(out_data, f, ensure_ascii=False)
print('saved, total:', len(merged))
print('region:', collections.Counter(i.get('regionName','?') for i in merged).most_common(12))
