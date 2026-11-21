# Anari Charge 两周验收基线（建立于 2026-10-20）

## 验收时间

~2026-11-03 当周（营销团队移交约定的两周后验收）。

## 验收口径（营销团队移交原文）

| 页面 | 验收目标 |
|---|---|
| /blog/ev-charging-business-plan | CTR ≥ 3% |
| /blog/ev-charging-station-franchise-profit | CTR ≥ 3% |
| /blog/ev-charging-station-franchise | CTR ≥ 3% |
| /products/ | 排名进前 15 |
| /inquiry | 展示量上升 |

## 基线数据（来源：2026-10-17 GSC 周报）

| 页面 | 点击 | 展示 | CTR | 平均排名 |
|---|---|---|---|---|
| /blog/ev-charging-business-plan | 1 | 11 | 9.1% | 12.4 |
| /blog/ev-charging-station-franchise-profit | 0 | 26 | 0% | 12.5 |
| /blog/ev-charging-station-franchise | 0 | 12 | 0% | 12.1 |
| /products/ | 0 | 15 | 0% | 21.7 |
| /inquiry | 0 | 4 | 0% | 6.3 |

## 2026-10-20 已执行动作（请求索引）

GSC URL Inspection → 4 个 URL 均已确认 "URL was added to a priority crawl queue"：
1. https://www.anaricharge.com/blog/ev-charging-station-franchise-profit
2. https://www.anaricharge.com/blog/ev-charging-station-franchise
3. https://www.anaricharge.com/blog/ev-charging-business-plan
4. https://www.anaricharge.com/products/

存证截图（workspace）：
- gsc-request-indexed-1-franchise-profit.png
- gsc-request-indexed-2-franchise.png
- gsc-request-indexed-3-business-plan.png
- gsc-request-indexed-4-products.png

## 对照方式

1. 看板 GSC 周报 Widget：对比 weekClicks / weekImpressions / CTR / 排名变化。
2. 口径说明：CTR 按单页展示计算；排名取 GSC 该页平均排名；"展示上升"指 /inquiry 周展示数高于基线 4。
3. 注意 GSC 数据有 2-3 天延迟，验收时以 10-17 之后最近一个完整周的数据为准。

## 待办提醒

- content/business-case-template 分支 PR 待用户创建合并（compare: main...content/business-case-template），合并后补 IndexNow 提交。
