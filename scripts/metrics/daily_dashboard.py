#!/usr/bin/env python3
"""daily_dashboard.py — R6 每日看板数据文件生成器。

为什么单独一个脚本（而不是在 north_star.py 里加）：
  1) north_star.py 的窗口是「今天往前 N 天」，包含未 finalize 的今天；
     本文件按任务书用「昨天往前 N 天」，并把未 finalize 的日期显式标出来。
  2) 任务书要求的前 10 页、环比、周环比、0 点击页是固定字段，
     需要落成一份可被外部消费的 JSON（08-execution/daily/dashboard-<day>.json）。

口径（AGENTS.md §3 铁律）：
  - KPI 只用 GSC **页面维度** 或 **无维度总量**；
  - 查询词维度在低流量站会因匿名化丢约 60% 展示（本轮 1013/2824），
    只放进原始文件供选题参考，**不参与任何 KPI 计算**；
  - GSC 有 finalize 延迟（T+2~T+3），API 不返回的日期按「未 finalize」处理，
    绝不当作 0 流量；周环比因此同时给出「按任务书窗口」和「只用已 finalize 日」
    两个口径，判读以后者为准。

用法：
  # 先用官方脚本拉原始数据（任务书第 2 步）
  python3 scripts/gsc_pull.py --start <start> --end <end> ... \
      --out 08-execution/daily/gsc-YYYYMMDD.json
  # 再生成看板
  python3 scripts/metrics/daily_dashboard.py [--day YYYY-MM-DD] [--days 28]
"""
import argparse
import datetime as dt
import json
import os
import sys

WS = "/Users/kerrychu/anari-charge-website"
DAILY = os.path.join(WS, "08-execution", "daily")

sys.path.insert(0, os.path.join(WS, "scripts"))
import gsc_pull as gp  # noqa: E402


# ---------- 小工具 ----------

def _iso(d):
    return d.isoformat()


def totals(rows):
    """页面维度/无维度行 → 总量。位次按展示加权（简单平均会误读）。"""
    c = sum(int(r.get("clicks") or 0) for r in rows)
    i = sum(int(r.get("impressions") or 0) for r in rows)
    w = sum(float(r.get("position") or 0) * int(r.get("impressions") or 0) for r in rows)
    return {
        "clicks": c,
        "impressions": i,
        "ctr": round(c / i * 100, 2) if i else 0.0,
        "avg_position_weighted": round(w / i, 2) if i else 0.0,
        "pages": len(rows),
    }


def change(cur, prev):
    """总量变化率。prev 为 0 时返回 None（不编 -100%/无穷大）。"""
    if prev in (None, 0) or cur is None:
        return None
    return round((cur - prev) / prev * 100, 2)


def diff_stats(cur, prev):
    return {
        "clicks": change(cur.get("clicks"), prev.get("clicks")),
        "impressions": change(cur.get("impressions"), prev.get("impressions")),
        "ctr_pp": round((cur.get("ctr") or 0) - (prev.get("ctr") or 0), 2),
        "avg_position_delta": round((cur.get("avg_position_weighted") or 0)
                                    - (prev.get("avg_position_weighted") or 0), 2),
    }


def split_totals(t, label=None):
    d = dict(t)
    if label:
        d = {"window": label, **d}
    return d


def strip_none(obj):
    """递归删掉值为 None 的键（W19 §⑥：null 字段省略，历史踩坑 plan.md:230）。"""
    if isinstance(obj, dict):
        return {k: strip_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [strip_none(v) for v in obj]
    return obj


def monday_of(d):
    return d - dt.timedelta(days=d.weekday())


# ---------- 主流程 ----------


# ---------- cohort 拆分（2026-11-13 新增） ----------
# 为什么要它：页均展示从 16.9 掉到 13.8，不是内容变差，是**分母膨胀**——
# 页面数 188→272（+46%）而展示只 +18%。没有按页面龄分层，就看不出「新页没成熟」
# 和「老页在退步」的区别，容易把结构问题误判成质量问题。
REPO = os.path.join(WS, "06-site", "anari-new-site")
AGE_CACHE = os.path.join(WS, "ops", "page-age.json")


def _sitemap_paths():
    """本地 sitemap 的 URL 路径集合（不含域名，去掉尾斜杠）。"""
    import re
    p = os.path.join(REPO, "site", "sitemap.xml")
    if not os.path.exists(p):
        return []
    xml = open(p, encoding="utf-8").read()
    out = []
    for u in re.findall(r"<loc>(.*?)</loc>", xml):
        path = u.replace("https://www.anaricharge.com", "").replace("http://www.anaricharge.com", "")
        out.append(path.rstrip("/") or "/")
    return out


def _page_file(path):
    base = os.path.join(REPO, "site")
    p = path.strip("/")
    cands = ([os.path.join(base, p, "index.html"), os.path.join(base, p + ".html"),
              os.path.join(base, p)] if p else [os.path.join(base, "index.html")])
    for c in cands:
        if os.path.isfile(c):
            return os.path.relpath(c, REPO)
    return None


def _first_commit(relfile, cache):
    """页面首次提交日期（git --diff-filter=A）。结果进 ops/page-age.json 缓存，
    否则每天 272 次 git 调用会拖慢看板。"""
    if relfile in cache:
        return cache[relfile] or None
    import subprocess
    try:
        r = subprocess.run(["git", "-C", REPO, "log", "--diff-filter=A",
                            "--format=%ad", "--date=short", "--reverse", "--", relfile],
                           capture_output=True, text=True, timeout=20)
        val = (r.stdout.strip().split("\n")[0] if r.stdout.strip() else "") or ""
    except Exception:  # noqa: BLE001
        val = ""
    cache[relfile] = val
    return val or None


def cohort_block(gsc_pages, day, days, want_cache=False):
    """按页面龄分层：页数 / 展示 / 点击 / 页均展示（折算月）。

    - 页面龄 = 该页**首次提交**到看板日期的天数（不是 lastmod，避免改文案把老页算成新页）
    - 展示/点击来自 GSC 页面维度（同一窗口）
    - 页均展示按月折算：impr / pages * 30/days，与 KPI `A.impressions_per_page_month` 同口径
    """
    cache = {}
    try:
        cache = json.load(open(AGE_CACHE, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        cache = {}

    # GSC 页面 → 路径（归一化；http/https 都算同一页）
    impr, clicks = {}, {}
    for r in gsc_pages:
        u = (r.get("page") or "").replace("http://", "https://")
        key = u.replace("https://www.anaricharge.com", "")
        key = key.split("?")[0].split("#")[0].rstrip("/") or "/"
        impr[key] = impr.get(key, 0) + int(r.get("impressions") or 0)
        clicks[key] = clicks.get(key, 0) + int(r.get("clicks") or 0)

    buckets = {"<7d": [0, 0, 0], "7-13d": [0, 0, 0],
               "14-27d": [0, 0, 0], ">=28d": [0, 0, 0], "unknown-age": [0, 0, 0]}
    for path in _sitemap_paths():
        relfile = _page_file(path)
        fd = _first_commit(relfile, cache) if relfile else None
        if not fd:
            b = "unknown-age"
        else:
            try:
                age = (day - dt.date.fromisoformat(fd)).days
            except Exception:  # noqa: BLE001
                b = "unknown-age"
            else:
                b = ("<7d" if age < 7 else "7-13d" if age < 14
                     else "14-27d" if age < 28 else ">=28d")
        buckets[b][0] += 1
        buckets[b][1] += impr.get(path, 0)
        buckets[b][2] += clicks.get(path, 0)

    def _row(v):
        n, im, cl = v
        return {"pages": n, "impressions": im, "clicks": cl,
                "impr_per_page_month": round(im / n * 30 / days, 1) if n else None}

    rows = {k: _row(v) for k, v in buckets.items()}
    mature_n = rows[">=28d"]["pages"] + rows["14-27d"]["pages"]
    mature_im = rows[">=28d"]["impressions"] + rows["14-27d"]["impressions"]
    new_n = rows["<7d"]["pages"] + rows["7-13d"]["pages"]
    new_im = rows["<7d"]["impressions"] + rows["7-13d"]["impressions"]
    res = {
        "by_age": rows,
        "mature_ge14d": {"pages": mature_n, "impressions": mature_im,
                         "impr_per_page_month": round(mature_im / mature_n * 30 / days, 1)
                         if mature_n else None},
        "new_lt14d": {"pages": new_n, "impressions": new_im,
                      "impr_per_page_month": round(new_im / new_n * 30 / days, 1)
                      if new_n else None},
        "share_new_pages_pct": round(new_n / (mature_n + new_n) * 100, 1) if (mature_n + new_n) else None,
        "note": ("页龄取页面首次 git 提交日；页均展示按月折算，与 KPI 同口径。"
                 "新页占比越高，全站页均展示越低——这是分母效应，不是内容质量下降。"
                 "口径警告：页龄取「文件首次提交」，仓库重构/文件搬家会让老内容显得新（本轮 156 页 <7d，"
                 "但同期站点实际只净增 84 页），所以只看相对趋势，不看绝对页龄。"),
    }

    # 补充口径（更客观）：按「是否已收录」拆，不依赖 git 年龄
    try:
        import glob as _g
        cands = [x for x in _g.glob(os.path.join(WS, "08-execution", "tech", "index-coverage*.json"))
                 if "full" in os.path.basename(x)]
        if cands:
            latest = max(cands, key=os.path.getmtime)
            cov = json.load(open(latest, encoding="utf-8"))
            idx = {}
            for r in cov.get("rows") or []:
                u = (r.get("url") or "").replace("http://", "https://")
                key = u.replace("https://www.anaricharge.com", "").rstrip("/") or "/"
                idx[key] = (r.get("verdict") == "PASS")
            grp = {"indexed": [0, 0, 0], "not_indexed": [0, 0, 0]}
            for path in _sitemap_paths():
                g = "indexed" if idx.get(path) else "not_indexed"
                grp[g][0] += 1
                grp[g][1] += impr.get(path, 0)
                grp[g][2] += clicks.get(path, 0)
            res["by_index_status"] = {k: _row(v) for k, v in grp.items()}
            res["index_status_source"] = {
                "file": os.path.basename(latest),
                "audited_at": cov.get("generated_at"),
            }
    except Exception as e:  # noqa: BLE001
        res["by_index_status_note"] = "读取收录审计失败: %s" % str(e)[:120]

    if want_cache:
        return res, cache
    return res


def build(day, days, raw_path):
    end = day - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days - 1)
    c_end = start - dt.timedelta(days=1)
    c_start = c_end - dt.timedelta(days=days - 1)

    # 任务书字面的「本周 / 上周」= 请求窗口最后 7 天 vs 再前 7 天
    wk_end, wk_start = end, end - dt.timedelta(days=6)
    pw_end, pw_start = wk_start - dt.timedelta(days=1), wk_start - dt.timedelta(days=7)

    out = {
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "day": _iso(day),
        "role": "R6 数据分析师",
        "property": "sc-domain:anaricharge.com",
        "ga4": "G-MT63H5Q8EV",
        "window": {"start": _iso(start), "end": _iso(end), "days": days},
        "raw_gsc_file": os.path.relpath(raw_path, WS),
    }

    # --- 认证 ---
    try:
        at = gp.access_token()
    except Exception as e:  # noqa: BLE001
        out.update({
            "auth": {"gsc": "failed", "ga4": "unknown"},
            "error": "OAuth refresh_token 换 access_token 失败: %s: %s"
                     % (type(e).__name__, str(e)[:300]),
            "retry_suggestion": [
                "检查 ~/Documents/kimi/workspace/.secrets/gsc-oauth.json 是否仍存在且未过期（只读引用，不要复制/打印内容）",
                "确认 refresh_token 未被用户撤销、系统时间正确（OAuth 对时钟偏移敏感）",
                "网络/代理异常时先 curl -sI https://oauth2.googleapis.com/token 确认可达，再重跑 gsc_pull.py",
                "重试用尽仍失败：停止产出数字，人工在 GSC 后台导出 CSV 备查；不得用旧文件冒充新数据",
            ],
            "numbers_produced": False,
        })
        return out

    out["auth"] = {"gsc": "ok", "ga4": None}

    # --- 原始文件（gsc_pull.py 产物）；缺失/窗口不符则当场拉一次 ---
    raw = None
    raw_note = None
    if os.path.exists(raw_path):
        try:
            cand = json.load(open(raw_path, encoding="utf-8"))
            if ((cand.get("window") or {}).get("start") == _iso(start)
                    and (cand.get("window") or {}).get("end") == _iso(end)):
                raw = cand
            else:
                raw_note = "原始文件窗口 %s 与期望窗口不一致，已改用当场拉取" % (
                    cand.get("window"))
        except Exception as e:  # noqa: BLE001
            raw_note = "原始文件不可读（%s），已改用当场拉取" % str(e)[:120]
    else:
        raw_note = "原始文件不存在，已改用当场拉取"

    if raw is None:
        pages_rows = gp.gsc(["page"], _iso(start), _iso(end), 1000, at)
        raw = {
            "pages": gp.shape(pages_rows, ["page"]),
            "page_totals": totals(pages_rows),
            "pages_with_impressions": sum(1 for r in pages_rows if (r.get("impressions") or 0) > 0),
            "ga4_events": None,
        }
        try:
            rep = gp.ga4({
                "dateRanges": [{"startDate": _iso(start), "endDate": _iso(end)}],
                "metrics": [{"name": "eventCount"}],
                "dimensions": [{"name": "eventName"}],
                "limit": 100,
            }, at)
            raw["ga4_events"] = [
                {r["dimensionValues"][0]["value"]: int(r["metricValues"][0]["value"])}
                for r in rep.get("rows") or []
            ]
        except Exception as e:  # noqa: BLE001
            raw["ga4_error"] = "%s: %s" % (type(e).__name__, str(e)[:200])

    pages = raw.get("pages") or []
    page_totals = raw.get("page_totals") or totals(pages)

    # --- 数据 finalize 边界：按 date 维度看 API 最后返回的是哪天 ---
    effective_end = None
    daily_series = []
    try:
        drows = gp.gsc(["date"], _iso(start), _iso(end), 1000, at)
        for r in sorted(drows, key=lambda x: x["keys"][0]):
            daily_series.append({
                "date": r["keys"][0],
                "clicks": int(r.get("clicks") or 0),
                "impressions": int(r.get("impressions") or 0),
                "ctr": round(float(r.get("ctr") or 0) * 100, 2),
                "position": round(float(r.get("position") or 0), 1),
            })
        got = sorted(r["keys"][0] for r in drows if int(r.get("impressions") or 0) > 0)
        if got:
            effective_end = dt.date.fromisoformat(got[-1])
    except Exception as e:  # noqa: BLE001
        out.setdefault("errors", []).append("date 维度探测失败: %s" % str(e)[:160])
    if daily_series:
        out["daily_series"] = daily_series
        out["daily_series_note"] = (
            "GSC 日期维度，只用于看趋势形状。其行之和与页面维度 KPI 不完全相等"
            "（GSC 聚合/匿名化差异：日期维度行之和通常略低于页面维度总量），"
            "KPI 以页面维度为准。")

    # --- 主体 KPI（页面维度）---
    out.update({
        "clicks": page_totals.get("clicks"),
        "impressions": page_totals.get("impressions"),
        "ctr": page_totals.get("ctr"),
        "avg_position_weighted": page_totals.get("avg_position_weighted"),
        "pages_with_impressions": raw.get("pages_with_impressions"),
        "pages_scanned": len(pages),
        "top_pages": sorted(pages, key=lambda p: -(p.get("impressions") or 0))[:10],
    })
    # 向后兼容：W19 老字段名 position = 加权平均位次（W1 消费时两个名字都能用）
    out["position"] = out["avg_position_weighted"]
    if effective_end:
        out["effective_data_end"] = _iso(effective_end)
        lag = (end - effective_end).days
        out["data_lag_days"] = lag
        if lag > 0:
            out["data_lag_note"] = (
                "GSC 只返回至 %s（距请求窗口末端 %s 差 %d 天，属正常 finalize 延迟 T+2~T+3）。"
                "未返回的日期不是 0 流量，而是尚未 finalize；窗口末端 %d 天数据缺失，"
                "任何含这些日期的环比都会被低估。"
                % (_iso(effective_end), _iso(end), lag, lag))
    out["query_dimension_dropped_pct"] = None
    qt = raw.get("query_totals") or {}
    if qt.get("impressions") and page_totals.get("impressions"):
        dropped = 1 - qt["impressions"] / page_totals["impressions"]
        out["query_dimension_dropped_pct"] = round(dropped * 100, 1)
    out["basis"] = (
        "GSC 页面维度（page dimension）。查询词维度展示为 %s，页面维度为 %s"
        "（匿名化丢 %.0f%% 展示），按 AGENTS.md §3 只用于选题参考、不进 KPI。"
        % (qt.get("impressions"), page_totals.get("impressions"),
           (out["query_dimension_dropped_pct"] or 0)))

    # 交叉核对：同一窗口的无维度总量。两者都符合 §3 口径，但 GSC 聚合后数值不同。
    # 本看板统一用页面维度（与历史 north-star 序列一致），差额只作提示、不参与计算。
    try:
        nd = totals(gp.gsc([], _iso(start), _iso(end), 1000, at))
        out["cross_check"] = {
            "no_dimension_total": {"clicks": nd["clicks"],
                                   "impressions": nd["impressions"],
                                   "ctr": nd["ctr"],
                                   "avg_position_weighted": nd["avg_position_weighted"]},
            "page_dimension_total": {"clicks": page_totals.get("clicks"),
                                     "impressions": page_totals.get("impressions")},
            "note": ("GSC 同一窗口两种汇总方式数值不同（无维度 < 页面维度，疑似"
                     "查询匿名化在聚合层过滤所致）。本看板用页面维度：它不丢行、"
                     "且与历史 north-star 序列一致；差额不影响趋势方向判读。"),
        }
    except Exception as e:  # noqa: BLE001
        out.setdefault("errors", []).append("无维度总量核对失败: %s" % str(e)[:160])

    # --- GA4 ---
    raw_events = raw.get("ga4_events") or []
    events = {}
    for e in raw_events:
        if isinstance(e, dict) and e:
            k = list(e.keys())[0]
            events[k] = list(e.values())[0]
    out["ga4_events"] = events or None
    if events:
        out["ga4_note"] = ("GA4 事件数为观测口径，含内部测试提交；"
                           "真实询盘以 D1 submissions 为准（见 inquiries_d1）。")
    # --- GA4 漏斗（询盘页口径；2026-11-16 CRO 对账后新增）---
    try:
        import ga4_query as gq
        body = {
            "dateRanges": [{"startDate": _iso(start), "endDate": _iso(end)}],
            "dimensions": [{"name": "eventName"}, {"name": "date"}],
            "metrics": [{"name": "eventCount"}],
            "dimensionFilter": {"andGroup": {"expressions": [
                {"filter": {"fieldName": "pagePath",
                            "stringFilter": {"matchType": "EXACT", "value": "/inquiry"}}},
                {"filter": {"fieldName": "eventName", "inListFilter": {
                    "values": ["form_start", "submit_attempt", "submit_failure",
                               "form_submit", "generate_lead"]}}},
                gq.diag_exclusion(),
            ]}},
            "limit": 200,
        }
        r = gq.post("runReport", body)
        if "error" not in r:
            f, by_date = {}, {}
            for row in r.get("rows", []):
                ev = row["dimensionValues"][0]["value"]
                day = row["dimensionValues"][1]["value"]
                v = int(row["metricValues"][0]["value"])
                f[ev] = f.get(ev, 0) + v
                by_date.setdefault(day, {})[ev] = by_date.setdefault(day, {}).get(ev, 0) + v
            out["ga4_funnel_inquiry_page"] = f or None
            out["ga4_funnel_by_date"] = dict(sorted(by_date.items())) or None
            out["ga4_funnel_note"] = (
                "仅 /inquiry（不含 /inquiry.html 与 es/ru 旧路径）；窗口内含 2026-11-09 "
                "GTM 自构建测试事件，真实期口径见 "
                "08-execution/refresh/2026-11-16-cro-funnel-reconciliation.md")
    except Exception as e:  # noqa: BLE001
        out.setdefault("errors", []).append("GA4 漏斗口径失败: %s" % str(e)[:160])
    if raw.get("ga4_error"):
        out["ga4_error"] = raw["ga4_error"]
        out["auth"]["ga4"] = "failed"
    elif events:
        out["auth"]["ga4"] = "ok"
    else:
        out["auth"]["ga4"] = "no_rows"

    # --- 28 天环比（页面维度，重算；不用 gsc_pull 的查询词维度 compare）---
    cmp_rows = gp.gsc(["page"], _iso(c_start), _iso(c_end), 1000, at)
    cmp_tot = totals(cmp_rows)
    out["compare"] = {
        "window": {"start": _iso(c_start), "end": _iso(c_end), "days": days},
        **{k: cmp_tot[k] for k in ("clicks", "impressions", "ctr", "avg_position_weighted")},
        "change_pct": diff_stats(
            {k: out[k] for k in ("clicks", "impressions", "ctr", "avg_position_weighted")},
            cmp_tot),
        "note": "环比按页面维度重算；gsc_pull.py 的 compare 字段是查询词维度，"
                "按 §3 口径不用于 KPI。",
    }

    # --- 衍生指标①：有曝光但 0 点击（展示 ≥ 40）---
    zero = [p for p in pages
            if (p.get("impressions") or 0) >= 40 and (p.get("clicks") or 0) == 0]
    zero.sort(key=lambda p: -(p.get("impressions") or 0))
    out["derived"] = {
        "zero_click_pages_ge40": {
            "threshold_impressions": 40,
            "count": len(zero),
            "impressions_at_stake": sum(p.get("impressions") or 0 for p in zero),
            "list": [{"page": p["page"], "impressions": p["impressions"],
                      "position": p["position"]} for p in zero],
        },
    }

    # --- 衍生指标③：按页面龄分层（回答「页均展示为什么掉」）---
    try:
        co, cache = cohort_block(pages, day, days, want_cache=True)
        out["derived"]["cohort"] = co
        os.makedirs(os.path.dirname(AGE_CACHE), exist_ok=True)
        json.dump(cache, open(AGE_CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception as e:  # noqa: BLE001
        out.setdefault("errors", []).append("cohort 计算失败: %s" % str(e)[:160])

    # --- 衍生指标②：本周 vs 上周（任务书字面窗口）---
    wk = totals(gp.gsc(["page"], _iso(wk_start), _iso(wk_end), 1000, at))
    pw = totals(gp.gsc(["page"], _iso(pw_start), _iso(pw_end), 1000, at))
    wow = {
        "current": {"window": {"start": _iso(wk_start), "end": _iso(wk_end)}, **wk},
        "previous": {"window": {"start": _iso(pw_start), "end": _iso(pw_end)}, **pw},
        "change_pct": diff_stats(wk, pw),
        "ctr_pp": round((wk["ctr"] or 0) - (pw["ctr"] or 0), 2),
        "avg_position_delta": round((wk["avg_position_weighted"] or 0)
                                    - (pw["avg_position_weighted"] or 0), 2),
    }

    # 只用已 finalize 的日期做同口径 7 天对比（避免把「缺失日」读成「下跌」）
    comp = None
    if effective_end:
        ce, cs = effective_end, effective_end - dt.timedelta(days=6)
        pe, ps = cs - dt.timedelta(days=1), cs - dt.timedelta(days=7)
        c7 = totals(gp.gsc(["page"], _iso(cs), _iso(ce), 1000, at))
        p7 = totals(gp.gsc(["page"], _iso(ps), _iso(pe), 1000, at))
        comp = {
            "current": {"window": {"start": _iso(cs), "end": _iso(ce)}, **c7},
            "previous": {"window": {"start": _iso(ps), "end": _iso(pe)}, **p7},
            "change_pct": diff_stats(c7, p7),
            "ctr_pp": round((c7["ctr"] or 0) - (p7["ctr"] or 0), 2),
            "avg_position_delta": round((c7["avg_position_weighted"] or 0)
                                        - (p7["avg_position_weighted"] or 0), 2),
            "note": "只用 API 已 finalize 的日期，同口径 7v7；周环比判读以本块为准。",
        }
    out["derived"]["week_over_week"] = {
        "as_requested": wow,
        "comparable_finalized": comp,
        "note": ("as_requested 的窗口末端含 GSC 未 finalize 的日期，点击/展示会被系统性低估；"
                 "判读改用 comparable_finalized。"),
    }

    # --- 周序列（W19「周趋势」/ W1 消费）：周一~周日，最近 8 周（含本周未完整）---
    if effective_end:
        try:
            weeks = []
            cur_monday = monday_of(day)
            for i in range(8):
                ws = cur_monday - dt.timedelta(weeks=i)
                we = ws + dt.timedelta(days=6)
                wsum = totals(gp.gsc(["page"], _iso(ws), _iso(we), 1000, at))
                weeks.append({
                    "week_start": _iso(ws), "week_end": _iso(we),
                    "complete": we <= effective_end,
                    **wsum,
                })
            out["weekly_series"] = list(reversed(weeks))
        except Exception as e:  # noqa: BLE001
            out.setdefault("errors", []).append("周序列拉取失败: %s" % str(e)[:160])

    # --- 收录覆盖（W19 指标卡「收录/URL」）；只信 scope=full 的全量审计 ---
    try:
        import glob as _glob
        cands = [p for p in _glob.glob(os.path.join(WS, "08-execution", "tech",
                                                    "index-coverage*.json"))
                 if "full" in os.path.basename(p)]
        if cands:
            latest = max(cands, key=os.path.getmtime)
            d = json.load(open(latest, encoding="utf-8"))
            insp = int(d.get("inspected") or 0)
            passed = int((d.get("verdict_dist") or {}).get("PASS") or 0)
            out["indexing"] = {
                "source": os.path.basename(latest),
                "audited_at": d.get("generated_at"),
                "inspected": insp,
                "indexed": passed,
                "indexed_pct": round(passed / insp * 100, 1) if insp else None,
                "sitemap_urls": d.get("sitemap_urls"),
                "coverage_dist": d.get("coverage_dist"),
                "note": "GSC URL Inspection 全量审计（scope=full），不是当日实时；"
                        "未收录页要么等 Google 抓取，要么靠外链/内链加速。",
            }
    except Exception as e:  # noqa: BLE001
        out.setdefault("errors", []).append("收录数据读取失败: %s" % str(e)[:160])

    # --- 询盘（口径铁律：只认 D1；失败降级但不冒充 0）---
    try:
        sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))
        import d1_query as d1  # noqa: E402
        rows = d1.query("SELECT COUNT(*) AS n,"
                        " SUM(CASE WHEN consent=1 THEN 1 ELSE 0 END) AS c1,"
                        " SUM(CASE WHEN consent=0 THEN 1 ELSE 0 END) AS c0"
                        " FROM submissions")
        r = (rows or [{}])[0]
        out["inquiries_d1"] = {"available": True, "total": r.get("n") or 0,
                               "consent_1": r.get("c1") or 0,
                               "consent_0": r.get("c0") or 0}
    except Exception as e:  # noqa: BLE001
        out["inquiries_d1"] = {"available": False,
                               "error": "%s: %s" % (type(e).__name__, str(e)[:200]),
                               "note": "D1 不可读时询盘数未知，不能当 0 报。"}

    # 向后兼容总字段：W19/W1 的「询盘」一项（D1 / GA4 / Brevo 分列，不合并）
    d1_ok = bool((out.get("inquiries_d1") or {}).get("available"))
    out["inquiries"] = {
        "d1_total": (out["inquiries_d1"].get("total") if d1_ok else None),
        "ga4_form_submit": events.get("form_submit"),
        "ga4_generate_lead": events.get("generate_lead"),
        "brevo": {"available": False,
                  "reason": "BREVO_API_KEY 只存在于 Worker secret，本地不可读；"
                            "Brevo 数字需人工在后台核对，不并入本文件"},
        "note": "询盘唯一真实口径 = D1 submissions；GA4 事件含内部测试，仅链路观测；"
                "Brevo 与 D1 分列，不合并。",
    }

    out["notes"] = [
        "本文件由 scripts/metrics/daily_dashboard.py 生成，可重复执行（幂等）。",
        "KPI 口径：GSC 页面维度 / 无维度总量；查询词维度仅作选题参考（AGENTS.md §3）。",
        "GSC 未 finalize 的日期不返回数据，不视为 0 流量。",
    ]
    if raw_note:
        out["notes"].append("原始数据来源：" + raw_note)
    return strip_none(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=dt.date.today().isoformat(),
                    help="运行日（看板文件名用）；数据窗口 = 前一天往前 N 天")
    ap.add_argument("--days", type=int, default=28)
    a = ap.parse_args()

    day = dt.date.fromisoformat(a.day)
    raw_path = os.path.join(DAILY, "gsc-%s.json" % day.strftime("%Y%m%d"))
    os.makedirs(DAILY, exist_ok=True)

    dash = build(day, a.days, raw_path)
    out_path = os.path.join(DAILY, "dashboard-%s.json" % _iso(day))
    json.dump(dash, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("WROTE", out_path)

    if not dash.get("numbers_produced", True):
        print("AUTH FAILED:", dash.get("error"))
        print("retry:", "; ".join(dash.get("retry_suggestion") or []))
        return 1

    print("window: %s..%s (effective data end: %s)"
          % (dash["window"]["start"], dash["window"]["end"],
             dash.get("effective_data_end")))
    print("clicks=%s impressions=%s ctr=%s%% pos=%s pages=%s"
          % (dash["clicks"], dash["impressions"], dash["ctr"],
             dash["avg_position_weighted"], dash["pages_with_impressions"]))
    print("compare(prev 28d):", json.dumps(dash["compare"]["change_pct"], ensure_ascii=False))
    d = dash["derived"]
    print("zero_click_pages_ge40:", d["zero_click_pages_ge40"]["count"])
    co = d.get("cohort")
    if co:
        m = co.get("mature_ge14d") or {}; nw = co.get("new_lt14d") or {}
        print("cohort: 成熟页(>=14d) %s 页 / 页均 %s 次每月 | 新页(<14d) %s 页 / 页均 %s | 新页占比 %s%%"
              % (m.get("pages"), m.get("impr_per_page_month"), nw.get("pages"),
                 nw.get("impr_per_page_month"), co.get("share_new_pages_pct")))
        bi = co.get("by_index_status") or {}
        if bi:
            print("cohort(按收录): 已收录 %s 页 / 页均 %s | 未收录 %s 页 / 页均 %s"
                  % (bi["indexed"]["pages"], bi["indexed"]["impr_per_page_month"],
                     bi["not_indexed"]["pages"], bi["not_indexed"]["impr_per_page_month"]))
    wow = d["week_over_week"]
    print("WoW(as requested):", json.dumps(wow["as_requested"]["change_pct"], ensure_ascii=False))
    if wow.get("comparable_finalized"):
        print("WoW(finalized):", json.dumps(
            wow["comparable_finalized"]["change_pct"], ensure_ascii=False))
    ws = dash.get("weekly_series") or []
    print("weekly_series:", "%d weeks（%s..%s）" % (
        len(ws), ws[0]["week_start"] if ws else "-", ws[-1]["week_end"] if ws else "-"))
    print("inquiries_d1:", json.dumps(dash.get("inquiries_d1"), ensure_ascii=False))
    print("inquiries:", json.dumps(dash.get("inquiries"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
