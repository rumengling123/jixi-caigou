# 鸡西政府采购网站每日同步报告 - 2026-08-22

## 任务ID: cron:48d26195-7fa0-48a0-9224-fbb580dbeff8

## 执行时间
2026-08-22 08:30 (Asia/Shanghai)，约 08:32 完成。

## 各步骤结果

### 步骤 1：下载验证码 ✅ 成功
- `get_captcha.py` 正常下载验证码到 `captcha_daily.png` (1744 bytes)
- WAF cookies 保存到 `hljcg_waf_cookies.json`

### 步骤 2：OCR 识别验证码 ⚠ 重试成功
- 第 1 次超时（image 模型 57 秒无响应）
- 第 2 次成功识别：**0765**

### 步骤 3：写入验证码 ✅ 成功
- 4 字节 "0765" 写入 `hljcg_verify_code.txt`

### 步骤 4：全量抓取+转换+生成 ⚠ 部分成功 — 0 新增
- 增量模式启动：已加载 6132 条历史数据
- 验证 "鸡西" 关键词时**验证码已过期**，中止关键词循环
- `hljcg_jixi_full.json`：6132 items, 18 MB
- `hljcg_budget.json`：6132 items, 9.15 MB
- `鸡西市政府采购项目统计.html` + `index.html`：各 9.6 MB
- **本次新增 0 条公告**（仅 ran `convert_hljcg.py` 和 `build_html.py` 重建输出文件）
- 总计 Total 8416 条（ccgp 1726 + hljcg 6132 + yixiang 555 + other 3）

### 步骤 5：推送到 GitHub ⚠ 部分成功
- `git add`：提示 `hljcg意向解析.json` 不存在，跳过；`index.html` 和 `鸡西市政府采购项目统计.html` 被 `.gitignore` 忽略（历史规则，保持现状）
- `git commit`：`b83c98a auto: daily hljcg sync [skip ci]`
- `git push origin main`：`fd75fa2..b83c98a main -> main` ✅

### 步骤 6：发布到 Surge ❌ 失败
- Surge CLI 0.34.0 通过 npm-global 安装在 `C:\Users\Admin\AppData\Roaming\QClaw\npm-global\`
- 尝试 `SURGE_LOGIN` + `SURGE_TOKEN`（从 `.netrc` 读取的 token）：**Invalid token**
- 直接调用 `surgeSDK.token({user, pass})` 拿新 token：**request did not complete**
- 直接访问 `https://surge.surge.sh`：**socket hang up**（证书 expired）
- 直接访问 `https://jixi-caigou.surge.sh`：**socket hang up**
- HTTP 访问 43.230.161.215:**ECONNRESET**

**根本原因：surge.sh 服务端 SSL 证书过期**（DNS 解析正确返回 A/AAAA 记录，但 TLS 握手失败）。这是 surge 服务端故障，超出本地能控制的范围。

### 步骤 7：网站可访问性 ❌ 不可访问
- 由于 surge.surge.sh 证书过期，`https://jixi-caigou.surge.sh` 当前**全球无法访问**
- 网站本身的 HTML/JSON 数据已经更新到最新（2026-08-22 08:32 生成）
- 待 surge 服务端修复证书后，可在 surge 控制台重试部署

## 关键文件
- `hljcg_budget.json` 9.15 MB — 鸡西完整数据（含预算）
- `hljcg_jixi_full.json` 18 MB — 抓取原始数据
- `鸡西市政府采购项目统计.html` 9.6 MB — 统计展示页
- `index.html` 9.6 MB — site/ 目录首页（surge 部署用）
- GitHub: https://github.com/rumengling123/jixi-caigou（main b83c98a）

## 后续行动建议
1. 等 surge.sh 证书恢复后，重跑 step 6：`cd ccgp_jixi && surge.cmd ./ jixi-caigou.surge.sh`
2. 或者可考虑改用其他 CDN（Vercel / Cloudflare Pages / Netlify），GitHub 仓库已就绪可直接接入
3. hljcg 网站验证码过期很快（约 30-60 秒），可考虑在脚本里 OCR 后立即发起抓取（已经是这样，但 WAF 仍有自己的过期窗口）
