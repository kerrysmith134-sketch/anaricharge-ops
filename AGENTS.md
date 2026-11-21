# AGENTS.md — ANARI 运营接管工作区

> 本文件是本工作区的**运行契约**。任何 AI agent（含后续会话）进入本目录，先读完本文件再动手。
> 建立于 2026-11-07，接管自 `/Users/kerrychu/Documents/kimi/workspace`（Kimi 时代的运营工作区）。

---

## 0. 这是什么

anaricharge.com（深圳安纳瑞能源 / Anari Energy 企业站）的**全部运营工作流、技能库、套件与执行记录**的接管工作区。

原工作区在 `~/Documents/kimi/workspace`，对本会话**只读**（沙箱限制）。所有接管产物都写在本目录。原工作区继续作为「事实来源」，但**不要再往那写**——两边会漂移。

> **接手先读**：`08-execution/SYSTEM-HANDOVER.md` —— 系统交接说明书（11 渠道 / 30 技能 / 22 任务 / 14 KPI 的现状与操作方式）。

```
00-takeover/    接管报告、缺口分析、迁移日志、同步回写方案
01-inventory/   资产盘点（技能/工作流/套件/记录/站点）
02-skills/      规范化后的技能库（含 manifest 与合并映射）
03-workflows/   可执行工作流 SOP（W1..Wn）+ 机器可读排期
04-suites/      套件（黄金组合，按序编排）
05-records/     执行记录复盘：时间线/现状/未闭环/决策集 + 原始副本
06-site/        站点工程镜像（主源 anari-new-site，含 git 历史）
07-optimization/ 优化方案（技能去重/工作流精简/自动化改造）
08-execution/   接管后的实际执行产出（真实的运营数据与裁定）
scripts/        可复跑脚本（拉数/校验/同步）
```

---

## 1. 硬规则（从执行记录里继承的，不能违反）

| # | 规则 | 来源 |
|---|---|---|
| R1 | **公司事实口径统一为「22 国 100+ 客户」**。任何地方禁止再出现「30+ 国」。23 国是路线图不是交付口径。 | 2026-10-20 用户拍板 |
| R2 | **不点名竞品**。内容红线：不写竞对品牌做对比，不做 listicle 排名。 | 多份内容记录 |
| R3 | **$500/月预算，有机优先；广告只用于小额验证**（2026-11-09 用户改判）：默认仍投有机；广告上限 **≤$100/月**，且须有明确假设+止损线（CPL 上限 / 7 天无有效询盘即停）、UTM+GA4 可归因、**单次开启需用户确认**。A33 档位保留，只做方案与监控，不自行花钱。 | 用户决定 2026-11-09 |
| R4 | **Brevo = 营销 + 销售 CRM**（2026-11-08 用户提供 API key 后更新）：营销侧是培育/订阅/序列邮件；销售侧用 Brevo 自带 **CRM Deals** 做商机与管线，**不再引入 HubSpot**。询盘落 D1 → 账本（`lead_lifecycle.py`）→ Brevo Deals（`brevo_crm.py`）。 | 2026-10-22 拍板 + 2026-11-08 用户决定 |
| R5 | **单轮只推进一项**：每轮只做队列第一个未完成条目，验证上线即收尾。 | 2026-10-26 用户指令 |
| R6 | **浏览器自动化已恢复为允许能力**（2026-11-07 用户覆盖旧规则）：可用真实浏览器带登录态操作 Quora / Reddit / Brevo 工作流。但**不可逆动作（发帖、发信、删数据、改线上配置）必须逐次人工确认或显式授权**；不代注册、不猜密码、不绕验证码。**GSC 已登录，URL Inspection 请求编入索引可全自动**（`00-takeover/BROWSER-CAPABILITY.md` 坑 3；2026-11-10 实测 5/5，脚本 `scripts/tools/gsc_request_indexing.py`），日常数据仍优先官方 API（见 §3）；Cloudflare 后台未登录 → 用 API token。 | 2026-11-07 用户指令（覆盖 2026-10-26）；2026-11-10 用户更正 GSC 信息 |
| R7 | **内核步数预算 ~100**，第 80 步强制收尾。**注意额度**：2026-11-01 停摆的真实原因是 Kimi 额度耗尽，排期必须按额度预算设计，宁少勿多。 | 2026-10-26 + 2026-11-07 用户说明 |
| R8 | 事实门禁：改任何事实性数字后必须跑 `node scripts/check-facts.js`，非零即不得提交。 | `site/AGENTS.md` |
| R9 | 发布走 PR + Gatekeeper 自动合并，分支名必须以 `seo/ content/ chore/ docs/ week` 开头才触发。 | `.github/workflows/pr-gatekeeper.yml` |
| R10 | **浏览器卫生（全员强制，含子 agent 与定时任务会话）**：① 开跑前 `wb.py hygiene` 清残留；② 同一时刻只留 1–2 个标签，能复用就复用（`newTab:false`）；③ 结束前再跑 `hygiene` 并确认 `✅ 浏览器已清空`；④ 优先用 `ops.py`（自带 cleanup）。**2026-11-10 起改为三层机制，不再靠自觉**：(a) `wb.py` 进程退出 **atexit 自动关闭本进程碰过的会话标签**（脚本异常/提前 return 也不漏；排查时用 `WB_KEEP_TABS=1`）；(b) 关键脚本 `approval.py` / `geo_ai_layer.py` 已包 `try/finally`；(c) **哨兵档位每 4 小时跑 `scripts/browser/patrol.py --quiet`**，发现残留自动清理并写台账 `08-execution/tech/browser-patrol.jsonl`。复查发现漏点：社区发布 `approval.py`、周三 GEO `geo_ai_layer.py` 开标签后不关。 | 2026-11-07 用户要求 + 2026-11-10 用户复查 |
| R11 | **防重复劳动（全员强制）**：任何渠道/资产工作动手前必须 `python3 scripts/metrics/prior_art.py <关键词>`，搜 `05-records/` `01-inventory/` `02-skills/` `03-workflows/`；命中先读再决定，没命中才当新领域。**起因**：2026-11-07 我把 UNGM 当新机会重新盘点（实际 10-22 已注册 Basic #1290463 / 27 机构 / 7 个 UNSPSC 码 / 32 条公告已扫，且决策 A4 已定"只作外链渠道不获客"），又把"自助目录"当新发现（实际 10-17 已做 6 家字段级实测 + 12 候选 + 4 排除）。`05-records/` 就是记忆，不查等于失忆。 | 2026-11-07 用户纠正 |
| R12 | **发布前强制分支检查（全员强制）**：发布（push 到 main）只能从 **main 分支**且必须是 fast-forward。 仓库里已有两道机制，**不要绕过**：① `scripts/hooks/pre-push`（版本化、随 `install-hooks.sh` 安装） 非 main 分支直接拒绝；② 唯一发布入口 `bash scripts/tools/publish.sh "commit message"` = 分支检查 → 四道门禁（validate / check-facts / 入链审计 / ci-static-checks）→ 提交(仅指定路径) → 推送 → 线上 200 复核。 **起因**：2026-11-10/11 各发生一次「在并行会话的分支上 commit，`git add -A` 把别人未完成的页面一起推上 main」。 确需推分支做 PR 时：`ANARI_ALLOW_BRANCH_PUSH=1 git push origin <branch>`。**每次站点改动必须同一轮内完成「提交 + 部署 + 一致性核对」**（用户 2026-11-12 明确要求）：`publish.sh` 第 5 步会自动读线上 `/deploy-manifest.json` 与本地 HEAD 比对，落后就**自动调用** `scripts/tools/deploy-site.sh` 补部署并复核（`SKIP_AUTO_DEPLOY=1` 可关）；单独核对用 `bash scripts/tools/deploy-sync-check.sh`（0=同步 / 1=落后）。**部署复核**：站点 = Worker `anaricharge-website`（静态资源），push 后等 ~2 分钟验证线上；若 5–10 分钟仍没变（字节/etag 不动），说明 CF Workers Builds 没跑成功，用 `bash scripts/tools/deploy-site.sh` 手动部署并复核 200（2026-11-12 实测案例 f6e01ef）。 | 用户要求 2026-11-11 |
| R13 | **会话治理（全员强制，2026-11-12 用户要求）**：① **排期任务禁止用 `target.kind="new"`**——每次运行新建会话会导致一年几千个会话（实测旧配置每月 +314 个）；默认投递到固定会话（`this_session` 或指定 session）；② 同一主体/团队的工作必须在**同一个会话**里延续，不按"每天一次"开新会话；③ 上下文满了靠 harness 自动压缩，**持久状态一律落文件**（`08-execution/`、`ops/`），会话只作工作台；④ 每月 1 日跑 `python3 scripts/tools/session_hygiene.py`，用 `--archive-days 30 --apply` 归档 30 天未动的旧会话（移动到 `~/.dsh/sessions-archive/`，可逆，保护当前会话与排期引用会话）。策略文档：`08-execution/tech/2026-11-12-SESSION-POLICY.md`。 | 用户要求 2026-11-12 |

| R14 | **档位分级 + 独立验证 + 写作用域（2026-11-17 起，全员强制）**：① **档位分级**：所有排期任务必须标 tier —— `L1` 纯脚本（秒级、零判断：哨兵/清理/兜底通知/摘要/会话治理）、`L2` 快模型+脚本（看板/守夜/送达率/位次）、`L3` 强模型判断（内容/策略/飞轮/复盘）；台账在 `03-workflows/TASK-TIERS.json`。新增档位必须登记 tier，`L1` 禁止做任何解释性写作。② **独立验证（verifier 必须独立重跑）**：任何人报告"门禁全绿"都必须在**合并后的 HEAD** 上重跑 `bash 06-site/anari-new-site/scripts/tools/verify-gates.sh`，把命令与输出原文归档到 `08-execution/tech/gate-runs/`；**不采信构建方自述的通过率**（起因：2026-11-17 并行提交自述 12/12，实测 8/12，还回退了部署脚本、恢复了 32 个已删页）。③ **写作用域 + 变基守卫**：发布前跑 `bash scripts/tools/gate-preflight.sh --scope "<前缀,...>"`（`publish.sh` 第 3.5 步已内置，`SCOPE=` 传入作用域）：分支必须 main、落后上游即拒绝、改动必须落在声明作用域内。`channel_lock.py` 只防"同时"，防不住"先后覆盖"——对外发送前还要查 `Sent` 里近 24h 是否已发过同一收件人。 | 用户要求 2026-11-17 |

---

## 2. 站点与账号事实

- 线上：https://anaricharge.com（`www.` 为准，裸域 301）
- **范围裁定（2026-11-07 用户拍板）**：本团队**只运营 anaricharge.com**；**anariev.com 由人工团队维护，本团队不再承接**（其 WordPress 源、线上 llms.txt、交付物上传、WP 侧 30-口径修复均归对方团队）。仓库内 `06-site/*/anariev/` 仅作参考；已推的 `docs/anariev-22countries-20261107` 分支留档供对方取用，本团队不跟进其 PR 与合并。
- 仓库：`git@github.com:kerrysmith134-sketch/anaricharge-website.git`
- 主机：**Cloudflare Worker `anaricharge-website`（静态资源模式）**，由 CF Workers Builds 从 `main` 自动部署；提示词/文档里写的 Cloudflare Pages 是历史说法（2026-11-12 查证更正）。API Worker：`api.anaricharge.com`（D1 `anari-leads` + Brevo）
- 法务实体：Shenzhen Anari Energy Co., Ltd. · 2021 成立 · 深圳总部，西安/伊斯坦布尔/迪拜办公室
- 产品线（**2026-11-08 起只做直流 + 储能**）：Fora 360–960 kW 分体式 DC · Vulco 60–480 kW · Pales 60–240 kW · Castor 20–40 kW 壁挂 · Aquila DC+广告屏 · 液冷 BESS 120/261/418 kWh · ANARI OS。**AC（Gaia/Vesta）与便携（Sena）已下架，站上不再出现**。
- 联系：sales@anarienergy.com · WhatsApp +86 188 6620 5186
- 姊妹站：anariev.com（产品规格站）
- 三语：EN `/`、RU `/ru/`、ES `/es/`

> 站点当前线上 sitemap = **119 URL**，全量 200。本地仓库克隆曾落后（106/114），须先 fetch 到 origin/main。

---

## 3. 数据访问（已实测可用）

### GSC 官方 API —— 可直连，优先用它，不要再看板/桥回退
```bash
python3 scripts/gsc_pull.py --start 2026-10-10 --end 2026-11-06 \
  --out 08-execution/gsc-$(date +%Y%m%d).json
```
- 凭证：`~/Documents/kimi/workspace/.secrets/gsc-oauth.json`（OAuth refresh_token，**只读引用，不复制、不打印**）
- 属性：`sc-domain:anaricharge.com`；GA4：`G-MT63H5Q8EV`（property `553998974`）
- **口径铁律**：KPI 用**页面维度或无维度总量**。查询词维度在低流量站会因 GSC 匿名化丢 60% 展示，只可用于选题参考。

### 浏览器自动化（WebBridge）—— 已恢复
```bash
python3 scripts/browser/wb.py health      # 守护进程 + 扩展
python3 scripts/browser/wb.py status      # 各平台登录态（Quora/Reddit/Brevo 已登录）
python3 scripts/browser/ops.py quora-search "ev charging station franchise"
python3 scripts/browser/ops.py brevo-contacts
```
- 守护进程：`~/.kimi-webbridge/bin/kimi-webbridge start`（首次需 full-access，因为要写 `~/.kimi-webbridge/`）
- **坑**：后台标签页被 Chrome 节流导致页面不渲染 → 先 `osascript -e 'tell application "Google Chrome" to activate'`，并用 `wait_text` 等真实内容。
- 完整能力矩阵与边界：`00-takeover/BROWSER-CAPABILITY.md`

### Brevo API（2026-11-08 起可用）
```bash
python3 scripts/metrics/brevo_crm.py whoami   # 账号 + CRM 端点自检
python3 scripts/metrics/brevo_crm.py deals    # 现有商机
python3 scripts/metrics/brevo_crm.py push     # 账本 → Brevo Deals（幂等，--dry 可预览）
python3 scripts/metrics/brevo_crm.py verify   # 两侧对账
```
- 凭证：`.secrets/brevo.json`（600，`api_key` + `mcp_key`，**勿提交勿打印**）
- 账号：kerry@anaricharge.com · 公司 Shenzhen Anari Energy Co., Ltd · plan=free(300 credits)
- 列表：`Inquiry Nurture` id=3（0 订阅者）· 现有联系人 1 个（内部测试地址）
- **实测边界**：`POST/PATCH/DELETE /v3/crm/deals` 可用；**没有公开的 pipeline/stage 列表端点**
  → 脚本不猜 stage id，状态写在 deal_name 与 deal_description，stage 由销售在 UI 推进

### 其他
- **GA4 Data API 可直连**：`ga4_query.py realtime|events|event`（OAuth 凭证含 `analytics.readonly`，2026-11-08 实测通过）。旧说法"走代理可能失败"已作废。
- IndexNow：key 文件在站点根 `07a4fc3586fd43710c5ea08299d05c43.txt` 与 `1dc4587cc2384236b023b914cb76abf0.txt`。
- Worker 健康检查：`curl api.anaricharge.com/health` 返回 **403 是正常的**（Origin 白名单）。

---

## 4. 六个在岗角色与排期

| 角色 | 档期 | 核心产出 |
|---|---|---|
| R1 增长操盘手（总编排） | 周一 09:17 | 数据→选题→内容→社区→外链→索引→周报 |
| R2 SEO 工程师 | 周一 + 每月 8 日 | 技术 SEO、索引覆盖、Schema/GEO、CWV |
| R3 内容主编 | 周二～周六 09:23 | 每日 1 篇长尾（五件套），当周分支累积 PR |
| R4 外链与数字公关 | 周二/周五 10:19 | 每周 10 家新 pitch + 第 4/10 天跟进 |
| R5 社区引流 | 每日 15:41 | Quora 日更 1–2 答、Reddit 养号 |
| R6 数据分析师 | 每周 | GSC+GA4 数据、周报、转化核对 |

完整 SOP 见 `03-workflows/`，机器可读排期见 `03-workflows/_SCHEDULE.json`。
内容选题队列的**当前状态**见 `03-workflows/W5-content-pipeline.md` 与执行记录里的最新队列。

### v5.0 团队规格（2026-11-08 纳入）

`03-workflows/specs/v5.0/`（42 Agent / 8 Guild / 160 Skill / 25 Workflow / 19 Connector / 97 backlog）。
**机器可读花名册**：`03-workflows/TEAM-V5-ROSTER.json`（由 `scripts/team/import_v5.py` 生成，
每个角色带权限边界 + 谁在做 + 证据路径）。

- `python3 scripts/team/coverage.py` — 编制覆盖率 + **权限合规**（对照 Permission_Boundary 扫档位提示词），
  已接进 selftest。**当前 42 角色全覆盖：full 19 · partial 15 · planned 1（A30 付费搜索）· blocked 7
  （A08–A11 Apollo 额度恢复后启用；A20 需真人访谈；A26 需视频设备；A31 付费社媒不做）· gap 0 · none 0**
- **2026-11-09 用户两处改判**：① R2 只禁"对外点名/对比竞品"，**竞品研究允许**（A05 已设岗，仅内部 intel）
  ② R3 改为"有机优先 + 广告 ≤$100/月 验证"，**A33 广告档位保留**并写入预算上限/止损线/需授权
  ③ Apollo 有账号（masterkey 当前 422 额度耗尽）→ A08–A11 标 blocked 而非不做
- `python3 scripts/team/triage_backlog.py` — 97 条工程 backlog 分诊
  （met 14 / partial 14 / light 2 / na 10 / 需平台 57），见 `08-execution/backlog/v5-triage.md`
- **新增 3 个缺口档位**：A13 送达率与抑制（周一）· A37 月度归因结账（每月 1 日）·
  A32 生命周期培育（周四，只出草稿不发送）
- **抑制台账**：`ops/suppression.json` + `scripts/metrics/suppression.py`
  （邮箱/域名/机构三维匹配，命中即 HOLD），**已接进外联导入**
- **法域×触达矩阵**：`ops/outreach-privacy-matrix.json`（6 法域口径；中国境内冷邮件=硬禁止）

---

## 5. 质量门（改站点必跑）

```bash
cd 06-site/anari-new-site
node validate.js            # 页面契约：单 h1、无死链、FAQ schema 一致、canonical
node scripts/check-facts.js # 事实库一致性（事实性数字改动后必跑）
node build-sitemap.js && node scripts/build-markdown-mirrors.js && node scripts/build-llms-full.js
```

> 已知坑（2026-11-07 起部分解除）：Gatekeeper 白名单原不含生成器脚本。已在 `chore/mirror-generator-and-gatekeeper` 分支把 `scripts/build-markdown-mirrors.js` 与 `scripts/build-llms-full.js` 加入白名单——**该 chore 分支合并后**，生成器改动可随内容 PR 自动合并；合并前仍需「临时应用 → 构建 → 还原脚本 → 只提交产物」。
>
> **git hooks（2026-11-09 起）**：hook 版本化在 `06-site/anari-new-site/scripts/hooks/`；新 clone 或新 worktree 首次需 `bash scripts/install-hooks.sh`（设 `core.hooksPath`，本地配置不入库）。pre-commit 只做通用安全扫描，**不替代上面三条门禁**。
> **sitemap lastmod（2026-11-09 起）**：`build-sitemap.js` 已改为确定性来源（页面自述 → git 提交日期 → 常量兜底），**禁止再用 mtime**；整表重建现在同 commit 输出一致，若再出现「大批无关 lastmod 变化」先查是否被改回 mtime。**182/182 页已有页面自述 `dateModified`**；新增页面**不需要手动补**——`npm run build` 会在构建前置自动写入（`npm run dates` 单独跑也行），`node validate.js` 第 7 条会拦截没有日期声明的页。

---

## 6. 当前状态（精简；历史见 08-execution/HISTORY.md）

> 为什么精简：本文件此前累积了 40+ 轮状态条目，撞到工作区指令 65536 字节上限被
> **系统截断**（79978 → 65242），截断后契约后半部分对 agent 不可见。
> 现在只留"必须随时可见"的内容，其余按下面三个文件查。

| 文件 | 放什么 |
|---|---|
| `08-execution/STATUS.md` | **当前状态**：站点规模、KPI 读数、Growth OS 进度、待用户决定 |
| `08-execution/HISTORY.md` | **逐轮历史**（原 §6 全文，含每条教训与过程失误） |
| `08-execution/` 下按日期命名的 `*.md` | 单轮执行记录（详细版） |

### 最新一轮摘要

- **站点**：**179 页（EN 131 / RU 24 / ES 24）**· validate PASS · facts 54 · 0 孤儿 ·
  E2E 14/14 · 布局回归 20/20 · 对比度 0 问题。**产品线只做直流 + 储能**（AC 与便携已下架）。
- **北极星 SAQO**：`lead_lifecycle.py`（账本 + 六条件门）+ `brevo_crm.py`
  （账本 → Brevo Deals 幂等同步，已实测）。**当前 D1 询盘 0 → SAQO 0**。
- **工具**：4 个免费计算器；ROI / BESS TCO / 选型器支持**分享链接（URL 带输入、打开即重算）**，
  也支持打印/另存 PDF；`tco-calculator` 是 iframe 应用 → 暂无分享。
- **门禁**：`validate.js` / `check-facts.js` / `audit-inbound-links.js` /
  `selftest.sh`（**24 项**，含 evidence / SAQO 账本 / Brevo 对账 / GA4 / run log）/ `e2e-smoke.py`（14 项）/
  `contrast-audit.py` / **`layout-regression.py`**（DOM 度量，20 张，连跑两次确定性通过）。
- **发布分级（Gatekeeper Tier A/B/C）**：A 内容自动合并；B（CSS/JS/模板/生成器）不自动合并；
  C（Worker/询盘/追踪/隐私/`_headers`/workflows）不自动合并且要求人工冒烟；**未知路径按 C**。
- **run log**：`run_log.py`（人工写）+ `run_log_autolog.py`（从产物反推，已接进 watchdog，
  **qa=unknown 不假装**）。
- **GA4 生命周期事件（已打通）**：`ga4_events.py` 用 Measurement Protocol 发
  MQL/SAL/SAQO/won/lost；**`api_secret` 已配置**（`.secrets/ga4.json`，600），
  2026-11-08 实测 Realtime 查到 `lead_mql 1`。缺 secret 时会入队不丢。
- **GA4 可直查**：`ga4_query.py realtime|events|event`（OAuth 凭证含 `analytics.readonly`）；
  看板已加 `sections.ga4_lifecycle`。**MP 事件进标准报告约 24h 延迟，Realtime 立即**。

### 每日节奏（2026-11-08 起，用户要求"每天都要有推进"）

| 时间（北京） | 档位 | 产出 |
|---|---|---|
| **09:15** | **每日进度播报 → 本会话** | 档位 OK/PENDING/MISSING + 昨日产物 + 今天最该推进的 1–2 件 |
| **10:05** | **每日增长脉冲 → 本会话** | 每天一件具体增长事（周一索引/二内链/三 GEO/四转化/五存量/六内容复用/日外联复盘），必留产物 + run log |
| 09:17 13:17 17:17 21:17 | 询盘守夜 | 告警 + `lead_pipeline.py tick` |
| **22:05（工作日）** | **外联发信后体检 → 本会话** | `send_health.py`：退信>3% 红警、0 打开/有回复告警；样本<3 不下结论 |
| 周三 11:20 | 法规监测（A04） | `reg_watch.py`：官方页 diff；抓不到的源列"需人工看" |
| 周四 14:00 | 竞品情报（A05） | 仅内部 intel；R2 仍禁对外点名 |
| 周五 11:00 | 招标信号（A06） | TED/UNGM 公开公告；只做信号不做投标 |
| 周五 15:30 | 社媒监听（A28） | Quora/Reddit 问题与活跃回答者；只读 |
| 周六 09:40 | 位次监控（A18） | `position_watch.py`：下滑/上升/零点击/消失 |
| 每月 15 日 10:15 | 月度策略复盘（A01） | 加/减/停哪条渠道 + 哪个目标到不了 + 下月唯一优先级 |
| 21:30 | 每日工作总结 → 本会话 | 数据 / 做了什么 / 明天 3 件 |

> 为什么加这两个：用户反馈"其他团队都没见动作"。查下去是**两个度量 bug + 可见性问题**——
> watchdog 把"跑过的档位"判成"未启用"（读 `scheduledAt` 而非 rrule DTSTART，已修）；
> `marketing_outbound.py status` 读的 analytics 字段恒为 null，三个外联活动全报 0 leads（已改为翻页实查）。
> 修后真实数字：三波外联共 **29 个目标已就位**，索引收录 **108/178 = 60.7%**。

### 已知阻塞与诚实边界（2026-11-08）

- **DKIM（2026-11-09 邮件头级验证通过）**：`google._domainkey` TXT 三处 DNS 生效 +
  Google Admin 显示 `Authenticating email with DKIM` +
  **真实发信验到了 `DKIM-Signature: d=anaricharge.com; s=google`**。
  验证工具：`python3 scripts/outbound/dkim_verify.py`（mail.tm 一次性收件箱 + Instantly
  `/emails/test` 真发一封 → 读原始 EML 头 → 删临时信箱）。
  **边界**：接收方 `Authentication-Results` 读不到（mail.tm 不返回），只能证明"签名存在"。
  Gmail 自测与 Admin Email Log Search 两条路都不可用（前者页面不渲染，后者无公开 API 且会话会过期）。
  **DMARC 仍是 `p=none`**：等外联跑出第一周数据后再考虑升级 quarantine。
- **Quora（2026-11-08 已通）**：3 条回答全部发布并逐页实核在线（片段命中 + "无答案"提示消失）。
  踩坑记录：`approval.py` 只看退出码会误报成功；`ops.py` 三种失败形态（无入口 / Try again 错误页 / 限流）
  已分别处理；WebBridge daemon 偶发 502 已加重试。**注意本工作区可能有并行会话在跑社区频道**，
  发布前应做页面级查重。

### v6.0.1 / v6.1.0 代码库（2026-11-09）

`03-workflows/specs/v6/`（NestJS + Next.js + OpenAI Agents SDK + Temporal + Postgres RLS + OPA，
42 agent/160 skill/25 workflow/16 connector/93 schema；包自检 34 项全过）。

- **动作风险分级**：`ops/action-catalog.json`（R0–R5；v6 的 14 个 + 本地 5 个：
  Instantly 发信 R4 / 导入 R2、Quora 发布 R3、推站 R3、读询盘 R0）
- **动作策略检查**：`python3 scripts/team/policy_check.py check --action <key> ...`
  语义照搬 `infra/opa/marketing-actions.rego`：fail closed、同意门、抑制门、
  **agent 只能 R0–R2**、R3/R4 需审批。已接进外联导入与 selftest（23 项）
- **D1（✅ 迁移已应用生产）**：`workers/migrations/2026-11-09-consent-and-action-intents.sql`
  → `consent_ledger` / `action_intents` / `action_approvals` / `action_results`；
  并对 `audit_log` 做了幂等对齐（**更正：曾误判"audit_log 缺失/审计失败"——实为查询时 `tail` 截断
  导致误读；该表自 2026-11-07 就存在**）
- **同意台账已上线**：Worker 落库双写 `consent_ledger`（service_update 每次；marketing 仅
  `consent=1 && 未抑制`），`notice_version=privacy-v2026-10`，`withdrawn_at` 可撤回。
  **表单或隐私文本改版时必须同步改 Worker 里的 `NOTICE_VERSION` 常量**
- **端到端链路已受控验证**：真实提交 → D1 → audit → Brevo 联系人 → 账本 sync 全通，
  幂等去重生效；测试数据已清理（submissions=0）
- **查存在性数据别用 `tail`**：结构化输出用 jq/python 解析后计数（本轮误判的根因）
- **wrangler 可用前提**：`npm_config_cache=/tmp/npm-cache` + `XDG_CONFIG_HOME=<ws>/.tmpcfg`
  （`d1_query.py` 已自动设置；否则会误报 "token expired"）
- **不接**：NestJS/Cockpit/Temporal/Outbox/OpenAI Runtime/Postgres RLS/HubSpot/Apollo

### Instantly 发信诊断（2026-11-09 实测，重要）

- **`status=1` 不等于会发信**。判断"到底有没有在发"只能看
  `GET /campaigns/{id}/sending-status` →
  `status` ∈ `healthy` / `out_of_schedule` / `daily_limit_met` / `paused` 等。
- **新活动创建后必须显式 `POST /campaigns/{id}/activate`**。
  只把 status 设成 1 不够：本次 WAVE1 因此卡了 6 小时 0 封，
  调 activate 后约 2 分钟即开始发送、sending-status 转为 `healthy`。
- **该诊断的 `last_updated` 是缓存的**（本次一直停在 14:04），不刷新时别当实时状态。
- `campaign_schedule.start_date` 建议留 `null`（长期运行的活动）；设成未来日期会让活动"不开始"。
- 排查顺序：lead 状态（1=active）→ 账号状态（status/warmup_score/CTD）→
  `sending-status` 的 status 与 in_schedule → 最后才怀疑内容/域名。


### 审计 Wave 1（2026-11-10，两份外部审计落地）

`08-execution/2026-11-10-AUDIT-TRIAGE.md`（逐条分诊）+ `2026-11-10-AUDIT-WAVE1.md`（执行记录）。

**已修并上线**
- **D1 成为主记录通道**：`track.js` 在有效提交时先 `fetch POST /nurture` 落 D1（4s 超时），
  再走 Web3Forms 备份；成功页按 `anari_d1_status` 分两态文案（`ok` = recorded，
  其他 = on its way + 明确写出"未能确认内部记录"）。**不显示虚假成功。**
- **consent 台账 append-only**：`consent_events`（granted/withdrawn/regranted/notice_changed）
  + `consent_current` 视图；`consent_ledger` 降级为状态投影。**撤回后重新授权记 regranted**
  （旧实现被唯一约束静默吞掉）。Worker 用 `submission_id` 幂等。
- **语言切换器**：`add-lang-switch.py` 唯一判据 = 目标译文文件是否存在；支持就地刷新。
- **robots**：14 个具名爬虫组各带 `Disallow: /apps/`；两个计算器 SPA 加 `noindex, follow`。
- **案例数 9 → 8**（第 9 篇是下架的 22kW AC 案例），事实库同步。

**明确未做（别以为已做）**
- markets 55 页仍用旧 `/style.css` 模板 → 需把国别数据转 v2 spec 走 `build-v2-pages.js`，专项一轮
- 7 个过期页面已登记 `ops/fact-review-queue.json` + `regwatch-sources.json.manual_review_pages`，
  交 A04 回一手源后再改日期（**不伪造 Last verified**）
- D1→Brevo 仍是 `waitUntil` 重试，不是持久队列

**教训**：改任何出现在 `ops/fact-library.json` 里的数字，先同步事实库再提交
（本轮先推了案例数 commit、门禁是红的，随后才补事实库——违反 R8）。


### 外联/社媒频道互斥锁（2026-11-10 起，防并行会话撞车）

**起因**：EcoMENA 编辑回复后，我方已有一封"拒绝付费"的回信发出，但**不在 Instantly 发件记录里**
→ 说明有另一条路径（人工或并行会话）在操作同一个外联活动。两边同时回信会给媒体留下极差印象。

**机制**：`scripts/outbound/channel_lock.py`（锁文件 `ops/locks/<channel>.json`，TTL 30 分钟）
```bash
python3 scripts/outbound/channel_lock.py status  outbound
python3 scripts/outbound/channel_lock.py acquire outbound --owner <who> --purpose "回复某某"
python3 scripts/outbound/channel_lock.py release outbound --owner <who>
```
退出码 3 = 已被他人持有（**不要抢**，先看对方在做什么或等 30 分钟过期）。

**规则**：任何**对外发送/发布**动作（回信、发信、发帖、投稿、提交表单）动手前先 `acquire`；
做完 `release`。已接进 `selftest.sh`。这不能替代 R6（不可逆动作仍需授权），只是防重复。

### 询盘 → 商机的闭环操作（销售侧）

```bash
# 1) 拉 D1 新询盘进账本（幂等）
python3 scripts/metrics/lead_lifecycle.py sync
# 2) 逐条判资格（六条件，缺一项不能进 SAQO）
python3 scripts/metrics/lead_lifecycle.py qualify <sid> --real-contact --icp --market --need --trigger --accepted
# 3) 推进状态（lost/disqualified 必须写原因）
python3 scripts/metrics/lead_lifecycle.py set <sid> sal --by kerry
python3 scripts/metrics/lead_lifecycle.py set <sid> saqo --value 180000 --by kerry
# 4) 推到 Brevo CRM（销售在那边跟进）
python3 scripts/metrics/brevo_crm.py push
# 5) 对账（每周）
python3 scripts/metrics/brevo_crm.py verify
```
**口径**：北极星是 SAQO + pipeline value，**不是询盘条数**；放宽六条件等于制造假数字。

### 每次接手先跑

```bash
bash scripts/selftest.sh                        # 全链路冒烟（24 项）
python3 scripts/metrics/north_star.py           # 每日看板
python3 scripts/metrics/lead_lifecycle.py sync  # 拉 D1 询盘进账本
python3 scripts/tools/e2e-smoke.py --base https://www.anaricharge.com --ext ""
```
