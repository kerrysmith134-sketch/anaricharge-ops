# ANARI Charge 周运营报告 — 2026-10-19（Week7 / W43）

> 执行：周运营总编排（周一 17:34 CST 收尾）｜ 数据：GSC sc-domain:anaricharge.com（OpenSEO 桥程序化实拉，免费路径）+ GA4 G-MT63H5Q8EV
> 快照留存：`gsc-queries-2026-10-19.txt`（脚本 `week7-gsc-pull.py` 可复跑）

---

## 一、数据组：GSC + GA4 实测

### GSC 总量对比（28 天窗口 09-20..10-17，与上周 10-15 拉取有 2 天口径错位，趋势可比）

| 口径 | 10-15（28 天） | 10-19（28 天） | 变化 |
|---|---|---|---|
| 展示 | 413 | **469** | +14% |
| 点击 | 2（品牌词，首页） | **3**（首页 2 + 博客 1） | **首个博客点击** |
| 平均位次 | 38.9 | 37.0 | +1.9 位 |
| 查询词数 | 64 | **81** | +27% |
| 有展示的页面数 | — | **33** | — |
| 前 28 天（08-23..09-19） | — | 44 展示 / 0 点击 | **环比 ~10 倍** |

近 7 天（10-11..10-17）：34 展示 / 0 点击 / p42.3。其中 ~12 次展示来自 "agari incoming/on-prem/powertech" 等同形异义垃圾词（p67-98），属噪声，不视为业务流量；剔除后真实 7 天展示约 22。

### 本周亮点（按战略价值排序）

| 信号 | 数据 | 判断 |
|---|---|---|
| **首个博客点击** | /blog/ev-charging-business-plan：1 点击 / 11 展示 / **CTR 9.1%** / p12.4 | 内容页 CTR 健康，位次进首页即可放量 |
| franchise 支柱页 | 118 展示 / p22.7（上周 p24.7） | 最大展示页，位次持续爬升，离二页顶部一步 |
| franchise-profit 文章 | 26 展示 / p12.5 | Week5 文章已进二页头部 |
| profit-margin 词簇 | 4 个词进 p9–16（profit margin p9 / p11 / p13 / p16） | **首页机会带已成形**，CTR 优化可收割 |
| business-plan 词簇 | 4 个词 p10–18 | 与首个点击同源，CTR 优化第二优先 |
| 首页 | 2 点击 / 35 展示 / CTR 5.7% / p5.3 | 品牌词基本盘稳 |
| 印度 franchise 页 | 74 展示 / p82.6 | 需求真实但位次深——外链权威性的直接缺口 |
| commercial-cost 文章 | 47 展示 / p65.9 | 同上，等外链 |

### GA4（近 28 天）

- **generate_lead = 0，key events 行仍为空**——用户仍未把 generate_lead 标记为关键事件（Admin → Events → 点星），已拖 3 周以上。这是 30 询盘目标的数据地基，本周待办第 1 项。

---

## 二、本周各角色产出

### 内容组 ✅✅✅ 三篇当日完成并全部上线（分支 `seo/week7-content`，PR #23）

| 文章 | 承接查询词 | 状态 |
|---|---|---|
| Commercial AC Charging Station Installation Cost（$3k–10k/port 六行预算） | cost of installing commercial ac charging station（11 展示）+ commercial cost 词簇 | ✅ 线上 200 |
| EV Charging Station Dealership in India（PM E-DRIVE ₹2,000 crore） | 印度 franchise 词簇 ~74 展示 + dealership 意图 | ✅ 线上 200 |
| EV Charging Franchise Agreement: 10 Clauses | **ev station contract p33.5 + ev charging point franchise p36.5**（唯一直接命中 10–40 位次带） | ✅ 线上 200 |

- 三道门全绿：Markdown 镜像 55/55、sitemap 重建 **100 URL**、`node validate.js` **101 页 PASSED**（push 前本地跑，零 Gatekeeper 返工）
- PR #23 经 compare 页提交后 **Gatekeeper 自动 squash 合并**（main = 9384381），Cloudflare 已部署，无需用户操作
- blog hub 3 卡置顶、"30 business guides" 计数、verified 2026-10-19 均已更新
- **队列消耗标记：D1/D2/D3 已用完**，周二内容主编应从 D4 起取（已同步 anari-daily-ops-plan.md）

### 优化组 ⚠️ 部分完成 + ✅ CTR 专项提前落地（PR #24）

- ✅ **CTR 优化专项已于当晚执行完毕**（用户 17:48 批准）：5 个高展示存量页 title/meta 数字前置改写，仅动 title+meta 不动正文，所有数字取自各文正文。分支 `seo/week7-ctr`（commit 864797d），PR #24 由 Gatekeeper 自动 squash 合并（main=1f95f75），validate 101 页 PASSED。5 页线上新 title 已 curl 验证全部生效，IndexNow 5 URL HTTP 200
- 改写的 5 页：franchise 支柱页（118imp/p22.7 → "$15k–$50k + 4–8%"）、franchise-profit（26imp/p12.5 → "Breakeven at ~15% Utilization"）、investment（p19.4 → "$3k to $250k+ by Format"）、fleet-depot（32imp 词/p68 → "AC $3k–7k per Stall vs DC $25k+"）、buy-existing（p33.5 → "5 Due-Diligence Checks"）。效果观察：下周 GSC 快照对比这 5 页 CTR
- ✅ IndexNow：4 个新 URL + 5 个 CTR 页 = 当日 9 URL 全部 HTTP 200
- ✅ 部署后验证：三篇新文 + 5 个 CTR 页线上 curl 200，线上 sitemap 100 URL 含全部新文
- ⚠️ GSC 索引请求 **1/4 成功**：commercial-ac-installation-cost 已确认 "Indexing requested" 绿条；剩 3 个新文 URL + 5 个 CTR 页 URL 判断为**日配额耗尽**（凌晨验收员已用 5 个 + 本次 1 个 = 6，与 9/22「提交 6 个后限流」记录吻合；症状 = 检查工具输入框无法触发检查页）。8 个 URL 转明日验收员 10:43 档**分两天**提交（每天 ≤5 个），脚本 `gsc-request2.py` 可用（注意其检测正则需区分大小写）
- 经验：GSC 检查工具今天极慢，单 URL 5–7 分钟，自动化需拆段跑；GitHub compare 页建 PR 后出现的红色 flash 报错文字多为页面预渲染的隐藏模板，实际可能已创建成功——以 `git fetch + git log origin/main` 为准

### Quora 社区组 ❌ 诚实失败（0/2 发布）

- 目标问题 ROI 类（3 回答低竞争），~260 词原创回答（六行 ROI 计算法 + /tools/charging-station-roi 链接已验 200 + 披露句）**两次提交均被吞**（Post 后刷新无 permalink/正文/横幅）——连「每会话首发必成功」的旧规律今天都未守住，疑似 Quora 发布通道收紧/限流升级
- 处置：草稿已存 Quora 服务端（Edit draft）+ 全文落 `quora-draft-roi.md`，**隔 ≥24h 由明日社区档（15:41）重试**，今日不再试（防账号风控）
- 本周 W43 带链接配额 3 条实际使用 0；solar 草稿（quora-draft-solar.md）排在 ROI 之后
- 过程中确认：OneTrust 隐私弹窗会挡编辑器（点 Allow All 解决）；Cloudflare 验证页 reload 一次可过

### 外链组 ✅ 弹药已交付：`anari-backlinks-week-1019.md`

- **明天 10/20 是 10/16 批次 14 家的第 4 天跟进节点**：模板 G（轻触式）+ 各家定制钩子句已备好
- 10/27 第 10 天收尾：模板 H
- Canary 通用角度首发 pitch 已写好（禁用约旦独家角度）
- 新增 10 家免费 pitch 目标：EVreporter / Mercom India / ET EnergyWorld / Smart Energy Decisions / Facility Executive / Parking Today / Hotel Management / Microgrid Knowledge / PV Tech / Work Truck——角度绑本周三篇新文
- 低成本路线确认：CharIN/OCA 付费渠道继续暂缓

### 引流组 ✅ 素材包：`anari-promo-pack-week7.md`（9 条 + 1 条 ROI 复用）

- 每篇新文 3 条问答式素材（Quora 6 条可直接用 / Reddit 3 条储备），150–250 词 + 1 回链 + 披露句
- **Reddit 纪律**：u/Sad-Researcher3564 已 ~27 天，但 **karma 仍未验证**——karma <100 前 Reddit 素材只储备不发布

---

## 三、下周（Week8）选题地图

| 优先级 | 选题 | 依据 |
|---|---|---|
| P0 | ~~CTR 优化专项~~ **已于 10-19 当晚完成**（PR #24，5 页上线）；下周转为**效果观察**：周一 GSC 快照对比首批 5 页 CTR | 首批数字前置改写已落地，用数据验证打法 |
| P0 | **第二批 CTR + 内链加固**（用户 10-19 18:56 批准排入）：目标页 commercial-ev-charging-station-cost（47imp/p65.9）、franchise-cost-india（74imp/p82.6）、fleet-depot 方案页（34imp/p64.7）、agents 页（22imp/p47.8）；动作 = title/meta 数字前置改写 + 从本周 3 篇新文和高位次页（franchise 支柱 p22.7、transformer p8、50kw-dc p6.3）向这 4 页加相关内链。**触发条件：周一快照显示首批 5 页 CTR 有改善即执行；若无改善则只改 title/meta、暂缓内链大动，先复盘写法** | 深位次高展示页单靠 CTR 不够，需内链权重配合；与首批构成 A/B 对照 |
| P0 | 队列 D4：LCFS 碳信用增收文 | anari-daily-ops-plan.md 队列下一篇（周二主编取） |
| P1 | 队列 D5–D10 顺延（feasibility checklist 等） | 策略师周日 20:17 档会按新 GSC 数据重置队列，以重置后为准 |
| P1 | franchise 支柱页二刷（118 展示 p22.7，扩印度/非洲小节承接深位次词） | 最大展示页，进二页顶部后 CTR 优化空间最大 |
| P2 | 印度词簇外链落地前，暂缓新增印度内容 | 74 展示 p82.6 证明需求，但无权威性支撑新文同样沉底 |

---

## 四、用户待办清单（按优先级）

1. **GA4 标记 generate_lead 为关键事件**（Admin → Events → 找到 generate_lead → 点星）——拖了 3 周+，0 询盘无法归因到渠道，30 询盘目标的数据地基
2. **外链邮件明天 10/20 发出**（sales@ 手动发）：模板 G 跟进 ×12 + Canary 首发 ×1，全部文案在 `anari-backlinks-week-1019.md`，发完在清单里打勾
3. **Reddit karma 帮查**：打开 reddit.com/user/Sad-Researcher3564 看一眼 karma 数告诉我；≥100 则 Week8 启用带链接帖（每周 ≤2 条）
4. **Qwoted 档案补完**（余 25%）——免费 PR 渠道，一次投入长期收益
5. ~~合并 PR~~ 本周无需操作：PR #23 已被 Gatekeeper 自动合并并部署上线
6. Quora 无需用户操作：明日后台自动档隔 24h 重试 ROI 草稿；若再被吞会在日报中报告
7. **口径更新 PR 未建/未合并（chore/fact-30-countries@67cdc70）**——10-20 18:00 档核查：远端 chore/fact-30-countries 分支已消失，但 origin/main 无对应 squash commit、全站仍为「100+ customers in 22 countries」旧口径，线上未更新；不做补救，归明日验收员 10:43 档兜底（补建 PR → Gatekeeper squash 合并）

---

## 本周最重要的发现

**内容机器已全速运转——展示环比前 28 天约 10 倍、史上首个博客内容点击出现（CTR 9.1%）、三篇新文当日写完当日上线——但询盘仍为 0 且 Quora 发布通道今天疑似被限流升级：瓶颈已从「内容产能」彻底转向「分发通道（Quora/外链）+ 转化事件标记（GA4）」，下周的最高杠杆动作是用户把 generate_lead 点星和把 12 封跟进邮件发出去。**
