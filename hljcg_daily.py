#!/usr/bin/env python3
"""
hljcg_daily.py - Daily automated scrape of hljcg.hlj.gov.cn 鸡西采购公告
Reads OCR'd verify code from hljcg_verify_code.txt, searches all keywords, saves + converts.
Run: python3 hljcg_daily.py
"""
import json, os, sys, re, time, random
from datetime import datetime
import requests
import urllib3
urllib3.disable_warnings()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS = ['鸡西', '鸡冠', '恒山', '鸡东', '城子河', '梨树', '麻山', '密山', '虎林', '珍宝岛', '兴凯湖']
SITE_ID = '94c965cc-c55d-4f92-8469-d5875c68bd04'
CHANNEL_ID = 'c5bff13f-21ca-4dac-b158-cb40accd3035'
API_BASE = 'https://hljcg.hlj.gov.cn'
NOTICE_TYPE = '00101'
PAGE_SIZE = 100

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)

def get_session():
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': f'{API_BASE}/maincms-web/noticeInformationHlj',
        'Origin': API_BASE,
    })
    # Reuse WAF cookies saved by get_captcha.py so the verify code stays valid
    cookie_file = os.path.join(BASE_DIR, 'hljcg_waf_cookies.json')
    if os.path.exists(cookie_file):
        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            for name, value in cookies.items():
                s.cookies.set(name, value, domain='hljcg.hlj.gov.cn')
            log(f'Loaded {len(cookies)} WAF cookie(s) from file')
        except Exception as e:
            log(f'WARN: failed to load cookies: {e}')
    return s

def read_verify_code():
    """Read verify code from file (written by AI OCR)"""
    vf = os.path.join(BASE_DIR, 'hljcg_verify_code.txt')
    for attempt in range(30):  # wait up to 30 seconds
        if os.path.exists(vf):
            with open(vf, 'r', encoding='utf-8') as f:
                code = f.read().strip()
            if len(code) == 4:
                os.remove(vf)
                return code
        time.sleep(1)
    return ''

def fetch_pages(session, keyword, verify_code):
    """Fetch all pages for a keyword, return items list"""
    items = []
    page = 1
    while True:
        params = {
            'title': keyword,
            'region': '',
            'siteId': SITE_ID,
            'channel': CHANNEL_ID,
            'currPage': page,
            'pageSize': PAGE_SIZE,
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
            '_t': int(time.time() * 1000),
        }
        try:
            resp = session.get(f'{API_BASE}/gpcms/rest/web/v2/info/selectInfoForIndex',
                              params=params, verify=False, timeout=30)
            data = resp.json()
            code = data.get('code', '')
            if code == '4009':
                # Captcha expired - need new one
                return items, 'captcha_expired'
            if code != '200':
                log(f'  API error: {resp.text[:200]}')
                break

            rows = data.get('data', {}).get('rows', [])
            total = data.get('data', {}).get('total', 0)
            items.extend(rows)

            if page == 1:
                log(f'  Keyword="{keyword}" total={total} pages={-(-total//PAGE_SIZE)}')

            if page * PAGE_SIZE >= total or not rows:
                break
            page += 1
            time.sleep(random.uniform(0.8, 1.5))
        except Exception as e:
            log(f'  ERROR page {page}: {e}')
            time.sleep(2)
            break
    return items, 'ok'


def main():
    log('=== hljcg daily scrape start ===')

    # Read verify code
    log('Waiting for verify code in hljcg_verify_code.txt...')
    verify = read_verify_code()
    if not verify:
        log('ERROR: No verify code received after 30s')
        sys.exit(1)
    log(f'Got verify code: {verify}')

    session = get_session()

    # 增量模式：先加载已有数据，避免验证码中途过期时覆盖丢失历史数据
    raw_file = os.path.join(BASE_DIR, 'hljcg_jixi_full.json')
    all_items = []
    seen = set()
    if os.path.exists(raw_file):
        try:
            with open(raw_file, 'r', encoding='utf-8') as f:
                old = json.load(f)
            for it in old.get('items', []):
                cid = it.get('id', '') or it.get('noticeId', '')
                if cid and cid not in seen:
                    seen.add(cid)
                    all_items.append(it)
            log(f'Incremental mode: loaded {len(all_items)} existing items')
        except Exception as e:
            log(f'WARN: failed to load existing data: {e}')

    for kw in KEYWORDS:
        log(f'Fetching: {kw}')
        items, status = fetch_pages(session, kw, verify)

        if status == 'captcha_expired':
            log(f'Captcha expired during keyword "{kw}", got {len(items)} items so far, stopping')
            # Save partial
            break

        added = 0
        for it in items:
            cid = it.get('id', '') or it.get('noticeId', '')
            if cid and cid not in seen:
                seen.add(cid)
                all_items.append(it)
                added += 1
        log(f'  Added {added} unique (total unique: {len(all_items)})')

    # Save raw
    output = {
        'source': 'hljcg.hlj.gov.cn',
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total': len(all_items),
        'keywords': KEYWORDS,
        'items': all_items,
    }
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)
    log(f'Saved {len(all_items)} items to hljcg_jixi_full.json ({os.path.getsize(raw_file)} bytes)')

    # Step 2: Convert to standard format
    log('Running convert_hljcg.py...')
    import subprocess
    py = sys.executable
    subprocess.run([py, os.path.join(BASE_DIR, 'convert_hljcg.py')], check=True)

    # Step 3: Build HTML
    log('Running build_html.py...')
    subprocess.run([py, os.path.join(BASE_DIR, 'build_html.py')], check=True)

    log('=== hljcg daily scrape complete ===')


if __name__ == '__main__':
    main()
