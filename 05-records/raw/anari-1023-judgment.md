# ANARI 1023 晚间数据判断（验收分析员）

- 产出时间：2026-10-23 22:35 CST（Asia/Shanghai，UTC+8）
- 数据截止：今日 19:33 看板刷新（OpenSEO 桥回退口径）；PR #34 上线时间 21:43
- 背景：原定 20:37 一次性「数据解读（连接器破零 + CTR 触发判定）」任务漏跑（runs 为空，见 `anari-daily-summary-2026-10-23.md` §一），本文件为补跑产出

## 结论（3 行）

1. 连接器新文章：已上线（HTTP 200）、IndexNow 已受理（202）、GSC 已确认「Indexing requested」——今晚口径为「已请求索引、待明晚（10-24）20:07 复查验证」，今晚不做破零判定。
2. franchise CTR 触发：支柱页「109 展 / CTR 0%」字面满足触发条件，profit 页 CTR 已升至 1.5% 不满足；但今日 21:43 PR #34 已上线同方向（问句式）title 改写，v2 素材包不重复执行，转入 7–14 天观察。
3. 11-03 验收提前读数：5 项中 3 项达标（business-plan CTR 6.0%、/products/ p11.5、/inquiry 8 展示），剩余缺口集中在两篇 franchise 的 CTR。

## 一、收录加速状态（口径确认）

来源：`anari-index-submission-2026-10-23.md`（今日 12:25–12:40 执行）

| 项目 | 状态 |
| --- | --- |
| 新 URL | `https://www.anaricharge.com/blog/ccs1-vs-ccs2-nacs-connector-guide` |
| 上线确认 | HTTP 200（sitemap `<lastmod>2026-10-23</lastmod>`） |
| IndexNow | HTTP 202（Accepted，正常受理） |
| GSC 请求索引 | ✓ Indexing requested（按钮已变 REQUEST AGAIN），截图存档于 `gsc-screenshots/` |
| 复查报告 | workspace 内无 10-23 或更新的 `anari-index-verify-*.md`（已核实） |

**今晚口径：已请求索引、待明晚验证。** 收录复查任务已改至 10-24 晚 20:07 执行，今晚不等、不重试复查报告。

## 二、连接器破零判定

| 数据点 | 数值 | 来源 |
| --- | --- | --- |
| 连接器簇基线（近 28 天，10-22 13:53 导出） | 展示 0 / 点击 0 / 位次无 | `anari-connector-baseline-2026-10-22.md` |
| 今日中午连接器词展示（*ccs*/*connector*/*nacs* 筛选） | 展示 0 / 点击 0（符合预期） | `anari-index-submission-2026-10-23.md` §4 |

**判定：今晚不做破零判定。** 文章尚未收录，破零需等收录生效，最早看 10-24 晚复查。记录口径：「请求已受理，破零观察窗口从 10-24 晚开始」。后续里程碑（基线文件既定）：任一连接器簇词首次展示即破零；2 周内位次 ≤50；4 周内进 p20-40；10-29 前后重拉基线对比。

## 三、CTR 触发检查（franchise 两篇）

数据对照：10-20 周五验收快照（周窗 10-12~10-18）vs 10-23 19:33 看板读数（OpenSEO 桥回退）。

| 页面 | 10-20 快照 | 10-23 最新 | 触发条件核对 | 判定 |
| --- | --- | --- | --- | --- |
| /blog/ev-charging-station-franchise（支柱页） | 20 展 / 0 点击 / CTR 0% | **109 展 / 0 点击 / CTR 0%** | 展示 ≥15 ✓；CTR 仍 0% ✓ | **字面触发成立** |
| /blog/ev-charging-station-franchise-profit（profit 页） | 35 展 / 0 点击 / CTR 0% | CTR **1.5%**（展示数未单列；相关 top 词 12 展 p19.8） | CTR 仍 0% ✗ | **不触发**；且按素材包降级条款「CTR >0.5% 降级为只观察」应转观察 |

**关键修正项（实读仓库核实）**：PR #34（commit cdd639d，今日 21:43 合并）已上线——

- 支柱页 title：`EV Charging Station Franchise Cost: $15k–$50k + 4–8%` → `How Much Does an EV Charging Station Franchise Cost in 2026?`（即素材包**备选 C 问句式**方向）
- profit 页 title：`EV Charging Franchise Profit: Breakeven at ~15% Utilization` → `Is an EV Charging Station Franchise Profitable in 2026?`，meta 加 2026 年份（仅动 title/meta，未动正文）

**判定结论：v2 改写不重复触发。** 理由：① PR #34 已覆盖素材包问句式方向，当前线上 title 与素材包备选 C 实质一致；② 素材包注意事项明确「排名波动期改 title 有风险」，24 小时内二次改 title 不可取；③ 与素材包**推荐 A**（总账数字 $115k–$550k all-in / $8k–$60k/站/年）的差距仅为「title 未上绝对值数字」，留作后手。改写不执行；是否追加推荐 A 需用户确认（见动作清单）。

**观察口径**：窗口自 10-23（PR #34 上线）起算 7–14 天，恰覆盖 11-03 验收周；若验收周支柱页 CTR 仍为 0%，再评估按推荐 A 追加总账数字。

## 四、11-03 验收口径对照（提前读数）

| 指标 | 目标 | 10-20 快照（周窗 10-12~10-18） | 10-23 提前读数（19:33） | 状态变化 |
| --- | --- | --- | --- | --- |
| /blog/ev-charging-business-plan CTR | ≥3% | 9.1%（2/22）✅ | 6.0% ✅ | 达标，数值略降 |
| /blog/ev-charging-station-franchise-profit CTR | ≥3% | 0.0%（0/35）❌ | 1.5% ❌ | 点击破零，仍未达标 |
| /blog/ev-charging-station-franchise CTR | ≥3% | 0.0%（0/20）❌ | 0.0%（109 展 0 点击）❌ | 展示 5 倍级增长，点击仍 0 |
| /products/ 平均位次 | ≤前 15 | 21.2 ❌ | **p11.5 ✅** | 新达标（升约 10 位） |
| /inquiry 周展示 | >4 | 3 🟡 | **8 ✅** | 新达标 |

**达标数：1/5（10-20）→ 3/5（10-23）。** 全站 28 天盘面同步抬升：点击 12 / 展示 718（约为上期 4.3 倍）/ 收录页 47/71。

口径备注：10-23 读数走 OpenSEO 桥回退（本机到 Google 官方端点不可达），查询维度仅 top100，展示/点击为下限估计；且与 10-20 快照窗口口径不同（周窗 vs 看板 28 天），仅作趋势参考，正式验收以 GSC 官方口径为准。

## 五、建议动作清单

**需用户手动 / 确认：**

1. 【已确认 · 2026-10-23 晚】v2 处置口径：用户确认「转观察、11-03 验收周后再定是否按推荐 A 追加总账数字」；团队不擅自二次改写两篇 title。
2. 【已解决 · 2026-10-23 晚】内容验收员时限：经核实执行配置 timeoutMs 已为 5400000（90 分钟），用户确认口径与现状一致，无需重复修改。run 记录显示上限此前逐级上调（10-20/21 超时于 30 分钟 → 10-23 超时于 45 分钟 → 现已 90 分钟），10-24 10:43 班起按 90 分钟上限执行。

**团队可自动执行（无需用户操作）：**

1. 10-24 20:07 GSC 收录复查（8 URL 对照 + 连接器新文章，一次性任务，已在调度）。
2. 10-24 21:17 连接器复查简报推送（一次性任务，已在调度）。
3. 对 PR #34 的 2 个 franchise URL 补 IndexNow 提交 + GSC 请求索引，促使新 title 尽快被重新抓取（沿用今日中午已验证流程）。
4. 10-29 前后重拉连接器簇基线对比破零情况（基线文件既定动作）。
5. 明晚核查 20:07/21:17 两拍 runs 非空，防再次调度积压（今日 20:37 任务曾漏跑），可由巡检类任务覆盖。

## 合规红线确认

- 本文全部数据来自实读文件：`anari-index-submission-2026-10-23.md`、`anari-connector-baseline-2026-10-22.md`、`anari-gsc-snapshot-2026-10-20.md`、`anari-daily-summary-2026-10-23.md`、`anari-ctr-rewrite-v2-franchise-draft.md`，及仓库 commit cdd639d 实读 diff；无估数。
- 未改动任何仓库代码、未改动任何 GSC 设置。
- 公司事实口径保持「22 国 100+ 客户」，本文未涉及对外内容。
