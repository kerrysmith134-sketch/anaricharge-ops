# 站点技术资产盘点（site-assets）

> 对象：`06-site/anari-new-site/`（origin/main `0f7d8a1`，2026-11-01，sitemap 119 URL）
> 状态标注：**live** = 线上真实可用 / **demo** = 本地演示态 / **planned** = 规划未实现

---

## 一、页面资产

| 板块 | HTML 页数 | 状态 | 说明 |
|---|---|---|---|
| `blog/` | 44 | live | 内容主力，最长尾承接面 |
| `products/` | 9 | live | 产品线页（Fora / Vulco / Pales / Castor / Aquila / Gaia / Sena / BESS / 索引） |
| `es/` | 8 | live | 西语核心页（5 核心 + inquiry + products + solutions） |
| `ru/` | 8 | live | 俄语核心页（同构） |
| `journey/` | 8 | **demo** | 交互漏斗，7 步方案构建器；后端 agent 为演示态，不产生真实计算 |
| `markets/` | 5 | live | 国别市场页 |
| `solutions/` | 5 | live | 方案页 |
| `tools/` | 5 | live | TCO 计算器 / 选型器 / BESS TCO / 充电站 ROI / 索引 |
| `who-we-serve/` | 5 | live | 客群页（CPO 创业者 / 车队 / 工程承包商 / 能源地产 / 索引） |
| `cases/` | **10** | live | 案例（3 篇原 + 6 篇专题 + 索引页；2026-11-07 两轮扩容） |
| `regulations/` | 4 | live | 法规（NEVI / AFIR 等） |
| `turnkey/` | 4 | live | 七模块交付 |
| `academy/` | 3 | live | 课程 |
| `playbooks/` | 2 | live | 手册 |
| `agents/` | 1 | live | 18 个 AI agent 生态 |
| `apps/` | 1 | live（**robots Disallow**） | vendored 计算器 SPA |
| 根页面 | 5 | live | index / about / inquiry / privacy / 404 |
| **合计** | **121 HTML / sitemap 119** | | 404 与 apps/ 不入 sitemap |

---

### 案例图片资产（2026-11-07 新增）
| 文件 | 内容 | 主图 / 640w |
|---|---|---|
| `israel-hot-climate.webp` | 以色列热气候现场 | 116KB / 59KB |
| `georgia-mall-240kw.webp` | 乔治亚商场 240kW | 54KB / 32KB |
| `czechia-cpo-bulk-delivery.webp` | 捷克 CPO 批量交付 | 51KB / 30KB |
| `czechia-bus-depot.webp` | 捷克公交场站 12 台 | 59KB / 24KB |
| `bulgaria-parking.webp` | 保加利亚停车场 | 54KB / 26KB |
| `ethiopia-180kw.webp` | 埃塞俄比亚现场调试 | 71KB / 34KB |
| `kazakhstan-120kw.webp` | 哈萨克斯坦双枪 120kW | 113KB / 46KB |

> 来源：anariev.com `/category/cases/`。另有 3 张 LinkedIn 案例数据卡归档在 `08-execution/materials/cases/`（只做事实来源，不进照片网格）。

## 二、脚本资产（`scripts/` 15 个 + 根 4 个）

| 脚本 | 作用 | 状态 |
|---|---|---|
| `validate.js` | 页面契约门禁（单 h1 / 死链 / FAQ schema / canonical） | live，120 页 PASSED |
| `build-sitemap.js` | 生成 sitemap.xml + sitemap.md（三级 lastmod 回退） | live |
| `scripts/check-facts.js` | 事实库一致性门禁 | live，60 一致 / 0 不一致 |
| `scripts/build-markdown-mirrors.js` | 每页 `.md` 镜像 | live（**Gatekeeper 白名单坑见 RUNBOOK**） |
| `scripts/build-llms-full.js` | llms-full.txt 全文汇总 | live |
| `scripts/build-og-images.js` | OG 社交图 | live |
| `scripts/build-responsive-images.js` | 响应式图片 | live |
| `scripts/site-fixes.js` | 幂等批量修复（`--dry` 预览） | live |
| `scripts/meta-length-scan.js` | title/meta 长度扫描 | live |
| `scripts/inject-ga4.js` / `inject-gtm.js` | GA4 / GTM 注入 | live |
| `scripts/dev-server.js` | 本地预览 | live |
| `scripts/add-lang-switch.py` / `finalize-bilingual.js` | 语言切换器注入 | live |
| `scripts/migrate-extensionless-urls.js` | URL 形态迁移 | 一次性 |
| `scripts/sync-agents.sh` | agent 产物同步 | live |
| `scripts/strip-app-gtm.js` | 剥离 apps/ 的 GTM | 一次性 |
| `update-brand.js` | 品牌资产更新 | 一次性 |

---

## 三、后端资产（`workers/`）

| 项 | 值 | 状态 |
|---|---|---|
| Worker | `anari-leads`（`workers/leads-worker.js`） | **live**，v2 已于 2026-10-22 部署 |
| 路由 | `api.anaricharge.com/*`（zone `anaricharge.com`） | live |
| D1 | `anari-leads`，binding `DB`，id `8af713d2-a27b-45f7-b5ba-75467600d427`（WNAM） | live |
| 表 | `submissions`（18 列）、`suppressions`、`audit_log` | live（#23 数据治理已于 2026-10-28 实装） |
| Secrets | `BREVO_API_KEY`（受限 key，2027-10-22 到期）、`IP_HASH_SECRET` | 已写入，不在仓库 |
| 安全 | Origin 白名单 / 蜜罐 / IP 限流（第 6 次 429）/ UUID 校验 / 幂等三层 | live |
| 健康检查 | `curl api.anaricharge.com/health` → **403 属正常**（无 Origin 头被白名单拦） | live |

---

## 四、外部依赖与账号

| 服务 | 用途 | 状态 |
|---|---|---|
| Cloudflare Pages | 静态托管 + CDN + 自动部署 | live |
| Cloudflare Worker + D1 | 询盘中继 | live |
| Cloudflare DNS / SSL | 域名、证书、Redirect Rule | live（**http→https 未生效，见技术发现 F1**） |
| Google Analytics 4 | `G-MT63H5Q8EV`（property `553998974`） | live |
| Google Tag Manager | `GTM-MRHHMP62` | live |
| Google Search Console | `sc-domain:anaricharge.com` | live（API 直连可用） |
| Brevo | List 3「Inquiry Nurture」+ 7 个 `ANARI_*` 属性 | live |
| HubSpot | 销售侧 CRM | **planned**（交接桥未建） |
| Web3Forms | 表单主投递 → sales@anarienergy.com | live |
| IndexNow | Bing/Yandex 秒级收录 | live（key 文件 2 个） |
| GitHub | `kerrysmith134-sketch/anaricharge-website` | live，PR Gatekeeper 自动合并 |

---

## 五、自动化资产（`.github/workflows/`）

| 工作流 | 触发 | 做什么 | 状态 |
|---|---|---|---|
| `pr-gatekeeper.yml` | `pull_request`（分支名 `seo/` `content/` `chore/` `docs/` `week` 开头） | rebase → 重建生成物 → `validate.js` → `check-facts.js` → 风险分级（内容类白名单）→ squash 合并 → 删分支 | live，已实战合并 40+ PR |

---

## 六、文档资产（`ops/` 38 项）

关键文档：`fact-library.json`（事实库单一来源）、`system-capabilities.json`（live/demo/planned 目录）、`audit-checklist-20261022.md`（36 项对账）、`attribution-model.md`（归因三期）、`gtm-event-setup.md`、`worker-deploy.md`、`cloudflare-deploy.md`、`deployment-guide.md`、`design-benchmark-sop.md`、`retro-2026-09.md`、`growth-plan-2026-09.md`、`TEMPLATE`/`AGENTS` 契约。

---

## 七、技术资产健康度（2026-11-07 实测）

| 项 | 结果 |
|---|---|
| 线上 119 URL 全量探活 | **119/119 = 200** |
| 索引覆盖（24 个关键 URL 抽样） | 23 indexed / **1 unknown to Google** |
| 页面契约门禁 | PASSED 120 页，EXIT 0 |
| 事实库门禁 | PASS 60 一致 / 2 未覆盖 / 0 不一致，EXIT 0 |
| 明文 HTTP | ❌ **200 直出，未跳 https**（P0，需 Cloudflare 开关） |
| 仓库同步 | ✅ 镜像已到 origin/main `0f7d8a1` = 线上 119 |
