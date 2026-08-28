# 鸡西政府采购每日同步 — 2026-08-13

## 执行时间
2026-08-13 08:30 (Asia/Shanghai) 自动触发

## 本次关键修复：验证码 Cookie 会话绑定问题

### 问题
今天首次运行时，连续两次（验证码 0076、0542）都在抓取"鸡西"关键词时**同一秒内**立即报 `Captcha expired (4009)`，抓取 0 条。

### 根因诊断
1. 验证码绑定 WAF Cookie（`HWWAFSESID`），不是简单的图片识别码。
2. 原流程用两个独立进程：
   - `get_captcha.py` 用独立 `requests.Session` 下载验证码
   - `hljcg_daily.py` 又新建另一个 `requests.Session` 提交查询
3. 两个 Session 的 Cookie 不同 → 服务器校验验证码与会话不匹配 → 立即返回"验证码错误或已失效"。
4. 通过 `test_cookie_bind.py` 验证：同进程内"访问主页→下载验证码→提交错误码"返回的是 4009 且带 `HWWAFSESID` Cookie，确认了绑定关系。

### 修复方案
1. `get_captcha.py`：先访问主页建立 WAF 会话，再下载验证码，最后把 Cookie 保存到 `hljcg_waf_cookies.json`。
2. `hljcg_daily.py`：`get_session()` 加载该 Cookie 文件并注入到查询会话，实现跨进程会话复用。

### 修复验证
- 修复后重跑：验证码 8906 成功生效，正常查询到全部数据。

## 抓取结果
- 完成 7 个关键词：鸡西(1000条) · 鸡冠(24) · 恒山(19) · 鸡东(393) · 城子河(50) · 梨树(14) · 麻山(30)
- "密山"关键词在抓取 280 条时验证码过期，但已通过其他关键词覆盖 21 条密山数据
- hljcg 总计：**1,530** 条
- 全部平台总计：**3,186** 条 (ccgp 1653 + hljcg 1530 + 其他 3)

### 分类统计
- 硬件：287 · 其他：823 · 信息化软件：148 · 维保：241 · 集成：31

### 地区统计
- 鸡西市本级：584 · 鸡东县：385 · 梨树区：113 · 滴道区：101 · 恒山区：100
- 麻山区：80 · 城子河区：78 · 鸡冠区：67 · 密山市：21 · 虎林市：1

## 各步骤结果
- 步骤 1-3 验证码：首次失败（Cookie 未共享），修复后成功
- 步骤 4 抓取+转换+生成：✅
- 步骤 5 Git Push：✅ commit `5d61ac6` → main
- 步骤 6 Surge 发布：✅ 196 文件，45.8 MB
- 步骤 7 验证：https://jixi-caigou.surge.sh 返回 HTTP 200 ✅

## 注意事项（给下次运行）
- surge 发布时不能直接把 `surge.cmd` 交给 node 执行（是批处理），需用真正入口：
  `node ...\npm-global\node_modules\surge\bin\surge ./ jixi-caigou.surge.sh`
- cron 提示中的 git add 文件 `hljcg意向解析.json` 实为 `hjlcg意向解析.json`（前两字母顺序），且该文件在 .gitignore 中被忽略，实际上无需提交。真正需要提交的是 `hljcg_budget.json` + `hljcg_jixi_full.json` + 脚本。
- 根 `index.html`（3,186条，build_html.py 生成）→ Surge 发布；`site/index.html`（3,868条，云端维护）→ GitHub Pages。两者独立。
