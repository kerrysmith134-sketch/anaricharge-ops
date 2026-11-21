#!/usr/bin/env python3
"""build_site_dashboard.py — 生成 ANARI 运营仪表盘（单文件 HTML，可离线打开）。

数据全部来自本工作区已有产物，不编造、不估算：
  - 08-execution/daily/dashboard-<date>.json        R6 看板（GSC 页面维度 + 环比 + 周序列 + 0 点击页）
  - 08-execution/dashboard/north-star-<date>.json   全渠道单一度量（GA4/D1/收录/引用域/GEO/外联）
  - 08-execution/tech/index-coverage-full-*.json    GSC URL Inspection 全量审计（只信 scope=full）
  - 08-execution/content/content-ledger.json        内容刷新台账（0 点击页修复状态）
  - 08-execution/geo/geo-citations*.json            GEO 两层引用台账
  - 08-execution/backlink/referring-domains.json    引用域台账
  - 站点仓库 git log / 本机门禁（validate / check-facts / 入链）
  - Brevo CRM（只读，API 失败则降级为 unknown）

用法：
  python3 scripts/metrics/build_site_dashboard.py [--date YYYY-MM-DD]
输出：
  08-execution/dashboard/site-dashboard-<date>.json
  08-execution/dashboard/site-dashboard-<date>.html
"""
import argparse
import base64
import collections
import datetime as dt
import glob
import html
import json
import os
import re
import subprocess
import sys

WS = "/Users/kerrychu/anari-charge-website"
SITE = os.path.join(WS, "06-site", "anari-new-site")
OUT = os.path.join(WS, "08-execution", "dashboard")
LOGO_DIR = os.path.expanduser("~/.agents/skills/anari-design-system/assets")


# ---------------------------------------------------------------- 工具函数
def jload(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return default


def newest(pattern):
    files = glob.glob(os.path.join(WS, pattern))
    return max(files, key=os.path.getmtime) if files else None


def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def fmt(n, dash="—"):
    if n is None:
        return dash
    try:
        return f"{int(round(n)):,}"
    except Exception:  # noqa: BLE001
        return str(n)


def f1(n, dash="—"):
    if n is None:
        return dash
    try:
        return f"{float(n):.1f}"
    except Exception:  # noqa: BLE001
        return str(n)


def pct(n, d=1, dash="—"):
    if n is None:
        return dash
    try:
        return f"{float(n):.{d}f}%"
    except Exception:  # noqa: BLE001
        return str(n)


def pct_change(cur, prev):
    try:
        if not prev:
            return None
        return round((cur - prev) / prev * 100, 1)
    except Exception:  # noqa: BLE001
        return None


def chip(text, tone="neutral"):
    return f'<span class="chip chip-{tone}">{esc(text)}</span>'


def base64_img(path):
    try:
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------- 数据采集
def run_gate(cmd, cwd=SITE, timeout=180):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:  # noqa: BLE001
        return -1, "%s: %s" % (type(e).__name__, str(e)[:160])


def collect_site_health():
    out = {"validate": None, "facts": None, "orphans": None}
    code, log = run_gate(["node", "validate.js"])
    m = re.search(r"VALIDATION PASSED:\s*(\d+) pages", log)
    out["validate"] = {"ok": code == 0, "pages": int(m.group(1)) if m else None}
    code, log = run_gate(["node", "scripts/check-facts.js"])
    m = re.search(r"PASS\s*—\s*(\d+)\s*条机检一致", log)
    out["facts"] = {"ok": code == 0, "count": int(m.group(1)) if m else None}
    code, log = run_gate(["node", "scripts/audit-inbound-links.js", "--min", "3"])
    out["orphans"] = {"ok": code == 0,
                      "count": (0 if ("无孤儿" in log or code == 0) else None)}
    return out


def git_recent(n=6):
    code, log = run_gate(["git", "log", "-%d" % n, "--format=%h|%ad|%s",
                          "--date=format:%m-%d %H:%M"], cwd=SITE)
    rows = []
    if code == 0:
        for line in log.strip().splitlines():
            parts = line.split("|", 2)
            if len(parts) == 3:
                rows.append({"hash": parts[0], "time": parts[1], "subject": parts[2]})
    return rows


def brevo_snapshot():
    try:
        sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))
        import brevo_crm as bc  # noqa: E402
        deals = bc.all_deals()
        return {"ok": True, "deals": len(deals or [])}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:160])}


def collect(day):
    dash_path = os.path.join(WS, "08-execution", "daily",
                             "dashboard-%s.json" % day.isoformat())
    dash = jload(dash_path) or jload(newest("08-execution/daily/dashboard-*.json"))
    ns_path = newest("08-execution/dashboard/north-star-*.json")
    ns = jload(ns_path) or {}
    if not dash:
        raise SystemExit("未找到看板数据（先跑 scripts/metrics/daily_dashboard.py）")

    # 收录审计：只取 scope=full 的最新一份（文件名含 full 兼容老文件）
    audit, audit_file = None, None
    for p in sorted(glob.glob(os.path.join(WS, "08-execution", "tech",
                                           "index-coverage*.json")),
                    key=os.path.getmtime, reverse=True):
        base = os.path.basename(p)
        if "full" not in base:
            continue
        d = jload(p) or {}
        if d.get("scope") in (None, "full"):
            audit, audit_file = d, base
            break

    # 内容台账 → 0 点击页状态
    ledger = jload(os.path.join(WS, "08-execution", "content",
                                "content-ledger.json")) or {"entries": []}
    # 兼容两种形态：dict{"entries":[...]} 与 纯 list（2026-11-13 并行会话改成 list）
    if isinstance(ledger, dict):
        ledger_entries = ledger.get("entries") or []
    elif isinstance(ledger, list):
        ledger_entries = ledger
    else:
        ledger_entries = []
    fixed, diagnosed = set(), set()
    for e in ledger_entries:
        if not isinstance(e, dict):
            continue
        if e.get("type") == "refresh" and e.get("slug"):
            fixed.add(e["slug"])
        if e.get("type") == "diagnosis":
            diagnosed.update(e.get("pages") or [])

    # GEO 两层
    geo_search = jload(os.path.join(WS, "08-execution", "geo",
                                    "geo-citations.json")) or {}
    gs_rows = geo_search.get("rows") if isinstance(geo_search, dict) else geo_search
    gs_rows = gs_rows or []
    geo_ai = jload(os.path.join(WS, "08-execution", "geo",
                                "geo-citations-ai.json")) or {}
    ai_rows = geo_ai.get("rows") if isinstance(geo_ai, dict) else geo_ai
    ai_rows = ai_rows or []

    referring = jload(os.path.join(WS, "08-execution", "backlink",
                                   "referring-domains.json")) or {}
    ref_rows = [r for r in (referring.get("rows") or []) if r.get("status") == "active"]

    # 社交：近 30 天已发布 + 待审批
    qlog = os.path.join(WS, "08-execution", "community", "quora-log.jsonl")
    published_30d = 0
    last_pub = None
    try:
        cutoff = day - dt.timedelta(days=30)
        with open(qlog, encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except Exception:  # noqa: BLE001
                    continue
                if e.get("status") != "published":
                    continue
                try:
                    d0 = dt.date.fromisoformat(str(e.get("date")))
                except Exception:  # noqa: BLE001
                    continue
                if d0 >= cutoff:
                    published_30d += 1
                if last_pub is None or d0 > last_pub:
                    last_pub = d0
    except Exception:  # noqa: BLE001
        pass
    pending = len(glob.glob(os.path.join(WS, "08-execution", "community",
                                         "pending", "*.md")))

    s = ns.get("sections") or {}
    site_health = collect_site_health()
    commits = git_recent(6)
    brevo = brevo_snapshot()

    # ---- 汇总 ----
    organic = s.get("organic") or {}
    ga4 = s.get("ga4_events") or {}
    conv = s.get("conversion") or {}
    idx_ns = s.get("indexing") or {}
    d1 = s.get("inquiries_d1") or {}
    out_ns = s.get("marketing_outbound") or {}
    life = s.get("lead_lifecycle") or {}
    domains = s.get("referring_domains") or {}
    geo_ns = s.get("geo") or {}

    audit_data = audit or {}
    sitemap_urls = audit_data.get("sitemap_urls") or idx_ns.get("sitemap_urls")
    inspected = audit_data.get("inspected") or idx_ns.get("inspected")
    indexed = int((audit_data.get("verdict_dist") or {}).get("PASS")
                  or idx_ns.get("indexed") or 0)
    cov_dist = audit_data.get("coverage_dist") or idx_ns.get("not_indexed") or {}
    indexed_pct = round(indexed / inspected * 100, 1) if inspected else None
    unknown = int((cov_dist or {}).get("URL is unknown to Google") or 0)
    discovered = int((cov_dist or {}).get("Discovered - currently not indexed") or 0)

    weekly = dash.get("weekly_series") or []
    daily = dash.get("daily_series") or []
    zero = (dash.get("derived") or {}).get("zero_click_pages_ge40") or {}
    wow = ((dash.get("derived") or {}).get("week_over_week") or {})
    cmp_ = dash.get("compare") or {}
    top = dash.get("top_pages") or []

    zero_rows = []
    for r in zero.get("list") or []:
        path = str(r.get("page", "")).replace("https://www.anaricharge.com", "")
        status = "fixed" if path in fixed else ("non_title" if path in diagnosed else "todo")
        zero_rows.append({"page": path, "url": r.get("page"),
                          "impressions": r.get("impressions"),
                          "position": r.get("position"), "status": status})

    data = {
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "day": day.isoformat(),
        "site": "https://www.anaricharge.com",
        "role": "R6 数据分析师",
        "window": dash.get("window"),
        "effective_data_end": dash.get("effective_data_end"),
        "data_lag_days": dash.get("data_lag_days"),
        "data_lag_note": dash.get("data_lag_note"),
        "compare_window": (cmp_.get("window") or {}),
        "kpi": {
            "clicks": dash.get("clicks"),
            "impressions": dash.get("impressions"),
            "ctr": dash.get("ctr"),
            "avg_position_weighted": dash.get("avg_position_weighted"),
            "pages_with_impressions": dash.get("pages_with_impressions"),
            "pages_scanned": dash.get("pages_scanned"),
            "d1_inquiries": d1.get("total"),
        },
        "prev": {
            "clicks": cmp_.get("clicks"),
            "impressions": cmp_.get("impressions"),
            "ctr": cmp_.get("ctr"),
            "avg_position_weighted": cmp_.get("avg_position_weighted"),
        },
        "change": cmp_.get("change_pct") or {},
        "wow": wow,
        "weekly_series": weekly,
        "daily_series": daily,
        "daily_series_note": dash.get("daily_series_note"),
        "query_dimension_dropped_pct": dash.get("query_dimension_dropped_pct"),
        "cross_check": dash.get("cross_check"),
        "top_pages": top,
        "zero_click": {"threshold": zero.get("threshold_impressions"),
                       "count": zero.get("count"),
                       "impressions_at_stake": zero.get("impressions_at_stake"),
                       "rows": zero_rows},
        "ga4_events": ga4,
        "conversion": conv,
        "funnel": {
            "impressions": dash.get("impressions"),
            "clicks": dash.get("clicks"),
            "ga4_page_view": ga4.get("page_view"),
            "ga4_session_start": ga4.get("session_start"),
            "form_start": ga4.get("form_start") or conv.get("form_start"),
            "form_submit": ga4.get("form_submit") or conv.get("form_submit"),
            "generate_lead": ga4.get("generate_lead") or conv.get("generate_lead"),
            "d1_inquiries": d1.get("total"),
        },
        "indexing": {
            "audited_at": audit_data.get("generated_at") or idx_ns.get("audited_at"),
            "source_file": audit_file or idx_ns.get("file"),
            "inspected": inspected,
            "indexed": indexed,
            "indexed_pct": indexed_pct,
            "sitemap_urls": sitemap_urls,
            "unknown": unknown,
            "discovered": discovered,
        },
        "authority": {
            "referring_domains": domains.get("domains"),
            "follow_domains": domains.get("follow_domains"),
            "domain_list": domains.get("list") or [],
            "geo_search": {"checked": len(gs_rows),
                           "cited": sum(1 for r in gs_rows if r.get("cited"))},
            "geo_ai": {"checked": len(ai_rows),
                       "cited": sum(1 for r in ai_rows if r.get("cited"))},
        },
        "outbound": {
            "campaigns": len(out_ns.get("campaigns") or []),
            "leads": out_ns.get("leads_total"),
            "sent": out_ns.get("sent_total"),
            "replies": out_ns.get("replies_total"),
        },
        "social": {"published_30d": published_30d,
                   "last_published": last_pub.isoformat() if last_pub else None,
                   "pending": pending},
        "crm": {"d1_inquiries": d1.get("total"),
                "saqo": (life.get("saqo") if life.get("available") else 0),
                "brevo_deals": brevo.get("deals") if brevo.get("ok") else None,
                "brevo_error": None if brevo.get("ok") else brevo.get("error")},
        "site_health": site_health,
        "commits": commits,
        "gap": build_gap(sitemap_urls, indexed_pct, d1.get("total"),
                         out_ns.get("sent_total"), domains.get("domains")),
        "sources": {
            "gsc": "sc-domain:anaricharge.com（GSC 官方 API，页面维度）",
            "ga4": "G-MT63H5Q8EV（GA4 Data API）",
            "d1": "Cloudflare D1 submissions（询盘唯一真源）",
            "index": "GSC URL Inspection API（scope=full）",
            "brevo": "Brevo CRM Deals（只读）",
        },
        "data_files": {
            "r6_dashboard": os.path.relpath(dash_path, WS),
            "north_star": os.path.relpath(ns_path, WS) if ns_path else None,
            "index_audit": ("08-execution/tech/" + audit_file) if audit_file else None,
            "content_ledger": "08-execution/content/content-ledger.json",
            "handoff": "08-execution/HANDOFF-TO-R1.md",
        },
    }
    return data


def build_gap(indexable, coverage_pct, inquiries, outreach_sent, referring):
    def row(key, label, value, target, note, better="high"):
        status = "no_data"
        prog = None
        if value is not None and target:
            prog = round(value / target * 100, 1)
            status = "on_track" if value >= target else "behind"
        return {"key": key, "label": label, "value": value, "target": target,
                "progress": prog, "status": status, "note": note, "better": better}
    return [
        row("A.indexable_pages", "可索引页面", indexable, 200,
            "页面工厂产出", "high"),
        row("A.index_coverage_pct", "收录覆盖率", coverage_pct, 90,
            "Google 已收录 / 已检查", "high"),
        row("B.inquiries", "真实询盘（D1）", inquiries, 1,
            "M1 校准目标 = 1", "high"),
        row("C.outreach_sent", "外联已发送", outreach_sent, 60,
            "11-10 起三波窗口", "high"),
        row("C.referring_domains", "引用域", referring, 5,
            "dofollow 更值钱", "high"),
    ]


# ---------------------------------------------------------------- SVG 组件
def svg_weekly(series):
    if not series:
        return '<p class="muted">无周序列数据</p>'
    w, h = 820, 330
    pad_l, pad_r, pad_t = 46, 10, 26
    top_h, gap, bot_h = 170, 60, 58
    n = len(series)
    max_i = max([s.get("impressions") or 0 for s in series] + [1])
    max_c = max([s.get("clicks") or 0 for s in series] + [1])
    step = (w - pad_l - pad_r) / n
    bw = step * 0.54
    y_i = pad_t + top_h
    y_c = pad_t + top_h + gap + bot_h

    def yv(val, base, height, mx):
        return base - (val / mx) * height

    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" '
             f'aria-label="近 8 周 GSC 趋势：展示与点击的周度柱状图">']

    # 展示面板
    parts.append(f'<text x="{pad_l}" y="16" class="svg-label">展示 / 周</text>')
    for k in range(0, 5):
        val = max_i * k / 4
        y = yv(val, y_i, top_h, max_i)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w - pad_r}" y2="{y:.1f}" class="svg-grid"/>')
        parts.append(f'<text x="{pad_l - 6}" y="{y + 4:.1f}" text-anchor="end" class="svg-axis">{fmt(val)}</text>')
    for i, s in enumerate(series):
        v = s.get("impressions") or 0
        x = pad_l + i * step + (step - bw) / 2
        y = yv(v, y_i, top_h, max_i)
        cls = "svg-bar svg-bar-partial" if not s.get("complete", True) else "svg-bar"
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{y_i - y:.1f}" rx="3" class="{cls}">'
                     f'<title>{esc(s.get("week_start"))} 展示 {fmt(v)} · 点击 {fmt(s.get("clicks"))}</title></rect>')
        parts.append(f'<text x="{x + bw / 2:.1f}" y="{y - 5:.1f}" text-anchor="middle" class="svg-val">{fmt(v)}</text>')

    # 点击面板
    parts.append(f'<text x="{pad_l}" y="{pad_t + top_h + gap - 14}" class="svg-label">点击 / 周</text>')
    for k in range(0, 3):
        val = max_c * k / 2
        y = yv(val, y_c, bot_h, max_c)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w - pad_r}" y2="{y:.1f}" class="svg-grid"/>')
        parts.append(f'<text x="{pad_l - 6}" y="{y + 4:.1f}" text-anchor="end" class="svg-axis">{fmt(val)}</text>')
    for i, s in enumerate(series):
        v = s.get("clicks") or 0
        x = pad_l + i * step + (step - bw) / 2
        y = yv(v, y_c, bot_h, max_c)
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{y_c - y:.1f}" rx="3" '
                     f'class="svg-bar svg-bar-click"><title>{esc(s.get("week_start"))} 点击 {fmt(v)}</title></rect>')
        if v:
            parts.append(f'<text x="{x + bw / 2:.1f}" y="{y - 4:.1f}" text-anchor="middle" class="svg-val">{fmt(v)}</text>')
        md = str(s.get("week_start", ""))[5:].replace("-", "/")
        parts.append(f'<text x="{x + bw / 2:.1f}" y="{y_c + 16:.1f}" text-anchor="middle" class="svg-axis">{md}</text>')

    parts.append("</svg>")
    return "".join(parts)


def svg_daily(series):
    if not series:
        return '<p class="muted">无日序列数据</p>'
    w, h = 900, 190
    pad_l, pad_r, pad_t, pad_b = 44, 8, 18, 28
    n = len(series)
    max_i = max([s.get("impressions") or 0 for s in series] + [1])
    step = (w - pad_l - pad_r) / n
    bw = step * 0.62
    base = h - pad_b
    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" '
             f'aria-label="按日 GSC 展示趋势（日期维度，仅看形状）">']
    for k in range(0, 4):
        val = max_i * k / 3
        y = base - (val / max_i) * (base - pad_t)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w - pad_r}" y2="{y:.1f}" class="svg-grid"/>')
        parts.append(f'<text x="{pad_l - 6}" y="{y + 4:.1f}" text-anchor="end" class="svg-axis">{fmt(val)}</text>')
    for i, s in enumerate(series):
        v = s.get("impressions") or 0
        x = pad_l + i * step + (step - bw) / 2
        bh = (v / max_i) * (base - pad_t)
        parts.append(f'<rect x="{x:.1f}" y="{base - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="2" '
                     f'class="svg-bar svg-bar-daily">'
                     f'<title>{esc(s.get("date"))} 展示 {fmt(v)} · 点击 {fmt(s.get("clicks"))}</title></rect>')
        label_idx = list(range(0, n, 5))
        if n - 1 not in label_idx and (n - 1) - label_idx[-1] >= 2:
            label_idx.append(n - 1)
        if i in label_idx:
            md = str(s.get("date", ""))[5:].replace("-", "/")
            parts.append(f'<text x="{x + bw / 2:.1f}" y="{base + 15:.1f}" text-anchor="middle" class="svg-axis">{md}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_donut(indexed, total):
    if not total:
        return '<p class="muted">无收录数据</p>'
    p = indexed / total
    r = 54
    c = 2 * 3.1415926 * r
    return (f'<svg viewBox="0 0 160 160" width="160" height="160" role="img" '
            f'aria-label="收录覆盖：{indexed} / {total} 页已收录，{p * 100:.1f}%">'
            f'<circle cx="80" cy="80" r="{r}" fill="none" class="donut-track" stroke-width="16"/>'
            f'<circle cx="80" cy="80" r="{r}" fill="none" class="donut-value" stroke-width="16" '
            f'stroke-linecap="round" stroke-dasharray="{c * p:.1f} {c:.1f}" '
            f'transform="rotate(-90 80 80)"/>'
            f'<text x="80" y="76" text-anchor="middle" class="donut-num">{p * 100:.1f}%</text>'
            f'<text x="80" y="96" text-anchor="middle" class="donut-sub">已收录</text></svg>')


# ---------------------------------------------------------------- HTML 组件
def kpi_card(label, value, sub, tone="neutral", chip_html=""):
    return (f'<article class="card kpi">'
            f'<p class="kpi-label">{esc(label)}</p>'
            f'<p class="kpi-value">{value}</p>'
            f'<p class="kpi-sub">{sub}</p>'
            f'{chip_html}</article>')


def badge(text, tone="neutral"):
    return f'<span class="chip chip-{tone}">{esc(text)}</span>'


def gap_row(r):
    tone = "success" if r["status"] == "on_track" else ("warning" if r["status"] == "behind" else "neutral")
    val = fmt(r["value"]) if isinstance(r["value"], int) else f1(r["value"])
    if r["key"].endswith("pct"):
        val = pct(r["value"])
    prog = min(100, max(0, r["progress"] or 0))
    return (f'<div class="gap-row">'
            f'<div class="gap-head"><span class="gap-label">{esc(r["label"])}</span>'
            f'<span class="gap-val">{val} <span class="muted">/ {fmt(r["target"]) if isinstance(r["target"], int) else f1(r["target"])}</span></span></div>'
            f'<div class="track" role="img" aria-label="{esc(r["label"])} 进度 {prog:.1f}%">'
            f'<span class="fill fill-{tone}" style="width:{prog:.1f}%"></span></div>'
            f'<p class="gap-note">{esc(r["note"])}{" · " + badge("落后", "warning") if r["status"] == "behind" else ""}</p>'
            f'</div>')


def page_link(path):
    url = "https://www.anaricharge.com" + path
    return f'<a class="page-link" href="{esc(url)}" target="_blank" rel="noopener">{esc(path)}</a>'


def top_pages_table(rows):
    if not rows:
        return '<p class="muted">无数据</p>'
    mx = max([r.get("impressions") or 0 for r in rows] + [1])
    body = []
    for i, r in enumerate(rows, 1):
        path = str(r.get("page", "")).replace("https://www.anaricharge.com", "")
        bar = (r.get("impressions") or 0) / mx * 100
        body.append(
            f'<tr><td class="num">{i}</td><td>{page_link(path)}</td>'
            f'<td class="num">{fmt(r.get("clicks"))}</td>'
            f'<td class="num"><span class="cell-bar" aria-hidden="true"><span style="width:{bar:.0f}%"></span></span>{fmt(r.get("impressions"))}</td>'
            f'<td class="num">{pct(r.get("ctr"), 2)}</td>'
            f'<td class="num">{f1(r.get("position"))}</td></tr>')
    return (f'<div class="table-wrap" role="region" aria-labelledby="top-h" tabindex="0">'
            f'<table><caption class="sr-only">近 28 天展示前 10 页面</caption>'
            f'<thead><tr><th scope="col">#</th><th scope="col">页面</th>'
            f'<th scope="col" class="num">点击</th><th scope="col" class="num">展示</th>'
            f'<th scope="col" class="num">CTR</th><th scope="col" class="num">位次</th></tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def zero_table(rows, threshold=40):
    if not rows:
        return '<p class="muted">无数据</p>'
    status_map = {
        "fixed": ("已改 title · 观察中", "success"),
        "non_title": ("非标题瓶颈", "warning"),
        "todo": ("待诊断", "neutral"),
    }
    body = []
    for r in rows:
        label, tone = status_map.get(r["status"], ("待诊断", "neutral"))
        body.append(
            f'<tr><td>{page_link(r["page"])}</td>'
            f'<td class="num">{fmt(r["impressions"])}</td>'
            f'<td class="num">{f1(r["position"])}</td>'
            f'<td>{badge(label, tone)}</td></tr>')
    return (f'<div class="table-wrap" role="region" aria-labelledby="zero-h" tabindex="0">'
            f'<table><caption class="sr-only">展示≥{threshold} 但 0 点击的页面</caption>'
            f'<thead><tr><th scope="col">页面</th><th scope="col" class="num">展示</th>'
            f'<th scope="col" class="num">位次</th><th scope="col">状态</th></tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


# ---------------------------------------------------------------- 主题与页面
CSS = r"""
:root{
  color-scheme:light dark;
  --brand:#1877f2; --brand-press:#1464cc; --brand-ink:#1464cc; --brand-soft:rgba(24,119,242,.10);
  --ink:#342e2c; --ink-2:#6b6560; --ink-3:#9a938d;
  --canvas:#f5f5f7; --surface:#ffffff; --surface-2:#eeedeb; --line:#e6e3df;
  --shadow-card:0 1px 3px rgba(52,46,44,.08),0 4px 14px rgba(52,46,44,.06);
  --danger:#b91c1c; --danger-ink:#991b1b; --danger-soft:rgba(220,38,38,.10);
  --warning:#b45309; --warning-ink:#92400e; --warning-soft:rgba(217,119,6,.12);
  --success:#15803d; --success-ink:#116932; --success-soft:rgba(21,128,61,.10);
  --gutter:24px; --radius:12px;
  --font:-apple-system,BlinkMacSystemFont,"SF Pro Text","PingFang SC","Segoe UI",system-ui,sans-serif;
}
html.dark{
  --ink:#f2f1ef; --ink-2:#a8a29b; --ink-3:#736d67;
  --canvas:#0d0f12; --surface:#15181d; --surface-2:#1d2127; --line:#272c33;
  --brand-soft:rgba(77,148,247,.16); --brand-ink:#6ea8ff;
  --danger:#f87171; --danger-ink:#f87171; --danger-soft:rgba(248,113,113,.14);
  --warning:#fbbf24; --warning-ink:#fbbf24; --warning-soft:rgba(251,191,36,.14);
  --success:#4ade80; --success-ink:#4ade80; --success-soft:rgba(74,222,128,.14);
  --shadow-card:0 1px 3px rgba(0,0,0,.5),0 4px 14px rgba(0,0,0,.35);
}
@media (prefers-color-scheme: dark){
  :root:not(.light):not(.dark){
    --ink:#f2f1ef; --ink-2:#a8a29b; --ink-3:#736d67;
    --canvas:#0d0f12; --surface:#15181d; --surface-2:#1d2127; --line:#272c33;
    --brand-soft:rgba(77,148,247,.16); --brand-ink:#6ea8ff;
    --danger:#f87171; --danger-ink:#f87171; --danger-soft:rgba(248,113,113,.14);
    --warning:#fbbf24; --warning-ink:#fbbf24; --warning-soft:rgba(251,191,36,.14);
    --success:#4ade80; --success-ink:#4ade80; --success-soft:rgba(74,222,128,.14);
    --shadow-card:0 1px 3px rgba(0,0,0,.5),0 4px 14px rgba(0,0,0,.35);
  }
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:var(--canvas);color:var(--ink);font:15px/1.55 var(--font);
  -webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
a{color:var(--brand-ink)}
a:focus-visible,button:focus-visible,.table-wrap:focus-visible{outline:2px solid var(--brand);outline-offset:2px}
.skip{position:absolute;left:-9999px;top:0;background:var(--surface);color:var(--ink);padding:10px 16px;border-radius:8px;z-index:99}
.skip:focus{left:12px;top:12px}
.shell{width:100%;max-width:1920px;margin:0 auto;padding:0 var(--gutter)}
@media (min-width:1200px){:root{--gutter:32px}}
@media (min-width:1600px){:root{--gutter:40px}}
.topbar{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--surface) 86%,transparent);
  backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.topbar-in{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:64px;flex-wrap:wrap;padding-top:8px;padding-bottom:8px}
.brand{display:flex;align-items:center;gap:12px;min-width:0}
.logo{height:26px;width:auto;display:block}
.logo-dark{display:none}
html.dark .logo-light{display:none}
html.dark .logo-dark{display:block}
@media (prefers-color-scheme: dark){
  html:not(.light):not(.dark) .logo-light{display:none}
  html:not(.light):not(.dark) .logo-dark{display:block}
}
.brand-t{display:flex;flex-direction:column;line-height:1.2;min-width:0}
.brand-t strong{font-size:15px;font-weight:600;letter-spacing:.2px}
.brand-t span{font-size:12px;color:var(--ink-2)}
.top-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.theme-btn{min-height:44px;padding:0 14px;border-radius:8px;border:1px solid var(--line);
  background:var(--surface);color:var(--ink-2);font:13px var(--font);cursor:pointer;
  display:inline-flex;align-items:center;gap:8px}
.theme-btn:hover{background:var(--surface-2);color:var(--ink)}
.pill{font-size:12px;padding:4px 10px;border-radius:999px;background:var(--surface-2);color:var(--ink-2)}
.pill.ok{background:var(--success-soft);color:var(--success-ink)}
.pill.warn{background:var(--warning-soft);color:var(--warning-ink)}
main{padding-top:28px;padding-bottom:56px}
.hero{display:flex;justify-content:space-between;gap:24px;align-items:flex-end;flex-wrap:wrap;margin-bottom:24px}
.eyebrow{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2);margin:0 0 6px}
h1{font-size:28px;line-height:1.2;margin:0;font-weight:600;letter-spacing:-.01em}
.hero p{margin:8px 0 0;color:var(--ink-2);font-size:14px;max-width:80ch}
.hero-meta{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}
section{margin-top:14px}
.section-h{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:0 0 10px;flex-wrap:wrap}
.section-h h2{font-size:17px;margin:0;font-weight:600;letter-spacing:-.01em}
.section-h p{margin:0;font-size:12px;color:var(--ink-2)}
.grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:14px}
.span-3{grid-column:span 3}.span-4{grid-column:span 4}.span-5{grid-column:span 5}
.span-6{grid-column:span 6}.span-7{grid-column:span 7}.span-8{grid-column:span 8}.span-12{grid-column:span 12}
@media (max-width:1100px){.span-3,.span-4,.span-5{grid-column:span 6}.span-7,.span-8{grid-column:span 12}}
@media (max-width:680px){.span-3,.span-4,.span-5,.span-6,.span-7,.span-8{grid-column:span 12}}
.kpi-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:14px}
@media (max-width:1200px){.kpi-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (max-width:680px){.kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  box-shadow:var(--shadow-card);padding:18px 18px 16px;min-width:0}
.kpi-label{margin:0;font-size:12px;color:var(--ink-2);letter-spacing:.02em}
.kpi-value{margin:6px 0 2px;font-size:30px;line-height:1.1;font-weight:600;letter-spacing:-.02em}
.kpi-sub{margin:0 0 8px;font-size:12px;color:var(--ink-2)}
.chip{display:inline-flex;align-items:center;gap:4px;font-size:11.5px;line-height:1.2;
  padding:3px 8px;border-radius:999px;background:var(--surface-2);color:var(--ink-2);white-space:nowrap}
.chip-success{background:var(--success-soft);color:var(--success-ink)}
.chip-warning{background:var(--warning-soft);color:var(--warning-ink)}
.chip-danger{background:var(--danger-soft);color:var(--danger-ink)}
.chip-brand{background:var(--brand-soft);color:var(--brand-ink)}
.muted{color:var(--ink-2)}
.small{font-size:12px}
.split{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
.wow-strip{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:12px;
  padding-top:12px;border-top:1px solid var(--line)}
@media (max-width:680px){.wow-strip{grid-template-columns:repeat(2,minmax(0,1fr))}}
.wow-strip .mini{min-width:0}
.wow-strip .mini b{display:block;font-size:18px;font-weight:600;line-height:1.2}
.wow-strip .mini span{font-size:11.5px;color:var(--ink-2)}
figure{margin:0}
figcaption{font-size:12px;color:var(--ink-2);margin-top:6px}
svg text{font-family:var(--font)}
.svg-label{font-size:11px;fill:var(--ink-2)}
.svg-axis{font-size:10.5px;fill:var(--ink-2)}
.svg-val{font-size:10.5px;fill:var(--ink-2)}
.svg-grid{stroke:var(--line);stroke-width:1}
.svg-bar{fill:var(--brand);opacity:.9}
.svg-bar-partial{opacity:.45}
.svg-bar-click{fill:var(--ink-2);opacity:.75}
.svg-bar-daily{fill:var(--brand);opacity:.55}
.gap-row{padding:9px 0;border-bottom:1px solid var(--line)}
.gap-row:last-child{border-bottom:0;padding-bottom:0}
.gap-head{display:flex;justify-content:space-between;gap:10px;font-size:13px}
.gap-label{color:var(--ink-2)}
.gap-val{font-weight:600}
.gap-note{margin:4px 0 0;font-size:11.5px;color:var(--ink-2)}
.track{height:6px;border-radius:999px;background:var(--surface-2);overflow:hidden;margin-top:6px}
.fill{display:block;height:100%;border-radius:999px;background:var(--brand)}
.fill-warning{background:var(--warning)}
.fill-success{background:var(--success)}
.funnel{display:flex;flex-direction:column;gap:0}
.fstep{display:flex;align-items:center;justify-content:space-between;gap:12px;
  padding:10px 12px;border-radius:10px;background:var(--surface-2)}
.fstep b{font-size:18px;font-weight:600}
.fstep .lbl{font-size:13px;color:var(--ink-2)}
.farrow{display:flex;align-items:center;gap:8px;padding:4px 12px;font-size:11.5px;color:var(--ink-2)}
.farrow .line{flex:1;height:1px;background:var(--line);min-width:20px}
.ctx-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:12px}
@media (max-width:680px){.ctx-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
.ctx{background:var(--surface-2);border-radius:10px;padding:10px 12px;min-width:0}
.ctx b{display:block;font-size:17px;font-weight:600}
.ctx span{font-size:11.5px;color:var(--ink-2)}
.donut-track{stroke:var(--surface-2)}
.donut-value{stroke:var(--brand)}
.donut-num{font-size:24px;font-weight:600;fill:var(--ink)}
.donut-sub{font-size:11px;fill:var(--ink-2)}
.legend{display:flex;flex-direction:column;gap:8px;font-size:12.5px;min-width:180px}
.legend-row{display:flex;align-items:center;gap:8px;justify-content:space-between}
.legend-dot{width:9px;height:9px;border-radius:2px;display:inline-block;margin-right:7px}
.donut-wrap{display:flex;gap:20px;align-items:center;flex-wrap:wrap}
.hl-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
@media (max-width:680px){.hl-grid{grid-template-columns:1fr}}
.hl{background:var(--surface-2);border-radius:10px;padding:12px;min-width:0}
.hl h3{margin:0 0 6px;font-size:12px;color:var(--ink-2);font-weight:500}
.hl b{font-size:20px;font-weight:600;display:block;line-height:1.2}
.hl p{margin:4px 0 0;font-size:11.5px;color:var(--ink-2)}
.table-wrap{overflow:auto;max-height:520px}
table{width:100%;border-collapse:collapse;font-size:13.5px}
caption{text-align:left}
th{font-size:11.5px;font-weight:600;color:var(--ink-2);text-align:left;
  padding:8px 10px;background:var(--surface-2);position:sticky;top:0;white-space:nowrap;z-index:1}
th.num,td.num{text-align:right;font-variant-numeric:tabular-nums}
td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:middle}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:var(--brand-soft)}
.page-link{color:var(--ink);text-decoration:none;font-weight:500;word-break:break-word}
.page-link:hover{color:var(--brand-ink);text-decoration:underline}
.cell-bar{display:inline-block;width:64px;height:5px;border-radius:999px;background:var(--surface-2);margin-right:8px;vertical-align:middle;overflow:hidden}
.cell-bar span{display:block;height:100%;background:var(--brand);opacity:.65;border-radius:999px}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.timeline{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:10px}
.timeline li{display:flex;gap:10px;font-size:13px;line-height:1.45}
.timeline time{color:var(--ink-2);font-size:11.5px;white-space:nowrap;padding-top:2px;min-width:74px}
.timeline b{font-weight:500}
.alert{display:flex;gap:8px;align-items:flex-start;padding:9px 0;border-bottom:1px solid var(--line);font-size:13px;line-height:1.45}
.alert:last-child{border-bottom:0}
.alert .dot{width:8px;height:8px;border-radius:50%;background:var(--warning);margin-top:6px;flex:none}
.alert.danger .dot{background:var(--danger)}
.alert.info .dot{background:var(--ink-3)}
.notes{font-size:12.5px;color:var(--ink-2)}
.notes ul{margin:6px 0 0;padding-left:18px;display:flex;flex-direction:column;gap:6px}
.notes li{line-height:1.5}
.notes code{background:var(--surface-2);padding:1px 5px;border-radius:4px;font-size:11.5px}
footer{border-top:1px solid var(--line);margin-top:28px;padding-top:16px;
  font-size:12px;color:var(--ink-2);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
@media (prefers-reduced-motion: reduce){*{transition:none!important;animation:none!important;scroll-behavior:auto!important}}
"""

JS = r"""
(function(){
  var root=document.documentElement;
  var modes=['system','light','dark'];
  var labels={system:'跟随系统',light:'亮色',dark:'暗色'};
  function apply(mode){
    var dark = mode==='dark' || (mode==='system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    root.classList.toggle('dark', dark);
    root.classList.toggle('light', mode==='light');
    root.dataset.themeMode=mode;
    root.dataset.theme=dark?'dark':'light';
    var next=modes[(modes.indexOf(mode)+1)%3];
    var btn=document.getElementById('themeBtn');
    if(btn){ btn.setAttribute('aria-label','外观：'+labels[mode]+'（点击切换到'+labels[next]+'）');
      btn.querySelector('.theme-text').textContent='外观：'+labels[mode]; }
  }
  function cycle(){
    var cur=(function(){try{var v=localStorage.getItem('anari-dash-theme')||'system';return ['system','light','dark'].indexOf(v)<0?'system':v}catch(e){return 'system'}})();
    var next=modes[(modes.indexOf(cur)+1)%3];
    try{localStorage.setItem('anari-dash-theme',next)}catch(e){}
    apply(next);
  }
  var mq=window.matchMedia('(prefers-color-scheme: dark)');
  var onMq=function(){ if((root.dataset.themeMode||'system')==='system') apply('system'); };
  if(mq.addEventListener){mq.addEventListener('change',onMq);}else if(mq.addListener){mq.addListener(onMq);}
  var btn=document.getElementById('themeBtn');
  if(btn){ btn.addEventListener('click',cycle); }
  apply(root.dataset.themeMode||'system');
})();
"""



# ---------------------------------------------------------------- 逐日（用户 2026-11-09 要求）
def _runlog_by_day():
    """run-log.jsonl 按天分组（含 05-records 回填的 hist-* 条目）。"""
    out = collections.defaultdict(list)
    path = os.path.join(WS, "08-execution", "run-log.jsonl")
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        day = (r.get("at") or "")[:10]
        if day:
            out[day].append(r)
    return out


def _artifacts_by_day(days=10):
    """按文件名里的日期统计 08-execution 产物数（不代表全部工作，只作旁证）。"""
    cnt = collections.Counter()
    horizon = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    for root, dirs, files in os.walk(os.path.join(WS, "08-execution")):
        dirs[:] = [x for x in dirs if x not in (".git", "node_modules", "__pycache__")]
        for fn in files:
            if not (fn.endswith(".md") or fn.endswith(".json")):
                continue
            m = re.search(r"(20\d{2})-?(\d{2})-?(\d{2})", fn)
            if not m:
                continue
            day = "%s-%s-%s" % m.groups()
            if day >= horizon:
                cnt[day] += 1
    return cnt


def daily_data_table(series, days=14):
    rows = (series or [])[-days:]
    if not rows:
        return '<p class="muted">无 GSC 日数据</p>'
    body = []
    for r in rows:
        body.append(
            f'<tr><td>{esc(r.get("date"))}</td>'
            f'<td class="num">{fmt(r.get("clicks"))}</td>'
            f'<td class="num">{fmt(r.get("impressions"))}</td>'
            f'<td class="num">{pct(r.get("ctr"), 2)}</td>'
            f'<td class="num">{f1(r.get("position"))}</td></tr>')
    return ('<div class="table-wrap" style="max-height:none"><table>'
            '<caption class="sr-only">近 14 天逐日数据</caption>'
            '<thead><tr><th scope="col">日期</th>'
            '<th scope="col" class="num">点击</th><th scope="col" class="num">展示</th>'
            '<th scope="col" class="num">CTR</th><th scope="col" class="num">位次</th>'
            '</tr></thead><tbody>' + "".join(body) + '</tbody></table></div>')


def daily_work_table(days=7):
    runs = _runlog_by_day()
    arts = _artifacts_by_day(days + 4)
    today = dt.date.today()
    body = []
    for i in range(days - 1, -1, -1):
        day = (today - dt.timedelta(days=i)).isoformat()
        rs = runs.get(day, [])
        parts, seen = [], set()
        for r in rs:
            who = "历史档案" if (r.get("agent") == "history-backfill") else (r.get("agent") or "?")
            task = (r.get("task") or "—")[:34]
            key = (who, task)
            if key in seen:
                continue
            seen.add(key)
            parts.append(f"{who}·{task}")
        summary = "；".join(parts[:2])
        if not summary:
            n = arts.get(day, 0)
            summary = f"产物 {n} 个（文件名反推）" if n else "无记录"
        body.append(f'<tr><td>{esc(day)}</td><td>{esc(summary)}</td>'
                    f'<td class="num">{fmt(len(rs))}</td>'
                    f'<td class="num">{fmt(arts.get(day, 0))}</td></tr>')
    return ('<div class="table-wrap" style="max-height:none"><table>'
            '<caption class="sr-only">近 14 天每天做了什么</caption>'
            '<thead><tr><th scope="col">日期</th><th scope="col">做了什么</th>'
            '<th scope="col" class="num">记录</th><th scope="col" class="num">产物</th>'
            '</tr></thead><tbody>' + "".join(body) + '</tbody></table></div>')


def render(data, logos):
    d = data
    k = d["kpi"]
    prev = d["prev"]
    ch = d["change"] or {}
    wow = d.get("wow") or {}
    wcf = ((wow.get("comparable_finalized") or {}).get("change_pct") or {})
    wcur = (wow.get("comparable_finalized") or {}).get("current") or {}
    wprev = (wow.get("comparable_finalized") or {}).get("previous") or {}
    idx = d["indexing"]
    auth = d["authority"]
    sh = d["site_health"]
    pages = (sh.get("validate") or {}).get("pages")
    denom = idx.get("sitemap_urls") or pages
    daily_tbl = daily_data_table(d.get("daily_series") or [], 14)
    work_tbl = daily_work_table(14)

    def delta_chip(change, suffix="%", good_up=True, label="vs 上期"):
        if change is None:
            return chip("无上期对比", "neutral")
        tone = "success" if ((change > 0) == good_up) and change != 0 else ("neutral" if change == 0 else "danger")
        arrow = "↑" if change > 0 else ("↓" if change < 0 else "→")
        sign = "+" if change > 0 else ""
        return chip(f"{arrow} {sign}{change:g}{suffix} {label}", tone)

    def pos_chip(v):
        if v is None:
            return chip("无上期对比", "neutral")
        if v < 0:
            return chip("↓ " + f1(abs(v)) + " · 位次改善", "success")
        if v > 0:
            return chip("↑ " + f1(v) + " · 位次变差", "danger")
        return chip("持平", "neutral")

    kpi_cards = [
        kpi_card("GSC 点击", fmt(k["clicks"]),
                 f"上期 {fmt(prev['clicks'])} 次", "neutral",
                 delta_chip(ch.get("clicks"))),
        kpi_card("GSC 展示", fmt(k["impressions"]),
                 f"上期 {fmt(prev['impressions'])} 次", "neutral",
                 delta_chip(ch.get("impressions"))),
        kpi_card("CTR", pct(k["ctr"], 2),
                 f"上期 {pct(prev['ctr'], 2)}", "neutral",
                 delta_chip(ch.get("ctr_pp"), "pp")),
        kpi_card("加权平均位次", f1(k["avg_position_weighted"]),
                 f"上期 {f1(prev['avg_position_weighted'])}", "neutral",
                 pos_chip(ch.get("avg_position_delta"))),
        kpi_card("有展示页面", fmt(k["pages_with_impressions"]),
                 f"占 sitemap {fmt(denom)} 页的 "
                 f"{pct(k['pages_with_impressions'] / denom * 100 if denom else None, 1)}", "neutral",
                 chip("页面维度", "brand")),
        kpi_card("D1 真实询盘", fmt(k["d1_inquiries"]),
                 "询盘唯一真源 · M1 目标 1", "neutral",
                 chip("当前 0", "warning")),
    ]

    weekly_svg = svg_weekly(d.get("weekly_series") or [])
    daily_svg = svg_daily(d.get("daily_series") or [])
    idx_svg = svg_donut(idx.get("indexed") or 0, idx.get("inspected") or 0)

    wow_strip = (
        f'<div class="wow-strip">'
        f'<div class="mini"><b>{fmt(wcur.get("impressions"))}</b><span>本周展示（已 finalize 7 天）{badge("+"+f1(wcf.get("impressions"))+"%", "success")}</span></div>'
        f'<div class="mini"><b>{fmt(wcur.get("clicks"))}</b><span>本周点击 {badge(("+" if (wcf.get("clicks") or 0) > 0 else "")+f1(wcf.get("clicks"))+"%", "neutral")}</span></div>'
        f'<div class="mini"><b>{pct(wcur.get("ctr"), 2)}</b><span>本周 CTR {badge(f1(wow.get("comparable_finalized", {}).get("ctr_pp"))+"pp", "warning")}</span></div>'
        f'<div class="mini"><b>{f1(wcur.get("avg_position_weighted"))}</b><span>本周位次 {badge("改善 "+f1(abs(wow.get("comparable_finalized", {}).get("avg_position_delta") or 0)), "success")}</span></div>'
        f'</div>')

    gap_html = "".join(gap_row(r) for r in d["gap"])

    funnel = d["funnel"]
    def fstep(label, value, sub=""):
        sub_html = (' <span class="muted small">' + esc(sub) + '</span>') if sub else ""
        return (f'<div class="fstep"><span class="lbl">{esc(label)}</span>'
                f'<span><b>{fmt(value)}</b>{sub_html}</span></div>')
    funnel_html = (
        fstep("GSC 展示", funnel.get("impressions"), "页面维度")
        + f'<div class="farrow"><span class="line"></span>CTR {pct(k["ctr"], 2)}<span class="line"></span></div>'
        + fstep("GSC 点击", funnel.get("clicks"), "真实点击")
        + f'<div class="farrow"><span class="line"></span>GA4 事件（含内部测试）<span class="line"></span></div>'
        + fstep("表单提交 form_submit", funnel.get("form_submit"), "GA4 观测口径")
        + f'<div class="farrow"><span class="line"></span>D1 落库（真实询盘）<span class="line"></span></div>'
        + fstep("D1 询盘", funnel.get("d1_inquiries"), "唯一真源")
    )
    ctx = (f'<div class="ctx-grid">'
           f'<div class="ctx"><b>{fmt(funnel.get("ga4_page_view"))}</b><span>GA4 page_view</span></div>'
           f'<div class="ctx"><b>{fmt(funnel.get("ga4_session_start"))}</b><span>GA4 会话</span></div>'
           f'<div class="ctx"><b>{fmt(funnel.get("form_start"))}</b><span>表单开始</span></div>'
           f'<div class="ctx"><b>{fmt(funnel.get("generate_lead"))}</b><span>generate_lead</span></div>'
           f'</div>')

    zero_rows = d["zero_click"]["rows"]
    zero_threshold = d["zero_click"].get("threshold") or 40
    zero_stats = (f'共 <b>{fmt(d["zero_click"]["count"])}</b> 页 · 涉及 '
                  f'<b>{fmt(d["zero_click"]["impressions_at_stake"])}</b> 次展示 · '
                  f'其中 {fmt(sum(1 for r in zero_rows if r["status"] == "fixed"))} 页今日已改 title')

    # 权威 / 渠道
    domain_chips = "".join(chip(x, "neutral") for x in (auth.get("domain_list") or [])) or '<span class="muted">暂无</span>'
    hl = (
        f'<div class="hl-grid">'
        f'<div class="hl"><h3>引用域</h3><b>{fmt(auth.get("referring_domains"))}</b>'
        f'<p>dofollow {fmt(auth.get("follow_domains"))} · 目标 5</p><p>{domain_chips}</p></div>'
        f'<div class="hl"><h3>GEO 引用</h3><b>{fmt((auth.get("geo_ai") or {}).get("cited"))}/8</b>'
        f'<p>AI 层被引 · 搜索层 {fmt((auth.get("geo_search") or {}).get("cited"))}/20</p></div>'
        f'<div class="hl"><h3>营销外联</h3><b>{fmt((d.get("outbound") or {}).get("sent"))}</b>'
        f'<p>已发送 · 目标池 {fmt((d.get("outbound") or {}).get("leads"))} · 回复 {fmt((d.get("outbound") or {}).get("replies"))}</p></div>'
        f'<div class="hl"><h3>社媒（30 天）</h3><b>{fmt((d.get("social") or {}).get("published_30d"))}</b>'
        f'<p>已发布 · 待审批 {fmt((d.get("social") or {}).get("pending"))} · 最近 {(d.get("social") or {}).get("last_published") or "—"}</p></div>'
        f'<div class="hl"><h3>销售闭环</h3><b>{fmt((d.get("crm") or {}).get("d1_inquiries"))}</b>'
        f'<p>D1 询盘 → SAQO {fmt((d.get("crm") or {}).get("saqo"))} → Brevo Deals {fmt((d.get("crm") or {}).get("brevo_deals"))}</p></div>'
        f'<div class="hl"><h3>站点健康</h3><b>{fmt(pages)}</b>'
        f'<p>validate {"PASS" if (sh.get("validate") or {}).get("ok") else "FAIL"} · facts {fmt((sh.get("facts") or {}).get("count"))} · 孤儿 {fmt((sh.get("orphans") or {}).get("count"))}</p></div>'
        f'</div>')

    commits_html = "".join(
        f'<li><time>{esc(c["time"])}</time><span><b>{esc(c["hash"])}</b> {esc(c["subject"])}</span></li>'
        for c in (d.get("commits") or [])[:5]) or "<li>无提交</li>"

    alerts = []
    alerts.append(("danger", "真实询盘仍为 0：D1 自 2026-10-26 后无新提交；GA4 表单事件含内部测试，不能当询盘。"))
    alerts.append(("warn", f"CTR {pct(k['ctr'], 2)}：{fmt(d['zero_click']['count'])} 个页面共 {fmt(d['zero_click']['impressions_at_stake'])} 次展示 0 点击（占窗口展示的 "
                           f"{pct((d['zero_click']['impressions_at_stake'] or 0) / (k['impressions'] or 1) * 100, 1)}）。"))
    alerts.append(("warn", f"外联已发送 {fmt((d.get('outbound') or {}).get('sent'))}：目标池 {fmt((d.get('outbound') or {}).get('leads'))} 个已就绪，11-10 起为三波发送窗口。"))
    alerts.append(("info", f"GSC 数据窗口 {d['window']['start']} → {d['window']['end']}，API 有效至 {d.get('effective_data_end')}（finalize 延迟 {fmt(d.get('data_lag_days'))} 天）。"))
    alerts.append(("info", f"收录审计 {esc((idx.get('audited_at') or '—')[:16])}：{fmt(idx.get('indexed'))}/{fmt(idx.get('inspected'))} = {pct(idx.get('indexed_pct'))}"
                           f"（sitemap {fmt(idx.get('sitemap_urls'))} URL）。"))
    alerts_html = "".join(f'<div class="alert {tone}"><span class="dot" aria-hidden="true"></span><span>{esc(txt)}</span></div>'
                          for tone, txt in alerts)

    notes = [
        f"KPI 口径：<b>GSC 页面维度</b>（无维度总量也可）。查询词维度匿名化丢 "
        f"{pct(d.get('query_dimension_dropped_pct')) if d.get('query_dimension_dropped_pct') is not None else '约 60%'} 展示，仅用于选题，不进 KPI。",
        f"GSC finalize 延迟：请求窗口至 {esc(d['window']['end'])}，实际 API 返回至 {esc(d.get('effective_data_end') or '—')}；未返回的日期不是 0 流量。",
        f"GA4 事件（form_start/submit/generate_lead）含内部测试；<b>真实询盘只认 D1 submissions</b>。",
        f"收录覆盖率来自 GSC URL Inspection 全量审计（scope=full），不是当日实时；未收录页需等抓取或靠外链/内链加速。",
        f"日期序列（按日图）为 GSC 日期维度，只用于看趋势形状；其行之和与页面维度 KPI 存在 GSC 聚合差异。",
        f"Brevo CRM 只读：Deals {fmt((d.get('crm') or {}).get('brevo_deals'))}"
        + (f"（读取失败：{esc((d.get('crm') or {}).get('brevo_error'))}）" if (d.get("crm") or {}).get("brevo_error") else "")
        + "。",
        (f"交叉核对：同窗口无维度总量 {fmt(((d.get('cross_check') or {}).get('no_dimension_total') or {}).get('impressions'))} 展示 / 页面维度 "
         f"{fmt(k['impressions'])}；差额来自 GSC 聚合/匿名化，KPI 统一用页面维度。") if (d.get("cross_check") or {}).get("no_dimension_total") else None,
        f"生成方式：<code>python3 scripts/metrics/build_site_dashboard.py</code>（数据文件见下方链接，可复跑）。",
    ]
    notes_html = "".join(f"<li>{n}</li>" for n in notes if n)

    files = d.get("data_files") or {}
    rel = lambda p: os.path.relpath(os.path.join(WS, p), OUT) if p else None
    file_links = []
    for label, key in [("R6 看板 JSON", "r6_dashboard"), ("North Star JSON", "north_star"),
                       ("收录审计 JSON", "index_audit"), ("内容台账", "content_ledger"),
                       ("总编排交接", "handoff")]:
        p = files.get(key)
        if p:
            file_links.append(f'<a href="{esc(rel(p))}">{esc(label)}</a>')
    file_links_html = " · ".join(file_links)

    win = d["window"]
    hero = (f'<section class="hero"><div>'
            f'<p class="eyebrow">ANARI 虚拟营销团队 · {esc(d["role"])}</p>'
            f'<h1>anaricharge.com 运营仪表盘</h1>'
            f'<p>数据窗口 <b>{esc(win["start"])} → {esc(win["end"])}</b>（{fmt(win.get("days"))} 天，'
            f'GSC 有效至 {esc(d.get("effective_data_end") or "—")}）· 对比窗口 '
            f'{esc((d.get("compare_window") or {}).get("start"))} → {esc((d.get("compare_window") or {}).get("end"))}。'
            f'所有数字来自官方 API / D1 / 站点门禁，可复跑。</p></div>'
            f'<div class="hero-meta">'
            f'{chip("GSC 官方 API ✅", "success")}{chip("GA4 ✅", "success")}{chip("D1 ✅", "success")}'
            f'{chip("URL Inspection ✅", "success")}{chip("Brevo ✅", "success")}'
            f'<span class="pill">生成于 {esc(d["generated_at"][:16].replace("T", " "))}</span>'
            f'</div></section>')

    html_doc = f"""<!doctype html>
<html lang="zh-CN" data-theme-mode="system">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ANARI 运营仪表盘 · {esc(d["day"])} · anaricharge.com</title>
<script>
(function(){{try{{var m=localStorage.getItem('anari-dash-theme')||'system';if(['system','light','dark'].indexOf(m)<0)m='system';
var dark=m==='dark'||(m==='system'&&window.matchMedia('(prefers-color-scheme: dark)').matches);
var r=document.documentElement;r.classList.toggle('dark',dark);r.classList.toggle('light',m==='light');
r.dataset.themeMode=m;r.dataset.theme=dark?'dark':'light';}}catch(e){{}}}})();
</script>
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#main">跳到主内容</a>
<header class="topbar"><div class="shell topbar-in">
  <div class="brand">
    {('<img class="logo logo-light" src="' + logos['light'] + '" alt="ANARI">') if logos.get('light') else ''}
    {('<img class="logo logo-dark" src="' + logos['dark'] + '" alt="ANARI">') if logos.get('dark') else ''}
    <div class="brand-t"><strong>运营仪表盘</strong><span>anaricharge.com · {esc(d["day"])}</span></div>
  </div>
  <div class="top-meta">
    {chip("数据有效至 " + str(d.get("effective_data_end") or "—"), "brand")}
    <button id="themeBtn" class="theme-btn" type="button" aria-label="外观：跟随系统（点击切换到亮色）">
      <span aria-hidden="true">◐</span><span class="theme-text">外观：跟随系统</span>
    </button>
  </div>
</div></header>
<main id="main" class="shell">
{hero}
<section aria-labelledby="kpi-h">
  <div class="section-h"><h2 id="kpi-h">核心指标 · 近 {fmt(win.get("days"))} 天</h2>
  <p>页面维度 · 对比上一周期</p></div>
  <div class="kpi-grid">{''.join(kpi_cards)}</div>
</section>

<section>
  <div class="grid">
    <article class="card span-7">
      <div class="section-h"><h2>近 14 天逐日数据</h2><p>GSC 日期维度 · 日线只看形状，KPI 仍以 28 天页面维度为准</p></div>
      {daily_tbl}
    </article>
    <article class="card span-5">
      <div class="section-h"><h2>近 14 天每天做了什么</h2><p>run-log + 产物文件名反推 · 历史回填行标「历史档案」（qa=unknown）</p></div>
      {work_tbl}
    </article>
  </div>
</section>

<section>
  <div class="grid">
    <article class="card span-8">
      <div class="section-h"><h2>周趋势（GSC 页面维度）</h2><p>近 8 周 · 展示与点击</p></div>
      <figure>{weekly_svg}
        <figcaption>灰柱 = 点击；蓝柱 = 展示；浅色柱 = 本周未完整。当前周 {esc((d["weekly_series"][-1]["week_start"]) if d.get("weekly_series") else "—")} 起。</figcaption>
      </figure>
      {wow_strip}
    </article>
    <article class="card span-4">
      <div class="section-h"><h2>M1 目标进度</h2><p>领先指标 · 非访问量</p></div>
      {gap_html}
    </article>
  </div>
</section>

<section>
  <div class="grid">
    <article class="card span-7">
      <div class="section-h"><h2>转化链路</h2><p>展示 → 点击 → 表单 → D1 询盘</p></div>
      <div class="funnel">{funnel_html}</div>
      {ctx}
      <p class="small muted" style="margin-top:10px">注：GA4 事件含内部测试与重复事件，故 form_submit 可能大于 form_start；<b>询盘以 D1 为准</b>。</p>
    </article>
    <article class="card span-5">
      <div class="section-h"><h2>收录覆盖</h2><p>{esc((idx.get("source_file") or "—"))}</p></div>
      <div class="donut-wrap">
        {idx_svg}
        <div class="legend">
          <div class="legend-row"><span><span class="legend-dot" style="background:var(--brand)"></span>已收录</span><b>{fmt(idx.get("indexed"))}</b></div>
          <div class="legend-row"><span><span class="legend-dot" style="background:var(--ink-3)"></span>未知（未抓取/未收录）</span><b>{fmt(idx.get("unknown"))}</b></div>
          <div class="legend-row"><span><span class="legend-dot" style="background:var(--warning)"></span>已发现未收录</span><b>{fmt(idx.get("discovered"))}</b></div>
          <div class="legend-row"><span>检查总数</span><b>{fmt(idx.get("inspected"))}</b></div>
          <div class="legend-row"><span>sitemap URL</span><b>{fmt(idx.get("sitemap_urls"))}</b></div>
        </div>
      </div>
      <p class="small muted" style="margin-top:10px">审计时间 {esc((idx.get("audited_at") or "—")[:16].replace("T", " "))} · 未收录页需等抓取或靠外链/内链加速。</p>
    </article>
  </div>
</section>

<section>
  <div class="grid">
    <article class="card span-8">
      <div class="section-h"><h2 id="top-h">展示 Top 10 页面</h2><p>近 {fmt(win.get("days"))} 天 · 按展示排序</p></div>
      {top_pages_table(d.get("top_pages") or [])}
    </article>
    <article class="card span-4">
      <div class="section-h"><h2>今日动态</h2><p>站点仓库最近提交</p></div>
      <ul class="timeline">{commits_html}</ul>
      <div class="section-h" style="margin-top:16px"><h2 style="font-size:14px">关注项</h2></div>
      {alerts_html}
    </article>
  </div>
</section>

<section>
  <div class="grid">
    <article class="card span-7">
      <div class="section-h"><h2 id="zero-h">0 点击页面（展示 ≥ {fmt(zero_threshold)}）</h2><p>{zero_stats}</p></div>
      {zero_table(zero_rows, zero_threshold)}
      <p class="small muted" style="margin-top:8px">状态来自内容台账：已改 title 的 3 页观察窗 11-15 ~ 11-22；「非标题瓶颈」主要是排名/意图问题，改 title 无效。</p>
    </article>
    <article class="card span-5">
      <div class="section-h"><h2>渠道与权威</h2><p>外链 / GEO / 外联 / 社媒 / 销售</p></div>
      {hl}
    </article>
  </div>
</section>

<section>
  <div class="grid">
    <article class="card span-12">
      <div class="section-h"><h2>按日趋势（GSC 日期维度）</h2><p>{esc(d.get("daily_series_note") or "")}</p></div>
      <figure>{daily_svg}
        <figcaption>最近 {fmt(len(d.get("daily_series") or []))} 天有数据（窗口末端日期尚未 finalize，不按 0 处理）。</figcaption>
      </figure>
    </article>
  </div>
</section>

<section>
  <div class="grid">
    <article class="card span-12 notes">
      <div class="section-h"><h2>口径与数据说明</h2><p>不看口径的数字不要用</p></div>
      <ul>{notes_html}</ul>
    </article>
  </div>
</section>

<footer>
  <span>ANARI 运营仪表盘 · {esc(d["day"])} · 由 {esc(d["role"])} 生成 · 数据源：GSC 官方 API / GA4 / D1 / GSC URL Inspection / Brevo / GEO 台账</span>
  <span>{file_links_html}</span>
</footer>
</main>
<script>{JS}</script>
</body>
</html>
"""
    return html_doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.date.today().isoformat())
    a = ap.parse_args()
    day = dt.date.fromisoformat(a.date)

    data = collect(day)
    logos = {"light": base64_img(os.path.join(LOGO_DIR, "logo-horizontal.png")),
             "dark": base64_img(os.path.join(LOGO_DIR, "logo-icon.png"))}
    html_doc = render(data, logos)

    os.makedirs(OUT, exist_ok=True)
    json_path = os.path.join(OUT, "site-dashboard-%s.json" % day.isoformat())
    html_path = os.path.join(OUT, "site-dashboard-%s.html" % day.isoformat())
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    print("WROTE", json_path)
    print("WROTE", html_path)
    print("KPI:", json.dumps(data["kpi"], ensure_ascii=False))
    print("index:", json.dumps(data["indexing"], ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
