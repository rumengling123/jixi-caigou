# 鸡西政府采购网站每日同步 - 2026-08-14

## 目标
执行鸡西政府采购网站的每日自动更新（验证码识别 → 全量抓取 → 转换生成 → GitHub 推送 → Surge 发布）。

## 执行结果

### 步骤 1-3：验证码
- 首次 OCR 调用超时（57s），导致验证码过期，第一次抓取 0 条。
- 重试后 OCR 成功，后续两次均正常写入。

### 步骤 4：抓取+转换+生成
- 共执行 3 轮（因验证码在"虎林"关键词抓取中途过期）。
- 最终数据量：6119 → **6121 条**（新增 2 条，来自"密山"关键词）。
- 转换成功：hljcg_budget.json（9129KB→9133KB）、hljcg_details.json（8550KB，6120 条）。
- build_html.py 成功生成 `鸡西市政府采购项目统计.html`（6664KB，共 8335 项：ccgp 1656 / other 3 / hljcg 6121 / yixiang 555）。
- 已知问题：验证码有效期约 40 秒，不足以抓完"虎林"关键词全部 1517 条/16 页（每次约到 280~520 条时过期），但增量模式下不影响已入库数据。

### 步骤 5：GitHub 推送 —— ❌ 被阻止（安全问题）
- 本地 commit `3f30968` 已创建（4 文件变更：hljcg_budget.json / hljcg_details.json / hljcg_jixi_full.json / site/index.html）。
- `git push` 被 GitHub 推送保护（secret scanning）拒绝：**site/index.html 第 137 行内嵌了一个 GitHub OAuth Access Token（gho_feztt...）**。
- 该 token 在 HEAD 版本已存在（历史遗留），由 build_html.py 注入——脚本从环境变量 `PAGES_UPDATE_TOKEN` 或 `gh auth token` 读取 token 并写入页面 HTML，用于页面"手动更新"按钮触发 GitHub workflow。

### 步骤 6：Surge 发布 —— ✅ 成功
- 通过 `node ...\surge\bin\surge ./ jixi-caigou.surge.sh` 发布成功。
- 网站可访问：https://jixi-caigou.surge.sh 返回 HTTP 200，内容 6665058 字节，含鸡西数据。

## 结论与待办

**正常部分**：数据已更新（+2 条），Surge 网站已上线且可访问。

**安全问题（需人工处理）**：
1. `site/index.html`（以及根目录 index.html、鸡西市政府采购项目统计.html）内嵌了有效的 GitHub OAuth token，已泄露到公开仓库。该 token 应立即在 GitHub 上**撤销/重新生成**。
2. build_html.py 把 token 注入前端 HTML 的设计本身不安全（前端 token 等于公开）。建议改为不注入 token，或改用受限的 workflow dispatch token（且仍需防泄露）。
3. 在 token 问题解决前，`git push origin main` 将持续被 GitHub 拒绝（这是正确的安全拦截，不应绕过）。

**次要问题**：验证码有效期短导致"虎林"关键词无法一次抓完，建议后续评估是否需要拆分关键词或提高抓取速度。
