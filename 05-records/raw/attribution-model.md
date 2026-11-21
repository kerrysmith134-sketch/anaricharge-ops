# Anari 网站 · 归因模型设计 — 「网站行为 → CRM 商机」

> 版本：v1（设计契约，待评审）· 2026-10
> 目标读者：后续开发 / 运营负责人。本文只定契约，不改代码。
> 现状描述均已对照仓库代码核实（track.js v1、leads-worker.js v2、schema.sql、inquiry.html、privacy.md/html、gtm-event-setup.md、hubspot-integration.md、growth-plan-2026-09.md）。
> 业务问题（一句话）：**哪篇内容 / 哪个渠道 / 哪次会话，最终带来了一条真实询盘。**

---

## 0. 现状核实（事实基础）

| 项 | 代码核实结论 | 文件 |
|---|---|---|
| 事件总线 | 全部走 `window.dataLayer`，GTM-MRHHMP62 → GA4（G-MT63H5Q8EV）；事件含 `whatsapp_click / case_to_inquiry / market_to_inquiry / inquiry_view / segment_select / journey_start / journey_step / journey_complete / checklist_request`，以及询盘成功页内联推送的 `generate_lead` | `site/assets/js/track.js`、`site/inquiry.html:556` |
| 来源捕获 | 会话首次落地抓取 `utm_source/medium/campaign/content` + referrer + landing，写入 **sessionStorage** `anari_attr_v1`；归并口径 `line` = A-outbound / B-referral / C-organic / direct / other；**未抓 `utm_term`**；跨会话不保留（关标签页即丢） | `track.js:30-66` |
| 询盘表单归因 | 提交前注入隐藏字段 `attr_line / attr_source / attr_medium / attr_campaign / attr_referrer / attr_landing / page_language`，随 Web3Forms 邮件送达——**邮件通道的归因已通** | `track.js:186-204` |
| generate_lead 参数 | 成功页只推 `form_name / page_language / segment / has_journey`，**未带归因参数**（growth-plan E6 规划了 source/medium/campaign，实际未实现） | `inquiry.html:553-559` |
| 归因中继 | track.js 尾部中继模块 `ENDPOINT = ""` / `KEY = ""`，惰性不生效；且其 `fetch` 携带自定义头 `X-Anari-Key`，与 Worker v2 的 CORS（`Allow-Headers: Content-Type`，v2 靠 Origin 白名单 + 蜜罐 + IP 限流，**故意不要共享密钥**）不兼容——Phase 1 接线时必须去掉该自定义头，否则预检失败 | `track.js:287-310` vs `leads-worker.js:51-59` |
| Worker v2 | `POST /nurture`：D1 先落库（`submission_id` = 服务端 `crypto.randomUUID()`）→ consent=1 才外发 Brevo（3 次指数退避，失败置 `dead`）；幂等 = 邮箱+表单类型+10 分钟窗；限流 = IP 加盐散列 5 次/10 分钟；蜜罐 `email_address_check` | `workers/leads-worker.js` |
| D1 schema | `submissions(submission_id PK, email, form_type, payload JSON≤8000, consent, consent_ts, status, retry_count, last_error, ip_hash, user_agent, created_at, updated_at)` + 3 个索引。**无归因列、无身份列**；但原始提交 JSON 整体进 `payload`，前端多发的字段不会丢、只是不可查询 | `workers/schema.sql` |
| 成功页 beacon | `sendBeacon(text/plain)` → `api.anaricharge.com/nurture`，字段 = EMAIL/FIRSTNAME/COMPANY/COUNTRY/PRODUCT/PROJECT/consent/consent_ts/蜜罐——**不含 attr_* 归因字段**，这是当前 D1 侧归因断点 | `inquiry.html:564-596` |
| Journey 状态 | `localStorage["anari_journey_v1"]`（跨会话持久）；同意后的简报在 `sessionStorage["mc_journey_brief"]`，inquiry 页校验 `ref` 一致才采纳，摘要随 `journey_brief` 隐藏字段入表单 | `journey/journey.js`、`inquiry.html:423-469` |
| HubSpot | **workers/ 目录下没有 HubSpot 版 Worker 文件**；HubSpot 对接目前只是一份操作手册（11 个自定义联系人属性 + 私有应用令牌 + FIELD_MAP 契约），线索由 track.js 惰性中继转发。v2 Worker 已改为 Brevo 路线 | `ops/hubspot-integration.md` |
| 隐私政策 | 明确声明「This site sets **no cookies of its own**」；已披露 GA4/GTM cookie（`_ga`）、journey 答案存 localStorage、Web3Forms/Google/Cloudflare 三个处理方、询盘留存 24 个月、分析数据 14 个月 | `site/privacy.md`（与 privacy.html 同源） |

**关键推论：**
1. 「唯一不落 cookie」是硬约束——匿名身份只能用 localStorage/sessionStorage，不能引入第一方 cookie，否则与隐私政策直接冲突。
2. 归因数据已有两条通路：Web3Forms 邮件（已通）与 D1（断在 beacon 不带 attr）。Phase 1 的核心就是补上 D1 这条。
3. Worker v2 的 `payload` 原样存 JSON，意味着**前端先行扩字段、Worker 后补列**是安全的渐进路径（先存后查）。

---

## 1. 事件与身份模型

### 1.1 三级身份

| 标识 | 键 / 来源 | 存储 | 生命周期 | 用途 |
|---|---|---|---|---|
| `anon_id`（匿名访客 ID） | `localStorage["anari_vid_v1"]`，首次访问时 `crypto.randomUUID()` 生成 | 浏览器 localStorage | 持久，用户清浏览器数据即灭；不设主动过期 | 跨会话缝合：同一访客多次访问、多次提交归并为一人 |
| `session_id`（会话 ID） | `sessionStorage["anari_sid_v1"]`，会话首页生成 UUID | sessionStorage | 标签页关闭即灭（天然对齐 GA4 会话语义，无需自己实现 30 分钟超时） | 单次会话内的页面路径、Journey 步骤归并 |
| `submission_id`（提交 ID） | **改为前端生成**：表单提交瞬间 `crypto.randomUUID()`，随表单/beacon 字段送出；Worker 收到合法 UUID 即采用为主键，缺失才服务端生成（保持向后兼容） | D1 主键 | 永久 | 对账句柄：GA4 事件 ↔ D1 记录 ↔ CRM 联系人三方的唯一公共键 |

**为什么 submission_id 要前端生成**：当前成功页用 `sendBeacon`/`fetch(no-cors)`，**读不到响应**，服务端下发的 submission_id 回不到浏览器，无法写进 `generate_lead` 事件。前端生成后，同一个 ID 可以同时：(a) 进 D1 主键；(b) 作为 `generate_lead` 的事件参数进 GA4；(c) 进 Web3Forms 邮件隐藏字段；(d) 未来进 CRM 联系人属性。四方对齐，零额外接口。

**缝合点总览：**

```
anon_id ──┬── localStorage 持久，随每次提交进 D1
          └── 回答「这个询盘访客之前来过几次、第一次从哪来」
session_id ── sessionStorage，随提交进 D1 + 可作 GA4 事件参数
          └── 回答「这次会话里看了哪些页面、走了几步 Journey」
submission_id ── 提交瞬间生成，四处随行
          └── 回答「这条询盘 = 这封邮件 = D1 这行 = CRM 这个联系人」
```

**隐私政策一致性**：全部使用 localStorage/sessionStorage，不新增任何 cookie，privacy.md 第 90 行「This site sets no cookies of its own」继续成立（需按 §6 补一句 localStorage 用途披露）。

### 1.2 事件层

现有 10 个 dataLayer 事件不动。归因视角下只增补两类参数，不新增事件名：

- `generate_lead`：补 `submission_id / attr_line / attr_source / attr_medium / attr_campaign / attr_landing`（读取 sessionStorage 现有 `anari_attr_v1` 即可，零新增采集）。
- 全部事件：GTM 侧把 `session_id` 作为事件参数附加（可选，Phase 0 不做也不阻塞）。

---

## 2. 触点采集

### 2.1 采集内容

| 触点数据 | 采集点 | 现状 |
|---|---|---|
| UTM 五参数 `utm_source/medium/campaign/content/term` | 会话首次落地 | 已有四个，**缺 `utm_term`**，补上即可 |
| `referrer`（完整值） | 同上 | 已有 |
| `landing`（落地路径） | 同上 | 已有 |
| 流量线 `line`（A/B/C/direct/other 归并） | 同上 | 已有，口径见 growth-plan Block 0.2 |
| 内容消费路径 | 每次页面加载 append `{p: path, t: ts}` 到 `sessionStorage["anari_path_v1"]`，**上限 30 条**（防抖：同一 path 连续刷新只记一次） | 无，新增 |
| Journey 步骤 / 工具使用 | 已有 `journey_*` 事件 + `journey_ref/segment/country/brief` 隐藏字段 | 已有，无需重复采集 |

### 2.2 存储位置与留存

| 数据 | 位置 | 留存 |
|---|---|---|
| **first-touch 快照** `anari_first_v1` | localStorage，**只在访客首个非 direct 会话写入一次，永不覆盖** | 浏览器清数据为止；提交时随表单入 D1 后由 D1 长期留存 |
| **last-touch 快照**（现有 `anari_attr_v1`） | sessionStorage，会话内首次非 direct 落地写入 | 会话级 |
| 内容路径 `anari_path_v1` | sessionStorage，30 条滚动窗口 | 会话级 |
| 提交时的归因快照 | D1 `submissions` 新增列（见 §3.3） | 随询盘记录 24 个月（对齐现有询盘留存政策） |

**设计取舍**：内容路径只保留**会话内**（sessionStorage），不做跨会话全行为画像。理由：B2B 长周期里跨会话 stitching 的边际收益远低于其维护成本和隐私风险；跨会话维度的关键问题（「最早从哪来」）已由 first-touch 快照回答。

---

## 3. 归因规则

### 3.1 模型取舍

| 模型 | 结论 | 理由 |
|---|---|---|
| **first-touch** | ✅ 采用（营销投入决策的主口径） | B2B 充电桩决策链数月、多会话；团队要回答的是「哪篇内容/哪个渠道**最早**把这个人带来的」——这正是内容预算该投向哪里的依据 |
| **last-touch（last-non-direct）** | ✅ 采用（转化优化的副口径） | 回答「临门一脚是什么页面/渠道促成的提交」，指导 CTA 与落地页优化；现有 `anari_attr_v1` 语义天然就是它 |
| linear / position-based | ❌ 不采用 | 需要跨会话完整路径 + 稳定身份缝合 + 专门的计算与解释成本；对 0 预算小团队，两张并列的快照（first + last）已覆盖 90% 的决策场景，且任何人看一眼就懂 |

**结论一句话：双快照制——每条询盘同时携带 first-touch 与 last-touch 两份触点快照入 D1；营销投入按 first-touch 归因，转化优化按 last-touch 归因，不做多触点分摊。**

### 3.2 口径细则（沿用并钉死现有口径）

- 流量线归并沿用 `track.js:42-48` 的四线口径（A-outbound / B-referral / C-organic / direct / other），与 growth-plan Block 0.2 一致，不另起炉灶。
- direct 不覆盖已有触点（现有「非直访才固化」逻辑保留）：用户先搜到博客、三天后输网址直接进来提交，first 与 last 都仍是那条自然搜索记录——这是 last-**non-direct** 的标准做法。
- AI 引用流量（chatgpt.com / perplexity.ai 等 referrer）已归入 C-organic 线，报表中可按 referrer 细分单独呈现。

### 3.3 D1 schema 衔接（扩列 ALTER）

`payload` 列已能兜住全部新增字段（先存后查），但报表需要可查询的列。Phase 1 执行：

```sql
-- workers/schema.sql 追加（D1 为 SQLite，支持 ADD COLUMN；存量行新列为 NULL，视为「归因未知」）
ALTER TABLE submissions ADD COLUMN anon_id      TEXT;  -- 匿名访客 ID（前端生成）
ALTER TABLE submissions ADD COLUMN session_id   TEXT;  -- 会话 ID（前端生成）
ALTER TABLE submissions ADD COLUMN attr_first   TEXT;  -- first-touch 快照 JSON：{ts,utm_source,utm_medium,utm_campaign,utm_content,utm_term,referrer,landing,line}
ALTER TABLE submissions ADD COLUMN attr_last    TEXT;  -- last-touch 快照 JSON，同构
ALTER TABLE submissions ADD COLUMN content_path TEXT;  -- 本会话内容路径 JSON 数组（≤30 条 path）

-- 周报表口径常用查询
CREATE INDEX IF NOT EXISTS idx_submissions_created ON submissions (created_at);
```

配套 Worker 改动（Phase 1，仅设计、本文不动代码）：
- `normalize()` 增读 `anon_id / session_id / attr_first / attr_last / content_path / submission_id`；
- 幂等逻辑增加一层：收到已存在的 `submission_id` 直接返回首次记录（防 sendBeacon 与 fetch 双发、防重试重放）；
- INSERT 语句带上 5 个新列；submission_id 优先采用前端值（校验 UUID 格式，非法则服务端生成）。

### 3.4 前端提交契约（Phase 1 目标态）

`POST /nurture`（beacon / fetch text/plain）body 在现有字段上新增：

```json
{
  "EMAIL": "...", "FIRSTNAME": "...", "...": "现有字段不变",
  "submission_id": "前端 UUID",
  "anon_id": "localStorage UUID",
  "session_id": "sessionStorage UUID",
  "attr_first": {"ts":"...","utm_source":"...","line":"C-organic","landing":"/blog/..."},
  "attr_last":  {"同上结构"},
  "content_path": ["/markets/kenya","/cases/jordan-160kw","/journey/roi","/inquiry"]
}
```

---

## 4. CRM 对接面

三条通道各自携带的归因字段（契约表）：

### 4.1 Web3Forms（邮件，主通道，零改动）

- 已有隐藏字段：`attr_line / attr_source / attr_medium / attr_campaign / attr_referrer / attr_landing / page_language / journey_ref / journey_segment / journey_country / journey_brief`。
- Phase 1 增量：`submission_id` 一个隐藏字段（让邮件可对账 D1）。其余 attr 字段已在，无需动。

### 4.2 Brevo（nurture，经 Worker v2）

- `brevoUpsertContact()` 的 `attributes` 当前只有 FIRSTNAME/COMPANY/COUNTRY/PRODUCT/PROJECT。
- Phase 1 增量映射（Brevo 联系人属性需先建）：`ANARI_SUBMISSION_ID / ANARI_ANON_ID / ANARI_ATTR_LINE / ANARI_UTM_SOURCE / ANARI_UTM_MEDIUM / ANARI_UTM_CAMPAIGN / ANARI_LANDING`（值取 last-touch，营销序列语境下「最近为什么回来」比 first 更相关；first 快照留在 D1 查）。
- 合规门禁不变：consent=1 才外发。

### 4.3 HubSpot（未来，按 ops/hubspot-integration.md 契约）

- 手册已定义 11 个联系人属性（`anari_attr_line / anari_utm_source / anari_utm_medium / anari_utm_campaign / anari_referrer / anari_landing / anari_journey_ref / anari_journey_segment / anari_journey_country / anari_message / anari_form_name`）。
- Phase 2 增补 3 个属性：`anari_submission_id`（对账键）、`anari_first_touch`（JSON 或拆 4 列，决定权交给实施时的报表需求）、`anari_anon_id`。
- 接线注意：track.js 尾部中继模块的 `X-Anari-Key` 自定义头与 v2 Worker CORS 不兼容；Phase 2 若启用中继，要么 Worker 的 `Access-Control-Allow-Headers` 加 `X-Anari-Key` 并恢复密钥校验，要么前端去掉该头沿用 Origin+蜜罐+限流防护。**二选一，写进实施票。**
- HubSpot 版 Worker 目前不在 workers/ 目录（只有手册），若重启 HubSpot 路线，是在 v2 的 D1+Brevo 骨架上加一个 deliver 分支，不是另起 Worker。

---

## 5. 报表口径（周报「内容 → 询盘」）

### 5.1 各源能回答什么

| 数据源 | 能回答 | 不能回答 |
|---|---|---|
| GA4 | 各内容页流量与互动、Journey 漏斗每层转化、`case_to_inquiry`/`market_to_inquiry` 等意图事件量、`generate_lead` 总量与 segment 分布、渠道分组趋势 | **单条询盘的确定归属**（GA4 匿名聚合 + 24-48h 延迟 + 采样，不能也不该当对账源） |
| D1 `submissions` | **每一条询盘的 first/last 触点、内容路径、Journey ref、语言、提交时间**——「哪篇内容带来几条询盘」的唯一权威源 | 没提交就跑了的流量（那是 GA4 的事） |
| Web3Forms 邮件 | 人读的对账备份 | 统计 |

### 5.2 周报统计方法（钉死口径，避免每次重议）

1. **询盘归因主表**（D1 出）：
   ```sql
   SELECT json_extract(attr_first,'$.line')     AS first_line,
          json_extract(attr_first,'$.landing')  AS first_landing,
          json_extract(attr_last,'$.landing')   AS last_landing,
          COUNT(*) AS inquiries
   FROM submissions
   WHERE created_at >= date('now','-7 days') AND form_type='inquiry'
   GROUP BY 1,2,3 ORDER BY inquiries DESC;
   ```
   产出「首次来源线 × 首次落地页」的询盘计数；`attr_first IS NULL` 的旧数据统一归入「归因未知」并在报表注明。
2. **内容助攻榜**（GA4 出）：`case_to_inquiry` / `market_to_inquiry` / `journey_complete` 按 case/market/segment 分组计数——解释 D1 主表里 first_landing 相同但转化不同的「为什么」。
3. **口径断点披露**：plan.md 已记载 `generate_lead` / `checklist_request` 曾因虚增修正口径（c057999），周报应固定附一行「数据口径自 2026-09 下旬为真实提交口径」。

### 5.3 看板 widget 读哪个源

- **询盘归因 widget 读 D1**（经 Worker 只读端点或定时导出的 artifact JSON，不走 GA4）——理由是它是「真实业务结果」层。
- 流量/漏斗 widget 继续读 GA4/GSC（沿用 plan.md 既有 OpenSEO bridge → widget 管线）。
- 两源并置即可，**不做 widget 层的实时 join**；join 只发生在周报生成那一刻。

---

## 6. 隐私合规（与 privacy.html 逐条对齐）

| privacy 现有声明 | 本方案是否冲突 | 处置 |
|---|---|---|
| 「This site sets no cookies of its own」（§Cookies） | 不冲突——方案全用 localStorage/sessionStorage | §Cookies 补一句：*We also store an anonymous visitor ID and your browsing path on this site in your browser's localStorage/sessionStorage (not cookies) to understand which content led to your inquiry. Clearing site data removes them.* |
| §1 收集表单字段清单 | 新增「归因元数据随询盘收集」 | §1 增列：*the page you first arrived from, referral/UTM parameters, and the pages you viewed in that visit, attached to your inquiry* |
| §2 自动收集（GA4/GTM/Cloudflare 日志） | 新增 D1/Worker 存储 | 处理方清单的 Cloudflare 条目扩展为「hosting + inquiry relay (Cloudflare Worker) + inquiry database (Cloudflare D1)」；披露存 IP 的加盐散列与 UA（Worker v2 已在存，目前政策未提，**必须补**） |
| 处理方清单（Web3Forms/Google/Cloudflare） | 新增 Brevo | 补 Brevo（仅勾选同意后接收邮箱与订阅属性）——同时修正一处既有不一致：§「What we do NOT collect」写了 *No newsletter subscription list*，而 nurture 勾选制已上线，应改为「仅在你明确勾选后进入产品资讯序列，可随时退订」 |
| 留存（询盘 24 个月 / 分析 14 个月） | 对齐 | D1 submissions 行（含归因快照）沿用询盘 24 个月口径，写进政策；浏览器侧 ID 随用户清数据即灭 |
| 合法基础表（GDPR Art. 6） | 新增一行 | *Measuring which content and channels lead to inquiries* → attribution metadata → Legitimate interest (Art. 6(1)(f))；营销序列一行已存在（Consent 6(1)(a)），不变 |
| 删除权 | 可执行 | D1 按邮箱/anon_id 删除 = 一条 SQL；流程写进 worker-deploy.md 附录即可，无需新系统 |

**需要新增的声明条款汇总**（交给文案/法务一次性改 privacy.html + privacy.md，并更新 Last verified 日期）：① localStorage 匿名 ID 与路径；② 询盘附归因元数据；③ Cloudflare Worker/D1 处理与存储（含 IP 散列、UA）；④ Brevo 为勾选同意的处理方；⑤ 修正 newsletter 旧表述。

---

## 7. 实施分期

### Phase 0 — 纯 GA4/GTM（零代码、零新存储）

| 项 | 内容 | 前置依赖 | 工作量 |
|---|---|---|---|
| GTM/GA4 体检 | 按 `ops/gtm-event-setup.md` 第 4 步核对 9 个自定义维度注册齐全；`journey_complete` 标为关键事件 | GTM 后台权限 | 0.5 天 |
| 渠道分组与探索报表 | GA4 建「内容 → generate_lead」探索模板（landing page × 默认渠道组 × segment） | 上一步 | 0.5 天 |
| UTM 命名规范 | 一页纸规范（source/medium/campaign 取值表），外联与内容团队共用 | 无 | 0.5 天 |
| 周报 v0 | 数据源 = Web3Forms 邮件里的 attr_* 隐藏字段（人工/半自动汇总）+ GA4 渠道趋势 | 邮件通道归因已通（现状） | 持续 1 小时/周 |

**Phase 0 出口标准**：每周能说出「本周询盘的 first 来源分布」（来自邮件隐藏字段人工统计），GA4 漏斗报表可看。

### Phase 1 — Worker v2 部署后 D1 缝合（核心期）

| 项 | 内容 | 前置依赖 | 工作量 |
|---|---|---|---|
| Worker v2 上线 | 按 `ops/worker-deploy.md` 人工部署（wrangler + D1 建库 + secrets） | **Cloudflare 账号操作（人工，当前唯一硬阻塞）** | 0.5 天（人工） |
| D1 扩列 | 执行 §3.3 的 ALTER 语句 | Worker 上线 | 0.5 小时 |
| track.js / inquiry.html 改造 | ① `anari_vid_v1`/`anari_sid_v1` 生成；② `anari_first_v1` first-touch 持久化 + 补 utm_term；③ `anari_path_v1` 内容路径；④ 提交瞬间生成 submission_id；⑤ beacon body 带齐 §3.4 字段；⑥ `generate_lead` 补归因参数与 submission_id；⑦ 中继模块去 `X-Anari-Key`（或按 §4.3 决策） | 本文档评审通过 | 1.5–2 天 |
| Worker 改造 | normalize 扩字段 + submission_id 幂等层 + INSERT 新列 + Brevo 属性映射（§4.2） | 同上 | 0.5–1 天 |
| 隐私政策更新 | §6 五条新条款三语同步（en/ru/es 页面） | 法务/业务过目 | 0.5 天 |
| 端到端验收 | 测试询盘 → D1 行含双快照+路径+IDs；GA4 DebugView 见 generate_lead 新参数；Web3Forms 邮件含 submission_id | 以上全部 | 0.5 天 |

**Phase 1 出口标准**：D1 每条新询盘可回答「从哪来（first/last）、看了什么（path）、是谁（anon_id 维度第几次来）」；周报主表切换为 §5.2 的 SQL 口径。

### Phase 2 — CRM 深度对接

| 项 | 内容 | 前置依赖 | 工作量 |
|---|---|---|---|
| CRM 决策 | HubSpot vs 继续 Brevo-only，业务拍板（growth-plan Block 0.3 遗留决策） | Phase 1 稳定跑 2–4 周，积累真实字段需求 | Biz 决策 |
| HubSpot 接线 | 私有应用 + 11+3 个联系人属性（§4.3）+ Worker 加 HubSpot deliver 分支（复用 v2 重试/死信骨架） | CRM 决策 + HubSpot 账号 | 1–2 天 |
| 商机回写 | 销售在 CRM 把联系人推进到 Deal/成交；周报表增加「询盘 → 商机 → 成交」按 first-touch 渠道的转化列 | HubSpot 接线 + 销售录入纪律 | 0.5 天 + 持续运营 |
| 看板升级 | 归因 widget 数据源从 D1 扩展到 CRM 商机阶段 | 商机回写稳定 | 0.5–1 天 |

**Phase 2 出口标准**：「哪篇内容带来了成交」可回答（而不只是「带来了询盘」）。

---

## 8. 明确不做的事（防 scope 蔓延）

- 不做多触点分摊模型（linear/position-based/data-driven）——理由见 §3.1。
- 不做跨设备身份缝合、不做登录体系——B2B 小站询盘量级不值得。
- 不引入 CDP / Segment / 数据仓库——D1 + GA4 + 一份 SQL 就是全部「数据栈」。
- 不上 cookie 同意横幅——方案不新增 cookie；GA4 现状维持（若未来进入严管市场再评估）。
- 不在 widget 层做实时 join、不建专职数据工程依赖的任何组件。

---

## 附：关键文件索引

| 文件 | 作用 |
|---|---|
| `site/assets/js/track.js` | 事件 + 归因采集 + 惰性中继（ENDPOINT 待填） |
| `site/inquiry.html` | 表单、journey 参数注入、generate_lead、nurture beacon |
| `site/journey/journey.js` | journey 状态与 mc_journey_brief 同意传递 |
| `workers/leads-worker.js` | v2：D1 持久化 + Brevo + 幂等 + 限流 |
| `workers/schema.sql` | D1 建表（本文 §3.3 给出扩列 ALTER） |
| `ops/gtm-event-setup.md` | GTM 9 事件配置手册 |
| `ops/hubspot-integration.md` | HubSpot 11 属性 + 中继契约（workers/ 无对应文件，属规格文档） |
| `ops/worker-deploy.md` | Worker v2 部署手册 |
| `site/privacy.html` / `privacy.md` | 隐私政策（§6 对齐对象） |
