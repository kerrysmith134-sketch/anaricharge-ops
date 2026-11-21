#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ga4_query.py — 直查 GA4 Data API（实时 + 按日事件）

为什么需要：此前 GA4 只能靠 UI 看，north_star 里只有 GSC 与前端事件推断。
OAuth 凭证里含 `analytics.readonly`（2026-11-08 确认），所以可以直接读。

用法：
  python3 scripts/metrics/ga4_query.py realtime          # 近 30 分钟事件
  python3 scripts/metrics/ga4_query.py events --days 7   # 按事件名汇总
  python3 scripts/metrics/ga4_query.py event lead_mql --days 30
  python3 scripts/metrics/ga4_query.py conversion --days 7   # 转化事件 raw/诊断/净

## 诊断流量口径（2026-11-09 加，重要）

**Tag Assistant / GTM 预览会话不是业务转化。** 它们进 GA4 时 `sessionSource`
形如 `tagassistant.google.com`，会把 `form_start / submit_attempt /
submit_failure / generate_lead / form_submit` 计入报表，导致
「D1 询盘 0 但 GA4 有转化」的假警报（2026-11-09 实际踩到：当天 4 个转化类
事件全部来自 Tag Assistant 预览，而 D1/Worker 一条请求都没收到）。

所以：
- `events` / `event` 加 `--exclude-diagnostic` 即剔除会话来源含
  `tagassistant` 的会话，得到**业务口径**；
- `conversion` 一条命令同时给出 raw / 诊断量 / 净值，巡检时用它而不是裸 count；
- **GA4 采集侧已加过滤器（2026-11-09 12:20 激活）**：属性 553998974 有一条
  `Exclude Tag Assistant preview traffic`（类型 Developer traffic，状态 Active），
  它会排除 `debug_mode` / `debug_event` 有值的事件。但它**不追溯**，且拦不住
  "没带 debug_mode 的假会话"，所以历史窗口内仍按会话来源剔除，不要删这段逻辑。
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CRED = "/Users/kerrychu/Documents/kimi/workspace/.secrets/gsc-oauth.json"   # 只读引用
PROPERTY = "553998974"
TOKEN_CACHE = os.path.join(WS, ".secrets", "ga4-access.json")

#: 转化类事件（巡检口径统一用这些名字，避免各处自造）
CONV_EVENTS = ["form_start", "form_submit", "submit_attempt",
               "submit_failure", "generate_lead", "lead_mql"]
#: 诊断流量的会话来源特征（Tag Assistant / GTM 预览）
DIAGNOSTIC_SOURCE = "tagassistant"


def diag_exclusion():
    """GA4 FilterExpression：排除会话来源含 tagassistant 的会话。"""
    return {"notExpression": {"filter": {
        "fieldName": "sessionSource",
        "stringFilter": {"value": DIAGNOSTIC_SOURCE,
                         "matchType": "CONTAINS", "caseSensitive": False}}}}


def is_diagnostic_source(src):
    return DIAGNOSTIC_SOURCE in (src or "").lower()



def access_token():
    """用 refresh_token 换 access_token（只读，不打印凭证）。"""
    try:
        d = json.load(open(CRED, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"读不到 OAuth 凭证：{e}")
    # 缓存（50 分钟内复用）
    try:
        c = json.load(open(TOKEN_CACHE, encoding="utf-8"))
        if c.get("expires_at", 0) > dt.datetime.now().timestamp() + 60:
            return c["access_token"]
    except Exception:  # noqa: BLE001
        pass
    body = urllib.parse.urlencode({
        "client_id": d["client_id"], "client_secret": d["client_secret"],
        "refresh_token": d["refresh_token"], "grant_type": "refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body)
    with urllib.request.urlopen(req, timeout=20) as r:
        tok = json.load(r)
    out = {"access_token": tok["access_token"],
           "expires_at": dt.datetime.now().timestamp() + int(tok.get("expires_in", 3600)) - 120}
    try:
        json.dump(out, open(TOKEN_CACHE, "w", encoding="utf-8"))
        os.chmod(TOKEN_CACHE, 0o600)
    except Exception:  # noqa: BLE001
        pass
    return out["access_token"]


def post(path, body):
    req = urllib.request.Request(
        f"https://analyticsdata.googleapis.com/v1beta/properties/{PROPERTY}:{path}",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + access_token(),
                 "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read(400).decode("utf-8", "ignore")}


def cmd_realtime(a):
    d = post("runRealtimeReport", {
        "dimensions": [{"name": "eventName"}],
        "metrics": [{"name": "eventCount"}],
        "limit": 30})
    if "error" in d:
        print("❌", d["error"], d["body"][:200]); return 1
    rows = d.get("rows") or []
    if not rows:
        print("近 30 分钟没有事件。")
        return 0
    print(f"{'event':<28} {'count':>7}")
    for r in rows:
        print(f"{r['dimensionValues'][0]['value']:<28} {r['metricValues'][0]['value']:>7}")
    return 0


def cmd_events(a):
    end = dt.date.today()
    start = end - dt.timedelta(days=a.days)
    body = {
        "dateRanges": [{"startDate": start.isoformat(), "endDate": end.isoformat()}],
        "dimensions": [{"name": "eventName"}],
        "metrics": [{"name": "eventCount"}, {"name": "totalUsers"}],
        "limit": 60}
    if a.exclude_diagnostic:
        body["dimensionFilter"] = diag_exclusion()
    d = post("runReport", body)
    if "error" in d:
        print("❌", d["error"], d["body"][:300]); return 1
    rows = d.get("rows") or []
    if not rows:
        print(f"近 {a.days} 天没有事件数据。")
        return 0
    scope = "（已剔除 tagassistant 诊断流量）" if a.exclude_diagnostic else ""
    print(f"{'event':<28} {'count':>8} {'users':>7}{scope}")
    for r in sorted(rows, key=lambda r: -int(r["metricValues"][0]["value"])):
        print(f"{r['dimensionValues'][0]['value']:<28} "
              f"{r['metricValues'][0]['value']:>8} {r['metricValues'][1]['value']:>7}")
    return 0


def cmd_event(a):
    end = dt.date.today()
    start = end - dt.timedelta(days=a.days)
    name_filter = {"filter": {"fieldName": "eventName",
                              "stringFilter": {"value": a.name}}}
    flt = ({"andGroup": {"expressions": [name_filter, diag_exclusion()]}}
           if a.exclude_diagnostic else name_filter)
    d = post("runReport", {
        "dateRanges": [{"startDate": start.isoformat(), "endDate": end.isoformat()}],
        "dimensions": [{"name": "date"}],
        "metrics": [{"name": "eventCount"}],
        "dimensionFilter": flt,
        "limit": 60})
    if "error" in d:
        print("❌", d["error"], d["body"][:300]); return 1
    rows = d.get("rows") or []
    if not rows:
        print(f"近 {a.days} 天没有 `{a.name}` 事件"
              f"{'（已剔除诊断流量）' if a.exclude_diagnostic else ''}。")
        return 0
    total = 0
    for r in rows:
        n = int(r["metricValues"][0]["value"])
        total += n
        print(f"  {r['dimensionValues'][0]['value']}  {n}")
    print(f"合计 {total}")
    return 0


def cmd_conversion(a):
    """转化事件 raw / 诊断 / 净 —— 巡检时用这条，不要用裸 count。

    一次报告按 (eventName, sessionSource) 拆分，本地聚合：
      raw  = 全部
      diag = 会话来源含 tagassistant（GTM 预览 / Tag Assistant）
      clean= raw - diag  ← 业务口径
    """
    end = dt.date.today()
    start = end - dt.timedelta(days=a.days)
    d = post("runReport", {
        "dateRanges": [{"startDate": start.isoformat(), "endDate": end.isoformat()}],
        "dimensions": [{"name": "eventName"}, {"name": "sessionSource"}],
        "metrics": [{"name": "eventCount"}],
        "dimensionFilter": {"filter": {"fieldName": "eventName",
                                       "inListFilter": {"values": CONV_EVENTS}}},
        "limit": 500})
    if "error" in d:
        print("❌", d["error"], d["body"][:300]); return 1
    agg = {}
    for r in d.get("rows") or []:
        ev = r["dimensionValues"][0]["value"]
        src = r["dimensionValues"][1]["value"]
        n = int(r["metricValues"][0]["value"])
        cur = agg.setdefault(ev, {"raw": 0, "diag": 0, "sources": []})
        cur["raw"] += n
        if is_diagnostic_source(src):
            cur["diag"] += n
            if src not in cur["sources"]:
                cur["sources"].append(src)
    print(f"== 转化事件 {a.days} 天：raw / 诊断 / 净（业务口径） ==")
    if not agg:
        print("  没有任何转化类事件。")
        return 0
    print(f"{'event':<20} {'raw':>6} {'诊断':>6} {'净':>6}  诊断来源")
    for ev in CONV_EVENTS:
        if ev not in agg:
            continue
        c = agg[ev]
        clean = c["raw"] - c["diag"]
        print(f"{ev:<20} {c['raw']:>6} {c['diag']:>6} {clean:>6}  "
              f"{','.join(c['sources']) or '-'}")
    other = [e for e in agg if e not in CONV_EVENTS]
    for e in other:  # 理论上不会出现（已有 inListFilter），防御式保留
        c = agg[e]
        print(f"{e:<20} {c['raw']:>6} {c['diag']:>6} {c['raw']-c['diag']:>6}")
    print("\n净 = 业务口径；D1 询盘应与「净」同向（D1 0 时净也应为 0）。")
    print("采集侧过滤器已激活（Exclude Tag Assistant preview traffic · Active），"
          "但**不追溯**：历史窗口仍要按会话来源剔除，所以别删这段逻辑。")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("realtime")
    p = sub.add_parser("events"); p.add_argument("--days", type=int, default=7)
    p.add_argument("--exclude-diagnostic", action="store_true")
    p = sub.add_parser("event"); p.add_argument("name"); p.add_argument("--days", type=int, default=30)
    p.add_argument("--exclude-diagnostic", action="store_true")
    p = sub.add_parser("conversion"); p.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    return {"realtime": cmd_realtime, "events": cmd_events,
            "event": cmd_event, "conversion": cmd_conversion}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
