#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""import_v5.py — 把 v5.0 规格包转成我们可执行的机器可读花名册

## 为什么需要
`03-workflows/specs/v5.0/` 是 42 agent / 160 skill / 25 workflow / 19 connector
的**设计规格**（不是部署软件）。它信息量很大，但直接读 md 没法驱动执行。
本脚本把其中**执行要用的部分**抽成 JSON：

- 42 个角色：id / slug / 名称 / guild / 使命 / 核心产出 / KPI / 触发事件
- 权限边界：来自 `AGENT_SKILL_PERMISSION_MATRIX.csv`（Connector_Allowlist、
  Permission_Boundary、Output_Artifact、Primary_Evaluation、Handoff）
- 每个角色需要的 skills（CSV 里的 Required_Skills）
- workflow / connector / skill 目录的索引
- 97 条工程 backlog

没有 PyYAML（本机装不上），所以用**只取顶层标量**的轻量解析——
这里不需要完整 YAML 语义，只需要读 manifest 的头字段。

用法：
  python3 scripts/team/import_v5.py            # 生成 03-workflows/TEAM-V5-ROSTER.{json,md}
  python3 scripts/team/import_v5.py --check    # 只校验不写
"""
import argparse
import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
SPEC = os.path.join(WS, "03-workflows", "specs", "v5.0")
OUT_JSON = os.path.join(WS, "03-workflows", "TEAM-V5-ROSTER.json")
OUT_MD = os.path.join(WS, "03-workflows", "TEAM-V5-ROSTER.md")
BACKLOG_OUT = os.path.join(WS, "08-execution", "backlog", "v5-backlog.json")

# ---------------------------------------------------------------------------
# 在岗映射（2026-11-08 按真实执行证据核定，不是按名字猜）
#
# status:
#   full    = 有独立档位/脚本，稳定产出（有产物路径）
#   partial = 有产物或脚本，但没有固定档期（靠临时触发）
#   planned = 已确定要做、方案已定，但档位/脚本尚未建
#   blocked = 要做，但依赖外部条件（Apollo 额度 / 真人访谈 / 视频设备 / 政策确认）
#   none    = 明确不做
#
# 2026-11-09 用户纠正两条，直接影响分类：
#   1) R2「不点名竞品」= 不推荐/不对比竞品产品，**不禁止竞品研究** → A05 可做（内部情报，对外不提名字）
#   2) Apollo 有账号（.secrets/enrichment.json 的 masterkey），当前 422 insufficient credits，
#      **等额度恢复** → A08–A11 标 blocked 而非 none
# evidence 指向能证明"谁在做"的具体文件或命令。
# ---------------------------------------------------------------------------
STAFFED = {
    "A00": ("full", "每日进度播报 09:15 + 每日增长脉冲 10:05 + watchdog_daily.py", "08-execution/growth-pulse/"),
    "A02": ("partial", "POSITIONING 文档与产品定位（本轮已按直流+储能重写）", "03-workflows/POSITIONING-*.md"),
    "A03": ("partial", "markets 页的六区域绑定约束分析", "site/markets/index.html"),
    "A07": ("partial", "ICP/角色页（who-we-serve）+ 五份 ICP playbook（v5 规格）", "03-workflows/specs/v5.0/playbooks/"),
    "A12": ("partial", "Instantly 外联的定制正文（leads-ready 3 封三段序列）", "08-execution/marketing-outbound/leads-ready-20261107.json"),
    "A13": ("full", "送达率与抑制档（周一 10:47）", "08-execution/outbound/deliverability/"),
    "A14": ("partial", "询盘守夜 4 次/日 + Brevo deal 状态推进（回复分类仍人工）", "08-execution/inquiry/"),
    "A15": ("partial", "opportunity_rank.py + 内容选题队列", "03-workflows/W5-content-pipeline.md"),
    "A16": ("full", "R2 技术 SEO 档 + validate.js / check-facts.js / audit-inbound-links.js", "06-site/anari-new-site/validate.js"),
    "A17": ("partial", "geo_ai_layer.py 抽检（周三增长脉冲）", "08-execution/geo/"),

    # 2026-11-09 用户要求"都可以做"：以下从默认 gap 改为 planned/blocked
    "A01": ("full", "月度策略复盘档（每月 15 日 10:15）", "08-execution/strategy/"),
    "A04": ("full", "法规监测档（周三 11:20）+ reg_watch.py；自动覆盖 EU AFIR/捷克 ERÚ，其余 4 国标人工", "08-execution/tech/regwatch/"),
    "A20": ("blocked", "专家访谈：需要真人受访（Kerry），自动化只能出问题清单 + 笔记蒸馏", ""),
    "A25": ("partial", "设计总监：contrast-audit + layout-regression + 品牌规范已覆盖多数；缺创意 brief", ""),
    "A26": ("blocked", "视频制作：需要拍摄/剪辑设备与素材，自动化只能出分镜与脚本", ""),
    "A28": ("full", "社媒监听档（周五 15:30），只读不发帖", "08-execution/community/listening/"),
    "A18": ("full", "位次监控档（周六 09:40）+ position_watch.py（窗口可比性守卫）", "08-execution/tech/position-watch/"),
    "A19": ("partial", "内容队列与页面简报（W5）", "03-workflows/W5-content-pipeline.md"),
    "A21": ("full", "R3 内容主编（周二～六 1 篇长尾）", "08-execution/content/"),
    "A22": ("full", "事实库 56 条 + check-facts + evidence-report + 案例证据面板", "ops/fact-library.json"),
    "A23": ("partial", "社媒一稿多用（P6 16:30）+ 内容复用草稿", "08-execution/social/"),
    "A24": ("full", "RU/ES 24+24 页本地化（gen-locale-*）", "scripts/site/v2/gen-ru-specs.py"),
    "A27": ("full", "R5 社区（15:41 Quote/Reddit）+ P6 社媒分发（16:30）", "08-execution/community/"),
    "A29": ("full", "R4 外链与数字公关（Instantly 三波，29 目标）", "08-execution/marketing-outbound/"),
    "A34": ("full", "站点 v2 组件体系 / 页面工厂 / 导航与 IA", "scripts/site/build-v2-pages.js"),
    "A35": ("partial", "询盘两步表单 + 工具带上下文 CTA + E2E 14 项", "scripts/tools/e2e-smoke.py"),
    "A36": ("full", "lead_lifecycle 六条件门 + lead_pipeline tick", "scripts/metrics/lead_lifecycle.py"),
    "A37": ("full", "月度归因结账档（每月 1 日 11:17）+ 每日看板", "08-execution/metrics/monthly/"),
    "A38": ("partial", "Brevo Deals 推送（销售按 deal 跟进）", "scripts/metrics/brevo_crm.py"),
    "A39": ("partial", "8 个案例页 + 项目记录证据面板", "site/cases/"),
    "A40": ("full", "watchdog_daily + run_log_autolog + selftest + Gatekeeper 分级", "scripts/watchdog_daily.py"),
    "A41": ("partial", "周度 flywheel 复盘（自评 + 改进），未做版本化 A/B", "08-execution/flywheel/"),
    # 政策上明确不做
    "A30": ("planned", "付费搜索：**R3 已改为允许 ≤$100/月 验证**（2026-11-09）；需先有专用落地页 + UTM + 止损线，再申请开户", "R3 2026-11-09 改判"),
    "A31": ("blocked", "付费社媒/再营销：$100 上限内不安排（ROI 不明），保持不做", "R3"),
    "A32": ("full", "生命周期培育档（每周四 11:07）——只出草稿不发送", "03-workflows/nurture/"),
    "A33": ("partial", "广告档（周一 11:00）已加预算上限 ≤$100/月 + 止损线；不自行开户/付费，需用户逐次确认", "08-execution/ads/"),
    "A05": ("full", "竞品情报档（周四 14:00），仅内部 intel；R2 仍禁对外点名", "08-execution/intel/"),
    "A06": ("full", "招标信号档（周五 11:00），只做信号不做投标运营（决策 A4）", "08-execution/intel/"),
    "A08": ("blocked", "账号发现：Apollo masterkey 已配置，当前 422 insufficient credits，等额度恢复", ".secrets/enrichment.json masterkey"),
    "A09": ("blocked", "联系人/采购委员会映射：同 A08，等 Apollo 额度", ".secrets/enrichment.json masterkey"),
    "A10": ("blocked", "账号研究与评分：同 A08，等 Apollo 额度", ".secrets/enrichment.json masterkey"),
    "A11": ("blocked", "ABM 编排：依赖 A08–A10 产出，等 Apollo 额度", ".secrets/enrichment.json masterkey"),
}


def read_scalar_block(path, keys):
    """从一个 manifest 里取顶层标量字段（够用即可，不实现完整 YAML）。"""
    out = {}
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return out
    for k in keys:
        m = re.search(rf"^{k}:\s*(.+?)\s*$", text, re.M)
        if m:
            v = m.group(1).strip().strip('"').strip("'")
            if v and not v.startswith("|"):
                out[k] = v
    return out


def read_list_block(path, key):
    """取 `key:` 下的 `- item` 列表（到下一个顶层键为止）。"""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return []
    m = re.search(rf"^{key}:\s*$((?:\n(?:- .*|\s+.*))*)", text, re.M)
    if not m:
        return []
    items = []
    for line in m.group(1).split("\n"):
        s = line.strip()
        if s.startswith("- "):
            items.append(s[2:].strip())
        elif s and not s.startswith("-"):
            break
    return items


def load_permission_matrix():
    """42 行权限矩阵：技能的"谁可以做什么"就取这里。"""
    path = os.path.join(SPEC, "AGENT_SKILL_PERMISSION_MATRIX.csv")
    rows = {}
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            aid = (r.get("Agent_ID") or "").strip()
            if not aid:
                continue
            rows[aid] = {
                "name": r.get("Agent_Name", "").strip(),
                "triggers": r.get("Trigger_Inputs", "").strip(),
                "skills": [s.strip() for s in (r.get("Required_Skills") or "").split(";") if s.strip()],
                "connectors": [s.strip() for s in (r.get("Connector_Allowlist") or "").split(";") if s.strip()],
                "boundary": r.get("Permission_Boundary", "").strip(),
                "artifact": r.get("Output_Artifact", "").strip(),
                "evaluation": r.get("Primary_Evaluation", "").strip(),
                "handoff": [s.strip() for s in (r.get("Handoff") or "").split("/") if s.strip()],
            }
    return rows


def load_catalog(path, key):
    d = json.load(open(path, encoding="utf-8"))
    items = d if isinstance(d, list) else (d.get(key) or d.get("items") or [])
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    agents_dir = os.path.join(SPEC, "agents")
    perm = load_permission_matrix()
    agents = []
    for fn in sorted(os.listdir(agents_dir)):
        if not fn.startswith("A") or not fn.endswith(".yaml"):
            continue
        fp = os.path.join(agents_dir, fn)
        head = read_scalar_block(fp, ["agent_id", "slug", "display_name", "guild",
                                      "version", "lifecycle", "mission"])
        aid = head.get("agent_id")
        if not aid:
            continue
        p = perm.get(aid, {})
        agents.append({
            "agent_id": aid,
            "slug": head.get("slug", ""),
            "name": head.get("display_name") or p.get("name", ""),
            "guild": head.get("guild", ""),
            "mission": head.get("mission", ""),
            "lifecycle": head.get("lifecycle", ""),
            "core_outputs": read_list_block(fp, "core_outputs"),
            "business_kpis": read_list_block(fp, "business_kpis"),
            "trigger_events": read_list_block(fp, "trigger_events"),
            "skills": p.get("skills", []),
            "connectors": p.get("connectors", []),
            "boundary": p.get("boundary", ""),
            "artifact": p.get("artifact", ""),
            "evaluation": p.get("evaluation", ""),
            "handoff": p.get("handoff", []),
            "staffed_by": (STAFFED.get(aid) or ("", "", ""))[1],
            "staffing_status": (STAFFED.get(aid) or ("gap", "", ""))[0],
            "staffing_evidence": (STAFFED.get(aid) or ("", "", ""))[2],
            "manifest": os.path.relpath(fp, WS),
        })

    workflows = load_catalog(os.path.join(SPEC, "workflows", "WORKFLOW_CATALOG.json"), "workflows")
    skills = load_catalog(os.path.join(SPEC, "skills", "SKILL_CATALOG.json"), "skills")
    connectors = load_catalog(os.path.join(SPEC, "connectors", "CONNECTOR_CATALOG.json"), "connectors")

    backlog_path = os.path.join(WS, "08-execution", "backlog", "v5-backlog.json")
    backlog = []
    csv_path = os.path.join(SPEC, "backlog", "BACKLOG_IMPORT.csv")
    if os.path.exists(csv_path):
        with open(csv_path, encoding="utf-8-sig") as f:
            backlog = [dict(r) for r in csv.DictReader(f)]
        backlog = [{(k or "").lstrip("\ufeff"): v for k, v in r.items()} for r in backlog]

    guilds = {}
    for ag in agents:
        guilds.setdefault(ag["guild"], []).append(ag["agent_id"])

    roster = {
        "spec_version": "v5.0",
        "imported_at": "2026-11-08",
        "counts": {"agents": len(agents), "skills": len(skills),
                   "workflows": len(workflows), "connectors": len(connectors),
                   "backlog_items": len(backlog)},
        "staffed_count": sum(1 for x in agents if x["staffed_by"]),
        "status_counts": {s: sum(1 for x in agents if x["staffing_status"] == s)
                          for s in ("full", "partial", "planned", "blocked", "gap", "none")},
        "guilds": {k: sorted(v) for k, v in sorted(guilds.items())},
        "agents": agents,
        "workflows": [{"id": w.get("workflow_id") or w.get("id"),
                       "name": w.get("name") or w.get("title") or ""} for w in workflows],
        "skills": [{"id": s.get("skill_id"), "domain": s.get("domain", ""),
                    "purpose": (s.get("purpose") or "")[:120]} for s in skills],
        "connectors": [{"id": c.get("id"), "name": c.get("name", ""),
                        "role": (c.get("role") or "")[:160]} for c in connectors],
    }

    if a.check:
        print(json.dumps(roster["counts"], ensure_ascii=False))
        print("在岗:", roster["staffed_count"], "/", len(agents))
        missing = [x["agent_id"] for x in agents if not x["staffed_by"]]
        print("未设岗:", " ".join(missing))
        return 0

    os.makedirs(os.path.dirname(BACKLOG_OUT), exist_ok=True)
    json.dump(roster, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(backlog, open(BACKLOG_OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 人类可读版
    lines = [
        "# ANARI 虚拟营销团队 · v5.0 花名册（机器生成的摘要）",
        "",
        f"> 来源：`03-workflows/specs/v5.0/`（42 agent / 160 skill / 25 workflow / 19 connector / 97 backlog）。",
        "> 本文件由 `scripts/team/import_v5.py` 生成，勿手改；改编制请改脚本里的 `STAFFED` 映射。",
        "",
        f"**在岗 {roster['staffed_count']} / {len(agents)}**"
        f"（full {roster['status_counts']['full']} · partial {roster['status_counts']['partial']}"
        f" · planned {roster['status_counts']['planned']} · blocked {roster['status_counts']['blocked']}"
        f" · gap {roster['status_counts']['gap']}）",
        "",
        "## 按 Guild 分组",
        "",
    ]
    for guild, ids in roster["guilds"].items():
        lines.append(f"### {guild}（{len(ids)}）")
        lines.append("")
        lines.append("| ID | 角色 | 状态 | 谁在做 | 权限边界 |")
        lines.append("|---|---|---|---|---|")
        icon = {"full": "✅", "partial": "◐", "planned": "○", "blocked": "⏸", "gap": "❌", "none": "—"}
        for aid in ids:
            ag = next(x for x in agents if x["agent_id"] == aid)
            lines.append(f"| {aid} | {ag['name']} | {icon[ag['staffing_status']]} {ag['staffing_status']} | "
                         f"{ag['staffed_by'] or '—'} | {(ag['boundary'] or '')[:60]} |")
        lines.append("")
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    print(f"花名册 → {os.path.relpath(OUT_JSON, WS)}")
    print(f"摘要   → {os.path.relpath(OUT_MD, WS)}")
    print(f"backlog→ {os.path.relpath(BACKLOG_OUT, WS)}（{len(backlog)} 条）")
    print(f"角色 {len(agents)} · 在岗 {roster['staffed_count']} · skill {len(skills)} · "
          f"workflow {len(workflows)} · connector {len(connectors)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
