# S1 · 询盘增长启动包（inquiry-growth-launch）

> 来源：`AI营销团队增强报告-v3-136技能.md:278-286` 组合 1（icp → channel → community → landing → outbound → pipeline），按本工作区流程落地为 W 系列编排。
> 目标：把「0 询盘」的站，用「精准客群 + 已有渠道 + 可追踪转化」在 2 周内产生首批可跟进线索，而不是等 SEO。

## 启动前置（P0，缺一即降级）

| 项 | 判据 | 卡点 |
|---|---|---|
| GSC / GA4 / GTM | 已配置且 generate_lead 事件在线 | G4（用户后台） |
| OpenSEO | 可拉数（credits > 0） | G17 |
| 产品上下文 | `product-marketing.md` 已填（ICP/痛点/竞品/目标线索数） | 用户 30 分钟（`手动配置清单.md:11-26`） |
| site 镜像 | `06-site/anari-new-site` 已同步 origin/main（线上 119 URL） | site-engineer |
| 转化链路 | D1/Brevo 链路可用（W12 日检过） | G5 |

## 编排（固定顺序）

### Step 1 · ICP 与客群定义（0.5 天）

- 调用：`cm-icp-research`、`customer-research`（按 `02-skills/_MERGE-MAP.md` 映射）。
- 输入：`product-marketing.md`、`$SITE/ops/product-marketing.md`、22 国案例、4 客群页（cpo / fleet / epc / energy-real-estate）。
- 执行：读 `W8` 步骤 3.2/3.3 的客群口径；输出 ICP 卡（行业/角色/痛点/触发事件/搜索词/预算区间）。
- 产出：`$D/step-1-icp.md`（4 客群 × 6 字段）。
- 验收：每个客群有「他们在哪问问题 + 问什么词 + 谁决策」三行；无编造。

### Step 2 · 渠道与社区发现（0.5 天）

- 调用：`sa-channel-discovery`、`sa-community-discovery`、`seo-competitor-gap-analysis`。
- 参照：`W14`（竞品渠道打法：EVB 展会/PR、Grasen 市场平台）+ `anari-b2b-channels.md`（T1/T2 机构渠道）。
- 产出：`$D/step-2-channels.md`：渠道 × 客群 × 内容形态 × 预计线索周期；社区清单（Quora/Reddit/行业论坛/协会）。
- 验收：≥8 个渠道，每个有可执行入口（URL/账户/流程），标注免费/付费（付费默认暂缓）。

### Step 3 · 落地页与内容资产（1 天）

- 复用：`W6`（新文五件套）+ `W20`（存量页转化改造）+ `cm-landing-page-optimizer`、`cm-cro-auditor`、`lead-magnets`。
- 输入：GSC 高展示页、`/inquiry` 三语页、工具页（/tools/charging-station-roi 等）。
- 执行：选 1 个客群做首轮（先 `cpo-entrepreneurs` 模式，参照 10-26/27 四页重构手法）+ 1 个 lead magnet（可行性清单/ROI 模板）。
- 门禁：走 W17 PR + W18 事实门 + W21 发布后验收。
- 产出：`$D/step-3-pages.md`（改了哪页/为什么/预期 CTR 或线索路径）。
- 验收：改动上线 200、CTA 指向 `/inquiry` 或 `/journey/segment?segment=`、有 schema。

### Step 4 · 社区首发（每日，1 周）

- 复用：`W11`（Quora 1–2 答/日；Reddit 仅备稿）。
- 输入：Step 3 的新页 + 素材包。
- 产出：`$D/step-4-community.md`（发布记录 + permalink 三证）。
- 验收：Quora 发布成功率 ≥70%，带链接 ≤3/周，披露句齐全。

### Step 5 · 外联启动（每周二/五）

- 复用：`W10`（弹药 + 模板 + 第 4/10 天跟进）。
- 输入：Step 1 ICP、Step 3 数据页、`backlinks-log.md` 台账副本。
- 卡点：**G1 用户手动发信**（sales@anarienergy.com）。
- 产出：`$D/step-5-outreach.md`（本周目标 10 家 + pitch 全文 + 用户发信清单）。
- 验收：≤10 家/周、模板定制完成、用户可复制即发。

### Step 6 · 漏斗与归因（持续）

- 复用：`W12`（每日 D1/GA4）+ `W2` 漏斗周报口径（`ops/attribution-model.md:184-200`）。
- 产出：`$D/step-6-funnel.md`：询盘数（D1/Brevo）、来源线（D1 attr_first）、转化断点。
- 验收：每条询盘可归到「落地页 + 来源线」；无归因的标「归因未知」。

## 套件级验收（2 周后）

- [ ] 首批 ≥3 条可跟进线索（D1 `form_type=inquiry` 且非测试）。
- [ ] 至少 1 个客群落地页改造上线并有 CTA 点击数据。
- [ ] Quora 带链接回答 ≥4 条（3/周上限内），有 permalink 证据。
- [ ] 外联首批 ≥10 封已由用户发出、≥1 个跟进节点到期并处理。
- [ ] 漏斗报告能回答「哪篇内容带来几条询盘」。

## 时间与卡点

| 阶段 | 时长 | 卡点 |
|---|---|---|
| Step 1–2 | 1 天 | G9（客群优先级需拍板） |
| Step 3 | 1 天 | G2/G14（改版提案审批） |
| Step 4 | 1 周（并行） | G6/G15（账号/养号） |
| Step 5 | 1 周（并行） | **G1**（用户发信） |
| Step 6 | 持续 | G5（Brevo 核对） |

**总时长：3–5 天启动，2 周见首批线索；业务上限取决于 GSC 曝光基数（28 天 27 点击时，纯 SEO 不可能快，必须靠社区+外联先起量）。**

## 失败处理

| 失败 | 处置 |
|---|---|
| P0 前置缺失（GA4 未标关键事件等） | 套件降级：只做 Step 1/2/4/5，转化数据延后；把缺口列用户 P0 |
| 无 OpenSEO credits | Step 2 用公开检索 + 站内 GSC；标「数据口径降级」 |
| 用户不发外联邮件 | 套件结果只统计社区与自然流量；连续 2 周未发 → 升级 lead |
| 改造被驳回 | 保留 Step 1/2 资产，改走内容线（W6）承接同一意图 |
