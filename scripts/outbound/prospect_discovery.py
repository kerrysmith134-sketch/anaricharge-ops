#!/usr/bin/env python3
"""prospect_discovery.py — 外链/媒体目标的持续发现与入池流水线。

## 为什么存在
静态名单一定会耗尽：16 个发完就没了。外链要持续，必须有个"每周自动发现新目标"的机制。
本脚本负责**流水线的后半段**（去重 / 富化 / 入池 / 入活动）；
前半段（发现）由每周定时任务里的 agent 用搜索完成，写入 candidates JSON。

## 数据流
  agent 搜索 → candidates-<日期>.json
     → queue（本脚本：去重 + 公开层富化 + 入池）
     → browse（可选：浏览器层补邮箱）
     → load（导入到营销活动）
     → report（看产出率，反推下轮该调什么）

## 用法
  python3 scripts/outbound/prospect_discovery.py queue  <candidates.json>
  python3 scripts/outbound/prospect_discovery.py browse <N>            # 对池内待挖的前 N 个跑浏览器层
  python3 scripts/outbound/prospect_discovery.py load   <campaign_id>  --confirm
  python3 scripts/outbound/prospect_discovery.py report
"""
import argparse
import datetime as dt
import json
import os
import sys

WS = "/Users/kerrychu/anari-charge-website"
OUT = os.path.join(WS, "08-execution", "marketing-outbound")
POOL = os.path.join(OUT, "prospect-pool.jsonl")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 已是目标/已联系过的域名都在这些台账里
LEDGERS = ["media-targets-20261107.json", "media-targets-wave3.json"]


def known_domains():
    d = set()
    for f in LEDGERS:
        p = os.path.join(OUT, f)
        if not os.path.exists(p):
            continue
        for t in json.load(open(p, encoding="utf-8")):
            if t.get("domain"):
                d.add(t["domain"].lower())
    if os.path.exists(POOL):
        for line in open(POOL, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            if r.get("domain"):
                d.add(r["domain"].lower())
    return d


def read_pool():
    if not os.path.exists(POOL):
        return []
    rows = []
    for line in open(POOL, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    return rows


def write_pool(rows):
    with open(POOL, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def today():
    return dt.date.today().isoformat()


def cmd_queue(path):
    import email_enrichment as ee
    cands = json.load(open(path, encoding="utf-8"))
    if isinstance(cands, dict):
        cands = cands.get("candidates") or []
    known = known_domains()
    pool = read_pool()
    added, skipped = 0, 0
    for c in cands:
        dom = (c.get("domain") or "").lower().strip()
        if not dom or dom in known:
            skipped += 1
            continue
        e = ee.enrich(dom, allow_paid=False)
        top = (e["results"] or [{}])[0]
        row = {
            "name": c.get("name") or dom,
            "domain": dom,
            "type": c.get("type") or "unknown",
            "angle": c.get("angle") or "",
            "source_query": c.get("source_query") or "",
            "discovered_at": today(),
            "email": top.get("email", ""),
            "email_source": top.get("source", ""),
            "status": "ready" if top.get("email") else "needs_email",
            "campaign_id": None,
        }
        pool.append(row)
        known.add(dom)
        added += 1
        print(f"  + {row['name'][:28]:30s} {dom:30s} {row['email'] or '（待挖）'}")
    write_pool(pool)
    ready = sum(1 for r in pool if r["status"] == "ready" and not r.get("campaign_id"))
    print(f"\n新增 {added} | 跳过重复 {skipped} | 池内待投 {ready} / 共 {len(pool)}")
    return 0


def cmd_browse(n):
    import email_enrichment as ee
    pool = read_pool()
    todo = [r for r in pool if r["status"] == "needs_email"][:n]
    if not todo:
        print("没有待挖目标")
        return 0
    print(f"对 {len(todo)} 个目标跑浏览器层（增量落盘）…")
    for r in todo:
        e = ee.browser_scan(r["domain"])
        top = (e["results"] or [{}])[0]
        if top.get("email"):
            r["email"] = top["email"]
            r["email_source"] = top.get("source", "browser")
            r["status"] = "ready"
        print(f"  {'✅' if r.get('email') else '❌'} {r['domain']:32s} {r.get('email') or '（仍未找到）'}")
        write_pool(pool)  # 增量落盘
    ready = sum(1 for x in pool if x["status"] == "ready" and not x.get("campaign_id"))
    print(f"\n池内待投 {ready}")
    return 0


def cmd_load(campaign_id, confirm=False):
    import instantly_client as ic
    pool = read_pool()
    todo = [r for r in pool if r["status"] == "ready" and not r.get("campaign_id")]
    if not todo:
        print("没有可导入的 ready 目标")
        return 0
    if not confirm:
        print(f"[dry-run] 将导入 {len(todo)} 条到 {campaign_id}：")
        for r in todo:
            print(f"  - {r['email']:36s} {r['name']}")
        print("\n加 --confirm 才会真的导入")
        return 0
    ok = 0
    for r in todo:
        try:
            ic.call("/leads", "POST", {"campaign": campaign_id, "email": r["email"],
                                       "company_name": r["name"],
                                       "personalization": (r.get("angle") or "")[:200]})
            r["campaign_id"] = campaign_id
            r["status"] = "loaded"
            ok += 1
        except SystemExit as e:
            print(f"  ✗ {r['email']}: {str(e)[:100]}")
        write_pool(pool)
    print(f"导入 {ok}/{len(todo)}")
    return 0


def cmd_report():
    pool = read_pool()
    if not pool:
        print("池为空")
        return 0
    from collections import Counter
    by_status = Counter(r["status"] for r in pool)
    by_type = Counter(r.get("type") or "unknown" for r in pool)
    by_query = Counter((r.get("source_query") or "unknown")[:48] for r in pool if r.get("source_query"))
    total = len(pool)
    with_email = sum(1 for r in pool if r.get("email"))
    print(f"池内 {total} 个 | 有邮箱 {with_email}（{with_email/total*100:.0f}%）")
    print("状态:", dict(by_status))
    print("类型:", dict(by_type))
    if by_query:
        print("按发现来源的产出（哪个搜索式最有效）：")
        for q, n in by_query.most_common(10):
            got = sum(1 for r in pool if (r.get("source_query") or "")[:48] == q and r.get("email"))
            print(f"  {n:>3} 个 / 有邮箱 {got:>2}  ← {q}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["queue", "browse", "load", "report"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args()
    if a.cmd == "queue":
        if not a.args:
            raise SystemExit("用法: queue <candidates.json>")
        return cmd_queue(a.args[0])
    if a.cmd == "browse":
        return cmd_browse(int(a.args[0]) if a.args else 5)
    if a.cmd == "load":
        if not a.args:
            raise SystemExit("用法: load <campaign_id> [--confirm]")
        return cmd_load(a.args[0], confirm=a.confirm)
    return cmd_report()


if __name__ == "__main__":
    sys.exit(main())
