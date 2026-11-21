#!/usr/bin/env python3
"""instantly_client.py — Instantly API v2 共用客户端（被 sdr/marketing 两条线共用）。

两条线必须分开：
  - SDR sales outbound  -> 既有 EV-SDR-* / [AI SDR] 活动，销售侧，**营销线不读写、不改动**
  - Marketing outbound  -> MKT-OUTREACH-PR-* 活动，本脚本服务对象

凭证：INSTANTLY_API_KEY 环境变量 或 <workspace>/.secrets/instantly.json
注意：Cloudflare 对非浏览器指纹返回 1010，必须带真实 UA + Origin/Referer。
"""
import json
import os
import urllib.error
import urllib.request

WS = "/Users/kerrychu/anari-charge-website"
BASE = "https://api.instantly.ai/api/v2"
HEADERS_BASE = {
    "Content-Type": "application/json",
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/131.0.0.0 Safari/537.36"),
    "Accept": "application/json",
    "Origin": "https://app.instantly.ai",
    "Referer": "https://app.instantly.ai/",
}
SECRETS = os.path.join(WS, ".secrets", "instantly.json")


def api_key():
    k = os.environ.get("INSTANTLY_API_KEY")
    if k:
        return k.strip()
    if os.path.exists(SECRETS):
        return json.load(open(SECRETS))["api_key"].strip()
    raise SystemExit("缺少 Instantly API Key（%s）" % SECRETS)


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
        raise SystemExit("HTTP %s on %s: %s" % (
            e.code, path, e.read()[:400].decode("utf-8", "replace")))


def list_campaigns():
    d = call("/campaigns?limit=100")
    return d.get("items") or []


def campaign_by_id(cid):
    return call("/campaigns/" + cid)


def analytics():
    a = call("/campaigns/analytics")
    return a if isinstance(a, list) else (a.get("items") or [])


def received_emails(limit=100):
    d = call("/emails?email_type=received&limit=%d" % limit)
    return d.get("items") or []


def add_leads(campaign_id, leads, skip_existing=True):
    """加 lead 到活动。

    ⚠️ 2026-11-08 实测的**正确形状**（此前写错了，导致外联活动一直 0 leads）：
    Instantly API v2 的 `POST /leads` 是**一次一条**，字段在顶层，
    活动用 `campaign` 而不是 `campaign_id` + `leads[]` 批量数组。
    错的形状返回 400 "Email is required when creating a lead"——看起来像缺邮箱，
    其实是整包被当成一条空 lead 解析。

    `skip_existing`：遇到已存在（400/409 或 duplicate 字样）就跳过，不算失败。
    """
    ok, skipped, failed = 0, 0, []
    for ld in leads:
        payload = {
            "campaign": campaign_id,
            "email": (ld.get("email") or "").strip(),
            "first_name": ld.get("first_name") or "",
            "company_name": ld.get("company_name") or "",
            "website": ld.get("website") or "",
            "personalization": ld.get("personalization") or "",
        }
        if not payload["email"]:
            skipped += 1
            continue
        try:
            call("/leads", "POST", payload)
            ok += 1
        except SystemExit as e:
            msg = str(e)
            if "duplicate" in msg.lower() or "already" in msg.lower() or "409" in msg:
                skipped += 1
            else:
                failed.append({"email": payload["email"], "error": msg[:160]})
    return {"created": ok, "skipped": skipped, "failed": failed}
