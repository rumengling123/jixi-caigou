# hljcg_daily_sync — 2026-08-27 (Thu 08:30 Asia/Shanghai)

## 执行步骤与结果

| 步骤 | 描述 | 结果 |
|---|---|---|
| 1 | 下载验证码 `get_captcha.py` | ✅ 1700 bytes → captcha_daily.png，WAF cookies 已保存 |
| 2 | OCR 识别验证码 | ⚠ 首次超时，第二次返回 `3267` |
| 3 | 写入 `hljcg_verify_code.txt` | ✅ "3267"（4 字节） |
| 4 | 执行 `hljcg_daily.py` | ⚠ 验证码在第一个关键字"鸡西"即过期，0 条新抓取；脚本按增量模式保存了现有 6156 条数据并完成转换+HTML 生成 |
| 5 | Git push | ✅ commit `2709d23` pushed to origin/main |
| 6 | Surge 发布 | ✅ `jixi-caigou.surge.sh` 发布成功 |
| 7 | 网站可访问性 | ✅ HTTP 200，9,680,451 字节 |

## 关键数据

- 新抓取公告数：**0 条**（验证码在第一个关键字即失效，本轮无新增）
- 现有全量：6156 条（hljcg_jixi_full.json）
- 鸡西地区：6156 条（hljcg_budget.json）
  - 类别分布：其他 3343 / 硬件 1111 / 维保 945 / 信息化软件 649 / 集成 108
  - 区域分布：虎林市 1451 / 鸡西市本级 1517 / 密山市 1145 / 鸡东县 921 / 恒山区 253 / 梨树区 236 / 滴道区 228 / 麻山区 151 / 鸡冠区 147 / 城子河区 107
- 总统计（含 ccgp/其他/意向）：8487 条
  - ccgp: 1773 / other platforms: 3 / hljcg: 6156 / 意向: 555
- HTML：`鸡西市政府采购项目统计.html` 6,738,539 bytes
- details：`hljcg_details.json` 8,614,912 bytes (6155 entries)

## 风险与备注

- 验证码识别服务出现一次超时（>58s），但重试成功拿到了数字。
- 验证码在站内请求开始后立即失效 → 增量抓取完全失败。后续可能需要在每个关键字重新下载验证码 + 注入 WAF cookies，或缩短单关键字请求间隔并增加 retry。
- cron 触发附带的内嵌图片看起来像是另一个验证码预览（`2 2 9 6` 拼图），但本轮未使用它。
- 本次 commit 仅包含 budget/full/details/index.html 的 5 行微调（属于 hljcg_daily.py 重写 timestamp 元数据或 normalize 后的正常输出）。

## 下一步建议

1. 在 `hljcg_daily.py` 中加入 per-keyword 验证码刷新：检测 "captcha expired" 立即重新下载 → OCR → 注入 cookies → 继续。
2. 提升 OCR 服务稳定性，必要时本地化（Tesseract + 简单预处理）。
3. 监控首次 OCR 失败的频次，超阈值时改用 fallback 验证码图（cron 触发中可见的图片）。