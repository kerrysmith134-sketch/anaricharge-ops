#!/usr/bin/env python3
"""opportunity_rank.py — 用「期望 CTR vs 实际 CTR」排序真实机会。

为什么需要它：连续两次我的"快赢"判断都被数据推翻（词级位次当页面级、以为 title 没优化其实已优化）。
直觉不可靠，必须用位置带（position band）的期望 CTR 来算机会值。

机会值 = 展示 × (该位置带的期望 CTR − 实际 CTR)，再按缺口排序。
期望 CTR 用业界公开的位置带均值（B2B 场景取偏保守值）。

用法：
  python3 scripts/metrics/opportunity_rank.py            # 默认 28 天窗口
  python3 scripts/metrics/opportunity_rank.py --top 20
"""
import argparse
import glob
import json
import os

WS = "/Users/kerrychu/anari-charge-website"

# 位置带 → 期望 CTR（保守值，B2B 工业品；来源为业界公开 CTR-by-position 曲线的下沿）
BANDS = [
    (1, 1, 0.28), (2, 2, 0.15), (3, 3, 0.11), (4, 4, 0.08), (5, 5, 0.06),
    (6, 10, 0.035), (11, 15, 0.018), (16, 20, 0.011), (21, 30, 0.007),
    (31, 50, 0.004), (51, 100, 0.002),
]


def expected_ctr(pos):
    p = pos or 100
    for lo, hi, c in BANDS:
        if lo <= p <= hi:
            return c
    return 0.001


def latest_gsc():
    """取「数据窗口最晚」的 GSC 文件（不是按文件名排序）。

    2026-11-21 修：日更档把文件写到 08-execution/daily/gsc-*.json，
    而旧文件留在 08-execution/gsc-*.json；原来只 glob 根目录、按文件名排序，
    结果一直读到 2026-11-10 的旧窗口，机会榜连续一周没变化。
    """
    fs = glob.glob(os.path.join(WS, "08-execution", "gsc-*.json")) + \
         glob.glob(os.path.join(WS, "08-execution", "daily", "gsc-*.json"))
    if not fs:
        raise SystemExit("没有 GSC 文件，先跑 python3 scripts/gsc_pull.py")
    best, best_key = None, None
    for f in fs:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        w = d.get("window") or {}
        key = (w.get("end") or "", os.path.getmtime(f))
        if best_key is None or key > best_key:
            best, best_key = (d, f), key
    if not best:
        raise SystemExit("GSC 文件都无法解析")
    return best[0], best[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--min-imp", type=int, default=10)
    ap.add_argument("--out", default=os.path.join(WS, "08-execution", "dashboard", "opportunity-rank.json"))
    a = ap.parse_args()

    d, src = latest_gsc()
    win = d.get("window") or {}
    rows = []
    for p in d.get("pages") or []:
        imp = p.get("impressions") or 0
        if imp < a.min_imp:
            continue
        pos = p.get("position") or 100
        ctr = (p.get("clicks") or 0) / imp if imp else 0
        exp = expected_ctr(pos)
        gap = exp - ctr
        rows.append({
            "page": p.get("page"),
            "impressions": imp,
            "clicks": p.get("clicks") or 0,
            "position": round(pos, 1),
            "ctr_pct": round(ctr * 100, 2),
            "expected_ctr_pct": round(exp * 100, 2),
            "opportunity_clicks": round(imp * gap, 1),
            "diagnosis": ("位次太远 → 要外链/内链" if pos > 20
                          else "位次尚可但 CTR 低于期望 → 改 title/meta" if gap > 0.005
                          else "表现正常"),
        })
    rows.sort(key=lambda r: -r["opportunity_clicks"])

    total_opp = sum(max(0, r["opportunity_clicks"]) for r in rows)
    out = {"source": src, "window": win, "pages_considered": len(rows),
           "total_opportunity_clicks": round(total_opp, 1), "rows": rows}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"窗口 {win.get('start')} ~ {win.get('end')} | 考量 {len(rows)} 页 | 总机会 ≈ {total_opp:.1f} 点击")
    print(f"{'#':>2} {'展示':>5} {'点击':>4} {'位次':>5} {'CTR%':>5} {'期望%':>5} {'机会':>5}  诊断 / 页面")
    for i, r in enumerate(rows[:a.top], 1):
        print(f"{i:>2} {r['impressions']:>5} {r['clicks']:>4} {r['position']:>5.1f} "
              f"{r['ctr_pct']:>5.2f} {r['expected_ctr_pct']:>5.2f} {r['opportunity_clicks']:>5.1f}  "
              f"{r['diagnosis'][:22]:24s} {r['page'].replace('https://www.anaricharge.com','')}")
    print(f"\n→ {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
