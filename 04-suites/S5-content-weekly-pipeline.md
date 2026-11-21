# S5 · 内容周产线包（content-weekly-pipeline）

> 本工作区补充套件（非 AI 报告原四组合）：把「周日选题 → 周一到周六产出 → 验收 → 索引 → 发布后验收」串成一条每周可复跑的产线。
> 目标：稳定 5 篇/周（周二–周六），每篇都过双门禁、24h 内提交索引、无自我竞争。

## 启动前置

| 项 | 判据 | 卡点 |
|---|---|---|
| 队列已批准 | `08-execution/keywords/queue-approved-<date>.json`（W9 产出） | — |
| 站点镜像同步 | `06-site/anari-new-site` = origin/main（线上 119 URL） | G2?（site-engineer） |
| 当周分支策略 | `seo/week<N>-content` 或按 Gatekeeper 策略新建 | — |
| 事实库 | `node scripts/check-facts.js` 基线 PASS | G8 |

## 编排（一周固定节奏）

### 周日 20:17–21:00 · 选题与复核（W8 → W9）

- 跑 `W8`：拉 GSC、吸收 W14 情报、SERP 验证、重写 10 天队列。
- 跑 `W9`：五道校验 → `queue-approved-<date>.json`；推送 ≤15 行摘要给用户。
- 产出：`$D/step-0-queue.md`（本周 5 篇 slug/主词/内链/目标位次）。

### 周一 09:17 · 周编排（W2，若已在跑可复用其产物）

- 取线上 sitemap 快照做撞题基线；确认本周队列与分支名。
- 产出：`$D/step-1-sitemap.txt`。

### 周二–周六 09:23 · 每日 1 篇（W6）

- 每日：撞车核对 → 五件套写作 → 全链重建 → 双门禁 → 分支累积 → PR。
- 09:53 盯梢：补产/查 PR。
- 每日产出：`$D/step-2-day<N>.md`（slug/主词/commit/PR 状态）。

### 每日 10:43 · 内容验收（W7）

- 三证验收（200 + sitemap + title）+ IndexNow + GSC 请求（≤5/日，交 W13 缓冲）。
- 产出：`$D/step-3-accept-<date>.md`。

### 每日/随合并 · PR 门禁（W17）

- 观察 Gatekeeper：rebase → 重建 → validate → check-facts → 风险分级 → squash。
- 失败当日修，不跨天带病。
- 产出：`$D/step-4-gatekeeper-<date>.md`。

### 每日 · 事实门（W18）

- 任何数字改动后必跑；不一致 0 才允许合并。
- 产出：`$D/step-5-facts-<date>.md`。

### 每日 · 发布后验收（W21）

- commit → 本地门禁 → sitemap diff → 线上 curl → IndexNow → GSC → 偏差与遗留。
- 产出：`$D/step-6-postdeploy-<date>.md`。

### 周六 · 周产线小结

- 本周 5 篇是否全上线？索引提交是否全 200？红线条数？下周队列是否已排？
- 产出：`$D/summary.md`。

## 套件级验收（周末）

- [ ] 本周上线 ≥5 篇（或明确说明缺口原因与补排日）。
- [ ] 每篇双门禁绿 + PR 已合并 + 发布后验收六步有输出。
- [ ] 每篇 IndexNow 状态码记录、GSC 请求 ≤5/日。
- [ ] 0 竞品点名、0「30+ 国」、0 未标源数字。
- [ ] 下周队列已批准（否则下周产线无输入）。

## 时间与卡点

| 阶段 | 时长 | 卡点 |
|---|---|---|
| 周日 | 1.5h | G9/G13/G17 |
| 周一 | 0.5h | G1/G2/G4 |
| 周二–六 每日 | 2–2.5h（写作 90m + 验收/门禁 30m） | G2/G3/G9 |
| 周六小结 | 0.5h | — |

## 失败处理

| 失败 | 处置 |
|---|---|
| 队列未批准 | 用 W8 应急队列（最多 5 篇，标注「应急」），不空档 |
| 当天写不完 | 09:53 档补产；顺延 ≤24h；周产能不足时 W2 调整（不硬凑低质） |
| Gatekeeper 冲突 | 按 W17 ⑥；既有文刷新用 reset+cherry-pick |
| 线上未部署 | W21 判延迟，等 6 分钟重试；CF 事故按 `ops/worker-deploy.md §11` 回滚 |
| 索引配额耗尽 | 剩余 URL 次日续，不重复请求 |
