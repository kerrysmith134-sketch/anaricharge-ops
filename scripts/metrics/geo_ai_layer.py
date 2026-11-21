#!/usr/bin/env python3
"""geo_ai_layer.py — GEO 的 AI 引擎层测量（Perplexity / AI 答案）。

## 为什么单独一层
2026-11-07 的 GEO 基线只有 `search_proxy` 层（搜索引擎结果里我们是否出现），
**AI 引擎层从来没测过**——而 GEO 的目标恰恰是"AI 回答里是否引用我们"。
两层会不一致：搜索引擎结果页看的是排名，AI 答案看的是"被当成来源引用"。

## 做法
对 query-set 里的查询，真跑 AI 引擎（浏览器带真实会话），
读回答文本 + 引用链接，判断 anaricharge.com 是否被引用，记录引用来源域名（=该抢的位置）。

## 用法
  python3 scripts/metrics/geo_ai_layer.py --per-cluster 1        # 每簇 1 条（基线）
  python3 scripts/metrics/geo_ai_layer.py --ids Q01,Q06,Q11     # 指定
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.parse

WS = "/Users/kerrychu/anari-charge-website"
QS = os.path.join(WS, "08-execution", "geo", "query-set.json")
OUT = os.path.join(WS, "08-execution", "geo", "geo-citations-ai.json")
OURS = ("anaricharge.com", "anari energy")

sys.path.insert(0, os.path.join(WS, "scripts", "browser"))
from wb import WB, cleanup_all  # noqa: E402


def load_queries():
    d = json.load(open(QS, encoding="utf-8"))
    return d.get("queries") or d


def pick(args, queries):
    if args.ids:
        want = {x.strip() for x in args.ids.split(",") if x.strip()}
        return [q for q in queries if q.get("id") in want]
    if args.per_cluster:
        seen, out = set(), []
        for q in queries:
            c = q.get("cluster")
            if c in seen:
                continue
            seen.add(c)
            out.append(q)
            if len(out) >= args.per_cluster * len({x.get("cluster") for x in queries}):
                break
        return out
    return queries


def ask(wb, query_text, wait=45):
    """在 Perplexity 里跑一条查询，返回 (answer_text, links[])。"""
    url = "https://www.perplexity.ai/search?q=" + urllib.parse.quote(query_text)
    wb.nav(url, new_tab=False)
    t0 = time.time()
    # 等回答出现（有 <a href="http 且正文变长）
    while time.time() - t0 < wait:
        time.sleep(4)
        st = wb.eval("""
        const t=(document.body.innerText||'');
        const links=[...document.querySelectorAll('a[href^="http"]')].map(a=>a.href)
          .filter(h=>!/perplexity\\.ai|google\\.com|apple\\.com|chrome/i.test(h));
        return JSON.stringify({len:t.length, links:[...new Set(links)].slice(0,40),
                               txt:t.slice(0,6000)});
        """)
        try:
            st = json.loads(st)
        except Exception:  # noqa: BLE001
            continue
        if st.get("len", 0) > 1200 and st.get("links"):
            return st.get("txt", ""), st.get("links", [])
    try:
        st = json.loads(wb.eval("""
        const t=(document.body.innerText||'');
        const links=[...document.querySelectorAll('a[href^="http"]')].map(a=>a.href)
          .filter(h=>!/perplexity\\.ai|google\\.com|apple\\.com|chrome/i.test(h));
        return JSON.stringify({len:t.length, links:[...new Set(links)].slice(0,40), txt:t.slice(0,6000)});
        """))
        return st.get("txt", ""), st.get("links", [])
    except Exception:  # noqa: BLE001
        return "", []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-cluster", type=int, default=0)
    ap.add_argument("--ids", default="")
    ap.add_argument("--engine", default="perplexity")
    a = ap.parse_args()

    queries = pick(a, load_queries())
    print(f"将测 {len(queries)} 条查询（引擎 {a.engine}）")
    wb = WB(session="geo")
    try:
        rows = []
        for q in queries:
            txt, links = ask(wb, q["q"])
            low = (txt or "").lower()
            cited = any(o in low for o in OURS) or any(
                any(o in (l or "").lower() for o in ("anaricharge", "anariev")) for l in links)
            # 回答里出现的来源域名（=该抢的位置）
            domains = []
            for l in links:
                m = re.match(r"https?://([^/]+)", l)
                if m:
                    domains.append(m.group(1).replace("www.", ""))
            rival = [d for d in dict.fromkeys(domains) if not any(o in d for o in ("anaricharge", "anariev"))]
            row = {"id": q.get("id"), "cluster": q.get("cluster"), "q": q["q"],
                   "engine": a.engine, "cited": bool(cited),
                   "answer_chars": len(txt or ""),
                   "sources": rival[:12],
                   "checked_at": dt.datetime.now().isoformat(timespec="seconds")}
            rows.append(row)
            print(f"  {'✅' if cited else '❌'} {row['id']} [{row['cluster']}] {q['q'][:52]} "
                  f"| 回答 {row['answer_chars']} 字 | 来源 {len(rival)} 个"
                  + (f" | 前3: {', '.join(rival[:3])}" if rival else ""))

        old = []
        if os.path.exists(OUT):
            try:
                old = (json.load(open(OUT, encoding="utf-8")).get("rows") or [])
            except Exception:  # noqa: BLE001
                old = []
        old_ids = {(r.get("id"), r.get("engine")) for r in rows}
        merged = rows + [r for r in old if (r.get("id"), r.get("engine")) not in old_ids]
        payload = {"layer": "ai_engine", "engine": a.engine,
                   "checked_at": dt.datetime.now().isoformat(timespec="seconds"),
                   "rows": merged}
        json.dump(payload, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        n = len(rows)
        c = sum(1 for r in rows if r["cited"])
        print(f"\n本轮：{c}/{n} 被引用 | 写入 {OUT}")
    finally:
        try:
            cleanup_all(verbose=False)
        except Exception:  # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
