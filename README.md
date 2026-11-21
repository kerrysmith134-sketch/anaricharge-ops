# ANARI 运营体系 — 接管工作区

> 从 `~/Documents/kimi/workspace` 接管 anaricharge.com 的全部运营工作流、技能库、套件与执行记录。
> 接管完成时间：2026-11-07 · 执行：Lead + 4 条并行线（技能 / 工作流 / 记录 / 站点）

---

## 30 秒结论

1. **接的东西比你说的「一个工作流 + 一些 skill」大得多**：是四层叠在一起——146 个技能 / 6 个在岗角色 + 25 个定时档 / 119 个线上页面 + 40 个构建脚本 + Cloudflare Worker / 60+ 份执行记录与一条 71 小节的 4 个月时间线。
2. **原工作区对本会话只读**（沙箱限制），所以接管形态是「镜像 + 规范化到本目录」，不是原地改造。回写工具已备好：`scripts/sync-back.sh`。
3. **最重要的发现：运营在 2026-11-01 已经整体停摆，到今天 6 天没人发现。** 本地零产出、线上零改动的同一天。没有心跳机制。
4. **第二个发现：效率全在「分发与点击」，不在「内容产能」。** 4 个月产出 44 篇博客 / 119 页，28 天只换来 27 次点击；而 8 个页面有 872 次展示却 0 点击——改这 8 个标题的收益是再写 8 篇新文的 5 倍。
5. **第三个发现（新，历史从未记录）：全站可明文 HTTP 访问且不跳转。** GSC 里 35 个页面行是 `http://` 版本，重复内容稀释。**已修**（Cloudflare Always Use HTTPS 已开，`http://` 现在 301）。

> **第二轮**：停摆根因确认为 **Kimi 额度耗尽**；HTTP 重复内容**已修好**；3 页 title/meta 已推送；**浏览器自动化已恢复**（Quora/Reddit/Brevo）。
> **第三轮**：建站队列 #16 收尾（2 页偏差补齐）；从 **anariev.com 案例区 + LinkedIn 官方页**取到 **7 张真实安装现场照 + 3 张案例数据卡**，案例页新增「In the field」画廊，柬埔寨补 17 台/3,040 kW 硬数据。
> **第四轮**：案例页扩容 —— 新增 **3 个专题案例页**（热气候 / 极寒 / 公交场站），内容全部提炼自 anariev 20 篇源案例，配套数据驱动生成器；站内案例 3→6。
> **第五轮**：再增 **3 个专题案例页**（22kW AC 五国 / 离网 PV+ESS / 新兴市场）+ **RU/ES 本地化案例中心页**，三语 hreflang 闭环；站内案例 6→9，anariev 20 篇源案例覆盖 19 篇。
> **第六轮**：补齐 **AI 可读层** —— 9 个案例页全部生成 `.md` 镜像、`llms-full.txt` 从 81→87 页、`llms.txt` 案例区扩写、转换器修两处瑕疵并全量重生成。
> **第十五轮**：**建队**——8 个 Pod 编制、`north_star.py` 单一度量主干、9 个营销作战级 skill、排期 12→19 档；同时用数学算清目标：**10 万/月在 90 天不可达（需 12.5万–100万页），可达的是 3 个月末 2,000–5,000 访问 + 8–15 询盘**，且当前瓶颈在转化不在流量。详见 [03-workflows/TARGETS.md](03-workflows/TARGETS.md) 与 [03-workflows/TEAM-V2.md](03-workflows/TEAM-V2.md)。
> **第十四轮**：营销外联分两波定稿并**全部开放送**——WAVE1 首触 4 家（11-10）、WAVE2 二触 7 家（11-11，10 月联系过的那批改写「承认角度错+给数据集」）；剔除 Fleet Maintenance 通知箱。详见 [08-execution/2026-11-07-round14-two-wave-outreach-copy.md](08-execution/2026-11-07-round14-two-wave-outreach-copy.md)。
> **第十三轮**：盘点三家付费 API 额度（**Hunter 0/50、Snovio 0、Apollo 无额度**）→ 转攻免费路径，邮箱覆盖提到 **12/17**、0 次付费调用；脚本加「先查余额再调用」。详见 [08-execution/2026-11-07-round13-enrichment-budget-and-12of17.md](08-execution/2026-11-07-round13-enrichment-budget-and-12of17.md)。
> **第十二轮**：**营销外联已开放送**（`MKT-OUTREACH-PR-2026H2`，日上限 5、3 步序列、首批 3 家媒体）；新建 **`email-enrichment` skill**（公开优先、付费兜底），首轮纯公开层把邮箱覆盖率从 3/17 提到 10/17、0 次付费调用。详见 [08-execution/2026-11-07-round12-marketing-send-and-enrichment.md](08-execution/2026-11-07-round12-marketing-send-and-enrichment.md)。
> **第十轮**：**营销外联线新建**（与 SDR 销售外联合并会酿错，已彻底分开）：Instantly 建 `MKT-OUTREACH-PR-2026H2`（草稿）、17 个媒体目标入台账、独立脚本与定时档；Quora 首答已发布并三证验证。详见 [03-workflows/OUTBOUND-LINES.md](03-workflows/OUTBOUND-LINES.md) 与 [08-execution/2026-11-07-round10-quora-instantly.md](08-execution/2026-11-07-round10-quora-instantly.md)。
> **第九轮**：**GSC 打通**（上次是我参数没编码）——已为 41 天未收录页成功提交索引请求；**Instantly 接入**（5 个邮箱各 30 封/天，集成脚本就绪，待 API Key）；Quora 已选题备稿待发布授权。详见 [08-execution/2026-11-07-round9-gsc-instantly-quora.md](08-execution/2026-11-07-round9-gsc-instantly-quora.md)。
> **第八轮**：清理 24 个历史浏览器标签并立 **R10 浏览器卫生**规则；GTM/GA4 登录态确认 + 出**字段级配置规格**（控制台挡合成事件，已给两条路径）；澄清 Quora/GSC/Instantly 的前置条件。详见 [08-execution/2026-11-07-round8-browser-hygiene-and-gtm.md](08-execution/2026-11-07-round8-browser-hygiene-and-gtm.md)。
> **第七轮**：**虚拟团队自动化落地** —— 用定时任务重建 12 档排期（编排/内容/内容检查/外链/社媒/内链/看板/日报/询盘）；拆出 chore 分支让内容 PR 恢复全自动合并；完成 RU·ES 案例镜像、llms 分片（8 个板块文件）。详见 [08-execution/2026-11-07-round7-automation-and-final-3.md](08-execution/2026-11-07-round7-automation-and-final-3.md) 与 [03-workflows/AUTOMATION-ARCHITECTURE.md](03-workflows/AUTOMATION-ARCHITECTURE.md)。

---

## 从这里开始读

| 你想知道 | 打开 |
|---|---|
| 接管了什么、怎么接的、判定标准 | [00-takeover/TAKEOVER-PLAN.md](00-takeover/TAKEOVER-PLAN.md) |
| 接管结果与关键发现（**建议先读这份**） | [00-takeover/TAKEOVER-REPORT.md](00-takeover/TAKEOVER-REPORT.md) |
| 还有哪些没接、哪些卡在人手上 | [00-takeover/GAP-ANALYSIS.md](00-takeover/GAP-ANALYSIS.md) |
| 机器的自动校验结果（**PASS 33 / FAIL 0 / WARN 0**） | [00-takeover/VERIFICATION.md](00-takeover/VERIFICATION.md) |
| **今天实际跑的运营班次（真实数据）** | [08-execution/2026-11-07-daily-run.md](08-execution/2026-11-07-daily-run.md) |
| 11-03 验收五项的真实裁定 | 同上「二、验收五项裁定」 |
| 技术面新发现（HTTP 重复内容等） | [08-execution/TECH-FINDINGS-20261107.md](08-execution/TECH-FINDINGS-20261107.md) |
| 第二轮落地（HTTP 已修/标题已推/浏览器已恢复） | [08-execution/2026-11-07-round2-user-feedback.md](08-execution/2026-11-07-round2-user-feedback.md) |
| 第三轮落地（网站升级 + 案例图片） | [08-execution/2026-11-07-round3-site-upgrade-and-images.md](08-execution/2026-11-07-round3-site-upgrade-and-images.md) |
| 第四轮落地（3 个专题案例页） | [08-execution/2026-11-07-round4-case-pages.md](08-execution/2026-11-07-round4-case-pages.md) |
| 第五轮落地（再 3 页 + RU/ES 中心页） | [08-execution/2026-11-07-round5-more-cases-and-i18n.md](08-execution/2026-11-07-round5-more-cases-and-i18n.md) |
| 第六轮落地（AI 可读层 .md 镜像） | [08-execution/2026-11-07-round6-agent-readability.md](08-execution/2026-11-07-round6-agent-readability.md) |
| 第七轮落地（12 档自动化 + llms 分片） | [08-execution/2026-11-07-round7-automation-and-final-3.md](08-execution/2026-11-07-round7-automation-and-final-3.md) |
| **自动化架构（虚拟团队三层）** | [03-workflows/AUTOMATION-ARCHITECTURE.md](03-workflows/AUTOMATION-ARCHITECTURE.md) |
| 案例图片素材与来源清单 | [08-execution/materials/cases/SOURCES.md](08-execution/materials/cases/SOURCES.md) |
| 浏览器自动化能力与坑 | [00-takeover/BROWSER-CAPABILITY.md](00-takeover/BROWSER-CAPABILITY.md) |
| 优化建议（按 ROI 排序） | [07-optimization/OPTIMIZATION.md](07-optimization/OPTIMIZATION.md) |
| 给后续 agent 的运行契约 | [AGENTS.md](AGENTS.md) |
| 146 个技能的去向 | [02-skills/_MERGE-MAP.md](02-skills/_MERGE-MAP.md) |
| 21 个工作流 SOP | [03-workflows/_INDEX.md](03-workflows/_INDEX.md) |
| 6 个套件 | [04-suites/_INDEX.md](04-suites/_INDEX.md) |
| 4 个月执行时间线（123 条） | [05-records/timeline.md](05-records/timeline.md) |
| 站怎么跑、怎么部署 | [06-site/RUNBOOK.md](06-site/RUNBOOK.md) |

---

## 目录结构

```
00-takeover/      接管方案 / 报告 / 缺口分析 / 自动校验
01-inventory/     资产盘点（技能·工作流·套件·记录·站点）
02-skills/        146 个规范化技能（_manifest.json + _MERGE-MAP.md）
03-workflows/     21 个可执行 SOP + _SCHEDULE.json（25 档 + 4 类事件驱动）
04-suites/        6 个套件（一条命令启动的编排）
05-records/       时间线 123 条 / 现状 / 未闭环 37 项 / 决策 53 条 + 61 份原始快照
06-site/          站点工程镜像（主源 anari-new-site + agent 子仓库 + 运行手册）
07-optimization/  优化方案
08-execution/     接管首班的真实执行产出
scripts/          可复跑脚本
```

---

## 可复跑的脚本

```bash
# 拉真实 GSC/GA4 数据（官方 API，只读凭证）
python3 scripts/gsc_pull.py --start 2026-10-10 --end 2026-11-06 --out 08-execution/gsc.json

# 全站索引覆盖审计（GSC URL Inspection API）
python3 scripts/index_coverage.py --sitemap /tmp/sitemap.xml --out 08-execution/index.json

# 零点击 / 低 CTR 页面诊断（选题与改标题用）
python3 scripts/ctr_diagnose.py --days 28
python3 scripts/ctr_diagnose.py --page /blog/nevi-grants-ev-charging-station

# 流水线存活检查（这条本该拦住 6 天停摆）
python3 scripts/heartbeat.py            # 超 48h 非零退出

# 接管完整性校验
python3 scripts/verify-takeover.py

# 把接管成果回写原 Kimi 工作区（默认 dry-run，需 --apply）
bash scripts/sync-back.sh
```

---

## 你的 5 分钟清单

按影响排序，前三条不做，接管就等于没交付：

1. **按顺序合并**（先 chore 手动一次，其余三个自动）：
   1. **手动**合 `chore/mirror-generator-and-gatekeeper` —— https://github.com/kerrysmith134-sketch/anaricharge-website/pull/new/chore/mirror-generator-and-gatekeeper
   2. 然后开这三个 PR（自动合并）：
   - 标题修复：https://github.com/kerrysmith134-sketch/anaricharge-website/pull/new/seo/ctr-title-meta-20261107
   - 客群页收尾：https://github.com/kerrysmith134-sketch/anaricharge-website/pull/new/seo/who-we-serve-20261107
   - **案例图片 + 6 个专题案例页 + RU/ES 中心页 + AI 可读层**（分支 `895e2f5`，**含 scripts 改动，需手动合并**）：https://github.com/kerrysmith134-sketch/anaricharge-website/pull/new/seo/cases-field-images-20261107
2. ~~Cloudflare Always Use HTTPS~~ **✅ 已由我修好**，`http://anaricharge.com/` 现在返回 301。
3. ~~授权改标题~~ **✅ 已改并过双门禁**（validate 120 页 / check-facts 0 不一致）。
4. ~~Brevo 核对真实询盘~~ **✅ 已用浏览器自动化查明**：全库只有 1 个联系人（内部地址），**0 真实询盘**。
5. **确认额度预算**：这次停摆是 Kimi 额度耗尽。要重启日更，建议先定「每周多少档」，我按这个改 `_SCHEDULE.json`。
