import requests, re, json
requests.packages.urllib3.disable_warnings()
s = requests.Session(); s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

r = s.get('https://www.qianlima.com/hot1700955/', timeout=15)
html = r.text

# Extract the full function body
m = re.search(r'STATIC_DATA_\s*=\s*function\s*\(\)\s*\{\s*return\s*(\{[\s\S]*?\});\s*\}', html)
if m:
    raw = m.group(1)
    print(f'JSON length: {len(raw)}')
    try:
        data = json.loads(raw)
        print('Keys:', list(data.keys()))
        
        # The items might not be called "dataList" 
        for key in data:
            val = data[key]
            if isinstance(val, list) and len(val) > 0:
                print(f"List '{key}': {len(val)} items")
                if isinstance(val[0], dict):
                    print(f"  Sample keys: {list(val[0].keys())}")
                    # Show first item
                    first = val[0]
                    # Check for budget in any field
                    for k, v in first.items():
                        if isinstance(v, str) and ('预算' in v or '万' in v or '金额' in v):
                            print(f"  {k}: {v[:200]}")
                    # Show full first item
                    print(f"  Full first item:")
                    print(json.dumps(first, ensure_ascii=False, indent=2)[:1500])
                    break
            elif isinstance(val, dict) and len(val) > 0:
                print(f"Dict '{key}': {json.dumps(val, ensure_ascii=False)[:300]}")
    except Exception as e:
        print(f'JSON decode error: {e}')
        # Show start and end
        print(f'First 500: {raw[:500]}')
        print(f'Last 500: {raw[-500:]}')
        # Save for manual inspection
        with open(r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi\static_data_raw.json', 'w', encoding='utf-8') as f:
            f.write(raw[:50000])
        print('Saved raw to static_data_raw.json')
else:
    print('Pattern not found')
    # Try broader
    m2 = re.search(r'STATIC_DATA_\s*=\s*function[\s\S]{0,100}return\s*(\{)', html)
    if m2:
        print(f'Broad match at: {m2.start()}')
        print(html[m2.start():m2.start()+500])
