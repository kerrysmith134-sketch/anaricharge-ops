#!/usr/bin/env python3
"""sdr_status_readonly.py — SDR **sales** outbound 只读状态查看（不要操作它）。

⚠️ 这条是销售侧的 SDR 外联（Instantly 里的 EV-SDR-* / [AI SDR] 活动）。
   营销外联是另一条线，见 scripts/outbound/marketing_outbound.py（MKT-OUTREACH-*）。

本脚本**只读**：不导入线索、不改活动、不发送。仅用于了解家底与做口径对照。


凭证：API Key 从以下位置读取（不打印、不进 git）：
  1. 环境变量 INSTANTLY_API_KEY
  2. <workspace>/.secrets/instantly.json  {"api_key": "..."}
  3. <workspace>/.secrets/instantly.key  （纯文本）

用法：
  python3 scripts/backlink/instantly.py accounts            # 发信邮箱与容量/健康度
  python3 scripts/backlink/instantly.py campaigns           # 活动列表
  python3 scripts/backlink/instantly.py leads <campaign_id> # 该活动线索与状态
  python3 scripts/backlink/instantly.py replies             # 最近回复（用于跟进）
  python3 scripts/backlink/instantly.py import <campaign_id> <leads.csv>
  python3 scripts/backlink/instantly.py summary             # 汇总：发信/回复/退信

只读命令：accounts / campaigns / leads / replies / summary
写命令：import（会把 CSV 里的目标导入 campaign，需 --confirm）
"""
import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request

WS = "/Users/kerrychu/anari-charge-website"
SECRETS = [os.path.join(WS, ".secrets", "instantly.json"),
           os.path.join(WS, ".secrets", "instantly.key")]
BASE = "https://api.instantly.ai/api/v2"
# Cloudflare 会按浏览器指纹拦截（error 1010）：必须带真实 UA + Origin/Referer
HEADERS_BASE = {
    "Content-Type": "application/json",
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/131.0.0.0 Safari/537.36"),
    "Accept": "application/json",
    "Origin": "https://app.instantly.ai",
    "Referer": "https://app.instantly.ai/",
}


def api_key():
    k = os.environ.get("INSTANTLY_API_KEY")
    if k:
        return k.strip()
    for p in SECRETS:
        if not os.path.exists(p):
            continue
        try:
            if p.endswith(".json"):
                return json.load(open(p))["api_key"].strip()
            return open(p).read().strip()
        except Exception:  # noqa: BLE001
            continue
    raise SystemExit(
        "缺少 Instantly API Key。放到 %s（{\"api_key\":\"...\"}）或设 INSTANTLY_API_KEY。"
        % SECRETS[0])


def call(path, method="GET", payload=None, timeout=45):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers=HEADERS_BASE | {"Authorization": "Bearer " + api_key()})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            return json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read()[:400].decode("utf-8", "replace")
        raise SystemExit("HTTP %s on %s: %s" % (e.code, path, detail))


# ---------------------------------------------------------------- 只读
def accounts():
    d = call("/accounts?limit=100")
    rows = []
    for a in (d.get("items") or []):
        rows.append({
            "email": a.get("email"),
            "provider": a.get("provider"),
            "status": a.get("status"),
            "daily_limit": a.get("daily_limit"),
            "warmup": a.get("warmup_status"),
            "health": a.get("stat_warmup_score") or a.get("health_score"),
        })
    return rows


def campaigns():
    d = call("/campaigns?limit=100")
    return [{"id": c.get("id"), "name": c.get("name"),
             "status": c.get("status"),
             "accounts": len(c.get("email_list") or [])}
            for c in (d.get("items") or [])]


def leads(campaign_id):
    d = call("/leads/list", "POST",
             {"campaign_id": campaign_id, "limit": 100})
    return [{"email": l.get("email"), "company": l.get("company_name"),
             "status": l.get("status"), "step": l.get("last_step_number")}
            for l in (d.get("items") or [])]


def replies():
    """最近回复：优先用 /emails?email_type=received。"""
    try:
        d = call("/emails?email_type=received&limit=50")
    except SystemExit:
        return []
    out = []
    for e in (d.get("items") or []):
        out.append({"from": e.get("from_address_email"),
                    "subject": e.get("subject"),
                    "when": e.get("timestamp_email"),
                    "campaign": e.get("campaign_id"),
                    "body": (e.get("body") or {}).get("text", "")[:300]})
    return out


def summary():
    acc = accounts()
    camps = campaigns()
    rep = replies()
    cap = sum(int(a.get("daily_limit") or 0) for a in acc)
    return {"mailboxes": len(acc), "daily_capacity": cap,
            "campaigns": len(camps),
            "campaigns_active": sum(1 for c in camps if c.get("status") in (1, "active", "Active")),
            "recent_replies": len(rep), "accounts": acc}


def analytics():
    """活动级与账号级真实指标（发信/打开/回复/退信/商机）。"""
    camps = call("/campaigns/analytics")
    rows = []
    for c in (camps if isinstance(camps, list) else camps.get("items") or []):
        sent = int(c.get("emails_sent_count") or 0)
        rep = int(c.get("reply_count_unique") or c.get("reply_count") or 0)
        bou = int(c.get("bounced_count") or 0)
        rows.append({
            "campaign": c.get("campaign_name"),
            "status": c.get("campaign_status"),
            "leads": int(c.get("leads_count") or 0),
            "sent": sent,
            "opens_unique": int(c.get("open_count_unique") or 0),
            "replies_unique": rep,
            "bounces": bou,
            "reply_rate_pct": round(rep / sent * 100, 2) if sent else 0.0,
            "bounce_rate_pct": round(bou / sent * 100, 2) if sent else 0.0,
            "opportunities": c.get("total_opportunities"),
            "opportunity_value": c.get("total_opportunity_value"),
        })
    try:
        ov = call("/campaigns/analytics/overview")
    except SystemExit:
        ov = {}
    return {"overview": ov, "campaigns": rows}


# ---------------------------------------------------------------- 写
LEAD_COLS = ["email", "first_name", "last_name", "company_name", "website",
             "phone", "personalization", "custom_variables"]


def import_leads(campaign_id, path, confirm=False):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = {k: (r.get(k) or "").strip() for k in LEAD_COLS if r.get(k)}
            if row.get("email"):
                rows.append(row)
    if not confirm:
        return {"status": "dry_run", "campaign_id": campaign_id,
                "leads": len(rows), "sample": rows[:3]}
    res = call("/leads", "POST",
               {"campaign_id": campaign_id, "leads": rows,
                "skip_if_in_workspace": True})
    return {"status": "imported", "campaign_id": campaign_id, "count": len(rows),
            "api": res}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["accounts", "campaigns", "leads", "replies",
                                    "summary", "import", "analytics"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args()

    if a.cmd == "accounts":
        out = accounts()
    elif a.cmd == "campaigns":
        out = campaigns()
    elif a.cmd == "leads":
        out = leads(a.args[0])
    elif a.cmd == "replies":
        out = replies()
    elif a.cmd == "summary":
        out = summary()
    elif a.cmd == "analytics":
        out = analytics()
    elif a.cmd == "import":
        out = import_leads(a.args[0], a.args[1], confirm=a.confirm)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
