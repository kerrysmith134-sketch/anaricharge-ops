# 套件盘点（suites-inventory）

> 建立 2026-11-07｜对象：`04-suites/` 6 个套件
> 来源基准：`AI营销团队增强报告-v3-136技能.md:276-316`（四黄金组合）+ 本工作区补 2 个产线套件

---

## 一、套件总表

| 编号 | 套件 | 文件 | 来源 | 启动前置 | 串联工作流 | 总时长 | 状态 |
|---|---|---|---|---|---|---|---|
| S1 | 询盘增长启动包 | `S1-inquiry-growth-launch.md` | AI 报告组合 1（`:278-286`） | P0 手动配置 + 镜像 + 转化链路 | W8 → W14 → W6/W20 → W11 → W10 → W12 | 3–5 天启动，2 周见线索 | 可启动（外联受 G1 限制） |
| S2 | SEO + GEO 增长包 | `S2-seo-geo-growth.md` | AI 报告组合 2（`:288-296`） | 镜像 + GSC API + 队列 | W3 → W8 → W6 → W4 → W13 → W5 | 2 周 | 可启动 |
| S3 | 付费媒体诊断包 | `S3-paid-media-diagnostic.md` | AI 报告组合 3（`:298-306`） | **预算决策变更** + 广告账户 + 转化追踪 | 6 个付费审计技能（不接站点工作流） | 半天 | **暂停**（$500 全有机，R3） |
| S4 | 增长实验引擎 | `S4-growth-experiment-engine.md` | AI 报告组合 4（`:308-316`） | GA4 归因后台配置 + 基线流量 | W19 → W20 → W12 → W4 → W16 | 4–6 周/实验 | 条件启动（G4 未完成则不可启动） |
| S5 | 内容周产线包 | `S5-content-weekly-pipeline.md` | 本工作区补充 | W9 队列已批准 + 镜像同步 | W8→W9→W6×5→W7→W17→W18→W13→W21 | 1 周 | 可启动 |
| S6 | 月度复盘验收包 | `S6-monthly-review-pack.md` | 本工作区补充 | 本月周报 ≥3 份 + 验收基线 | W19 → W2 → W16 → 决策会 | 1 天 | 可启动（月度） |

**合计：6 个套件（任务书要求 ≥4，其中 4 个来自黄金组合、2 个为产线级补充）。**

---

## 二、套件 × 工作流矩阵

| 工作流 | S1 | S2 | S3 | S4 | S5 | S6 |
|---|---|---|---|---|---|---|
| W1 日终简报 | ○ | ○ | — | ○ | ● 日更 | ○ |
| W2 周编排 | ● | ● | — | ○ | ● | ● |
| W3 技术 SEO | — | ● | — | — | ○ | ○ |
| W4 GEO | — | ● | — | ● | ○ | — |
| W5 AI 可见度 | — | ● | — | — | — | ○ |
| W6 内容生产 | ● | ● | — | ● | ● 核心 | — |
| W7 内容验收 | — | ○ | — | ○ | ● | — |
| W8 关键词策略 | ● | ● | — | — | ● | — |
| W9 策略复核 | ○ | ○ | — | — | ● | — |
| W10 外链 | ● | ○ | — | — | ○ | — |
| W11 社区 | ● | — | — | — | ○ | — |
| W12 询盘监控 | ● | — | — | ● | ○ | ● |
| W13 索引 | — | ● | — | — | ● | — |
| W14 竞品情报 | ● | ○ | — | — | ○ | ○ |
| W15 招投标 | — | — | — | — | — | — |
| W16 月度复盘 | — | — | — | ● | — | ● 核心 |
| W17 PR 门禁 | ● | ● | — | ● | ● | — |
| W18 事实门 | ● | ● | — | ○ | ● | — |
| W19 看板值守 | ○ | ○ | — | ● | ○ | ● |
| W20 存量刷新 | ● | ○ | — | ● | ○ | — |
| W21 发布后验收 | ○ | ○ | — | ● | ● | — |

● = 核心步骤；○ = 可选/交接；— = 不使用。（W15 招投标独立成线，暂不属于四个黄金组合，单列）

---

## 三、套件与技能库的映射

| 套件 | 需要的技能（源库原名） | 迁移后以 `02-skills/_MERGE-MAP.md` 为准 |
|---|---|---|
| S1 | cm-icp-research、customer-research、sa-channel-discovery、sa-community-discovery、seo-competitor-gap-analysis、cm-landing-page-optimizer、cm-cro-auditor、lead-magnets、es-outbound-engine、es-sales-pipeline、cold-email、prospecting、seo-content-brief、copywriting、stop-slop | 活跃技能（R1/R3/R4/CRO 组） |
| S2 | seo-technical-audit、core-web-vitals、seo-schema、llms-txt、seo-content-brief、programmatic-seo、cm-aeo-geo-optimizer、cm-llms-txt、seo-ai-search-share-of-voice、seo-google、seo-sitemap、content-pipeline | 活跃技能（R2/R3） |
| S3 | cm-google-ads、cm-facebook-ads、cm-cross-platform-audit、cm-competitor-ads-analyst、cm-wasted-spend-finder、sa-ad-campaign-analyzer | **归档技能**（v2 花名册：付费媒体类 9 个归档，`营销团队v2-花名册与技能整合.md:55`） |
| S4 | es-growth-engine、ab-testing、analytics、es-conversion-ops、cm-cro-auditor、es-revenue-intelligence | 活跃（增长/数据组） |
| S5 | 同 W6/W8/W9/W17/W18/W21 | 活跃 |
| S6 | analytics、cm-google-analytics、cm-looker-studio、marketing-plan | 活跃 |

---

## 四、套件启动检查单（通用）

每次启动任意套件前逐项确认（任一失败 → 降级或暂停）：

- [ ] 写路径在 `/Users/kerrychu/anari-charge-website/` 内（工作区外只读）。
- [ ] 站点镜像已同步 origin/main，且与线上 sitemap（119 URL）差异已登记。
- [ ] 数据口径为页面维度/无维度总量；GSC API 可用或已注明回退。
- [ ] 本次运行涉及的人工卡点（G1–G17）已列出，用户可执行项已写进待办。
- [ ] 若为 S3：预算决策未变更 → **不启动**。
- [ ] 若为 S4：G4（GTM/GA4 后台配置）未完成 → 不启动。

---

## 五、套件欠账（未覆盖的组合）

| # | 缺口 | 说明 | 建议 |
|---|---|---|---|
| 1 | 招投标获客包 | W15 有 SOP，但无套件把它与资质文件/案例库/投标撰写串起来 | 建议 S7「招投标响应包」：W15 → 资质核对 → 案例匹配 → 投标文件骨架 → 用户审核 |
| 2 | 多语言扩页包 | RU/ES 扩页是迭代④主题（`anari-new-site/plan.md:843-848`），但无独立编排 | 建议并入 S2 Step 3 的 programmatic 分支，或新增 S8 |
| 3 | 危机/回滚包 | CF 事故、Gatekeeper 误合并、询盘链路断裂的应急恢复 | 建议 S9「事故响应包」：检测（W19/W12）→ 回滚（ops/worker-deploy.md §11）→ 复盘（W16） |
| 4 | 用户决策会包 | 每次验收/预算/口径拍板的会议材料与决策记录 | 已并入 S6 Step 6；独立化优先级低 |
| 5 | 「单轮一项」任务包 | 2026-10-26 规则：每轮只推进队列第一个未完成条目 | 已写入 AGENTS.md R5；套件层不再重复 |
