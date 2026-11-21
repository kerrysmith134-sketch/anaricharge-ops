# 技能质量门 skills-quality

> 由 `scripts/validate-skills.py --write-report` 生成，可复跑。
> 生成时间：2026-11-07 ｜ 技能数：**146** ｜ 结果：**FAIL**

## 1. 总览

| 指标 | 数值 |
|---|---|
| 扫描技能数 | 146 |
| 硬失败（必须修） | 27 |
| 软告警（建议修） | 51 |
| 结论 | **FAIL** |

> **结论含义**：FAIL 全部来自源库自带的「引用了但未随包安装」的文件（见 §4），
> **0 项由本次迁移造成**。frontmatter / name / description / UTF-8 / 空目录 / 超大文件全部 PASS。

## 2. 分项计数

| 检查项 | 级别 | 数量 |
|---|---|---|
| 缺 SKILL.md | FAIL | 0 |
| 缺 YAML frontmatter | FAIL | 0 |
| frontmatter 缺 name | FAIL | 0 |
| frontmatter 缺 description | FAIL | 0 |
| 非 UTF-8 文件 | FAIL | 0 |
| 单文件 >512KB | FAIL | 0 |
| SKILL.md 引用的 scripts/ 或 lib/ 缺失 | FAIL | 26 |
| SKILL.md 引用的 assets/ 模板缺失 | FAIL | 1 |
| SKILL.md 引用的 references/ 文档缺失（多为可选/自定义提示） | WARN | 1 |
| 跨仓库/运行时引用缺失（upstream tools/、examples/ 或生成文件） | WARN | 103 |
| frontmatter.name ≠ 目录名 | WARN | 51 |
| description <60 字符 | WARN | 0 |
| description >1024 字符 | WARN | 0 |
| 空技能目录 | WARN | 0 |
| 技能内空子目录 | WARN | 0 |
| 整技能 >2MB | WARN | 0 |

| `_manifest.json` 一致性 | PASS | PASS（条目数 == 目录数） |

## 3. 问题清单（逐条）

### SKILL.md 引用的 references/ 文档缺失（多为可选/自定义提示）（1）

- es-autoresearch -> references/founder-voice.md

### frontmatter.name ≠ 目录名（51）

- cm-aeo-geo-optimizer => aeo-geo-optimizer
- cm-brand-dna => brand-dna
- cm-brand-voice-guidelines => brand-voice-guidelines
- cm-cold-email-outreach => cold-email-outreach
- cm-competitor-ads-analyst => competitor-ads-analyst
- cm-content-pipeline => content-pipeline
- cm-cro-auditor => cro-auditor
- cm-cross-platform-audit => cross-platform-audit
- cm-customer-journey-mapping => customer-journey-mapping
- cm-email-composer => email-composer
- cm-facebook-ads => facebook-ads
- cm-google-ads => google-ads
- cm-google-analytics => google-analytics
- cm-icp-research => icp-research
- cm-klaviyo-analyst => klaviyo-analyst
- cm-landing-page-optimizer => landing-page-optimizer
- cm-linkedin-ads => linkedin-ads
- cm-llms-txt => llms-txt
- cm-looker-studio => looker-studio
- cm-market-research => market-research
- cm-pricing-strategy => pricing-strategy
- cm-programmatic-seo => programmatic-seo
- cm-retention-churn-prevention => retention-churn-prevention
- cm-schema-markup-generator => schema-markup-generator
- cm-shopify => shopify
- cm-social-media-strategy => social-media-strategy
- cm-technical-seo-audit => technical-seo-audit
- cm-tiktok-ads => tiktok-ads
- cm-utm-attribution-strategy => utm-attribution-strategy
- cm-wasted-spend-finder => wasted-spend-finder
- es-autoresearch => autoresearch
- es-content-ops => expert-panel
- es-outbound-engine => cold-outbound-optimizer
- sa-ads-ad-angles => ad-angles
- sa-ads-ad-campaign-analyzer => ad-campaign-analyzer
- sa-ads-ad-creative => ad-creative
- sa-content-content-repurposer => content-repurposer
- sa-content-content-strategy => content-strategy
- sa-content-social-post-writer => social-post-writer
- sa-conversion-conversion-audit => conversion-audit
- sa-reddit-reply-writer => reply-writer
- sa-research-channel-discovery => channel-discovery
- sa-research-community-discovery => community-discovery
- sa-research-competitor-content-analysis => competitor-content-analysis
- sa-research-competitor-discovery => competitor-discovery
- sa-research-competitor-keyword-analysis => competitor-keyword-analysis
- sa-research-competitor-landscape => competitor-landscape
- sa-research-competitor-site-analysis => competitor-site-analysis
- sa-research-influencer-discovery => influencer-discovery
- sa-research-keyword-research => keyword-research
- sa-search-search-page-audit => search-page-audit

## 4. 缺失引用的性质与裁决（重要）

本节回答一个问题：这些缺失是**迁移丢的**，还是**源库本来就没有**？

已逐一回到只读源目录 `/Users/kerrychu/Documents/kimi/workspace/.agents/skills/` 核对：

| 类别 | 数量 | 性质 | 裁决 |
|---|---|---|---|
| `scripts/` 缺失 | 26 | SE Ranking 系列 SKILL.md 引用的 Python 脚本**未随技能包安装**（源目录本身无 `scripts/` 子目录） | 上游半安装，非迁移丢失；调用这些技能时需补脚本或改走 GSC API 直连（见 `scripts/gsc_pull.py`） |
| `assets/` 缺失 | 1 | `seo-ai-social-report` 声称 bundling `assets/report-template.html`，源目录只有 SKILL.md | 上游半安装；报告模板需重建 |
| `references/` 缺失 | 1 | `es-autoresearch` 建议用户自建 `references/founder-voice.md`（可选自定义） | 非缺陷 |
| 跨仓库引用 | 103 | coreyhaines/SE Ranking 技能引用 upstream 仓库的 `../../tools/`、`../../examples/` 共享文件，这些从未随技能安装 | 上游依赖未落地；不影响技能加载，影响「按文档执行」 |

**结论**：0 处缺失由本次迁移造成（复制前后比对确认）；以上均为源库自带缺陷。
按严格质量门口径记为 **FAIL**（文档承诺的文件不存在），但不阻塞技能发现与加载。

## 5. 迁移时已修复的问题（源库缺陷）

| # | 技能 | 源库问题 | 处置 |
|---|---|---|---|
| 1 | `es-conversion-ops` | SKILL.md 直接以 `#` 标题开头，无 YAML frontmatter | 已补 name + description |
| 2 | `es-growth-engine` | 同上 | 已补 |
| 3 | `es-revenue-intelligence` | 同上 | 已补 |
| 4 | `es-sales-pipeline` | 同上 | 已补 |
| 5 | `es-sales-playbook` | 同上 | 已补 |
| 6 | `es-seo-ops` | 同上 | 已补 |

> 这 6 个技能来自 Eric Siu 系列，源库缺 frontmatter 会导致**技能加载器永远发现不到它们**。
> 接管时按目录名补 `name`，并按各自 README/正文提炼 1–2 句 `description`（含触发词），已修复 6/6。

## 6. frontmatter.name 与目录名不一致清单（WARN，不阻塞）

共 51 个。这些技能自身 `name` 使用短名（如 `cm-google-ads` 的 name 是 `google-ads`），
加载器若按 `name` 去重会与 corey 原版同名技能冲突——本库统一以**目录名**为唯一 ID，
manifest 同时保留 `name`（frontmatter）与目录名两个字段，冲突已在 `skills-duplicates.md` §1 登记。

- `cm-aeo-geo-optimizer => aeo-geo-optimizer`
- `cm-brand-dna => brand-dna`
- `cm-brand-voice-guidelines => brand-voice-guidelines`
- `cm-cold-email-outreach => cold-email-outreach`
- `cm-competitor-ads-analyst => competitor-ads-analyst`
- `cm-content-pipeline => content-pipeline`
- `cm-cro-auditor => cro-auditor`
- `cm-cross-platform-audit => cross-platform-audit`
- `cm-customer-journey-mapping => customer-journey-mapping`
- `cm-email-composer => email-composer`
- `cm-facebook-ads => facebook-ads`
- `cm-google-ads => google-ads`
- `cm-google-analytics => google-analytics`
- `cm-icp-research => icp-research`
- `cm-klaviyo-analyst => klaviyo-analyst`
- `cm-landing-page-optimizer => landing-page-optimizer`
- `cm-linkedin-ads => linkedin-ads`
- `cm-llms-txt => llms-txt`
- `cm-looker-studio => looker-studio`
- `cm-market-research => market-research`
- `cm-pricing-strategy => pricing-strategy`
- `cm-programmatic-seo => programmatic-seo`
- `cm-retention-churn-prevention => retention-churn-prevention`
- `cm-schema-markup-generator => schema-markup-generator`
- `cm-shopify => shopify`
- `cm-social-media-strategy => social-media-strategy`
- `cm-technical-seo-audit => technical-seo-audit`
- `cm-tiktok-ads => tiktok-ads`
- `cm-utm-attribution-strategy => utm-attribution-strategy`
- `cm-wasted-spend-finder => wasted-spend-finder`
- `es-autoresearch => autoresearch`
- `es-content-ops => expert-panel`
- `es-outbound-engine => cold-outbound-optimizer`
- `sa-ads-ad-angles => ad-angles`
- `sa-ads-ad-campaign-analyzer => ad-campaign-analyzer`
- `sa-ads-ad-creative => ad-creative`
- `sa-content-content-repurposer => content-repurposer`
- `sa-content-content-strategy => content-strategy`
- `sa-content-social-post-writer => social-post-writer`
- `sa-conversion-conversion-audit => conversion-audit`
- `sa-reddit-reply-writer => reply-writer`
- `sa-research-channel-discovery => channel-discovery`
- `sa-research-community-discovery => community-discovery`
- `sa-research-competitor-content-analysis => competitor-content-analysis`
- `sa-research-competitor-discovery => competitor-discovery`
- `sa-research-competitor-keyword-analysis => competitor-keyword-analysis`
- `sa-research-competitor-landscape => competitor-landscape`
- `sa-research-competitor-site-analysis => competitor-site-analysis`
- `sa-research-influencer-discovery => influencer-discovery`
- `sa-research-keyword-research => keyword-research`
- `sa-search-search-page-audit => search-page-audit`
