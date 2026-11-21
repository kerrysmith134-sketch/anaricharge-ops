#!/usr/bin/env python3
"""north_star.py — 全渠道单一度量契约（North Star）。

所有渠道任务（内容/SEO/GEO/社媒/外联/内链/转化）都必须能在这里被看见。
每天跑一次，输出 08-execution/dashboard/north-star-<日期>.json + 一屏摘要。

数据源：
  - GSC 官方 API（展示/点击/CTR/位次/页面）—— KPI 用页面维度或无维度总量
  - GA4 事件（form_start / form_submit / generate_lead）
  - Instantly 营销外联（MKT-OUTREACH-*，只统计营销线，不含 SDR）
  - 本地台账（索引覆盖、GEO 引用、内容产出）

用法：
  python3 scripts/metrics/north_star.py                # 用缓存（若当天已有 GSC 文件）
  python3 scripts/metrics/north_star.py --refresh      # 重新拉 GSC
  python3 scripts/metrics/north_star.py --days 28
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys

WS = "/Users/kerrychu/anari-charge-website"
OUT = os.path.join(WS, "08-execution", "dashboard")
DAILY = os.path.join(WS, "08-execution", "daily")
MKT = os.path.join(WS, "08-execution", "marketing-outbound")

# 分阶段目标（与 03-workflows/TARGETS.md 对齐）
STAGES = [
    {"stage": "S1", "month": 1, "sessions": 800, "inquiries": 3},
    {"stage": "S2", "month": 3, "sessions": 5000, "inquiries": 15},
    {"stage": "S3", "month": 6, "sessions": 20000, "inquiries": 40},
    {"stage": "S4", "month": 12, "sessions": 60000, "inquiries": 80},
    {"stage": "S5", "month": 24, "sessions": 100000, "inquiries": 100},
]


def today():
    return dt.date.today().isoformat()


def gsc_path(day):
    return os.path.join(WS, "08-execution", "gsc-%s.json" % day.replace("-", ""))


def refresh_gsc(start, end, path):
    cmd = [sys.executable, os.path.join(WS, "scripts", "gsc_pull.py"),
           "--start", start, "--end", end, "--out", path]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        return True, None
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:200]


def load_gsc(day, days, refresh):
    path = gsc_path(day)
    if refresh or not os.path.exists(path):
        end = day
        start = (dt.date.fromisoformat(day) - dt.timedelta(days=days - 1)).isoformat()
        ok, err = refresh_gsc(start, end, path)
        if not ok:
            return None, "gsc_pull 失败: %s" % err
    return json.load(open(path, encoding="utf-8")), None


def local_json(path, default):
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return default
    return default


def marketing_snapshot():
    """只统计营销线（MKT-OUTREACH-*），SDR 一律不读。"""
    try:
        sys.path.insert(0, os.path.join(WS, "scripts", "outbound"))
        import instantly_client as ic
    except Exception:  # noqa: BLE001
        return {"error": "instantly_client 不可用"}
    try:
        camps = [c for c in ic.list_campaigns()
                 if (c.get("name") or "").startswith("MKT-OUTREACH")]
        rows = {c.get("campaign_id"): c for c in (ic.analytics() or [])}
        out = []
        for c in camps:
            a = rows.get(c.get("id"), {})
            items = (ic.call("/leads/list", "POST",
                             {"campaign": c.get("id"), "limit": 100}).get("items") or [])
            out.append({
                "name": c.get("name"), "status": c.get("status"),
                "leads": len(items),
                "sent": int(a.get("emails_sent_count") or 0),
                "replies": int(a.get("reply_count_unique") or 0),
                "bounces": int(a.get("bounced_count") or 0),
            })
        return {"campaigns": out,
                "leads_total": sum(x["leads"] for x in out),
                "sent_total": sum(x["sent"] for x in out),
                "replies_total": sum(x["replies"] for x in out)}
    except SystemExit as e:
        return {"error": str(e)[:200]}


def stage_target(day):
    """按最早月份映射到当前应达成的阶段目标。"""
    start = dt.date(2026, 11, 1)
    months = max(1, (dt.date.fromisoformat(day) - start).days // 30 + 1)
    hit = [s for s in STAGES if s["month"] <= months]
    return hit[-1] if hit else STAGES[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=28)
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()

    day = today()
    gsc, err = load_gsc(day, a.days, a.refresh)
    ns = {
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "day": day,
        "window_days": a.days,
        "stage_target": stage_target(day),
        "sections": {},
        "errors": [],
    }

    # 1) 自然搜索
    if gsc:
        pt = gsc.get("page_totals") or {}
        pages = gsc.get("pages") or []
        zero_click = [p for p in pages
                      if (p.get("impressions") or 0) >= 40 and (p.get("clicks") or 0) == 0]
        ns["sections"]["organic"] = {
            "clicks": pt.get("clicks"), "impressions": pt.get("impressions"),
            "ctr_pct": pt.get("ctr"), "avg_position_weighted": pt.get("avg_position_weighted"),
            "pages_with_impressions": gsc.get("pages_with_impressions"),
            "zero_click_pages_ge40": len(zero_click),
            "zero_click_list": [p.get("page") for p in zero_click[:20]],
            "top_pages": sorted(pages, key=lambda p: -(p.get("impressions") or 0))[:10],
        }
        ev = {list(e.keys())[0]: list(e.values())[0]
              for e in (gsc.get("ga4_events") or []) if isinstance(e, dict)}
        ns["sections"]["ga4_events"] = ev
    else:
        ns["errors"].append(err or "无 GSC 数据")

    # 2) 转化（询盘）——口径：D1 为准；此处用前端事件与本地台账做观测
    #    2026-11-09：GA4 侧已剔除 Tag Assistant / GTM 预览诊断会话（见 gsc_pull.py），
    #    被剔除量单列，避免看板报「无询盘却有 13 次 form_submit」的假转化。
    ev = ns["sections"].get("ga4_events") or {}
    diag_ev = {list(e.keys())[0]: list(e.values())[0]
               for e in ((gsc or {}).get("ga4_diagnostic_events") or [])
               if isinstance(e, dict)}
    ns["sections"]["conversion"] = {
        "form_start": ev.get("form_start"), "form_submit": ev.get("form_submit"),
        "generate_lead": ev.get("generate_lead"),
        "diagnostic_excluded": diag_ev,
        "note": "真实询盘以 D1 submissions 为准；GA4 已剔除 tagassistant 诊断流量"
                "（被剔除量见 diagnostic_excluded），仅作链路观测",
    }

    # 2b) 转化事件改读 live GA4（带诊断剔除），不再依赖 GSC 快照里的陈旧/未过滤数字。
    #     2026-11-09 修：快照里的 form_submit 13 / generate_lead 9 全是 Tag Assistant
    #     预览流量，D1 一条询盘都没有 —— 看板报假转化比没有数字更糟。
    try:
        sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))
        import ga4_query as _gq
        import datetime as _dt
        _end = _dt.date.today()
        _start = _end - _dt.timedelta(days=a.days)
        _rep = _gq.post("runReport", {
            "dateRanges": [{"startDate": _start.isoformat(), "endDate": _end.isoformat()}],
            "dimensions": [{"name": "eventName"}, {"name": "sessionSource"}],
            "metrics": [{"name": "eventCount"}],
            "dimensionFilter": {"filter": {"fieldName": "eventName",
                                           "inListFilter": {"values": _gq.CONV_EVENTS}}},
            "limit": 500})
        if "error" in _rep:
            ns["sections"]["conversion"]["live_error"] = _rep.get("error")
        else:
            _agg = {}
            for _r in _rep.get("rows") or []:
                _ev = _r["dimensionValues"][0]["value"]
                _src = _r["dimensionValues"][1]["value"]
                _n = int(_r["metricValues"][0]["value"])
                _c = _agg.setdefault(_ev, {"raw": 0, "diag": 0})
                _c["raw"] += _n
                if _gq.is_diagnostic_source(_src):
                    _c["diag"] += _n
            _clean = {k: v["raw"] - v["diag"] for k, v in _agg.items()}
            _diag = {k: v["diag"] for k, v in _agg.items() if v["diag"]}
            ns["sections"]["conversion"].update({
                "form_start": _clean.get("form_start", 0),
                "form_submit": _clean.get("form_submit", 0),
                "generate_lead": _clean.get("generate_lead", 0),
                "diagnostic_excluded": _diag,
                "source": "GA4 live（已剔除 tagassistant 诊断会话）",
            })
    except Exception as e:  # noqa: BLE001
        ns["sections"]["conversion"]["live_error"] = str(e)[:160]

    # 3) 营销外联
    ns["sections"]["marketing_outbound"] = marketing_snapshot()

    # 4) 收录覆盖 —— 按 mtime 取最新一份（原来找 index-<day>.json，实际文件名是
    #    index-coverage-*.json，导致看板永远显示"无当日索引文件"）
    import glob as _g
    cand = _g.glob(os.path.join(WS, "08-execution", "tech", "index-coverage*.json"))
    if cand:
        latest = max(cand, key=os.path.getmtime)
        d = local_json(latest, {}) or {}
        inspected = int(d.get("inspected") or 0)
        passed = int((d.get("verdict_dist") or {}).get("PASS") or 0)
        ns["sections"]["indexing"] = {
            "file": os.path.basename(latest),
            "inspected": inspected,
            "indexed": passed,
            "indexed_pct": round(passed / inspected * 100, 1) if inspected else None,
            "sitemap_urls": d.get("sitemap_urls"),
            "not_indexed": d.get("coverage_dist"),
        }
    else:
        ns["sections"]["indexing"] = {"note": "尚无 index-coverage*.json（跑 scripts/index_coverage.py）"}

    # 4b) D1 询盘 —— 口径铁律：询盘只认 D1，GA4 只是链路观测
    try:
        sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))
        import d1_query as _d1
        rows = _d1.query(
            "SELECT COUNT(*) AS n,"
            " SUM(CASE WHEN consent=1 THEN 1 ELSE 0 END) AS c1,"
            " SUM(CASE WHEN consent=0 THEN 1 ELSE 0 END) AS c0"
            " FROM submissions")
        r = (rows or [{}])[0]
        ns["sections"]["inquiries_d1"] = {
            # SUM(...) 在空表上返回 NULL —— 必须归 0，否则日报会打出 "None"
            "available": True, "total": r.get("n") or 0,
            "consent_1": r.get("c1") or 0, "consent_0": r.get("c0") or 0,
        }
    except Exception as e:  # noqa: BLE001
        ns["sections"]["inquiries_d1"] = {"available": False, "error": str(e)[:160]}

    # 4b2) 询盘生命周期（Growth OS 计划的北极星：SAQO）
    # 数据源是本地账本（08-execution/inquiry/lifecycle.jsonl），由
    # scripts/metrics/lead_lifecycle.py 维护；CRM 未上线前这是最接近
    # "销售接受的机会"的可信记录。没有账本时明确标 no_data，不编数字。
    try:
        sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))
        import lead_lifecycle as _ll
        recs = list(_ll.load().values())
        if recs:
            def _stage(r):
                return r.get("max_stage") if r.get("max_stage") is not None else _ll.ORDER.get(r["status"], 0)
            ns["sections"]["lead_lifecycle"] = {
                "available": True,
                "tracked": len(recs),
                "mql": sum(1 for r in recs if _stage(r) >= _ll.ORDER["mql"]),
                "sal": sum(1 for r in recs if _stage(r) >= _ll.ORDER["sal"]),
                "saqo": sum(1 for r in recs if _stage(r) >= _ll.ORDER["saqo"]),
                "won": sum(1 for r in recs if r["status"] == "won"),
                "pipeline_usd": sum((r.get("pipeline_value") or 0) for r in recs
                                    if r["status"] in ("saqo", "won")),
                "lost_reasons": [e.get("reason") for r in recs
                                 if r["status"] in ("lost", "disqualified")
                                 for e in (r.get("events") or []) if e.get("reason")][:8],
            }
        else:
            ns["sections"]["lead_lifecycle"] = {"available": False, "note": "账本为空（先跑 lead_lifecycle.py sync）"}
    except Exception as e:  # noqa: BLE001
        ns["sections"]["lead_lifecycle"] = {"available": False, "error": str(e)[:160]}

    # 4b3) GA4 生命周期事件（服务端 Measurement Protocol 发的，不是浏览器事件）
    # 这是 GROW-004 的落地：MQL / SAL / SAQO 现在真的能在 GA4 里看到。
    try:
        sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))
        import ga4_query as _gq
        import datetime as _dt
        end = _dt.date.today()
        start = end - _dt.timedelta(days=30)
        # 不用 dimensionFilter（v1beta 的 StringFilter 方言容易踩坑）：
        # 直接取前 60 个事件名，再在本地挑生命周期事件 —— 少一次 API 语义依赖。
        d = _gq.post("runReport", {
            "dateRanges": [{"startDate": start.isoformat(), "endDate": end.isoformat()}],
            "dimensions": [{"name": "eventName"}],
            "metrics": [{"name": "eventCount"}],
            "limit": 60})
        if "error" in d:
            ns["sections"]["ga4_lifecycle"] = {"available": False, "error": d.get("error")}
        else:
            LIFE = {"lead_mql", "lead_sal", "opportunity_created",
                    "closed_won", "closed_lost", "lead_disqualified"}
            counts = {r["dimensionValues"][0]["value"]: int(r["metricValues"][0]["value"])
                      for r in (d.get("rows") or [])
                      if r["dimensionValues"][0]["value"] in LIFE}
            ns["sections"]["ga4_lifecycle"] = {"available": True, "window_days": 30,
                                               "counts": counts, "total": sum(counts.values())}
    except Exception as e:  # noqa: BLE001
        ns["sections"]["ga4_lifecycle"] = {"available": False, "error": str(e)[:160]}

    # 4c) 引用域 —— 逐页验证过的真实外链
    ledger = local_json(os.path.join(WS, "08-execution", "backlink",
                                     "referring-domains.json"), None)
    if ledger:
        rows = [r for r in (ledger.get("rows") or []) if r.get("status") == "active"]
        follow = [r for r in rows if (r.get("result") or {}).get("rel") != "nofollow"]
        ns["sections"]["referring_domains"] = {
            "active_pages": len(rows),
            "domains": len({r["domain"] for r in rows}),
            "follow_domains": len({r["domain"] for r in follow}),
            "list": sorted({r["domain"] for r in rows}),
        }
    else:
        ns["sections"]["referring_domains"] = {"note": "尚无 referring-domains.json"}

    # 5) GEO 引用台账
    # 兼容两种格式：裸数组（旧）与 {"rows":[...]}（geo_check.py 写的，2026-11-07 起）
    geo_raw = local_json(os.path.join(WS, "08-execution", "geo", "geo-citations.json"), [])
    geo = geo_raw.get("rows", []) if isinstance(geo_raw, dict) else (geo_raw or [])
    cited = [g for g in geo if isinstance(g, dict) and g.get("cited")]
    ns["sections"]["geo"] = {
        "checked": len(geo), "cited": len(cited),
        "layer": geo_raw.get("layer") if isinstance(geo_raw, dict) else "unknown",
    }
    if not geo:
        ns["sections"]["geo"]["note"] = "尚无 geo-citations.json（GEO 任务首跑后生成）"

    # 6) 与阶段目标的差距 —— 用已校准的 M1 领先指标（见 CALIBRATION-20261107.md）
    #    旧模型用"月访问 800"当第 1 月目标，已证明按 SEO 路径不可达（需 1,194+ 页），
    #    所以 gap 改为考核可控项：可索引页数 / 外联发出 / D1 询盘。
    state = local_json(os.path.join(WS, "08-execution", "flywheel", "state.json"), {}) or {}
    kpis = state.get("kpis") or {}
    def val(k):
        return (kpis.get(k) or {}).get("target")
    idx_sec = ns["sections"].get("indexing") or {}
    d1_sec = ns["sections"].get("inquiries_d1") or {}
    rd_sec = ns["sections"].get("referring_domains") or {}
    ob = (ns["sections"].get("marketing_outbound") or {})
    sent = sum((c.get("sent") or 0) for c in (ob.get("campaigns") or []))
    rows = [
        {"kpi": "A.indexable_pages", "value": idx_sec.get("sitemap_urls"), "target": val("A.indexable_pages")},
        {"kpi": "A.index_coverage_pct", "value": idx_sec.get("indexed_pct"), "target": val("A.index_coverage_pct")},
        {"kpi": "B.inquiries", "value": d1_sec.get("total"), "target": val("B.inquiries")},
        {"kpi": "C.outreach_sent", "value": sent, "target": val("C.outreach_sent")},
        {"kpi": "C.referring_domains", "value": rd_sec.get("domains"), "target": val("C.referring_domains")},
    ]
    def status(v, tg):
        if v is None or tg is None:
            return "no_data"
        return "on_track" if v >= tg else "behind"
    for r in rows:
        r["status"] = status(r["value"], r["target"])
        r["progress_pct"] = (round(r["value"] / r["target"] * 100, 1)
                             if r["value"] is not None and r["target"] else None)
    ns["gap"] = {
        "cycle": state.get("stage_cycle"),
        "basis": "M1 领先指标（CALIBRATION-20261107）",
        "rows": rows,
        "behind": [r["kpi"] for r in rows if r["status"] == "behind"],
        "note": "访问量已降为观测指标，不再作为 gap 依据（见 CALIBRATION-20261107）",
    }

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "north-star-%s.json" % day)
    json.dump(ns, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 一屏摘要
    o = ns["sections"].get("organic") or {}
    m = ns["sections"]["marketing_outbound"]
    print("=" * 62)
    print("North Star — %s（窗口 %d 天）" % (day, a.days))
    print("=" * 62)
    print("自然搜索  点击 %s | 展示 %s | CTR %s%% | 位次 %s" %
          (o.get("clicks"), o.get("impressions"), o.get("ctr_pct"), o.get("avg_position_weighted")))
    print("零点击页  展示≥40 且 0 点击：%s 个" % o.get("zero_click_pages_ge40"))
    c = ns["sections"]["conversion"]
    print("转化事件  form_start %s | form_submit %s | generate_lead %s%s" %
          (c.get("form_start"), c.get("form_submit"), c.get("generate_lead"),
           ("（业务口径，已剔除诊断 %s 条）" % sum((c.get("diagnostic_excluded") or {}).values())
            if c.get("diagnostic_excluded") else "")))
    print("营销外联  活动 %s | 线索 %s | 已发 %s | 回复 %s" %
          (len(m.get("campaigns") or []), m.get("leads_total"), m.get("sent_total"), m.get("replies_total")))
    print("GEO       已查 %s | 被引 %s" % (ns["sections"]["geo"]["checked"], ns["sections"]["geo"]["cited"]))
    ix = ns["sections"].get("indexing") or {}
    if ix.get("inspected"):
        print("收录覆盖  %s / %s = %s%%（%s）" %
              (ix.get("indexed"), ix.get("inspected"), ix.get("indexed_pct"), ix.get("file")))
    d1 = ns["sections"].get("inquiries_d1") or {}
    print("D1 询盘   total %s（consent1 %s / consent0 %s）" %
          (d1.get("total"), d1.get("consent_1"), d1.get("consent_0")))
    rd = ns["sections"].get("referring_domains") or {}
    print("引用域    %s 个（dofollow %s）：%s" %
          (rd.get("domains"), rd.get("follow_domains"), ", ".join(rd.get("list") or []) or "—"))
    print("-" * 62)
    g = ns["gap"]
    print("目标对照  %s（%s）" % (g.get("cycle"), g.get("basis")))
    for r in g.get("rows") or []:
        print("          %-26s %-8s 目标 %-6s 进度 %s%%" %
              (r["kpi"], r["value"], r["target"], r["progress_pct"]))
    if g.get("behind"):
        print("          落后项: %s" % ", ".join(g["behind"]))
    if ns["errors"]:
        print("错误:", "; ".join(ns["errors"]))
    print("→", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
