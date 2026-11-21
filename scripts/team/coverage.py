#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""coverage.py — 团队编制覆盖率与权限合规检查

回答两个问题：
1. **42 个角色里，谁真的有人在做、谁只是纸面**（full / partial / gap / 政策不设）
2. **已排期的档位有没有越权**：v5 规格里每个 Agent 有明确 Permission_Boundary
   （例如"只能提案，不能发布/发送"）。扫描每个定时任务的提示词，
   如果出现"发送/发帖/发布/投放/删除"这类不可逆动作，而该 Agent 的边界不允许，
   就报违规。

用法：
  python3 scripts/team/coverage.py            # 覆盖率 + 权限检查
  python3 scripts/team/coverage.py --json out.json
退出码：有权限违规返回 1（可接进 selftest）。
"""
import argparse
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
ROSTER = os.path.join(WS, "03-workflows", "TEAM-V5-ROSTER.json")
SCHED = os.path.expanduser("~/.dsh/storages/schedule.json")

# 只抓**强指令**（"直接发/代发/发布到/开启投放"），不做模糊词命中。
# 第一版用"发送/发布"单词匹配，结果 18 条全是噪音：
# "不发布""等用户授权""草稿"全被当成违规 → 报警太多等于没有报警。
STRONG = {
    "external_send": [r"直接(?:发送|发出)", r"代发", r"自动(?:发送|发出)", r"无需确认(?:就)?发送",
                      r"send (?:it )?now", r"auto-send"],
    "publish": [r"直接(?:发布|上线)", r"自动发布", r"发布到(?:线上|站点)",
                r"publish (?:it )?now", r"auto-publish"],
    "post": [r"直接(?:发帖|发布到社区)", r"代发(?:帖|回答)", r"自动发帖"],
    "spend": [r"直接(?:投放|加预算)", r"开启投放", r"activate (?:the )?campaign now"],
    "delete": [r"直接删除", r"批量删除", r"drop table"],
}
# 任务里写明这些守卫 = 合规（不代发、等授权、只出草稿）
GUARDS = [r"不代发", r"不(?:直接)?发送", r"不(?:直接)?发布", r"不(?:直接)?发帖",
          r"不投放", r"不互动", r"只读", r"等用户授权", r"逐次(?:人工)?确认",
          r"草稿", r"待审", r"不代注册", r"授权后再", r"需用户(?:确认|授权)"]
# 任务标题 → Agent 映射（人工核定，宁缺不猜）
TASK_AGENT = [
    (r"总编排", "A00"), (r"进度播报", "A00"), (r"增长脉冲", "A00"),
    (r"内容主编|内容生产", "A21"), (r"技术 SEO|技术SEO", "A16"),
    (r"GEO", "A17"), (r"外联|Marketing Outbound", "A29"),
    (r"社区", "A27"), (r"社媒", "A27"), (r"广告", "A33"),
    (r"查词|关键词", "A15"), (r"索引", "A16"), (r"内链", "A15"),
    (r"询盘|表单", "A36"), (r"外链资产", "A29"), (r"看板|数据", "A37"),
    (r"守夜", "A36"), (r"简报|总结", "A00"), (r"复盘|飞轮", "A41"),
    (r"刷新|机会", "A15"), (r"本地化|RU|ES", "A24"),
    (r"CRO|转化优化", "A35"), (r"总结|值班长", "A00"),
    (r"程序化|批量页", "A15"), (r"页面工厂|建站", "A34"),
]


def load_roster():
    return json.load(open(ROSTER, encoding="utf-8"))


def load_schedule():
    try:
        d = json.load(open(SCHED, encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for t in (d.get("tables", {}).get("tasks") or {}).values():
        r = t.get("record") or {}
        if r.get("title"):
            out.append(r)
    return out


def staffing_report(roster):
    st = roster["status_counts"]
    g = st.get
    lines = [
        f"团队编制：42 角色 → full {g('full',0)} · partial {g('partial',0)} "
        f"· planned {g('planned',0)} · blocked {g('blocked',0)} "
        f"· gap {g('gap',0)} · none {g('none',0)}",
    ]
    gaps = [a for a in roster["agents"] if a["staffing_status"] in ("gap", "planned")]
    if gaps:
        lines.append("真缺口（应做未做）：")
        for a in gaps:
            lines.append(f"  ❌ {a['agent_id']} {a['name']} — {a['artifact']}")
    lines.append("按 Guild：")
    from collections import Counter
    c = Counter((a["guild"], a["staffing_status"]) for a in roster["agents"])
    for guild in roster["guilds"]:
        parts = " ".join(f"{k}={c[(guild, k)]}" for k in ("full", "partial", "planned", "blocked")
                         if c[(guild, k)])
        lines.append(f"  {guild}: {parts}")
    return lines


def permission_check(roster, tasks):
    """只报"强指令 + 无授权守卫"的组合，避免报警疲劳。"""
    by_id = {a["agent_id"]: a for a in roster["agents"]}
    problems, guarded, checked = [], 0, 0
    for t in tasks:
        title = t.get("title") or ""
        prompt = t.get("prompt") or ""
        checked += 1
        agent_id = next((aid for pat, aid in TASK_AGENT if re.search(pat, title)), None)
        expected = (by_id.get(agent_id) or {}).get("boundary", "") if agent_id else ""
        has_guard = any(re.search(g, prompt) for g in GUARDS)
        hits = []
        for kind, pats in STRONG.items():
            for pat in pats:
                m = re.search(pat, prompt)
                if m:
                    hits.append((kind, m.group(0)))
                    break
        if not hits:
            continue
        if has_guard:
            guarded += 1
            continue
        problems.append({
            "task": title,
            "agent": agent_id or "未映射",
            "actions": [h[0] for h in hits],
            "hits": [h[1] for h in hits],
            "boundary": (expected or "（未映射/无边界）")[:90],
        })
    return checked, problems, guarded


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    roster = load_roster()
    tasks = load_schedule()
    lines = staffing_report(roster)
    checked, problems, guarded = permission_check(roster, tasks)
    lines.append("")
    lines.append(f"权限合规：扫描 {checked} 个已排期档位 → "
                 + ("✅ 无越权" if not problems
                    else f"⚠️ {len(problems)} 处强指令缺授权守卫")
                 + f"（{guarded} 个含守卫已跳过）")
    for p in problems:
        hits = p.get("hits") or []
        actions = p.get("actions") or []
        lines.append(f"  ⚠️ [{p.get('agent')}] {p.get('task')} 提到 "
                     f"「{'/'.join(hits)}」({'/'.join(actions)})；"
                     f"边界=「{p.get('boundary','')}」")
    print("\n".join(lines))
    if a.json:
        json.dump({"staffing": roster["status_counts"], "permission_problems": problems},
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
