# ANARI Charge GSC 收录复查报告（2026-10-24 晚补跑）

- 执行窗口：2026-10-24 23:18–23:38（CST，UTC+8），遵守 25 分钟总预算 / 20 分钟硬收尾约定
- 执行方式：Kimi WebBridge 控制本机浏览器（GSC 已登录，资源 `sc-domain:anaricharge.com`，英文界面）
- 红线自查：未改动 GSC 任何设置；未触碰仓库代码；未点击任何 "Request indexing"（无符合补发条件的新鲜状态）

## 一、结论先行：本次复查未能产出任何一条 URL 的 10-24 当日新鲜收录状态

**原因（已截图留证）：Google URL Inspection 的索引检索后端当前无法完成请求。**

- URL1（apartment-condo-ev-charging-roi）于 23:30 前后首次触发检索，"Retrieving data from Google Index" 弹窗 3 分半钟未返回；23:34:34 取消后重试，又等 2 分半钟仍不返回。
- 取消后 GSC 弹出官方错误提示：**"Something went wrong — If the issue persists, try again in a few hours"**（见 `gsc-screenshots/99-final-state.png`）。这是 Google 侧/网络侧的故障声明，不是操作问题。
- 旁证：23:19–23:20 两次新开 GSC 标签页均 30 秒超时并落入 `chrome-error://` 错误页（网络级加载失败）；其中一个标签页渲染进程随后无响应。本机当前访问 Google 后端链路不稳定。

按任务约定，23:38 到达 20 分钟硬收尾线，停止浏览器动作；**其余 7 个 URL 标记「未检查」，不虚构任何状态**。

## 二、对照表

| # | URL | 请求索引时间 | 今次状态（10-24 晚） | 是否补发请求 |
|---|---|---|---|---|
| 1 | `/blog/apartment-condo-ev-charging-roi` | 2026-10-21 19:50 | 未检查——两次检索均卡在 "Retrieving data from Google Index"，未返回结果 | 否 |
| 2 | `/blog/ev-charging-carbon-credits-lcfs` | 2026-10-21 19:50 | 未检查（检索后端不可用 + 时间预算耗尽） | 否 |
| 3 | `/blog/used-ev-charging-equipment` | 2026-10-21 19:50 | 未检查（同上） | 否 |
| 4 | `/blog/ev-charging-revenue-share-hotels-parking` | 2026-10-21 19:50 | 未检查（同上） | 否 |
| 5 | `/blog/bess-valuation-software` | 2026-10-21 19:50 | 未检查（同上） | 否 |
| 6 | `/blog/ev-charging-station-operating-cost`（对照） | 基线已收录 | 未检查（同上） | 否 |
| 7 | `/blog/nevi-grants-ev-charging-station`（对照） | 基线已收录 | 未检查（同上） | 否 |
| 8 | `/blog/ccs1-vs-ccs2-nacs-connector-guide`（重点） | 2026-10-23 12:30 | **未获得 10-24 新鲜结果**；所用标签页残留 10-23 会话的检索结果「URL is on Google / Page is indexed」（截图佐证），仅作历史状态参考 | 否 |

URL 前缀均为 `https://www.anaricharge.com`。

**补发请求说明**：任务规定仅对状态为「unknown / Indexing requested / Crawled - currently not indexed」的 URL 补发 Request indexing。本次没有任何 URL 获得新鲜状态，故补发清单为空；页面上残留的 URL8「已收录」结果本身也不满足补发条件。

## 三、过程时间线（要点）

| 时间 | 事件 |
|---|---|
| 23:18:39 | 时间锚点确认；WebBridge daemon 健康（v2.0.26，扩展已连接） |
| 23:19–23:20 | navigate 两次 30s 超时；标签页落入 chrome-error 错误页 |
| 23:21–23:22 | 改附着到 10-23 会话遗留的 URL Inspection 标签页；登录态与属性确认正常；定位到 inspect 输入框 |
| 23:25–23:26 | URL1 首次提交：合成 Enter 事件未触发检索（GSC React 受控输入框） |
| 23:28–23:30 | 改用「原生 setter 赋值 + daemon 真实按键 Enter」组合，成功触发检索 |
| 23:30–23:34 | 检索弹窗 3.5 分钟不返回 → 取消重试 |
| 23:34–23:37 | 重试仍不返回（>2.5 分钟）；取消后 GSC 报 "Something went wrong… try again in a few hours" |
| 23:37:56 | 关闭报错弹窗，页面恢复干净状态；浏览器动作停止 |

## 四、证据文件

- `gsc-screenshots/01-apartment-roi.png` —— URL1 检索弹窗卡住，背景为 URL8 的 10-23 残留结果「URL is on Google」
- `gsc-screenshots/00-stuck-check.png` —— 23:32 复核弹窗仍在检索
- `gsc-screenshots/99-final-state.png` —— 取消后 GSC 官方报错 "Something went wrong"，背景仍为 URL8 残留结果

## 五、三行结论

1. **收录率：0/8 完成 10-24 当日新鲜验证**——不是「未收录」，是「未验证」；Google 检索后端故障期间不应据此下任何收录结论。
2. **连接器新文章（ccs1-vs-ccs2-nacs-connector-guide）：10-23 残留结果显示已收录（URL is on Google / Page is indexed），与 10-23 三次复查一致；今日复检未能执行。**
3. **未收录清单：无（无新鲜数据支撑判定）；补发请求清单：无。**

## 六、建议（供下次执行参考）

1. 等 Google 侧恢复后重跑（GSC 自行提示 "try again in a few hours"）；若本机网络持续出现 chrome-error，先切换稳定代理/网络。
2. 已验证可用的提交手法：evaluate 原生 setter 赋值 → daemon `send_keys` 真实 Enter → 轮询 "Retrieving data" 消失后读状态 + 截图；合成 KeyboardEvent 对 GSC 受控输入框无效。
3. 重跑优先级：URL8（重点）→ URL1–5（10-21 批次）→ URL6/7 对照抽查。
4. 本次导航失败遗留的两个 chrome-error 标签页仍在浏览器中，可手动关闭；未动用户既有标签页。
