#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""add-article-toc.py — 给长文自动加目录（计划 §3：博客正文应有 TOC）

规则：
- 只处理 h2 ≥ 3 的页面（短文章加目录是噪音）
- 没有 id 的 h2 自动补 slug 化 id（重复自动加后缀）
- TOC 插在第一个 h2 之前；已有 `data-toc` 则跳过（幂等）
- 纯静态 HTML，不依赖 JS；样式在 v2.css（.article-toc）

用法：
  python3 scripts/site/add-article-toc.py            # 干跑
  python3 scripts/site/add-article-toc.py --write
"""
import argparse
import html
import io
import os
import re
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
SITE = os.path.join(WS, "06-site/anari-new-site/site")
DIRS = ["blog", "regulations", "academy", "playbooks", "cost", "depot", "markets"]
SKIP = {"index.md"}


def slugify(text):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t or "section"


def process(fp):
    t = io.open(fp, encoding="utf-8").read()
    if "data-toc" in t or "<article" not in t:
        return "skip"
    # 只取文章正文区（避免把导航/footer 里的 h2 算进来）
    art = re.search(r"<article.*?</article>", t, re.S)
    if not art:
        return "skip"
    body = art.group(0)
    h2s = list(re.finditer(r"<h2([^>]*)>(.*?)</h2>", body, re.S))
    if len(h2s) < 3:
        return "short"

    new_body = body
    entries, used = [], set()
    # 逆序处理，保证插 id 不移动前面的位置
    for m in reversed(h2s):
        attrs, inner = m.group(1), m.group(2)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        if not text:
            continue
        mm = re.search(r'id="([^"]+)"', attrs)
        if mm:
            hid = mm.group(1)
        else:
            hid = slugify(text)
            base, i = hid, 2
            while hid in used:
                hid = f"{base}-{i}"
                i += 1
            new_body = (new_body[: m.start()]
                        + f'<h2{attrs} id="{hid}">{inner}</h2>'
                        + new_body[m.end():])
        used.add(hid)
        entries.append((hid, text))
    entries.reverse()

    toc = ['<nav class="article-toc" data-toc aria-label="On this page">',
           "  <p class=\"article-toc-title\">On this page</p>", "  <ol>"]
    for hid, text in entries:
        toc.append(f'    <li><a href="#{hidden_ok(hid)}">{html.escape(text)}</a></li>')
    toc.append("  </ol>")
    toc.append("</nav>")

    # 插在第一个 h2 之前
    first = re.search(r"<h2", new_body)
    new_body = new_body[: first.start()] + "\n".join(toc) + "\n" + new_body[first.start():]
    t = t[: art.start()] + new_body + t[art.end():]
    io.open(fp, "w", encoding="utf-8").write(t)
    return "ok"


def hidden_ok(s):
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    stats = {"ok": 0, "skip": 0, "short": 0}
    for d in DIRS:
        root = os.path.join(SITE, d)
        if not os.path.isdir(root):
            continue
        for fn in sorted(os.listdir(root)):
            if not fn.endswith(".html"):
                continue
            fp = os.path.join(root, fn)
            if not a.write:
                t = io.open(fp, encoding="utf-8").read()
                art = re.search(r"<article.*?</article>", t, re.S)
                n = len(re.findall(r"<h2", art.group(0))) if art else 0
                if "data-toc" in t:
                    stats["skip"] += 1
                elif n < 3:
                    stats["short"] += 1
                else:
                    stats["ok"] += 1
                    print(f"  将加目录: {d}/{fn}（{n} 个 h2）")
                continue
            r = process(fp)
            stats[r] += 1
            if r == "ok":
                print(f"  ✅ {d}/{fn}")
    print(f"\n{'已写入' if a.write else '干跑'}：加目录 {stats['ok']} · 已有跳过 {stats['skip']} · 段落不足 {stats['short']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
