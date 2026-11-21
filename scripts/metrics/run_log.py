#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_log.py — Agent 运行日志（Growth OS GROW-011）

计划要求：每次 Agent 执行至少留下 run_id / Agent / 任务目标 / 输入快照 /
使用工具 / 产出物 URI / 依据来源 / 风险与待确认项 / QA 结果 / 审批人 /
发布 URL / 7-14-30 天结果指标。

现实问题：12 个定时任务各自写各自的执行记录，**格式不统一、无法横向比较**，
"这个 Agent 上周到底做了什么、有没有用" 只能靠翻文件。

本脚本给一个统一的追加式日志（JSONL），并提供 CLI 让任意脚本/任务写一条。
不假装已经全自动接线——**接线是逐步的**，先让"写一条 run"这件事变便宜。

用法：
  python3 scripts/metrics/run_log.py append --agent R3-content --task "写 cost guide" \
      --output 08-execution/content/xxx.md --qa pass --note "过了事实门禁"
  python3 scripts/metrics/run_log.py list --days 7
  python3 scripts/metrics/run_log.py summary            # 按 Agent 聚合近 30 天
"""
import argparse
import datetime as dt
import json
import os
import uuid

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG = os.path.join(WS, "08-execution", "run-log.jsonl")


def now():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def append(a):
    rec = {
        "run_id": a.run_id or uuid.uuid4().hex[:12],
        "at": now(),
        "agent": a.agent,
        "task": a.task,
        "inputs": a.inputs or "",
        "outputs": a.output or "",
        "sources": a.sources or "",
        "risks": a.risks or "",
        "qa": a.qa,
        "approved_by": a.approved_by or "",
        "published_url": a.published or "",
        "review_due": a.review_due or "",
        "note": a.note or "",
    }
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"logged {rec['run_id']} · {rec['agent']} · qa={rec['qa']} → {LOG}")


def load():
    if not os.path.exists(LOG):
        return []
    out = []
    with open(LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def cmd_list(a):
    cutoff = (dt.datetime.now().astimezone() - dt.timedelta(days=a.days)).isoformat()
    rows = [r for r in load() if r.get("at", "") >= cutoff]
    if not rows:
        print(f"近 {a.days} 天没有 run 记录。")
        return 0
    print(f"{'at':<20} {'agent':<18} {'qa':<6} task")
    for r in rows[-a.limit:]:
        print(f"{r['at'][:19]:<20} {r['agent'][:18]:<18} {r.get('qa',''):<6} {r.get('task','')[:56]}")
    print(f"\n共 {len(rows)} 条")
    return 0


def cmd_summary(a):
    cutoff = (dt.datetime.now().astimezone() - dt.timedelta(days=a.days)).isoformat()
    rows = [r for r in load() if r.get("at", "") >= cutoff]
    if not rows:
        print(f"近 {a.days} 天没有 run 记录 → Agent 产出无法横向比较。")
        return 0
    agg = {}
    for r in rows:
        k = r["agent"]
        d = agg.setdefault(k, {"runs": 0, "pass": 0, "fail": 0, "unknown": 0, "outputs": 0})
        d["runs"] += 1
        qa = r.get("qa")
        d["pass" if qa == "pass" else ("unknown" if qa == "unknown" else "fail")] += 1
        if r.get("outputs"):
            d["outputs"] += 1
    print(f"{'agent':<20} {'runs':>5} {'pass':>5} {'fail':>5} {'unknown':>8} {'有产出':>7}")
    for k, v in sorted(agg.items(), key=lambda kv: -kv[1]["runs"]):
        print(f"{k[:20]:<20} {v['runs']:>5} {v['pass']:>5} {v['fail']:>5} {v['unknown']:>8} {v['outputs']:>7}")
    print("\nunknown = 从产物反推的记录（不知道 QA 结果，不假装知道）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("append")
    p.add_argument("--agent", required=True)
    p.add_argument("--task", required=True)
    p.add_argument("--inputs", default="")
    p.add_argument("--output", default="")
    p.add_argument("--sources", default="")
    p.add_argument("--risks", default="")
    p.add_argument("--qa", default="pass", choices=["pass", "fail", "skipped"])
    p.add_argument("--approved-by", default="")
    p.add_argument("--published", default="")
    p.add_argument("--review-due", default="")
    p.add_argument("--note", default="")
    p.add_argument("--run-id", default="")
    p = sub.add_parser("list"); p.add_argument("--days", type=int, default=7); p.add_argument("--limit", type=int, default=40)
    p = sub.add_parser("summary"); p.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    return {"append": append, "list": cmd_list, "summary": cmd_summary}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
