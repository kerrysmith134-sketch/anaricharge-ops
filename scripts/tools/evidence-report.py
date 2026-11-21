#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evidence-report.py — 证据台账体检（Growth OS GROW-010）

计划要求：每条可能影响采购决策的数字都要有 Evidence ID + 来源 + 核验日期 +
适用范围 + 限制 + 责任人；过期时页面显示"需复核"。

现实：`ops/fact-library.json` 已有 id / value / status / must_match / pages，
但**缺 source / verified_at / owner**。本脚本不编造来源，只做两件事：
  1. 统计覆盖率（有多少条有来源/日期/责任人）
  2. 列出缺口清单，按"影响面"排序（被越多页面引用的越该先补）

用法：
  python3 scripts/tools/evidence-report.py            # 汇总
  python3 scripts/tools/evidence-report.py --list 25  # 列出前 25 条缺口
"""
import argparse
import json
import os

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIB = os.path.join(WS, "06-site/anari-new-site/ops/fact-library.json")
# 真实字段（2026-11-08 核对 ops/fact-library.json 确认）：
#   source=出处  last_verified=出处页 Last verified 日期  review_by=下次复核截止  scope=适用范围
FIELDS = ["source", "last_verified", "review_by", "scope"]
TEMPLATE_IDS = ("点分命名：类别.对象.属性",)   # 库里第一条是 schema 说明，不是事实


def walk(o, acc):
    if isinstance(o, list):
        for x in o:
            walk(x, acc)
    elif isinstance(o, dict):
        if isinstance(o.get("id"), str) and "value" in o and o["id"] not in TEMPLATE_IDS:
            acc.append(o)
        for v in o.values():
            if isinstance(v, (list, dict)):
                walk(v, acc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", type=int, default=0, help="列出前 N 条缺口")
    a = ap.parse_args()

    lib = json.load(open(LIB, encoding="utf-8"))
    facts = []
    walk(lib, facts)
    total = len(facts)
    have = {f: sum(1 for x in facts if x.get(f)) for f in FIELDS}
    verified = sum(1 for x in facts if x.get("status") == "verified")

    print(f"事实条目 {total}（status=verified {verified}）")
    for f in FIELDS:
        print(f"  有 {f:12s} {have[f]:3d}/{total}  ({have[f]/total*100:.0f}%)")

    gaps = [x for x in facts if not all(x.get(f) for f in FIELDS)]

    def pages_of(x):
        chk = x.get("check")
        p = x.get("pages") or (chk.get("pages") if isinstance(chk, dict) else []) or []
        return len(p) if isinstance(p, list) else 0

    gaps.sort(key=lambda x: (-pages_of(x), x["id"]))
    print(f"\n缺口 {len(gaps)} 条（按被引用页面数排序，先补影响面大的）")
    if a.list:
        print(f"{'pages':>5}  {'id':34s} {'缺':16s} value")
        for x in gaps[: a.list]:
            miss = ",".join(f for f in FIELDS if not x.get(f))
            print(f"{pages_of(x):>5}  {x['id'][:34]:34s} {miss:16s} {str(x.get('value'))[:44]}")

    import datetime as _dt
    today = _dt.date.today().isoformat()
    overdue = [x for x in facts if (x.get("review_by") or "") and str(x["review_by"]) < today]
    print(f"\n已过期需复核 {len(overdue)} 条（review_by < {today}）")
    for x in overdue[: a.list or 8]:
        print(f"   {x['id'][:38]:38s} review_by={x['review_by']}  {str(x.get('value'))[:40]}")

    print("\n说明：本脚本**不生成**来源。补台账要靠人或现场资料；"
          "没有来源的数字应降级为 needs_review，而不是继续被页面引用。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
