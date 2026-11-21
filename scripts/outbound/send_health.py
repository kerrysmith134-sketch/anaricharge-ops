#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""send_health.py — 外联"发信后早期体检"（比等到 24h 更早发现异常）

## 为什么需要
冷邮件出问题最贵的是"发了很多才发现"。典型三种：
1. 退信率高（名单脏 / 域名声誉 / DMARC 未对齐）→ 继续发就烧域名
2. 零打开（进垃圾箱）→ 主题/发件人信誉问题，再发也没用
3. 有回复但没人接手 → 错过黄金 48 小时

所以在**首封发出后 6 小时**先看一批，比等一天早半天。

## 用法
  python3 scripts/outbound/send_health.py                 # 全部活动
  python3 scripts/outbound/send_health.py --only WAVE1
  python3 scripts/outbound/send_health.py --json
退出码：0 = 正常；1 = 触发红线（退信 >3% 或投诉 >0.1%）；2 = 需要留意（零打开等）
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import marketing_outbound as M  # noqa: E402
import instantly_client as ic  # noqa: E402

BOUNCE_RED = 3.0       # %
COMPLAINT_RED = 0.1    # %
MIN_SAMPLE = 3         # 少于此数不下结论（12 封的时候尤其重要）


def opens_for(campaign_id):
    """尝试取打开数；Instantly 不同版本字段名不同，取不到就返回 None（不猜）。"""
    try:
        a = ic.call("/campaigns/analytics")
        rows = a if isinstance(a, list) else (a.get("items") or [])
        for r in rows:
            if (r.get("campaign_id") or r.get("id")) == campaign_id:
                for k in ("emails_opened_count", "unique_opened_count", "open_count", "opens"):
                    v = r.get(k)
                    if isinstance(v, (int, float)):
                        return int(v)
    except SystemExit:
        pass
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="只查名称包含该串的活动")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    rows = []
    red = []
    warn = []
    for c in M.marketing_campaigns():
        name = c.get("name") or ""
        if a.only and a.only.lower() not in name.lower():
            continue
        st = M.status()["campaigns"]
        row = next((x for x in st if x["campaign"] == name), {})
        sent = int(row.get("sent") or 0)
        bou = int(row.get("bounces") or 0)
        rep = int(row.get("replies_unique") or 0)
        opens = opens_for(c.get("id") or "")
        b_rate = (bou / sent * 100) if sent else 0.0
        # 活动自身的计划开始日（campaign_schedule.start_date）——不是顶层 start_date。
        # 2026-11-09 踩过：活动 status=active 但 start_date=次日，当天 0 封，
        # 脚本只说"尚未发信"，让人误以为发信失败。
        sched = {}
        try:
            full = ic.call("/campaigns/" + (c.get("id") or ""))
            sched = (full.get("campaign_schedule") or {})
        except SystemExit:
            sched = {}
        plan_start = sched.get("start_date") or (c.get("start_date") or "")

        item = {
            "campaign": name, "status": c.get("status"), "sent": sent,
            "planned_start": plan_start,
            "bounces": bou, "bounce_rate_pct": round(b_rate, 2),
            "replies": rep, "opens": opens,
            "leads": row.get("leads_actual"),
        }
        rows.append(item)
        if sent >= MIN_SAMPLE:
            if b_rate > BOUNCE_RED:
                red.append(f"{name}: 退信率 {b_rate:.1f}% > {BOUNCE_RED}%")
            if opens == 0 and sent >= 5:
                warn.append(f"{name}: 已发 {sent} 封但 0 打开（可能进垃圾箱）")
            if rep > 0:
                warn.append(f"{name}: 有 {rep} 条回复 → 立刻跟进（优先级最高）")
        elif sent > 0:
            warn.append(f"{name}: 已发 {sent} 封（<{MIN_SAMPLE}），样本太小不下结论")

    if a.json:
        print(json.dumps({"rows": rows, "red": red, "warn": warn}, ensure_ascii=False, indent=1))
    else:
        print("=== 外联发送体检 ===")
        for r in rows:
            print(f"  {r['campaign'][:40]:42s} status={r['status']} lead={r['leads']} "
                  f"sent={r['sent']} bounce={r['bounces']}({r['bounce_rate_pct']}%) "
                  f"reply={r['replies']} open={r['opens'] if r['opens'] is not None else '?'} "
                  f"计划开始={r.get('planned_start') or '未设'}")
        not_started = [r for r in rows if r["sent"] == 0 and r.get("planned_start")]
        if not_started and not red and not warn:
            import datetime as _dt
            today = _dt.date.today().isoformat()
            for r in not_started:
                ps = r["planned_start"]
                if ps and ps > today:
                    print(f"\n⏳ {r['campaign']}: 尚未开始（计划 {ps}），今天 0 封是正常的，不是失败")
        if red:
            print("\n🔴 红线：")
            for x in red: print("  -", x)
        if warn:
            print("\n🟡 留意：")
            for x in warn: print("  -", x)
        if not red and not warn:
            print("\n✅ 无异常（或尚未发信）")
    return 1 if red else (2 if warn else 0)


if __name__ == "__main__":
    raise SystemExit(main())
