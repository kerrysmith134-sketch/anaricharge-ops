# Anari 连接器选型指南文章 收录加速执行报告

- 执行时间：2026-10-23 12:25–12:40 CST（Asia/Shanghai，UTC+8）
- 执行人：Anari 营销团队收录执行员（自动化任务）
- 公司事实口径：22 国 100+ 客户（本流程未涉及对外内容，未改动）

## 1. 新文章 URL 确认

| 项目 | 结果 |
| --- | --- |
| 新 URL | `https://www.anaricharge.com/blog/ccs1-vs-ccs2-nacs-connector-guide` |
| 来源 | sitemap.xml（`<lastmod>2026-10-23</lastmod>`，当日更新） |
| HTTP 状态 | **200**（curl -o /dev/null -w "%{http_code}" 验证） |
| 结论 | 文章已实际上线 |

## 2. IndexNow 提交

| 项目 | 结果 |
| --- | --- |
| 提交地址 | `https://api.indexnow.org/indexnow?url=<新URL>&key=anari-indexnow-key` |
| HTTP 状态码 | **202**（Accepted，非预期的 200） |
| 说明 | 202 表示 IndexNow 已接受提交请求，属正常受理状态；响应体为空。 |

## 3. GSC URL Inspection — 请求编入索引

| 项目 | 结果 |
| --- | --- |
| 检查前状态 | 「URL is not on Google — URL is unknown to Google」（尚未收录） |
| 操作 | 通过 WebBridge 打开 GSC URL Inspection，输入新 URL，点击 REQUEST INDEXING |
| 技术备注 | 合成 click 未触发（GSC Shadow DOM），改用 CDP `Input.dispatchMouseEvent` 真实鼠标事件点击成功；未改动任何 GSC 设置 |
| 请求结果 | **✓ Indexing requested**（页面显示确认，按钮变为 REQUEST AGAIN） |

截图（均保存在 workspace）：

- 检查/请求前：`gsc-screenshots/gsc-inspect-before-index-2026-10-23.png`
- 合成点击未生效记录：`gsc-screenshots/gsc-request-indexing-clicked-2026-10-23.png`
- 请求成功确认：`gsc-screenshots/gsc-request-indexing-after-click-2026-10-23.png`

## 4. GSC 性能报告 — 连接器相关词展示数

查询筛选：`*ccs*`、`*connector*`、`*nacs*`

| 指标 | 数值 |
| --- | --- |
| Total clicks | 0 |
| Total impressions | **0**（符合预期） |
| Top queries | No data |

截图：`gsc-screenshots/gsc-performance-connector-queries-2026-10-23.png`

## 5. 结论与后续

- 文章已上线（200），IndexNow 已受理（202），GSC 已确认「Indexing requested」。
- 连接器相关词当前展示数为 0，属新文章正常状态。
- 建议 7–14 天后复查该 URL 收录状态及连接器词展示量变化。

## 合规红线确认

- 未改动任何仓库代码。
- 未改动任何 GSC 设置（仅执行 URL 检查与请求编入索引）。
- 公司事实口径保持「22 国 100+ 客户」。
