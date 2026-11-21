# GTM 事件配置手册 — 9 个 dataLayer 事件转发 GA4

> 容器：**GTM-MRHHMP62**（已含 GA4 基础代码 G-MT63H5Q8EV + generate_lead 触发器，发布于 09-15）。
> 本手册把 track.js 推送的 9 个事件接入 GA4。全程在 [tagmanager.google.com](https://tagmanager.google.com) 操作，约 30-40 分钟。
> 事件契约（参数/触发时机）见 `ops/growth-plan-2026-09.md` Block 0.1，代码见 `site/assets/js/track.js`。

## 第 0 步：确认现状

容器 → 触发器：应已存在 `generate_lead`（自定义事件）。标签：应已有一个 GA4 事件标签（GA4 事件 = generate_lead）。
**若 generate_lead 不在，按第 2/3 步同样方法补建。**

## 第 1 步：创建数据层变量（10 个）

变量（Variables）→ 新建 → **数据层变量（Data Layer Variable）** → 数据层变量名填下表第二列 → 命名建议 `dlv - xxx`：

| 变量名建议 | 数据层变量名（逐字符） | 用于哪些事件 |
|---|---|---|
| dlv - segment | `segment` | segment_select, journey_start, journey_complete, generate_lead |
| dlv - step | `step` | journey_step |
| dlv - step_name | `step_name` | journey_step |
| dlv - country | `country` | journey_complete |
| dlv - case | `case` | case_to_inquiry |
| dlv - market | `market` | market_to_inquiry |
| dlv - location | `location` | whatsapp_click, case/market_to_inquiry |
| dlv - has_journey | `has_journey` | generate_lead（补参数时用） |
| dlv - has_journey_ref | `has_journey_ref` | inquiry_view |
| dlv - page_language | `page_language` | 全部（每个事件标签都带） |

注意大小写敏感。`page_path` 不用建——GA4 基础代码自动采集。

## 第 2 步：创建 8 个自定义事件触发器

触发器（Triggers）→ 新建 → **自定义事件（Custom Event）** → 事件名称填下表 → 命名建议 `CE - xxx`：

`segment_select` · `journey_start` · `journey_step` · `journey_complete` · `inquiry_view` · `whatsapp_click` · `checklist_request` · `case_to_inquiry` · `market_to_inquiry`

（generate_lead 已存在则跳过，共 9 个事件 8 个新触发器。）

## 第 3 步：创建 8 个 GA4 事件标签

标签 → 新建 → **Google Analytics：GA4 事件** → 目标代码选现有的 GA4 基础代码 → 事件名称与参数按下表；触发条件选第 2 步对应触发器。**每个标签都加一行参数 `page_language` = `{{dlv - page_language}}`**：

| 标签/事件名 | 附加事件参数 |
|---|---|
| segment_select | segment |
| journey_start | segment |
| journey_step | step、step_name |
| journey_complete | segment、country |
| inquiry_view | has_journey_ref |
| whatsapp_click | location |
| checklist_request | （仅 page_language） |
| case_to_inquiry | case、location |
| market_to_inquiry | market、location |

另：检查既有 generate_lead 标签——若参数不全，补上 `segment`=`{{dlv - segment}}`、`has_journey`=`{{dlv - has_journey}}`、`page_language`=`{{dlv - page_language}}`。

## 第 4 步：GA4 注册自定义维度（不做这步，报告里参数为空）

GA4 → 管理 → 媒体资源 → 数据展示 → **自定义定义** → 创建自定义维度（范围：事件）：

`segment` `step_name` `country` `case` `market` `location` `has_journey` `has_journey_ref` `page_language`

关键事件（Admin → 关键事件）：`generate_lead` 已是关键事件 ✔；建议把 `journey_complete`（方案书完成 = 最强意向）也标为关键事件，其余保持普通事件。

## 第 5 步：预览测试（必须逐个点一遍）

GTM → 预览（Tag Assistant）→ 输入 `https://www.anaricharge.com` → Connect，新窗口里按下面路径走，**回 GTM 预览面板看每个标签 Fired 且参数取值正确**：

1. 首页点任意身份 chip → `segment_select`（segment 应为 engineering-contractor 等，**不是 unknown**）
2. 点 Continue → journey 第 1 步 → `journey_start` + `journey_step`（step=1）+ 页面应**自动预选**刚点的身份
3. journey 点 Next 走 2-3 步 → `journey_step`（step=2,3…）；不选内容直接点 Continue 应**被门拦住**（页面不跳转）
4. 点任意 WhatsApp → `whatsapp_click`（location=footer/contact-bar 等）
5. 首页邮箱捕获提交 → `checklist_request`
6. 直接访问 `https://www.anaricharge.com/inquiry?sent=1&ref=TEST-01&segment=fleet` → `generate_lead`（segment=fleet，has_journey=true）——**这就是 journey 线索归因的最终形态**
7. 案例页点 CTA → `case_to_inquiry`（case=jordan-160kw 等，location=content）
8. GA4 左下角选 DebugView/实时，确认事件与参数到达

## 第 6 步：发布

提交 → 版本命名如 `9 events + params — 2026-09-19` → 发布。

## 故障排查

- 预览里一个事件都没有：track.js 是否 200（`curl -sI https://www.anaricharge.com/assets/js/track.js`）；浏览器强刷；确认没开 Adblock
- 事件到但参数 undefined：第 1 步变量名大小写/拼写；参数在事件 push 里不存在（对照 track.js 源码）
- segment=unknown 出现在 RU/ES 首页：理论上已修（位置索引映射），若复现立即报架构师
- GA4 报告延迟 24-48h，测试以 DebugView/实时为准

## 归因 Phase 1 增量（2026-10-26 上线，待 GTM/GA4 后台配置）

2026-10-26 起 `generate_lead` 事件新增 6 个参数（代码已上线，GTM/GA4 侧需人工配置后才能进报告）：

| 新参数 | 含义 | 取值来源 |
|---|---|---|
| `submission_id` | 四方对账键（GA4↔D1↔Brevo↔邮件），提交瞬间前端生成的 UUID | dataLayer |
| `attr_line` | 流量线：A-outbound / B-referral / C-organic / direct / other | dataLayer |
| `attr_source` | utm_source | dataLayer |
| `attr_medium` | utm_medium | dataLayer |
| `attr_campaign` | utm_campaign | dataLayer |
| `attr_landing` | 会话落地页路径 | dataLayer |

后台待办（人工，约 15 分钟）：

1. **GTM 变量**：新建 6 个数据层变量（`submission_id`、`attr_line`、`attr_source`、`attr_medium`、`attr_campaign`、`attr_landing`），命名建议 `dlv - submission_id` 等；
2. **GTM 标签**：在既有 generate_lead GA4 事件标签上补挂这 6 个参数；
3. **GA4 自定义维度**（范围：事件）：注册 `attr_line`、`attr_source`、`attr_medium`、`attr_campaign`、`attr_landing`；`submission_id` 高基数，**不要**注册为自定义维度（会触顶），对账走 BigQuery 导出或 DebugView 实时核对；
4. 预览模式下提交一条测试询盘，确认 generate_lead 带齐新参数后发布版本，版本命名如 `generate_lead attribution params — 2026-10-26`。

附：D1↔Brevo 侧的对账字段（anon_id / session_id / attr_first / attr_last / content_path）不经过 dataLayer，由询盘成功页 beacon 直送 Worker，无需 GTM 配置。
