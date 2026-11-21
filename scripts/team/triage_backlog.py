#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""triage_backlog.py — 把 v5 的 97 条工程 backlog 分诊到我们的现实

## 为什么要分诊而不是照做
v5 的 backlog 是**平台工程**（SSO/RBAC/数仓分层/Temporal 编排/HubSpot 与 Apollo 连接器）。
我们的现实是：一个运营工作区 + 若干 python/node 脚本 + 真实站点，没有平台团队。
照单全做等于永远在做平台、不做增长。所以逐条标注：

  met     已用轻量方式满足（有证据路径）
  partial 部分满足，缺口写清楚
  light   可做轻量替代（下一步候选）
  na      不适用（政策/架构选择：HubSpot→Brevo、Apollo 无账号、付费广告不投）
  backlog 真要做，但需要平台投入（本轮不做）

产出：08-execution/backlog/v5-triage.json + 同目录 md。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(WS, "08-execution", "backlog", "v5-backlog.json")
OUT = os.path.join(WS, "08-execution", "backlog", "v5-triage.json")
OUT_MD = os.path.join(WS, "08-execution", "backlog", "v5-triage.md")

# 逐条判定。键=Work_Item_ID；未列出的按 epic 默认处理。
OVERRIDES = {
    # E00 治理
    "ANARI-0001": ("met", "北星看板 `north_star.py` + STATUS.md 已固定 SAQO/pipeline/收录/引用域口径；"
                          "但缺『公式级』语义注册（版本/owner/可执行测试）→ 下一步做成 ops/kpi-registry.json"),
    "ANARI-0002": ("met", "v5 花名册 `03-workflows/TEAM-V5-ROSTER.json` + ICP 角色页 + markets 六区域"),
    "ANARI-0003": ("na", "无预算分配权限（$500 已由 R3 固定为全有机），无需投资组合治理"),
    "ANARI-0004": ("met", "Gatekeeper Tier A/B/C + R8 事实门禁 + PR 白名单"),
    "ANARI-0005": ("met", "`~/.dsh/storages/schedule.json` + watchdog + 每日播报/脉冲 + run-log"),
    # E01 身份与权限
    "ANARI-0006": ("na", "单操作员（用户本人）+ 单会话，无员工 SSO 需求"),
    "ANARI-0007": ("partial", "agent 身份=档位标题（watchdog 按档位查产物）；无独立服务身份"),
    "ANARI-0008": ("partial", "权限靠 R6 + Gatekeeper 分级 + Agent 权限边界（coverage.py 检查）；无 RBAC 服务"),
    "ANARI-0009": ("met", "R6（不可逆动作逐次确认）+ Gatekeeper Tier C 人工审批 + 外联只出草稿"),
    "ANARI-0010": ("met", "`08-execution/run-log.jsonl`（含 qa/outputs/note）+ git 提交历史"),
    # E02 领域模型
    "ANARI-0011": ("partial", "D1 submissions 真实列 + 账本状态机 + GA4 事件名；无统一 schema 注册中心"),
    "ANARI-0012": ("na", "无第三方 CRM/账号库实体解析需求（Brevo 为唯一 CRM）"),
    "ANARI-0013": ("na", "未做 ABM/账号层级（见花名册 A08–A11 政策不设岗）"),
    "ANARI-0014": ("met", "`ops/fact-library.json` 56 条（source/last_verified/review_by/scope）+ 案例证据面板"),
    "ANARI-0015": ("partial", "`evidence-report.py` 体检 + check-facts 门禁；无数据质量工作台"),
    # E03 事件与度量
    "ANARI-0016": ("partial", "GA4 生命周期事件名（lead_mql/sal/opportunity_created/won/lost）+ D1 表结构"),
    "ANARI-0017": ("partial", "D1 持久化 + GA4 队列入队/重放（ga4_events.py）；无通用事件总线"),
    "ANARI-0018": ("na", "无数仓；用 JSON/JSONL 快照（north-star、gsc、index-coverage）"),
    "ANARI-0019": ("met", "GA4 MP 服务端事件（实测收到）+ GSC API + D1 服务端落库"),
    "ANARI-0020": ("partial", 'watchdog 检测「档位到点无产出」；无新鲜度/漂移/事件丢失看板'),
    # E04 Agent 运行时
    "ANARI-0021": ("partial", "档位=执行单元（schedule.json），花名册=契约；无运行时 SDK"),
    "ANARI-0022": ("met", "档位编排（每周/每日/每月）+ 依赖靠文档与 watchdog 顺序"),
    "ANARI-0023": ("partial", "run-log.jsonl 记输入/输出/风险；无 trace/context store"),
    "ANARI-0024": ("na", "单模型环境，无路由需求"),
    "ANARI-0025": ("na", "无沙箱控制台；浏览器纪律 R10 + 单标签巡检替代"),
    # E05 技能与证据
    "ANARI-0026": ("met", "`02-skills/` manifest + v5 160 skill 目录已导入花名册"),
    "ANARI-0027": ("partial", "技能=脚本/文档组合，人工编排；无执行引擎"),
    "ANARI-0028": ("met", "证据索引=fact-library + GSC/GA4/索引审计快照"),
    "ANARI-0029": ("met", "事实库 review_by/status + evidence-report 过期检测"),
    "ANARI-0030": ("na", "无多租户检索需求"),
    # E06 连接器
    "ANARI-0031": ("partial", "脚本即连接器（gsc/ga4/brevo/instantly/d1/cloudflare）；无 SDK"),
    "ANARI-0032": ("na", "R4 决策：Brevo 为 CRM，不引入 HubSpot"),
    "ANARI-0033": ("na", "无 Apollo 账号；媒体 PR 外联走 Instantly + 公开投稿入口"),
    "ANARI-0034": ("met", "GSC API + GA4 Data API + IndexNow（广告未投，按 R3）"),
    "ANARI-0035": ("partial", "Brevo 邮件/CRM API 已用；社媒无 API（人工/浏览器草稿）"),
    # E18 安全与合规
    "ANARI-0093": ("light", "可做轻量：法域×触达方式矩阵（EU/海湾/东南亚的 cold outreach 规则）"),
    "ANARI-0094": ("light", "可做轻量：统一抑制台账 + 发送前检查（当前散在 Instantly 与台账）"),
    "ANARI-0095": ("partial", "D1 有 consent/consent_ts；无 DSR/保留期流程"),
    "ANARI-0096": ("met", "凭证 600 权限存 `.secrets/`，不入库不打印；R6 授权门"),
    "ANARI-0097": ("partial", "账本/git 即恢复手段；无正式 DR 演练"),
}

EPIC_DEFAULT = {
    "E00": ("partial", "治理类：靠文档 + git + run-log 部分满足"),
}


def get(row, key):
    for k in row:
        if k.lstrip("\ufeff").endswith(key):
            return row[k]
    return ""


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    out = []
    for r in rows:
        wid = get(r, "Work_Item_ID")
        status, evidence = OVERRIDES.get(wid, ("backlog", "需平台投入，本轮不做"))
        out.append({
            "id": wid,
            "epic": get(r, "Epic_ID"),
            "epic_name": get(r, "Epic_Name"),
            "type": get(r, "Type"),
            "title": get(r, "Title"),
            "priority": get(r, "Priority"),
            "status": status,
            "evidence": evidence,
        })
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    from collections import Counter
    cnt = Counter(x["status"] for x in out)
    lines = ["# v5 backlog 分诊（97 条）", "",
             "> 由 `scripts/team/triage_backlog.py` 生成。",
             "> met=已用轻量方式满足 · partial=部分 · light=可做轻量替代 · na=不适用 · backlog=需平台投入", "",
             "## 汇总", ""]
    for k in ("met", "partial", "light", "na", "backlog"):
        lines.append(f"- **{k}** {cnt.get(k, 0)}")
    lines += ["", "## 按 Epic", "", "| Epic | 名称 | met | partial | light | na | backlog |",
              "|---|---|---|---|---|---|---|"]
    epics = {}
    for x in out:
        epics.setdefault((x["epic"], x["epic_name"]), []).append(x)
    for (eid, ename), items in sorted(epics.items()):
        c = Counter(i["status"] for i in items)
        lines.append(f"| {eid} | {ename[:44]} | {c['met']} | {c['partial']} | "
                     f"{c['light']} | {c['na']} | {c['backlog']} |")
    lines += ["", "## 可做轻量替代（下一步候选）", ""]
    for x in out:
        if x["status"] == "light":
            lines.append(f"- **{x['id']}** {x['title']} — {x['evidence']}")
    lines += ["", "## 已满足（有证据）", ""]
    for x in out:
        if x["status"] == "met":
            lines.append(f"- {x['id']} {x['title'][:66]} — {x['evidence'][:80]}")
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"分诊 → {os.path.relpath(OUT, WS)}")
    print("汇总:", dict(cnt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
