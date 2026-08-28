"""探路 bidchance 其他公告类型（招标公告/中标公告等，含预算金额）"""
import requests, re
requests.packages.urllib3.disable_warnings()
s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

base = 'http://heilongjiang.bidchance.com'
area = '230300'  # 鸡西

# 测试不同 type 代码
for type_code in range(1, 15):
    url = f'{base}/tsp_{area}_8_{type_code:02d}_0_1.html'
    try:
        r = s.get(url, timeout=15)
        if r.status_code == 200:
            r.encoding = 'gbk'
            # 查页面标题/分类名
            title_m = re.search(r'<title>([^<]+)</title>', r.text)
            # 查条目数
            links = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r.text)
            info_links = [h for h,t in links if 'info-' in h]
            page_title = re.search(r'当前位置[^<]*<[^>]*>([^<]+)</[^>]*>', r.text)
            print(f'type={type_code:02d}: HTTP 200, {len(r.text)}B, {len(info_links)} links, title={title_m.group(1) if title_m else "N/A"}')
            if info_links:
                print(f'  第一条: {info_links[0]}')
        else:
            print(f'type={type_code:02d}: HTTP {r.status_code}')
    except Exception as e:
        print(f'type={type_code:02d}: {e}')
