
## 架构说明

本网站由两个机制协同运转，确保 24/7 可用：

### 机制一：GitHub Actions + Pages（主力 — 永不关机）

- 代码托管在 `github.com/rumengling123/jixi-caigou`
- **每天 08:30（北京时间）** GitHub 服务器自动运行：
  1. 抓取中国政府采购网 (scraper.py)
  2. 抓取采购意向公告 (scrape_bc_all.py → parse → build)
  3. 生成 HTML (build_html.py)
  4. 发布到 GitHub Pages (`https://rumengling123.github.io/jixi-caigou`)
- 网页上的「实时更新」按钮 → 打开 GitHub Actions 手动触发
- 永久免费、永不关机

### 机制二：本机 cloudflared 隧道（辅助 — 电脑在线时）

- 本机 `update_server.py` (监听 127.0.0.1:8088) 提供 /update 实时抓取
- cloudflared 隧道提供公网 URL
- 网页上的「实时更新」按钮 → 调用本机隧道 /update → 6 秒全量刷新
- 电脑关机则不可用（但不影响 GitHub Pages 访问）
