#!/usr/bin/env python3
"""heartbeat.py — 运营流水线存活检查。

存在理由：2026-11-02 ～ 11-07 流水线静默停摆 6 天，没有任何机制报警。
本脚本检查「最近一次执行记录」的年龄，超阈值即非零退出，可挂 cron / CI / 每日任务。

用法:
  python3 scripts/heartbeat.py                 # 默认阈值 48h
  python3 scripts/heartbeat.py --max-age 72    # 放宽到 72h
  python3 scripts/heartbeat.py --json          # 机器可读

检查对象（任一存在即算活）:
  1. 本工作区 05-records/ 里最新的日终简报（文件名含 daily-summary）
  2. 运营记录源目录里的最新日终简报（只读引用）
  3. 线上 sitemap 的 <lastmod> 最大值（兜底：站点还在更新说明线在跑）
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
import urllib.request

WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
SOURCES = [
    "/Users/kerrychu/anari-charge-website/05-records",
    "/Users/kerrychu/anari-charge-website/08-execution/daily",
    "/Users/kerrychu/Documents/kimi/workspace",
]


def newest_daily():
    best = None
    for root in SOURCES:
        # 两种命名都算：历史 anari-daily-summary-<date>.md 与排期规定的 <date>-daily-brief.md
        paths = []
        for pat in ("*daily-summary*", "*daily-brief*"):
            paths += glob.glob(os.path.join(root, "**", pat), recursive=True)
        for p in paths:
            if not p.endswith(".md"):
                continue
            d = parse_date_from_name(os.path.basename(p))
            if d and (best is None or d > best[0]):
                best = (d, p, os.path.getmtime(p))
    return best


def parse_date_from_name(name):
    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", name)
    if not m:
        m = re.search(r"(20\d{2})(\d{2})(\d{2})", name)
    if m:
        try:
            return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


UA = "anari-ops-heartbeat/1.0 (+https://anaricharge.com)"


def live_lastmod():
    try:
        # Cloudflare 会 403 掉 python-urllib 默认 UA，必须显式带 UA
        req = urllib.request.Request(
            "https://www.anaricharge.com/sitemap.xml",
            headers={"User-Agent": UA, "Accept": "application/xml,*/*"})
        xml = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        lm = re.findall(r"<lastmod>([^<]+)</lastmod>", xml)
        if not lm:
            return None
        dates = sorted(x[:10] for x in lm)
        return dt.date.fromisoformat(dates[-1]), dates[-1]
    except Exception:  # noqa: BLE001
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age", type=float, default=48.0, help="小时（历史兜底阈值）")
    ap.add_argument("--brief-max-age", type=float, default=26.0,
                    help="日终简报最大年龄（小时，默认 26h：漏跑一天，次日晨检即报警）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    now = dt.datetime.now()
    today = now.date()
    findings = {}
    ok = True

    nd = newest_daily()
    if nd:
        age_h = (now - dt.datetime.fromtimestamp(nd[2])).total_seconds() / 3600
        findings["newest_daily"] = {
            "date_in_name": str(nd[0]), "path": nd[1],
            "mtime_age_hours": round(age_h, 1),
            "age_vs_named_date_days": (today - nd[0]).days,
        }
        # 双判据：① 简报文件年龄（mtime，小时级；默认 26h）
        #          ② 文件名的业务日 vs 今天（天级兜底）
        if age_h > a.brief_max_age:
            ok = False
            findings["brief_stale_reason"] = "mtime %.1fh > %.0fh" % (age_h, a.brief_max_age)
        if (today - nd[0]).days > a.max_age / 24:
            ok = False
            findings["brief_stale_reason"] = "业务日落后 %d 天" % ((today - nd[0]).days)
    else:
        findings["newest_daily"] = None
        ok = False

    lm = live_lastmod()
    if lm:
        findings["live_lastmod"] = {"date": str(lm[0]), "raw": lm[1],
                                    "age_days": (today - lm[0]).days}

    findings["today"] = str(today)
    findings["weekday"] = WEEKDAYS[today.weekday()]
    findings["verdict"] = "ALIVE" if ok else "STALE"

    if a.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    else:
        print(f"今天 {today}（{WEEKDAYS[today.weekday()]}）")
        if nd:
            print(f"最近日终简报: {nd[0]}  ({(today - nd[0]).days} 天前)  {nd[1]}")
        else:
            print("最近日终简报: 未找到")
        if lm:
            print(f"线上 sitemap 最新 lastmod: {lm[1]}  ({(today - lm[0]).days} 天前)")
        if findings.get("brief_stale_reason"):
            print(f"  ⛔ 简报超期：{findings['brief_stale_reason']}")
        print(f"判定: {findings['verdict']}  (简报阈值 {a.brief_max_age:g}h / 兜底 {a.max_age:g}h)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
