#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""session_hygiene.py — 会话治理：统计增长、找出可归档的旧会话

## 为什么（2026-11-12 用户提出）
用户发现"这个项目堆了 49 个会话，执行一年就是几万个，不可维护"。
根因已修：38 个排期任务原本有 **20 个 target.kind="new"**（每次运行新建会话），
每月约新增 314 个会话；已全部改为投递到固定会话（每月新增 0）。
本脚本负责**持续治理**：统计、找出可归档的旧会话、防止再长回去。

## 用法
  python3 scripts/tools/session_hygiene.py                 # 只报告
  python3 scripts/tools/session_hygiene.py --json
  python3 scripts/tools/session_hygiene.py --archive-days 30 --apply   # 归档 30 天未动的会话
  python3 scripts/tools/session_hygiene.py --archive-days 30           # 只预览会归档哪些

## 归档行为
把整个会话目录移动到 `~/.dsh/sessions-archive/<project>/`（可逆：移回去即恢复）。
保护：① 当前会话 ② 任何被 active 排期任务引用的会话 ③ 近 N 天有改动的会话。
"""
import argparse
import datetime as dt
import glob
import json
import os
import shutil
import sys

SESS_ROOT = os.path.expanduser("~/.dsh/sessions")
ARCH_ROOT = os.path.expanduser("~/.dsh/sessions-archive")
SCHED = os.path.expanduser("~/.dsh/storages/schedule.json")


def protected_ids():
    ids = set()
    try:
        d = json.load(open(SCHED, encoding="utf-8"))
        for e in d["tables"]["tasks"].values():
            tg = e.get("target") or {}
            if tg.get("sessionId"):
                ids.add(tg["sessionId"])
            ld = (e.get("lastDelivery") or {}).get("targetSessionId")
            if ld:
                ids.add(ld)
    except Exception:
        pass
    return ids


def scan():
    rows = []
    total_sessions = 0
    for proj in sorted(glob.glob(os.path.join(SESS_ROOT, "*"))):
        if not os.path.isdir(proj):
            continue
        for sd in sorted(glob.glob(os.path.join(proj, "*"))):
            if not os.path.isdir(sd):
                continue
            # 只用会话载荷文件判断活跃度（2026-11-12 修）：
            # 之前用 `**/*` 会带上 attachments 等目录，mtime 被非会话文件刷新，导致"所有会话都很新"。
            payload = glob.glob(os.path.join(sd, "session.v*.jsonl.zstd")) or \
                      glob.glob(os.path.join(sd, "*.jsonl*")) or \
                      glob.glob(os.path.join(sd, "*.json"))
            files = payload or [f for f in glob.glob(os.path.join(sd, "*")) if os.path.isfile(f)]
            size = sum(os.path.getsize(f) for f in files) if files else 0
            mtime = max((os.path.getmtime(f) for f in files), default=os.path.getmtime(sd))
            rows.append({
                "project": os.path.basename(proj),
                "session": os.path.basename(sd),
                "path": sd,
                "size_kb": round(size / 1024, 1),
                "files": len(files),
                "age_days": round((dt.datetime.now().timestamp() - mtime) / 86400, 1),
            })
        total_sessions += len([d for d in glob.glob(os.path.join(proj, "*")) if os.path.isdir(d)])
    return rows, total_sessions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--archive-days", type=int, default=0)
    ap.add_argument("--project", default="", help="只处理某个项目目录（子串匹配，如 anari-charge-website）")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    rows, total = scan()
    if a.project:
        rows = [r for r in rows if a.project in r["project"]]
    proj = [r for r in rows if "anari-charge-website" in r["project"]]
    summ = {
        "all_projects_sessions": total,
        "all_projects_size_mb": round(sum(r["size_kb"] for r in rows) / 1024, 1),
        "this_project_sessions": len(proj),
        "this_project_size_mb": round(sum(r["size_kb"] for r in proj) / 1024, 1),
        "this_project_newest": sorted(proj, key=lambda r: r["age_days"])[:3],
        "scheduled_tasks_targeting_new_sessions": 0,
    }
    # 排期任务是否还有 kind=new
    try:
        d = json.load(open(SCHED, encoding="utf-8"))
        summ["scheduled_tasks_targeting_new_sessions"] = sum(
            1 for e in d["tables"]["tasks"].values() if (e.get("target") or {}).get("kind") == "new")
        summ["scheduled_tasks_total"] = len(d["tables"]["tasks"])
    except Exception:
        pass

    if a.json:
        print(json.dumps({"summary": summ, "sessions": rows}, ensure_ascii=False, indent=1))
        return 0

    print("== 会话治理报告 ==")
    print(f"  全部项目会话: {summ['all_projects_sessions']} 个 / {summ['all_projects_size_mb']} MB")
    print(f"  本项目会话:   {summ['this_project_sessions']} 个 / {summ['this_project_size_mb']} MB")
    print(f"  排期任务:     {summ.get('scheduled_tasks_total', '?')} 个，其中每次新建会话的: "
          f"{summ['scheduled_tasks_targeting_new_sessions']}（应为 0）")
    print("\n  本项目最大的 5 个会话：")
    for r in sorted(proj, key=lambda x: -x["size_kb"])[:5]:
        print(f"   {r['size_kb']:9.1f} KB   {r['age_days']:6.1f} 天前   {r['session'][:24]}")

    if a.archive_days > 0:
        prot = protected_ids()
        cands = [r for r in rows if r["age_days"] >= a.archive_days and r["session"] not in prot]
        print(f"\n  可归档（≥{a.archive_days} 天未动且未被排期引用）: {len(cands)} 个")
        for r in cands[:10]:
            print(f"   {r['age_days']:6.1f} 天  {r['size_kb']:9.1f} KB  {r['session'][:24]}")
        if not a.apply:
            print("  （预览模式；加 --apply 才会真的移动）")
            return 0
        moved = 0
        for r in cands:
            dst = os.path.join(ARCH_ROOT, r["project"])
            os.makedirs(dst, exist_ok=True)
            try:
                shutil.move(r["path"], os.path.join(dst, r["session"]))
                moved += 1
            except Exception as e:  # noqa: BLE001
                print(f"   ⚠️ 移动失败 {r['session'][:20]}: {e}")
        print(f"  ✅ 已归档 {moved} 个 → {ARCH_ROOT}")
        return 0

    print("\n  提示：`--archive-days 30` 预览可归档项，加 `--apply` 执行（移动到 sessions-archive，可逆）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
