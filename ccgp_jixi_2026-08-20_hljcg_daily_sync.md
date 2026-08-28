# 鸡西政府采购每日同步 - 2026-08-20

## 执行结果

| 步骤 | 状态 | 说明 |
|------|------|------|
| 1. 下载验证码 | ✅ | `captcha_daily.png` 1699 bytes，WAF cookies 已落盘 |
| 2. OCR 识别 | ✅ | 识别为 **3381**（image 工具超时后改用本地 PIL 放大 + image 重试成功） |
| 3. 写入验证码 | ✅ | `hljcg_verify_code.txt` 已写入 4 位数字 |
| 4. 全量抓取 | ⚠️ 部分 | 验证码在第一个关键词 "鸡西" 时失效，导致本次未新增条目（still 6132） |
| 5. Git 提交推送 | ✅ | commit `8ad6146` push 到 `main` |
| 6. Surge 发布 | ✅ | `Success! - Published to jixi-caigou.surge.sh` |
| 7. 站点可访问 | ✅ | https://jixi-caigou.surge.sh/ 返回 HTTP 200，~9.6MB |

## 数据统计

- **hljcg 鸡西条目**：6132（与上次持平，本次无新增）
- **本次抓取新公告**：0（验证码在搜索阶段过期）
- **总条目**：8404（ccgp 1714 + 其它 3 + hljcg 6132 + 意向 555）
- **区域分布**：虎林市 1451 / 鸡西市本级 1508 / 密山市 1145 / 鸡东县 918 / …
- **类别分布**：其他 3331 / 硬件 1106 / 维保 941 / 信息化软件 647 / 集成 107

## 本次提交变更（commit 8ad6146）

```
hljcg_budget.json        M
hljcg_details.json       M
hljcg_jixi_full.json     M
site/index.html          M
site/hljcg_details.json  A
```

## 备注

- `hljcg意向解析.json` 文件不存在（之前已删除），git add 时跳过
- 根目录的 `index.html` / `鸡西市政府采购项目统计.html` 被 `.gitignore` 忽略，实际发布版本以 `site/index.html` 为准
- surge 部署交互结束时提示 "verify your account with `surge verify`"，属历史未验证提示，不影响发布
- 验证码仅可用 1 次，下个 cron 周期需重新下载+识别
