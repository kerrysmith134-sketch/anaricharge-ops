# 技能重复与命名冲突 skills-duplicates

> 由 `scripts/skill-build.py` 生成，可复跑。
> 判定方法：① frontmatter `name` 同名；② 去来源前缀后的职能名同名；③ description 3-gram Jaccard 排序；④ 触发词重合。
> 结论以 `02-skills/_MERGE-MAP.md` 的逐条处置为准。

## 1. frontmatter `name` 完全同名（3 组）

| frontmatter name | 目录（状态） | 处置建议 |
|---|---|---|
| `ad-creative` | `ad-creative`（archived）<br>`sa-ads-ad-creative`（merged → `ad-creative`） | 该同名组无在岗技能：以 `ad-creative` 为实体，另一个已 merge 进来 |
| `content-strategy` | `content-strategy`（active）<br>`sa-content-content-strategy`（merged → `content-strategy`） | 保留 `content-strategy`（active）为唯一实体；其余已并入/归档 |
| `programmatic-seo` | `cm-programmatic-seo`（merged → `programmatic-seo`）<br>`programmatic-seo`（active） | 保留 `programmatic-seo`（active）为唯一实体；其余已并入/归档 |

> 说明：frontmatter 同名但目录名不同的，多为 v3 来源（cm-/sa-）复用了 corey 原版的 `name` 字段。
> 这是**必须处置**的加载歧义——同名技能在装载时无法区分来源。本库统一以目录名作为唯一标识，
> 已被合并的副本保留在 `02-skills/<dir>` 中做溯源，不再作为独立技能注册。

## 2. 去来源前缀后职能名同名（3 组）

| 归一化职能名 | 原始目录（状态） | 判断 |
|---|---|---|
| `ad-creative` | `ad-creative`（archived）、`sa-ads-ad-creative`（merged） | 已合并：`sa-ads-ad-creative`→`ad-creative` |
| `content-strategy` | `content-strategy`（active）、`sa-content-content-strategy`（merged） | 已合并：`sa-content-content-strategy`→`content-strategy` |
| `programmatic-seo` | `cm-programmatic-seo`（merged）、`programmatic-seo`（active） | 已合并：`cm-programmatic-seo`→`programmatic-seo` |

## 3. description 重合度（3-gram Jaccard）

最高重合度仅 **0.11**，因此 description 文本不能作为去重依据——同一职能在不同来源中的措辞完全不同。
去重必须靠「名称 + 职能 + 触发词」，见 §1/§2/§4。

无 ≥0.35 的对（全部 description 措辞独立）。

## 4. 触发词重合（共享 ≥2 个引号触发词，1 对）

| 共享数 | A（状态） | B（状态） | 共同触发词 | 建议 |
|---|---|---|---|---|
| 3 | `schema`（merged） | `seo-schema`（active） | "json-ld"、"schema markup"、"structured data" | 留 active 者，另一个已 merged |

## 5. 已落地的合并（21 个）

| 被合并 | → 归入主技能 | 依据 |
|---|---|---|
| `ai-seo` | `seo-geo` | v2 合并表：ai-seo → seo-geo |
| `cm-cold-email-outreach` | `cold-email` | v3 从属：cm 冷邮件外联并入 corey cold-email（R4 单一入口） |
| `cm-cro-auditor` | `cro` | v2 合并表：cro-auditor → cro（53 点审计） |
| `cm-email-composer` | `copywriting` | v3 从属：邮件撰写并入 copywriting（emails 已并入 lead-magnets） |
| `cm-programmatic-seo` | `programmatic-seo` | v3 同名：cm-programmatic-seo 并入 programmatic-seo |
| `cm-retention-churn-prevention` | `churn-prevention` | v3 同名：保留 churn-prevention（已归档域）为唯一实体 |
| `cm-social-media-strategy` | `social` | v3 从属：社媒策略并入 social |
| `cm-technical-seo-audit` | `seo-technical-audit` | v2 合并表：technical-seo-audit → seo-technical-audit |
| `copy-editing` | `copywriting` | v2 合并表：copy-editing → copywriting |
| `emails` | `lead-magnets` | v2 合并表：emails → lead-magnets（lead magnet 交付邮件场景） |
| `keywords` | `seo-keyword-cluster` | v2 合并表：keywords → seo-keyword-cluster |
| `sa-ads-ad-angles` | `ad-creative` | v3 从属：广告角度并入 ad-creative（付费域已归档） |
| `sa-ads-ad-campaign-analyzer` | `ads` | v3 从属：战役评级并入 ads（付费域已归档） |
| `sa-ads-ad-creative` | `ad-creative` | v3 同名：sa 广告创意并入 ad-creative（付费域已归档） |
| `sa-content-content-strategy` | `content-strategy` | v3 同名：sa 内容策略并入 content-strategy |
| `sa-content-social-post-writer` | `social` | v2 合并表：social-post-writer → social |
| `sa-research-keyword-research` | `seo-keyword-cluster` | v3 从属：关键词宇宙扩展并入 seo-keyword-cluster |
| `sa-search-search-page-audit` | `seo-page` | v3 从属：38 点搜索页审计并入 seo-page |
| `schema` | `seo-schema` | v2 合并表：schema → seo-schema |
| `seo-audit` | `seo-technical-audit` | v2 合并表：seo-audit → seo-technical-audit |
| `seo-gaps-to-social-campaign` | `ai-search-gaps-to-social-campaign` | v3 同义：两条 seo-gaps→社媒 路线合并为一条 |

## 6. 未处置冲突

无。所有同名/近义检测结果均已被 `_MERGE-MAP.md` 的 active/merged/archived 处置覆盖。
