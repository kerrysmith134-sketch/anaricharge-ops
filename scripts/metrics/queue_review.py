#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""queue_review.py — 内容队列复盘与观察窗回归（W8 队列的下游检查器）

用途
  给「W8 关键词策略」产出的 10 天选题队列做**上线后复盘**：逐条对比上线前基线（内容台账）
  与当前 GSC 页面/查询读数，判断「成功 / 未达标 / 观察中 / 无数据」，并输出下一步动作。
  队列清空后、或任意观察窗到期日，都可以直接复跑。

数据源（全部只读，不写站点）
  · 队列：08-execution/content/content-queue-*.json（默认取最新）
  · 基线：08-execution/content/content-ledger.json（每条 publish 记录的 before_metrics）
  · 现读数：GSC 官方 API（页面维度 + 查询维度，默认最近 28 天，与 W8 基线同窗口长度）
  · 线上状态：页面 HTTP、.md 镜像 HTTP、线上 sitemap 是否在列

用法
  python3 scripts/metrics/queue_review.py                     # 最新队列，默认 asof=今天
  python3 scripts/metrics/queue_review.py --queue 08-execution/content/content-queue-2026-11-08.json
  python3 scripts/metrics/queue_review.py --asof 2026-11-23   # 模拟观察窗到期日（数据仍是真实数据）
  python3 scripts/metrics/queue_review.py --no-http           # 跳过线上探活（离线跑）
  python3 scripts/metrics/queue_review.py --json <path> --md <path>

判定口径（写死在代码里，避免每次凭感觉）
  · 观察窗：优先取台账 observe_until；队列项无记录时按 publish+28 天
  · 目标：从 target_pos 文本解析第一个 p<数字> 作为位次目标；从 target 文本解析 CTR ≥x%；
    刷新类(refresh_*)若未写 CTR 目标，默认 2.0%（W20 的 CTR 修复判据）
  · success = 已声明目标全部达成；observing = 未到观察窗截止日；no_data = 发布≥3 天仍 0 展示
  · 查询维度仅作辅助（低流量站匿名化会丢约 60% 展示，AGENTS §3），**不得当 KPI**
"""

import argparse
import datetime as dt
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))  # scripts/ 以便 import gsc_pull

from gsc_pull import access_token, gsc, shape  # noqa: E402

BASE = "https://www.anaricharge.com"
CONTENT = os.path.join(WS, "08-execution", "content")
SITEMAP_URL = BASE + "/sitemap.xml"


def latest_queue():
    files = sorted(glob.glob(os.path.join(CONTENT, "content-queue-*.json")))
    if not files:
        raise SystemExit("找不到队列文件 content-queue-*.json")
    return files[-1]


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_date(s):
    return dt.date.fromisoformat(s[:10]) if s else None


def parse_targets(queue_item, ledger_entry):
    """从文本里解析目标：位次取第一个 p<数字>，CTR 取 'CTR ≥x%'；刷新类缺省 CTR 2%。"""
    text = " ".join(str(x) for x in [
        (queue_item or {}).get("target_pos", ""),
        (ledger_entry or {}).get("target_pos", ""),
    ])
    pos = None
    m = re.search(r"p\s*(\d+(?:\.\d+)?)", text, re.I)
    if m:
        pos = float(m.group(1))
    ctr = None
    m = re.search(r"CTR\s*[≥>=]+\s*(\d+(?:\.\d+)?)\s*%", text, re.I)
    if m:
        ctr = float(m.group(1))
    task = (queue_item or {}).get("task_type", "") or (ledger_entry or {}).get("task_type", "")
    if ctr is None and task.startswith("refresh"):
        ctr = 2.0
    return {"position": pos, "ctr_pct": ctr}


def http_status(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (queue-review)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:  # noqa: BLE001 网络失败如实标记
        return "ERR:%s" % type(e).__name__


def fetch_sitemap_urls():
    try:
        req = urllib.request.Request(SITEMAP_URL, headers={"User-Agent": "Mozilla/5.0 (queue-review)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            xml = r.read().decode("utf-8", "replace")
        return set(re.findall(r"<loc>(.*?)</loc>", xml))
    except Exception:  # noqa: BLE001
        return None


def page_row(pages, slug):
    target = BASE + slug
    for p in pages:
        if p["page"].rstrip("/") == target.rstrip("/"):
            return p
    return None


def query_row(queries, kw):
    """查询维度匹配：主词整串优先，其次取主词里较长的 3 个词片段做包含匹配。"""
    if not kw:
        return None
    k = kw.lower().strip()
    exact = [q for q in queries if q["query"].lower().strip() == k]
    if exact:
        return sorted(exact, key=lambda q: -q["impressions"])[0]
    tokens = [t for t in re.split(r"[^a-z0-9]+", k) if len(t) >= 3]
    if not tokens:
        return None
    cands = [q for q in queries if sum(1 for t in tokens if t in q["query"].lower()) >= max(2, len(tokens) - 1)]
    if not cands:
        return None
    # 取展示最高且与主词最接近的一条
    return sorted(cands, key=lambda q: (-q["impressions"], abs(len(q["query"]) - len(k))))[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", default=None, help="队列 JSON 路径（默认最新）")
    ap.add_argument("--asof", default=None, help="复盘基准日 YYYY-MM-DD（默认今天，北京时间口径用本机日期）")
    ap.add_argument("--days", type=int, default=28, help="GSC 现读数窗口天数（默认 28，与 W8 基线同长）")
    ap.add_argument("--json", dest="json_out", default=None)
    ap.add_argument("--md", dest="md_out", default=None)
    ap.add_argument("--no-http", action="store_true", help="跳过线上探活")
    a = ap.parse_args()

    asof = parse_date(a.asof) if a.asof else dt.date.today()
    gsc_end = asof - dt.timedelta(days=1)          # GSC 通常 T+2，取到昨天
    gsc_start = gsc_end - dt.timedelta(days=a.days - 1)
    queue_path = a.queue or latest_queue()
    queue = load_json(queue_path)
    ledger = load_json(os.path.join(CONTENT, "content-ledger.json"))
    led_by_slug = {}
    for e in ledger.get("entries", []):
        led_by_slug.setdefault(e.get("slug"), []).append(e)

    print(f"队列：{queue_path}")
    print(f"GSC 窗口：{gsc_start} ~ {gsc_end}（{a.days} 天）· asof={asof}")

    try:
        at = access_token()
        pages = shape(gsc(["page"], gsc_start.isoformat(), gsc_end.isoformat(), at=at), ["page"])
        queries = shape(gsc(["query"], gsc_start.isoformat(), gsc_end.isoformat(), at=at), ["query"])
        gsc_ok = True
    except Exception as e:  # noqa: BLE001
        pages, queries, gsc_ok = [], [], False
        print(f"⚠ GSC 拉取失败：{type(e).__name__}: {e} —— 报告将标「数据不可用」")

    sitemap_urls = None if a.no_http else fetch_sitemap_urls()

    items = []
    for q in queue.get("items", []):
        slug = q.get("slug", "")
        led = (led_by_slug.get(slug) or [None])[-1]
        publish = (parse_date(led.get("published_at")) if led else None) or parse_date(q.get("publish_date"))
        observe_until = parse_date(led.get("observe_until")) if led else None
        if observe_until is None and publish:
            observe_until = publish + dt.timedelta(days=28)

        before = ((led or {}).get("before_metrics") or {})
        now_row = page_row(pages, slug) if gsc_ok else None
        now = {
            "impressions": (now_row or {}).get("impressions", 0),
            "clicks": (now_row or {}).get("clicks", 0),
            "ctr_pct": (now_row or {}).get("ctr", 0.0),
            "position": (now_row or {}).get("position"),
        }
        qr = query_row(queries, q.get("main_kw")) if gsc_ok else None
        targets = parse_targets(q, led)

        days_since = (asof - publish).days if publish else None
        days_left = (observe_until - asof).days if observe_until else None

        ctr_ok = targets["ctr_pct"] is not None and now["ctr_pct"] >= targets["ctr_pct"]
        pos_ok = targets["position"] is not None and now["position"] is not None and now["position"] <= targets["position"]

        LOW = 30  # 展示 <30 的达标/不达标都不下结论（低流量站小样本抖动）
        if not gsc_ok:
            status = "gsc_unavailable"
        elif days_since is not None and days_since >= 3 and now["impressions"] == 0:
            status = "no_data"
        elif days_left is not None and days_left > 0:
            status = "success_early" if (ctr_ok or pos_ok) else "observing"
        else:
            status = "success" if (ctr_ok or pos_ok) else "below_target"

        low_sample = (gsc_ok and now["impressions"] < LOW and status in ("success", "success_early", "below_target"))
        if low_sample:
            status = "inconclusive_low_sample"

        if status in ("observing", "success_early"):
            nxt = f"继续观察至 {(observe_until or asof).isoformat()}；到期复跑本脚本"
        elif status == "no_data":
            nxt = "发布≥3天仍0展示：查 GSC URL 检查/索引状态；补内链 + IndexNow；14 天仍0曝光则加内链并复核"
        elif status == "below_target":
            nxt = "未达目标：刷新类只换 meta 不再动 title（W20 §6）；新篇查收录与 AIO 截流"
        elif status == "inconclusive_low_sample":
            nxt = "样本<30展示，不下结论：等展示累积到30+后复跑（到期日仍无数据则按 W20 处理）"
        elif status == "success":
            nxt = "达标：写回复盘结论（可复用角度/标题/模板），并考虑同簇扩写"
        else:
            nxt = "GSC 不可用：稍后重跑"

        evidence = {}
        if not a.no_http:
            evidence["http"] = http_status(BASE + slug)
            evidence["md_http"] = http_status(BASE + slug + ".md")
            evidence["in_sitemap"] = (None if sitemap_urls is None else (BASE + slug) in {u.rstrip("/") for u in sitemap_urls} or (BASE + slug) in sitemap_urls)

        items.append({
            "id": q.get("id"), "slug": slug, "priority": q.get("priority"),
            "task_type": q.get("task_type"), "main_kw": q.get("main_kw"),
            "published_at": publish.isoformat() if publish else None,
            "observe_until": observe_until.isoformat() if observe_until else None,
            "days_since_publish": days_since, "days_left": days_left,
            "targets": targets, "status": status, "low_sample": bool(low_sample),
            "before": {"impressions": before.get("impressions"), "clicks": before.get("clicks"),
                       "ctr_pct": before.get("ctr_pct", before.get("ctr")), "position": before.get("position")} if before else None,
            "now": now,
            "delta": {
                "impressions": (now["impressions"] - before.get("impressions", 0)) if before.get("impressions") is not None else None,
                "clicks": (now["clicks"] - before.get("clicks", 0)) if before.get("clicks") is not None else None,
                "position": (round(before.get("position") - now["position"], 1)
                             if before.get("position") is not None and now["position"] is not None else None),
            },
            "query_check": ({"query": qr["query"], "impressions": qr["impressions"],
                             "clicks": qr["clicks"], "position": round(qr["position"], 1)} if qr else None),
            "goals": {"ctr_ok": bool(ctr_ok), "position_ok": bool(pos_ok)},
            "next_action": nxt, "evidence": evidence,
        })

    checkpoints = {}
    for i in items:
        if i.get("observe_until"):
            checkpoints.setdefault(i["observe_until"], []).append(i["id"])

    summary = {
        "items": len(items),
        "by_status": {},
        "total_now": {
            "impressions": sum(i["now"]["impressions"] for i in items),
            "clicks": sum(i["now"]["clicks"] for i in items),
        },
    }
    for i in items:
        summary["by_status"][i["status"]] = summary["by_status"].get(i["status"], 0) + 1
    summary["total_now"]["ctr_pct"] = round(
        summary["total_now"]["clicks"] / summary["total_now"]["impressions"] * 100, 2
    ) if summary["total_now"]["impressions"] else 0.0

    report = {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "asof": asof.isoformat(),
        "queue": os.path.relpath(queue_path, WS),
        "gsc": {"available": gsc_ok, "start": gsc_start.isoformat(), "end": gsc_end.isoformat(), "days": a.days},
        "caveats": [
            "展示<30 时即便命中目标也标 inconclusive_low_sample：低流量站小样本的位次/CTR 会剧烈抖动，不制造结论",
            "GSC 数据通常 T+2：asof 当天与前一天的数据可能缺失或被回填",
            "现读数固定取最近 28 天，对新发布页会包含发布前数据；发布 7 天内的读数只作参考，不当结论",
            "before 基线窗口（台账记录）与现读数窗口起点可能相差 1–2 天，delta 为近似值；判断以「目标是否达成」为准",
            "查询维度在低流量站会被匿名化（丢约 60% 展示与点击），只作辅助，不作 KPI",
            "成功判据取「已声明目标任一达成」；观察窗内提前达标记为 success_early",
            "before 基线来自内容台账的 before_metrics；台账缺失时为 null",
        ],
        "summary": summary,
        "checkpoints": checkpoints,
        "items": items,
    }

    json_out = a.json_out or os.path.join(CONTENT, f"{asof.isoformat()}-queue-review.json")
    md_out = a.md_out or os.path.join(CONTENT, f"{asof.isoformat()}-queue-review.md")
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    lines = [
        f"# 内容队列复盘 · {asof.isoformat()}",
        "",
        f"- 队列：`{report['queue']}`",
        f"- GSC 窗口：{gsc_start} ~ {gsc_end}（{a.days} 天，{ '可用' if gsc_ok else '不可用' }）",
        f"- 汇总：{summary['items']} 条 · " + " · ".join(f"{k} {v}" for k, v in summary["by_status"].items()),
        f"- 队列页面现读数合计：{summary['total_now']['impressions']} 展示 / {summary['total_now']['clicks']} 点击 / CTR {summary['total_now']['ctr_pct']}%",
        "",
        "> 口径：查询维度只用于辅助（低流量站匿名化丢约 60% 展示，AGENTS §3）；before 基线来自内容台账；"
        "「成功」= 已声明目标（位次或 CTR）任一达成。",
        "",
        "| 项 | 发布日 | 观察窗 | 状态 | before（展示/点击/CTR/位次） | now（展示/点击/CTR/位次） | 位次变化 | 查询辅助 | 下一步 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i in items:
        b = i["before"] or {}
        n = i["now"]
        def fmt(m):
            if not m or m.get("impressions") is None and m.get("position") is None:
                return "—"
            pos = m.get("position")
            return f"{m.get('impressions', 0)}/{m.get('clicks', 0)}/{m.get('ctr_pct', 0)}%/{'—' if pos is None else round(pos,1)}"
        qc = i["query_check"]
        qtxt = f"{qc['query'][:28]} ({qc['position']})" if qc else "—"
        d = i["delta"]["position"]
        lines.append(
            f"| {i['id']} | {i['published_at'] or '—'} | 至 {i['observe_until'] or '—'} | **{i['status']}** | "
            f"{fmt(i['before'])} | {fmt(n)} | {'—' if d is None else (('+' if d >= 0 else '') + str(d))} | {qtxt} | {i['next_action']} |"
        )
    lines += ["", "## 逐条动作", ""]
    for i in items:
        ev = i["evidence"]
        evtxt = ("；".join(f"{k}={v}" for k, v in ev.items()) if ev else "未探活")
        lines.append(f"- **{i['id']} {i['slug']}** — {i['status']} · {evtxt} · {i['next_action']}")
    lines += ["", "## 下次复查", ""]
    for d in sorted(checkpoints):
        lines.append(f"- **{d}**：{', '.join(checkpoints[d])}")
    lines += ["", "## 方法说明", ""] + [f"- {c}" for c in report["caveats"]]
    with open(md_out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("\n".join(lines[:12]))
    print(f"\nWROTE {json_out}\nWROTE {md_out}")


if __name__ == "__main__":
    main()
