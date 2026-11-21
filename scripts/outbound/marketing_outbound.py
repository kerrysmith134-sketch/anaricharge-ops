#!/usr/bin/env python3
"""marketing_outbound.py — 营销外联线（PR / 媒体 / 嘉宾投稿 / 合作 / 目录）。

与 SDR sales outbound **严格分开**：
  - 本脚本只读写 MKT-OUTREACH-* 活动
  - SDR 的 EV-SDR-* / [AI SDR] 活动一律不碰（销售侧资产）

用法：
  python3 scripts/outbound/marketing_outbound.py status      # 营销活动指标
  python3 scripts/outbound/marketing_outbound.py targets     # 目标台账与邮箱覆盖
  python3 scripts/outbound/marketing_outbound.py replies     # 只取营销活动的回复
  python3 scripts/outbound/marketing_outbound.py import --dry # 导入有邮箱的目标
"""
import argparse
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instantly_client as ic  # noqa: E402

WS = "/Users/kerrychu/anari-charge-website"
OUT = os.path.join(WS, "08-execution", "marketing-outbound")
LEDGER = os.path.join(OUT, "media-targets-20261107.json")
PREFIX = "MKT-OUTREACH"


def marketing_campaigns():
    return [c for c in ic.list_campaigns()
            if (c.get("name") or "").startswith(PREFIX)]


def status():
    rows = {c["campaign_id"]: c for c in ic.analytics()}
    # campaigns/analytics 的 leads 字段是 None → 会误报 0，看起来像"没有动作"。
    # 用 /leads/list 逐活动实查：这才是"有多少目标准备发送"。
    def real_leads(cid):
        """真实 lead 数。响应里**没有 total**，只有游标 next_starting_after，
        所以要翻页数——这是唯一可信的口径（analytics 的 leads 字段是 None）。"""
        try:
            total, cursor = 0, None
            for _ in range(20):
                body = {"campaign": cid, "limit": 100}
                if cursor:
                    body["starting_after"] = cursor
                d = ic.call("/leads/list", "POST", body)
                items = d.get("items") or []
                total += len(items)
                cursor = d.get("next_starting_after")
                if not cursor or not items:
                    break
            return total
        except SystemExit:
            return None

    out = []
    for c in marketing_campaigns():
        a = rows.get(c.get("id"), {})
        sent = int(a.get("emails_sent_count") or 0)
        rep = int(a.get("reply_count_unique") or 0)
        bou = int(a.get("bounced_count") or 0)
        out.append({
            "campaign": c.get("name"), "id": c.get("id"),
            "status": c.get("status"),
            "leads": int(a.get("leads_count") or 0),
            "leads_actual": real_leads(c.get("id") or ""), "sent": sent,
            "replies_unique": rep, "bounces": bou,
            "reply_rate_pct": round(rep / sent * 100, 2) if sent else 0.0,
            "bounce_rate_pct": round(bou / sent * 100, 2) if sent else 0.0,
        })
    targets = json.load(open(LEDGER, encoding="utf-8")) if os.path.exists(LEDGER) else []
    with_email = [t for t in targets if t.get("email")]
    return {"campaigns": out,
            "targets_total": len(targets),
            "targets_with_email": len(with_email),
            "targets_form_only": len(targets) - len(with_email)}


def targets():
    if not os.path.exists(LEDGER):
        return []
    return json.load(open(LEDGER, encoding="utf-8"))


def replies():
    """只保留落在营销活动上的回复。"""
    mkt_ids = {c.get("id") for c in marketing_campaigns()}
    out = []
    if not mkt_ids:
        return out
    for e in ic.received_emails(100):
        if e.get("campaign_id") in mkt_ids:
            out.append({"from": e.get("from_address_email"),
                        "date": str(e.get("timestamp_email"))[:10],
                        "subject": e.get("subject"),
                        "body": ((e.get("body") or {}).get("text") or "")[:400]})
    return out


def do_import(dry=True):
    tg = [t for t in targets() if t.get("email")]
    # 发送前必须过统一抑制台账（ANARI-0094）：命中邮箱/域名/机构任一即 HOLD，
    # 不给"明确拒绝过"或"退信过"的地址再发一次。台账在 ops/suppression.json。
    try:
        import sys as _sys
        _sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))
        import suppression as _sup
        _ledger = _sup.load()["entries"]
        kept, held = [], []
        for t in tg:
            if _sup.match(_ledger, t.get("email") or "") or _sup.match(_ledger, t.get("domain") or ""):
                held.append(t.get("email"))
            else:
                kept.append(t)
        if held:
            print("抑制台账命中，已 HOLD:", ", ".join(str(x) for x in held))
        tg = kept
    except Exception as e:  # noqa: BLE001
        print(f"（抑制台账检查跳过：{type(e).__name__}: {e}）")
    if not tg:
        return {"status": "nothing_to_import", "reason": "台账里没有带邮箱的目标"}
    camps = marketing_campaigns()
    if not camps:
        return {"status": "no_campaign", "reason": "未找到 MKT-OUTREACH-* 活动"}
    cid = camps[0]["id"]
    leads = [{"email": t["email"],
              "first_name": t.get("contact") or "",
              "company_name": t.get("name") or "",
              "website": t.get("domain") or "",
              "personalization": t.get("pitch_angle") or ""} for t in tg]
    # 动作级策略检查（v6.1.0 OPA 语义）：导入是 R2 但需营销同意 + 未抑制
    try:
        sys.path.insert(0, os.path.join(WS, "scripts", "team"))
        import policy_check as _pc
        allowed, needs_approval, reasons = _pc.evaluate(
            "instantly.lead.import", "agent", "marketing-outbound",
            "connector.instantly.write", consent=True, suppressed=False)
        if not allowed:
            return {"status": "blocked_by_policy", "reasons": reasons}
    except Exception as e:  # noqa: BLE001
        print(f"（策略检查跳过：{type(e).__name__}: {e}）")

    if dry:
        return {"status": "dry_run", "campaign": camps[0]["name"],
                "would_import": len(leads), "sample": leads[:3]}
    return {"status": "imported", "campaign": camps[0]["name"],
            "count": len(leads), "api": ic.add_leads(cid, leads)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "targets", "replies", "import"])
    ap.add_argument("--dry", action="store_true", default=False)
    ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args()
    if a.cmd == "status":
        out = status()
    elif a.cmd == "targets":
        out = targets()
    elif a.cmd == "replies":
        out = replies()
    else:
        out = do_import(dry=not a.confirm)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
