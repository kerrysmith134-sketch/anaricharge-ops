#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lead_pipeline.py — 询盘守夜的"一条命令"（D1 → 账本 → Brevo Deals）

## 为什么要有这个入口
守夜的执行者是定时任务里的 agent，它每 4 小时跑一次。如果让它记 5 条命令、
判断 3 个先后顺序，实际就会漏。所以把链路压成一个 `tick`：

    D1 新询盘 → 账本(new) → 已判资格的推 Brevo Deals → 输出"下一步该人做什么"

**它不做判断**：不替人 qualify、不改状态、不发信。只做幂等同步与摘要。

## 用法
  python3 scripts/metrics/lead_pipeline.py tick            # 守夜档位调用这个
  python3 scripts/metrics/lead_pipeline.py tick --dry      # 只读，不写 Brevo
  python3 scripts/metrics/lead_pipeline.py status          # 看账本各状态计数
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def cmd_tick(a):
    import lead_lifecycle as L
    import brevo_crm as B

    print("== 1) 拉 D1 新询盘进账本 ==")
    class _A:  # 复用 sync 的参数形态
        pass
    rc = L.cmd_sync(_A())
    recs = list(L.load().values())

    by = {}
    for r in recs:
        by.setdefault(r["status"], []).append(r)
    print("\n== 2) 账本状态 ==")
    if not recs:
        print("  账本为空（D1 无询盘）——北极星为 0 时先看流量与转化，不要加页面。")
    else:
        for s in L.STATES:
            if by.get(s):
                print(f"  {s:14s} {len(by[s])}")
        # 需要人判资格的
        news = by.get("new") or []
        if news:
            print(f"\n  ⚠ {len(news)} 条 new 需要判资格（六条件，缺一项进不了 SAQO）：")
            for r in news[:10]:
                print(f"    - {r['submission_id'][:16]}  {r.get('country') or '-'}  "
                      f"{r.get('project_type') or '-'}  {r.get('email','')[:30]}")
            print(f"    → python3 scripts/metrics/lead_lifecycle.py qualify <sid> "
                  f"--real-contact --icp --market --need --trigger --accepted")

    print("\n== 3) 已判资格 → Brevo Deals（幂等）==")
    if a.dry:
        print("  （--dry：跳过写入）")
    else:
        pushable = [r for r in recs if r.get("status") in B.PUSH_STATUSES]
        if not pushable:
            print("  没有 mql/sal/saqo/won/lost 的记录，无需推送。")
        else:
            push_rc = B.cmd_push(type("P", (), {"dry": False})())
            if push_rc:
                print("  ⚠ 推送有失败项，见上")

    print("\n== 3b) 生命周期事件 → GA4（Measurement Protocol）==")
    try:
        import ga4_events as G
        G.cmd_sync(type("Q", (), {})())
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠ GA4 事件同步异常（不影响账本/Brevo）：{type(e).__name__}: {str(e)[:120]}")

    print("\n== 4) 下一步（人来做的）==")
    if not recs:
        print("  无。等真实询盘。")
    else:
        todo = []
        if by.get("new"):
            todo.append(f"判资格 {len(by['new'])} 条（qualify 六条件）")
        if by.get("mql"):
            todo.append(f"mql {len(by['mql'])} 条：决定是否 SAL（销售接受）")
        if by.get("sal"):
            todo.append(f"sal {len(by['sal'])} 条：补齐六条件后可进 SAQO（北极星）")
        print("  " + ("；".join(todo) if todo else "无待办"))
        print("  对账（每周）：python3 scripts/metrics/brevo_crm.py verify")
    return rc if rc else 0


def cmd_status(a):
    import lead_lifecycle as L
    recs = list(L.load().values())
    if not recs:
        print("账本为空。")
        return 0
    for s in L.STATES:
        n = sum(1 for r in recs if r["status"] == s)
        if n:
            print(f"  {s:14s} {n}")
    tot = sum((r.get("pipeline_value") or 0) for r in recs if r["status"] in ("saqo", "won"))
    print(f"  {'pipeline':14s} {tot:,} USD")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("tick"); p.add_argument("--dry", action="store_true")
    sub.add_parser("status")
    a = ap.parse_args()
    return {"tick": cmd_tick, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
