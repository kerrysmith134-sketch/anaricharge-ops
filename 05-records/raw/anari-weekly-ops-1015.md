# ANARI Charge 周运营报告 — 2026-10-15（Week5，断更恢复周）

> 执行：周运营总编排 ｜ 数据：GSC sc-domain:anaricharge.com（WebBridge 实拉）+ GA4 G-MT63H5Q8EV
> ⚠️ 背景：9/22–10/15 全部 6 个营销定时任务被意外禁用，断更 3 周，今日恢复。本报告对比基线仍为 09-22 周报。

---

## 一、数据组：GSC + GA4 实测

### GSC 总量对比

| 口径 | 09-22（90 天） | 10-15（28 天） | 变化 |
|---|---|---|---|
| 展示 | 约 20+（17 词各 1-2 次） | **413** | 量级跃升 |
| 点击 | 0 | 2（品牌词，首页 p5.7） | 破零 |
| 平均位次 | — | 38.9 | — |
| 查询词数 | 17 | **64** | +276% |

### 近 28 天关键词战场（按战略价值排序）

| 查询词 | 展示 | 位次 | 判断 |
|---|---|---|---|
| fleet depot overnight ac charging system | 32 | 68.3 | **最大展示词**，本周文章 2 承接 |
| ev charging station franchise cost | 25 | 25.7 | **主战场**，franchise 支柱页 p25.0 |
| ev charging station franchise | 18 | 53.6 | 同簇 |
| cost of installing commercial ac charging station | 11 | 90.9 | 本周文章 2 兼承接 |
| anari ev charger / anari energy / anari charger | 18 | p6-7 | 品牌词稳居首页 |
| charging station investment | 6 | 19.0 | p17→p19 基本持平，Week4 文章承接中 |
| peak-valley arbitrage | 7 | 63.3 | p58→p63 略降 |
| **ev charging station franchise profit** | 3 | **11.7** | 首页边缘，本周文章 1 承接 |
| ev charger franchise cost | 2 | **8.5** | 已在首页 |
| charging station franchise cost | 2 | **10.5** | 首页/二页边界 |
| ev charging station investment/startup cost | 2 | **10.0** | 首页/二页边界 |
| ev charging business for sale / ev station contract | 4 | 33.5 | 本周文章 3 承接 |
| Tata/Reliance/Adani/Jio franchise 词簇 | ~30 | 73-104 | 印度需求真实且量大，但位次深（外链=0 的直接后果） |

### GA4（近 7 天）

- 活跃用户 21（持平），事件 115（+53%），**关键事件 0 —— generate_lead 仍无转化，且仍未被标记为关键事件**（Admin 事件列表里 lead 类事件全是 "No stream data detected"）
- **AI 引荐已出现**：chatgpt.com 1 + copilot.com 2（30 天口径 AI Assistant 14 个用户）——GEO 投入开始产生真实流量
- 内容阅读信号：mobile EV charging 文章 9 次浏览（+350%）、commercial cost 5 次、inquiry 页 3 次
- 国家：新加坡 10、美国 6、英国 2、约旦 1——约旦案例页在带真实地域流量

---

## 二、本周各角色产出

### 内容组 ✅（分支 `seo/week5-content`，**PR #4 待合并**）

| 文章 | 承接查询词 | 状态 |
|---|---|---|
| How Profitable Is an EV Charging Station Franchise? | p11.7 profit 词 + p25.7 主词簇 | 五件套齐全，validate 通过 |
| Fleet Depot Charging: Overnight AC or DC Fast | 32 展示最大词 + AC 安装成本词 | 同上 |
| Buying an Existing EV Charging Station: Due-Diligence | p33.5 business-for-sale / station contract | 同上 |

- 三篇均含：问题式 H1/H2、FAQ + FAQPage JSON-LD、署名、带来源统计、5 条相关内链
- blog hub 3 张新卡片置顶、计数刷新、verified 日期更新
- 顺手修复 3 个既有页面超长 title/meta（与迭代①并行撞车，rebase 时取 main 版本解决）
- `node validate.js` 86 页全绿；sitemap 重建 85 URL；Markdown 镜像 40/40

### Quora 社区组 ✅（3 条全部发布并验证）

| 问题 | 链接落地页 | 永久链接 |
|---|---|---|
| Is setting up an EV charging station business profitable and what is the cost? | /blog/ev-charging-station-franchise | …/answer/Kerry-Chu-8（见记忆文件） |
| How do you start an EV charging station business on your land? | /blog/charging-station-investment | 同上 |
| How much does it cost to install an EV charging station in a parking lot? | /blog/commercial-ev-charging-station-cost | 同上 |

均为 200+ 词原创 + 1 链接 + 利益披露句。Kerry Chu 账号累计 5 条回答。

### 外链组 ✅ 弹药已交付：`anari-outreach-week-1015.md`

- 存量 5 家媒体全部进入**终审跟进**（第 23 天，模板 D/E/F 备好，发完即归档）
- 目录收录复查清单（VUKA/EV Trade Show/EV4Life）+ **CharIN 询价列为最高优先**（拖了 3 周）
- 新增 10 家目标：FleetOwner、Fleet Maintenance、NGT News、pv magazine、Energy Storage News、Transport Topics、EV Charging Summit 演讲、CharIN webinar、国家 EV 协会、非洲 newsletter——角度从"新闻稿"转向"数据供稿"（配合本周文章主题）

### 引流组 ✅ 素材包：`anari-promo-pack-week5.md`（9 条）

- 每篇新文 3 条问答式素材（Quora 6 条可直接用 / Reddit 3 条储备）
- **Reddit 纪律**：账号满 23 天已过时间线，但 karma 未验证（Reddit 封 curl，需浏览器查）——karma <100 前 Reddit 素材只储备不发布

### 优化组 ✅ 复查结果

- ✅ **sitemap lastmod 已修复**（线上验证：真实日期分布，82 URL）——09-22 遗留问题关闭
- ✅ IndexNow 密钥文件在线（200）；历史提交通道正常
- ✅ 既有 PR #3（chore/sitemap-week4）已随分支删除自动关闭——**无需再处理**
- ⏸️ Week5 的 IndexNow 提交 + GSC 索引请求 + 部署后 validate：**等 PR #4 合并后立即执行**（GSC 索引每天 ≤5 个分批防限流）

---

## 三、下周（Week6）选题地图

| 优先级 | 选题 | 依据 |
|---|---|---|
| P0 | EV Charging Franchise Cost 支柱页刷新（扩 FAQ + 加 2026 各国费用表） | 25 展示 p25.7 主词，离首页最近的大流量词，强化比新写更值 |
| P0 | EV Charging Business Plan: Template + Real Numbers（lead magnet 换邮箱） | 09-22 选题图遗留 P1，直接服务 30 询盘目标 |
| P1 | EV Charging Franchise Kenya / East Africa | 差异化空白 + 22 国事实支撑 |
| P1 | Demand Charge 计算器工具页升级 | demand charge 词有展示（p63），工具页比文章转化强 |
| P2 | BESS Valuation Software 对比文 | p100 长尾但采购意图极高 |

---

## 四、用户待办清单（按优先级）

1. **合并 PR #4**（seo/week5-content）→ Cloudflare 自动部署 → 回我一声，我立即跑 IndexNow + GSC 分批索引 + 部署后 validate
2. **GA4 标记 generate_lead 为关键事件**（Admin → Events → 点星）——挂了三周，30 询盘目标的数据地基
3. **OpenSEO 余额已有 9,814 credits**（无需充值）——回复确认后我跑 franchise 词簇排名核查 + AIO 引用监测
4. **Reddit karma 验证**：打开 reddit.com/user/Sad-Researcher3564 看一眼 karma 数告诉我；≥100 下周开始发带链接帖
5. **外链邮件**（sales@ 手动发）：终审跟进 5 封（模板 D/E/F）+ 新发 7 封，全部在 anari-outreach-week-1015.md
6. **CharIN 会员询价**——权威背书最强的一项，已拖 3 周
7. 可选：Crunchbase 审核状态查看（09-22 提交的公司主页）

---

## 本周最重要的发现

**断更三周反而验证了内容策略：零运营期间 GSC 展示从零星涨到 413 次/28 天，franchise 词簇在 p8-26 形成真实的首页机会带，且 GA4 出现了 ChatGPT/Copilot 的 AI 引荐流量——内容资产在自己干活；但 0 询盘和印度词簇 p73-104 的深位次说明：没有外链权威性，单靠内容封顶就在这个区间，下周起外链邮件必须真正发出去。**
