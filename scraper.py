# -*- coding: utf-8 -*-
"""
鸡西地区政府采购公告抓取器
- 按 9 个关键词（鸡西 + 8 个区县市）在中国政府采购网搜索候选公告
- 逐个打开详情页，提取「采购单位地址」作为地区归属依据（按实际单位地址归类）
- 支持增量：已抓过的 url 不再重复抓取详情页，每日更新只抓新公告，速度快
"""
import json, re, sys, io, os, time, urllib.request, urllib.parse
import gzip
import http.cookiejar
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# 鸡西全域：市本级 + 8 个区县市
# 一、区域关键词：命中“标题/采购人/项目地点”中含区县字样的项目（ccgp 的 kw 同时检索标题与采购人，
#    多数“地址在鸡西”的项目因项目地点或采购人地址含区县而被覆盖）
AREA_KEYWORDS = ["鸡西", "鸡冠区", "恒山区", "鸡东县", "城子河区", "梨树区", "麻山区", "密山市", "虎林市"]
# 二、特殊采购人关键词：单位全称中含“鸡西属地”标识、但标题/项目地点都不带区县字样的主体
#    （例如国家级/省级驻鸡西单位）。ccgp 的 kw 会检索采购人字段，故用单位全称兜底发现此类项目。
BUYER_KEYWORDS = ["珍宝岛湿地国家级自然保护区管理局"]
KEYWORDS = AREA_KEYWORDS + BUYER_KEYWORDS
DISTRICTS = ["城子河区", "梨树区", "麻山区", "鸡冠区", "恒山区", "鸡东县", "密山市", "虎林市", "鸡西市"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data.json")
# 抓取后自动发现、但暂未加入 BUYER_KEYWORDS 的候选采购人（名称不含区县但归属鸡西），供人工复核补充
SPECIAL_BUYERS_CANDIDATES = os.path.join(BASE_DIR, "special_buyers_candidates.txt")
START_DATE = "2026:01:01"
END_DATE = datetime.now().strftime("%Y:%m:%d")
# 浏览器式请求头（政采网 WAF 会按“无会话/无 UA 的高频请求”判为频繁访问，必须带完整头+cookie）
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "http://search.ccgp.gov.cn/",
}
DETAIL_TIMEOUT = 25
WORKERS = 3
LIST_GAP = 4.0      # 列表翻页间隔（秒）
DETAIL_GAP = 0.8    # 详情页请求间隔（秒）

# 全局 cookie 会话：首次请求前访问一次搜索首页建立会话，后续请求复用 cookie，避免被 WAF 判为“频繁访问”
_COOKIE_JAR = http.cookiejar.CookieJar()
_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_COOKIE_JAR))
_SESSION_READY = {"ok": False}

def ensure_session():
    """首次调用时访问搜索首页建立 cookie 会话；已建立则跳过。失败不影响后续（仅失去 cookie 加成）。"""
    if _SESSION_READY["ok"]:
        return
    try:
        req = urllib.request.Request("http://search.ccgp.gov.cn/", headers=HEADERS)
        with _OPENER.open(req, timeout=15) as _:
            pass
    except Exception:
        pass
    _SESSION_READY["ok"] = True

def http_get(url, timeout=DETAIL_TIMEOUT, retries=4):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with _OPENER.open(req, timeout=timeout) as r:
                raw = r.read()
            # 处理 gzip 压缩响应
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            # 政采网详情页 meta 标 utf-8（个别实为 GBK，先 utf-8 再退 gbk）
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                return raw.decode("gbk", "ignore")
        except Exception as e:
            last = e
            time.sleep(2 + attempt * 3)
    raise last if last else RuntimeError("http_get failed")

FREQ_MARK = "频繁访问"
RATE_LIMITED = {"hit": False}

def search_keyword(kw, page=1, retries=3):
    ensure_session()  # 首次自动建立 cookie 会话，绕过 WAF 频繁访问封锁
    params = {
        "searchtype": "1", "page_index": str(page), "bidSort": "0", "pinMu": "0",
        "bidType": "0", "dbselect": "bidx", "kw": kw,
        "start_time": START_DATE, "end_time": END_DATE, "timeType": "6",
    }
    url = "http://search.ccgp.gov.cn/bxsearch?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        html = http_get(url)
        if FREQ_MARK in html:
            wait = 3 + attempt * 3   # 3,6,9 秒，缩短避免超时窗口被耗尽
            print("  [限流] 关键词[%s] 第%d页被限流，%ds后重试" % (kw, page, wait))
            time.sleep(wait)
            continue
        items, total = parse_list(html)
        return items, total
    RATE_LIMITED["hit"] = True   # 全部重试仍被限流
    return [], 0

# 公告类型规范化：把列表页 <strong> 里的“XX公告”归一
_TYPE_NORM = {
    "公开招标公告": "公开招标", "公开招标": "公开招标",
    "询价公告": "询价", "竞争性谈判公告": "竞争性谈判", "竞争性谈判": "竞争性谈判",
    "单一来源公告": "单一来源", "单一来源": "单一来源",
    "资格预审公告": "资格预审", "资格预审": "资格预审",
    "邀请公告": "邀请", "中标公告": "中标", "中标（成交）结果公告": "中标",
    "更正公告": "更正", "其他公告": "其他", "其他": "其他",
    "竞争性磋商公告": "竞争性磋商", "竞争性磋商": "竞争性磋商",
    "成交公告": "成交", "终止公告": "终止",
}

def parse_list(html):
    items = []
    total = 0
    m = re.search(r"共找到\s*<em[^>]*>(\d+)</em>\s*条", html)
    if m:
        total = int(m.group(1))
    # 只在结果列表 ul（class 含 vT-srch-result-list-bid）内解析，避开顶部导航 <li>
    ul = re.search(r'<ul[^>]*vT-srch-result-list-bid[^>]*>(.*?)</ul>', html, re.S)
    scope = ul.group(1) if ul else html
    for blk in re.findall(r'<li>(.*?)</li>', scope, re.S):
        a = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', blk, re.S)
        if not a:
            continue
        url = a.group(1)
        if url.startswith("//"):
            url = "http:" + url
        elif url.startswith("/"):
            url = "http://www.ccgp.gov.cn" + url
        # 只保留指向公告详情的链接（过滤搜索/频道导航）
        if "ccgp.gov.cn/cggg/" not in url:
            continue
        # 标题：剥离 <font>/<strong> 等标签
        title = re.sub(r"<[^>]+>", "", a.group(2)).strip()
        tm = re.search(r"(\d{4})[-.](\d{2})[-.](\d{2})", blk)
        tstr = "%s.%s.%s" % (tm.group(1), tm.group(2), tm.group(3)) if tm else ""
        buyer = ""
        bm = re.search(r"采购人[:：]\s*([^<｜|]+)", blk)
        if bm:
            buyer = bm.group(1).strip(" ｜|\t")
        # 类型：优先取 <strong>（已在结果块内），其次标题里的 [类型]
        st = re.search(r"<strong[^>]*>\s*([^<]+?)\s*</strong>", blk)
        itype = ""
        if st:
            raw = st.group(1).strip()
            itype = _TYPE_NORM.get(raw, raw)
        if not itype:
            tm2 = re.search(r"\[(.*?)\]", title)
            if tm2:
                itype = _TYPE_NORM.get(tm2.group(1), tm2.group(1))
        items.append({"title": title, "url": url, "time": tstr, "buyer": buyer, "type": itype})
    return items, total

def extract_detail(url):
    """打开详情页，提取采购人地址/采购人/代理机构"""
    try:
        html = http_get(url)
    except Exception:
        return None
    if FREQ_MARK in html:
        # 限流：短暂重试一次
        time.sleep(5)
        try:
            html = http_get(url)
        except Exception:
            return None
    def field(label):
        m = re.search(label + r"</td>\s*<td[^>]*>(.*?)</td>", html, re.S)
        if m:
            return re.sub(r"<[^>]+>", "", m.group(1)).strip()
        return ""
    def normalize_amount(raw):
        raw = re.sub(r'[￥¥,（）()]', '', raw).strip()
        m = re.search(r'([\d.]+)\s*(万|元)', raw)
        if not m:
            return ""
        num = float(m.group(1))
        if '万' in (m.group(2) or ''):
            return "%.2f万元" % num
        else:
            wan = num / 10000
            return ("%.2f万元" % wan) if wan >= 1 else ("%.4f万元" % wan)
    addr = field("采购单位地址") or field("采购人地址")
    buyer = field("采购人")
    agency = field("代理机构") or field("采购代理机构")
    budget = ""
    budget_raw = field("预算金额") or field("采购预算") or \
                 field("中标金额") or field("成交金额") or field("合同金额")
    if budget_raw:
        budget = normalize_amount(budget_raw)
    if not budget:
        m = re.search(r'(?:中标|成交|合同|预算)金额[^：:]*[：:][\s]*(￥\s*[\d,.]+)\s*万?元?', html)
        if m:
            budget = normalize_amount(m.group(1))
    return {"addr": addr, "buyer": buyer, "agency": agency, "budget": budget}

def detect_region(title, buyer, addr, agency):
    """优先用实际单位地址，其次采购人名称，最后标题"""
    blob = " ".join([addr or "", buyer or "", title or "", agency or ""])
    for d in DISTRICTS:           # 区县优先
        if d in blob:
            return d
    return "鸡西市本级"

# 项目类别分类：ccgp 无现成“类别”字段，按标题/类型/采购人关键词启发式分类。
# 采用有序规则表：按优先级从上到下，第一个命中即定类（未命中归“其他”）。
# 顺序很重要：具体类别（软件/集成/维保）应排在前，宽泛的（信息化/硬件）靠后。
_CAT_RULES = [
    ("维保", re.compile(r"维保|运维|运营|物业|保安|保洁|养护|管护|托管|外包服务|监理|运行维护|维护|保养|修缮|维修(?!资金)")),
    ("信息化软件", re.compile(r"信息化|智慧|数字化|网络|智能|大数[据据]|电子政务|一网|信息(系统|平台)|软件|系统开发|应用开发|小程序|APP|管理系统|平台软件|数据库|云(?!计|南|雾)|数字化|源代码|定制开发")),
    ("集成", re.compile(r"集成|一体化|综合(?!执|行|治)|整体|弱电|安防|智能化(工程|系统|建设)|信息化(工程|建设)|指挥(中心|平台)|协同(平台|作战)")),
    ("硬件", re.compile(r"设备|硬件|电脑|服务器|车辆|仪器|器械|家具|办公|耗材|器材|无人机|显示屏|摄像机|空调|打印机|终端|机器|工具|材料|物资|装备|计算机|监控|投影|音响|广播|机车|雷达|传感器|机房")),
]
def classify_category(title, itype, buyer):
    blob = " ".join([title or "", itype or "", buyer or ""])
    for name, pat in _CAT_RULES:
        if pat.search(blob):
            return name
    return "其他"

def fetch_detail_worker(item):
    det = extract_detail(item["url"])
    if det:
        item["region"] = detect_region(item["title"], det["buyer"] or item["buyer"], det["addr"], det["agency"])
        item["buyer"] = det["buyer"] or item["buyer"]
        item["agency"] = det["agency"] or ""
        item["addr"] = det["addr"]
        if det.get("budget"):
            item["budget"] = det["budget"]
    else:
        item["region"] = detect_region(item["title"], item["buyer"], "", "")
        item["addr"] = ""
        item["agency"] = item.get("agency", "")
    item["category"] = classify_category(item["title"], item.get("type", ""), item["buyer"])
    return item

def main():
    incremental = "--full" not in sys.argv
    known = {}
    if incremental and os.path.exists(DATA_PATH):
        try:
            old = json.load(open(DATA_PATH, encoding="utf-8"))
            for it in old.get("items", []):
                known[it["url"]] = it
        except Exception:
            known = {}
    print("已有记录: %d 条（增量模式）" % len(known) if incremental else "全量模式")

    # 限流探测：若搜索接口当前被限流，本次直接中止（保留已有数据，不发布空/旧数据）。
    # 注：政采网“频繁访问”多为无会话/无 cookie 触发，已通过 ensure_session() 建立 cookie 会话缓解；
    # 极少数情况为 IP 级临时封锁，需等待自然冷却（每日定时任务会自行重试）。
    RATE_LIMITED["hit"] = False
    ensure_session()
    probe_items, _ = search_keyword(KEYWORDS[0], 1)
    if RATE_LIMITED["hit"]:
        print("  [限流] 搜索接口当前被封锁（IP: 频繁访问），本次更新中止。已有数据保留，稍后定时任务会自动重试。")
        sys.exit(3)

    seen = set(known.keys())
    candidates = []
    for kw in KEYWORDS:
        page = 1
        kw_total = 0
        while True:
            items, total = search_keyword(kw, page)
            if page == 1:
                kw_total = total
            if not items:
                break
            new_here = 0
            for it in items:
                if it["url"] not in seen:
                    seen.add(it["url"])
                    candidates.append(it)
                    new_here += 1
            print("  关键词[%s] 第%d页 命中%d 新%d" % (kw, page, len(items), new_here))
            if new_here == 0 or len(items) < 20 or (kw_total and page * 20 >= kw_total):
                break
            page += 1
            time.sleep(LIST_GAP)
    print("新增候选: %d 条，开始抓取详情页..." % len(candidates))

    # 若全程被限流且未抓到任何新数据，中止本次更新（保留已有数据，不发布空/旧数据）
    if not candidates and RATE_LIMITED["hit"]:
        print("  [限流] 全程被封锁且未抓到新数据，本次更新中止（保留已有数据）。稍后定时任务会自动重试。")
        sys.exit(3)

    # 已有记录直接复用（无需重新抓详情）
    result_items = list(known.values())
    # 新候选：并发抓详情
    if candidates:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = [ex.submit(fetch_detail_worker, it) for it in candidates]
            done = 0
            for f in as_completed(futs):
                result_items.append(f.result())
                done += 1
                if done % 50 == 0:
                    print("  已处理详情 %d/%d" % (done, len(candidates)))

    # 去重保险 + 按时间倒序
    uniq = {}
    for it in result_items:
        uniq[it["url"]] = it
    items = sorted(uniq.values(), key=lambda x: x.get("time", ""), reverse=True)
    # 兜底：确保每条都有 category（增量复用的旧记录可能缺失）
    for it in items:
        if "category" not in it or not it.get("category"):
            it["category"] = classify_category(it.get("title", ""), it.get("type", ""), it.get("buyer", ""))

    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "range": ["2026-01-01", datetime.now().strftime("%Y-%m-%d")],
        "keywords": KEYWORDS,
        "total": len(items),
        "items": items,
    }
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("完成。共 %d 条，已写入 %s" % (len(items), DATA_PATH))
    from collections import Counter
    c = Counter(i["region"] for i in items)
    for k, v in c.most_common():
        print("  %s: %d" % (k, v))

    # 自动发现“名称不含区县关键词、但地址归属鸡西属地”的采购人（潜在漏网特殊主体）
    # 这些主体不会被 AREA_KEYWORDS 命中，需人工确认后加入 BUYER_KEYWORDS。
    try:
        seen_buyers = set()
        cands = []
        for it in items:
            b = (it.get("buyer") or "").strip()
            if not b or b in seen_buyers:
                continue
            region_ok = it.get("region") in DISTRICTS
            has_area = any(k in b for k in AREA_KEYWORDS)
            in_buyer_kw = any(k in b for k in BUYER_KEYWORDS)
            if region_ok and not has_area and not in_buyer_kw:
                seen_buyers.add(b)
                cands.append("%s\t%s\t%s" % (b, it.get("region"), it.get("time")))
        with open(SPECIAL_BUYERS_CANDIDATES, "w", encoding="utf-8") as f:
            f.write("# 名称不含区县关键词但归属鸡西属地的采购人候选（请人工确认后加入 BUYER_KEYWORDS）\n")
            f.write("# 格式: 采购人全称\t归属区县\t示例公告时间\n")
            f.write("\n".join(cands) + ("\n" if cands else ""))
        if cands:
            print("[提示] 发现 %d 个特殊采购人候选，已写入 %s（确认后可加入 BUYER_KEYWORDS）"
                  % (len(cands), os.path.basename(SPECIAL_BUYERS_CANDIDATES)))
    except Exception as e:
        print("[warn] 特殊采购人候选发现跳过: %r" % e)

if __name__ == "__main__":
    main()
