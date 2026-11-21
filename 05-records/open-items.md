# ANARI Charge 未闭环事项清单（open-items）

> **口径**：截至 **2026-11-07** 仍未闭环的事项，全部来自执行记录（`来源` 列给 `文件:行号`）。
> **优先级定义**：`P0` = 不解决则运营/验收/数据不可信，接管后第一周必须动；`P1` = 影响增长效率，两周内应排；`P2` = 结构性/长期，可排后。
> **统计**：P0 **6** 项 · P1 **17** 项 · P2 **14** 项 · 合计 **37** 项。另单列「卡在人手上」14 项、「外部阻塞」11 项（与前三档有交叉，交叉处在条目里注明）。
> **断档期未闭环事项集中在 §1，不进 P1/P2 稀释。**

---

## 0. 断档期补班清单（11-02 → 11-07，6 天）

| # | 缺的档期 | 原应产出 | 现状 | 补法 |
|---|---|---|---|---|
| 0.1 | 11-02 周一 | R1 周编排 + R6 漏斗周报（含 11-02 桥回退预授权） | 无记录 | 并入 11-09 周一档一次补齐；桥回退改造按 10-28 预授权执行 |
| 0.2 | 11-03 周二 | **验收五项正式读数**（目标日） | 逾期 4 天，已由接管首班 11-07 补裁定 | 已补：1 PASS / 1 分歧 / 3 FAIL（`08-execution/2026-11-07-daily-run.md:51-68`）；**但口径需用户拍板后归档** |
| 0.3 | 11-04 周三 | 内容主编 1 篇 + 竞品情报周报 | 无记录 | 竞品轮换（teison/盛弘/星星充电）顺延 |
| 0.4 | 11-05 周四 | 索引覆盖周复查 + **Plan B 判定档** + GEO 优化师 | 无记录 | Plan B 判定**事实上已无需放行**（两篇 10-29 已确认自愈），标注「已自愈」即可 |
| 0.5 | 11-06 周五 | 内容主编 + 外链 + 社区 | 无记录 | 外链 16 封仍卡人手（见 §3） |
| 0.6 | 11-02 后运营归属 | 谁在跑这条线（线上多了 5 篇） | **未知** | **问用户**（11-07 接管首班列为最高优先用户项，`08-execution/2026-11-07-daily-run.md:124`） |

---

## 1. P0（6 项）

### P0-1 运营流水线断档 6 日，未恢复排期
- **事实**：最后实质产出 2026-11-01 05:39；11-02 → 11-07 无日终简报、无周复盘、无验收读数、无内容档记录。详见 `current-state.md` §0。
- **影响**：所有日更指标（内容节奏/索引请求/外链跟进）归零 6 天；断档期数据无法回溯。
- **建议动作**：①按 11-07 接管首班的 A4 建议，**先不做新内容**，用 11-09 周一档把 W-1 数据 + 验收裁定跑通，再恢复日更；②把「每日 22:30 值班长汇报」和「22:17 表单监控」作为断档哨兵（这两个岗历史上几乎没掉过班）。
- **来源**：`anari-daily-ops-plan.md` mtime 11-01 05:39；`08-execution/2026-11-07-daily-run.md:6,111-114`

### P0-2 验收五项（11-03 到期）3 项 FAIL，且 business-plan 出现「排名↑但 CTR↓」的结构性问题
- **事实**：11-07 正式裁定 1 PASS（/products/，脆弱）/ 1 口径分歧（/inquiry）/ 3 FAIL（business-plan 0.70%、profit 0%、franchise 支柱 0%）。business-plan 位次 p15.7→p7.9，展示 63→142，点击没涨。
- **影响**：验收无法结项。**注意：「低意图长尾涌入」这个解释已被数据否证**——该页 271 展示中仅 68（25%）可被查询词维度归因，且这 68 展示的可见查询 100% 是商业意图、0 点击；其余 75% 被 GSC 匿名化不可观测。所以不能归因于意图稀释，只能确认「在 p10–32 的商业意图词上拿不到点击」（见 `08-execution/TECH-FINDINGS-20261107.md` F4）。
- **建议动作**：优先修「位次已进前 10 却 0 点击」的 3 个页面——nevi-grants（p8.7 / 167 展示）、revenue-share-hotels-parking（p5.6 / 82 展示）、首页（p4.8 / 111 展示 / 1 点击）；这些位置足够好，0 点击只能是 SERP 呈现问题，可诊断可验证。business-plan 因 75% 展示不可归因，排在后面。改后 14 天验收。**需用户授权改动**。同时拍板第 4/5 项口径（≥100 展示 / 28 天窗口 / 三语是否合计）。
- **来源**：`08-execution/2026-11-07-daily-run.md:51-68,98-102,127`；基线 `anari-acceptance-baseline-2026-10-20.md:9-15`
- **2026-11-08 进展（R2 CTR 轮）**：nevi-grants 与 revenue-share 两页 title 已改写并上线（main `e5163ec`；`title` 单变量，观察窗 11-15~11-22）；**首页仍未做**（下一候选，旧分支 `seo/ctr-title-meta-20261107` 有草稿）。另 5 个 0 点击页诊断结论是排名/意图瓶颈、不是 title 问题（勿再排 title 刷新）。交接见 `08-execution/HANDOFF-TO-R1.md`，细节见 `08-execution/content/content-refresh-2026-11-08.md`。

### P0-3 真实询盘数不可见（Brevo 核对 + GTM/GA4 后台配置）
- **事实**：GA4 28d `form_submit` 13 / `generate_lead` 9（含测试），最后一次 **10-26**，此后 12 天零提交；Brevo 口径真实询盘「待核」；10-31 记月累计 2，但 11-01 复核指「2 个 lead 含测试嫌疑、Brevo 无对应新增真实联系人」。
- **影响**：30 询盘/月目标无法度量 → 所有渠道产出无法归因 → 团队无法判断谁在有效工作。
- **建议动作**：①用户 Brevo Contacts 一眼核对 10-26 后是否有真实新增（1 分钟）；②GTM/GA4 后台两批配置一次做完（Phase 1 归因 6 参数 ~15 分钟 + 事件分层 3 事件 ~10 分钟 + Consent Mode 体检）；③做一次低成本真浏览器三语冒烟，确认 12 天零提交是「流量太小」而非「链路又断」。
- **来源**：`anari-daily-summary-2026-10-31.md:23,10`；`anari-ru-es-indexing-check-1029.md:34-38`；`08-execution/2026-11-07-daily-run.md:40-47,124`；待办三方：plan.md:699-702 + anari-new-site/plan.md:882-888 + audit-checklist #15/#20

### P0-4 本地仓库落后线上（119 vs 114/106），直接提交会覆盖线上 5 篇文章
- **事实**：线上 sitemap **119**（11-07 实测 119/119 200）；Kimi 侧 `anari-new-site` HEAD `72a0d6c`（10-28，sitemap 114）；接管工作区克隆 HEAD `125dc18`（10-26，sitemap 106）。线上多 5 篇：fleet-electrification-business-plan / station-maintenance / station-insurance / feasibility-checklist / gas-station-retrofit。
- **影响**：下一次本地提交会把 blog 列表/sitemap/llms-full 覆盖回旧态，等于删掉 5 篇的入口。
- **建议动作**：`git fetch origin && git checkout main && git reset --hard origin/main`，核对 sitemap=119 再动工。**✅ 已完成**：接管工作区镜像 `06-site/anari-new-site/` 已同步到 origin/main `0f7d8a1`（2026-11-01），sitemap = **119 URL**，`git status` 干净，双门禁在同步后重跑通过（validate 120 页 / check-facts 60 一致）。
- **来源**：`08-execution/2026-11-07-daily-run.md:80-92,104-106`；`current-state.md` §8

### P0-5 断档期间运营归属未知（是否存在第二条运营线）
- **事实（已核实，结论已修正）**：线上 `sitemap.xml` 的 `<lastmod>` 最大值 = **2026-11-01**（build-sitemap.js 取页面 JSON-LD dateModified / Last verified 徽章），**说明 11-02 之后站点内容没有任何修改**。线上 119 > 本地 114/106 的差额是本地克隆停在 10-28 未 fetch origin/main，**不是断档期的新增**。那 5 篇在 `anari-daily-ops-plan.md:143-155` 有 commit 级记录，10-28～11-01 期间上线。→ **不存在需要收编的「第二条运营线」**；仍需确认的是「11-01 之后是不是用户主动停的」。
- **影响**：已排除「幽灵生产线」风险；真实风险只剩「本地继续跑而不同步 origin/main 会覆盖线上 5 篇入口」。
- **建议动作**：问用户「11-01 之后是否你主动停的」（1 分钟）。若是主动停 → 直接重启；若不是 → 定时任务集体失效，需排查调度侧，否则重启后还会再停。
- **来源**：`08-execution/2026-11-07-daily-run.md:108-109,124`

### P0-6 索引验证/数据通道仍双轨脆弱（浏览器故障 + API 凭证）
- **事实**：10-24、10-25 两晚 0/8 新鲜状态（Google 检索后端挂起 + 本机 `ERR_CONNECTION_TIMED_OUT`）；10-27 API 首跑 8/8 ERROR（OAuth 令牌刷新超时）；10-29 全端点不通（oauth2/searchconsole 直连与代理均超时）；11-07 官方 API 才恢复直连成功。
- **影响**：收录结论在通道故障期不可下；一旦再断，索引线停摆。
- **建议动作**：①确认 `gsc_url_status.py`/`scripts/gsc_pull.py` 的 refresh_token 有效期与自动续期；②浏览器通道保留为降级但不再作为主路径；③所有收录报告必须写明通道与时点（10-24/10-25 报告已树立正确做法：无新鲜数据就写「未验证」）。
- **来源**：`anari-index-verify-2026-10-24.md:7-15`；`anari-index-verify-2026-10-25.md:7-15`；`anari-index-verify-api-2026-10-27.md:8-19`；`anari-ru-es-indexing-check-1029.md:9`；`08-execution/2026-11-07-daily-run.md:5,128`

---

## 2. P1（17 项）

| # | 事项 | 现状 / 缺口 | 建议动作 | 来源 |
|---|---|---|---|---|
| P1-1 | RU/ES 6 个新页 0/6 收录 | PR #38（c5767c1）10-28 上线，10-29、10-30 两次复查均 `URL is unknown to Google` | 从已收录 EN 对应页加 hreflang 互链 + IndexNow 补提交；下次复查并入周档 | `anari-ru-es-indexing-check-1029.md:7-20`；`anari-ru-es-indexing-recheck-1030.md:6-18` |
| P1-2 | 连接器词簇仍未破零 | 文章 10-23 已收录，10-26/10-29 三次验证 ccs/connector/nacs 3 个月窗口 0 展示 0 点击 | 保持观察（收录 6 天，正常积累期）；从已收录 franchise/fleet-depot 文补 1–2 条上下文内链；里程碑：破零后 2 周 p≤50、4 周 p20-40 | `anari-connector-baseline-recheck-2026-10-29.md:8-60` |
| P1-3 | Discovered 桶 43 条未被抓取（8 博客 + 5 产品页等） | 内链方案已就绪（18 条 / 15 来源 / 13 目标）但**未执行** | 下一轮站点迭代直接执行 `anari-interlink-plan-20261101.md`，来源页必须已收录、正文自然段、每页 1–2 条 | `anari-interlink-plan-20261101.md:1-50`；`anari-index-coverage-recheck-20261029.md:64-83` |
| P1-4 | franchise 支柱页/profit 页 CTR 长期为 0 | 支柱页 0/61（28d）、0/12（周）；profit 0/54（周）。观察窗（10-23 起 7–14 天）已到期 | 按 10-23 判定：若验收周仍 0% → 提请用户按「推荐 A」追加总账数字（$115k–$550k all-in / $8k–$60k/站/年）；否则继续观察 | `anari-1023-judgment.md:36-52`；`anari-weekly-actions.json` a-ctr-rewrite-v2-franchise |
| P1-5 | AI 可见度测量环境未中性化 | 两期（10-22、10-29）都被账号记忆污染；Perplexity 连续两期被 Cloudflare 拦；10-29 「1/18 宽松、0/18 保守」 | 提用户建专用无记忆测量账号 或 提供登出态浏览器 profile；Perplexity 测前手动过验证；否则趋势线永远不可比 | `anari-ai-visibility-2026-10-29.md:5-27,48-53` |
| P1-6 | AI 可见度倒逼的两个内容缺口 | ①apartment-condo 文缺「计费软件供应商选择」段（Gemini Q10 已被 ChargePoint/FLO/Wallbox/SWTCH 占位）；②缺 become-a-cpo 步骤指南支柱页（Gemini Q2 引 ChargeTronix/Powerbank） | ①下一轮 apartment 文增补选型框架 FAQ（不点名贬损）；②新增 CPO 支柱页（~2000 词，步骤化+检查清单表+FAQ） | `anari-ai-visibility-2026-10-29.md:50-53`；`anari-weekly-actions.json` a-aivis-apartment-software-list / a-aivis-become-cpo-pillar |
| P1-7 | GEO 优化师 / 竞品情报 / 内容验收员 调度漏跑 | GEO 10-29 档未见 run（最近 10-22 超时）；竞品 10-28 漏跑；验收员 10-28/29/30 连续三档无 run（10-31 才恢复） | 排查调度器 fire 记录与机器休眠/会话忙；给这三个岗加「漏跑即告警」哨兵 | `anari-daily-summary-2026-10-31.md:29-43`；`anari-daily-summary-2026-10-28.md:33-35` |
| P1-8 | 抑制名单与 Brevo 退订未联动 | suppressions 表已上线（10-28），但 Brevo 里取消订阅的联系人不会自动回流 | 决策：定期人工对照导入（§10 命令）vs 做 Brevo webhook→Worker 自动同步（需签名验证端点） | anari-new-site/plan.md:784-806 |
| P1-9 | Gatekeeper 白名单不含多语言/产品/方案页 | #16 四页、PR #36、PR #38 都被拦转人工（每次多一轮人工审核） | 把 `site/ru/** site/es/** site/products/** site/solutions/**` 纳入内容白名单（10-28 已列遗留建议） | plan.md:843-849（10-28 迭代④遗留建议） |
| P1-10 | 事件分层与归因参数的 GTM 后台增量未配置 | 代码侧 10-26/10-28 全部上线（submission_id/attr_*/form_start/submit_attempt/submit_failure），GTM 侧 0 配置 | 与 P0-3 合并一次做完（约 25 分钟），做完后 GA4 才有完整漏斗与归因维度 | plan.md:699-702；anari-new-site/plan.md:882-888；audit #3/#15 |
| P1-11 | 海湾双页（沙特/约旦）待批准 | 分支 `content/markets-gulf-reports` 已成型（四道门全绿、镜像 60/60、validate 106 页、check-facts 65 项），未推送 | 周一复盘议程 ⭐：批准则推送即触发 Gatekeeper 自动合并，验收员按清单六步（含 IndexNow+GSC） | `anari-monday-review-1026.md:14-27`；`anari-weekly-actions.json` a-comp-country-lp |
| P1-12 | China OEM 着陆页逾期 | a-comp-china-oem-page due 11-05，未做（与 D1 买家指南文错位：文=博客、LP=厂商页） | 排入下一轮站点迭代维度池；与 D1 文互链防撞意图 | `anari-weekly-actions.json` a-comp-china-oem-page；`anari-adjudication-input-2026-10-26.md:15-19` |
| P1-13 | 案例证据链不完整（审计 #17） | fact-library case 8 条 verified，jordan 页有 Source/Last verified；缺测试报告、可用率统计口径、客户授权披露范围、ROI 计算口径 | 向业务要 3 份材料；补齐后补 case 页证据区 | `ops/audit-checklist-20261022.md:43` |
| P1-14 | anariev 新站「30+ 国」口径未清 | `anari-new-site/anariev/deliverables/llms-full.txt` 两处违规；须先改源文再重新生成（否则被覆盖） | due 11-08 执行；同时确认两份仓库副本哪份为正本 | `anari-weekly-actions.json` a-fact-22countries-anariev；`anari-review-weekly-brief-2026-10-26.md:26-28` |
| P1-15 | 询盘漏斗周报 / GSC 周报的桥回退改造未执行 | 10-28 已预授权「若再失败按 OpenSEO 桥回退改造」，11-02 档已漏 | 11-09 周一档执行改造（含 cbc21777） | `anari-daily-summary-2026-10-28.md:31-32,52`；`anari-daily-summary-2026-10-31.md:56` |
| P1-16 | /agents/ 页排名 71.7 诊断未做 + apartment 页两周验收未排 | /agents/ 16 展示/周、p71.7；apartment 页 10-28 加深后目标 p49.5→前 30 | 排入下一轮 R2/R3 档；apartment 验收看 11-11 后的周报 | anari-new-site/plan.md:862-866（下周队列候选） |
| ~~P1-17~~ **【已闭环 2026-11-07】** | ~~外链主动成果仍为 0（16 封邮件未发）~~ **用户 2026-11-07 确认：此前已发过** | ~~4 封（top3+Canary）+ 12 封（模板 H）稿件全部就绪，卡在「必须从 sales@ 人工发」~~ 用户拍板已发，不再挂待办；与 WAVE1–3（10 月联系过的在 WAVE2 二触里已按「承认上次角度错」改写）无双线冲突 | 用户 2026-11-07 口头确认 | `anari-top3-canary-refresh-1026.md:1-7`；`anari-daily-summary-2026-10-31.md:59-62`；actions a-send-template-h-and-top3 |

---

## 3. P2（14 项）

| # | 事项 | 说明 | 来源 |
|---|---|---|---|
| P2-1 | validate.js 分级质量引擎（Blocker/Major/Minor） | 审计 #22 未做；事实语义已由 check-facts 部分等效 | audit-checklist:48 |
| P2-2 | 5 个 Skill（release-qa/content-evidence-qa/search-opportunity/lead-conversion/calculator-validation） | 审计 #24 未建，非 Skill 形态 | audit-checklist:50 |
| P2-3 | MCP 只读连接 GitHub/Cloudflare/GSC/GA4/HubSpot | 审计 #25 未建；GSC 已用官方 API 但其余未接 | audit-checklist:51 |
| P2-4 | Growth Brain 增长决策引擎 + A/B/C 总框架 | 审计 #36，长期方向 | audit-checklist:72 |
| P2-5 | 视觉回归 / JS 错误监控 / 部署告警 / CWV 监控制度化 | 审计 #32 部分；仅做过一轮性能实修 | audit-checklist:68 |
| P2-6 | 转化实验机制（A/B 或分阶段） | 审计 #28；首页改版 8 条验收中 #1/#2 仍待数据 | audit-checklist:59 |
| P2-7 | 设计 Token / 组件库 / 移动端规范 | 审计 #33 部分；首页三语已重构但全站未建 Token 体系 | audit-checklist:69 |
| P2-8 | 内容质量八项门槛自动化 | 审计 #35；仅事实与结构两项自动化 | audit-checklist:71 |
| P2-9 | 四方数据统一分析维度（搜索/站/CRM/商机） | 审计 #26，依赖归因后台配置完成 | audit-checklist:57 |
| P2-10 | 内容→询盘→商机闭环 | 审计 #27，依赖 P2-9 | audit-checklist:58 |
| P2-11 | 询盘质量评分（Lead Score vs Deal Probability） | 审计 #30；建议积累 4–6 周真实询盘后再定规则 | audit-checklist:66 |
| P2-12 | Benchmark 原创数据研究立项 | 最强引用磁铁（外链+AI 引用双赢），待用户决策 | monday-review-pack:44 |
| P2-13 | 真实项目摄影（库内仅 5 张真实现场照） | 首页/产品/方案页循环使用同一批图；建议按 5 类各拍一组 | plan.md:408-409 |
| P2-14 | 事实库 2 条「未覆盖」+ 设计资产小项（BESS stat-label 等） | check-facts 报 60 一致/2 未覆盖；属覆盖缺口非错误 | anari-new-site/plan.md:60,77（10-27/10-28 门禁记录） |

---

## 4. 卡在人手上（14 项，机器无解）

> 判定标准：**只有用户/真人能执行**（第三方后台 UI、真实邮箱发信、业务拍板、真实素材）。这些不该再出现在自动化队列里。

| # | 事项 | 为什么必须人做 | 耗时 | 影响 |
|---|---|---|---|---|
| H1 | Brevo Contacts 核对真实询盘（10-26 后有无新增 / ANARI_* 七属性是否有值） | 需登录 Brevo 后台；禁浏览器自动化 | 1 分钟 | 决定「询盘是否真为 0」 |
| H2 | GTM/GA4 后台配置（Phase 1 归因 6 参数 + 事件分层 3 事件 + 5 自定义维度） | 需 GTM/GA4 UI；禁浏览器自动化 | ~25 分钟 | 决定漏斗/归因是否可用 |
| H3 | GA4 Consent Mode 与既有事件体检 | 同上（attribution Phase 0 人工项） | ~20 分钟 | 欧盟合规 + 数据完整性 |
| H4 | 发外链邮件（top3+Canary 4 封 + 模板 H 12 封） | 必须从 sales@anarienergy.com 实发（发件人信誉） | ~30 分钟 | 主动外链成果=0 的唯一堵点 |
| H5 | 稳定代理/出口（Google 端点间歇断） | 本机网络环境 | 不定 | 索引复查/看板/GSC 周报可用性 |
| H6 | 海湾双页上线批准（含 SASO 措辞「delivered with SASO certification」认可与否） | 业务/合规拍板 | 5 分钟 | 国家落地页 11-08 到期项 |
| H7 | 验收口径拍板（/products/ 是否改 ≥100 展示+28 天；/inquiry 三语是否合计） | 定 KPI 口径 | 5 分钟 | 否则每次读数随机翻转 |
| H8 | business-plan title/meta 改动授权（A1） | 改 title 需用户审核 | 5 分钟 | 当前唯一能直接抬 CTR 的动作 |
| H9 | 断档期运营归属确认（11-02 后谁在跑） | 只有用户知道 | 1 分钟 | 决定接管是否残缺 |
| H10 | Brevo 退订联动决策（人工导入 vs webhook 自动同步） | 业务/技术取舍 | 10 分钟 | 合规（GDPR 删除请求） |
| H11 | Reddit karma 报数（u/Sad-Researcher3564，10-21 实测 karma=1） | 需打开 reddit 看 | 1 分钟 | 10 条储备帖能否放行（≥100） |
| H12 | Qwoted 档案补完（剩 25%） | 平台账号操作 | 10 分钟 | 免费 PR 被动曝光入口 |
| H13 | 业务侧 5 项决策：定价带宽（from $8–15k / 单站 $120–350k / 网络 $400k–1M+）、两封具名推荐信、本地电话/WhatsApp、日历预约、真实摄影 | 业务事实，不能编 | — | 转化与采购尽调的直接门槛（plan.md:309-315 五项） |
| H14 | anariev 仓库正本确认（两份副本哪份为准） | 需用户判断 | 2 分钟 | 决定 P1-14 怎么修 |

---

## 5. 外部阻塞（11 项，非人力可控）

| # | 阻塞源 | 影响 | 证据 | 缓解 |
|---|---|---|---|---|
| E1 | **Google 官方端点间歇不可达**（search.google.com / oauth2 / searchconsole.googleapis.com） | 10-22~10-31 看板全走桥回退；10-27 API 8/8 ERROR；10-29 全端点超时；11-07 才恢复直连 | `anari-daily-summary-2026-10-22.md:17`；`anari-index-verify-api-2026-10-27.md:8-19`；`anari-ru-es-indexing-check-1029.md:9` | 官方 API 为主 + 桥回退兜底；所有报告标通道与时点 |
| E2 | **本机代理/VPN 抖断**（Clash 节点掉线；`ERR_CONNECTION_TIMED_OUT`） | 连堵两晚收录复查；GSC 周报/漏斗周报晚间档失败 | `anari-index-verify-2026-10-25.md:11,49`；`anari-daily-summary-2026-10-27.md:44,51` | 换稳定节点；GSC 拉数改 API 直连（11-07 已成功） |
| E3 | **Brevo 后台**（受限 key、UI 验证弹窗卡死、黑名单需人工同步） | ANARI_* 属性无法脚本核验；退订回流不通 | plan.md:657-659；anari-new-site/plan.md:802-806 | 只读 API + 人工一眼核对；退订导入走文档命令 |
| E4 | **Cloudflare Workers build delays 事故**（2026-10-26 15:12 UTC 起） | #16 前两页 + PR #36 积压约 24h 未部署 | plan.md:710-735 | 已恢复（10-27 21:35 补验收全过）；部署等待时不改标题反复排查 |
| E5 | **Cloudflare 控制台导航超时**（dash.cloudflare.com） | 10-26 无法自查构建状态 | plan.md:199（actions 备注） | 用 `curl` 查线上而非进控制台 |
| E6 | **Perplexity Cloudflare 人机验证**（连续两期） | AI 可见度整引擎 10 格空白 | `anari-ai-visibility-2026-10-29.md:27` | 测前手动过验证保持会话；不绕验证（红线） |
| E7 | **GSC URL Inspection 日配额**（~5/天，10-12 上限） | 10-19 索引请求 1/4 成功；10-21 5 篇排队 | `anari-weekly-ops-1019.md:63`；plan.md:236 | 分批提交；API 查询不计该配额（200/天独立） |
| E8 | **GitHub HTTPS 间歇故障**（SSH 正常） | 10-22 建 PR 失败、compare 页 form.submit 静默失败 | `anari-index-coverage-weekly-summary-20261022.md:34`；plan.md:613 | 用 `git ls-remote refs/pull/*` 作权威判据；委托管线建 PR |
| E9 | **Quora 发布通道限流** | 10-19 ROI 稿两次提交被吞（0/2） | `anari-weekly-ops-1019.md:67-71` | 隔 ≥24h 重试；每会话首发后 ~30 分钟窗口；被吞即停防风控 |
| E10 | **Reddit 账号风控** | r/evcharging 两条评论被系统移除；karma=1 无法发带链接帖 | `anari-weekly-actions.json` a-reddit-karma-grow note；`anari-weekly-ops-1019.md:84` | 只投 r/electricvehicles + r/electriccars；纯干货养号 |
| E11 | **WebBridge/浏览器自动化限制**（GSC Shadow DOM、Gemini isTrusted、非激活标签页导航挂起） | 三次实测踩坑：合成 click 无效、提交被拒、导航不执行 | `anari-index-verify-2026-10-24.md:41-42`；plan.md:693；`anari-ai-visibility-2026-10-29.md:26` | 用 CDP 真实事件 + activate_tab；能走 API 就不走浏览器 |

---

## 6. 已闭环但容易被误当未闭环（防重复劳动）

| 事项 | 闭环证据 |
|---|---|
| Worker v2 部署 + 验收 4/4 | plan.md:654-663（10-22 深夜） |
| #16 四个客群页转化重构 | anari-new-site/plan.md:761-783（10-27 深夜全部完成） |
| #23 抑制名单 + 审计日志 | anari-new-site/plan.md:784-815（10-28） |
| 10-21 批次 5 篇收录状态悬置 | `anari-index-verify-2026-10-26.md:8-27`（8/8 全收录） |
| 连接器文章收录 | 10-23/10-26/10-30 三次确认 indexed |
| 两篇前拒文（transformer/franchise-kenya） | `anari-index-coverage-recheck-20261029.md:23-30`（已自愈，Plan B 无需放行） |
| Brevo 测试联系人清理 | plan.md:700（e2e-phase1 已不存在；4 条已 API 删除） |
| 400 电话条目 / 功率口径漂移 | plan.md:633,639（事实门抓出并修复，fact-library 转 verified） |
| GTM 关键事件标记 | `anari-weekly-actions.json` a-ga4-key-event（用户 10-21 已完成） |

---

## 未闭环（2026-11-13 新增）

| 事项 | 阻塞原因 | 最小解 | 复跑 |
|---|---|---|---|
| ~~GSC sitemap 重提~~ | ✅ **2026-11-13 已解决**：根因是「复用旧标签导致页面被节流」，改每 URL 开新标签后一次成功；API 回读 `lastDownloaded=2026-11-13T15:05:36Z`、`submitted=272`（Google 1.4 秒后重读） | 已固化进 `scripts/tools/gsc_request_indexing.py`（fresh_tab）与 BROWSER-CAPABILITY 坑 1 | — |
| **GSC requestIndexing 剩余未收录页**（97 → 已请求 9 个；GSC 配额约 10/天） | 首批 9/10 已成功；剩余按价值分批（拉美国别页 → regulations → 其余） | 每个批次 ≤10 URL，逐日推进；脚本已修（fresh_tab + 502 重试） | `python3 scripts/tools/gsc_request_indexing.py <url...>` |
| **IndexNow**（已完成，非阻塞） | — | — | 97 个未收录 URL 已 POST，HTTP 200；台账 `08-execution/tech/indexnow-20261113-unindexed.json` |

### 已排查但不可用（2026-11-13，避免后续重复搜索）

| 方案 | 结论 | 证据 |
|---|---|---|
| **GSC 服务账号（service account）** 直写 `sitemaps.submit` | ❌ 本机无凭证：`~/.config/seo-skills/` 不存在，`.secrets/` 内无 `type: service_account` JSON；只在旧 Kimi 工作区 `~/Documents/kimi/workspace/.agents/skills/seo-google/references/auth-setup.md`（只读参考）里有做法说明 | 全盘搜索 `*service*account*.json` / `google-api.json` 结果为空 |
| GSC OAuth **写权限**（`webmasters` 而非 `readonly`） | ❌ 现有 refresh_token 只授了只读 scope，`PUT /sitemaps/...` 返回 **403 insufficient scopes** | 2026-11-13 实测 |
| **浏览器（fresh_tab）** | ✅ **当前可用**：每 URL 开新标签后 sitemap 重提 1 次成功、requestIndexing 9/10 成功 | `08-execution/tech/2026-11-13-index-batch-attempt.md` |

> 若将来要做**无人值守的每日 sitemap 提交**（现在靠人工/会话触发），最小路径是：创建 GCP 服务账号 → GSC「用户和权限」加为该账号 `client_email`、级别 Full → 放 JSON 到 `.secrets/`。
> 这需要用户操作（建 key + 加用户），不能由 agent 代做。
