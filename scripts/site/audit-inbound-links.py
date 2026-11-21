#!/usr/bin/env python3
"""audit-inbound-links.py — 页面族入链审计（防孤儿页）。

## 为什么需要
页面工厂解决"生产"，不解决"分发"。新增页面族若没有站内入口：
  - 只能靠 sitemap 被发现，抓取深度与权重分配都吃亏
  - 越是批量产页，抽屉里堆得越多
本脚本把"孤儿检查"变成一条命令。

用法:
  python3 scripts/site/audit-inbound-links.py            # 审计所有页面族
  python3 scripts/site/audit-inbound-links.py --min 3    # 入链少于 3 视为异常
"""
import argparse
import glob
import os
import re
import sys

WS = "/Users/kerrychu/anari-charge-website"
SITE = os.path.join(WS, "06-site", "anari-new-site", "site")
FAMILIES = ["/cost/", "/markets/", "/data/", "/cases/", "/depot/", "/connectors/", "/regulations/"]
# 本就不该有入链的页面（错误页、跳转页）
EXEMPT = {"/404", "/404.html", "/offline", "/maintenance"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=1, help="低于此入链数视为孤儿")
    a = ap.parse_args()

    files = glob.glob(os.path.join(SITE, "**", "*.html"), recursive=True)
    pages = []
    for f in files:
        rel = "/" + os.path.relpath(f, SITE).replace(os.sep, "/")
        pages.append((rel, open(f, encoding="utf-8", errors="replace").read()))

    bad = 0
    print("=== 页面族入链审计 ===")
    for fam in FAMILIES:
        hub = fam
        hub_exists = any(rel == fam + "index.html" for rel, _ in pages)
        if not hub_exists:
            continue
        inbound = 0
        for rel, t in pages:
            if rel.startswith(fam) and rel != fam + "index.html":
                continue  # 族内互链不算"外部入口"
            if rel == fam + "index.html":
                continue
            if 'href="%s"' % fam in t:
                inbound += 1
        flag = "✅" if inbound >= a.min else "❌ 孤儿"
        print("  %-16s 入链 %3d 页面  %s" % (fam, inbound, flag))
        if inbound < a.min:
            bad += 1

    # 逐页孤儿扫描（无任何入链的页）
    print("\n=== 全站孤儿页（零入链）===")
    targets = [rel for rel, _ in pages
               if not rel.endswith("index.html")
               and (rel[:-5] if rel.endswith(".html") else rel) not in EXEMPT]
    orph = 0
    for rel in targets:
        url = rel[:-5] if rel.endswith(".html") else rel
        inbound = sum(1 for r2, t2 in pages if r2 != rel and ('href="%s"' % url in t2))
        if inbound == 0:
            print("  ❌ %s" % url)
            orph += 1
    if orph == 0:
        print("  ✅ 无孤儿页")
    return 1 if bad or orph else 0


if __name__ == "__main__":
    sys.exit(main())
