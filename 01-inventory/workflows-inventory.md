# 工作流盘点与欠账清单（workflows-inventory）

> 建立 2026-11-07｜盘点对象：`/Users/kerrychu/Documents/kimi/workspace/`（只读源）全部工作流类文档
> 交付：21 个可执行 SOP（`03-workflows/W1..W21`）+ `_SCHEDULE.json`（24 定时档位 + 4 事件类）+ 17 类人工卡点

---

## 一、盘点结果总表

| 编号 | 工作流 | SOP 文件 | 频率 | 负责人 | 来源证据（文件:行号） | 建模状态 |
|---|---|---|---|---|---|---|
| W1 | 日终简报 | `W1-daily-brief.md` | 每日 22:30 | E3 | `anari-daily-ops-plan.md:113`；`anari-daily-summary-2026-10-31.md:1-62` | ✅ 完整 |
| W2 | 周运营编排 | `W2-weekly-orchestration.md` | 周一 09:17 | R1 | `anari-daily-ops-plan.md:52,117-129`；`anari-weekly-ops-1019.md` | ✅ 完整 |
| W3 | 技术 SEO 巡检 | `W3-tech-seo-audit.md` | 周一（时刻待确认） | R2 | `anari-daily-ops-plan.md:53`；`营销团队v2-花名册与技能整合.md:13` | ✅ 完整（cron 标 `time_confirmed:false`） |
| W4 | GEO 优化专项 | `W4-geo-optimization.md` | 周四 10:17 / 每月 8 日 | E8 | `anari-daily-ops-plan.md:54,122` | ✅ 完整 |
| W5 | AI 可见度监测 | `W5-ai-visibility.md` | 双周四 15:23 | E7 | `anari-daily-ops-plan.md:123`；`anari-ai-visibility-2026-10-29.md:1-56` | ✅ 完整 |
| W6 | 内容生产线 | `W6-content-production.md` | 周二–六 09:23 | R3 | `anari-daily-ops-plan.md:49,63-101,139-156` | ✅ 完整 |
| W7 | 内容验收 | `W7-content-acceptance.md` | 周二–六 10:43 | E1 | `anari-daily-summary-2026-10-31.md:34`；`anari-weekly-ops-1019.md:63` | ✅ 完整 |
| W8 | 关键词策略/词图 | `W8-keyword-strategy.md` | 周日 20:17 | E5 | `anari-daily-ops-plan.md:110,124` | ✅ 完整 |
| W9 | 策略产出复核 | `W9-strategy-review.md` | 周日 20:47 | E4 | `anari-daily-ops-plan.md:125,129` | ✅ 完整 |
| W10 | 外链与数字公关 | `W10-backlinks-pr.md` | 周二/周五 10:19 | R4/E10 | `anari-daily-ops-plan.md:51`；`backlinks-log.md:1-40` | ✅ 完整（发送人工） |
| W11 | 社区引流 | `W11-community.md` | 每日 15:41 | R5 | `anari-daily-ops-plan.md:50`；`quora-log.md`；`anari-reddit-warmup.md` | ✅ 完整 |
| W12 | 询盘监控与对账 | `W12-inquiry-monitor.md` | 每日 22:17 | R6 | `anari-daily-summary-2026-10-31.md:37`；`ops/attribution-model.md:174-210` | ✅ 完整 |
| W13 | 索引提交与验证 | `W13-indexing.md` | 新文 24h + 周四 10:41 + 周五 12:47 | R2 | `anari-indexing-sop.md:1-85`；`anari-index-coverage-recheck-20261029.md` | ✅ 完整 |
| W14 | 竞品情报 | `W14-competitor-intel.md` | 周三 11:17 | E6 | `anari-daily-ops-plan.md:121`；`anari-competitor-intel-2026-10-22.md` | ✅ 完整 |
| W15 | 招投标扫描 | `W15-tender-scan.md` | 周一 09:13 | E9 | `anari-b2b-channels.md:66`；`anari-tender-scan-20261026.md:1-103` | ✅ 完整 |
| W16 | 月度复盘与验收 | `W16-monthly-retro.md` | 每月 1 日（待确认） | R1+R6 | `anari-acceptance-baseline-2026-10-20.md`；`ops/retro-2026-09.md` | ✅ 完整（cron 标 `time_confirmed:false`） |
| W17 | PR 门禁与合并 | `W17-pr-gatekeeper.md` | PR 事件 | Actions+负责人 | `.github/workflows/pr-gatekeeper.yml:1-142` | ✅ 完整 |
| W18 | 事实库门禁 | `W18-fact-gate.md` | 事实改动/PR CI | R2 | `scripts/check-facts.js:1-40`；`ops/fact-library.json`；`pr-gatekeeper.yml:100-101` | ✅ 完整 |
| W19 | 运营值守与看板 | `W19-ops-watch.md` | 每日 08:47/08:53/13:30 | R6+E3 | `anari-daily-ops-plan.md:48,113`；`anari-daily-summary-2026-10-31.md:35` | ✅ 完整（隐性档位，本次建模） |
| W20 | 存量刷新与内链 | `W20-content-refresh.md` | 每周 ≥1 次（数据驱动） | R3+R2 | `anari-daily-ops-plan.md:80`；`anari-interlink-plan-20261101.md:1-80` | ✅ 完整（隐性流程，本次建模） |
| W21 | 发布后验收 | `W21-postdeploy-verify.md` | 周二 14:17 | E2 | `anari-postdeploy-2026-10-27.md:1-58` | ✅ 完整（Lead 指定补建模） |

**统计**：完整 21 / 部分 0 / 仅列名 0。人工卡点 17 类（G1–G17），在 `_SCHEDULE.json.manual_gate_registry` 统一定义，SOP 内引用共 60+ 处。

---

## 二、按来源文档的覆盖情况

| 源文档 | 抽出的工作流 | 说明 |
|---|---|---|
| `anari-daily-ops-plan.md`（11-01 05:39 版） | W1/W2/W3/W4/W6/W7/W8/W9/W10/W11/W14/W16/W19 | 每日节奏、周循环、内容队列、配额、额度 |
| `anari-weekly-ops-0922/1015/1019.md` | W2/W6/W7/W10/W11/W19 | 周报结构、角色产出、待办清单 |
| `anari-weekly-gsc-2026-10-17.md` | W2/W19 | GSC 周报格式 |
| `anari-new-site/plan.md`（117KB，主源） | W3/W4/W6/W12/W16/W17/W18/W21 | 门禁演进、CF 事故、GSC 驱动刷新、PR #38/#39、白名单扩容 |
| `anaricharge-website/plan.md`（94KB，旧源） | 补充核对 10-26 前事件 | 已并入 W17/W21 来源 |
| `营销团队v2-花名册与技能整合.md` | 全部（角色与技能映射） | R1–R6、79 技能处置、4 项人工卡点 |
| `营销团队指挥中心.md` | 技能清单（参考） | 早期 47 技能版，已被 v2 取代 |
| `AI营销团队增强报告-v3-136技能.md` | 04-suites S1–S4 | 黄金组合四套 |
| `CMO审计报告-79技能完整矩阵.md` | W3/W8/W12/W16 | 缺口与下一步（数据层/询盘捕获/GEO/规模化） |
| `手动配置清单.md` | S1/S2 前置、G4/G10/G17 | P0/P1/P2 依赖 |
| `anari-indexing-sop.md` | W13/W7 | IndexNow + GSC Shadow DOM 实操 |
| `anari-quantum-setup-checklist.md` | W15/G12 | 供应商门户注册 |
| `anari-mailchimp-setup-guide.md` | W12（历史通道） | Mailchimp→Brevo 迁移前记录 |
| `anari-b2b-channels.md` | W15 | T1/T2 渠道 + 世行 API |
| `anari-reddit-warmup.md` | W11/G15 | 养号纪律 |
| `anari-backlinks-week-*.md` / `backlinks-log.md` | W10 | 跟进状态机与模板 |
| `anari-tender-scan-20261026.md` | W15 | 来源核验 + 四档分级 |
| `anari-ai-visibility-2026-10-22/29.md` | W5 | 30 格测量方法 |
| `anari-daily-summary-2026-10-22..31.md` | W1/W7/W12/W19 | 日终结构 + 档位健康 |
| `anari-index-coverage-recheck-20261022/29.md`、`anari-index-verify-api-*.md` | W13 | 四桶复查 + API 通道 |
| `anari-interlink-plan-20261101.md` | W20 | 内链加固清单 |
| `anari-postdeploy-2026-10-27.md` | W21 | 六步发布后验收实例 |
| `ops/audit-checklist-20261022.md`、`ops/system-capabilities.json`、`ops/fact-library.json`、`ops/gtm-event-setup.md`、`ops/worker-deploy.md`、`ops/attribution-model.md` | W12/W18/W16 | 门禁/事实库/Worker/归因权威定义 |

---

## 三、发现但未建模的流程（欠账清单）

> 这些流程在文档里真实存在（有档位/产出/命令），但本次未单独写成 W 系列。**不是遗漏，是明确决定**：其中一部分应并入已有工作流作为子步骤，一部分需要用户决策后才能建模。

| # | 流程 | 证据 | 为什么未单独建模 | 建议归属 / 下一步 |
|---|---|---|---|---|
| 1 | 站点迭代 cron（每周 ≥3 项多维度迭代：多语言/性能/CRO/GEO/工具） | `anari-new-site/plan.md:488,708,811`；`plan.md:604-614`（性能季度） | 属「工程迭代」而非运营档位；频率与内容每周变，无法固定 SOP 步骤 | 建议建模为 **W22 网站迭代**（输入=审计清单 🟡/⬜ + GSC 机会；输出=PR；走 W17/W18/W21）。需 lead 决定是否纳入 |
| 2 | LinkedIn 发帖（周一个人号/公司号，素材外包） | `anari-ops-instructions-0917.md:41-56`；`营销团队v2-花名册与技能整合.md:56` | 用户硬卡点（账号由专人操作），agent 只产素材 | 并入 W11 作为「社媒素材」子步骤（当前 W11 只写 Quora/Reddit） |
| 3 | 播客 / newsletter 外联（Electrek 播客、EV News Daily、能源 Substack） | `anari-weekly-ops-0922.md:70-71`；`backlinks-log.md`（转 newsletter 池） | 与 W10 同类，但目标形态/周期不同 | 并入 W10 的「目标池 B 段」；需要一份 podcast/newsletter 目标清单 |
| 4 | GTM/GA4 后台配置（12 事件 + 归因 Phase 1 + 事件分层） | `ops/gtm-event-setup.md:1-120`；`anari-new-site/plan.md:876` | **R6 禁止 agent 操作第三方后台**，只能由用户做 | 保持为「待用户处理」清单；S4 硬前置。建议在 08-execution 建 `user-todos.md` 跟踪 |
| 5 | Brevo 培育序列（5 封 nurture + 退订/抑制名单联动） | `anari-mailchimp-setup-guide.md:1-46`（Mailchimp 版，已迁 Brevo）；`anari-new-site/plan.md:807` | 后台操作属用户；序列内容已固化 | 并入 W12 的「待用户核对」段；退订联动需用户决策（人工导入 vs webhook） |
| 6 | 姊妹站 anariev.com 维护与互链 | `anari-weekly-ops-0922.md:35`；`review-1017/linkcheck-anariev-2026-10-17.md` | 独立代码库/WordPress，不在本站 Gatekeeper 范围 | 建模为 W23 或纳入 W20 的「站外互链」；需确认维护负责人 |
| 7 | GSC 周报 widget / 看板 widget 数据管线 | `anari-new-site/plan.md:219-230,460`；`anari-daily-summary-2026-10-31.md:21-27` | 属可视化层，已由 W19 artifact + W1 阅读替代 | 保留为冗余（widget 可重建自 `08-execution/daily/dashboard-*.json`） |
| 8 | 代理运行健康监控（agent_dispatch_failed / 漏跑） | `anari-daily-summary-2026-10-31.md:29-43` | 依赖调度器内部 API（未文档化） | 并入 W19 巡检第 1 项；若要自动化需调度器提供 run 列表接口 `[需确认]` |
| 9 | 一次性/加档任务管理（如 10-29/30 加档、4a851348 提醒任务） | `anari-daily-summary-2026-10-31.md:43-44,54` | 生命周期短、每次不同 | 用 `_SCHEDULE.json` 之外的 `one-shot` 清单；当前无载体 → 建议 lead 建 `08-execution/scheduler-notes.md` |
| 10 | 内容验收后的 GSC 分日缓冲队列 | `anari-weekly-ops-1019.md:63` | 是 W13 内部状态，不是独立流程 | 已并入 W13；需一个 `index-request-queue.json` 载体（当前 SOP 用文件约定） |
| 11 | URL 参数页 canonical / redirect 治理 | `anari-index-coverage-recheck-20261029.md:44-70`（Page with redirect 10、alternate 4） | 属技术 SEO 子项，按需处理 | 并入 W3 作为季度检查项 |
| 12 | 用户决策会 / 验收口径拍板 | `08-execution/2026-11-07-daily-run.md:122-129`；`00-takeover/TAKEOVER-PLAN.md:98-107` | 人机协同会议，非 agent 流程 | 并入 W16 Step 6「用户决策会」；待办用 `user-todos.md` 跟踪 |
| 13 | 站点安全/资质文件维护（business license、case PDF） | 源目录 `anari-business-license.pdf`、`2026Anari_Cases.pdf` | 静态资产，无周期动作 | 不建模；列入 `site-assets` 盘点 |
| 14 | 邮件通道迁移（Mailchimp → Brevo） | `anari-new-site/plan.md:576` | 一次性迁移已完成 | 不建模；W12 已按 Brevo 口径 |

**合计：21 个已建模 + 14 项欠账（其中 4 项建议并入现有工作流、4 项建议新增 W22/W23、6 项保持人工待办）。**

---

## 四、本次建模的判断依据

1. **「有档位 + 有产出 + 有命令」三要素齐才建 W**：只有概念没有执行路径的（如 widget 管线）不建。
2. **人工卡点是流程的一部分**：17 类 G 卡点全部登记，避免 SOP 写成「看起来能自动跑」。
3. **无法还原的一律标 `[需确认]`**：如 W3/W16 的 cron 时刻、OpenSEO 工具参数 schema、legacy 脚本输出路径。已标注 11 处，未编造任何账号/密钥/命令。
4. **线上为准**：所有验收以线上 119 URL 为真值，本地差异登记不掩盖。
5. **主源更新优先**：以 `anari-new-site/plan.md`（至 10-28）为主，旧 `anaricharge-website/plan.md` 只做 10-26 前补充核对。
