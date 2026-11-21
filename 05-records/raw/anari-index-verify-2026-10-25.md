# ANARI Charge GSC 收录复查报告（2026-10-25 晚，补 10-24 失败场次）

- 执行窗口：2026-10-25 22:13–22:28（CST，UTC+8），遵守 25 分钟总预算，提前收尾（故障确诊后不再空耗）
- 执行方式：Kimi WebBridge 控制本机浏览器（GSC 已登录，资源 `sc-domain:anaricharge.com`，英文界面）
- 红线自查：未改动 GSC 任何设置；未触碰仓库代码；未点击任何 "Request indexing"（无符合补发条件的新鲜状态）

## 一、结论先行：连续第二晚因基础设施故障无法获得任何新鲜收录状态

**故障签名（两晚完全一致，已截图留证）：**

1. **新建连接失败**：任何对 `search.google.com` 的新页面加载均落入 Chrome 错误页 `ERR_CONNECTION_TIMED_OUT`（"响应时间太长"）——见 `gsc-screenshots/2026-10-25-inspect-chrome-error.png`。本机到 Google 的网络链路（代理/VPN）当前不通。
2. **缓存页上的检索后端挂起**：在幸存的缓存页面上可正常操作 UI（输入、回车均成功），但 "Retrieving data from Google Index" 检索请求挂起超过 4 分钟不返回（昨晚同样症状最终以 Google 报错 "Something went wrong" 收场）。
3. 今晚先后尝试：昨日可用的缓存 URL Inspection 页（检索挂起 4 分钟）→ 刷新该页（落入 ERR_CONNECTION_TIMED_OUT）→ 换用缓存的 Insights 页（输入成功但无法触发检索，合成点击与 CDP 真实鼠标事件均无法唤起 SPA 路由跳转）。

**结论：GSC 新鲜数据今晚对本机不可达，8 个 URL 全部标记「未检查」，不虚构任何状态。**

## 二、对照表

| # | URL | 请求索引时间 | 今次状态（10-25 晚） | 是否补发请求 |
|---|---|---|---|---|
| 1 | `/blog/apartment-condo-ev-charging-roi` | 2026-10-21 19:50 | 未检查——两次提交：首次检索挂起 >4 分钟；后续因页面失效/路由不可达未能再触发 | 否 |
| 2 | `/blog/ev-charging-carbon-credits-lcfs` | 2026-10-21 19:50 | 未检查（网络/检索后端故障） | 否 |
| 3 | `/blog/used-ev-charging-equipment` | 2026-10-21 19:50 | 未检查（同上） | 否 |
| 4 | `/blog/ev-charging-revenue-share-hotels-parking` | 2026-10-21 19:50 | 未检查（同上） | 否 |
| 5 | `/blog/bess-valuation-software` | 2026-10-21 19:50 | 未检查（同上） | 否 |
| 6 | `/blog/ev-charging-station-operating-cost`（对照） | 基线已收录 | 未检查（同上） | 否 |
| 7 | `/blog/nevi-grants-ev-charging-station`（对照） | 基线已收录 | 未检查（同上） | 否 |
| 8 | `/blog/ccs1-vs-ccs2-nacs-connector-guide`（复核） | 2026-10-23 12:30 | 未检查——今日无法复核；最近可信状态为 10-23「URL is on Google / Page is indexed」（见 `index-monitor/connector-index-log.jsonl` 三条 10-23 记录） | 否 |

URL 前缀均为 `https://www.anaricharge.com`。

**补发请求说明**：仅当某 URL 获得「unknown / Indexing requested / Crawled - currently not indexed」的新鲜状态时才补发。本次无任何新鲜状态，补发清单为空。

## 三、过程时间线

| 时间 | 事件 |
|---|---|
| 22:13:08 | 时间锚点确认；WebBridge daemon 正常（会话内仍有昨日标签页） |
| 22:13–22:14 | 附着昨日缓存的 URL Inspection 页；登录态、属性、inspect 输入框均正常 |
| 22:14:27 | URL1 提交成功（setter 赋值 + 真实按键 Enter），检索开始 |
| 22:14–22:18 | 检索挂起 >4 分钟不返回（与 10-24 晚相同签名） |
| 22:18:47 | 取消检索，刷新页面尝试重建会话 → 落入 `ERR_CONNECTION_TIMED_OUT` |
| 22:21–22:25 | 换用缓存的 Insights 页：输入与 Enter 成功但不触发检索；激活标签页后重试仍无效 |
| 22:26–22:27 | 侧边栏「URL inspection」合成点击与 CDP 真实鼠标点击均无法唤起 SPA 路由 |
| 22:27:05 | 故障确诊，留存两张证据截图，停止浏览器动作（页面无弹窗残留，干净状态） |

## 四、证据文件

- `gsc-screenshots/2026-10-25-inspect-chrome-error.png` —— `search.google.com` 新连接 `ERR_CONNECTION_TIMED_OUT`（决定性证据）
- `gsc-screenshots/2026-10-25-insights-alive.png` —— 缓存 Insights 页可渲染但检查功能不可用
- 另见 10-24 报告（`anari-index-verify-2026-10-24.md`）：同签名故障 + Google 官方 "Something went wrong" 报错截图

## 五、三行结论

1. **收录率：0/8 完成新鲜验证（连续第二晚）**——是「未验证」而非「未收录」；10-21 批次 5 篇文章的收录状态已连续悬置 4 天，为当前最大数据缺口。
2. **未收录清单：无**（无新鲜数据支撑任何判定）；**补发请求清单：无**。
3. **连接器新文章（ccs1-vs-ccs2-nacs-connector-guide）：今日复核未能执行；最近可信状态仍为 10-23「已收录」（URL is on Google / Page is indexed），无证据表明状态有变。**

## 六、建议（按优先级）

1. **先修网络**：`ERR_CONNECTION_TIMED_OUT` 指向本机到 Google 的代理/VPN 链路失效。恢复后重跑本复查（操作链已于 10-23 验证可用：缓存页 → 激活标签 → setter 赋值 → daemon 真实按键 Enter → 轮询读状态）。
2. **考虑绕开浏览器**：改用 GSC **URL Inspection API**（`urlInspection.index.inspect`，需 OAuth 凭证）直接查询收录状态，可由脚本定时执行，不再依赖浏览器登录态与页面渲染。
3. **重跑优先级**：URL8 复核 → URL1–5（10-21 批次，悬置最久）→ URL6/7 对照抽查。
4. 浏览器现场说明：诊断过程中刷新了原 URL Inspection 标签页（现为 chrome-error 页，网络恢复后手动刷新即可复原）；昨晚遗留的两个 chrome-error 标签页可一并手动关闭。
