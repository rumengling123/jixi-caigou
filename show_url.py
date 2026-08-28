with open(r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi\convert_hljcg.py', 'r', encoding='utf-8') as f:
    c = f.read()
i = c.find('hljcg.hlj.gov.cn')
print(c[i:i+150])
