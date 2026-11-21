#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""backfill_runlog.py — 把 05-records/ 的历史回填进 run-log.jsonl。

## 为什么
用户 2026-11-09 要求：「把 05-records/ 的历史也回填进 run-log」。
`run-log.jsonl` 从 2026-11-08 才开始记，导致每日简报的「逐日做了什么」在更早的
日子只能显示「无记录」。而 `05-records/timeline.md` 里有完整的两张表：
  - 一、主时间线 P00–P71（2026-07-20 → 2026-10-28）
  - 二、记录派生条目 R 系列（日终简报 / 周报 / 收录 / 可见度 / 交接 / 裁决）
本脚本把它们转成 run-log 条目，**只追加、幂等**（run_id = `hist-<ID>`，已存在则跳过）。

## 诚实边界（写进每条 note）
- 原记录只有日期，**时间戳 12:00:00+08:00 是占位**，不是真实运行时刻。
- `qa` 一律 `unknown` —— 原记录里没有统一的 QA 判定，不假装 pass。
- 产出物/验收结论原样搬进 `outputs` 字段，不改写、不升格。

## 用法
  python3 scripts/metrics/backfill_runlog.py --dry     # 只预览统计
  python3 scripts/metrics/backfill_runlog.py           # 真写入
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TIMELINE = os.path.join(WS, "05-records", "timeline.md")
LOG = os.path.join(WS, "08-execution", "run-log.jsonl")

ROW_RE = re.compile(
    r"^\|\s*(P\d{2}|R\d{2})\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$")
DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")


def parse_rows():
    rows = []
    for lineno, line in enumerate(open(TIMELINE, encoding="utf-8"), 1):
        m = ROW_RE.match(line.rstrip("\n"))
        if not m:
            continue
        rid, date_cell, event, typ, output, source = [x.strip() for x in m.groups()]
        dm = DATE_RE.search(date_cell)
        if not dm:
            continue
        rows.append({
            "id": rid,
            "date": dm.group(1),
            "date_raw": date_cell,
            "event": event,
            "type": typ,
            "output": output,
            "source": source,
            "line": lineno,
        })
    return rows


def existing_ids():
    out = set()
    if not os.path.exists(LOG):
        return out
    for line in open(LOG, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            out.add((json.loads(line).get("run_id") or ""))
        except Exception:  # noqa: BLE001
            continue
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    rows = parse_rows()
    have = existing_ids()
    new = [r for r in rows if ("hist-" + r["id"]) not in have]

    by_month = {}
    for r in rows:
        by_month[r["date"][:7]] = by_month.get(r["date"][:7], 0) + 1
    print("timeline 解析：%d 条（P %d / R %d）"
          % (len(rows),
             sum(1 for r in rows if r["id"].startswith("P")),
             sum(1 for r in rows if r["id"].startswith("R"))))
    print("月份分布：" + " · ".join("%s=%d" % (k, v) for k, v in sorted(by_month.items())))
    print("已存在（跳过）：%d · 待回填：%d" % (len(rows) - len(new), len(new)))

    if a.dry:
        for r in new[:5]:
            print("  预览 %s %s %s" % (r["id"], r["date"], r["event"][:50]))
        return 0
    if not new:
        print("无新增，无需写入。")
        return 0

    recs = []
    for r in sorted(new, key=lambda x: (x["date"], x["id"])):
        recs.append({
            "run_id": "hist-" + r["id"],
            "at": r["date"] + "T12:00:00+08:00",
            "agent": "history-backfill",
            "task": r["event"],
            "inputs": "",
            "outputs": r["output"],
            "sources": "05-records/timeline.md:%d（%s）" % (r["line"], r["source"]),
            "risks": "",
            "qa": "unknown",
            "approved_by": "",
            "published_url": "",
            "review_due": "",
            "note": "回填自 05-records/timeline.md（%s · 类型：%s）。原记录只有日期，"
                    "时间戳 12:00 为占位；qa=unknown 表示原记录无统一 QA 判定，不假装通过。"
                    % (r["id"], r["type"]),
        })
    # 单次追加，减少与其他会话并发写的窗口
    blob = "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in recs)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(blob)
    print("已写入 %d 条 → %s" % (len(recs), LOG))
    print("覆盖日期：%s → %s" % (recs[0]["at"][:10], recs[-1]["at"][:10]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
