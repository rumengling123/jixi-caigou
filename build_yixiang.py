"""
transform yixiang data to data.json-compatible format
and extract time from title patterns
"""
import json, re

with open(r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi\hjlcg意向解析.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

def extract_time(title):
    """Try to extract date from title. Default to 2026"""
    # Pattern: "2026年度" -> use 2026 as year
    m = re.search(r'(\d{4})年度', title)
    year = m.group(1) if m else '2026'
    
    # Pattern: "第N批" - approximate by batch number
    m = re.search(r'第(\d+)批', title)
    batch = int(m.group(1)) if m else 1
    
    # Estimate month: higher batch = later in year
    # Rough: batch 1-5 = Q1, 6-10 = Q2, 11-15 = Q3, 16+ = Q4
    # But this is too rough. Use "2026.01.01" as placeholder
    # Actually check if there's a date in the title
    m = re.search(r'(\d{4})[年.](\d{1,2})[月]', title)
    if m:
        return f"{m.group(1)}.{int(m.group(2)):02d}.01"
    
    # Default: put in the middle of the year
    return f"{year}.06.01"

def extract_budget(title):
    """Try to extract budget from title if present"""
    # Pattern: "预算金额XX万元" or just "XX万元"
    m = re.search(r'(\d+(?:\.\d+)?)\s*万元', title)
    if m:
        return m.group(1)
    return ""

def classify_category(title):
    """Classify意向公告 by title content"""
    t = title.lower()
    # Look for project name after the last "-"
    parts = title.rsplit('-', 1)
    project = parts[-1] if len(parts) > 1 else title
    
    if any(kw in project for kw in ['维修', '维护', '养护', '维保', '运维', '保养']):
        return '维保'
    if any(kw in project for kw in ['系统', '软件', '平台', '信息化', '数据', '网络', '电脑', '计算机', '服务器', '打印机', '复印机', '扫描仪', '投影仪', '监控', '摄像', '电子', '数字']):
        return '信息化'
    if any(kw in project for kw in ['集成', '安装', '改造', '工程', '建设', '施工', '装修', '修缮', '建筑', '管道', '路面', '道路']):
        return '集成'
    if any(kw in project for kw in ['设备', '仪器', '器械', '空调', '电梯', '车辆', '家具', '办公桌', '办公椅', '柜', '床', '桌椅']):
        return '硬件'
    if any(kw in project for kw in ['印刷', '保险', '加油', '维修', '服务', '设计', '咨询', '评估', '体检', '检测', '审计', '物业', '保洁', '保安', '培训', '宣传', '制作', '服装', '被服']):
        return '其他'
    return '其他'

items = []
for r in raw:
    title = r['title']
    items.append({
        'title': title,
        'url': r['url'],
        'buyer': r['buyer'] or title,
        'type': '采购意向',
        'region': r['region'],
        'time': extract_time(title),
        'agency': '黑龙江省政府采购网',
        'addr': '黑龙江省' + r['region'],
        'budget': extract_budget(title),
        'category': classify_category(title),
        'source': '黑龙江政府采购(意向)',
        'source_origin': 'hljcg',
    })

# Sort by time desc
items.sort(key=lambda x: x['time'], reverse=True)

# Count stats
from collections import Counter
cats = Counter(i['category'] for i in items)
areas = Counter(i['region'] for i in items)
print(f'Total 意向 items: {len(items)}')
print(f'By category: {dict(cats)}')
print(f'By area: {dict(areas)}')
print(f'With budget: {sum(1 for i in items if i["budget"])}')

output = r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi\hljcg_yixiang.json'
with open(output, 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
print(f'\nSaved {len(items)} items to {output}')

# Sample
for it in items[:3]:
    print(f'  [{it["time"]}] [{it["region"]}] {it["category"]} | {it["buyer"]}: {it["title"][:60]}')
