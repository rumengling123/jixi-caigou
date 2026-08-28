# 鸡西采购站点 — hljcg 数据恢复 + 意向数据补回修复

## 日期
2026-08-13

## 问题
用户报告"全部来源平台只剩 hljcg 和中国政府采购网了"，实际是三个叠加问题：

1. **数据退化**：`hljcg_daily.py` 是「全量覆盖」模式。每天 08:30 重跑时若验证码中途过期（虎林/密山/珍宝岛/兴凯湖等关键词没跑到），就用不完整数据覆盖掉之前补抓的完整数据。
   - 历史数据从 6112 条 → 2646 条 → 2212 条 → 1530 条 持续退化
   - 8-13 早自动更新后：虎林市仅 1 条、密山市仅 21 条（正常应各 400+ 条）

2. **意向数据丢失**：整合 hljcg 官方数据时，`build_html.py` 重写后不再加载 `hljcg_yixiang.json`（555 条采购意向，bidchance 转载），导致来源平台少了「黑龙江政府采购(意向)」这一项。

3. **数据源下拉框**：只剩 hljcg + 中国政府采购网 2 项（另 3 条外部平台数据仍存在但数量极少）。

## 修复

### 1. 恢复完整数据基线
从 git 历史 commit `fcfcc4a` 恢复最完整的 6112 条 hljcg 数据，与当前 1530 条合并去重（键 id/noticeId），得到 **6119 条**。

### 2. hljcg_daily.py 改增量模式
- 启动时先加载 `hljcg_jixi_full.json` 已有数据，验证码中途过期时不再覆盖丢失历史
- 只在有新条目时追加

### 3. catchup.py 修复
- 复用 WAF cookies（`hljcg_waf_cookies.json`），保证验证码与会话一致
- 补抓关键词加回「密山」

### 4. build_html.py 重新加载意向数据
- 重新加载 `hljcg_yixiang.json`（555 条采购意向）
- 合并到 all_items，参与去重（意向数据 source=黑龙江政府采购(意向)，不会被 hljcg 的 contentId 去重吞掉）
- 给意向数据也打负责人标签

## 结果
- 站点 Total：**8330 条**（ccgp 1653 + 其他平台 3 + hljcg 6119 + 意向 555）
- 来源分布：hljcg 6119 / 中国政府采购网 1653 / 黑龙江政府采购(意向) 555 / 鸡西矿业 1 / 北大荒 1 / 阳光采购 1
- hljcg 地区分布恢复：虎林市 1485、密山市 1130、鸡西市本级 1074、鸡东县 922、恒山区 266、梨树区 225、滴道区 223、鸡冠区 150、麻山区 146、城子河区 97
- 已发布 Surge（Tokyo 节点已恢复 ✔，jixi-caigou.surge.sh 200 OK）
- git commit `1d1d270` 已推送 origin/main

## 遗留注意
- `hljcg_jixi_full_restore.json` 是临时恢复文件（含 BOM 版本），可删除
- 大量临时探路脚本（probe_*.py / test_*.py / captcha*.png 等）未纳入 git，属本机临时文件
- 每日 08:30 自动更新链路：QClaw Cron（本机跑 hljcg）+ GitHub Actions（云端跑 ccgp/bidchance/发布），hljcg 因验证码仍需本机中国 IP 执行
