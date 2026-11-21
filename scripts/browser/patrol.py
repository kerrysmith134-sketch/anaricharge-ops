#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patrol.py — 浏览器卫生巡检哨兵

## 为什么有这个
R10 说"结束前必须 hygiene"，但那是**自觉**。2026-11-10 复查发现仍有档位留标签。
现在的防线是三层：
  1. `wb.py` 进程退出 atexit 兜底（脚本异常也不会漏）
  2. 关键脚本 try/finally cleanup（approval / geo / ops）
  3. **本脚本**：定期巡检，发现残留就清掉并记录是谁留下的会话名

## 用法
  python3 scripts/browser/patrol.py            # 巡检 + 清理 + 写台账
  python3 scripts/browser/patrol.py --quiet    # 只有发现残留才输出（给定时任务用）
退出码：0 = 干净或已清理；2 = 检查失败（daemon 不可用）
"""
import argparse
import datetime as dt
import json
import os
import sys

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(WS, "scripts", "browser"))

LEDGER = os.path.join(WS, "08-execution", "tech", "browser-patrol.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    try:
        from wb import tabs_summary, cleanup_all, tabs_all
    except Exception as e:  # noqa: BLE001
        print(f"❌ 无法加载 wb：{e}")
        return 2

    found = tabs_summary()
    total = sum(f["count"] for f in found)
    if not total:
        if not a.quiet:
            print("✅ 浏览器干净：0 个残留标签")
        return 0

    print(f"⚠️ 发现 {total} 个残留标签，来源会话：")
    for f in found:
        print(f"   {f['session']:12s} {f['count']} 个  {', '.join(f['titles'][:2])}")
    closed = cleanup_all(verbose=False)
    after = sum(x["count"] for x in tabs_all()) if callable(tabs_all) else 0
    rec = {"at": dt.datetime.now().isoformat(timespec="seconds"),
           "leftover_total": total, "sessions": found, "closed": closed, "after": after}
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"🧹 已清理 {closed} 个 → 剩余 {after}；台账 {LEDGER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
