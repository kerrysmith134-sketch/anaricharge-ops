#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_log_autolog.py — 从当日产物自动补 run 记录（GROW-011 的接线方式）

## 为什么这样接线
计划要求每个 Agent 每次执行都有 run 记录。但 12 个定时任务的任务书各写各的，
逐个改提示词既慢又容易漂。改成**从产物反推**：
每个档位都会在 `08-execution/<区域>/` 留下 `<日期>-*.md`，扫一遍就知道谁跑了、
产出是什么文件。这样无需改任务书，历史记录也能回填。

## 规则
- 只看今天（或 --date）的产物文件；按 (agent, 文件) 去重
- qa 字段标 `unknown`——**我们从产物反推不出 QA 结论，就不假装知道**
- 已经由人/脚本显式写过的 run 不覆盖（按 outputs 路径去重）

用法：
  python3 scripts/metrics/run_log_autolog.py            # 补今天的
  python3 scripts/metrics/run_log_autolog.py --date 2026-11-07
  python3 scripts/metrics/run_log_autolog.py --dry
"""
import argparse
import datetime as dt
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
LOG = os.path.join(WS, "08-execution", "run-log.jsonl")

# 目录 → agent 标识（按我们实际的档位）
DIR_AGENT = {
    "daily": "R6-daily-brief",
    "dashboard": "R6-dashboard",
    "tech": "R2-tech-seo",
    "content": "R3-content",
    "cro": "P5-cro",
    "geo": "P4-geo",
    "marketing-outbound": "R4-outbound",
    "backlink": "podC-backlink",
    "community": "R5-community",
    "social": "P6-social",
    "inquiry": "R6-inquiry-watch",
    "refresh": "podA-refresh",
    "weekly": "R1-weekly",
    "flywheel": "flywheel",
    "ads": "P8-ads",
    "metrics": "platform-metrics",
    "visual": "platform-visual",
    "tech/gtm": "R2-gtm",
}


def load_runs():
    if not os.path.exists(LOG):
        return []
    out = []
    for line in open(LOG, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    existing = load_runs()
    seen_outputs = {r.get("outputs") for r in existing if r.get("outputs")}
    new = []
    for area, agent in DIR_AGENT.items():
        d = os.path.join(WS, "08-execution", area)
        if not os.path.isdir(d):
            continue
        for fp in glob.glob(os.path.join(d, f"{a.date}-*.md")):
            rel = os.path.relpath(fp, WS)
            if rel in seen_outputs:
                continue
            new.append({
                "run_id": "auto-" + os.path.basename(fp).replace(".md", "")[:28],
                "at": dt.datetime.fromtimestamp(os.path.getmtime(fp)).astimezone().isoformat(timespec="seconds"),
                "agent": agent,
                "task": f"自动补记：{os.path.basename(fp)}",
                "inputs": "", "outputs": rel, "sources": "", "risks": "",
                "qa": "unknown",          # 从产物反推不出 QA，不假装
                "approved_by": "", "published_url": "", "review_due": "",
                "note": "由 run_log_autolog 从产物目录反推",
            })
            seen_outputs.add(rel)

    if not new:
        print(f"{a.date}：没有需要补记的产物（已全部记录）。")
        return 0
    print(f"{a.date}：补记 {len(new)} 条 run")
    for r in new:
        print(f"  + {r['agent']:22s} {r['outputs']}")
    if a.dry:
        print("（--dry：未写入）")
        return 0
    with open(LOG, "a", encoding="utf-8") as f:
        for r in new:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"→ {LOG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
