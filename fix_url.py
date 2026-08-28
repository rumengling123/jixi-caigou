import re

with open(r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi\convert_hljcg.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the url field
old = "'url': '',  # hljcg doesn't provide direct URL in API, will construct from contentId"
new = "'url': f\"https://hljcg.hlj.gov.cn/maincms-web/noticeInformation?subSystemCode=projectProcurement&noticeType={it.get('noticeType','')}&noticeId={it.get('noticeId','')}\""

if old in c:
    c = c.replace(old, new)
    with open(r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi\convert_hljcg.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("REPLACED OK")
else:
    print("NOT FOUND")
    i = c.find("url")
    if i >= 0:
        print(c[i:i+100])
