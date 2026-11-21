# 执行记录文件索引（records-index）

> **用途**：接管后要查「某天发生了什么 / 某个数字哪来的 / 某个决策哪来的」时，先从这张表定位文件，再进 `05-records/raw/` 看原文（快照）或原路径（Kimi 工作区，只读）。
> **路径约定**：
> - `K=` = `/Users/kerrychu/Documents/kimi/workspace/...`（源工作区，**只读**）
> - `raw=` = `05-records/raw/...`（本工作区的原文件名快照副本，共 **57 个根文件 + review-1017/ 子目录 4 个 = 61 份**）
> **行数**为源文件实测（`wc -l`，2026-11-07）。
> **「关键结论」一句话**为抽取式摘要，不是评价。

---

## 1. 计划与主时间线（2 份）

| 文件 | 日期 | 类型 | 行数 | 关键结论一句话 | raw 副本 |
|---|---|---|---|---|---|
| `K/anari-new-site/plan.md` | 更新至 10-28 | 计划+执行日志（**主源**） | 895（117KB） | 71 个 `## 2026-*` 小节；10-26 前与旧副本逐行相同，10-26 后 +9 小节（#16 四页/#23/迭代④/常规节奏 3 项） | `raw/plan-anari-new-site.md` |
| `K/anaricharge-website/plan.md` | 更新至 10-26 | 计划+执行日志（**核对副本**） | 708（94KB） | 只到 10-26 的旧副本，前 668 行与主源完全一致；10-26 之后的 227 行增量只见于主源 | `raw/plan-anaricharge-website-94KB.md` |

---

## 2. 日终简报（8 份，10-22 → 10-31；**11-02 起断档**）

| 文件 | 日期 | 类型 | 行数 | 关键结论一句话 | raw |
|---|---|---|---|---|---|
| `K/anari-daily-summary-2026-10-22.md` | 10-22 | 日终简报 | 47 | 28d 点击 9/展示 625（≈6 倍）；AI 可见度首期 0/11；编排/内容主编各漏跑一次 | ✅ |
| `K/anari-daily-summary-2026-10-23.md` | 10-23 | 日终简报 | 56 | 点击 12/展示 718；验收提前读数 3/5；20:37 数据解读任务漏跑（22:35 补跑） | ✅ |
| `K/anari-daily-summary-2026-10-24.md` | 10-24 | 日终简报 | 61 | 点击 14/展示 834；连接器文已收录未破零；20:07 复查任务 4ms 配置错误失败 | ✅ |
| `K/anari-daily-summary-2026-10-25.md` | 10-25 | 日终简报 | 54 | 点击 14/展示 925；主编漏跑；代理/VPN 失效列第一优先；收录连续两晚 0/8 | ✅ |
| `K/anari-daily-summary-2026-10-26.md` | 10-26 | 日终简报 | 61 | 点击 14/展示 972；**收录复查 8/8 全清**、网络恢复；主编连续第二天漏跑 | ✅ |
| `K/anari-daily-summary-2026-10-27.md` | 10-27 | 日终简报 | 52 | 点击 14/展示 1052；主编恢复；#16 第 1 页上线；API 脚本就绪待实跑 | ✅ |
| `K/anari-daily-summary-2026-10-28.md` | 10-28 | 日终简报 | 60 | 点击 14/展示 1144；GSC 8 URL 复查 API 8/8 PASS；验收员+竞品情报双双漏跑 | ✅ |
| `K/anari-daily-summary-2026-10-31.md` | 10-31 | 日终简报（**最后一份**） | 62 | 点击 22/展示 1494/有曝光 68/71；验收 **2 PASS/3 FAIL**；连接器 API 首秀 indexed | ✅ |

---

## 3. 周报 / 周期运营（4 份）

| 文件 | 日期 | 类型 | 行数 | 关键结论一句话 | raw |
|---|---|---|---|---|---|
| `K/anari-weekly-ops-0922.md` | 09-22 | 周运营报告 W2 | 120 | GSC 90 天 17 词全 0 点击；四条洞察（franchise 簇/印度长尾/investment p17/品牌词被压）；OpenSEO credits=0 | ✅ |
| `K/anari-weekly-ops-1015.md` | 10-15 | 周运营报告 W5 | 117 | 断更 3 周后恢复：展示 413（28d）、点击 2、64 词；AI 引荐首现；GA4 关键事件拖 3 周未标 | ✅ |
| `K/anari-weekly-ops-1019.md` | 10-19 | 周运营报告 W7 | 115 | 展示 469/点击 3（首个博客点击）；CTR 专项 5 页 PR #24 当晚合并；Quora 0/2 被吞 | ✅ |
| `K/anari-weekly-gsc-2026-10-17.md` | 10-17 | GSC 周报 | 48 | 点击 1/展示 116；唯一点击 business-plan 博文（CTR 9.1% p12.4）；inquiry 4 展示 p6.3 | ✅ |

---

## 4. 索引 / 收录（11 份）

| 文件 | 日期 | 类型 | 行数 | 关键结论一句话 | raw |
|---|---|---|---|---|---|
| `K/anari-index-coverage-0923.md` | 10-15（文件名 0923） | 索引覆盖诊断 | 119 | Indexed 27 / Not indexed 62（Discovered 55）；抓取预算瓶颈确诊；sitemap 82 | ✅ |
| `K/anari-index-coverage-recheck-20261022.md` | 10-22 | 索引覆盖周复查 | 76 | Indexed 37（+10）、Discovered 50；两篇被抓拒收（唯一警报）；sitemap 103 | ✅ |
| `K/anari-index-coverage-weekly-summary-20261022.md` | 10-22 | 一周摘要 | 44 | 三层自动化防线（内链/观察/Plan B 停放分支）；Plan B 11-05 若仍拒收自动放行 | ✅ |
| `K/anari-index-coverage-recheck-20261029.md` | 10-29 起，11-01 续跑 | 索引覆盖周复查 | 117 | **Indexed 61（+24）**、Discovered 43、Crawled-not-indexed 清零；两篇前拒文全自愈；sitemap 117 | ✅ |
| `K/anari-index-verify-2026-10-24.md` | 10-24 | 收录复查（浏览器） | 64 | 0/8 新鲜状态：Google 检索后端故障 + 本机链路不稳；未虚构任何状态 | ✅ |
| `K/anari-index-verify-2026-10-25.md` | 10-25 | 收录复查（浏览器） | 64 | 连续第二晚 0/8：`ERR_CONNECTION_TIMED_OUT`（代理失效）；建议改 API | ✅ |
| `K/anari-index-verify-2026-10-26.md` | 10-26 | 收录复查（浏览器） | 64 | **8/8 全部 indexed**，5 篇悬置 5 天状态解除；连接器词仍 0 展示 | ✅ |
| `K/anari-index-verify-api-2026-10-27.md` | 10-27 | 收录复查（API 首跑） | 19 | 8/8 ERROR（OAuth 令牌刷新超时）——「未查到」非「未收录」 | ✅ |
| `K/anari-index-verify-api-2026-10-28.md` | 10-28 | 收录复查（API） | 17 | **8/8 PASS**（Submitted and indexed），与 10-26 浏览器一致；通道迁移收官 | ✅ |
| `K/anari-index-verify-api-2026-11-01.md` | 11-01 | 收录复查（API） | 10 | buy-existing 1/1 PASS；桥查「crawled-not-indexed」确认是过期状态 | ✅ |
| `K/anari-index-submission-2026-10-23.md` | 10-23 | 收录加速执行 | 61 | 连接器文 200 + IndexNow 202 + GSC「Indexing requested」；连接器词 0 展示（预期） | ✅ |

**相关附件**：`K/anari-indexing-sop.md`（85 行，收录加速 SOP v1.0）、`K/anari-gsc-index-backlog.md`（72 行，12 URL 待提交清单）、`K/anari-gsc-url-inspection-api-plan.md`（49 行，浏览器→API 改造方案）、`K/index-monitor/connector-index-log.jsonl`（连接器收录日志）、`K/gsc-screenshots/`（截图证据）。

---

## 5. 连接器 / 多语言 专项（5 份）

| 文件 | 日期 | 类型 | 行数 | 关键结论一句话 | raw |
|---|---|---|---|---|---|
| `K/anari-connector-baseline-2026-10-22.md` | 10-22 | 基线冻结 | 34 | 连接器全簇 28 天 0 展示 0 点击（零覆盖实证） | ✅ |
| `K/anari-connector-baseline-recheck-2026-10-29.md` | 10-29 | 基线对比（一次性） | 64 | 仍未破零（三过滤 3 个月 0/0）；同日发现周复查任务漏跑、补跑 API 超时失败 | ✅ |
| `K/anari-ru-es-indexing-check-1029.md` | 10-29 | RU/ES 收录复查 | 51 | 6 新页 0/6 `unknown to Google`；同批询盘 28d lead=2（含测试嫌疑） | ✅ |
| `K/anari-ru-es-indexing-recheck-1030.md` | 10-30 | RU/ES 定时复查 | 18 | 仍 6/6 NEUTRAL/unknown；官方 API timed out | ✅ |
| `K/anari-interlink-plan-20261101.md` | 11-01 | 内链加固方案 | 63 | 18 条链接/15 已收录来源/13 目标（8 博客+5 产品页）；**方案已就绪未执行** | ✅ |

---

## 6. AI 可见度 / GEO（2 份）

| 文件 | 日期 | 类型 | 行数 | 关键结论一句话 | raw |
|---|---|---|---|---|---|
| `K/anari-ai-visibility-2026-10-22.md` | 10-22 | 可见度台账（首期基线） | 55 | 0/11 实测格被引、竞品也零（答案框空位期）；ChatGPT 零外链、Gemini 9/10 提交被拒 | ✅ |
| `K/anari-ai-visibility-2026-10-29.md` | 10-29 | 可见度台账（第 2 期） | 56 | 宽松 1/18、保守 0/18；竞品在 Gemini 开始具名（ChargePoint/FLO/Wallbox/SWTCH/Blink） | ✅ |

---

## 7. 交接 / 复盘 / 裁决 / 验收（10 份）

| 文件 | 日期 | 类型 | 行数 | 关键结论一句话 | raw |
|---|---|---|---|---|---|
| `K/anari-handoff-2026-10-20.md` | 10-20 | 团队遗留项分派单 | 41 | 六组遗留 + 用户 3 项阻塞；编排任务连续 failed 建议修复或暂停待拍板 | ✅ |
| `K/anari-orchestrator-brief-2026-10-20.md` | 10-20 | 营销编排简报 | 46 | 外链 13 封发出/目录 4 家终态/backlinks 40；GA4 点星阻塞 >3 周为全局瓶颈 | ✅ |
| `K/anari-acceptance-baseline-2026-10-20.md` | 10-20 | **验收基线** | 49 | 五项验收目标 + 10-17 基线值 + 4 URL 已请求索引（截图存证） | ✅ |
| `K/anari-team-sync-20261022.md` | 10-22 | 团队同步邮件 | 45 | 投标策略定调（聚焦充电桩/UNGM=外链）；索引 +10；franchise 互链 issue 待建站团队认领 | ✅ |
| `K/anari-1023-judgment.md` | 10-23 | 晚间数据判断（补跑） | 87 | 连接器「已请求索引待验证」；CTR v2 不重复触发（PR #34 已覆盖）；验收 3/5 | ✅ |
| `K/anari-1024-brief.md` | 10-24 | 晚间复查简报 | 83 | 8 URL 仅 1 个有可核实状态；1–5 号未知连续悬置两日；里程碑短帖不硬写 | ✅ |
| `K/anari-adjudication-input-2026-10-26.md` | 10-26 | 插队裁决输入 | 30 | 追认 china charger 簇（红线三条件）、折入 dynamic power、否决 ev charger repair | ✅ |
| `K/anari-monday-review-1026.md` | 10-26 | 周一复盘议程 | 54 | 竞品情报首轮 + 海湾双页审批（⭐本周核心）+ 行动池 5 条 + 阿曼立项 | ✅ |
| `K/anari-monday-review-pack-1026.md` | 10-26 | 周一复盘包（三线合订） | 62 | 索引线+外链线+竞品线合订；10-24/25/26 三次复查结果全程记录 | ✅ |
| `K/anari-review-weekly-brief-2026-10-26.md` | 10-26 | 复核员周报附件 | 35 | 策略师产出复核通过；口径清扫修 3 处「30+ 国」+派单 1 条 | ✅ |

---

## 8. 内容流水线与执行计划（3 份）

| 文件 | 日期 | 类型 | 行数 | 关键结论一句话 | raw |
|---|---|---|---|---|---|
| `K/anari-daily-ops-plan.md` | 10-15 制定，11-01 05:39 最后更新 | **作战排期+队列**（单文件最长生命期） | 156 | 战略复盘/渠道重排/每日节奏/D1–D10+W8–W9 队列与逐篇锚点；**最后一条记录=W9-D2 + PR #42/#43 闭环** | ✅ |
| `K/anari-weekly-actions.json` | 10-26 生成（W44） | 任务清单（看板读源） | 244 | 22 条动作：done 6 / todo 8 / observing 1 / blocked 1 等；含 AI 可见度新增 2 条（11-09/11-16 到期） | ✅ |
| `K/anari-new-site/anari-postdeploy-2026-10-27.md` | 10-27 生成，11-01 05:35 更新 | 发布后验收报告 | 68 | Week8 D1+D2 上线 109 页；IndexNow 4 URL 200；**GSC 补投 11-01 全部完成 4/4** | ✅ |

**相关**：`K/anari-top3-canary-refresh-1026.md`（外联稿 4 封，等用户发）、`K/anari-ctr-rewrite-v2-franchise-draft.md`（CTR 二轮素材包，未触发）、`K/anari-connector-baseline-*`（见 §5）、`K/w9d2-gas-station-retrofit-outline.md` / `K/w9d3-revenue-models-outline.md`（11-01 大纲）。

---

## 9. 运维 / 复盘 / 机制文档（6 份，均在 `K/anaricharge-website/ops/`）

| 文件 | 日期 | 类型 | 行数 | 关键结论一句话 | raw |
|---|---|---|---|---|---|
| `K/anaricharge-website/ops/audit-checklist-20261022.md` | 10-22（10-26 刷新） | **36 项审计对账** | 80 | ✅/🟡/⬜ 三态；10-26 时 ✅12/🟡15/⬜9，之后 #16、#23 转 ✅；P0 服务端能力全部落地 | ✅ |
| `K/anaricharge-website/ops/retro-2026-09.md` | 09-18 | 四轮整改复盘 | 119 | 6 个自评错误 + 6 条验证纪律（token 改动必须 3 宽渲染等） | ✅ |
| `K/anaricharge-website/ops/growth-plan-2026-09.md` | 09-18 | 增长排期 v1 | 278 | Block 0–6；当时唯一阻塞=GTM 权限（后来 10-15 才解决） | ✅ |
| `K/anaricharge-website/ops/iteration-2026-09-25.md` | 09-25 | 迭代计划（**已标 superseded**） | 96 | 基于旧本地 main 的过期结论，仅历史留档，**不可执行** | ✅ |
| `K/anaricharge-website/ops/attribution-model.md` | 10-22 | 归因模型设计 | 285 | 三级 ID + 双快照 + submission_id 四方对账；Phase 0/1/2 分层与硬前置 | ✅ |
| `K/anaricharge-website/ops/gtm-event-setup.md` | 10-26 更新 | GTM 事件手册 | 109 | 8 事件 + 数据层变量 + 自定义维度 + 归因 Phase 1 增量 + 事件分层模型 | ✅ |

---

## 10. review-1017 巡检包（4 份 md 已快照；另有 2 txt + 2 html 在源目录）

| 文件 | 日期 | 类型 | 行数 | 关键结论一句话 | raw |
|---|---|---|---|---|---|
| `K/review-1017/anaricharge-SEO巡检修复清单-20261017.md` | 10-17 | 修复清单 | 78 | SEO 周巡检的修复项清单 | ✅ |
| `K/review-1017/directory-candidates-2026-10-17.md` | 10-17 | 目录候选 | 71 | 外链目录候选池 | ✅ |
| `K/review-1017/linkcheck-anariev-2026-10-17.md` | 10-17 | 死链检查 | 31 | anariev 姊妹站链接体检 | ✅ |
| `K/review-1017/tools-outreach-2026-10-17.md` | 10-17 | 工具外联 | 127 | 工具型外联机会与邮件角度 | ✅ |
| `K/review-1017/anaricharge-seo-weekly-inspection-2026-10-17.{txt,html}` | 10-17 | 巡检报告全文 | 427 / 318 | 技术 SEO 周巡检完整报告 | 源目录 |
| `K/review-1017/anaricharge-weekly-unified-execution-report-2026-10-17.{txt,html}` | 10-17 | 统一执行周报 | 272 / 303 | 周执行汇总 + 待人工/待开发阻塞点 | 源目录 |

---

## 11. 读取顺序建议（新会话/接管者）

1. **`05-records/current-state.md`** —— 先知道现在是什么状态（含断档与版本漂移）。
2. **`05-records/decisions.md`** —— 再知道哪些规则不能违反（一页速记 8 条）。
3. **`05-records/open-items.md`** —— 然后知道该修什么（P0 六项）。
4. **`05-records/timeline.md`** —— 需要追溯「某天做了什么/为什么」时按日期查。
5. **本文件** —— 要进原文时定位文件与行数。
6. `K/anari-new-site/plan.md`（主源）与 `K/anari-daily-ops-plan.md`（队列现状）—— 最后才读全文，因为最长。

---

## 12. 本工作区已产出的接管档案（非原始记录）

| 文件 | 性质 | 说明 |
|---|---|---|
| `05-records/timeline.md` | 衍生 | 时间线：plan.md 71 小节全覆盖（P01–P71）+ 51 条记录派生条目（R01–R51） |
| `05-records/current-state.md` | 衍生 | 现状：三层数据口径 + 断档专节 + 验收裁定 + 六角色健康度 + 版本对账 |
| `05-records/open-items.md` | 衍生 | 未闭环：P0 6 / P1 17 / P2 14 + 卡人手 14 + 外部阻塞 11 |
| `05-records/decisions.md` | 衍生 | 决策集 53 条：生效 43 / 条件触发 3 / 历史 7（A4+B8+C8+D9+E8+F5+G4+历史 7），含一页速记 8 条 |
| `05-records/raw/` | **快照** | 61 份原始记录副本（原文件名，2026-11-07 快照时点） |
| `08-execution/2026-11-07-daily-run.md` | **接管后新产出** | 接管首班补班简报（官方 API 实读），本索引的现状数据来源之一 |
