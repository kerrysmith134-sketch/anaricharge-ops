# 连接器词簇基线对比复查（2026-10-29 晚，一次性观察任务）

- 站点：www.anaricharge.com（GSC 资源 `sc-domain:anaricharge.com`，英文界面）
- 执行时间：2026-10-29 21:13–21:22（Asia/Shanghai，本机时间已锚定）
- 执行方式：Kimi WebBridge 控制本机已登录浏览器（session `connector-watch`），只读性能报告；AutomationControl 核查周复查任务运行记录
- 红线自查：未改仓库代码、未动 GSC 任何设置（未点 VALIDATE FIX / REQUEST INDEXING）；浏览器标签页保持打开

## 一、破零判定：❌ 未破零

三个查询过滤（ccs / connector / nacs）在 3 个月窗口下 **Total clicks 全部 0、Total impressions 全部 0**。无任何连接器簇词的首次展示，破零条件（任一簇词展示 >0）未达成。

- 数据新鲜度：GSC 页面显示「Last update: 4 hours ago」，为检查前约 4 小时的快照，属正常新鲜数据
- 过滤生效确认：三张截图均可见对应过滤 chip（`Query: +ccs*` / `+connector*` / `+nacs*`），3 months 窗口、Search type: Web
- 背景：连接器文章 `/blog/ccs1-vs-ccs2-nacs-connector-guide` 10-23 上线当天被收录，10-26 晚复核仍为「URL is on Google / Page is indexed」（[anari-index-verify-2026-10-26](anari-index-verify-2026-10-26.md)，8/8 全收录）。**收录已 6 天仍零展示**——Google 已存页但尚未在任何连接器簇查询中给出曝光。

## 二、基线 vs 10-26 vs 今日 三栏对比

口径说明：基线为近 28 天导出（含 ccs / nacs / chademo / j1772 / connector / type 2 / mennekes / gb/t 全簇）；10-26 与今日为 GSC 效果报告 3 个月窗口、逐过滤实测（GSC 经 URL 参数仅应用单个 query 过滤，故分三次查）。

| 查询过滤 | 基线 10-22（28 天） | 10-26 晚实测（3 个月） | 今日 10-29 晚实测（3 个月） |
|---|---|---|---|
| +ccs*（点击/展示） | 0 / 0 | 0 / 0 | **0 / 0** |
| +connector*（点击/展示） | 0 / 0 | 0 / 0 | **0 / 0** |
| +nacs*（点击/展示） | 0 / 0 | 0 / 0 | **0 / 0** |
| 簇内其余词（chademo / j1772 / type 2 / mennekes / gb/t） | 0 / 0 | 未单独测（含于三过滤代理口径） | 未单独测（同上） |
| 平均位次 | 无 | 无（0） | 无（0） |

**变化：无。三个时点全部为零，曲线完全平直（截图中 Daily 图表全程贴 0 轴）。**

## 三、周复查任务运行状态核查（⚠️ 发现漏跑）

任务 `automation_c941e76b-d794-4c02-a993-b08b3caddcac`（「GSC 索引覆盖周复查」，cron `41 10 * * 4`，Asia/Shanghai）：

| 核查项 | 结果 |
|---|---|
| 任务状态 | enabled: true，latestRunStatus: succeeded |
| 应跑时间 | 2026-10-29 10:41（周四） |
| listRuns 实际记录 | 截至 21:14 **仅 1 条：2026-10-22 19:06（北京）跑成功的 run_232707f3**；当时无 10-29 运行记录 |
| 今日应产出报告 | `anari-index-coverage-recheck-20261029.md` **不存在**（workspace 最新复查报告仍为 [anari-index-coverage-recheck-20261022](anari-index-coverage-recheck-20261022.md)） |

**结论：周复查任务今天白天漏跑**（任务本身 enabled，但 10:41 档无 fire 记录——可能守护进程/调度器当时未就绪）。本报告无法引用新的收录覆盖结论；与连接器相关的收录背景沿用 10-26 复核（8/8 收录）。

**补跑进展（22:15–23:21 更新）**：用户于 22:15 手动触发补跑（run_4f8acbae），但运行 **失败**——模型 API 连接超时（APITimeoutError / APIConnectionError，10 次指数退避重试全部超时，provider.connection_error），agent 未能开始任何实际工作，未产出报告。我在 22:17 的重复触发被调度器正确跳过（already_running，skipped run_ef940ca9）。23:20 又两次触发（run_26e81656、run_eef87df6）均**秒败**（<100ms），错误相同：会话 conv-977c57dea7add52192d9c544「was updated by another client; reload it before continuing」——即首跑失败遗留的会话处于冲突状态，需客户端 reload 后才能再跑。我 23:20–23:21 的两次触发也均被跳过（already_running）。结论：10-29 档报告暂缺，是否再补跑待客户端刷新后决定；下一次自动档为 11-05 周四 10:41（Plan B 判断档）。

## 四、截图清单（gsc-screenshots/）

| 文件 | 内容 |
|---|---|
| `connector-recheck-1029-ccs.jpeg` | Query: +ccs*，Total clicks 0 / Total impressions 0，3 个月窗口 |
| `connector-recheck-1029-connector.jpeg` | Query: +connector*，0 / 0 |
| `connector-recheck-1029-nacs.jpeg` | Query: +nacs*，0 / 0 |

三张截图均经回读核验，过滤 chip、总数卡片与 Last update 时间清晰可见。

## 五、下一步建议（未破零 → 继续观察）

1. **继续观察，不动作。** 文章收录仅 6 天，新站新页从收录到获得展示常见需 1–3 周；里程碑不变：任一簇词首次展示即破零 → 破零后 2 周内（约 11-06 前）位次 ≤50、4 周内（约 11-20 前）进 p20-40。目前位次无从谈起，里程碑计时以破零日为起点。
2. **下次观察窗口：11-05（周四）**，与周复查任务同档合并观察即可，无需单独加跑；若 11-05 仍全零，再考虑加做 chademo / j1772 单过滤验证与页面内链加固评估。
3. **周复查补跑已尝试但失败**：22:15 手动触发，因模型 API 连接超时失败（详见第三节），未产出 10-29 档报告；待链路恢复后可再补跑，否则并入 11-05 档（11-05 同时是 Plan B 判断档，更重要）。
4. **内容侧可选加速项**（供主编参考，不在本任务执行范围）：从已收录的 franchise / fleet-depot 簇文章正文向连接器指南补 1–2 条上下文内链，传递主题相关性信号。

## 一句话总结

**连接器词簇未破零：今日（10-29 晚）+ccs* / +connector* / +nacs* 三过滤展示均 0、点击均 0，与 10-22 基线和 10-26 实测完全一致；周复查任务 automation_c941e76b 今日白天漏跑、晚间手动补跑又因模型 API 超时失败，10-29 档收录覆盖报告暂缺。**
