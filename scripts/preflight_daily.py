#!/usr/bin/env python3
"""preflight_daily.py — 每日自动档位的「起飞前检查」。

## 为什么需要
2026-11-08 是这套系统第一个真正的无人值守日（6 个每日档位首跑）。
档位失败最怕的不是报错，而是**静默失败**：脚本跑完但没产出，第二天才发现。
所以把每个档位的**关键路径先手动跑一遍**，能跑的现在就跑，不能跑的就检查输入是否就绪。

## 检查项（对应档位）
| 档位 | 关键路径 |
|---|---|
| 08:53 看板刷新 R6 | GSC API 拉数（含 GA4） |
| 15:41 社区 R5 | Quora 搜索（浏览器） |
| 16:30 社媒 P6 | 内容源页面存在 |
| 21:30 每日总结 | north-star JSON 可生成 + 队列可读 |
| 22:17 表单监控 R6 | D1 计数 + Worker 健康 + 三语询盘页 200 |

## 用法
  python3 scripts/preflight_daily.py            # 全部
  python3 scripts/preflight_daily.py --no-browser   # 跳过浏览器项
退出码：有阻塞（FAIL）返回 1；只有警告返回 0。
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

WS = "/Users/kerrychu/anari-charge-website"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) anari-preflight"}


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, cwd=WS, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def http(url, timeout=25, method="GET"):
    try:
        req = urllib.request.Request(url, headers=UA, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:  # noqa: BLE001
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    rows = []

    def add(name, ok, detail, blocking=True):
        rows.append({"name": name, "ok": ok, "detail": detail,
                     "blocking": blocking})

    # 1) 看板刷新：GSC 拉数
    code, out = sh("python3 scripts/gsc_pull.py --start 2026-10-11 --end 2026-11-06 "
                   "--out /tmp/preflight-gsc.json", timeout=240)
    ok = code == 0 and os.path.exists("/tmp/preflight-gsc.json")
    tail = [l for l in out.splitlines() if l.strip()][-1][:70] if out.strip() else ""
    add("08:53 看板刷新 · GSC API", ok, tail or "无输出")

    # 2) 每日总结：north-star 可生成
    code, out = sh("python3 scripts/metrics/north_star.py", timeout=240)
    today = subprocess.run("date +%Y-%m-%d", shell=True, capture_output=True, text=True).stdout.strip()
    path = os.path.join(WS, "08-execution", "dashboard", "north-star-%s.json" % today)
    ok = code == 0 and os.path.exists(path)
    gap = ""
    if ok:
        try:
            d = json.load(open(path, encoding="utf-8"))
            gap = "gap.rows=%d behind=%d" % (len(d.get("gap", {}).get("rows") or []),
                                             len(d.get("gap", {}).get("behind") or []))
        except Exception:  # noqa: BLE001
            gap = "JSON 解析失败"
    add("21:30 每日总结 · north-star", ok, gap or path)

    # 3) 队列可读
    code, out = sh("python3 scripts/community/approval.py status", timeout=60)
    add("21:30 每日总结 · 审批队列", code == 0, (out.strip().splitlines() or [""])[-1][:60])

    # 4) 表单监控：D1 + Worker + 三语页面
    code, out = sh("python3 scripts/metrics/d1_query.py counts", timeout=120)
    add("22:17 表单监控 · D1 计数", code == 0, (out.strip().splitlines() or [""])[-1][:60])
    wh = http("https://api.anaricharge.com/health")
    add("22:17 表单监控 · Worker", wh == 403, "HTTP %s（403=正常）" % wh)
    bad = [u for u in ("/inquiry", "/ru/inquiry", "/es/inquiry")
           if http("https://www.anaricharge.com" + u) != 200]
    add("22:17 表单监控 · 三语询盘页", not bad, "全部 200" if not bad else "异常: " + ", ".join(bad))

    # 5) 社媒内容源
    base = os.path.join(WS, "06-site", "anari-new-site", "site")
    counts = {}
    for d in ("blog", "cases", "data"):
        p = os.path.join(base, d)
        counts[d] = len([f for f in os.listdir(p) if f.endswith(".html")]) if os.path.isdir(p) else 0
    add("16:30 社媒 P6 · 内容源", sum(counts.values()) >= 30,
        "blog %d / cases %d / data %d" % (counts["blog"], counts["cases"], counts["data"]))

    # 6) 社区档位：浏览器搜索（可选）
    if a.no_browser:
        add("15:41 社区 R5 · Quora 搜索", True, "已跳过（--no-browser）", blocking=False)
    else:
        code, out = sh("python3 scripts/browser/ops.py quora-search "
                       "\"ev charging station franchise\" --limit 3", timeout=240)
        ok = code == 0 and '"url"' in out
        add("15:41 社区 R5 · Quora 搜索", ok, "返回结果" if ok else out[-70:])
        sh("python3 scripts/browser/wb.py hygiene", timeout=60)

    # 输出
    print("=" * 78)
    print("每日档位起飞前检查")
    print("=" * 78)
    fails = 0
    for r in rows:
        icon = "✅" if r["ok"] else ("❌" if r["blocking"] else "⚠️")
        print(f"  {icon} {r['name']:34s} {r['detail']}")
        if not r["ok"] and r["blocking"]:
            fails += 1
    print("=" * 78)
    print(("✅ 全部就绪，明天可以无人值守运行" if fails == 0
           else "❌ %d 项阻塞，需先修" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
