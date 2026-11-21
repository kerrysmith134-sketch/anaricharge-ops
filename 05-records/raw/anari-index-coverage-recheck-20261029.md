# ANARI Charge 索引覆盖周复查报告（对比 10-22 基线）

- 站点：www.anaricharge.com（GSC 资源 sc-domain:anaricharge.com）
- 复查档位：2026-10-29 周四档（run 起于 10-29 22:17，中途浏览器通道中断，11-01 09:47 续跑完成；均为 Asia/Shanghai）
- 基线：[anari-index-coverage-recheck-20261022](/Users/kerrychu/Documents/kimi/workspace/anari-index-coverage-recheck-20261022.md)
- 数据来源：GSC Pages 报告（WebBridge 操作已登录 Edge，只读；数据快照 Last update 10/23/26）、URL Inspection API 单点核查、线上 curl、线上 sitemap
- 重要口径：GSC 数据截止 10/23，10-24 及以后发布的内容不可能出现在本次报告中，属预期而非异常

## 一、总览对比

| 指标 | 10-22 基线 | 本次（数据至 10/23） | 变化 |
|---|---|---|---|
| Indexed | 37 | **61** | **+24（+65%）** ✅ |
| Not indexed | 61 | 57 | -4 |
| └ Discovered – currently not indexed | 50 | **43** | **-7** ✅ 跨过 <45 阈值 |
| └ Page with redirect | 9 | 10 | +1（正常，见下） |
| └ Alternate page with proper canonical tag | 0（未出现） | 4 | 新桶，正常（见下） |
| └ Crawled – currently not indexed | 2 | **0** | ✅ 清零 |
| 线上 sitemap URL 数 | 103 | **117** | +14 |

**结论：收录爆发周。** 一周新增收录 24 页，被拒桶清零，Discovered 桶降至 43（低于周一复盘包设定的 45 阈值，内容线可按计划提速）。10-22 的 franchise 簇内链加固（PR #32）上线次日快照即显示两篇被拒文转入收录。

## 二、Plan B 观察档结论（10-29 档重点任务）

| URL | 10-22 状态 | 本次状态 | 结论 |
|---|---|---|---|
| /blog/transformer-upgrade-ev-charging | Crawled-not-indexed（10-17 抓） | ✅ **已被索引**（Indexed 列表在列） | 自愈/内链起效 |
| /blog/ev-charging-franchise-kenya | Crawled-not-indexed（10-17 抓） | ✅ **已被索引** | 自愈/内链起效 |

两篇线上均 200（11-01 curl 验证）。**本档按规则只记录、不动作。** 若 11-05 档两篇仍在收录中，Plan B（停放分支 seo/planb-diff-content-parked-1022）无需放行，届时在记忆文件标注「两篇均已自愈」即可。

## 三、基线待观察项核查

| 观察项 | 基线状态 | 本次状态 |
|---|---|---|
| /blog/buy-existing-ev-charging-station | 四桶均无（快照滞后） | ✅ **已被索引**（crawled Oct 20）。注：10-29 12:15 OpenSEO 桥查曾报 crawled-not-indexed，与 Pages 报告矛盾；11-01 经 URL Inspection API 实时复核确认为**已收录**，桥查结果为过期状态 |
| /blog/ev-charging-station-operating-cost | unknown | ✅ 已被索引（Oct 21） |
| /blog/charging-station-investment | Discovered | 仍在 Discovered 桶（未被抓取），继续观察 |
| /blog/workplace-ev-charging-cost-tax（D6，10-22 发布） | 未入桶 | sitemap 在列（lastmod 10-22）、线上 200，但尚未出现在任何桶——大概率错过 10/23 快照，列入下周观察 |

## 四、各分类明细

### 4.1 Page with redirect（10，+1）

全部正常，无需处理：

| URL | Last crawled | 说明 |
|---|---|---|
| /solutions/fleet-depot-charging.html | Sep 15 | **本周新进桶**，旧 .html → 干净 URL 301，干净版已收录（Oct 20） |
| /who-we-serve/fleet-operators.html | Oct 20 | 旧 .html，干净版已收录 |
| /cases/romania-highway.html | Oct 20 | 旧 .html，干净版已收录 |
| /journey/segment.html | Oct 20 | 旧 .html，干净版已收录 |
| /tools/bess-tco.html | Oct 16 | 旧 .html，干净版已收录 |
| /playbooks/commercial-charging-station-guide.html | Oct 16 | 旧 .html，干净版已收录 |
| /markets/kazakhstan.html | Oct 16 | 旧 .html，干净版已收录 |
| /who-we-serve/energy-real-estate.html | Oct 12 | 旧 .html，干净版已收录 |
| /who-we-serve/cpo-entrepreneurs.html | Oct 12 | 旧 .html，干净版已收录 |
| https://anaricharge.com/（裸域） | Oct 12 | 裸域 → www 规范化，正常 |

### 4.2 Alternate page with proper canonical tag（4，新出现）

First detected 10/24/26，均为 `/journey/segment?segment=*` 带参变体（engineering-contractor / cpo-entrepreneur / energy-real-estate / fleet），crawled Oct 23。这些参数页正确 canonical 到主 journey/segment 页（已收录），**是规范化的正常产物，不是错误**，无需处理。

### 4.3 Discovered – currently not indexed（43，-7）

全量 43 条（DOM 一次提取，与总数核对一致），分组：

| 分组 | 数量 | URL |
|---|---|---|
| 博客文章 | 8 | bess-600kwh-for-ev-charging、bess-peak-valley-arbitrage、charging-station-investment、charging-station-payback-period-roi-math、ev-charging-demand-charge-reduction、ev-charging-franchise-vs-turnkey、how-to-start-a-mobile-ev-charging-business、solar-bess-ev-charging-stacking |
| 产品页 | 5 | /products/bess、fora、gaia、pales、sena |
| 方案页 | 2 | /solutions/commercial-charging、home-workplace-charging |
| 工具页 | 3 | /tools/、charger-selector、tco-calculator |
| turnkey 页 | 4 | /turnkey/、ai-growth、ai-site-selection、anari-os |
| journey 页 | 5 | /journey/、blueprint、compliance、pv-ess-plan、roi |
| markets 页 | 4 | /markets/、georgia、kenya、nepal |
| regulations 页 | 3 | /regulations/、eu-afir、us-nevi |
| 语言变体 | 3 | /es/turnkey/、/es/who-we-serve/、/ru/turnkey/ |
| cases | 1 | /cases/jordan-160kw |
| academy | 2 | /academy/ocpp-2-0-1、pv-ess-charging |
| 其他 | 3 | /about、/privacy、/who-we-serve/engineering-contractors |

移出本桶（转入收录）的典型页：/products/aquila、castor、vulco，/tools/charging-station-roi，/solutions/、fleet-depot-charging，/blog/ev-charging-grid-connection-cost，/ru/who-we-serve/ 等——上周内链加固覆盖的枢纽页批量被处理。仍在桶内的 8 篇博客多为 10 月中旬发布的内容资产，是下一批抓取优先对象。

### 4.4 Indexed（61）构成速览

61 页全部提取核对。博客文章已收录 26 篇（全站博客 42 篇，收录率 62%）；产品页 4（aquila、castor、vulco + 索引页）；方案 3；工具 2；journey 3；who-we-serve 4；cases 3；playbooks 2；语言页 7（/es/ 3 + /ru/ 4）；其余为首页、inquiry、agents、academy、regulations、markets/kazakhstan 等。

## 五、本周新发文章入桶情况

| 文章 | 发布/lastmod | 本次报告 | 判断 |
|---|---|---|---|
| /blog/ccs1-vs-ccs2-nacs-connector-guide（D3 插队） | 10-23 | ✅ **已收录**（Oct 23 抓取） | 上线当日即收录，标杆速度 |
| /blog/ev-charging-station-site-selection（D7） | 10-24 | 未出现 | 晚于快照，预期 |
| /blog/buying-ev-chargers-from-china（D1） | 10-26 | 未出现 | 晚于快照，预期 |
| /blog/ev-charging-load-management（D2） | 10-27 | 未出现 | 晚于快照，预期 |
| /blog/fleet-electrification-business-plan（D3） | 10-28 | 未出现 | 晚于快照，预期 |
| /blog/ev-charging-station-maintenance（D4） | 10-29 | 未出现 | 晚于快照，预期 |
| /blog/ev-charging-station-insurance | 10-31 | 未出现 | 晚于快照，预期 |
| RU/ES 6 新页（products/solutions/vulco，PR #38） | 10-27 | 未出现 | 晚于快照，预期 |

以上 8 个关键 URL 全部 curl 200 验证通过。下周报告（数据预计至 10/30）是它们的首个检验点。

## 六、异常项判定

逐项核对：Indexed 周环比 **+24**（非下降）；Crawled-not-indexed 从 2 **清零**（无新增）；无新 404 / noindex / robots 封禁桶；基线待观察两项（被拒 2 篇、buy-existing）**全部解决**。

**本次复查无异常项。**

## 七、下一步建议

1. **内容线提速条件达成**：Discovered 43 < 45 阈值，按周一复盘包口径可提速；建议优先把桶内 8 篇博客 + 5 个产品页（bess/fora/gaia/pales/sena）纳入下一轮内链加固。
2. **11-05 档 Plan B 判定**：按规则复核两篇前拒文桶状态；若仍收录（大概率），在记忆文件标注「已自愈」并将停放分支保留备将来复用。
3. **下周观察清单**：workplace-ev-charging-cost-tax（10-22 发布未入桶，若下周仍无踪影需单点 API 核查）、10-24 之后发布的 7 篇新文章 + RU/ES 6 页是否入桶、charging-station-investment 是否被抓。
4. **经验固化**：OpenSEO 桥 inspect 可能返回过期状态，与 Pages 报告冲突时以 Pages 报告 + 官方 URL Inspection API 为准。

**一句话总结：收录从 37 暴涨到 61、被拒两篇全部转正、Discovered 跌破 45，10-22 的内链加固一周见效，本周零异常，内容线可以提速。**
