#!/usr/bin/env python3
"""watchdog_daily.py — 检测「档位该跑了但没有产出」（静默失败）。

## 为什么需要
自动化最危险的失败不是报错，是**跑完了但没产出**：
档位返回 0、日志正常，第二天才发现昨天什么都没有。
所以按「应该产出什么文件」反查——缺文件 = 静默失败。

## 判定
对每个每日档位列出它当天应产出的文件模式；到点之后仍缺失 → 报 MISSING。
未到点的档位标 PENDING（不算失败）。

## 用法
  python3 scripts/watchdog_daily.py            # 检查今天
  python3 scripts/watchdog_daily.py --date 2026-11-08
退出码：有 MISSING 返回 1。
"""
import argparse
import glob
import re as _re
import os
import sys
import datetime as dt

WS = "/Users/kerrychu/anari-charge-website"

# (档位, 北京时间几点, [(相对 today 的 glob 模式, 说明)])
TASKS = [
    ("08:40 Gmail 预热清理", "08:40", [
        ("08-execution/tech/gmail-cleanup-{d}.json", "清理结果"),
    ]),
    ("08:53 看板刷新 R6", "08:53", [
        ("08-execution/daily/dashboard-{d}.json", "看板数据文件"),
    ]),
    ("15:41 社区 R5", "15:41", [
        ("08-execution/community/{d}-quora-drafts.md", "当天稿件记录"),
    ]),
    ("16:30 社媒 P6", "16:30", [
        ("08-execution/social/{d}-dispatch.md", "一稿多用分发包"),
    ]),
    ("21:30 每日总结", "21:30", [
        ("08-execution/dashboard/north-star-{d}.json", "看板快照"),
    ]),
    ("22:00 日终简报 E3", "22:00", [
        ("08-execution/daily/{d}-daily-brief.md", "日终简报文字版"),
    ]),
    ("22:17 表单监控 R6", "22:17", [
        ("08-execution/inquiry/{d}-inquiry-monitor.md", "询盘监控报告"),
    ]),
]


SCHED = "/Users/kerrychu/.dsh/storages/schedule.json"


def first_run_dates():
    """每个档位的首次排期日期 —— 用来区分「还没开始」和「静默失败」。"""
    import json as _json
    out = {}
    try:
        d = _json.load(open(SCHED, encoding="utf-8"))
        for t in (d.get("tables", {}).get("tasks") or {}).values():
            r = t.get("record") or {}
            title = r.get("title") or ""
            # 坑（2026-11-08 实测）：`scheduledAt` 是"下一次"运行时间，跑完就变成明天，
            # 于是 today 检查时被判成"首次排期在将来"→ NOT_STARTED，
            # 把"看板 08:53 明明跑了"误报成"没启用"。
            # 正确判据：rrule 里的 DTSTART 才是首次排期。
            rr = r.get("rrule") or ""
            m = _re.search(r"DTSTART(?:;TZID=[^:]+)?:(\d{8})", rr)
            if m:
                out[title] = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:8]}"
            else:
                sa = (r.get("scheduledAt") or "")[:10]
                if sa:
                    out[title] = sa
    except Exception:  # noqa: BLE001
        pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="")
    ap.add_argument("--simulate-now", default="", help="模拟当前时间（HH:MM），用于测试 MISSING 分支")
    a = ap.parse_args()
    day = a.date or dt.date.today().isoformat()
    now_local = dt.datetime.now()
    if a.simulate_now:
        try:                       # 模拟时间要落在被检查的那一天，否则比较无意义
            now_local = dt.datetime.strptime("%s %s" % (day, a.simulate_now),
                                             "%Y-%m-%d %H:%M")
        except Exception:  # noqa: BLE001
            pass
    rows = []
    starts = first_run_dates()
    # 档位标题关键词 → 首次排期
    KEYMAP = [("看板", "看板刷新"), ("社区", "社区引流"), ("社媒", "社媒分发"),
              ("每日总结", "每日工作总结"), ("表单监控", "表单询盘监控")]
    def first_start(name):
        for kw, title_kw in KEYMAP:
            if kw in name:
                for k, v in starts.items():
                    if title_kw in k:
                        return v
        return None

    for name, hhmm, expects in TASKS:
        due = dt.datetime.strptime("%s %s" % (day, hhmm), "%Y-%m-%d %H:%M")
        past = now_local >= due
        missing = []
        late_h = 2.0            # 允许迟到 2 小时；超过即标 LATE（不是 MISSING，但同样要报）
        late_files = []
        # 看板 JSON 会被后续档位重新生成（mtime 不可信），所以不参与迟到判定
        late_check = "看板" not in name
        for pat, why in expects:
            p = os.path.join(WS, pat.format(d=day, compact=day.replace("-", "")))
            hits = glob.glob(p)
            # 兼容别名：标准 dashed 不存在时，再试 compact（YYYYMMDD）命名
            if not hits and "dashboard-{d}" in pat:
                alt = p.replace(day, day.replace("-", ""))
                hits = glob.glob(alt)
            if not hits:
                missing.append("%s（%s）" % (why, os.path.basename(pat).format(d=day, compact=day.replace("-", ""))))
            else:
                mt = max(os.path.getmtime(h) for h in hits)
                import datetime as _dt
                mt_utc = _dt.datetime.utcfromtimestamp(mt)
                due_utc = due - _dt.timedelta(hours=8)   # 档位时间是北京时间
                if late_check and mt_utc > due_utc + _dt.timedelta(hours=late_h):
                    late_files.append((why, round((mt_utc - due_utc).total_seconds() / 3600, 1)))
        fs = first_start(name)
        if fs and fs > day:
            status = "NOT_STARTED"          # 档位首次排期在将来，今天本不该跑
        elif not past:
            status = "PENDING"
        elif missing:
            status = "MISSING"
        elif late_files:
            status = "LATE"
        else:
            status = "OK"
        rows.append({"task": name, "due": hhmm, "status": status, "missing": missing,
                     "late": late_files})

    print("=" * 76)
    print("档位产出检测 · %s" % day)
    print("=" * 76)
    bad = 0
    for r in rows:
        icon = {"OK": "✅", "PENDING": "⏳", "MISSING": "❌", "LATE": "🟡",
                "NOT_STARTED": "·"}[r["status"]]
        extra = ""
        if r["status"] == "MISSING":
            extra = " 缺: " + "; ".join(r["missing"])
        elif r["status"] == "LATE":
            extra = " 迟到: " + "; ".join("%s +%.1fh" % (w, h) for w, h in r["late"])
        print(f"  {icon} {r['task']:24s} {r['status']:8s}{extra}")
        if r["status"] == "MISSING":
            bad += 1
    print("=" * 76)
    late_rows = [r for r in rows if r["status"] == "LATE"]
    if bad:
        print("❌ %d 个档位静默失败（到点但没有产出）" % bad)
        return 1
    if late_rows:
        print("🟡 %d 个档位迟到（有产出但晚于 %s 后 2h）" % (len(late_rows), "排期时间"))
        for r in late_rows:
            print("   %s: %s" % (r["task"], "; ".join("%s +%.1fh" % (w, h) for w, h in r["late"])))
    pend = sum(1 for r in rows if r["status"] == "PENDING")
    ns = sum(1 for r in rows if r["status"] == "NOT_STARTED")
    extra = []
    if pend:
        extra.append("%d 个未到点" % pend)
    if ns:
        extra.append("%d 个档位尚未启用（首次排期在将来）" % ns)
    print("✅ 无静默失败" + ("（" + "，".join(extra) + "）" if extra else ""))
    # 顺手补记 run log（GROW-011）：从今天的产物反推哪些档位真跑了。
    # 放在 watchdog 里是因为日终简报每期都调它 —— 不用改 12 个任务书。
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "metrics"))
        import run_log_autolog as _al
        _argv = sys.argv
        sys.argv = ["run_log_autolog"] + (["--date", a.date] if getattr(a, "date", None) else [])
        _al.main()
        sys.argv = _argv
    except Exception as e:  # noqa: BLE001
        print(f"  （run log 自动补记跳过：{type(e).__name__}: {e}）")

    return 0



if __name__ == "__main__":
    sys.exit(main())
