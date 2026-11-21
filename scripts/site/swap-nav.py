#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""swap-nav.py — 用新导航片段替换全站页面里的 <header>（幂等）

为什么需要：导航片段只被**生成器**使用（57 页），其余 ~110 页是早期套壳的
静态 HTML，导航写死在页面里。改导航必须同时覆盖这两类，否则新旧混用。

做法：从 `<header class="site-header"` 到第一个 `</header>` 整块替换成片段内容。
幂等：替换后再跑一次结果不变。
校验：每页替换后必须仍有且仅有 1 个 <header>、1 个 .site-nav。

用法：
  python3 scripts/site/swap-nav.py          # 干跑统计
  python3 scripts/site/swap-nav.py --write
"""
import argparse
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
SITE = os.path.join(WS, "06-site/anari-new-site/site")
FRAG = os.path.join(HERE, "fragments")

SKIP_DIRS = {"apps", "assets"}


def frag_for(rel):
    if rel.startswith("ru/"):
        return io.open(os.path.join(FRAG, "nav-ru.html"), encoding="utf-8").read()
    if rel.startswith("es/"):
        return io.open(os.path.join(FRAG, "nav-es.html"), encoding="utf-8").read()
    return io.open(os.path.join(FRAG, "nav.html"), encoding="utf-8").read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    changed = skipped = same = 0
    problems = []
    for root, dirs, files in os.walk(SITE):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if not fn.endswith(".html"):
                continue
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, SITE)
            t = io.open(fp, encoding="utf-8").read()
            m = re.search(r'<header class="site-header"', t)
            if not m:
                skipped += 1
                continue
            start = m.start()
            end = t.find("</header>", start)
            if end < 0:
                problems.append(f"{rel}: 找不到 </header>")
                continue
            end += len("</header>")
            new = t[:start] + frag_for(rel).rstrip("\n") + t[end:]
            if new == t:
                same += 1
                continue
            # 页面里可能有语义化的 <header>（文章头部），所以只校验站点导航本身唯一
            if new.count('class="site-header"') != 1 or new.count('class="site-nav"') != 1:
                problems.append(f"{rel}: 替换后 header/nav 计数异常")
                continue
            changed += 1
            if a.write:
                io.open(fp, "w", encoding="utf-8").write(new)

    print(f"{'写入' if a.write else '将改'} {changed} 页 · 已是最新 {same} 页 · 无 header {skipped} 页")
    if problems:
        print("异常：")
        for p in problems[:10]:
            print("  -", p)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
