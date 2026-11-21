# ANARI Charge GSC 收录复查报告（2026-10-26 晚，第二次补跑）

- 执行窗口：2026-10-26 18:44–19:28（CST，UTC+8）
- 执行方式：Kimi WebBridge 控制本机浏览器（GSC 已登录，资源 `sc-domain:anaricharge.com`，英文界面），会话 `gsc-verify`
- 背景：10-24 20:07 首跑因任务配置错误（workspace.path 越界）触发即失败；10-24 23:18 补跑遇 Google 检索后端故障 0/8；本次为故障恢复后的第二次补跑，由简报会话内联执行（自动化手动运行因「会话忙」被推迟，见运行记录 `run_d1ef66c9`）
- 红线自查：未改动 GSC 任何设置；未触碰仓库代码；未点击任何 "REQUEST INDEXING"（无符合补发条件的状态）

## 一、结论（3 行）

1. **收录率 8/8**——8 个 URL 全部确认「URL is on Google / Page is indexed」（每个均有截图留证，见第四节）。10-21 批次的 5 篇悬置状态全部解除。
2. **连接器新文章 `ccs1-vs-ccs2-nacs-connector-guide`：已收录**（10-26 新鲜验证，与 10-23 三次复查一致）。
3. **未收录清单：无；补发请求清单：无。连接器词破零：仍未破零**（详见第三节）。

## 二、8 URL 对照表

URL 前缀均为 `https://www.anaricharge.com`。

| # | URL | 请求索引时间 | 今次状态（10-26 晚，新鲜验证） | 是否补发请求 |
|---|---|---|---|---|
| 1 | /blog/apartment-condo-ev-charging-roi | 2026-10-21 19:50 | ✅ URL is on Google / Page is indexed | 否（已收录，不符合补发条件） |
| 2 | /blog/ev-charging-carbon-credits-lcfs | 2026-10-21 19:50 | ✅ URL is on Google / Page is indexed | 否 |
| 3 | /blog/used-ev-charging-equipment | 2026-10-21 19:50 | ✅ URL is on Google / Page is indexed | 否 |
| 4 | /blog/ev-charging-revenue-share-hotels-parking | 2026-10-21 19:50 | ✅ URL is on Google / Page is indexed | 否 |
| 5 | /blog/bess-valuation-software | 2026-10-21 19:50 | ✅ URL is on Google / Page is indexed | 否 |
| 6 | /blog/ev-charging-station-operating-cost（对照） | 2026-10-21 19:50 | ✅ URL is on Google / Page is indexed（与基线一致） | 否 |
| 7 | /blog/nevi-grants-ev-charging-station（对照） | 2026-10-21 19:50 | ✅ URL is on Google / Page is indexed（与基线一致） | 否 |
| 8 | /blog/ccs1-vs-ccs2-nacs-connector-guide（重点） | 2026-10-23 12:30 | ✅ URL is on Google / Page is indexed | 否 |

## 三、连接器词展示数（破零判定，顺手检查）

GSC 效果报告，Search type: Web，**3 个月**窗口（覆盖 28 天基线期），数据更新时间约为检查前 2 小时。GSC 经 URL 参数仅应用了单个 query 过滤，故三个过滤器分别实测：

| 查询过滤 | Total clicks | Total impressions |
|---|---|---|
| +ccs* | 0 | 0 |
| +connector* | 0 | 0 |
| +nacs* | 0 | 0 |

**判定：未破零。** 文章已收录 3 天但连接器词簇仍无任何展示，属收录后正常积累期；按基线文件既定里程碑继续观察（任一连接器簇词首次展示即破零；2 周内位次 ≤50；4 周内进 p20-40；10-29 前后重拉基线对比）。

## 四、证据文件（gsc-screenshots/）

- `verify-1026-url8-connector.jpeg` —— URL8 已收录
- `verify-1026-url1-apartment-roi.jpeg` —— URL1 已收录
- `verify-1026-debug-current.jpeg` —— URL2 已收录（调试截图，结果页完整可见）
- `verify-1026-url3-used-equipment.jpeg` —— URL3 已收录
- `verify-1026-url4-hotels-parking.jpeg` —— URL4 已收录
- `verify-1026-url5-bess-valuation.jpeg` —— URL5 已收录
- `verify-1026-url6-operating-cost.jpeg` —— URL6 已收录
- `verify-1026-url7-nevi-grants.jpeg` —— URL7 已收录
- `verify-1026-connector-perf.jpeg` / `-connector.jpeg` / `-nacs.jpeg` —— 三个查询过滤 0 展示留证

## 五、过程备注

- 提交手法（沿用 10-24 实测可用方案）：evaluate 原生 value setter 赋值 + input 事件 → daemon `send_keys` 真实 Enter ×2（第一次展开建议下拉、第二次提交检索）→ 轮询 "Retrieving data from Google Index" 消失 → 读状态 + 截图。
- 检索速度：URL8/1/2/3 约 30 秒内返回；URL4/5/6/7 约 3–4.5 分钟返回（Google 侧仍偏慢但可用，未再出现 "Something went wrong" 报错）。
- 旁证观察：GSC Overview 显示全站 "14 total web search clicks"（10-23 看板口径为 12），另有推荐卡提示 `ev-charging-business-plan` 展示量近期 ↑1,280%。仅作观察记录，非本次任务范围。
- 浏览器中留有「GSC 收录复查」标签组（2 个标签页），用户可随时要求关闭。

## 合规红线确认

- 未改动任何仓库代码、未改动任何 GSC 设置（仅 URL 检查与读取性能数据）。
- 全部状态均来自页面实测 + 截图，无估数。
- 公司事实口径保持「22 国 100+ 客户」，本文未涉及对外内容。
