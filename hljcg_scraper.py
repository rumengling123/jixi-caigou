"""
hljcg scraper: downloads captcha, saves it, then prompts for verify code.
Run: python hljcg_scraper.py [verify_code]
Step 1: If no verify_code arg, downloads captcha and exits (so user can OCR)
Step 2: If verify_code arg provided, queries hljcg API and saves results
"""
import urllib.request
import urllib.parse
import json
import gzip
import http.cookiejar
import time
import sys
import os

WORKDIR = r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi'
CAPTCHA_FILE = os.path.join(WORKDIR, 'hljcg_captcha.png')
COOKIE_FILE = os.path.join(WORKDIR, 'hljcg_cookies.txt')
DATA_FILE = os.path.join(WORKDIR, 'hljcg_data.json')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

SITE_ID = '94c965cc-c55d-4f92-8469-d5875c68bd04'
CHANNEL = 'c5bff13f-21ca-4dac-b158-cb40accd3035'
REGION = '230300'  # 鸡西市
NOTICE_TYPE = '00101'  # 项目采购

def save_cookies(cj, path):
    """Save cookies as simple name=value map"""
    cookies = [(c.name, c.value, c.domain, c.path) for c in cj]
    with open(path, 'w') as f:
        json.dump(cookies, f)

def load_cookies(path):
    """Load cookies into a new CookieJar"""
    with open(path, 'r') as f:
        cookies = json.load(f)
    cj = http.cookiejar.CookieJar()
    for name, value, domain, p in cookies:
        c = http.cookiejar.Cookie(version=0, name=name, value=value, port=None, port_specified=False,
                                   domain=domain, domain_specified=True, domain_initial_dot=False,
                                   path=p, path_specified=True, secure=False, expires=None,
                                   discard=True, comment=None, comment_url=None, rest={}, rfc2109=False)
        cj.set_cookie(c)
    return cj

def create_session():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
        urllib.request.HTTPRedirectHandler()
    )
    return cj, op

def http_get(op, url, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    resp = op.open(req, timeout=timeout)
    data = resp.read()
    if resp.headers.get('Content-Encoding') == 'gzip':
        data = gzip.decompress(data)
    return data.decode('utf-8', errors='ignore')

def download_captcha():
    """Step 1: download captcha image for OCR"""
    cj, op = create_session()
    
    # Visit homepage for cookies
    http_get(op, 'https://hljcg.hlj.gov.cn/maincms-web/noticeInformationHlj')
    
    # Download captcha
    captcha_url = 'https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/index/getVerify'
    req = urllib.request.Request(captcha_url, headers=HEADERS)
    resp = op.open(req, timeout=10)
    data = resp.read()
    
    with open(CAPTCHA_FILE, 'wb') as f:
        f.write(data)
    
    save_cookies(cj, COOKIE_FILE)
    print(f"Captcha saved: {len(data)} bytes")
    print(f"Cookies saved")
    print("Now run: python hljcg_scraper.py <verify_code>")

def query_api(verify_code, page=1, page_size=10):
    """Step 2: query hljcg API with verify code"""
    if not os.path.exists(COOKIE_FILE):
        print("Error: no cookies saved. Run without args first to download captcha.")
        return None
    
    cj = load_cookies(COOKIE_FILE)
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    params = {
        'title': '',
        'region': REGION,
        'siteId': SITE_ID,
        'channel': CHANNEL,
        'currPage': str(page),
        'pageSize': str(page_size),
        'noticeType': NOTICE_TYPE,
        'cityOrArea': '',
        'purchaseManner': '',
        'openTenderCode': '',
        'purchaser': '',
        'agency': '',
        'purchaseNature': '',
        'operationStartTime': '',
        'operationEndTime': '',
        'verifyCode': verify_code,
        'selectTimeName': 'noticeTime',
        '_t': str(int(time.time() * 1000)),
    }
    
    url = 'https://hljcg.hlj.gov.cn/gpcms/rest/web/v2/info/selectInfoForIndex?' + urllib.parse.urlencode(params)
    text = http_get(op, url)
    return json.loads(text)

def fetch_all_pages(verify_code, max_pages=500):
    """Fetch all pages of results"""
    all_items = []
    
    # First page
    j = query_api(verify_code, page=1, page_size=20)
    if j is None or j['code'] != '200':
        print(f"Query failed: {j}")
        return []
    
    total = (j.get('data') or {}).get('total', 0)
    rows = (j.get('data') or {}).get('rows', [])
    all_items.extend(rows)
    
    total_pages = (total + 19) // 20
    print(f"Total: {total}, Pages: {total_pages}")
    
    for page in range(2, min(total_pages + 1, max_pages + 1)):
        try:
            j = query_api(verify_code, page=page, page_size=20)
            if j['code'] != '200':
                print(f"  Page {page}: error {j['code']} - {j.get('msg','')}")
                break
            rows = (j.get('data') or {}).get('rows', [])
            all_items.extend(rows)
            print(f"  Page {page}: {len(rows)} items (total: {len(all_items)})")
            time.sleep(0.5)
        except Exception as e:
            print(f"  Page {page}: {e}")
            break
    
    return all_items

if __name__ == '__main__':
    if len(sys.argv) < 2:
        download_captcha()
    else:
        verify_code = sys.argv[1]
        items = fetch_all_pages(verify_code)
        
        if items:
            # Save results
            output = {
                'source': 'hljcg.hlj.gov.cn',
                'region': '鸡西市',
                'url': 'https://hljcg.hlj.gov.cn/maincms-web/noticeInformationHlj',
                'fetched_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total': len(items),
                'items': items,
            }
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"\nSaved {len(items)} items to {DATA_FILE}")
            
            # Print summary
            budgets = [i for i in items if i.get('budget')]
            purchasers = set(i.get('purchaser', '') for i in items if i.get('purchaser'))
            print(f"Items with budget: {len(budgets)}")
            print(f"Unique purchasers: {len(purchasers)}")
        else:
            print("No items fetched.")
