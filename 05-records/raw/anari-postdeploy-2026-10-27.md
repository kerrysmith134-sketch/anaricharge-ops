# Anari Charge 发布后验收报告 — 2026-10-27（周二）

验收时间：2026-10-27 15:47–15:55 (CST, UTC+8)
验收人：发布后验收员（自动化）
对应迭代任务：automation_a4a80c7e（每周二 14:17）

## 1. 迭代 commit 列表（今天新增）

| Commit | 时间 | 内容 |
|---|---|---|
| af38ce0 | 2026-10-27 10:58 +0800 | content(seo): Week8 D1+D2 — buying-ev-chargers-from-china + ev-charging-load-management (#37) |

变更文件：
- 新增 `site/blog/buying-ev-chargers-from-china.html/.md`
- 新增 `site/blog/ev-charging-load-management.html/.md`
- 更新 `site/blog/index.html`（博客列表收录两篇新文）
- 更新 `site/sitemap.xml`、`site/sitemap.md`、`site/llms-full.txt`

⚠️ 注意：今日计划主题为「RU/ES 多语言扩页」，但实际产出为两篇英文 SEO 博客（Week8 D1+D2）。报告中如实记录偏差；RU/ES 扩页未在本次提交中出现，列为遗留项，由迭代团队说明。

## 2. 复查结果

### 门禁（本地）
- `node validate.js`：**PASSED** — 109 页，单 h1、无死链、FAQ schema 与可见文案一致、结构化数据 canonical 正确。

### 新增/变更 URL（来自 sitemap diff）
| URL | 类型 | lastmod |
|---|---|---|
| https://www.anaricharge.com/blog/buying-ev-chargers-from-china | 新增 | 2026-10-26 |
| https://www.anaricharge.com/blog/ev-charging-load-management | 新增 | 2026-10-27 |
| https://www.anaricharge.com/blog/ | 变更（列表页收录新文） | — |
| https://www.anaricharge.com/who-we-serve/fleet-operators | 变更（lastmod 2026-09-19 → 2026-10-26，昨日内容重构由本次门禁重生成确认） | 2026-10-26 |

### 线上抽验（curl -s / -sI）
| URL | 状态码 | 标题/备注 |
|---|---|---|
| /blog/buying-ev-chargers-from-china | 200 | ✅ "Buying EV Chargers from China: 2026 Sourcing Guide" |
| /blog/ev-charging-load-management | 200 | ✅ "EV Charging Load Management: Dynamic Power Sharing 2026" |
| /blog/ | 200 | ✅ |
| /who-we-serve/fleet-operators | 200 | ✅ |
| /sitemap.xml | 200 | ✅ 线上已含两个新博客 URL |

Cloudflare 自动部署已生效，线上与 origin/main 一致。

## 3. 索引提交结果

### IndexNow ✅
- key 文件在线验证：200（https://www.anaricharge.com/07a4fc3586fd43710c5ea08299d05c43.txt）
- POST https://api.indexnow.org/indexnow → **HTTP 200**，一次提交 4 条：
  1. https://www.anaricharge.com/blog/buying-ev-chargers-from-china
  2. https://www.anaricharge.com/blog/ev-charging-load-management
  3. https://www.anaricharge.com/blog/
  4. https://www.anaricharge.com/who-we-serve/fleet-operators

### GSC ✅（2026-11-01 补投完成）
- 10-27 当天 `curl -sI --max-time 10 https://search.google.com` → 000 不可达（本机已知问题）。
- **2026-11-01 11:24 补投**：连通性恢复（301），通过 WebBridge 在用户已登录的 GSC（sc-domain:anaricharge.com，kerry@anaricharge.com）做网址检查 → 请求编入索引：
  1. `/blog/buying-ev-chargers-from-china` — 状态「URL is not on Google / Discovered – currently not indexed」→ **Indexing requested** ✅
  2. `/blog/ev-charging-load-management` — 状态「URL is not on Google」→ **Indexing requested** ✅
  3. `/blog/` — 已在 Google 收录中，重新 **Indexing requested** ✅（刷新抓取）
- 浏览器操作共约 21 步，已关闭标签组。
- `/who-we-serve/fleet-operators` — 已于 **2026-11-01 11:33 补投**：已在 Google 收录中，重新 **Indexing requested** ✅（4 条 URL 至此全部完成 GSC 提交）。

## 4. 遗留项

1. ~~GSC 补投~~：**已于 2026-11-01 全部完成**（4/4 条 Indexing requested，见上节），此遗留项关闭。
2. **RU/ES 扩页偏差**：今日迭代计划主题为 RU/ES 多语言扩页，实际产出为英文博客 Week8 D1+D2。需迭代团队确认 RU/ES 是否改期，验收侧不代写代码。（截至 2026-11-01 仍未见 RU/ES 提交）
3. 昨日 fleet-operators 页面当时「部署受 CF 事故阻塞」，今日已确认线上 200 且 sitemap lastmod 更新，该遗留项关闭。
