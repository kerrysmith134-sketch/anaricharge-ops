# S2 · SEO + GEO 增长包（seo-geo-growth）

> 来源：`AI营销团队增强报告-v3-136技能.md:288-296` 组合 2（technical audit → content brief → programmatic SEO → GEO optimize → llms.txt → AI SoV）。
> 目标：在 2 周内让「技术地基 + 内容产能 + AI 答案框占位」三线同时推进，而不是单点优化。

## 启动前置

| 项 | 判据 | 卡点 |
|---|---|---|
| 站点镜像 | `06-site/anari-new-site` = origin/main，validate 通过 | site-engineer |
| GSC API | `python3 scripts/gsc_pull.py` 可拉到数据 | G4/G6 |
| 事实库 | `ops/fact-library.json` 可跑 check-facts | G8 |
| 内容队列 | `08-execution/keywords/queue-approved-*.json` 存在（否则先跑 W8/W9） | — |

## 编排（固定顺序）

### Step 1 · 技术审计（W3，0.5 天）

- 技能：`seo-technical-audit`、`core-web-vitals`、`seo-schema`、`performance`、`web-quality-audit`。
- 命令：`cd $SITE && node validate.js && node scripts/check-facts.js`；线上 sitemap diff（W3 §3.3）。
- 产出：`$D/step-1-seo-audit.md`（问题 severity + 修复清单 + owner）。
- 验收：双门禁真实退出码；问题按 Blocker/Major/Minor 分级。

### Step 2 · 内容简报与词图（W8，0.5 天）

- 技能：`seo-content-brief`、`seo-keyword-cluster`、`seo-keyword-niche`、`seo-competitor-gap-analysis`。
- 输入：GSC 页面维度 + 竞品情报零覆盖簇（`W14` 输出）。
- 产出：`$D/step-2-briefs.md`（5 篇简报：主词/意图/大纲/内链/目标位次）+ 更新词图。
- 验收：每篇简报可直接交 W6 写作，无需二次解释。

### Step 3 · 批量/规模化页面（W6 + programmatic，2–3 天）

- 技能：`programmatic-seo`、`content-pipeline`、`copywriting`、`stop-slop`。
- 适用边界：国家系列/功率段/场景页可程序化；**产品规格页不得程序化编造**，只用官网已载配置。
- 走 W6 全文写作 + W17 门禁 + W18 事实门。
- 产出：`$D/step-3-pages.md`（slug/主词/PR 号）+ 站点分支。
- 验收：五件套齐全、双门禁绿、无自我竞争（W8 撞题筛查）。

### Step 4 · GEO 设施与答案框（W4，1 天）

- 技能：`cm-aeo-geo-optimizer`、`cm-llms-txt`、`seo-schema`、`schema-markup-generator`。
- 动作：llms.txt/llms-full 校验；问题式 H2 + 40 字直接答案段；FAQ ≥5；对比表；schema 与可见文案一致。
- 产出：`$D/step-4-geo.md`（轮转页清单 + diff 摘要）。
- 验收：validate 通过（schema 一致性机检）；无竞品点名。

### Step 5 · 索引与收录（W13，持续）

- IndexNow 逐 URL + GSC 请求 ≤5/日 + 周四覆盖复查。
- 证据：`anari-index-coverage-recheck-20261029.md`（一周 +24 收录的打法：内链加固 + IndexNow + 每日内容）。
- 产出：`$D/step-5-index.md`（提交清单 + 收录变化）。
- 验收：新 URL 24h 内提交；Discovered 桶周环比下降或持平。

### Step 6 · AI 可见度测量（W5，双周四）

- 技能：`seo-ai-search-share-of-voice`。
- 产出：`$D/step-6-ai-sov.md`（30 格台账 + 竞品占位 + ≤3 条建议）。
- 验收：覆盖格归因完整；建议已入 W8 队列。

## 套件级验收（2 周）

- [ ] 技术门禁全绿且无新增 Blocker。
- [ ] ≥5 篇内容上线（或 ≥3 篇 + 2 篇存量刷新），全部通过双门禁。
- [ ] 新增收录 ≥5 URL，Discovered 桶不上升。
- [ ] AI 可见度至少完成 1 次完整测量（覆盖 ≥18/30 格）。
- [ ] GEO 建议中 ≥1 条在两周内落地到页面。

## 时间与卡点

| 阶段 | 时长 | 卡点 |
|---|---|---|
| Step 1 | 0.5 天 | G2（修复需 PR） |
| Step 2 | 0.5 天 | G9/G17（credits） |
| Step 3 | 2–3 天 | G2/G9/G13 |
| Step 4 | 1 天 | G2/G13 |
| Step 5 | 持续 | **G3**（GSC 浏览器） |
| Step 6 | 0.5 天 | G5/G6 |

## 失败处理

| 失败 | 处置 |
|---|---|
| validate/事实门失败 | 阻断 Step 3 上线；先修 Step 1 清单 |
| 无 SERP credits | 简报标「未验证省 credits」，只做低风险题 |
| GSC 浏览器不可用 | Step 5 只做 IndexNow，GSC 入次日缓冲 |
| 收录两周无变化 | 转 W20 内链加固（来源页必须已收录）+ 内容差异化评估（Plan B 思路） |
