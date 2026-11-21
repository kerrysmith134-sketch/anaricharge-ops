#!/usr/bin/env python3
"""layout_audit.py — 全站布局结构审计（为大修准备地图）。

## 为什么
站点 153 页，没有模板机制：header / hero / footer 都是复制粘贴演化出来的。
改版前必须先知道"每一类页面用的是什么布局原语"，否则只能逐页手改。

## 输出
每页一行：族 / header 变体 / hero 变体 / 是否有面包屑 / section 数 / 组件组合
外加按族汇总：哪些族结构一致（可脚本批量改）、哪些族各页独立（需模板化）

## 用法
  python3 scripts/site/layout_audit.py              # 汇总
  python3 scripts/site/layout_audit.py --detail     # 每页一行
  python3 scripts/site/layout_audit.py --json
"""
import argparse
import collections
import hashlib
import io
import json
import os
import re

SITE = os.path.join(os.path.dirname(__file__), "..", "..", "06-site", "anari-new-site", "site")
SITE = os.path.abspath(SITE)
SKIP = {"apps", "assets", "node_modules", ".git"}

PRIMITIVES = [
    ("breadcrumb", r'class="breadcrumb'),
    ("hero", r'<section class="hero[^"]*"'),
    ("hero-v2", r'<section class="hero-v2'),
    ("page-head", r'class="page-head"'),
    ("tldr", r'class="tldr"'),
    ("stat-band", r'class="stat-band'),
    ("table", r'<table class="data"'),
    ("cards", r'class="grid grid-[234]'),
    ("faq", r'Frequently asked questions|faq-list'),
    ("cta", r'class="cta'),
    ("calc", r'class="calc"'),
    ("app-embed", r'iframe class="app-embed"'),
]


def pages():
    out = []
    for dp, dn, fn in os.walk(SITE):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            if f.endswith(".html"):
                out.append(os.path.join(dp, f))
    return sorted(out)


def family(path):
    rel = os.path.relpath(path, SITE)
    parts = rel.split(os.sep)
    if len(parts) == 1:
        return "root"
    return parts[0]


def sig(text, pattern):
    m = re.search(pattern, text, re.S)
    return hashlib.md5(m.group(0).encode()).hexdigest()[:8] if m else "-"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detail", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    rows = []
    for p in pages():
        t = io.open(p, encoding="utf-8", errors="ignore").read()
        used = [name for name, pat in PRIMITIVES if re.search(pat, t)]
        rows.append({
            "page": os.path.relpath(p, SITE),
            "family": family(p),
            "header": sig(t, r'<header class="site-header".*?</header>'),
            "hero": sig(t, r'<section class="[^"]*hero[^"]*".*?<h1'),
            "footer": sig(t, r'<footer class="site-footer".*?</footer>'),
            "sections": len(re.findall(r"<section\b", t)),
            "components": used,
            "bytes": len(t),
        })

    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0

    if a.detail:
        print(f"{'page':52s} {'族':14s} {'hero':9s} {'sec':>4s} 组件")
        for r in rows:
            print(f"{r['page']:52s} {r['family']:14s} {r['hero']:9s} {r['sections']:4d} "
                  f"{','.join(r['components'])}")
        return 0

    by_fam = collections.defaultdict(list)
    for r in rows:
        by_fam[r["family"]].append(r)

    print(f"全站 {len(rows)} 页 · {len(by_fam)} 个页面族\n")
    print(f"{'族':16s} {'页数':>4s} {'hero变体':>8s} {'header变体':>10s}  一致性")
    print("-" * 64)
    for fam, rs in sorted(by_fam.items(), key=lambda kv: -len(kv[1])):
        hv = len({r["hero"] for r in rs})
        hd = len({r["header"] for r in rs})
        if hv == 1 and hd == 1:
            note = "结构统一 → 可脚本批量改"
        elif hv == len(rs):
            note = "每页独立 hero → 需模板化"
        else:
            note = "混合"
        print(f"{fam:16s} {len(rs):4d} {hv:8d} {hd:10d}  {note}")

    print("\n组件使用频次：")
    c = collections.Counter()
    for r in rows:
        for x in r["components"]:
            c[x] += 1
    for k, v in c.most_common():
        print(f"  {k:14s} {v:3d} 页 ({v/len(rows)*100:.0f}%)")

    odd = [r for r in rows if not r["components"]]
    if odd:
        print(f"\n无任何已知布局原语的页面 {len(odd)} 个：")
        for r in odd[:8]:
            print("  ", r["page"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
