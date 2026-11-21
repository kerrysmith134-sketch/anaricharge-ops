#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""policy_check.py — 本地动作策略检查（对齐 v6.1.0 的 OPA 语义）

## 为什么需要
v6 用 OPA/Rego 做"这个动作能不能执行"的判定，规则见
`03-workflows/specs/v6/v6.1.0/infra/opa/marketing-actions.rego`。我们没有 OPA 服务，
但**语义可以照搬**——而且我们的自动化现在确实在对外动作（发信、发帖、推站），
缺的正是这一层"动作级"判定（现在是靠 Gatekeeper 分级 + 人肉确认）。

## 抄过来的语义（fail closed）
1. 身份缺失 → 拒绝：必须有 actor_id、actor_type、capability
2. **硬禁止**：`secret.*` / `policy.*` / `permission.expand` / `self_approve.*` /
   `delete.customer_data.permanent` —— 任何情况都不允
3. **同意门**：动作键含 email/marketing/sequence/nurture/newsletter 时，
   `consent_eligible` 必须为真
4. **抑制门**：`suppressed=true` 直接拒绝
5. **风险上限**：agent 只能做 R0–R2；service/human 可做 R0–R4；R5 任何角色都不行
6. **需审批标记**：R3/R4 返回 `requires_approval=true`（不是拒绝，是要人批）

## 用法
  python3 scripts/team/policy_check.py list
  python3 scripts/team/policy_check.py show instantly.outreach.send
  python3 scripts/team/policy_check.py check --action instantly.outreach.send \
      --actor-type agent --actor-id growth-pulse --capability connector.instantly.send \
      --consent --not-suppressed
  # 退出码：0 允许（或需审批时也返回 0，但 approval_required=true）；1 拒绝
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
CAT = os.path.join(WS, "ops", "action-catalog.json")

HARD_DENY_PREFIX = ("secret.", "policy.", "permission.expand", "self_approve.")
HARD_DENY_EXACT = {"delete.customer_data.permanent"}
CONSENT_PATTERN = ("email", "marketing", "sequence", "nurture", "newsletter", "outreach")
AGENT_MAX = {"R0", "R1", "R2"}
HUMAN_MAX = {"R0", "R1", "R2", "R3", "R4"}


def load():
    d = json.load(open(CAT, encoding="utf-8"))
    actions = {a["action_key"]: a for a in d["actions"]}
    actions.update({a["action_key"]: a for a in d.get("local_extensions") or []})
    return d, actions


def evaluate(action_key, actor_type, actor_id, capability, consent, suppressed,
             approval_granted=False):
    """返回 (allowed, approval_required, reasons[])。语义与 rego 一一对应。"""
    d, actions = load()
    reasons = []
    if not actor_id:
        return False, False, ["缺 actor_id"]
    if actor_type not in ("agent", "service", "human"):
        return False, False, [f"未知 actor_type: {actor_type}"]
    if not capability:
        return False, False, ["缺 required_capability"]

    a = actions.get(action_key)
    if not a:
        return False, False, [f"动作未在目录中注册（fail closed）: {action_key}"]

    # 硬禁止
    if action_key.startswith(HARD_DENY_PREFIX) or action_key in HARD_DENY_EXACT:
        return False, False, [f"硬禁止动作: {action_key}"]

    # 能力必须与目录一致（防止自选能力/风险）
    if a["capability"] != capability:
        return False, False, [f"能力不匹配：目录要求 {a['capability']}，传入 {capability}"]

    # 同意门
    if a.get("requires_marketing_consent") and not consent:
        return False, False, ["该动作需要营销同意（consent_eligible=false）"]
    key_hits = [k for k in CONSENT_PATTERN if k in action_key]
    if key_hits and not consent:
        return False, False, [f"动作键含营销语义（{key_hits}）且无同意"]

    # 抑制门
    if suppressed:
        return False, False, ["命中抑制清单（suppressed=true）"]

    # 风险上限
    tier = a["risk_tier"]
    ceiling = AGENT_MAX if actor_type == "agent" else HUMAN_MAX
    if tier == "R5":
        return False, False, ["R5 禁止任何自动执行"]
    if tier not in ceiling:
        return False, float(tier[1]) >= 3, [f"{actor_type} 风险上限 {sorted(ceiling)}，该动作 {tier}"]

    # 需审批
    approval_required = tier in ("R3", "R4")
    if approval_required and not approval_granted:
        return True, True, [f"{tier} 需人工审批（approval_granted=false）"]
    return True, approval_required, reasons or ["允许"]


def cmd_list(a):
    d, actions = load()
    print(f"风险分级: {json.dumps(d['risk_tiers'], ensure_ascii=False, indent=1)}\n")
    print(f"{'action_key':34s} {'tier':4s} {'consent':8s} {'启用':4s} provider")
    for k, v in sorted(actions.items()):
        print(f"{k:34s} {v['risk_tier']:4s} {'yes' if v['requires_marketing_consent'] else '-':8s} "
              f"{'✅' if v['enabled'] else '✗':4s} {v['provider']}")
    return 0


def cmd_show(a):
    _, actions = load()
    v = actions.get(a.action)
    if not v:
        print("未注册:", a.action); return 1
    print(json.dumps(v, ensure_ascii=False, indent=1))
    return 0


def cmd_check(a):
    allowed, needs_approval, reasons = evaluate(
        a.action, a.actor_type, a.actor_id, a.capability,
        a.consent, not a.not_suppressed, a.approval_granted)
    verdict = "ALLOW" if allowed and not needs_approval else (
        "ALLOW_WITH_APPROVAL" if allowed else "DENY")
    print(json.dumps({"action": a.action, "verdict": verdict,
                      "approval_required": needs_approval,
                      "reasons": reasons}, ensure_ascii=False, indent=1))
    return 0 if allowed else 1


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("show"); p.add_argument("action")
    p = sub.add_parser("check")
    p.add_argument("--action", required=True)
    p.add_argument("--actor-type", default="agent", choices=["agent", "service", "human"])
    p.add_argument("--actor-id", default="")
    p.add_argument("--capability", default="")
    p.add_argument("--consent", action="store_true", help="consent_eligible=true")
    p.add_argument("--not-suppressed", action="store_true", help="未被抑制")
    p.add_argument("--approval-granted", action="store_true")
    a = ap.parse_args()
    return {"list": cmd_list, "show": cmd_show, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
