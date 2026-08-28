import json, re
with open(r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi\exec.txt','r',encoding='utf-8',errors='ignore') as f:
    text = f.read()
urls = re.findall(r'https://hljcg\.hlj\.gov\.cn(/[^\"\s,]+)', text)
urls = sorted(set(urls))
for u in urls:
    if any(k in u for k in ['gpcms','freecms','gateway','maincms','select','notice','list','info']):
        print(u[:200])
