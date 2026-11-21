# ANARI Charge 内链加固清单（第二轮）— 2026-11-01

- 目标：把 Discovered 桶内 **8 篇博客 + 5 个产品页** 推向抓取
- 依据：10-29 档 GSC 复查（数据至 10/23），Discovered 43 全量清单 + Indexed 61 全量清单
- 原则（延续 PR #32 验证有效的打法）：
  1. **来源页必须已收录**（无权重的页传不出信号）——本清单 15 个来源页全部在 Indexed 61 内
  2. 每个来源页 1 条新内链（最多 2 条），插在正文相关段落，不做页脚堆链
  3. 锚文本用描述性英文短语（站点为英文），包含目标页核心词，不用 "click here"
  4. 共 18 条链接 / 15 个来源页 / 13 个目标页
- 注意：锚文本基于各页 title 与主题聚类设计，植入前编辑需扫一遍来源页正文，选语义最顺的段落落位

## Cluster A：BESS / 储能（5 个目标页）

| # | 来源页（已收录） | → 目标页（Discovered） | 建议锚文本 |
|---|---|---|---|
| A1 | /tools/bess-tco（BESS Peak-Valley TCO Calculator） | /blog/bess-peak-valley-arbitrage | the 2026 peak-valley arbitrage economics |
| A2 | /blog/bess-valuation-software（BESS Valuation Software） | /blog/bess-600kwh-for-ev-charging | sizing a 600 kWh BESS for EV charging stations |
| A3 | /solutions/pv-ess-charging-solution（PV+Storage+Charging Turnkey） | /blog/solar-bess-ev-charging-stacking | solar + BESS + EV charging revenue stacking |
| A4 | /blog/ev-charging-grid-connection-cost（Grid Connection Cost） | /blog/ev-charging-demand-charge-reduction | demand charge reduction strategies |
| A5 | /solutions/pv-ess-charging-solution | /products/bess | our liquid-cooled BESS (120–418 kWh) |

逻辑：工具页→经济学文章、估值软件→选型文章、方案页→堆叠收益文章+自家产品、电网成本→需量电费削减。

## Cluster B：投资 / 商业模型（4 个目标页）

| # | 来源页（已收录） | → 目标页（Discovered） | 建议锚文本 |
|---|---|---|---|
| B1 | /blog/ev-charging-station-franchise（Franchise Cost） | /blog/ev-charging-franchise-vs-turnkey | franchise vs turnkey: cost and control compared |
| B2 | /blog/ev-charging-station-franchise-profit（Franchise Profit） | /blog/charging-station-payback-period-roi-math | the payback-period math behind these numbers |
| B3 | /blog/buy-existing-ev-charging-station（Due-Diligence） | /blog/charging-station-investment | charging station investment from $3k to $250k+ by format |
| B4 | /blog/ev-charging-business-plan（Business Plan Template） | /blog/charging-station-investment | full investment breakdown by station format |
| B5 | /blog/ev-charging-business-case-template | /blog/charging-station-payback-period-roi-math | ROI math that survives investor scrutiny |
| B6 | /blog/electric-car-charging-stations-business-opportunity | /blog/how-to-start-a-mobile-ev-charging-business | starting a mobile EV charging business |

逻辑：franchise 簇（上周两篇自愈的功臣）继续外溢权重；投资测算三篇互成三角；mobile 创业文从 business-opportunity 引流。

## Cluster C：产品页（5 个目标页，bess 见 A5）

| # | 来源页（已收录） | → 目标页（Discovered） | 建议锚文本 |
|---|---|---|---|
| C1 | /products/vulco（60–480 kW DC for CPOs） | /products/fora | Fora split DC systems (360–960 kW) for turnkey hubs |
| C2 | /products/aquila（60–240 kW DC 广告屏） | /products/pales | Pales 60–240 kW DC chargers |
| C3 | /products/castor（20–40 kW DC Wallbox） | /products/gaia | Gaia AC chargers (7–22 kW) for destination charging |
| C4 | /blog/commercial-ac-charging-station-installation-cost | /products/gaia | Gaia 7–22 kW AC chargers |
| C5 | /blog/50kw-dc-charger-installation-cost | /products/pales | 60–240 kW DC chargers like Pales |
| C6 | /blog/dc-fast-charger-maintenance-cost | /products/fora | split DC architecture (Fora 360–960 kW) |
| C7 | /blog/electric-car-charging-stations-business-opportunity | /products/sena | portable chargers like Sena (3.5–7 kW) |

逻辑：已收录产品页兄弟互链（vulco→fora、aquila→pales、castor→gaia）+ 安装/运维成本博客按功率段对接对应产品 + 便携款从商业机会文引流。

## 执行流程（复用 PR #32 管线）

1. 站点仓库开分支 `seo/interlink-round2-1101`
2. 按上表在 15 个来源页正文植入 18 条内链
3. `node scripts/build-markdown-mirrors.js` → `node validate.js` 全绿
4. 推送建 PR → 合并
5. 合并后：curl 验证 15 个来源页 200 + 锚文本抽查 → IndexNow 提交 15 个来源页 URL（提交来源页而非目标页，让 Google 顺着新链接自己发现目标）
6. 下周（11-05 档）GSC 复查验收：13 个目标页是否进 Crawled/Indexed

## 验收标准

- 11-05 档：13 个目标页中 ≥5 个离开 Discovered（被抓或收录）即视为本轮起效
- 观察期为 2 周；11-12 仍纹丝不动的目标页，转入内容差异化评估（参照被拒两篇的处置路径）
