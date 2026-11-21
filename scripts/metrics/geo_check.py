#!/usr/bin/env python3
"""geo_check.py — GEO / AI 可见度基线统计。

## 为什么需要
飞轮里 `C.geo_cited` 一直是 no_data：没有台账就无法判断"AI 回答里有没有引用我们"。
这个脚本把 `geo-citations.json` 变成可算的 KPI，并指出**该抢谁的位置**。

## 两层
- `search_proxy`：搜索引擎结果里我们是否出现（可用 web_search 自动查）
- `ai_engine`：ChatGPT / Perplexity / AI Overview 是否引用（需浏览器，另跑）

## 用法
  python3 scripts/metrics/geo_check.py summary     # 引用率 + 按簇分布
  python3 scripts/metrics/geo_check.py rivals      # 反复出现的域名（该抢的位置）
  python3 scripts/metrics/geo_check.py gaps        # 哪些簇完全没露出
"""
import json
import os
import sys
from collections import Counter

WS = "/Users/kerrychu/anari-charge-website"
P = os.path.join(WS, "08-execution", "geo", "geo-citations.json")


def load():
    if not os.path.exists(P):
        raise SystemExit("缺 geo-citations.json：先按 query-set.json 跑一遍抽查并落盘")
    return json.load(open(P, encoding="utf-8"))


def summary(d):
    rows = d.get("rows") or []
    total = len(rows)
    cited = sum(1 for r in rows if r.get("cited"))
    print("=== GEO 可见度（%s 层）===" % d.get("layer", "?"))
    print("  抽查查询 %d 条 | 被引 %d 条 | 引用率 %.1f%%" % (
        total, cited, cited / total * 100 if total else 0))
    by = {}
    for r in rows:
        c = r.get("cluster", "?")
        by.setdefault(c, [0, 0])
        by[c][1] += 1
        if r.get("cited"):
            by[c][0] += 1
    print("\n  按意图簇：")
    for c, (n, t) in sorted(by.items()):
        print("    %-10s %d/%d" % (c, n, t))
    return cited, total


def rivals(d):
    c = Counter()
    for r in d.get("rows") or []:
        for dom in r.get("competitor_domains_visible") or []:
            c[dom] += 1
    print("=== 反复出现的域名（这些就是要抢的位置）===")
    for dom, n in c.most_common(20):
        print("  %2d 次  %s" % (n, dom))
    return c


def gaps(d):
    cited = {r.get("cluster") for r in d.get("rows") or [] if r.get("cited")}
    clusters = {r.get("cluster") for r in d.get("rows") or []}
    miss = sorted(clusters - cited)
    print("=== 完全没露出的意图簇（0 引用）===")
    for c in miss:
        n = sum(1 for r in d.get("rows") or [] if r.get("cluster") == c)
        print("  %-10s %d 条查询全无露出 → 该簇需要专门的内容资产" % (c, n))
    return miss


def ai_layer():
    """AI 引擎层（Perplexity 等）的可见度 —— 与 search_proxy 层分开看。"""
    p = os.path.join(WS, "08-execution", "geo", "geo-citations-ai.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def show_ai(a):
    d = ai_layer()
    if not d:
        print("\n=== AI 引擎层 === 尚未测量（跑 scripts/metrics/geo_ai_layer.py）")
        return
    rows = d.get("rows") or []
    cited = [r for r in rows if r.get("cited")]
    print("\n=== GEO 可见度（AI 引擎层 · %s）===" % d.get("engine", "?"))
    print("  抽查 %d 条 | 被引用 %d 条 | 最近测量 %s" %
          (len(rows), len(cited), d.get("checked_at", "")[:19]))
    for r in rows:
        print("   %s %-6s [%-7s] %-52s 来源 %d" %
              ("✅" if r.get("cited") else "❌", r.get("id"), r.get("cluster"),
               (r.get("q") or "")[:52], len(r.get("sources") or [])))
    # 反复出现的来源 = 该抢的位置
    from collections import Counter
    c = Counter()
    for r in rows:
        for s in (r.get("sources") or []):
            c[s] += 1
    if c:
        print("  反复出现的来源（= 该抢的位置）：" +
              ", ".join("%s %d 次" % (k, v) for k, v in c.most_common(6)))


def main():
    d = load()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"
    if cmd == "summary":
        summary(d)
        show_ai(None)          # AI 引擎层（Perplexity 等）单独一段
    elif cmd == "ai":
        show_ai(None)
    elif cmd == "rivals":
        rivals(d)
    elif cmd == "gaps":
        gaps(d)
    else:
        raise SystemExit("用法: summary | rivals | gaps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
