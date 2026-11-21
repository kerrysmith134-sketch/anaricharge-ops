# Franchise 两篇 CTR 二轮改写素材包（观察中）

> 状态：**观察中**（用户 2026-10-23 晚确认转观察，勿重复触发）。问句式方向已由 PR #34（cdd639d，10-23 21:43）先行上线，本素材包不重复执行；推荐 A 总账数字留作后手。再评估时点：11-03 验收周快照——支柱页 CTR 仍 0% 且展示 ≥15 则提请用户确认后按推荐 A 执行；CTR >0.5% 则继续观察。
> 数据依据：2026-10-17 周报 + 10-19 查询词快照 + 周五验收快照（10-20）+ 10-23 晚判定（anari-1023-judgment.md）。

## 问题诊断

| 页面 | 展示 | 排名 | CTR | 现状 title |
|---|---|---|---|---|
| /blog/ev-charging-station-franchise | 12→20 | 12.1 | 0% | EV Charging Station Franchise Cost: $15k–$50k + 4–8% |
| /blog/ev-charging-station-franchise-profit | 26→35 | 12.5 | 0% | EV Charging Franchise Profit: Breakeven at ~15% Utilization |

- 排名都在 12 上下（二页顶部），问题不在排名在 **SERP 上的点击率**
- 查询词证据：高展示词几乎全是 **cost 意图**——"ev charging station franchise cost" 27 展示 p26、"ev charging station franchise" 16 展示 p55.7、"charging station franchise" 7 展示 p55.1
- 噪声词（不追）：tata/reliance/jio/adani 品牌加盟词，p80-100，我们是制造商打不了
- 10-19 第一轮数字前置改写后展示在涨（12→20、26→35）但 CTR 仍 0%，说明现在的数字组合不够"戳"——读者在 cost 意图下没看到你给他算总账

## 改写原则（基于两轮数据的教训）

1. **cost 意图要算总账**：第一轮的 "$15k–$50k + 4–8%" 只给了费率和区间，没给"开一家店总共要多少钱"这个总账数字——查询者真正想搜的答案
2. **profit 页要给绝对值**："Breakeven at ~15% Utilization" 是运营概念，不如直接给 "每站每年赚多少"
3. **保持数字前置**（已验证能拉展示），但数字要换成读者视角的"总账/实得"
4. 正文不动，只改 title + meta description

## 候选方案

### 页面 1：/blog/ev-charging-station-franchise（支柱页）

**推荐 A（总账数字）：**
- Title: `EV Charging Station Franchise Cost: $115k–$550k All-In (2026)`
- Meta: `Franchise fee $15k–$50k is only the start. All-in first-site cost runs $115k–$550k with equipment, install and 6 months of working capital. Full breakdown by country.`

**备选 B（双数字对照）：**
- Title: `EV Charging Franchise Costs: $15k–$50k Fee + $100k–$500k Setup`
- Meta: `What a charging station franchise really costs in 2026: franchise fee, equipment, install, royalties at 4–8%, and the 3 hidden line items brands don't mention.`

**备选 C（问句截获）：**
- Title: `How Much Does an EV Charging Station Franchise Cost? (2026)`
- Meta: `$15k–$50k franchise fee, $100k–$500k first site, 4–8% royalties for life. Real all-in numbers by country — and when turnkey beats the brand.`

### 页面 2：/blog/ev-charging-station-franchise-profit

**推荐 A（绝对收益数字）：**
- Title: `EV Charging Franchise Profit: $8k–$60k/Year per Site (Real Math)`
- Meta: `Gross margin 25–40%, net 10–20% after royalty and rent. See the per-site profit math for 1, 4 and 8 stalls — and the 3 traps that erase it.`

**备选 B（投资回收主导）：**
- Title: `EV Charging Franchise ROI: 2–4 Year Payback (If Utilization Holds)`
- Meta: `Per-site profit $8k–$60k/yr on $115k–$550k invested. The utilization math that decides your payback — and the breakeven traps most franchisees miss.`

**备选 C（疑问+数字）：**
- Title: `Is an EV Charging Franchise Profitable? $8k–$60k/Site/Year`
- Meta: `Yes — if utilization clears 15%. Real margin math: 25–40% gross, 10–20% net, 2–4 year payback. Includes the scenario table by stall count.`

## 执行清单（触发后照做，全程 kimi 可独立完成）

1. `cd ~/Documents/kimi/workspace/anaricharge-website && git checkout main && git pull`
2. 新建分支 `seo/week8-ctr-v2`
3. 改两个 HTML 的 `<title>` + meta description（用推荐 A；如周五数据显示 cost 词占比 >70% 且 India 词 >30% 再考虑 B/C）
4. `node validate.js` 本地过一遍
5. push → 浏览器 compare 页开 PR → Gatekeeper 自动合并部署
6. IndexNow 提交 2 URL（openseo 桥）
7. GSC 请求索引 2 URL（WebBridge，限额内）
8. 在 `anari-weekly-actions.json` 追加记录，观察窗口 7-14 天

## 注意事项

- 两篇是姊妹页，必须**同一 PR 一起改**（内链结构相关，分开改会互相抢 SERP）
- 若周五快照显示展示已涨到 50+ 且排名进前 10：先别改 title（排名波动期改 title 有风险），改为优化 meta 前半句
- 若已有 ≥1 点击（CTR >0.5%）：降级为只观察，改写取消
