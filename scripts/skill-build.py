#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill-build.py — ANARI 接管工作区技能库构建器（可复跑）

扫描 02-skills/ 下的技能目录，生成：
  02-skills/_manifest.json          每个技能的清单与来源追溯
  02-skills/_MERGE-MAP.md           146 个技能每个的最终去向（active/merged/archived）
  01-inventory/skills-inventory.md  逐技能盘点表
  01-inventory/skills-duplicates.md 重复/近义/命名冲突检测

用法：
  python3 scripts/skill-build.py [--skills-dir 02-skills] [--lock /path/skills-lock.json]

前置：validate-skills.py 负责质量门（frontmatter/引用/编码），本脚本不重复。
"""

import os
import re
import json
import sys
import hashlib

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(WS, "02-skills")
INV_DIR = os.path.join(WS, "01-inventory")
LOCK_PATH = "/Users/kerrychu/Documents/kimi/workspace/skills-lock.json"

# ---------------------------------------------------------------------------
# 处置表（依据：营销团队v2-花名册与技能整合.md、CMO审计报告-79技能完整矩阵.md、
#        AI营销团队增强报告-v3-136技能.md、AGENTS.md 硬规则 R3「不投付费广告」）
# 角色码：R1 增长操盘手 / R2 SEO工程师 / R3 内容主编 / R4 外链与数字公关 /
#         R5 社区引流 / R6 数据分析师 / CRO 转化组（按需）
# ---------------------------------------------------------------------------

# dir -> (status, role, mergedInto, basis)
DISPOSITION = {}

def act(role, basis):
    return ("active", role, None, basis)

def mrg(target, basis):
    return ("merged", "-", target, basis)

def arc(basis):
    return ("archived", "-", None, basis)

# ---- R1 增长操盘手（总编排）----
for d, b in {
    "marketing-plan": "v2 R1 在岗",
    "seo-plan": "v2 R1 在岗",
    "analytics": "v2 R1 在岗",
    "marketing-loops": "v2 R1 在岗",
    "marketing-ideas": "v2 R1 在岗",
    "content-strategy": "v2 R1 在岗（sa-content-content-strategy 并入本技能）",
    "product-marketing": "所有技能的基础产品上下文，常驻 R1",
    "ai-marketing-team": "团队编排元技能，R1 总编排入口",
    "cm-market-research": "v3 研究分析师 → R1；市场/ICP 研究支撑选题",
    "sa-research-channel-discovery": "v3 研究分析师 → R1；渠道评分用于有机渠道分配",
    "sa-research-competitor-discovery": "v3 研究分析师 → R1；竞品发现（不点名，仅内部情报）",
    "sa-research-competitor-landscape": "v3 研究分析师 → R1；竞品全景用于差异化定位",
    "sa-research-competitor-site-analysis": "v3 研究分析师 → R1；竞品站点结构化提取",
    "es-growth-engine": "v3 增长工程师 → R1；含 Python 实验引擎，可跑",
    "es-autoresearch": "v3 增长工程师 → R1；Karpathy 式优化循环",
}.items():
    DISPOSITION[d] = act("R1", b)

# ---- R2 SEO 工程师 ----
for d, b in {
    "seo-technical-audit": "v2 R2 在岗（seo-audit / cm-technical-seo-audit 并入本技能）",
    "site-architecture": "v2 R2 在岗",
    "seo-sitemap": "v2 R2 在岗",
    "seo-schema": "v2 R2 在岗（schema 并入本技能）",
    "seo-page": "v2 R2 在岗（sa-search-search-page-audit 并入本技能）",
    "seo-images": "v2 R2 在岗",
    "seo-drift": "v2 R2+R6 共用",
    "seo-firecrawl": "v2 R2 在岗",
    "seo-google": "v2 R2 在岗（GSC/PSI 直连）",
    "programmatic-seo": "v2 R2 国家系列扩展期启用（cm-programmatic-seo 并入本技能）",
    "core-web-vitals": "v2 R2 在岗（addyosmani）",
    "performance": "v2 R2 在岗（addyosmani）",
    "web-quality-audit": "v2 R2 在岗（addyosmani）",
    "accessibility": "v2 R2 在岗（addyosmani）",
    "best-practices": "v2 R2 在岗（addyosmani）",
    "seo": "v2 R2 在岗（addyosmani web-quality seo）",
    "seo-sxo": "v2 R2 在岗",
    "seo-local": "v2 R2 按需",
    "seo-hreflang": "v2 R2 按需（三语 EN/RU/ES）",
    "cm-llms-txt": "v2 R2 在岗（llms-txt 生成器）",
    "cm-schema-markup-generator": "v2 R2 在岗（schema-markup-generator）",
    "cm-aeo-geo-optimizer": "v3 GEO 优化师 → R2；AEO/GEO 审计",
    "seo-geo": "v2 GEO 优化师 → R2；ai-seo 并入本技能",
    "seo-api": "v2 SEO 数据层 API 技能 → R2",
    "seo-ai-search-share-of-voice": "v3 SEO/GEO 黄金组合之一 → R2；AI 引用声量监控",
    "es-seo-ops": "v3 增长工程师 → R2；GSC Optimizer + Content Attack Brief",
    "sa-research-competitor-keyword-analysis": "v3 研究 → R2；竞品关键词映射",
}.items():
    DISPOSITION[d] = act("R2", b)

# ---- R3 内容主编 ----
for d, b in {
    "seo-keyword-cluster": "v2 R3 在岗（keywords / sa-research-keyword-research 并入本技能）",
    "seo-keyword-niche": "v2 R3 在岗",
    "seo-content-brief": "v2 R3 在岗",
    "copywriting": "v2 R3 在岗（copy-editing / cm-email-composer 并入本技能）",
    "image": "v2 R3 在岗",
    "cm-content-pipeline": "v2 R3 在岗（content-pipeline）",
    "seo-competitor-gap-analysis": "v2 R3 在岗",
    "seo-competitor-pages": "v2 R3 在岗",
    "sa-research-competitor-content-analysis": "v2 R3 在岗（competitor-content-analysis）",
    "cm-competitor-ads-analyst": "v2 R3 在岗（competitor-ads-analyst；内部情报，不点名竞品）",
    "seo-content-audit": "v2 内容审计 → R3 内容刷新循环",
    "cm-brand-dna": "v3 品牌 DNA → R3；内容/视觉口径统一",
    "cm-brand-voice-guidelines": "v3 品牌声音指南 → R3；三语文案一致性",
    "es-content-ops": "v3 内容创作 → R3；expert-panel 90+ 质量门",
}.items():
    DISPOSITION[d] = act("R3", b)

# ---- R4 外链与数字公关 ----
for d, b in {
    "seo-backlink-gap": "v2 R4 在岗",
    "seo-backlinks-profile": "v2 R4 在岗",
    "directory-submissions": "v2 R4 在岗",
    "public-relations": "v2 R4 在岗",
    "cold-email": "v2 R4 在岗（cm-cold-email-outreach 并入本技能）",
    "prospecting": "v2 R4 在岗",
    "es-outbound-engine": "v3 增长工程师 → R4；外联自动化（人工发送由用户执行，R6 红线）",
}.items():
    DISPOSITION[d] = act("R4", b)

# ---- R5 社区引流 ----
for d, b in {
    "social": "v2 R5 在岗（sa-content-social-post-writer / cm-social-media-strategy 并入本技能）",
    "community-marketing": "v2 R5 在岗",
    "sa-research-community-discovery": "v2 R5 在岗（community-discovery）",
    "sa-research-influencer-discovery": "v2 R5 在岗（influencer-discovery）",
    "sa-reddit-reply-writer": "v2 R5 在岗（reply-writer）",
    "ai-search-gaps-to-social-campaign": "v2 R5 在岗（seo-gaps-to-social-campaign 并入本技能）",
    "site-audit-to-social-distribution": "v2 R5 在岗",
    "sa-content-content-repurposer": "v2 R5 在岗（content-repurposer）",
}.items():
    DISPOSITION[d] = act("R5", b)

# ---- R6 数据分析师 ----
for d, b in {
    "cm-google-analytics": "v2 R6 在岗（google-analytics）",
    "cm-looker-studio": "v2 R6 在岗（looker-studio 月报可视化）",
    "seo-ai-social-report": "v3 数据分析 → R6；SEO+AI+社媒统一报告",
}.items():
    DISPOSITION[d] = act("R6", b)

# ---- CRO 转化组（按需）----
for d, b in {
    "cro": "v2 CRO 在岗（cm-cro-auditor 53 点审计并入本技能）",
    "sa-conversion-conversion-audit": "v2 CRO 在岗（conversion-audit）",
    "cm-landing-page-optimizer": "v2 CRO 在岗（landing-page-optimizer）",
    "lead-magnets": "v2 CRO 在岗（emails 并入本技能）",
    "free-tools": "v2 CRO 在岗（/tools/ 计算器）",
    "offers": "v2 CRO 在岗",
    "popups": "v2 CRO 在岗",
    "ab-testing": "v2 CRO 在岗",
    "es-conversion-ops": "v3 转化 → CRO；8 维页面打分 + survey→lead magnet，含 Python",
    "cm-customer-journey-mapping": "v3 客户旅程映射 → CRO；询盘路径诊断",
}.items():
    DISPOSITION[d] = act("CRO", b)

# ---- 合并（10 项来自 v2 处置表 + 11 项 v3 重复/从属）----
for d, t, b in [
    ("seo-audit", "seo-technical-audit", "v2 合并表：seo-audit → seo-technical-audit"),
    ("schema", "seo-schema", "v2 合并表：schema → seo-schema"),
    ("keywords", "seo-keyword-cluster", "v2 合并表：keywords → seo-keyword-cluster"),
    ("cm-cro-auditor", "cro", "v2 合并表：cro-auditor → cro（53 点审计）"),
    ("copy-editing", "copywriting", "v2 合并表：copy-editing → copywriting"),
    ("sa-content-social-post-writer", "social", "v2 合并表：social-post-writer → social"),
    ("emails", "lead-magnets", "v2 合并表：emails → lead-magnets（lead magnet 交付邮件场景）"),
    ("ai-seo", "seo-geo", "v2 合并表：ai-seo → seo-geo"),
    ("cm-technical-seo-audit", "seo-technical-audit", "v2 合并表：technical-seo-audit → seo-technical-audit"),
    ("cm-cold-email-outreach", "cold-email", "v3 从属：cm 冷邮件外联并入 corey cold-email（R4 单一入口）"),
    ("cm-email-composer", "copywriting", "v3 从属：邮件撰写并入 copywriting（emails 已并入 lead-magnets）"),
    ("cm-programmatic-seo", "programmatic-seo", "v3 同名：cm-programmatic-seo 并入 programmatic-seo"),
    ("cm-retention-churn-prevention", "churn-prevention", "v3 同名：保留 churn-prevention（已归档域）为唯一实体"),
    ("cm-social-media-strategy", "social", "v3 从属：社媒策略并入 social"),
    ("sa-content-content-strategy", "content-strategy", "v3 同名：sa 内容策略并入 content-strategy"),
    ("sa-search-search-page-audit", "seo-page", "v3 从属：38 点搜索页审计并入 seo-page"),
    ("sa-research-keyword-research", "seo-keyword-cluster", "v3 从属：关键词宇宙扩展并入 seo-keyword-cluster"),
    ("seo-gaps-to-social-campaign", "ai-search-gaps-to-social-campaign", "v3 同义：两条 seo-gaps→社媒 路线合并为一条"),
    ("sa-ads-ad-creative", "ad-creative", "v3 同名：sa 广告创意并入 ad-creative（付费域已归档）"),
    ("sa-ads-ad-angles", "ad-creative", "v3 从属：广告角度并入 ad-creative（付费域已归档）"),
    ("sa-ads-ad-campaign-analyzer", "ads", "v3 从属：战役评级并入 ads（付费域已归档）"),
]:
    DISPOSITION[d] = mrg(t, b)

# ---- 归档：v2 处置表 28 项 + v3 付费/销售域 ----
for d, b in {
    # 留存/客户成功（还没有客户）
    "churn-prevention": "v2 归档：留存类，尚无客户",
    "referrals": "v2 归档：留存类，尚无客户",
    "onboarding": "v2 归档：留存类，尚无客户",
    "signup": "v2 归档：留存类，尚无客户",
    "revops": "v2 归档：留存类，尚无客户",
    "sales-enablement": "v2 归档：留存类，尚无客户",
    "client-onboarding-proposal": "v2 归档：留存类，尚无客户",
    "co-marketing": "v2 归档：留存类，尚无客户",
    # 付费媒体（R3 硬规则：$500 全投有机，不投广告）
    "ads": "v2 归档：付费媒体，R3 不投广告",
    "ad-creative": "v2 归档：付费媒体，R3 不投广告",
    "cm-google-ads": "v2 归档：付费媒体（google-ads）",
    "cm-facebook-ads": "v2 归档：付费媒体（facebook-ads）",
    "cm-linkedin-ads": "v2 归档：付费媒体（linkedin-ads）",
    "cm-tiktok-ads": "v2 归档：付费媒体（tiktok-ads）",
    "cm-wasted-spend-finder": "v2 归档：付费媒体（wasted-spend-finder）",
    "cm-cross-platform-audit": "v2 归档：付费媒体（cross-platform-audit）",
    "cm-utm-attribution-strategy": "v2 归档：付费媒体（utm-attribution-strategy）",
    "cm-klaviyo-analyst": "v3 归档：无 Klaviyo（邮件栈用 Brevo，R4 硬规则）",
    "cm-shopify": "v3 归档：无 Shopify 店铺",
    "seo-ads": "v2 归档：付费广告 SEO 变体，R3 不投广告",
    "seo-agency-landing-page": "v3 归档：招揽 SEO 代理客户的落地页，与自营产品不符",
    "seo-subdomain": "v2 归档：子域 SEO，当前单域 + 三语前缀已够",
    # 产品形态不符
    "aso": "v2 归档：无 App",
    "paywalls": "v2 归档：无订阅",
    "sms": "v2 归档：无短信计划",
    "video": "v2 归档：暂缓，LinkedIn 视频由专人覆盖",
    "local-gmb-visibility": "v2 归档：GBP 未建，建号后归 R5",
    # 战略咨询类（按需现场调用，不占编制）
    "marketing-council": "v2 归档：战略咨询按需",
    "strategy": "v2 归档：战略咨询按需",
    "marketing-psychology": "v2 归档：战略咨询按需",
    "competitor-profiling": "v2 归档：战略咨询按需（且 R2 红线不点名竞品）",
    "competitors": "v2 归档：战略咨询按需（不点名竞品）；本地变体见 skills-variants/competitors-claude",
    "customer-research": "v2 归档：战略咨询按需",
    "audit": "v2 归档：战略咨询按需",
    "launch": "v2 归档：战略咨询按需",
    "pricing": "v2 归档：战略咨询按需（定价已固化）",
    "cm-icp-research": "v2 归档：icp-research，ICP 已在产品上下文固化",
    "cm-pricing-strategy": "v2 归档：pricing-strategy，定价已固化",
    # v3 销售/收入域（无销售团队/无 CRM 数据源）
    "es-sales-pipeline": "v3 归档：需 RB2B+Instantly+HubSpot，当前未接入",
    "es-revenue-intelligence": "v3 归档：需 Gong+HubSpot+Ahrefs，当前未接入",
    "es-sales-playbook": "v3 归档：价值定价 playbook，无销售团队",
}.items():
    DISPOSITION[d] = arc(b)


# ---------------------------------------------------------------------------
# 来源归属
# ---------------------------------------------------------------------------
PREFIX_SOURCE = {
    "cm-": ("thatrebeccarae/claude-marketing", "github-inferred",
            "AI营销团队增强报告-v3-136技能.md §二：Claude Marketing (30)"),
    "es-": ("eric-siu/ai-marketing-skills", "github-inferred",
            "AI营销团队增强报告-v3-136技能.md §二：Eric Siu (9)"),
    "sa-": ("superamped/ai-marketing-skills", "github-inferred",
            "AI营销团队增强报告-v3-136技能.md §二：Superamped (18)"),
    "seo-": ("seranking/seo-skills", "github-inferred",
             "CMO审计报告-79技能完整矩阵.md §2.1：seranking/seo-skills (29)"),
}
LOCAL_SKILLS = {
    "ai-marketing-team", "ai-search-gaps-to-social-campaign",
    "client-onboarding-proposal", "local-gmb-visibility",
    "site-audit-to-social-distribution",
}


# ---------------------------------------------------------------------------
# frontmatter 解析（支持 name / description，含 >, >-, |, |- 块标量）
# ---------------------------------------------------------------------------
def parse_frontmatter(path):
    """返回 dict(name, description, has_frontmatter, raw_block)"""
    try:
        raw = open(path, "rb").read()
    except OSError:
        return dict(name=None, description=None, has_frontmatter=False,
                    error="unreadable")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return dict(name=None, description=None, has_frontmatter=False,
                    error="non-utf8")
    m = re.match(r"^\ufeff?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)",
                 text, re.S)
    if not m:
        return dict(name=None, description=None, has_frontmatter=False,
                    error=None)
    block = m.group(1)
    lines = block.split("\n")
    vals = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        mm = re.match(r"^([A-Za-z_][\w-]*):[ \t]*(.*)$", line)
        if not mm:
            i += 1
            continue
        key, rest = mm.group(1), mm.group(2)
        rest_s = rest.strip()
        if rest_s in (">", ">-", "|", "|-", ">+", "|+"):
            folded = not rest_s.startswith("|")
            buf = []
            i += 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or lines[i] == ""):
                buf.append(lines[i].strip())
                i += 1
            while buf and buf[-1] == "":
                buf.pop()
            vals[key] = (" " if folded else "\n").join(buf).strip()
            continue
        if len(rest_s) >= 2 and rest_s[0] == rest_s[-1] and rest_s[0] in "\"'":
            rest_s = rest_s[1:-1]
        vals[key] = rest_s
        i += 1
    return dict(name=vals.get("name"), description=vals.get("description"),
                has_frontmatter=True, error=None)


def count_lines(path):
    try:
        with open(path, "rb") as f:
            return f.read().count(b"\n") + 1
    except OSError:
        return 0


def extract_triggers(desc, limit=6):
    if not desc:
        return []
    raw = re.findall(r"[\"“]([^\"”]{2,60})[\"”]", desc)
    found = []
    for t in raw:
        t = t.strip().rstrip(",.;:")
        # 过滤掉两段引号之间的连接词（如 ", or "），只保留真正以词开头的短语
        if not re.match(r"^[A-Za-z0-9\u4e00-\u9fff]", t):
            continue
        if len(t) < 2 or not re.search(r"[A-Za-z\u4e00-\u9fff]{2}", t):
            continue
        found.append(t)
    seen, out = set(), []
    for t in found:
        t = t.strip()
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    if not out:
        first = re.split(r"[.。;；]", desc)[0].strip()
        out = [first[:60]] if first else []
    return out[:limit]


def shingles(text, n=5):
    words = re.findall(r"[a-z0-9\u4e00-\u9fff]+", (text or "").lower())
    if len(words) < n:
        return set(words)
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    lock = {}
    if os.path.exists(LOCK_PATH):
        try:
            lock = json.load(open(LOCK_PATH, encoding="utf-8")).get("skills", {})
        except Exception as e:  # noqa: BLE001
            print("WARN: cannot read lock file: %s" % e)
    lock_dirnames = set(lock)

    names = sorted(d for d in os.listdir(SKILLS_DIR)
                   if os.path.isdir(os.path.join(SKILLS_DIR, d))
                   and not d.startswith("."))
    if not names:
        print("FATAL: no skill dirs in %s" % SKILLS_DIR)
        return 2

    manifest, missing = [], []
    for name in names:
        d = os.path.join(SKILLS_DIR, name)
        skill_md = os.path.join(d, "SKILL.md")
        fm = parse_frontmatter(skill_md) if os.path.exists(skill_md) else \
            dict(name=None, description=None, has_frontmatter=False,
                 error="missing-skill-md")
        files, size = [], 0
        for root, dirs, fs in os.walk(d):
            dirs.sort()
            for f in sorted(fs):
                p = os.path.join(root, f)
                rel = os.path.relpath(p, d)
                files.append(rel)
                try:
                    size += os.path.getsize(p)
                except OSError:
                    pass
        # 来源
        if name in lock_dirnames:
            ent = lock[name]
            source = dict(repo=ent.get("source"), sourceType=ent.get("sourceType"),
                          skillPath=ent.get("skillPath"),
                          computedHash=ent.get("computedHash"), origin="skills-lock.json")
        elif name in LOCAL_SKILLS:
            source = dict(repo="local/anari-workspace", sourceType="local",
                          skillPath=None, computedHash=None, origin="local-authored")
        else:
            hit = None
            for pfx, val in PREFIX_SOURCE.items():
                if name.startswith(pfx):
                    hit = val
                    break
            if hit:
                source = dict(repo=hit[0], sourceType=hit[1], skillPath=None,
                              computedHash=None, origin=hit[2])
            else:
                source = dict(repo="unknown", sourceType="unknown",
                              skillPath=None, computedHash=None, origin="unclassified")
        disp = DISPOSITION.get(name)
        if disp is None:
            missing.append(name)
            disp = ("unclassified", "-", None, "MISSING DISPOSITION")
        status, role, merged_into, basis = disp
        desc = fm.get("description") or ""
        manifest.append(dict(
            name=name,
            path="02-skills/%s/SKILL.md" % name,
            dir="02-skills/%s" % name,
            frontmatterName=fm.get("name"),
            hasFrontmatter=bool(fm.get("has_frontmatter")),
            descriptionLen=len(desc),
            description=desc,
            lineCount=count_lines(skill_md) if os.path.exists(skill_md) else 0,
            fileCount=len(files),
            bytes=size,
            files=files,
            triggers=extract_triggers(desc),
            source=source,
            role=role,
            status=status,
            mergedInto=merged_into,
            dispositionBasis=basis,
        ))

    if missing:
        print("FATAL: %d skills without disposition: %s" % (len(missing), missing))
        return 3
    # 覆盖校验
    covered = set(DISPOSITION)
    extra = covered - set(names)
    if extra:
        print("WARN: disposition entries not present as dirs: %s" % sorted(extra))

    # ---- 写 manifest ----
    status_counts = {}
    for r in manifest:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
    manifest_doc = dict(
        generatedBy="scripts/skill-build.py",
        generatedFrom="/Users/kerrychu/Documents/kimi/workspace (read-only source)",
        skillCount=len(manifest),
        statusSummary=status_counts,
        lockFile="/Users/kerrychu/Documents/kimi/workspace/skills-lock.json",
        lockEntries=len(lock),
        note=("Frontmatter was missing in 6 es-* skills at source; descriptions were "
              "authored during takeover (see 01-inventory/skills-quality.md)."),
        skills=manifest,
    )
    os.makedirs(SKILLS_DIR, exist_ok=True)
    with open(os.path.join(SKILLS_DIR, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_doc, f, ensure_ascii=False, indent=1)
        f.write("\n")

    # ---- 写 MERGE-MAP ----
    write_merge_map(manifest, status_counts, lock_entries=len(lock))

    # ---- 写 inventory ----
    os.makedirs(INV_DIR, exist_ok=True)
    write_inventory(manifest, lock)

    # ---- 写 duplicates ----
    write_duplicates(manifest)

    # ---- 摘要 ----
    print("skills: %d" % len(manifest))
    print("status: %s" % json.dumps(status_counts, ensure_ascii=False))
    role_counts = {}
    for r in manifest:
        role_counts[r["role"]] = role_counts.get(r["role"], 0) + 1
    print("roles: %s" % json.dumps(role_counts, ensure_ascii=False))
    print("with frontmatter: %d / %d" % (sum(1 for r in manifest if r["hasFrontmatter"]), len(manifest)))
    print("with lock source: %d" % sum(1 for r in manifest if r["source"]["origin"] == "skills-lock.json"))
    print("unclassified source: %d" % sum(1 for r in manifest if r["source"]["sourceType"] == "unknown"))
    return 0


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------
def write_merge_map(manifest, status_counts, lock_entries):
    A = status_counts.get("active", 0)
    M = status_counts.get("merged", 0)
    R = status_counts.get("archived", 0)
    lines = []
    w = lines.append
    w("# 技能合并映射 _MERGE-MAP — 146 个技能的最终去向")
    w("")
    w("> 本文件由 `scripts/skill-build.py` 从 `02-skills/_manifest.json` 生成，可复跑。")
    w("> 生成日期：2026-11-07 ｜ 技能总数：**%d** ｜ active **%d** / merged **%d** / archived **%d**" % (len(manifest), A, M, R))
    w("")
    w("## 0. 口径与冲突说明（以源文件为准，逐条标注）")
    w("")
    w("### 0.1 集合口径")
    w("")
    w("| 项 | 数字 | 说明 |")
    w("|---|---|---|")
    w("| `.agents/skills/` 真实目录 | 137 | Kimi 主技能库；另含空目录 `.manifests`（未计） |")
    w("| `.claude/skills/` 条目 | 142 | 其中 132 个符号链接指向 `../../.agents/skills/<name>`，**去重不重复迁** |")
    w("| `.claude/skills/` 独立真实目录 | 10 | `accessibility, audit, best-practices, competitors, core-web-vitals, keywords, performance, seo, strategy, web-quality-audit` |")
    w("| 其中与 `.agents` 同名但内容不同 | 1 | `competitors`：`.agents` 版含 evals/ + references/（已作为正式版迁移）；`.claude` 版为单文件变体（保存在 `01-inventory/skills-variants/competitors-claude/`，未丢弃） |")
    w("| 去重后迁移技能总数 | **146** | 137 + 10 − 1（competitors 同名合并） |")
    w("")
    w("> 任务书写作「137+8」，v3 报告写作「136」；实测为 **137 + 10 − 1 = 146**。")
    w("> 三者差异来自：任务书漏计 `competitors` 同名变体；v3 报告（2026-07-22）早于 9 月新增技能。")
    w("> 本表以**实际目录**为准，146 个一个不漏。")
    w("")
    w("### 0.2 v2 花名册声明数与逐条数的冲突")
    w("")
    w("`营销团队v2-花名册与技能整合.md` 表头声明 **在岗 41 / 合并 10 / 归档 28 = 79**，")
    w("但逐条清点其正文列表得到：在岗条目 **62 个唯一名**、合并 **10**、归档 **32**（其中 `stop-slop`、`seo-analyzer` 两个名字**在磁盘上不存在**）。")
    w("v2 报告日期为 2026-09-22，晚于 v3（2026-07-22），正文已把 v3 的 `cm-*` / `sa-*` 技能重新命名为短名混入在岗表，但表头 79 的计数没有同步更新。")
    w("")
    w("**处置原则**：① 以 v2 正文的**逐条处置**为权威；② 名字不存在于磁盘的（`stop-slop`、`seo-analyzer`）记为「源侧缺失」而非技能缺失；")
    w("③ v2 未列到的 v3 新技能，按 v3 报告的「7 个专家代理」映射 + `AGENTS.md` 硬规则 R3（不投付费广告）补处置；④ 冲突逐条记录在下方 0.3。")
    w("")
    w("### 0.3 逐条冲突与裁决")
    w("")
    w("| 冲突点 | 源文件说法 | 实际磁盘 | 裁决 |")
    w("|---|---|---|---|")
    w("| `stop-slop` | v2 在岗 R3 | 无此目录 | 源侧缺失，未迁移；R3 用 `copywriting` + `es-content-ops` 质量门替代 |")
    w("| `seo-analyzer` | v2 合并 → seo-technical-audit | 无此目录 | 源侧缺失，无需合并 |")
    w("| `technical-seo-audit` | v2 合并 → seo-technical-audit | 实际目录为 `cm-technical-seo-audit` | 合并到 `seo-technical-audit` |")
    w("| `cro-auditor` | v2 合并 → cro | 实际目录为 `cm-cro-auditor` | 合并到 `cro` |")
    w("| `conversion-audit` | v2 CRO 在岗 | 实际目录为 `sa-conversion-conversion-audit` | active / CRO |")
    w("| `competitors` | v2 归档 | `.agents` 与 `.claude` 两版内容不同 | 以 `.agents` 版为准归档；`.claude` 变体存档 |")
    w("| 付费媒体 `cm-*-ads` | v3 黄金组合要启用 | R3 硬规则：$500 全投有机 | **归档**（组合仅作能力储备） |")
    w("| Eric Siu `es-sales-*` / `es-revenue-*` | v3 称「真正干活」 | 需 RB2B/Instantly/Gong/HubSpot，均未接入 | 归档，待数据源接入后重评 |")
    w("")
    lock_tracked = sum(1 for r in manifest if r["source"]["origin"] == "skills-lock.json")
    seo_total = sum(1 for r in manifest if r["name"].startswith("seo-"))
    seo_locked = sum(1 for r in manifest if r["name"].startswith("seo-")
                     and r["source"]["origin"] == "skills-lock.json")
    seo_unlocked = seo_total - seo_locked
    baseline = lock_tracked + seo_unlocked
    increment = len(manifest) - baseline
    cm_n = sum(1 for r in manifest if r["name"].startswith("cm-"))
    es_n = sum(1 for r in manifest if r["name"].startswith("es-"))
    sa_n = sum(1 for r in manifest if r["name"].startswith("sa-"))
    local_n = increment - cm_n - es_n - sa_n
    w("### 0.4 79 → 146 的增量口径")
    w("")
    w("| 口径 | 目录数 | 构成 |")
    w("|---|---|---|")
    w("| v2 基线（`skills-lock.json` 可追溯） | %d | coreyhaines31 + ScaleBrick + addyosmani |" % lock_tracked)
    w("| v2 基线（SE Ranking，无 lock 条目） | %d | `seo-*` 中未被 lock 覆盖的部分 |" % seo_unlocked)
    w("| **v2 基线合计（目录口径）** | **%d** | v2 报告写 79，是编辑口径（86 条目去重名重叠） |" % baseline)
    w("| **v3 增量（按目录计）** | **%d** | cm-* %d + es-* %d + sa-* %d + 本地自建 %d |" % (increment, cm_n, es_n, sa_n, local_n))
    w("| **迁移后实际技能数** | **%d** | %d + %d |" % (len(manifest), baseline, increment))
    w("")
    w("> 任务书写「79→137 新增 58」：137 是 `.agents` 目录数，未含 `.claude` 的 9 个独立技能；")
    w("> 本库把 9 个独立技能一并迁入后为 %d，故增量为 %d − 79（口径值）= %d，或 %d − %d（目录值）= %d。"
      % (len(manifest), len(manifest), len(manifest) - 79, len(manifest), baseline, increment))
    w("> **无论用哪个口径，%d 个技能在下表 §2 中都逐条给出了 active/merged/archived 去向。**" % len(manifest))
    w("> §5 单列全部 %d 个 v3 增量技能的处置建议与依据。" % increment)
    w("")
    w("## 1. 角色汇总")
    w("")
    role_counts = {}
    for r in manifest:
        role_counts[r["role"]] = role_counts.get(r["role"], 0) + 1
    w("| 角色 | 在岗技能数 | 说明 |")
    w("|---|---|---|")
    ROLE_DESC = {
        "R1": "增长操盘手（总编排）",
        "R2": "SEO 工程师",
        "R3": "内容主编",
        "R4": "外链与数字公关",
        "R5": "社区引流",
        "R6": "数据分析师",
        "CRO": "转化组（按需）",
        "-": "不在岗（merged / archived）",
    }
    for role in ["R1", "R2", "R3", "R4", "R5", "R6", "CRO", "-"]:
        if role in role_counts:
            w("| %s | %d | %s |" % (role, role_counts[role], ROLE_DESC.get(role, "")))
    w("")
    w("## 2. 全部技能去向（%d 行，按状态 → 名称排序）" % len(manifest))
    w("")
    order = {"active": 0, "merged": 1, "archived": 2}
    rows = sorted(manifest, key=lambda r: (order.get(r["status"], 9), r["name"]))
    w("| # | 技能 | 状态 | 角色 | 归入 | 依据 |")
    w("|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        st = {"active": "✅ active", "merged": "🔀 merged", "archived": "🗄 archived"}[r["status"]]
        w("| %d | `%s` | %s | %s | %s | %s |" % (
            i, r["name"], st, r["role"],
            ("`%s`" % r["mergedInto"]) if r["mergedInto"] else "—",
            r["dispositionBasis"]))
    w("")
    w("## 3. 合并组明细（%d 个被合并技能 → 主技能）" % M)
    w("")
    groups = {}
    for r in manifest:
        if r["status"] == "merged":
            groups.setdefault(r["mergedInto"], []).append(r["name"])
    for tgt in sorted(groups):
        tgt_status = next((x["status"] for x in manifest if x["name"] == tgt), "?")
        w("- **`%s`**（目标状态：%s）← %s" % (tgt, tgt_status, "、".join("`%s`" % n for n in sorted(groups[tgt]))))
    w("")
    w("## 4. 归档区（%d 个）" % R)
    w("")
    for cat, pred in [
        ("留存/客户成功（尚无客户）", lambda r: r["name"] in {
            "churn-prevention", "referrals", "onboarding", "signup", "revops",
            "sales-enablement", "client-onboarding-proposal", "co-marketing"}),
        ("付费媒体（R3：$500 全投有机）", lambda r: r["role"] == "-" and r["status"] == "archived" and (
            "ads" in r["name"] or "ad-" in r["name"] or "klaviyo" in r["name"] or "shopify" in r["name"]
            or "utm" in r["name"] or "wasted" in r["name"] or "cross-platform" in r["name"])),
        ("产品形态不符（无 App/订阅/短信/GBP）", lambda r: r["name"] in {
            "aso", "paywalls", "sms", "video", "local-gmb-visibility"}),
        ("战略咨询（按需现场调用，不占编制）", lambda r: r["name"] in {
            "marketing-council", "strategy", "marketing-psychology", "competitor-profiling",
            "competitors", "customer-research", "audit", "launch", "pricing", "cm-icp-research",
            "cm-pricing-strategy"}),
        ("SEO 变体（当前业务形态用不上）", lambda r: r["name"] in {
            "seo-agency-landing-page", "seo-subdomain"}),
        ("销售/收入域（数据源未接入）", lambda r: r["name"] in {
            "es-sales-pipeline", "es-revenue-intelligence", "es-sales-playbook"}),
    ]:
        items = sorted(r["name"] for r in manifest if r["status"] == "archived" and pred(r))
        if items:
            w("- **%s**（%d）：%s" % (cat, len(items), "、".join("`%s`" % n for n in items)))
    w("")
    # v3 增量 = 非 lock 且非 seo- 前缀（seo-* 属 v2 基线 SE Ranking）
    base = set()
    for r in manifest:
        if r["source"]["origin"] == "skills-lock.json" or r["name"].startswith("seo-"):
            base.add(r["name"])
    inc = [r for r in manifest if r["name"] not in base]
    w("## 5. v3 增量技能处置（%d 个，79→146 的新增部分）" % len(inc))
    w("")
    w("| # | 技能 | 来源 | 状态 | 角色 | 归入 | 依据 |")
    w("|---|---|---|---|---|---|---|")
    for i, r in enumerate(sorted(inc, key=lambda x: x["name"]), 1):
        st = {"active": "✅ active", "merged": "🔀 merged", "archived": "🗄 archived"}[r["status"]]
        w("| %d | `%s` | %s | %s | %s | %s | %s |" % (
            i, r["name"], r["source"]["repo"], st, r["role"],
            ("`%s`" % r["mergedInto"]) if r["mergedInto"] else "—",
            r["dispositionBasis"]))
    w("")
    w("## 6. 可追溯性")
    w("")
    w("- 每个技能的来源（repo / sourceType / skillPath / computedHash）见 `_manifest.json` 的 `source` 字段。")
    w("- `skills-lock.json` 覆盖 %d 个技能；其余为 v3 新来源（cm-/es-/sa-/seo-）或本地自建。" % lock_entries)
    w("- 6 个 `es-*` 技能源库缺 YAML frontmatter，已在迁移时补写（详见 `01-inventory/skills-quality.md`）。")
    w("")
    dst = os.path.join(SKILLS_DIR, "_MERGE-MAP.md")
    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("wrote", dst)


def write_inventory(manifest, lock):
    lines = []
    w = lines.append
    w("# 技能盘点 skills-inventory")
    w("")
    w("> 由 `scripts/skill-build.py` 生成，可复跑。技能总数 **%d**。" % len(manifest))
    w("")
    w("| # | 技能 | 来源 | 一句话用途 | 行数 | 触发词 | 状态 | v2 花名册引用 |")
    w("|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(sorted(manifest, key=lambda x: x["name"]), 1):
        desc = (r["description"] or "").replace("|", "/").strip()
        one = re.split(r"(?<=[.。])\s+", desc)[0][:110] if desc else "（无 description）"
        trig = "、".join(r["triggers"][:3]).replace("|", "/")[:70] or "—"
        src = r["source"]["repo"]
        referenced = "是" if r["status"] in ("active", "merged") else "否"
        w("| %d | `%s` | %s | %s | %d | %s | %s | %s |" % (
            i, r["name"], src, one, r["lineCount"], trig, r["status"], referenced))
    w("")
    w("## 来源分布")
    w("")
    src_counts = {}
    for r in manifest:
        src_counts[r["source"]["repo"]] = src_counts.get(r["source"]["repo"], 0) + 1
    w("| 来源 | 技能数 |")
    w("|---|---|")
    for s, c in sorted(src_counts.items(), key=lambda x: -x[1]):
        w("| %s | %d |" % (s, c))
    w("")
    dst = os.path.join(INV_DIR, "skills-inventory.md")
    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("wrote", dst)


def write_duplicates(manifest):
    by_fm = {}
    for r in manifest:
        key = (r["frontmatterName"] or "").strip().lower()
        if key:
            by_fm.setdefault(key, []).append(r["name"])
    fm_collisions = {k: v for k, v in by_fm.items() if len(v) > 1}

    def strip_prefix(n):
        """把来源前缀去掉，得到职能名。sa- 还要去掉中间的分类段。"""
        n = re.sub(r"^(cm|es)-", "", n)
        if n.startswith("sa-"):
            n = re.sub(r"^(research|content|ads|conversion|search|reddit)-", "", n[3:])
        return n

    stripped = {}
    for r in manifest:
        stripped.setdefault(strip_prefix(r["name"]), []).append(r["name"])
    name_collisions = {k: v for k, v in stripped.items() if len(v) > 1}

    st = {r["name"]: r["status"] for r in manifest}
    tgt = {r["name"]: r["mergedInto"] for r in manifest}

    # description 相似度（3-gram，阈值仅用于排序，不作硬判）
    sh = {r["name"]: shingles(r["description"], 3) for r in manifest}
    pairs = []
    names = sorted(sh)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            jac = jaccard(sh[a], sh[b])
            if jac > 0:
                pairs.append((jac, a, b))
    pairs.sort(reverse=True)
    max_jac = pairs[0][0] if pairs else 0.0
    strong_pairs = [p for p in pairs if p[0] >= 0.35]

    # 触发词重合（两技能共享 >=2 个引号触发词）
    trig = {r["name"]: set(t.lower() for t in r["triggers"]) for r in manifest}
    trig_pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            if not trig[a] or not trig[b]:
                continue
            common = trig[a] & trig[b]
            if len(common) >= 2:
                trig_pairs.append((len(common), a, b, sorted(common)))

    lines = []
    w = lines.append
    w("# 技能重复与命名冲突 skills-duplicates")
    w("")
    w("> 由 `scripts/skill-build.py` 生成，可复跑。")
    w("> 判定方法：① frontmatter `name` 同名；② 去来源前缀后的职能名同名；③ description 3-gram Jaccard 排序；④ 触发词重合。")
    w("> 结论以 `02-skills/_MERGE-MAP.md` 的逐条处置为准。")
    w("")
    w("## 1. frontmatter `name` 完全同名（%d 组）" % len(fm_collisions))
    w("")
    w("| frontmatter name | 目录（状态） | 处置建议 |")
    w("|---|---|---|")
    for k in sorted(fm_collisions):
        dirs = sorted(fm_collisions[k])
        cells = "<br>".join("`%s`（%s%s）" % (
            d, st[d], (" → `%s`" % tgt[d]) if tgt.get(d) else "") for d in dirs)
        keep = [d for d in dirs if st[d] == "active"]
        if keep:
            advice = "保留 `%s`（active）为唯一实体；其余已并入/归档" % keep[0]
        else:
            target = [d for d in dirs if any(tgt.get(x) == d for x in dirs)]
            advice = "该同名组无在岗技能：以 `%s` 为实体，另一个已 merge 进来" % (
                target[0] if target else dirs[0])
        w("| `%s` | %s | %s |" % (k, cells, advice))
    w("")
    w("> 说明：frontmatter 同名但目录名不同的，多为 v3 来源（cm-/sa-）复用了 corey 原版的 `name` 字段。")
    w("> 这是**必须处置**的加载歧义——同名技能在装载时无法区分来源。本库统一以目录名作为唯一标识，")
    w("> 已被合并的副本保留在 `02-skills/<dir>` 中做溯源，不再作为独立技能注册。")
    w("")
    w("## 2. 去来源前缀后职能名同名（%d 组）" % len(name_collisions))
    w("")
    w("| 归一化职能名 | 原始目录（状态） | 判断 |")
    w("|---|---|---|")
    for k in sorted(name_collisions):
        dirs = sorted(name_collisions[k])
        cells = "、".join("`%s`（%s）" % (d, st[d]) for d in dirs)
        active = [d for d in dirs if st[d] == "active"]
        merged_here = [d for d in dirs if tgt.get(d) in dirs]
        if merged_here:
            verdict = "已合并：%s" % "、".join("`%s`→`%s`" % (d, tgt[d]) for d in merged_here)
        elif len(active) == 1:
            verdict = "保留 `%s`，其余见各自处置" % active[0]
        elif len(active) == 0:
            verdict = "均非在岗，保留实体即可"
        else:
            verdict = "**同名但在岗并列，需人工复核**：%s" % "、".join(active)
        w("| `%s` | %s | %s |" % (k, cells, verdict))
    w("")
    w("## 3. description 重合度（3-gram Jaccard）")
    w("")
    w("最高重合度仅 **%.2f**，因此 description 文本不能作为去重依据——同一职能在不同来源中的措辞完全不同。" % max_jac)
    w("去重必须靠「名称 + 职能 + 触发词」，见 §1/§2/§4。")
    w("")
    if strong_pairs:
        w("| Jaccard | A | B |")
        w("|---|---|---|")
        for jac, a, b in strong_pairs[:20]:
            w("| %.2f | `%s` | `%s` |" % (jac, a, b))
    else:
        w("无 ≥0.35 的对（全部 description 措辞独立）。")
    w("")
    w("## 4. 触发词重合（共享 ≥2 个引号触发词，%d 对）" % len(trig_pairs))
    w("")
    if trig_pairs:
        w("| 共享数 | A（状态） | B（状态） | 共同触发词 | 建议 |")
        w("|---|---|---|---|---|")
        for cnt, a, b, common in sorted(trig_pairs, reverse=True)[:30]:
            if st[a] == "active" and st[b] == "active":
                advice = "**在岗并列**，需在 description 里写清分工边界"
            elif "active" in (st[a], st[b]):
                advice = "留 active 者，另一个已 merged"
            else:
                advice = "均非在岗，保留一个实体"
            w("| %d | `%s`（%s） | `%s`（%s） | %s | %s |" % (
                cnt, a, st[a], b, st[b], "、".join("\"%s\"" % c for c in common[:5]), advice))
    else:
        w("无共享 ≥2 触发词的对。")
    w("")
    w("## 5. 已落地的合并（%d 个）" % sum(1 for r in manifest if r["status"] == "merged"))
    w("")
    w("| 被合并 | → 归入主技能 | 依据 |")
    w("|---|---|---|")
    for r in sorted(manifest, key=lambda x: x["name"]):
        if r["status"] == "merged":
            w("| `%s` | `%s` | %s |" % (r["name"], r["mergedInto"], r["dispositionBasis"]))
    w("")
    w("## 6. 未处置冲突")
    w("")
    unresolved = [r for r in manifest if r["status"] == "active" and r["name"] in
                  {d for grp in name_collisions.values() for d in grp}
                  and len([d for d in name_collisions[strip_prefix(r["name"])] if st[d] == "active"]) > 1]
    if unresolved:
        w("以下在岗技能与其他技能职能名相同，但处置表判定都需保留，需人工确认边界：")
        w("")
        for r in unresolved:
            w("- `%s`（%s）" % (r["name"], r["role"]))
    else:
        w("无。所有同名/近义检测结果均已被 `_MERGE-MAP.md` 的 active/merged/archived 处置覆盖。")
    w("")
    dst = os.path.join(INV_DIR, "skills-duplicates.md")
    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("wrote", dst, "| fm-collisions=%d name-collisions=%d strong-desc=%d trigger-pairs=%d" % (
        len(fm_collisions), len(name_collisions), len(strong_pairs), len(trig_pairs)))
    return unresolved


if __name__ == "__main__":
    sys.exit(main())
