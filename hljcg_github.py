"""
hljcg_github.py — GitHub Actions 版黑龙江政府采购网抓取
使用 Tesseract OCR 识别验证码（Linux 环境）
"""
import json, os, sys, time, random, io, re
import requests
import urllib3
urllib3.disable_warnings()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS = ['鸡西', '鸡冠', '恒山', '鸡东', '城子河', '梨树', '麻山', '密山', '虎林', '珍宝岛', '兴凯湖']
SITE_ID = '94c965cc-c55d-4f92-8469-d5875c68bd04'
CHANNEL_ID = 'c5bff13f-21ca-4dac-b158-cb40accd3035'
API_BASE = 'https://hljcg.hlj.gov.cn'
PAGE_SIZE = 100
MAX_RETRIES = 5  # 验证码 OCR 重试次数

def ocr_captcha(image_bytes):
    """使用 Tesseract OCR 识别验证码，支持多种预处理策略"""
    try:
        from PIL import Image, ImageFilter, ImageOps
        import pytesseract
    except ImportError:
        print("ERROR: PIL/pytesseract not installed", file=sys.stderr)
        return None

    img = Image.open(io.BytesIO(image_bytes))

    # 策略列表：(描述, 处理后的图片)
    strategies = []

    # 策略 1: 原图直接 OCR
    strategies.append(('raw', img))

    # 策略 2: 灰度 + resize 2x
    gray = img.convert('L')
    gray2x = gray.resize((img.width * 3, img.height * 3), Image.LANCZOS)
    strategies.append(('gray_2x', gray2x))

    # 策略 3: 灰度 + Otsu 二值化 + resize
    gray_arr = list(gray.getdata())
    threshold = _otsu_threshold(gray_arr)
    if threshold > 0:
        bw = gray.point(lambda p: 255 if p > threshold else 0)
        bw2x = bw.resize((img.width * 3, img.height * 3), Image.LANCZOS)
        inverted = ImageOps.invert(bw2x)
        strategies.append(('otsu_inv_2x', inverted))

    # 策略 4: 自适应阈值
    try:
        # manual adaptive: divide image into blocks
        bw_adaptive = _adaptive_threshold(gray, block_size=11, c_val=10)
        bw_ad = Image.fromarray(bw_adaptive, mode='L')
        bw_ad2x = bw_ad.resize((img.width * 3, img.height * 3), Image.LANCZOS)
        strategies.append(('adaptive_2x', bw_ad2x))
    except:
        pass

    # 策略 5: 灰度 + 锐化
    try:
        sharp = gray.filter(ImageFilter.SHARPEN)
        sharp2x = sharp.resize((img.width * 3, img.height * 3), Image.LANCZOS)
        strategies.append(('sharpen_2x', sharp2x))
    except:
        pass

    for name, proc_img in strategies:
        try:
            # 只识别数字
            text = pytesseract.image_to_string(
                proc_img,
                config='--psm 7 -c tessedit_char_whitelist=0123456789'
            ).strip()
            # 只保留 4 位数字
            digits = re.sub(r'\D', '', text)
            if len(digits) >= 3 and len(digits) <= 5:
                # 如果 5 位，取后 4 位；如果 3 位，补 0
                if len(digits) == 5:
                    digits = digits[-4:]
                elif len(digits) == 3:
                    digits = '0' + digits
                if len(digits) == 4:
                    print(f"  OCR [{name}]: {text!r} -> {digits}")
                    return digits
            else:
                print(f"  OCR [{name}]: {text!r} (len={len(digits)}, skip)")
        except Exception as e:
            print(f"  OCR [{name}] error: {e}")

    return None


def _otsu_threshold(pixels):
    """Otsu 二值化阈值计算"""
    hist = [0] * 256
    for p in pixels:
        hist[p] += 1
    total = len(pixels)
    sum_all = sum(i * hist[i] for i in range(256))
    sum_b, w_b, w_f = 0, 0, 0
    max_var, threshold = 0, 0
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_all - sum_b) / w_f
        var_between = w_b * w_f * (m_b - m_f) ** 2
        if var_between > max_var:
            max_var = var_between
            threshold = t
    return threshold


def _adaptive_threshold(gray_img, block_size=11, c_val=10):
    """简化的自适应二值化"""
    import numpy as np
    arr = np.array(gray_img, dtype=np.float64)
    h, w = arr.shape
    result = np.zeros((h, w), dtype=np.uint8)
    half = block_size // 2
    for i in range(h):
        for j in range(w):
            i1, i2 = max(0, i - half), min(h, i + half + 1)
            j1, j2 = max(0, j - half), min(w, j + half + 1)
            block = arr[i1:i2, j1:j2]
            thresh = np.mean(block) - c_val
            result[i, j] = 255 if arr[i, j] > thresh else 0
    return result


def main():
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': f'{API_BASE}/maincms-web/noticeInformationHlj',
    })

    # 尝试 OCR 验证码
    verify = None
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n[Attempt {attempt}/{MAX_RETRIES}] Downloading captcha...")
        try:
            resp = s.get(f'{API_BASE}/gpcms/rest/web/v2/index/getVerify',
                        params={'_t': int(time.time() * 1000)},
                        verify=False, timeout=15)
            if resp.status_code != 200:
                print(f"  getVerify failed: HTTP {resp.status_code}")
                time.sleep(2)
                continue

            verify = ocr_captcha(resp.content)
            if verify:
                print(f"  >> OCR SUCCESS: {verify}")
                break
            else:
                print(f"  OCR failed, retrying...")
                time.sleep(1)
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(2)

    if not verify:
        print("FATAL: Could not OCR captcha after all attempts", file=sys.stderr)
        # 尝试用已有数据继续
        existing_file = os.path.join(SCRIPT_DIR, 'hljcg_jixi_full.json')
        if os.path.exists(existing_file):
            print("Using existing data and skipping hljcg update")
            sys.exit(0)
        sys.exit(1)

    # 抓取所有关键词
    all_items = []
    seen = set()

    for kw in KEYWORDS:
        print(f"\nFetching: {kw}")
        page = 1
        kw_added = 0
        while True:
            params = {
                'title': kw,
                'region': '',
                'siteId': SITE_ID,
                'channel': CHANNEL_ID,
                'currPage': page,
                'pageSize': PAGE_SIZE,
                'noticeType': '00101',
                'verifyCode': verify,
                'selectTimeName': 'noticeTime',
                '_t': int(time.time() * 1000),
            }
            try:
                resp = s.get(f'{API_BASE}/gpcms/rest/web/v2/info/selectInfoForIndex',
                            params=params, verify=False, timeout=30)
                json_data = resp.json()
                code = json_data.get('code', '')
                if code == '4009':
                    print(f"  Captcha expired at page {page}")
                    break
                rows = json_data.get('data', {}).get('rows', [])
                total = json_data.get('data', {}).get('total', 0)
                if page == 1:
                    print(f"  total={total} pages={-(-total // PAGE_SIZE)}")

                added = 0
                for it in rows:
                    cid = it.get('id', '') or it.get('noticeId', '')
                    if cid and cid not in seen:
                        seen.add(cid)
                        all_items.append(it)
                        added += 1
                kw_added += added

                if page * PAGE_SIZE >= total or not rows:
                    break
                page += 1
                time.sleep(random.uniform(0.5, 1.0))
            except Exception as e:
                print(f"  ERROR: {e}")
                break
        print(f"  Added {kw_added} unique (total unique: {len(all_items)})")

    # 保存
    output = {
        'source': 'hljcg.hlj.gov.cn',
        'updated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total': len(all_items),
        'items': all_items,
    }
    output_path = os.path.join(SCRIPT_DIR, 'hljcg_jixi_full.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)
    print(f"\nSaved {len(all_items)} items ({os.path.getsize(output_path)} bytes)")

if __name__ == '__main__':
    main()
