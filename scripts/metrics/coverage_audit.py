#!/usr/bin/env python3
"""coverage_audit.py — 渠道 × 技能 × 定时任务 × KPI 的覆盖审计。

## 为什么要这个东西
目标要求"全渠道，每个渠道有可执行的 skill 与每日自动执行的定时任务"。
这类要求最容易在口头成立、实际有空缺——所以要用脚本核对，不靠印象。

## 判据（每渠道四项）
1. skill：`.agents/skills/` 里有对应技能目录
2. task：调度表里有对应定时任务（按标题关键词匹配）
3. kpi：飞轮 state.json 里有归属该渠道/Pod 的 KPI
4. asset：仓库里已有对应产出物（可选，用于判断"能不能立刻执行"）

## 用法
  python3 scripts/metrics/coverage_audit.py
  python3 scripts/metrics/coverage_audit.py --json
"""
import json
import os
import sys

WS = "/Users/kerrychu/anari-charge-website"
SKILLS = os.path.join(WS, ".agents", "skills")
SCHED = "/Users/kerrychu/.dsh/storages/schedule.json"
STATE = os.path.join(WS, "08-execution", "flywheel", "state.json")

# 渠道定义：skill 目录候选 + 任务标题关键词 + KPI key 前缀
CHANNELS = [
    ("建站/页面工厂", ["site-page-factory", "cloudflare", "web-perf"],
     ["页面工厂", "技术 SEO"], ["A.indexable_pages"]),
    ("SEO", ["programmatic-seo", "internal-linking"],
     ["程序化 SEO", "技术 SEO", "关键词"], ["A.index_coverage_pct", "A.org_impressions_28d"]),
    ("GEO / AI 可见度", ["geo-ai-visibility"],
     ["GEO"], ["C.geo_cited"]),
    ("内容营销", ["copy-anatomy", "storytelling-framework", "ai-humanizer", "case-study-builder"],
     ["内容", "选题"], ["A.impressions_per_page_month"]),
    ("内链", ["internal-linking"], ["内链"], ["A.orphan_pages"]),
    ("外链 / 数字公关", ["email-enrichment", "press-release"],
     ["外链", "外联"], ["C.referring_domains", "C.prospect_pool_ready"]),
    ("社媒 / 社区", ["social-distribution"], ["社媒", "社区"],
     ["C.social_posts_30d", "C.social_drafts_ready"]),
    ("广告", ["paid-ads-ops"], ["广告"], ["__N/A_R3__"]),
    ("转化优化 / CRO", ["cro-inquiry", "experimentation"], ["CRO", "询盘监控"], ["B.inquiries"]),
    ("度量 / 看板", ["marketing-measurement", "product-marketing-metrics"],
     ["看板", "工作总结", "飞轮"], ["A.index_coverage_pct", "B.inquiries"]),
    # 战略层：不是周期渠道（ICP/定位/信息架构是低频产出），所以不要求定时任务与 KPI
    ("战略层（ICP/定位/信息架构）__STATIC__",
     ["icp-persona", "customer-segments", "product-positioning",
      "portfolio-positioning", "product-messaging"],
     [], []),
]


def skills_present():
    return set(os.listdir(SKILLS)) if os.path.isdir(SKILLS) else set()


def tasks():
    try:
        d = json.load(open(SCHED, encoding="utf-8"))
        out = []
        for t in (d.get("tables", {}).get("tasks") or {}).values():
            r = t.get("record") or {}
            out.append({"title": r.get("title") or "", "status": t.get("status")})
        return [x for x in out if x["status"] == "active"]
    except Exception:  # noqa: BLE001
        return []


def kpis():
    try:
        s = json.load(open(STATE, encoding="utf-8"))
        return set((s.get("kpis") or {}).keys())
    except Exception:  # noqa: BLE001
        return set()


def main():
    as_json = "--json" in sys.argv
    have_skills, have_tasks, have_kpis = skills_present(), tasks(), kpis()
    rows = []
    for raw_name, want_skills, want_tasks, want_kpis in CHANNELS:
        static = raw_name.endswith("__STATIC__")
        name = raw_name.replace("__STATIC__", "")
        s_ok = [s for s in want_skills if s in have_skills]
        t_hit = [t["title"] for t in have_tasks
                 if any(k.lower() in t["title"].lower() for k in want_tasks)] if want_tasks else []
        na = bool(want_kpis) and want_kpis == ["__N/A_R3__"]
        k_ok = [k for k in want_kpis if k in have_kpis] if not na else []
        score = 0
        score += 1 if (s_ok or not want_skills) else 0
        score += 1 if (t_hit or not want_tasks) else 0
        if na:
            score += 1                       # 按 R3 明确不做，算覆盖
        elif want_kpis:
            score += 1 if k_ok else 0
        # want_kpis 为空 → 不计分（这是缺口，不是通过）
        rows.append({"channel": name, "na": na, "static": static,
                     "kpi_declared": bool(want_kpis) and not na,
                     "skills_ok": bool(s_ok or not want_skills),
                     "skills": s_ok, "tasks_ok": bool(t_hit or not want_tasks),
                     "tasks": t_hit, "kpi_ok": bool(k_ok or not want_kpis),
                     "kpis": k_ok, "score": score})
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    print(f"活跃定时任务 {len(have_tasks)} 个 | 技能 {len(have_skills)} 个 | KPI {len(have_kpis)} 条")
    print("=" * 96)
    print(f"{'渠道':<26} {'技能':<5} {'任务':<5} {'KPI':<5} 说明")
    print("-" * 96)
    gaps = []
    for r in rows:
        mark = lambda ok: "✅" if ok else "—"
        note = "N/A(按R3) " if r.get("na") else ("未定义KPI " if not r.get("kpi_declared") else "")
        if not r["skills_ok"]:
            note += "缺技能 "
            gaps.append((r["channel"], "skill"))
        if not r["tasks_ok"]:
            note += "缺定时任务 "
            gaps.append((r["channel"], "task"))
        if not r["kpi_ok"] and not r.get("na"):
            if r.get("kpi_declared"):
                note += "缺KPI（已声明未测） "
            gaps.append((r["channel"], "kpi"))
        if r["tasks"]:
            note += "| " + r["tasks"][0][:30]
        if r.get("static"):
            print(f"{r['channel']:<26} {mark(r['skills_ok']):<5} {'—':<5} {'—':<5} 静态层（低频产出）")
        else:
            print(f"{r['channel']:<26} {mark(r['skills_ok']):<5} {mark(r['tasks_ok']):<5} "
                  f"{mark(r['kpi_ok']):<5} {note}")
    print("=" * 96)
    na_channels = [r["channel"] for r in rows if r.get("na")]
    static_ch = [r["channel"] for r in rows if r.get("static")]
    full = [r["channel"] for r in rows
            if r["skills_ok"] and r["tasks_ok"] and (r["kpi_ok"] or r.get("na")) and not r.get("static")]
    print(f"完整覆盖（技能+任务+KPI）：{len(full)}/{len(rows)} 个渠道")
    if static_ch:
        print("  静态层（低频产出，不要求定时任务/KPI）：" + "、".join(static_ch))
    if na_channels:
        print("  按规则不做：" + "、".join(f"{c}（R3 不投付费广告）" for c in na_channels))
    if gaps:
        print("真实缺口：")
        for ch, what in gaps:
            if ch in static_ch:
                continue
            print(f"  - {ch}: 缺 {what}")
    else:
        print("  无未解释的缺口。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
