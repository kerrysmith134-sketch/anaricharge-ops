# ANARI Charge 索引覆盖率诊断报告

- 站点：www.anaricharge.com（GSC 资源 sc-domain:anaricharge.com）
- 诊断时间：2026-10-15 17:40–18:10（Asia/Shanghai）
- 数据来源：GSC Pages 报告（Indexing → Pages）、Sitemaps 报告、线上 HTTP 抽查
- 诊断方式：WebBridge 操作已登录浏览器；只读诊断，未改任何代码与 GSC 设置

> 注意：GSC Pages 报告为快照数据（报告内 sitemap 标记 Last update 10/9/26），今天的手动索引请求尚未反映在下表数字中；Sitemaps 页为实时数据。

## 一、总览数字

| 指标 | 今早 | 本次读取 | 说明 |
|---|---|---|---|
| Indexed | 27 | 27 | 持平 |
| Not indexed | 52 | 62 | +10，原因是 Google 持续从 sitemap 发现新 URL（Discovered 桶变大），不是页面被取消索引 |

Not indexed 分类明细（共 3 类，其余类别不存在）：

| 分类 | 页面数 | 来源 | 性质判断 |
|---|---|---|---|
| Discovered – currently not indexed | 55 | Google systems | 主体问题：已发现但从未抓取（抓取预算/新站信任度） |
| Page with redirect | 7 | Website | 正常现象：旧 .html 结构 URL，301 到干净 URL（已逐一 curl 验证） |
| Crawled – currently not indexed | 0 | Google systems | 好消息：没有被"抓了但拒收"的质量问题页面 |
| Excluded by noindex / Not found (404) / Blocked by robots / Duplicate without canonical | 0 | — | 均不存在，技术卫生干净 |

## 二、各类别抽样与判断

### 1. Discovered – currently not indexed（55 页，首次检测 9/15/26）

抽样 URL 的 Last crawled 全部为 N/A（**Google 知道这些页面存在，但一次都没来抓取**）。全量 55 个 URL 已完整提取，构成如下：

| 分组 | 数量 | 典型 URL | 判断 |
|---|---|---|---|
| 博客文章（含本周前全部文章） | 11 | /blog/charging-station-investment、/blog/bess-600kwh-for-ev-charging、/blog/ev-charging-grid-connection-cost | 可修复：内容资产，优先 |
| 产品页 | 8 | /products/aquila、/products/bess、/products/vulco | 可修复：转化关键页，优先 |
| 方案页 | 3 | /solutions/commercial-charging、/solutions/pv-ess-charging-solution | 可修复：商业价值最高 |
| 工具页 | 4 | /tools/、/tools/charger-selector、/tools/tco-calculator | 可修复：引流磁铁（/tools/bess-tco 已索引） |
| turnkey 页 | 4 | /turnkey/anari-os、/turnkey/ai-site-selection | 可修复 |
| journey / markets / cases | 10 | /journey/roi、/markets/kenya、/cases/jordan-160kw | 可修复，中优先 |
| 语言变体 /es/ /ru/ | 8 | /es/、/ru/turnkey/ | 基本正常：小语种镜像，低优先 |
| 其他（/about、/privacy、/academy/* 等） | 7 | /about、/academy/ocpp-2-0-1 | /privacy 低价值可不索引；/about、/academy 建议修复 |

### 2. Page with redirect（7 页）— 全部正常

7 个全部是旧站 .html 结构 URL，curl 验证均 301 到对应的干净 URL：

| URL | 线上状态 |
|---|---|
| /who-we-serve/cpo-entrepreneurs.html | 301 → /who-we-serve/cpo-entrepreneurs |
| /who-we-serve/fleet-operators.html | 301 → 干净 URL |
| /who-we-serve/energy-real-estate.html | 301 → 干净 URL |
| /playbooks/commercial-charging-station-guide.html | 301 → 干净 URL |
| /journey/segment.html | 301 → /journey/segment |
| /solutions/fleet-depot-charging.html | 301 → 干净 URL |
| /cases/romania-highway.html | 301 → 干净 URL |

无需处理，GSC 会自动把它们从已知页面里淘汰。

### 3. Indexed（27 页）结构

收录主体是索引/落地页（/、/blog/、/products/、/solutions/、/tools/bess-tco 等，多在 10/2–10/9 抓取）+ 4 篇早起文章（franchise-cost-india、business-opportunity、commercial-cost、franchise）。一个瑕疵：**/tools/bess-tco.html（9/15 收录）与 /tools/bess-tco（10/9 收录）同时被索引**，构成重复对；.html 现已是 301，预计会自然合并，观察即可。

## 三、专项核查

### 3.1 今天请求索引的 6 个 URL（含 4 篇本周文章）

URL 检查工具今天不可用（深链 404、输入框拒绝 fill 与键盘输入，与 9/22 限流表现一致），按预案降级用 Pages 报告 + 线上 curl 核查：

| URL | 线上状态 | GSC 状态 | 判断 |
|---|---|---|---|
| /blog/buy-existing-ev-charging-station | **404** | 不在任何桶 | ⚠️ P0：页面未上线就请求了索引 |
| /blog/ev-charging-station-franchise-profit | **404** | 不在任何桶 | ⚠️ P0：同上 |
| /blog/fleet-depot-charging-ac-vs-dc | **404** | 不在任何桶 | ⚠️ P0：同上 |
| /regulations/nevi-grant-application | 200 | 尚未入桶（报告快照滞后） | 正常，等抓取 |
| 其余 2 个 URL | 未提供清单，无法逐一核对 | — | — |

**结论：3 篇 week5 文章（PR #4 seo/week5-content）尚未合并部署，线上返回 404，对它们发起的索引请求会被 Google 抓到 404 而浪费，并可能在下次报告产生 Not found (404) 记录。** 必须先合并部署、curl 验证 200 后再重新请求索引。nevi-grant-application 已上线且在 sitemap 内，等抓取即可。

### 3.2 Sitemap 发现覆盖

- sitemap.xml：9/15 提交，**今天（10/15）刚被读取**，状态 Success，Discovered pages = **82**，videos 0。
- 线上 sitemap 实测 82 个 URL，**curl 全量检查全部 200**，无死链。
- 账目完全对平：82（sitemap 发现）= 27（已索引）+ 55（已发现未抓取）；7 个重定向页为 sitemap 之外的旧 URL。
- **结论：sitemap 提交的页面 100% 被 Google 发现，瓶颈不在"发现"环节，在"抓取"环节。**

## 四、可修复 Top 10（按预期流量价值排序）

| # | 项目 | 影响页 | 修复动作 | 是否动代码 |
|---|---|---|---|---|
| 1 | week5 三篇文章 404（索引请求已浪费） | buy-existing / franchise-profit / fleet-depot | 合并 PR #4 → 确认部署成功 → curl 验证 200 → 重新分批请求索引（≤4-5 个/天）+ IndexNow | 否（合并/部署操作） |
| 2 | 方案页未被抓取 | /solutions/commercial-charging、/solutions/home-workplace-charging、/solutions/pv-ess-charging-solution | 从已索引的 /solutions/ 与首页加强内链（首页"Solutions"区块直连 3 个子页） | 是（模板内链） |
| 3 | 产品页未被抓取 | /products/aquila、bess、castor、fora、gaia、pales、sena、vulco | 确认 /products/ 索引页到各产品页有直链；首页加"Featured products"锚点链接 | 是（模板内链） |
| 4 | 高价值博客未被抓取 | charging-station-investment、ev-charging-grid-connection-cost、ev-charging-demand-charge-reduction、bess-600kwh、solar-bess-stacking | /blog/ 索引页置顶推荐位 + 已收录的 4 篇文章内互链 | 是（内容内链） |
| 5 | 工具页未被抓取 | /tools/charger-selector、/tools/charging-station-roi、/tools/tco-calculator | 已收录的 /tools/bess-tco 页面内加"相关工具"互链；博客文章内嵌工具链接 | 是（内容内链） |
| 6 | turnkey 系列未被抓取 | /turnkey/anari-os、/turnkey/ai-growth、/turnkey/ai-site-selection | /turnkey/ 与 /agents/（已收录）互链 | 是（模板内链） |
| 7 | 案例/市场页未被抓取 | /cases/jordan-160kw、/markets/georgia、kazakhstan、kenya、nepal | 已收录的 /cases/ 索引页与 /who-we-serve/* 互链 | 是（模板内链） |
| 8 | /about、/academy/* 未被抓取 | /about、/academy/ocpp-2-0-1、/academy/pv-ess-charging | 页脚导航已存在则确认可爬行；博客文末加 About/Academy 链接 | 是（模板内链） |
| 9 | .html 重复收录 | /tools/bess-tco.html | 301 已生效，无需动作；检查模板内是否还有指向 .html 的内链，有则改干净 URL | 是（仅当存在此类内链） |
| 10 | /es/、/ru/ 镜像未被抓取 | /es/、/es/agents/、/ru/、/ru/turnkey/ 等 8 页 | 低优先；主站收录起来后自然会带起，可暂缓 | 否 |

需要动代码的清单汇总（只做清单，未实施）：#2–#8 的内链加固（首页、/products/、/solutions/、/blog/、已收录文章的模板/正文内链），#9 的内链 .html 引用排查。

## 五、正常现象说明（无需处理）

- **Page with redirect × 7**：旧 .html URL，301 全部正确，属自然淘汰。
- **Not indexed 从 52 → 62**：不是恶化，是 Google 通过 sitemap 发现了更多 URL 进"已发现"队列；Indexed 稳定在 27。
- **Crawled – currently not indexed = 0**：没有被判"质量不足"的页面，内容质量层面无警报。
- **无 404 / noindex / robots 封禁 / canonical 冲突**：技术 SEO 卫生良好。
- **/privacy 未被索引**：低价值页面，不索引无影响。
- **今天请求的 6 个 URL 未出现在 Pages 报告**：报告快照滞后（10/9），叠加检查工具限流，属预期，2–3 天后再看。

## 六、下一步建议

1. **立即**：合并 PR #4 并确认 Cloudflare 部署成功，curl 验证 3 篇 week5 文章返回 200；随后 `node build-sitemap.js` 重建 sitemap、提交 IndexNow、明天起分批重新请求 GSC 索引（每天 ≤4-5 个，防限流）。
2. **本周**：按 Top 10 #2–#5 做一轮内链加固（首页 + 已收录枢纽页 → 55 个未抓取页中的高价值页），这是推动"Discovered→Crawled"最有效的可控杠杆。
3. **持续**：新文章发布流程保持 sitemap 重建 + IndexNow + 次日 GSC 索引请求的固定节奏；避免在页面未上线时请求索引。
4. **复查**：下周同一诊断流程再跑一次，重点看 Discovered 桶是否开始下降、3 篇 week5 文章是否入桶；若两周后 Discovered 仍不下降，再评估外链引流（Quora/Reddit）对抓取预算的拉动。

**一句话总结：站点技术卫生干净（0 抓取拒收/0 死链/重定向全对）、sitemap 82 页 100% 被发现，核心瓶颈是 55 个页面"已发现但从未抓取"的抓取预算问题，外加一个必须今天处理的 P0——3 篇 week5 文章在 404 状态下被请求了索引，先合并部署再重新提交。**
