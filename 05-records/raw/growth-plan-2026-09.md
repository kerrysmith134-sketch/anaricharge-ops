# Anari Charge 增长排期计划 v1 — 2026-09-18

> 目标：把"等询盘"变成"可诊断的询盘流水线"。
> 本文按可排期颗粒度写：每项含 **交付物 / 完成定义(DoD) / 依赖 / 预估 / 执行方**。
> 执行方三种：**Code**（我可直接改并 push，Cloudflare 自动上线）、**GTM**（需 GTM-MRHHMP62 后台操作，我给配置规格）、**Biz**（需业务决策/账号/人力，我无法替代）。

---

## 现状核实（排期的事实基础）

在写计划前把代码翻了一遍，避免把"已有"当"待做"排进工期：

| 能力 | 现状 | 缺口 |
|---|---|---|
| GTM 容器 | ✅ GTM-MRHHMP62 全站 72 页已注入 | — |
| GA4 | ✅ G-MT63H5Q8EV，3 个关键事件已标记 | — |
| 主转化事件 | ⚠️ **仅 `generate_lead`**，只在 3 个 inquiry 页的 `?sent=1` 回跳时推 | 漏斗上游全无事件 |
| UTM 捕获 | ❌ 全站 `utm_` 出现 **0 次** | 来源不可归因 |
| journey 流程 | ⚠️ 7 步状态在 localStorage，**无任何事件** | 漏斗每层不可见 |
| 表单来源字段 | ⚠️ 已有 `journey_ref / journey_segment / journey_country`（JS 从 URL 注入） | 缺 source / medium / campaign / landing_page |
| 身份分流点击 | ❌ 首页四个身份 chip 无事件 | 无法验证 35/25/15/10 的预估占比 |
| WhatsApp 点击 | ❌ 无事件（注意：400 电话已全站下线，WhatsApp 是**唯一**非表单通道） | 次要转化不可测 |
| CRM | ❌ 不存在 | 线索无落库 |

**结论**：Block 0 的代码工作量比想象的小（我方可一次性完成），真正的关键路径在 **GTM 配置** 和 **CRM 选型** 上。

---

# Block 0 · 埋点体系与转化定义

> 依赖关系：Block 1/2/3/4/5 的**所有判断**都依赖本块。**这是唯一不可推迟的一块。**

## 0.1 事件层（Code，1 天）

统一 dataLayer 事件规范。所有事件带公共上下文 `page_language`（en/ru/es）、`page_path`。

| # | 事件名 | 触发点 | 关键参数 | 页面 |
|---|---|---|---|---|
| E1 | `segment_select` | 首页身份 chip 点击 | `segment` = engineering-contractor / fleet / energy-real-estate / cpo-entrepreneur | `/` |
| E2 | `journey_start` | 进入 `/journey/segment` 且已有答案 | `segment` | journey |
| E3 | `journey_step` | 每个 journey 步骤完成并前进 | `step` = 1..7, `step_name` | journey 7 页 |
| E4 | `journey_complete` | blueprint 页生成方案（含编号 AC-YYYY-…） | `segment`, `country` | `/journey/blueprint` |
| E5 | `inquiry_view` | `/inquiry` 页面可见（含 RU/ES） | `referrer_path`（站内来源页） | inquiry ×3 |
| E6 | `generate_lead` | **已存在**，本次补参数 | + `source/medium/campaign`, `segment`, `has_journey`, `form_name` | inquiry ×3 |
| E7 | `whatsapp_click` | 任一 `wa.me` 链接点击 | `location` = footer / contact-bar / inquiry-card / sticky | 全站 |
| E8 | `checklist_request` | 首页 "Email me the checklist" 提交成功 | — | `/` |
| E9 | `case_to_inquiry` | 案例页 CTA 点击进入 inquiry | `case` = jordan / romania / cambodia | cases ×4 |
| E10 | `market_to_inquiry` | 市场页 CTA 点击进入 inquiry | `market` = georgia / kazakhstan / nepal / kenya | markets ×5 |
| E11 | `tool_complete` | 工具页产生结果（ROI / BESS TCO / 选型 / TCO） | `tool` | tools ×4 |

**DoD**：11 个事件在 GTM Preview 里逐个可见，参数值正确；不产生重复触发。
**执行方**：Code（事件推送）+ GTM（触发器/变量）。

## 0.2 来源归因（Code，0.5 天）

首次落地时把 `utm_source / utm_medium / utm_campaign / utm_content` + `document.referrer` + 落地路径写入 `sessionStorage`（会话内首次为准，不被后续跳转覆盖），提交表单时作为隐藏字段一并送出。

统一口径（**这条必须业务拍板，否则数据永远对不上**）：

| 来源 | 判定规则 | 归入 |
|---|---|---|
| 挖矿行动回访 | `utm_source=outbound` | 流量线 A |
| anariev.com 反向导流 | `utm_source=anariev` 或 referrer 含 anariev.com | 流量线 B |
| 自然搜索 / AI 引用 | `utm_medium=organic` 或 referrer 为搜索引擎/`chatgpt.com`/`perplexity.ai` | 流量线 C |
| 直访 | 无 utm 且无 referrer | direct |

**DoD**：Web3Forms 收到的邮件里能看到 4 个 UTM + 来源线 + 落地页。
**依赖**：0.1 的公共上下文。

## 0.3 CRM 落库（Biz 决策 + Code 对接，3–5 天）

- **Biz**：选定 CRM（Attio / HubSpot / 其他），确认字段映射；提供 API key 或 webhook 地址
- **Code**：Web3Forms 目前是"邮件投递"，无 API 回调。方案二选一，需业务定：
  - **A（快）**：Web3Forms 保持，另加一个隐藏 post 到 CRM 的 webhook（Zapier/Make/n8n 中转）——1 天
  - **B（稳）**：表单直改 `fetch` 到自建端点（Cloudflare Worker），同时写 CRM + 发邮件——2–3 天
- **CRM 必填字段**：`来源线`、`utm_source/medium/campaign`、`落地页`、`segment`、`journey_ref`、`语言`、`国家`、`N-SDR 评分`、`响应时长`

**DoD（你的原话，照抄）**：两周内，任何一条 inquiry 记录，能在 CRM 里回答"这个人从哪来的、走了哪条路径、说了哪种语言"，不用问任何人。

## 0.4 验收与回归（Code，0.5 天）

- 用 GTM Preview + 真实提交做一次端到端联调（含 RU/ES 与 WhatsApp）
- 把事件规范写进 `site/TEMPLATE.md`，新建页面必须埋
- 加一条 `validate.js` 检查：新页面若含 inquiry 表单，必须有来源隐藏字段

**Block 0 总工期：Code 2 天 + GTM 0.5 天 + Biz 决策（CRM 选型）2–3 天。关键路径 = CRM 决策。**

---

# Block 1 · 流量来源（三条线并行导流）

## 1a 挖矿行动导流（**本周即可跑，不依赖 SEO**）

| # | 任务 | 交付物 / DoD | 依赖 | 预估 | 执行 |
|---|---|---|---|---|---|
| 1a.1 | 5000 联系人按国家/层级打标 | 一张映射表：联系人分层 → 目标页 | — | 0.5d | Biz |
| 1a.2 | 为每个国家/层级生成带 UTM 的落地链接 | 链接表（`utm_source=outbound&utm_medium=email&utm_campaign=<batch>`） | 0.1 | 0.5d | Code |
| 1a.3 | 按分层写 3 套外联邮件（不是 1 套群发） | 中东→约旦案例；CIS→哈萨克/俄罗斯页；非洲→肯尼亚/尼泊尔页 | 1a.1 | 1d | Biz |
| 1a.4 | 首批发送 + 打开/点击/询盘追踪 | 看板列：发送数/打开/点击/inquiry_submit | 0.2, 1a.3 | 0.5d | Biz |

**要点**：单条链接必须指向**对应案例或国家页**，不能都指首页——指向相关页的转化率差异通常数倍计。

## 1b anariev.com 反向导流（最低成本，现在几乎为 0）

| # | 任务 | 交付物 / DoD | 依赖 | 预估 | 执行 |
|---|---|---|---|---|---|
| 1b.1 | 产品站加"如何落地"导流组件 | 每个产品页在规格表下方加模块：*Need this delivered and operated? → 对应的 anaricharge 模块页* | — | 1d | Code（跨站，需 anariev 仓库权限） |
| 1b.2 | 双向互链锚文本改成描述性 | 现在页脚一行小字"sister site"；改为语境化锚文本 | — | 0.5d | Code |
| 1b.3 | 给 anariev 加 UTM 出站参数 | `?utm_source=anariev&utm_medium=referral` | 0.2 | 0.25d | Code |
| 1b.4 | 反向导流的 schema 互认 | 两站 Organization `sameAs` 互指（anaricharge 侧已完成） | — | 0.25d | Code |

## 1c SEO / GEO（中期，但现在开始）

| # | 任务 | 交付物 / DoD | 预估 | 执行 |
|---|---|---|---|---|
| 1c.1 | 结构化数据补全 | ✅ **已完成**（Organization/Product/FAQPage/BreadcrumbList/Article，204 个 ld+json 块全合法） | — | — |
| 1c.2 | 22 国页面 + 案例页的 Service/CaseStudy 语义补强 | 给市场页加 `Service`+`areaServed`，案例页加 `CaseStudy` | 0.5d | Code |
| 1c.3 | GEO prompt 追踪表 | 固定 8 个高意图 prompt，每周手工问 ChatGPT/Perplexity/Gemini，记录是否引用 + 引用 URL | 0.5d/周 | Biz |
| 1c.4 | AI 引用的第三方阵地 | Wikidata 条目、行业目录、贸易媒体投稿（Semrush 工业品类研究：AI 引用集中在目录/媒体，而非厂商自有域名） | 3–5d | Biz |

**1c.3 prompt 基线（建议）**：turnkey EV charging provider Jordan / EV charging station EPC Kazakhstan / how to start a charging business Kenya / AI site selection EV charging / AFIR compliant charger supplier / OCPP 2.0.1 CSMS for CPO / BESS peak shaving EV hub / charging station ROI calculator emerging markets

---

# Block 2 · 站内转化路径（先诊断，再优化）

> **前置**：Block 0.1 上线满 2 周才可开始。在此之前任何优化都是凭感觉。

| # | 任务 | 交付物 | 依赖 | 预估 | 执行 |
|---|---|---|---|---|---|
| 2.1 | 拉漏斗基线 | 一张表：`segment_select → journey_start → journey_step1..7 → journey_complete → inquiry_view → inquiry_submit` 各层量与转化率 | 0.1 + 14 天数据 | 0.5d | Biz |
| 2.2 | **分流占比对照** | 用真实 `segment_select` 分布对照 35/25/15/10 预估；偏差>10pp 则调整首页呈现顺序 | 2.1 | 0.5d | Biz |
| 2.3 | 判定 journey 是否是障碍 | 若 `journey_complete/journey_start < 40%` 且 `case_to_inquiry` 相对高 → 把"直接联系"提为主入口，journey 降级为可选 | 2.1 | 决策 | Biz |
| 2.4 | 案例页 CTA A/B | 每案例页两版 CTA（"Read more case" vs "Get a scoped proposal for your market"），跑 2 周 | 0.1 | 0.5d | Code+Biz |
| 2.5 | 表单字段精简测试 | 现行 6 字段 → 3 字段（国家 + 身份 + 一句话需求），观察完成率与线索质量 | 2.1 | 0.5d | Code |
| 2.6 | 移动端路径复核 | 手机端（目标市场主要设备）从落地到提交的完整点击链截图复核 | — | 0.5d | Code |

**注意 2.5 的反向风险**：字段减少会提高提交量但可能降低可跟进度。必须同时看"提交数"和"SDR 判定为可跟进的占比"两个指标，只看前者会误判。

---

# Block 3 · 询盘质检与分发（N-SDR 不能是黑箱）

| # | 任务 | 交付物 / DoD | 依赖 | 预估 | 执行 |
|---|---|---|---|---|---|
| 3.1 | 定义 N-SDR 打分维度与权重 | 一页文档：市场层级 / 身份画像 / 需求描述关键词 / 预算信号，各占多少、如何计算 | — | 1d | Biz |
| 3.2 | 打分可解释 | 每条线索在 CRM 显示"为什么是高分/低分"的因子明细，不接受"AI 说优先" | 3.1 | 1d | Code |
| 3.3 | 响应 SLA 定义 | 高分：X 小时；中分：Y 小时；低分：Z 天。写进 CRM 自动提醒 | 3.1 | 0.5d | Biz |
| 3.4 | **人工复核机制** | 每周抽 N% 被判低优先级的线索人工复核，记录误判率 | 3.2 | 0.5d/周 | Biz |
| 3.5 | 反哺 | 把误判样本回灌打分规则（这是这套机制唯一的价值所在） | 3.4 | 0.5d/月 | Biz |

**为什么 3.4 是必须的**：网站对外声称 N-SDR"线索效率提升 5 倍"。一个自动打分的黑箱如果不做人工抽查，它的误判成本会直接变成丢失的询盘，而且没人会发现。

---

# Block 4 · 内容节奏（挂到转化，不是纯发布量）

| # | 任务 | 交付物 / DoD | 依赖 | 预估 | 执行 |
|---|---|---|---|---|---|
| 4.1 | 内容分配改为按 outbound 优先级 | 每周内容计划以"本周 outbound 重点触达市场"为第一排序，而非平均撒 | 1a.1 | 0.25d/周 | Biz |
| 4.2 | 新市场页当周接导流 | 新页上线当周即接入 1a 的 UTM 链接测试，不留空窗 | 4.1 | 0.25d/周 | Code+Biz |
| 4.3 | **低效页面修复优先于新增** | 每周复盘 `case_to_inquiry`/`market_to_inquiry` 点击率最低的页面，优先补 ROI 数据/具体数字，而不是继续堆新页 | 2.1 | 0.5d/周 | Biz |
| 4.4 | 案例页补硬数据 | 补投运月份、台数、利用率/可用率、客户原话——**目前三个案例全部匿名无日期无金额** | 素材 | 3d | Biz |

**4.4 是内容块里唯一的高杠杆项**。案例页缺硬数据既是转化问题也是 GEO 问题（AI 引擎引用的是可引用的具体数字）。

---

# Block 5 · 运营节奏（固定周期，不发明新流程）

| 周期 | 动作 | 产出 | 时长 |
|---|---|---|---|
| **每周一 9:14** | 看板自动刷新（已启用）+ 漏斗各层量与转化率 | 周报：漏斗 + outbound 导流 + GEO 追踪表 | 1h |
| **每周** | 内容分配按 4.1 | 下周内容计划 | 0.5h |
| **每两周** | N-SDR 低分线索抽查（3.4）+ **只落地一项**站内优化 | 抽查记录 + 一项改动上线 | 2h |
| **每月** | 三条流量线对 `inquiry_submit` 的贡献占比对比 | 资源倾斜决策 | 1h |

**每两周只改一项**是刻意的：同时改多处会导致无法归因是哪个改动起效，这是 A/B 测试最基本的纪律。

---

# Block 6 · 里程碑（不编数字）

你说得对，现在没有流量基线，编出来的目标没有意义。所以里程碑定义为**获得基线的时点**：

| 里程碑 | 时间 | 判定标准 |
|---|---|---|
| **M1 埋点可用** | 第 1 周末 | 11 个事件在 GTM Preview 可见；真实提交一次全链路通；RU/ES 与 WhatsApp 已验证 |
| **M2 归因可用** | 第 1 周末 | 表单邮件里能看到 UTM + 来源线 + 落地页 |
| **M3 CRM 落库** | 第 2 周末 | 任一 inquiry 能在 CRM 回答"从哪来/走哪条路/哪种语言" |
| **M4 **基线冻结** | 第 3 周末 | 拿到：周 `journey_start` 数、周 `inquiry_submit` 数、三条流量线各自转化率。**此日之前不定 30/60/90 目标** |
| **M5 首次资源决策** | 第 4 周末 | 基于 M4 基线，决定下月资源在三条线间的配比 |

**M4 之后**才制定 30/60/90 天目标——届时目标才有分母。

---

## 排期甘特（4 周）

```
              W1            W2            W3            W4
Block 0  埋点Code ███
         来源归因   ██
         GTM配置     ██
         CRM选型 ★  ███         (关键路径)
         CRM对接      ███████
Block 1a 导流链接  ██
         外联邮件    ████
         首批发送      ████████████████
Block 1b 反向导流      ████
Block 1c GEO追踪   ████████████████████████ (持续)
Block 2  漏斗基线                  ████
         优化决策                    ████
Block 3  打分规则         ████
         复核机制             ████████████████ (持续)
Block 4  内容节奏   ████████████████████████ (持续)
Block 5  周复盘     ████████████████████████ (持续)
里程碑   M1 M2      M3        M4        M5
```

**唯一的关键路径**：CRM 选型（Biz）→ CRM 对接 → M3。其余全部可并行。
**如果 CRM 决策卡住**：先用方案 A（webhook 中转，1 天）+ 一张 Google Sheet 兜底，不要让它挡住 Block 1a——1a 本周就能出询盘，不该被 CRM 阻塞。

---

## 挂起项（需业务提供，无法排期）

| 项 | 阻塞什么 | 谁能解 |
|---|---|---|
| 真实项目摄影（站点全景/柜体特写/施工中/调试中/司机充电 五类） | 视觉可信度、案例页 4.4 | 下次现场出差 |
| 案例页硬数据（投运月份/台数/利用率/客户原话） | 4.4、GEO 引用率 | 业务/客户授权 |
| 两封具名推荐信 | 采购尽调 | 业务 |
| 定价带宽（可行性包/单站/网络三档） | 转化率与线索质量 | 业务 |
| 本地电话号码（现全站仅一个 WhatsApp） | WhatsApp 之外的第二通道 | 业务 |
| 日历预约工具 | 响应速度（数据显示提交后 1 分钟内响应成单率约 80%，隔天掉到约 40%） | 业务 |

---

*本文基于 2026-09-18 代码实测状态编写。执行过程中若某项前提变化（尤其 Block 0 的"现状"表），需回来修订依赖链。*

---

## 实施记录 · 2026-09-18（Block 0 代码部分已落地）

### 已完成（Code，可直接上线）
- **新增 `site/assets/js/track.js`**：统一埋点与来源归因单文件，全站 72 页已注入
  - 9 个事件：`segment_select` / `journey_start` / `journey_step` / `journey_complete` /
    `inquiry_view` / `whatsapp_click` / `checklist_request` / `case_to_inquiry` / `market_to_inquiry`
  - 来源归因：会话首次落地抓 UTM + referrer，写入 sessionStorage，**不被站内跳转覆盖**；
    按业务口径自动分三条流量线（A-outbound / B-referral / C-organic / direct）
  - 询盘表单提交前自动注入隐藏字段：`attr_line / attr_source / attr_medium /
    attr_campaign / attr_referrer / attr_landing / page_language`
  - 与既有表单的 `journey_ref / journey_segment / journey_country` 并存，不冲突
- **修掉一个真实转化 bug**：首页身份 chip 选完点 Continue 是裸链 `/journey/segment`，
  **用户刚选的画像被丢掉**。现在继续链接带 `?segment=<slug>`，journey 第一步自动预选，
  且 slug 契约与 `inquiry.html` 的 `SEGMENTS` 映射完全一致（已校验）
- **`generate_lead` 补参数**：`segment` + `has_journey`（三语 inquiry 页）
- 事件规范已并入 `scripts/site-fixes.js` 的注入步骤（幂等），新建页面自动带上

### 静态校验结果
| 检查 | 结果 |
|---|---|
| `track.js` 语法 | ✅ |
| 依赖的 5 个选择器在真实 DOM 中存在 | ✅ 5/5 |
| slug 契约（发出 ↔ 消费） | ✅ 完全一致 |
| 全站覆盖 | ✅ 72 / 72 页 |
| validate（5 项契约） | ✅ 全绿 |

### 尚未验证 / 未完成（诚实标注）
- **无头浏览器端到端点击测试未跑通**：本机 Chrome headless 在嵌套 iframe 场景反复挂死，
  改为静态校验。上线后请人工用 **GTM Preview** 点一遍：首页身份 chip → journey → 询盘提交，
  确认 9 个事件可见且参数正确。
- **GTM 侧未配置**（Block 0.1 的后半段，需 GTM-MRHHMP62 后台）：
  目前 dataLayer 有事件，但 GTM 里还没有对应的触发器/变量把它们转发给 GA4。
  在配置之前，GA4 里只能看到 `generate_lead`。**这是 Block 0 的当前唯一阻塞点。**
- **CRM 未对接**（Block 0.3，需业务选型）。
- `tool_complete`（E11）未做：4 个工具页的结果产生时机各不相同，需要逐个接，
  建议放在 CRM 对接之后。
