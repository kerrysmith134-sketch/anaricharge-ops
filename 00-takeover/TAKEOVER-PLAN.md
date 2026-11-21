# 接管方案与执行日志

> 建立 2026-11-07。执行人：Lead（接管首班）。
> 对象：`/Users/kerrychu/Documents/kimi/workspace` 里的 anaricharge.com 运营体系。

---

## 一、问题的真实形状

用户说「文稿-kimi 文件夹里有一个运营 anaricharge.com 的工作流，打包了很多 skill」。
实测下来，它不是「一个工作流 + 一些 skill」，而是**四层东西叠在一起**：

| 层 | 内容 | 规模 |
|---|---|---|
| L1 技能层 | 5 个来源的营销技能库（Corey Haines 50 / SE Ranking 29 / Claude Marketing 30 / Superamped 18 / Eric Siu 9 / addyosmani 8） | 源目录 `.agents/skills` 137 目录，`.claude/skills` 另有 8 个独立技能 + 符号链接；550 文件 / 4.3MB |
| L2 编排层 | 6 个在岗角色 + 每日/周/月排期 + 20 次/周 agent 运行 | `营销团队v2-花名册与技能整合.md`、`anari-daily-ops-plan.md` |
| L3 工程层 | 静态站点（119 URL，三语）+ 40 个构建脚本 + Cloudflare Worker/D1/Brevo + PR Gatekeeper CI | `anari-new-site/`（主）、`anaricharge-website/`（旧克隆）、`agent-repos/` 6 个 |
| L4 记录层 | 60+ 份执行记录：日终简报、周报、索引核查、验收基线、plan.md 94–117KB 时间线 | 2026-07-20 → 2026-11-01 |

只接 L1 就会「有技能没流程」；只接 L2 就会「有流程没资产」；不接 L4 就会重复已踩过的坑。所以四层一起接。

---

## 二、约束（决定了产出形态）

1. **写沙箱只允许写 `/Users/kerrychu/anari-charge-website`**。原工作区一切操作只读（实测 `touch` 被内核拒绝：`Operation not permitted`）。
   → 因此接管形态是**镜像 + 规范化到新工作区**，而不是原地改造。原工作区继续作为事实来源，本工作区作为新操作台。
2. **不能碰用户账号与第三方后台**（继承 R6 硬规则）。
   → 需要浏览器/后台的操作一律写成「待用户处理」，不由 agent 代做。
3. **不能伪造**。所有「PASS」必须是真跑出来的退出码；所有数字必须是真拉出来的 API 响应。

---

## 三、方法：四线并行 + Lead 归并

| 线 | 责任人 | 写作用域 | 交付 |
|---|---|---|---|
| T1 技能层 | skill-porter | `02-skills/`、`01-inventory/skills-*`、`scripts/skill-*` | 迁移全部技能 + manifest + 合并映射 + 质量门 |
| T2 编排层 | workflow-architect | `03-workflows/`、`04-suites/`、`01-inventory/workflows-*`、`01-inventory/suites-*` | W1..Wn 可执行 SOP + 4 个套件 + 机器可读排期 |
| T3 记录层 | records-archivist | `05-records/`、`01-inventory/records-*` | 时间线/现状/未闭环/决策集/原始副本 |
| T4 工程层 | site-engineer | `06-site/`、`01-inventory/site-*` | 仓库镜像（同步 origin/main）+ 质量门真跑 + 运行手册 |
| 归并 | Lead | `00/07/08`、根目录、`scripts/` | 接管报告 + 优化方案 + **真实执行**（GSC/GA4/站点探活/验收裁定） |

写作用域互不重叠，四条线可并行无锁冲突。

---

## 四、侦察阶段的关键发现（改变方案的三件事）

### D1. 有两个站点仓库，且**都落后于线上**
- `anaricharge-website/`：HEAD `125dc18` 2026-10-26，sitemap 106 URL，108 HTML，37 博客
- `anari-new-site/`：HEAD `72a0d6c` 2026-10-28，sitemap 114 URL，116 HTML，39 博客，`plan.md` 117KB（比旧的多 23KB）
- **线上**：sitemap **119 URL**
→ 主源改为 `anari-new-site`，且镜像后必须 `git fetch` 到 `origin/main`，否则接管到的是一份过期工程。

### D2. 运营流水线**已经停摆约 6 天**
- 最后一次实质产出：**2026-11-01 05:39**（`anari-daily-ops-plan.md` 更新 + W9 D2/D3 选题大纲）
- 今天：**2026-11-07**
- 缺失：11-02 起全部日终简报、11-03 到期的验收五项读数、11-03 周一的周复盘与总编排、11-04/05/06 内容档期
→ 接管的第一件事不是「继续跑」，而是**补读数 + 重新对账 + 确认 11-01 之后是谁在动线上**。

### D3. 线上比所有本地记录多 5 篇文章
`fleet-electrification-business-plan` / `ev-charging-station-maintenance` / `ev-charging-station-insurance` / `ev-charging-station-feasibility-checklist` / `gas-station-ev-charging-retrofit`
→ 说明 11-01 之后**还有一条内容线在跑，但产出没落回这个工作区**。这条线必须向用户确认并收编，否则接管是残缺的。**这是本次接管的头号未闭环项。**

### D4. 原「看板」的数据口径是错的
原看板用查询词维度聚合。低流量站上 GSC 会匿名化大量查询，实测丢失 **60%+** 展示（查询维度 948 展示 vs 页面维度 2,388 展示）。
→ 接管后 KPI 一律用**页面维度 / 无维度总量**；查询维度只做选题参考。这一条已写进 `AGENTS.md`。

---

## 五、执行时间线（本班）

| 步骤 | 动作 | 结果 |
|---|---|---|
| 1 | 定位源目录（「文稿」= macOS 的 Documents） | `~/Documents/kimi/workspace` |
| 2 | 四层资产盘点 + 处置依据文档通读 | 137+8 技能 / 6 角色 / 119 URL / 60+ 记录 |
| 3 | 确认沙箱边界 | 工作区外只读，故采用镜像式接管 |
| 4 | 起 4 条并行线（T1–T4） | 各线独立写作用域 |
| 5 | Lead 侧侦察补充 | 发现 D1–D4 |
| 6 | 向 T3/T4 下发更正（主源变更、断档事实） | 避免按过期材料交付 |
| 7 | **真实执行**：GSC/GA4 API 实拉 + 119 URL 全量探活 + 验收五项裁定 | `08-execution/` |
| 8 | 归并四条线 + 写接管报告 + 优化方案 | 见 `00-takeover/TAKEOVER-REPORT.md` |
| 9 | 统一校验（数量对账、链接校验、可跑性） | 见 `00-takeover/VERIFICATION.md` |

---

## 六、判定「接管完成」的标准（我的验收口径）

1. **无遗漏**：源目录里每个技能目录、每份工作流文档、每类执行记录，都能在本工作区找到对应条目或明确的「不接管理由」。
2. **可执行**：`03-workflows/` 里每条 SOP 能照着跑；`scripts/` 里的脚本能重复执行；质量门真跑过。
3. **已优化**：技能的去重/合并/归档有明确映射（不是原样复制 137 份）；工作流有精简与自动化改造建议。
4. **已执行**：至少跑通一次真实的日终班次，产出真实数据，并对 11-03 验收给出可核验的裁定。
5. **留缺口**：说不出「还剩什么没接」，就不算诚实交付。缺口集中列在 `00-takeover/GAP-ANALYSIS.md`。

---

## 七、与用户的分工（不可代做项）

| 事项 | 为什么 agent 不能做 | 时长 |
|---|---|---|
| 确认 11-02 之后的运营线归属 | 需要用户知道谁在动 | 1 分钟 |
| Brevo 后台核对真实询盘数 | 禁止浏览器操作第三方后台（R6） | 1 分钟 |
| 授权 title/meta 改动上线 | 影响线上，需人工审核 | 5 分钟 |
| 验收口径重定（/products/、/inquiry） | 业务判断 | 2 分钟 |
| 外链邮件从 sales@anarienergy.com 发出 | 需人工账号发信 | 20 分钟/周 |
| 合并 PR | 需仓库权限 | 5 分钟/周 |
