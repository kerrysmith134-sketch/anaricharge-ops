#!/usr/bin/env python3
"""ctr_diagnose.py — 零点击/低 CTR 页面的查询词性诊断（P0-1 的执行工具）。

做三件事:
  1. 找出「展示 ≥ 阈值 且 点击率 < 阈值」的页面（默认 展示≥40、CTR<3%）
  2. 对指定页面拉 query 明细，按意图粗分类：商业 / 信息 / 导航 / 品牌 / 噪声
  3. 输出 title 改写建议（哪些词该前置、哪些该放弃）

用法:
  python3 scripts/ctr_diagnose.py --days 28
  python3 scripts/ctr_diagnose.py --page /blog/nevi-grants-ev-charging-station
  python3 scripts/ctr_diagnose.py --days 28 --json 08-execution/ctr-diagnose.json
"""
import argparse
import datetime as dt
import json
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from gsc_pull import access_token, gsc  # noqa: E402

BASE = "https://www.anaricharge.com"

COMMERCIAL = [
    "cost", "price", "pricing", "buy", "for sale", "manufacturer", "supplier", "wholesale",
    "oem", "quote", "roi", "payback", "business plan", "business", "franchise", "invest",
    "profit", "revenue", "savings", "grant", "funding", "incentive", "subsidy", "lease",
    "financing", "tco", "sizing", "installation cost", "per kwh", "per kw", "guide 2026",
]
INFORMATIONAL = [
    "what is", "how does", "how do", "why", "difference between", "vs", "explained",
    "meaning", "definition", "tutorial", "example", "diagram", "working principle",
]
NAVIGATIONAL = ["anari", "login", "contact", "careers", "location", "near me"]
NOISE = ["qmerit", "-site:", "site:", "jobs", "salary", "internship", "pdf", "youtube"]


def classify(q):
    ql = q.lower()
    if any(n in ql for n in NOISE):
        return "noise"
    if any(n in ql for n in NAVIGATIONAL):
        return "navigational"
    if any(c in ql for c in COMMERCIAL):
        return "commercial"
    if any(i in ql for i in INFORMATIONAL):
        return "informational"
    return "other"


def ctr_tier(impressions, ctr):
    if impressions >= 100 and ctr < 1.0:
        return "P0"      # 高曝光零点击
    if impressions >= 40 and ctr < 2.0:
        return "P1"
    if impressions >= 20 and ctr < 3.0:
        return "P2"
    return "-"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=28)
    ap.add_argument("--end", default=None, help="YYYY-MM-DD，默认昨天")
    ap.add_argument("--page", default=None, help="/path 或完整 URL")
    ap.add_argument("--min-imp", type=int, default=20)
    ap.add_argument("--json", dest="out", default=None)
    a = ap.parse_args()

    end = dt.date.fromisoformat(a.end) if a.end else dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=a.days - 1)
    at = access_token()
    s, e = str(start), str(end)

    if a.page:
        url = a.page if a.page.startswith("http") else BASE + a.page
        rows = gsc(["query"], s, e, 200, at, filters=[
            {"dimension": "page", "operator": "equals", "expression": url}])
        out = {"window": [s, e], "page": url, "queries": []}
        print(f"页面: {url}\n窗口: {s} ~ {e}\n")
        print(f"{'展示':>6} {'点击':>5} {'位次':>6}  意图          查询词")
        for r in sorted(rows, key=lambda x: -x["impressions"]):
            q = r["keys"][0]
            intent = classify(q)
            out["queries"].append({
                "query": q, "intent": intent,
                "impressions": r["impressions"], "clicks": r["clicks"],
                "position": round(r["position"], 1)})
            print(f"{r['impressions']:6d} {r['clicks']:5d} {r['position']:6.1f}  {intent:14s}{q[:70]}")
        tots = {}
        for q in out["queries"]:
            t = tots.setdefault(q["intent"], {"impressions": 0, "clicks": 0, "n": 0})
            t["impressions"] += q["impressions"]
            t["clicks"] += q["clicks"]
            t["n"] += 1
        print("\n意图分布（展示占比）:")
        total_imp = sum(t["impressions"] for t in tots.values()) or 1
        for k, v in sorted(tots.items(), key=lambda x: -x[1]["impressions"]):
            print(f"  {k:14s} {v['n']:3d} 词  {v['impressions']:5d} 展示 "
                  f"({v['impressions']/total_imp*100:4.1f}%)  {v['clicks']} 点击")
        out["intent_totals"] = tots
        if a.out:
            json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=2)
            print("\nWROTE", a.out)
        return 0

    pages = gsc(["page"], s, e, 1000, at)
    cand = []
    for r in pages:
        ctr = r["ctr"] * 100
        tier = ctr_tier(r["impressions"], ctr)
        if tier == "-":
            continue
        cand.append({
            "page": r["keys"][0].replace(BASE, ""),
            "impressions": r["impressions"], "clicks": r["clicks"],
            "ctr": round(ctr, 2), "position": round(r["position"], 1), "tier": tier,
        })
    cand.sort(key=lambda x: (x["tier"], -x["impressions"]))
    print(f"窗口 {s} ~ {e}（{a.days} 天）")
    print(f"{'级别':4s}{'展示':>6}{'点击':>5}{'CTR':>7}{'位次':>7}  页面")
    for c in cand:
        print(f"{c['tier']:4s}{c['impressions']:6d}{c['clicks']:5d}{c['ctr']:6.2f}%{c['position']:7.1f}  {c['page']}")
    lost = sum(c["impressions"] for c in cand)
    gain = sum(c["impressions"] for c in cand if c["tier"] in ("P0", "P1")) * 0.03
    print(f"\n候选 {len(cand)} 页，合计展示 {lost}；"
          f"若 P0+P1 做到 3% CTR 约 +{gain:.0f} 点击/{a.days}天")
    if a.out:
        json.dump({"window": [s, e], "candidates": cand,
                   "potential_clicks_at_3pct": round(gain, 1)},
                  open(a.out, "w"), ensure_ascii=False, indent=2)
        print("WROTE", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
