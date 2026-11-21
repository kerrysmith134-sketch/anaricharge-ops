#!/usr/bin/env python3
"""GSC / GA4 只读数据拉取器（接管后执行用）。

凭证只读引用源目录的 .secrets/gsc-oauth.json，不复制、不回写、不打印密钥。
用法:
  python3 scripts/gsc_pull.py --start 2026-10-10 --end 2026-11-06 --out 08-execution/gsc-20261107.json
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

SECRETS = "/Users/kerrychu/Documents/kimi/workspace/.secrets/gsc-oauth.json"
GSC_SITE = "sc-domain%3Aanaricharge.com"
GA4_PROPERTY = "553998974"  # G-MT63H5Q8EV


def _load():
    with open(SECRETS) as f:
        return json.load(f)


def access_token(d=None):
    """用 refresh_token 换 access_token（内存态，不回写文件）。"""
    d = d or _load()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=urllib.parse.urlencode({
            "client_id": d["client_id"],
            "client_secret": d["client_secret"],
            "refresh_token": d["refresh_token"],
            "grant_type": "refresh_token",
        }).encode())
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["access_token"]


def gsc(dimensions, start, end, row_limit=1000, at=None, filters=None):
    at = at or access_token()
    body = {"startDate": start, "endDate": end,
            "dimensions": dimensions, "rowLimit": row_limit}
    if filters:
        body["dimensionFilterGroups"] = [{"filters": filters}]
    req = urllib.request.Request(
        "https://www.googleapis.com/webmasters/v3/sites/" + GSC_SITE + "/searchAnalytics/query",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + at, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r).get("rows") or []


def ga4(body, at=None):
    at = at or access_token()
    req = urllib.request.Request(
        "https://analyticsdata.googleapis.com/v1beta/properties/" + GA4_PROPERTY + ":runReport",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + at, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def shape(rows, dims):
    out = []
    for r in rows:
        item = {d: r["keys"][i] for i, d in enumerate(dims)}
        item.update(clicks=r.get("clicks", 0),
                    impressions=r.get("impressions", 0),
                    ctr=round(r.get("ctr", 0) * 100, 2),
                    position=round(r.get("position", 0), 1))
        out.append(item)
    return out


def totals(rows):
    c = sum(r.get("clicks", 0) for r in rows)
    i = sum(r.get("impressions", 0) for r in rows)
    # 加权平均位次（按展示加权，接管前的看板曾用简单平均导致误读）
    w = sum(r.get("position", 0) * r.get("impressions", 0) for r in rows)
    return {"clicks": c, "impressions": i,
            "ctr": round(c / i * 100, 2) if i else 0.0,
            "avg_position_weighted": round(w / i, 2) if i else 0.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--compare-start")
    ap.add_argument("--compare-end")
    a = ap.parse_args()

    result = {"generated_at": dt.datetime.now().astimezone().isoformat(),
              "window": {"start": a.start, "end": a.end},
              "property": "sc-domain:anaricharge.com", "ga4": "G-MT63H5Q8EV"}
    try:
        at = access_token()
        result["auth"] = "ok"
    except Exception as e:  # noqa: BLE001
        result["auth"] = "failed: %s" % e
        json.dump(result, open(a.out, "w"), ensure_ascii=False, indent=2)
        print("AUTH FAILED", e)
        return 1

    try:
        rq = gsc(["query"], a.start, a.end, 1000, at)
        rp = gsc(["page"], a.start, a.end, 1000, at)
        rq7 = gsc(["query"], a.end, a.end, 1000, at)
        result["queries"] = shape(rq, ["query"])
        result["pages"] = shape(rp, ["page"])
        result["query_totals"] = totals(rq)
        result["page_totals"] = totals(rp)
        result["pages_with_impressions"] = sum(1 for p in result["pages"] if p["impressions"] > 0)
        result["last_day_queries"] = shape(rq7, ["query"])
        result["last_day_totals"] = totals(rq7)
        if a.compare_start and a.compare_end:
            cq = gsc(["query"], a.compare_start, a.compare_end, 1000, at)
            result["compare"] = {"window": {"start": a.compare_start, "end": a.compare_end},
                                 "query_totals": totals(cq)}
    except urllib.error.HTTPError as e:
        result["gsc_error"] = "HTTP %s: %s" % (e.code, e.read()[:300].decode("utf-8", "replace"))
    except Exception as e:  # noqa: BLE001
        result["gsc_error"] = "%s: %s" % (type(e).__name__, e)

    # GA4（走系统代理；失败不致命）
    # 2026-11-09：按 (eventName, sessionSource) 拆分后在本地聚合，把
    # **Tag Assistant / GTM 预览会话**（sessionSource 含 tagassistant）从业务口径里剔除。
    # 起因：11-09 当天 4 个转化类事件全部来自 Tag Assistant 预览（D1 一条请求都没有），
    # 裸 count 会让 north_star 报「form_submit 13 / generate_lead 11」的假转化。
    try:
        rep = ga4({
            "dateRanges": [{"startDate": a.start, "endDate": a.end}],
            "metrics": [{"name": "eventCount"}],
            "dimensions": [{"name": "eventName"}, {"name": "sessionSource"}],
            "limit": 500,
        }, at)
        raw, diag = {}, {}
        for r in rep.get("rows") or []:
            ev = r["dimensionValues"][0]["value"]
            src = (r["dimensionValues"][1]["value"] or "").lower()
            n = int(r["metricValues"][0]["value"])
            raw[ev] = raw.get(ev, 0) + n
            if "tagassistant" in src:
                diag[ev] = diag.get(ev, 0) + n
        clean = {ev: raw[ev] - diag.get(ev, 0) for ev in raw}
        # 兼容原消费方（north_star 读 ga4_events）：默认给业务口径
        result["ga4_events"] = [{ev: n} for ev, n in clean.items() if n]
        result["ga4_events_raw"] = [{ev: n} for ev, n in raw.items()]
        result["ga4_diagnostic_events"] = [{ev: n} for ev, n in diag.items() if n]
        result["ga4_diagnostic_note"] = ("ga4_events 已剔除 sessionSource 含 tagassistant "
                                         "的诊断流量；被剔除量见 ga4_diagnostic_events")
    except Exception as e:  # noqa: BLE001
        result["ga4_error"] = "%s: %s" % (type(e).__name__, str(e)[:240])

    json.dump(result, open(a.out, "w"), ensure_ascii=False, indent=2)
    print("WROTE", a.out)
    print("query_totals:", json.dumps(result.get("query_totals"), ensure_ascii=False))
    print("page_totals:", json.dumps(result.get("page_totals"), ensure_ascii=False))
    print("pages_with_impressions:", result.get("pages_with_impressions"))
    print("ga4:", "ok" if "ga4_events" in result else result.get("ga4_error"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
