# anaricharge.com 技术 SEO 周巡检修复清单（2026-10-17）

> 依据：2026-10-17 巡检结论与 sitemap.xml（87 URL 全 200）、首页与 /blog/ 实测取证。
> 适用：内容工程师/开发在站点源码内修改，改完走 Cloudflare Pages 部署即可。

---

## 1. 首页补 BreadcrumbList JSON-LD（本次唯一 fail 项）

**结论**：https://www.anaricharge.com/ 是全站唯一无 BreadcrumbList JSON-LD 且无可见面包屑的页面（其他页面均有）。恢复方式二选一，由内容工程师按 SOP 措辞决定：

- **方案 A（推荐，若 SOP 要求仅覆盖内容页）**：首页作为站点根，规范上允许豁免面包屑。在 SOP 中明确"面包屑仅覆盖内容页，首页豁免"即可关闭本次 fail。
- **方案 B（若 SOP 要求每页都有）**：在首页 `<head>` 的 canonical 标签附近插入最小 BreadcrumbList JSON-LD：

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://www.anaricharge.com/"
    }
  ]
}
</script>
```

**验证**：部署后抓取首页 HTML，确认 `application/ld+json` 中存在 `BreadcrumbList`，且 `item` 指向 https://www.anaricharge.com/。

---

## 2. Blog 卡片 CTA 锚文本关键词化（minor 优化）

**结论**：/blog/ 列表页 25 个卡片 CTA 中，仅 2 组锚文本出现重复，建议改为带目标关键词的描述性锚文本，提升内链语义与 AI 检索可引性：

| 目标文章 URL | 当前锚文本 | 建议锚文本 |
| --- | --- | --- |
| /blog/how-to-start-a-mobile-ev-charging-business | Read the guide | Read: Mobile EV Charging Business Guide |
| /blog/ev-charging-station-franchise | Read the guide | Read: EV Charging Station Franchise Guide |
| /blog/ev-charging-demand-charge-reduction | Read the breakdown | Read: Demand Charge Reduction Breakdown |
| /blog/commercial-ev-charging-station-cost | Read the breakdown | Read: Commercial EV Charging Station Cost Breakdown |

其余 21 个 CTA 均为唯一描述性锚文本（如 "Read the opex breakdown"、"Read the grid connection guide"），无需改动。

**验证**：部署后抓取 /blog/，确认 25 个卡片 CTA 锚文本两两不重复，且均含目标关键词。

---

## 3. 收录"待确认"项补充取证（检查项 7）

**新增证据（2026-10-17 robots.txt 实测，HTTP 200）**：

- `User-agent: *` → `Allow: /`，全站可抓取；
- 显式欢迎 Googlebot / Bingbot / Google-Extended / ClaudeBot / GPTBot / PerplexityBot / Applebot / DuckDuckBot 等 AI 与搜索爬虫；
- `Sitemap: https://www.anaricharge.com/sitemap.xml` 声明存在；
- 唯一 `Disallow: /apps/`（vendored 计算器 iframe，非内容页，符合设计）。

**结论**：站点侧无 robots/meta-robots 索引障碍，Cloudflare Pages 托管正常（首页 cf-cache-status: HIT）。外部搜索（site: 与品牌词）仍未检索到 anaricharge.com 页面，问题集中在 **GSC 提交与抓取侧**。

**处置（需 Kerry 在 Google Search Console 执行）**：

1. 确认 www.anaricharge.com 属性已添加并验证所有权；
2. 在"Sitemaps"中提交 `https://www.anaricharge.com/sitemap.xml`；
3. 用"网址检查"工具对 https://www.anaricharge.com/ 执行"请求编入索引"；
4. 一周后查看"网页索引编制"报告，确认收录页数开始增长。

---

## 附：本次巡检唯一开放项状态

| 检查项 | 状态 | 处置归属 |
| --- | --- | --- |
| 9 首页面包屑 | fail | 内容工程师/开发（见第 1 节） |
| 11 CTA 锚文本 | minor | 内容工程师/开发（见第 2 节） |
| 7 收录 | 待确认 → 已收敛 | Kerry（GSC 操作，见第 3 节） |