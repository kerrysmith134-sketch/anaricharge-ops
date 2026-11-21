#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""position_watch.py — 搜索位次异动监控（A18 SERP monitor 的可行版本）

## 为什么用 GSC 而不是爬 SERP
爬 Google SERP 会被封、且结果不稳定。我们手上有官方 GSC 数据（页面维度），
它给的是**我们自己页面的平均位次**——这足够回答"哪页掉了、哪页起来了"，
而且零额外成本、零封禁风险。query 维度在低流量站会被匿名化丢 60%，所以**不用 query 维度**判定。

## 做什么
对比最近两份 GSC 快照（或指定两个 --from/--to 文件），输出：
- 位次下滑 > N 位（默认 3）的页面 → 需要救
- 位次上升 > N 位的页面 → 值得加内链/加内容
- 有新曝光但 0 点击的页面（展示 ≥20）→ 标题/摘要问题
- 掉出前 50 的页面（之前在前 20）

## 用法
  python3 scripts/metrics/position_watch.py                       # 自动取最近两份快照
  python3 scripts/metrics/position_watch.py --from a.json --to b.json --json
退出码：0 无异常；2 有下滑页面（供定时任务判断）
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
DEFAULT_DIR = os.path.join(WS, "08-execution", "daily")

HOST_FIX = ("http://anaricharge.com", "https://anaricharge.com",
            "http://www.anaricharge.com", "https://www.anaricharge.com")


def load_pages(path):
    d = json.load(open(path, encoding="utf-8"))
    rows = d.get("pages") or d.get("rows") or []
    out = {}
    for r in rows:
        p = str(r.get("page") or r.get("key") or "").strip()
        for h in HOST_FIX:
            p = p.replace(h, "")
        if not p:
            continue
        out[p] = {
            "clicks": int(float(r.get("clicks") or 0)),
            "impressions": int(float(r.get("impressions") or 0)),
            "position": float(r.get("position") or 0),
        }
    return out, (d.get("window") or {})


def window_of(path):
    try:
        d = json.load(open(path, encoding="utf-8"))
        w = d.get("window") or {}
        return (w.get("start") or "", w.get("end") or "")
    except Exception:  # noqa: BLE001
        return ("", "")


def window_days(w):
    import datetime as dt
    try:
        s = dt.date.fromisoformat(w[0]); e = dt.date.fromisoformat(w[1])
        return (e - s).days
    except Exception:  # noqa: BLE001
        return 0


def pick_pair(a):
    if a.src and a.dst:
        return a.src, a.dst
    files = sorted(glob.glob(os.path.join(DEFAULT_DIR, "gsc-2026*.json")),
                   key=os.path.getmtime)
    if len(files) < 2:
        return None, None
    # 只跟**窗口天数相同**的快照比，避免拿 28 天窗口比 7 天窗口（会误报整页消失）
    latest = files[-1]
    days = window_days(window_of(latest))
    for f in reversed(files[:-1]):
        if window_days(window_of(f)) == days:
            return f, latest
    return None, latest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", default="")
    ap.add_argument("--to", dest="dst", default="")
    ap.add_argument("--drop", type=float, default=3.0, help="位次下滑多少位算告警")
    ap.add_argument("--rise", type=float, default=5.0, help="位次上升多少位算机会")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    src, dst = pick_pair(a)
    if not src or not dst:
        print("没有可比的两份 GSC 快照（需要**相同窗口天数**）。先跑 scripts/gsc_pull.py 再比。")
        return 0
    w_src, w_dst = window_of(src), window_of(dst)
    if window_days(w_src) != window_days(w_dst) or w_src == w_dst:
        # 窗口长度不同 → 位次与展示不可比；同一窗口 → 没有对比意义
        print(f"⚠️ 两份快照窗口不可比，拒绝出结论：{os.path.basename(src)}={w_src} "
              f"vs {os.path.basename(dst)}={w_dst}")
        print("   需要**窗口天数相同但起止日期不同**的两份快照（例如两个相邻 7 天窗口）。")
        return 3
    old, w_old = load_pages(src)
    new, w_new = load_pages(dst)

    drops, rises, no_click, vanished = [], [], [], []
    for p, cur in new.items():
        prev = old.get(p)
        if not prev:
            if cur["impressions"] >= 20 and cur["clicks"] == 0:
                no_click.append((p, cur))
            continue
        d = cur["position"] - prev["position"]      # 正数=变差（位次数字变大）
        if prev["impressions"] >= 10 and d >= a.drop:
            drops.append((p, prev["position"], cur["position"], d))
        if cur["impressions"] >= 10 and -d >= a.rise:
            rises.append((p, prev["position"], cur["position"], -d))
        if cur["impressions"] >= 20 and cur["clicks"] == 0:
            no_click.append((p, cur))
    for p, prev in old.items():
        if p not in new and prev["impressions"] >= 10:
            vanished.append((p, prev["position"], prev["impressions"]))

    drops.sort(key=lambda x: -x[3]); rises.sort(key=lambda x: -x[3])
    result = {
        "from": os.path.basename(src), "to": os.path.basename(dst),
        "windows": {"old": w_old, "new": w_new},
        "drops": [{"page": p, "from": round(o, 1), "to": round(n, 1), "delta": round(d, 1)}
                  for p, o, n, d in drops],
        "rises": [{"page": p, "from": round(o, 1), "to": round(n, 1), "gain": round(-d, 1)}
                  for p, o, n, d in rises],
        "zero_click_with_impressions": [{"page": p, "impressions": c["impressions"],
                                         "position": round(c["position"], 1)}
                                        for p, c in sorted(no_click, key=lambda x: -x[1]["impressions"])],
        "vanished": [{"page": p, "was_position": round(o, 1), "impressions": i}
                     for p, o, i in vanished],
    }
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        print(f"位次异动：{os.path.basename(src)} → {os.path.basename(dst)}")
        print(f"  对比页面数：旧 {len(old)} / 新 {len(new)}")
        if drops:
            print(f"\n🔻 下滑（≥{a.drop} 位）：{len(drops)}")
            for p, o, n, d in drops[:10]:
                print(f"    {p}  {o:.0f} → {n:.0f}  (-{d:.0f})")
        if rises:
            print(f"\n🔺 上升（≥{a.rise} 位）：{len(rises)}")
            for p, o, n, g in rises[:8]:
                print(f"    {p}  {o:.0f} → {n:.0f}  (+{g:.0f})")
        if no_click:
            print(f"\n👀 有展示 0 点击（展示≥20）：{len(no_click)}")
            for p, c in no_click[:8]:
                print(f"    {p}  展示 {c['impressions']} · 位次 {c['position']:.0f}")
        if vanished:
            print(f"\n❓ 本期无数据（上期有展示）：{len(vanished)}")
            for p, o, i in vanished[:6]:
                print(f"    {p}  上期位次 {o:.0f} · 展示 {i}")
        if not (drops or rises or no_click or vanished):
            print("\n✅ 无明显异动")
    return 2 if drops else 0


if __name__ == "__main__":
    raise SystemExit(main())
