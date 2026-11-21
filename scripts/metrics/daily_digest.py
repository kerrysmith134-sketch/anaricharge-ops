#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""daily_digest.py — 逐日数据 + 逐日工作日志（供每日简报直接用）。

## 为什么需要
日报此前只有 28 天汇总（用户 2026-11-09 反馈："我得看到每天做了什么、每天的数据，
你现在只有月度数据"）。本脚本把三样东西按「天」聚合，输出 markdown 表格：

1. **GSC 日趋势**：读最新 `08-execution/daily/dashboard-<date>.json` 的 `daily_series`
   （看板刷新档每天 08:53 生成；口径 = GSC 日期维度，只用于看形状，KPI 仍以页面维度为准）。
2. **逐日工作日志**：`08-execution/run-log.jsonl`（每个 run 一行：agent/task/note）。
3. **逐日产物**：按文件名日期（YYYY-MM-DD 或 YYYYMMDD）统计每天产出的文件数与代表文件名。

## 用法
  python3 scripts/metrics/daily_digest.py                 # 近 14 天
  python3 scripts/metrics/daily_digest.py --days 7
  python3 scripts/metrics/daily_digest.py --days 30 --json

## 诚实边界
- run-log 2026-11-08 起为实时记录；更早历史（2026-07-20→2026-11-02）已由
  `backfill_runlog.py` 从 `05-records/timeline.md` 回填为 `hist-*` 条目
  （qa=unknown、时间 12:00 为占位）；2026-11-03→11-07 无记录，输出写「无记录」，不编造。
- GSC 日维度行之和 ≠ 页面维度 KPI（匿名化/聚合差异）；趋势看形状，KPI 看页面维度。
- 脚本只读，不写任何文件。
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DAILY = os.path.join(WS, "08-execution", "daily")
EXE = os.path.join(WS, "08-execution")
RUNLOG = os.path.join(EXE, "run-log.jsonl")


def newest_dashboard():
    files = sorted(glob.glob(os.path.join(DAILY, "dashboard-*.json")))
    return files[-1] if files else None


def gsc_daily(days):
    """返回 (rows, meta)。rows: [{date,clicks,impressions,ctr,position}]"""
    path = newest_dashboard()
    if not path:
        return [], {"error": "无 dashboard artifact"}
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return [], {"error": "读不了 %s: %s" % (os.path.basename(path), e)}
    series = d.get("daily_series") or []
    rows = series[-days:]
    meta = {
        "file": os.path.basename(path),
        "window": d.get("window"),
        "effective_data_end": d.get("effective_data_end"),
        "data_lag_days": d.get("data_lag_days"),
        "total_days_available": len(series),
    }
    return rows, meta


def ga4_daily(days):
    """GA4 逐日会话数（观测口径；失败返回 {}，不影响主流程）。"""
    script = os.path.join(WS, "scripts", "metrics", "ga4_query.py")
    try:
        r = subprocess.run([sys.executable, script, "event", "session_start",
                            "--days", str(days)],
                           capture_output=True, text=True, timeout=90)
    except Exception:  # noqa: BLE001
        return {}
    out = {}
    for line in (r.stdout or "").splitlines():
        # GA4 的 date 维度返回 YYYYMMDD（无横线），这里兼容两种写法
        m = re.match(r"\s*(20\d{2})-?(\d{2})-?(\d{2})\s+(\d+)\s*$", line)
        if m:
            out["%s-%s-%s" % (m.group(1), m.group(2), m.group(3))] = int(m.group(4))
    return out


def runlog_by_day():
    out = collections.defaultdict(list)
    if not os.path.exists(RUNLOG):
        return out
    for line in open(RUNLOG, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        day = (r.get("at") or "")[:10]
        if not day:
            continue
        out[day].append({
            "agent": r.get("agent") or "?",
            "task": (r.get("task") or "").strip(),
            "qa": r.get("qa") or "",
            "note": (r.get("note") or "").strip(),
            "outputs": (r.get("outputs") or "").strip(),
        })
    return out


DATE_RE = re.compile(r"(20\d{2})-?(\d{2})-?(\d{2})")


def artifacts_by_day(days):
    """按文件名里的日期统计产物（md/json），排除 run-log 与看板大文件重复计数。"""
    out = collections.defaultdict(list)
    cutoff = (dt.date.today() - dt.timedelta(days=days + 3)).isoformat()
    for root, dirs, files in os.walk(EXE):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__")]
        for fn in files:
            if not (fn.endswith(".md") or fn.endswith(".json")):
                continue
            m = DATE_RE.search(fn)
            if not m:
                continue
            day = "%s-%s-%s" % m.groups()
            try:  # 防 UUID/哈希里的数字被误当日期（如 …20512077… → 2051-20-77）
                dt.date.fromisoformat(day)
            except ValueError:
                continue
            if day < cutoff:
                continue
            out[day].append(os.path.relpath(os.path.join(root, fn), EXE))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    days = a.days

    rows, meta = gsc_daily(days)
    runs = runlog_by_day()
    arts = artifacts_by_day(days)
    # GA4 比 GSC 少 2~3 天滞后，多取 3 天以覆盖同一日期轴
    sess = ga4_daily(days + 3)

    # 日期轴：以 GSC 日序列为主，再并入 run-log / 产物里出现的日期（近 N 天）
    dates = [r["date"] for r in rows]
    today = dt.date.today()
    horizon = (today - dt.timedelta(days=days - 1)).isoformat()
    for d in list(runs.keys()) + list(arts.keys()):
        if d >= horizon and d not in dates:
            dates.append(d)
    dates = sorted(set(d for d in dates if d >= horizon))[-days:]

    if a.json:
        print(json.dumps({
            "generated_at": dt.datetime.now().astimezone().isoformat(),
            "gsc_daily": rows, "gsc_meta": meta,
            "runs": {d: runs.get(d, []) for d in dates},
            "artifacts": {d: arts.get(d, []) for d in dates},
        }, ensure_ascii=False, indent=1))
        return 0

    print("## 逐日数据（近 %d 天）" % days)
    if not rows:
        print("未取到 GSC 日数据：%s" % meta.get("error"))
    else:
        print("\n**GSC 日趋势**（来源 `%s`；窗口 %s～%s；有效数据末端 **%s**，滞后 %s 天）\n"
              % (meta["file"], (meta.get("window") or {}).get("start"),
                 (meta.get("window") or {}).get("end"),
                 meta.get("effective_data_end"), meta.get("data_lag_days")))
        print("| 日期 | 点击 | 展示 | CTR | 加权位次 | 会话(GA4) |")
        print("|---|---:|---:|---:|---:|---:|")
        for r in rows:
            print("| %s | %d | %d | %.2f%% | %.1f | %s |"
                  % (r["date"], r["clicks"], r["impressions"], r["ctr"], r["position"],
                     sess.get(r["date"], "—")))
        if len(rows) < days:
            print("\n> 只有 %d 天有返回（GSC finalize 延迟所致），缺的日子不是 0 流量。" % len(rows))

    print("\n## 逐日做了什么（近 %d 天）" % days)
    print("\n| 日期 | 记录数 | 做了什么（agent · task） | 产物数 |")
    print("|---|---:|---|---:|")
    for d in dates:
        rs = runs.get(d, [])
        if rs:
            parts = []
            seen = set()
            for r in rs:
                key = (r["agent"], r["task"][:40])
                if key in seen:
                    continue
                seen.add(key)
                parts.append("%s · %s" % (("历史档案" if r["agent"] == "history-backfill" else r["agent"]), (r["task"] or "—")[:40]))
            cell = "；".join(parts[:3]) + ("；…" if len(parts) > 3 else "")
        else:
            files = arts.get(d, [])
            base = [os.path.basename(f) for f in files]
            cell = ("产物：" + "、".join(base[:3]) + ("…" if len(base) > 3 else "")) \
                if base else "无记录（历史档案无该日条目）"
        print("| %s | %d | %s | %d |" % (d, len(rs), cell, len(arts.get(d, []))))
    print("\n> 说明：run-log 2026-11-08 起为实时记录；更早历史已从 05-records/timeline.md "
          "回填（`hist-*`，qa=unknown、时间 12:00 为占位）。2026-11-03→11-07 无记录；"
          "产物数按文件名日期统计，**不代表全部工作**。"
          "GSC 日维度行之和 ≠ 页面维度 KPI（匿名化/聚合差异），日线只看形状；"
          "GA4 会话为观测口径（含自测/自动化访问），不进 KPI。")

    # 各日代表产物（近 4 天，便于汇报）
    print("\n### 近 4 天代表产物")
    for d in dates[-4:]:
        files = arts.get(d, [])
        if not files:
            print("- %s：无（或文件名不带日期）" % d)
            continue
        shown = [f for f in files if "/" not in f][:4] or files[:4]
        print("- %s（%d 个）：%s" % (d, len(files), "、".join("`%s`" % f for f in shown)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
