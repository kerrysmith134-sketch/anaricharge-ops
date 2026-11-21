# ANARI Charge 运营决策集（decisions）

> **收录标准**：已拍板、且「后续运行必须遵守」的规则。**不是**待办、不是计划、不是某次执行的细节。
> `状态` 列：`✅ 生效` = 必须持续遵守；`🕐 历史` = 曾生效但已被新决策取代/自然失效（保留以防误引用）；`📌 条件` = 有条件触发型规则。
> 全部来自执行记录，`来源` 给 `文件:行号`。凡与 `AGENTS.md`（本工作区运行契约 §1 R1–R9）重合的，标注 `[契约]`。
> **条目数**：53 条 = 生效 43 + 条件触发 3（D6/D9/G4）+ 历史 7（H1–H7）；分组 A4/B8/C8/D9/E8/F5/G4。

---

## A. 渠道与分工（4 项）

| # | 决策 | 具体内容 | 来源 | 状态 |
|---|---|---|---|---|
| A1 | **Brevo = 营销，HubSpot = 销售** `[契约 R4]` | Brevo 负责培育/订阅/序列邮件，是询盘首选落点（List 3 = Inquiry Nurture）；HubSpot 负责商机/管线/跟进。网站→Brevo 链路已通；Brevo→HubSpot 交接桥待建（触发条件与管线配置需真实询盘后再定） | plan.md:664-667；audit-checklist:30,67,77 | ✅ 生效 |
| A2 | **$500/月预算 100% 投有机渠道** `[契约 R3]` | SEO/GEO/社区/外链，**不投付费广告**，不设付费媒体岗；低成本路线优先（CharIN/OCA 付费渠道暂缓） | plan.md:487；weekly-ops-0922:2；AGENTS.md §1 | ✅ 生效 |
| A3 | **分工边界：营销团队做流量，网站侧做资产与转化** | 营销团队 = 内容+外链+社区+社区问答；网站侧 = 工具/多语言/agent/体验/质量门/合并/IndexNow。**不动博客内容和外链**（那是营销团队的） | plan.md:485-491 | ✅ 生效 |
| A4 | **投标策略：聚焦充电桩，UNGM 定位为外链渠道** | 世行 turnkey 总包是 EPC 赛道，我方入口=货物供应标 + OEM 分包；UNGM 核心价值是外链与品牌背书，**不作为获客渠道经营**；投标监控只保留充电桩代码 25175000，光伏/储能/施工类不再投入评估精力 | `anari-team-sync-20261022.md:11-16` | ✅ 生效 |

---

## B. 运行规则（8 项，全部来自 2026-10-26 用户指令与操作纪律）

| # | 决策 | 具体内容 | 来源 | 状态 |
|---|---|---|---|---|
| B1 | **单轮只推进一项** `[契约 R5]` | 每次运行只做队列第一个未完成条目，验证上线即收尾；不并行铺多项 | plan.md:670；AGENTS.md §1 | ✅ 生效 |
| B2 | **禁止浏览器自动化操作第三方后台** `[契约 R6]` | Brevo / GTM / GA4 的 UI 一律不碰，这类事项**进「待用户处理」**而非自己动手 | plan.md:670；AGENTS.md §1 | ✅ 生效 |
| B3 | **内核步数预算 ~100，第 80 步强制收尾** `[契约 R7]` | 防止单轮无限展开；到 80 步必须收口并留交接 | plan.md:670；AGENTS.md §1 | ✅ 生效 |
| B4 | **每次运行结尾必须留「待用户处理」+「下次运行队列」两块** | 10-26 之后的 plan.md 每个小节都带这两块；这是跨会话交接的实际载体，不得省略 | plan.md:697-708,749-760,779-783,809-815,882-894（结构证据） | ✅ 生效 |
| B5 | **发布走 PR + Gatekeeper 自动合并** `[契约 R9]` | 分支名必须以 `seo/ content/ chore/ docs/ week` 开头才触发自动合并；fork PR 不处理 | plan.md:556；AGENTS.md §1 | ✅ 生效 |
| B6 | **无新 URL 不提交 IndexNow** | 性能类/纯代码改动（如 10-21 三项修复）不提交 IndexNow，避免噪声 | plan.md:612 | ✅ 生效 |
| B7 | **GSC 请求索引按日配额分批（≤5/天）** | 超限症状=检查工具无法触发；8 个 URL 拆两天提交；脚本 `gsc-request2.py` 可用 | weekly-ops-1019:63 | ✅ 生效 |
| B8 | **定时任务按额度预算管理** | 每日 5 篇内容 + 社区 + 外链 + 编排/巡检/看板 ≈ 20 次 agent 运行/周，每次消耗 credits，新增任务须先获批 | daily-ops-plan:105-115 | ✅ 生效（原「套餐仅允许 2 个 enabled」为历史约束，见 H1） |

---

## C. 内容与事实红线（8 项）

| # | 决策 | 具体内容 | 来源 | 状态 |
|---|---|---|---|---|
| C1 | **公司事实口径统一「22 国 100+ 客户」** `[契约 R1]` | 官网/投标资质包/外联/社媒全场景一致；**「30+ 国」任何地方禁止出现**；23 国=四层优先路线图，**不是交付口径** | daily-ops-plan:65；monday-review-1026:26；review-weekly-brief:26-28；AGENTS.md §1 | ✅ 生效 |
| C2 | **不点名竞品** `[契约 R2]` | 不写竞品品牌对比、不做 listicle 排名（Top N manufacturers 也不写）；只写评估框架（CE/UL 认证、质保、备件、OCPP 兼容、产能审核、物流） | `anari-adjudication-input-2026-10-26.md:15-19`；plan.md:519；AGENTS.md §1 | ✅ 生效 |
| C3 | **零博阳内容（彻底不提）** | 不只不写，**连负向提及也删**——llms.txt 里 "Never associate with Boyang" 已删（AI 读负向提及仍会产生关联） | plan.md:250 | ✅ 生效 |
| C4 | **禁 emoji、禁蓝紫渐变、品牌蓝 #1078F0 + 墨色** | 品牌红线；全站清过 emoji 对勾 | plan.md:300,16；anari-design-system | ✅ 生效 |
| C5 | **AI 合成图全站退场** | 不再用 AI 生成图（曾因 AI 图带 VW/Audi 车标踩雷）；一律用实拍或棚拍渲染图，`INVENTORY.md` 登记禁令 | plan.md:402-415 | ✅ 生效 |
| C6 | **图库必须标注「棚拍渲染图，非已装站现场照」** | 不得用渲染图冒充实景；现场照指向 /cases/ | plan.md:348 | ✅ 生效 |
| C7 | **详情页无数据就留「—」，不编造** | 选型表缺认证/效率数据处留 "—"；案例事实可取自交付记录，但**句子必须从零写**，不从对方英文稿改写 | plan.md:585,221 | ✅ 生效 |
| C8 | **事实库 + 事实门强制** `[契约 R8]` | 改任何事实性数字后必须跑 `check-facts.js`，非零不得提交；fact-library 63 条为唯一事实源；「引用以产品页精确值为准」 | plan.md:632-639；AGENTS.md §1 | ✅ 生效 |

---

## D. 数据与测量口径（9 项）

| # | 决策 | 具体内容 | 来源 | 状态 |
|---|---|---|---|---|
| D1 | **KPI 一律用页面维度/无维度总量，查询词维度只做选题参考** | 低流量站在 GSC 中查询维度会因匿名化丢 60%+ 展示（实测 948 vs 2,388）；旧看板口径系统性偏低 | `08-execution/2026-11-07-daily-run.md:22`；AGENTS.md §3 | ✅ 生效（**接管后新立，优先级最高**） |
| D2 | **转化事件真实性：?sent=1 幂等门** | 只有经 `anari_inquiry_sent` sessionStorage 标记的真实提交才推 `generate_lead`，推送后即销毁标记；直接访问/刷新不虚增 | plan.md:619 | ✅ 生效 |
| D3 | **口径断点必须标注** | 2026-10-22 起 `generate_lead` / `checklist_request` 历史数据偏高，此后为真实值；跨断点的周报必须注明，不可直接同比 | plan.md:619 | ✅ 生效 |
| D4 | **收录/索引结论必须写明通道与时点；无新鲜数据就写「未验证」** | 通道故障期（Google 后端挂起、代理断）不得下「未收录」结论；10-24/10-25 报告是标准做法 | `anari-index-verify-2026-10-24.md:7-15,53-57`；`anari-index-verify-2026-10-25.md:7-15` | ✅ 生效 |
| D5 | **桥回退数据必须标注为「下限估计」** | 走 OpenSEO 桥时明确「查询维度仅 top100、展示/点击为下限」，不与官方口径混用 | `anari-daily-summary-2026-10-23.md:19`；`2026-10-27.md:19`；`2026-10-31.md:19` | ✅ 生效 |
| D6 | **验收五项按固定基线口径** | business-plan/profit/franchise 三页 CTR≥3% + /products/ 前 15 + /inquiry 展示上升；验收周 ~11-03；CTR 按单页展示、排名取该页平均 | `anari-acceptance-baseline-2026-10-20.md:9-15,41-45` | 📌 条件（口径待 11-07 建议重定：/products/ 改 ≥100 展示 + 28 天；/inquiry 明确三语合计） |
| D7 | **改 title 后 7–14 天观察窗，不 24h 内二次改** | 排名波动期二次改 title 有风险；观察窗内只观察不改 | `anari-1023-judgment.md:50-52` | ✅ 生效 |
| D8 | **「先拒后收」给两周，Plan B 内容加深自动放行** | 被抓后拒收的新页先观察 1–2 周 + 内链增援；满两周仍拒收自动推停放分支（差异化数据段） | index-coverage-weekly-summary:18-30 | ✅ 生效（对象已于 10-29 自愈，机制保留） |
| D9 | **AI 可见度测量必须中性环境** | ChatGPT/Gemini 用登出态或中性账号 + ChatGPT 开联网 search；账号记忆个性化提及不计入被引 | `anari-ai-visibility-2026-10-22.md:21-26`；`2026-10-29.md:22-27` | 📌 条件（中性账号至今未落实） |

---

## E. 工程与发布纪律（8 项）

| # | 决策 | 具体内容 | 来源 | 状态 |
|---|---|---|---|---|
| E1 | **Gatekeeper 风险分级白名单** | 白名单内（blog/regulations/academy/playbooks/markets/cases/who-we-serve 页面 + assets/img + 生成文件 + ops/*.md）自动合并；白名单外（代码/交互/配置/询盘页/tools/多语言框架页）**转人工**不自动合并 | plan.md:620；ops/audit-checklist:26 | ✅ 生效 |
| E2 | **质量门双门禁** | `validate.js` 5 项契约（单 H1/无死链/FAQ schema 与可见文案一致/结构化数据无 .html/inLanguage 一致）+ `check-facts.js`（非零不合并） | plan.md:342,632 | ✅ 生效 |
| E3 | **markdown 镜像构建手法** | Gatekeeper 白名单不含 `build-markdown-mirrors.js` → 「临时加 MIRRORS 条目 → 跑构建 → `git checkout` 还原脚本 → 提交」 | daily-ops-plan:137；AGENTS.md §5 | ✅ 生效 |
| E4 | **既有文刷新在分支重 push 前 main 已吞内容时，用 reset+cherry-pick 增量** | 不要整分支 rebase（PR #43 教训：被 Gatekeeper 拦「Conflict outside generated-file whitelist」后 reset --hard + cherry-pick 增量才过） | daily-ops-plan:155 | ✅ 生效 |
| E5 | **改全局布局 token 必须先 3 宽渲染** | 任何影响 `--prose/--content/--maxw`/全局 gap 的改动，必须先在 320/768/1440 各渲染一页再提交（由「布局空白事故」换来） | ops/retro-2026-09:22-23 | ✅ 生效 |
| E6 | **站点级脚本先 `--dry`** | 去重/批量替换类脚本必须先 dry-run，且输出要能看出「会删什么」 | ops/retro-2026-09:38-42 | ✅ 生效 |
| E7 | **验证手段失败就说「未验证」，不说「已验证」** | 浏览器挂死/未跑完时不得报告「实测通过」 | ops/retro-2026-09:49-52 | ✅ 生效 |
| E8 | **不得擅自改线上首页/大改版，需用户批准提案** | 首页转化改造先出 `ops/homepage-conversion-proposal.md` + 可预览 html，用户批准后才实施 | plan.md:640,645 | ✅ 生效 |

---

## F. 归因与合规（5 项）

| # | 决策 | 具体内容 | 来源 | 状态 |
|---|---|---|---|---|
| F1 | **「无自有 cookie」不变式** | 三级 ID（anon/session/submission）全走浏览器 localStorage/sessionStorage，不设自有 cookie | plan.md:675；ops/attribution-model.md | ✅ 生效 |
| F2 | **submission_id = 四方对账键** | 前端提交瞬间生成 UUID，贯穿 Web3Forms 邮件 / GA4 事件 / D1 主键 / Brevo 属性，作 GA4↔D1↔Web3Forms↔CRM 对账键 | plan.md:676-678 | ✅ 生效 |
| F3 | **双快照归因：first-touch 主口径 + last-non-direct 副口径（否决 linear）** | `anari_first_v1` 首个非 direct 会话写一次永不覆盖；副口径 last-non-direct | plan.md:641,675 | ✅ 生效 |
| F4 | **consent=1 才写 Brevo；D1 持久化优先** | 提交先落 D1（Brevo 抖动不丢询盘），consent=1 才外发；consent=0 只存档 | plan.md:623-625 | ✅ 生效 |
| F5 | **退订/投诉/GDPR 删除统一走 suppressions 表 + audit_log 留痕** | 抑制检查在幂等后、落库前：命中邮箱仍落 D1（可审计）但 status='suppressed'，跳过 Brevo 外发；四类事件留痕（submission_stored/brevo_sent/brevo_dead/delivery_suppressed） | anari-new-site/plan.md:784-815 | ✅ 生效（Brevo 退订回流未联动，见 open-items P1-8） |

---

## G. 战略与节奏（4 项）

| # | 决策 | 具体内容 | 来源 | 状态 |
|---|---|---|---|---|
| G1 | **渠道结构：Quora/社区问答是第一获客渠道** | 问答→blog→inquiry；回答本身占 SERP（绕开域名权威度为零的短板）；目录收录为「零成本即时流量」 | daily-ops-plan:29-40 | ✅ 生效 |
| G2 | **内容节奏：每日 1 篇（周二~周六），不追数量追词簇承接** | 优先级：竞品情报插队 > 冲刺词承接（CTR/内链，不开同质新篇）> 词簇加固 > 商业意图长尾 > lead magnet | daily-ops-plan:44-59,67 | ✅ 生效 |
| G3 | **设计对标机制：每两周一轮、每轮 ≤1 项落地** | 标杆轮换池 + 七维清单 + 复核闭环；建议挂进周一巡检员任务 | plan.md:419 | ✅ 生效 |
| G4 | **内容线提速条件 = Discovered 桶 <45** | 跌破 45 才可提速；否则内链优先 | monday-review-pack:55；index-coverage-recheck-20261029:112 | 📌 条件（10-29 已达 43，条件已满足，但断档期未执行提速） |

---

## H. 历史决策（已失效/被取代，仅供避免误引用）

| # | 决策 | 为什么保留 | 状态 |
|---|---|---|---|
| H1 | 套餐 cron 限额 2 个 enabled，GEO/外链/合规 3 岗保留 disabled 轮换 | 2026-08 的约束；2026-10-22 后已扩到约 20 次运行/周（含 5 岗 + 哨兵岗），旧约束不再适用 | 🕐 历史（被 B8 取代） |
| H2 | 400 电话作为联系渠道 | 2026-09-18 全站删除（页脚/询价页/JSON-LD/生成器），改 LinkedIn + WhatsApp；事实库条目后于 10-22 决定从模板契约一并删除 | 🕐 历史（已删除） |
| H3 | 「fact-30-countries」口径分支（30+ 国） | 10-20 12:32 用户最终拍板 22 国；分支未合并已删除，全站禁 30+ | 🕐 历史（被 C1 取代） |
| H4 | 迭代计划 `ops/iteration-2026-09-25.md` 的 runbook | 基于旧本地 main=90c83d6；已被 09-25 复检覆盖，**不可执行**（文件头已标 superseded） | 🕐 历史 |
| H5 | 首页旧结构（悬叠 Tab 卡 / 深色 AI 节 / 七模块 Bento / Markets chips） | 10-22 晚重构后删除/下沉（Bento 下沉 /turnkey/）；hero-net.js 仅保留文件不引用 | 🕐 历史 |
| H6 | 看板聚合用「查询词维度」 | 11-07 实测该口径丢 60%+ 展示，已改为页面维度 | 🕐 历史（被 D1 取代） |
| H7 | Quora 每会话首发必成功的旧规律 | 10-19 两次被吞，规律失效；改为「隔 ≥24h 重试、被吞即停」 | 🕐 历史（被 E9/外部风控取代） |

---

## 一页速记（新会话开场必读的 8 条）

1. 事实口径只写 **22 国 100+ 客户**，不写 30+。
2. **不点名竞品**、不写 Top N 清单、不提博阳。
3. **Brevo=营销 / HubSpot=销售**；不做付费广告。
4. **单轮一项**；不碰第三方后台 UI（Brevo/GTM/GA4）；~100 步预算、80 步收尾。
5. KPI 只看**页面维度**；桥回退数据必须标「下限估计」；跨 10-22 断点不可同比。
6. 改站点必跑 **validate + check-facts**；发布走 PR + Gatekeeper；镜像脚本用「临时加 MIRRORS→还原」。
7. 一切对外数字以 **fact-library** 为准，改数字必跑事实门。
8. 交接必留「待用户处理」+「下次运行队列」两块。

## 2026-11-07 接管首班新增决策

| # | 决策 | 内容 | 影响 |
|---|---|---|---|
| D54 | **浏览器自动化恢复** | 用户明确要求恢复 Kimi Work 时代能力：用真实浏览器带登录态执行 Quora 发帖/回复、Reddit、Brevo 工作流。**覆盖 2026-10-26 的 R6 禁令**。 | W11 社区、W12 询盘、W10 外链从「半自动」转为可自动；但不可逆动作仍需逐次确认。见 `00-takeover/BROWSER-CAPABILITY.md` |
| D55 | **停摆根因是额度耗尽** | 2026-11-01 运营停摆不是主动停，是 Kimi 额度用完。 | 重启排期必须按额度预算设计；支持把 20 档/周降到 ~10 档/周（见 `07-optimization`）。 |
| D56 | **Always Use HTTPS 已开启** | 用 Cloudflare API token 把 zone `anaricharge.com` 的 `always_use_https` 由 off 改为 on；实测 `http://` 已 301。 | 修掉全站明文 HTTP 重复内容；GSC 里 35 个 http 页面行预计 2–8 周自然收口。 |
| D57 | **改 title/meta 走 seo/ 分支** | 3 页 title/meta 修复已提交到分支 `seo/ctr-title-meta-20261107`（commit `e038534`）并推送，等 PR + Gatekeeper 自动合并。 | 印证 Gatekeeper 流程可用；后续内容改动照此办理。 |
