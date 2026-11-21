# ANARI Charge 索引覆盖周复查报告（对比 10-15 基线）

- 站点：www.anaricharge.com（GSC 资源 sc-domain:anaricharge.com）
- 复查时间：2026-10-22 18:40–19:00（Asia/Shanghai）
- 基线：[anari-index-coverage-0923](/Users/kerrychu/Documents/kimi/workspace/anari-index-coverage-0923.md)（2026-10-15 诊断）
- 数据来源：GSC Pages 报告（WebBridge 操作已登录浏览器，只读），线上 curl 抽查
- 注意：Pages 报告有快照滞后（sitemap 标记 Last update 10/16/26），本周每日新发文章可能尚未全部入桶

## 一、总览对比

| 指标 | 10-15 基线 | 10-22 复查 | 变化 |
|---|---|---|---|
| Indexed | 27 | **37** | **+10** ✅ |
| Not indexed | 62 | 61 | -1 |
| └ Discovered – currently not indexed | 55 | **50** | **-5** ✅ 瓶颈松动 |
| └ Page with redirect | 7 | 9 | +2（均为正常，见下） |
| └ Crawled – currently not indexed | 0 | **2** | ⚠️ 新增，需关注 |
| 线上 sitemap URL 数 | 82 | **103** | +21（每日内容节奏起效） |

**结论：抓取预算瓶颈开始松动**——一周内 Google 多抓多收了 10 页，Discovered 桶 55→50。内链加固 + IndexNow + 每日更新的组合在起效。

## 二、week5 三篇文章专项核查（10-15 的 P0 遗留）

| URL | 10-15 状态 | 10-22 状态 |
|---|---|---|
| /blog/ev-charging-station-franchise-profit | 404（请求索引浪费） | ✅ **已被索引** |
| /blog/fleet-depot-charging-ac-vs-dc | 404（请求索引浪费） | ✅ **已被索引** |
| /blog/buy-existing-ev-charging-station | 404（请求索引浪费） | 线上 200、在 sitemap，但**报告四个桶都没有它**——快照滞后，预计下期报告出现 |

另外 10-15 请求的 /regulations/nevi-grant-application 也已被索引。上周的索引请求+IndexNow 提交全部生效。

## 三、新增关注项：Crawled – currently not indexed × 2

上周为 0，本周出现 2 页"抓了但不收"：

| URL | Last crawled | 判断 |
|---|---|---|
| /blog/transformer-upgrade-ev-charging | Oct 17, 2026 | 技术性选题，可能被认为与现有内容差异化不足 |
| /blog/ev-charging-franchise-kenya | Oct 17, 2026 | franchise 簇已有 4 篇收录（cost-india / profit / franchise / business-opportunity），肯尼亚篇与簇内主题重叠度高，疑被判同质 |

两篇线上均 200、均在 sitemap。**这不是技术故障，是 Google 的质量/增量价值判断。** 建议动作：

1. 观察 1–2 周——新页先拒后收很常见，尤其在新站信任积累期；
2. 从已收录的 franchise 簇文章（franchise-cost-india、franchise-profit）正文内互链这两篇，传递"被需要"信号；
3. 若两周后仍不收，再考虑给两篇补独家数据/案例段落，拉开与簇内文章的差异。

## 四、Page with redirect 9（+2，全部正常）

新增 2 条：/markets/kazakhstan.html（旧 .html，301 正确，其干净 URL 已被索引）和 https://anaricharge.com/（裸域 → www 规范化，Oct 12 抓取，完全正常）。其余 7 条为已知旧 .html URL，继续自然淘汰，无需处理。

/tools/bess-tco.html 的重复收录对仍在 indexed 列表里（与 /tools/bess-tco 并存），301 已生效，等自然合并。

## 五、Discovered 桶 50 页构成（全量提取）

| 分组 | 数量 | 典型 URL | 判断 |
|---|---|---|---|
| 博客文章 | 11 | charging-station-investment、ev-charging-grid-connection-cost、bess-600kwh 等 | 内容资产，优先推抓取 |
| 产品页 | 8 | /products/aquila、bess、castor、fora、gaia、pales、sena、vulco | 转化关键，优先 |
| 方案页 | 3 | /solutions/commercial-charging 等 3 个子页 | 商业价值最高 |
| 工具页 | 4 | /tools/、charger-selector、charging-station-roi、tco-calculator | 引流磁铁 |
| turnkey 页 | 5 | /turnkey/、anari-os、ai-growth、ai-site-selection | 中优先 |
| journey / markets / cases | 9 | journey/roi、markets/georgia、cases/jordan-160kw | 中优先 |
| regulations 子页 | 3 | /regulations/、eu-afir、us-nevi | 中优先 |
| 语言变体 /es/ /ru/ | 4 | /es/turnkey/、/es/who-we-serve/、/ru/turnkey/、/ru/who-we-serve/ | 低优先 |
| 其他 | 3 | /about、/academy/ocpp-2-0-1、/academy/pv-ess-charging、/privacy（4 取 3 列） | /about、/academy 建议修复；/privacy 可不索引 |

与基线相比移出 Discovered 的页（=被 Google 处理过）：/markets/kazakhstan（已索引）、/es/、/ru/（已索引）、week5 两篇（已索引）等 10 页；新进入的主要是本周新发内容。完整清单来自 GSC drilldown 逐页提取（50/50）。

## 六、下一步建议

1. **内链加固继续执行**（基线报告 Top 10 #2–#8 仍有效）：首页 + 已收录枢纽页 → 产品页、方案页、工具页，这是把 Discovered 50 推向抓取的最大可控杠杆。
2. **franchise 簇互链**：用已收录 4 篇带 transformer-upgrade 和 franchise-kenya 两篇被拒页。
3. **节奏保持**：每日内容 → sitemap 重建 → IndexNow 的流水线不变；新页发布次日再请求 GSC 索引（防限流）。
4. **下次复查**：10-29 同流程再跑，三个看点——buy-existing 是否入桶、被拒 2 篇是否转收、Discovered 是否降至 45 以下。

**一句话总结：索引数一周从 27 涨到 37、Discovered 桶开始下降，上周的 P0（week5 三篇 404）已全部救回，唯一新警报是 2 篇 franchise 簇新文被抓后拒收（同质化信号），靠簇内互链+观察应对即可。**
