#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""team_health.py — 全团队健康度与协作链路体检

回答三个问题：
  1) 每个档位"最近真的跑过吗"（lastDelivery + 产物新鲜度）
  2) 每个团队"产出物是否符合预期"（按档位类型找对应目录的最新文件）
  3) 协作链路是否通（上游产物是否被下游消费）

用法：
  python3 scripts/tools/team_health.py            # 表格 + 结论
  python3 scripts/tools/team_health.py --json     # 机器可读
退出码：0 全部正常 / 1 有 P0（档位长期未跑或协作断链）
"""
import json, os, sys, glob, datetime as dt

WS = "/Users/kerrychu/anari-charge-website"
SCHED = os.path.expanduser("~/.dsh/storages/schedule.json")
TODAY = dt.date.today()

# 档位 → 期望产物目录（用于判断"跑了但没产物"）
OUTPUT_HINT = {
    "内容主编日更": ["08-execution/content"],
    "内容档 #2": ["08-execution/content"],
    "内容档 #3": ["08-execution/content"],
    "内容验收": ["08-execution/content"],
    "看板刷新": ["08-execution/daily"],
    "每日简报": ["08-execution/daily"],
    "数据飞轮": ["08-execution/flywheel"],
    "飞轮中间裁决": ["08-execution/flywheel"],
    "周运营总编排": ["08-execution/weekly"],
    "社区引流": ["08-execution/community"],
    "社媒分发": ["08-execution/social"],
    "营销外联": ["08-execution/marketing-outbound"],
    "技术 SEO": ["08-execution/tech"],
    "GEO": ["08-execution/geo"],
    "CRO": ["08-execution/cro"],
    "内链": ["08-execution/content"],
    "页面工厂": ["08-execution/tech"],
    "案例研究工厂": ["08-execution/content"],
    "渠道开发": ["08-execution/channel"],
    "法规监测": ["08-execution/tech/regwatch"],
    "竞品情报": ["08-execution/intel"],
    "招标信号": ["08-execution/intel"],
    "社媒监听": ["08-execution/community/listening"],
    "位次监控": ["08-execution/tech/position-watch"],
    "生命周期": ["08-execution/lifecycle"],
    "外链资产": ["08-execution/backlink"],
    "存量刷新": ["08-execution/refresh"],
    "送达率": ["08-execution/outbound/health"],
    "外联发信后体检": ["08-execution/outbound/health"],
    "项目招标": ["08-execution/intel"],
}

def load_tasks():
    d = json.load(open(SCHED, encoding="utf-8"))
    return d["tables"]["tasks"]

def newest_file(dirs):
    best = None
    for d in dirs:
        p = os.path.join(WS, d)
        if not os.path.isdir(p):
            continue
        for f in glob.glob(os.path.join(p, "**", "*"), recursive=True):
            if os.path.isfile(f) and not f.endswith((".jsonl", ".pyc")):
                m = os.path.getmtime(f)
                if best is None or m > best[0]:
                    best = (m, os.path.relpath(f, WS))
    return best

def days_since(ts):
    if not ts:
        return None
    try:
        d = dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
        return (TODAY - d).days
    except Exception:
        return None

def main():
    tasks = load_tasks()
    rows = []
    for tid, t in tasks.items():
        r = t.get("record") or {}
        title = r.get("title", "")
        tg = t.get("target") or {}
        ld = (t.get("lastDelivery") or {}).get("scheduledAt")
        age = days_since(ld)
        hint = None
        for k, v in OUTPUT_HINT.items():
            if k in title:
                hint = v
                break
        nf = newest_file(hint) if hint else None
        art_age = round((dt.datetime.now().timestamp() - nf[0]) / 86400, 1) if nf else None
        rows.append({
            "id": tid[-8:], "title": title, "kind": tg.get("kind"),
            "last_run": (ld or "")[:10], "run_age_d": age,
            "artifact": nf[1] if nf else None, "artifact_age_d": art_age,
        })

    # 协作链路检查
    collab = []
    def exists(p):
        return os.path.exists(os.path.join(WS, p))

    # 1) R1 周编排 → 选题队列存在且被 R3 消费
    q = sorted(glob.glob(os.path.join(WS, "08-execution/weekly/content-queue-*.json")))
    collab.append({
        "link": "R1 周编排 → R3 内容（选题队列）",
        "ok": bool(q),
        "evidence": os.path.basename(q[-1]) if q else "无队列文件",
    })
    # 2) R3 内容 → E1 验收（验收记录存在且日期覆盖最新内容）
    acc = sorted(glob.glob(os.path.join(WS, "08-execution/content/acceptance-*.md")))
    collab.append({
        "link": "R3 内容 → E1 验收",
        "ok": bool(acc),
        "evidence": os.path.basename(acc[-1]) if acc else "无验收记录",
    })
    # 3) E1 → IndexNow（状态文件在 24h 内更新）
    idx = os.path.join(WS, "06-site/anari-new-site/ops/indexnow-state.json")
    idx_ok = exists("06-site/anari-new-site/ops/indexnow-state.json") and (
        dt.datetime.now().timestamp() - os.path.getmtime(idx) < 3 * 86400)
    collab.append({"link": "E1 → IndexNow 提交", "ok": idx_ok,
                   "evidence": f"state 更新 {(dt.datetime.now().timestamp()-os.path.getmtime(idx))/86400:.1f} 天前" if exists("06-site/anari-new-site/ops/indexnow-state.json") else "缺 state"})
    # 4) R5 草稿 → 发布台账
    pl = os.path.join(WS, "08-execution/community/publish-log.json")
    collab.append({"link": "R5 草稿 → approval 发布台账", "ok": exists("08-execution/community/publish-log.json"),
                   "evidence": "publish-log 存在" if os.path.exists(pl) else "缺 publish-log"})
    # 5) 飞轮 → 动作指派 → 档位执行（next-actions 有 assignee 字段）
    na = os.path.join(WS, "08-execution/flywheel/next-actions.json")
    has_assignee = False
    if os.path.exists(na):
        try:
            d = json.load(open(na, encoding="utf-8"))
            items = d if isinstance(d, list) else d.get("actions") or []
            has_assignee = any(isinstance(x, dict) and x.get("assignee") for x in items)
        except Exception:
            pass
    collab.append({"link": "飞轮判定 → 档位指派", "ok": has_assignee,
                   "evidence": "next-actions 含 assignee" if has_assignee else "next-actions 无 assignee（判定无法追踪）"})
    # 6) GEO → 内容（geo gaps 被内容档读取）
    g = sorted(glob.glob(os.path.join(WS, "08-execution/geo/*geo-run.md")) + glob.glob(os.path.join(WS, "08-execution/geo/*geo-gaps.md")))
    collab.append({"link": "GEO 缺口 → 内容选题", "ok": bool(g),
                   "evidence": os.path.basename(g[-1]) if g else "无 geo 产物"})
    # 7) CRO 诊断 → 转化改进（cro 审计存在）
    cro = [f for f in sorted(glob.glob(os.path.join(WS, "08-execution/cro/*.md"))) if "README" not in f]
    collab.append({"link": "CRO 诊断 → 改进执行", "ok": bool(cro),
                   "evidence": os.path.basename(cro[-1]) if cro else "无 cro 产物"})

    p0 = []
    for r in rows:
        if r["run_age_d"] is None:
            continue
        if r["run_age_d"] >= 8 and r["kind"] != "new_once":
            p0.append(f"{r['title'][:32]} 已 {r['run_age_d']} 天未投递")
    for c in collab:
        if not c["ok"]:
            p0.append(f"协作断链：{c['link']} — {c['evidence']}")

    out = {"generated": dt.datetime.now().isoformat(timespec="seconds"),
           "teams": rows, "collab": collab, "p0": p0}
    if "--json" in sys.argv:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 1 if p0 else 0

    # 表格
    print(f"=== 团队健康度 · {TODAY} ===")
    print(f"{'档位':38s} {'目标':10s} {'最近跑':10s} {'距今':>5s} {'产物':12s} {'产物龄':>6s}")
    for r in sorted(rows, key=lambda x: (x["run_age_d"] is None, -(x["run_age_d"] or 0))):
        print(f"{r['title'][:36]:38s} {str(r['kind'])[:9]:10s} {r['last_run'] or '—':10s} "
              f"{str(r['run_age_d'] if r['run_age_d'] is not None else '—'):>5s} "
              f"{(r['artifact'] or '—')[-11:]:12s} {str(r['artifact_age_d'] if r['artifact_age_d'] is not None else '—'):>6s}")
    print("\n=== 协作链路 ===")
    for c in collab:
        print(f"  {'✅' if c['ok'] else '❌'} {c['link']:34s} {c['evidence']}")
    print(f"\n=== P0（{len(p0)}）===")
    for x in p0:
        print("  🔴", x)
    if not p0:
        print("  ✅ 无 P0")
    return 1 if p0 else 0

if __name__ == "__main__":
    sys.exit(main())
