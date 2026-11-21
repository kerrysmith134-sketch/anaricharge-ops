#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""url-inventory.py — 生产 URL 清单（Growth OS GROW-001）

计划要求："URL 列表、页面版本、线上内容、构建来源有单一清单"。
此前只能靠 sitemap + 猜；本脚本从**构建产物**生成一份机器可读清单：
每个 URL 的 语言 / 页面族 / title / h1 / 字节数 / lastmod / markdown 镜像 / 入链数来源。

用法：
  python3 scripts/site/url-inventory.py                     # 写 08-execution/tech/url-inventory-<日期>.json
  python3 scripts/site/url-inventory.py --check             # 只比对：sitemap 与磁盘 HTML 是否一致
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
SITE = os.path.join(WS, "06-site/anari-new-site/site")
BASE = "https://www.anaricharge.com"

FAMILY_RULES = [
    (r"^/cases/", "cases"), (r"^/products/", "products"),
    (r"^/solutions/", "solutions"), (r"^/depot/", "depot"),
    (r"^/markets/", "markets"), (r"^/cost/", "cost"),
    (r"^/blog/", "blog"), (r"^/academy/", "academy"),
    (r"^/regulations/", "regulations"), (r"^/playbooks/", "playbooks"),
    (r"^/tools/", "tools"), (r"^/data/", "data"),
    (r"^/journey/", "journey"), (r"^/who-we-serve/", "who-we-serve"),
    (r"^/agents/", "agents"), (r"^/about", "about"), (r"^/privacy", "privacy"),
    (r"^/inquiry", "inquiry"), (r"^/turnkey/", "turnkey"),
]


def family(path):
    for pat, name in FAMILY_RULES:
        if re.search(pat, path):
            return name
    return "root"


def page_meta(fp):
    t = open(fp, encoding="utf-8", errors="ignore").read()
    lang = (re.search(r'<html[^>]*lang="([^"]+)"', t) or [None, "en"])[1]
    title = (re.search(r"<title>([^<]*)</title>", t) or [None, ""])[1]
    h1 = (re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S) or [None, ""])[1]
    h1 = re.sub(r"<[^>]+>", "", h1).strip()[:120]
    return {"lang": lang, "title": title.strip()[:120], "h1": h1,
            "bytes": len(t.encode()),
            "has_ld": '"@context"' in t, "mirror": None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    sm = open(os.path.join(SITE, "sitemap.xml"), encoding="utf-8").read()
    urls = re.findall(r"<loc>(.*?)</loc>", sm)
    lastmod = dict(zip(urls, re.findall(r"<lastmod>(.*?)</lastmod>", sm) or [""] * len(urls)))

    rows, missing = [], []
    for u in urls:
        path = u.replace(BASE, "") or "/"
        fp = os.path.join(SITE, path.lstrip("/"))
        if path.endswith("/"):
            fp = os.path.join(fp, "index.html")
        elif not path.endswith(".html"):
            fp = fp + ".html"
        if not os.path.exists(fp):
            missing.append(path)
            continue
        m = page_meta(fp)
        md_rel = (path.rstrip("/") + "/index.md") if path.endswith("/") else path + ".md"
        m.update({"url": u, "path": path, "family": family(path),
                  "lastmod": lastmod.get(u, ""),
                  "mirror": md_rel if os.path.exists(os.path.join(SITE, md_rel.lstrip("/"))) else None})
        rows.append(m)

    by_family, by_lang = {}, {}
    for r in rows:
        by_family[r["family"]] = by_family.get(r["family"], 0) + 1
        by_lang[r["lang"]] = by_lang.get(r["lang"], 0) + 1

    print(f"sitemap {len(urls)} · 磁盘可解析 {len(rows)} · 缺失 {len(missing)}")
    print("按语言:", json.dumps(by_lang, ensure_ascii=False))
    print("按族:", json.dumps(dict(sorted(by_family.items(), key=lambda kv: -kv[1])), ensure_ascii=False))
    print("无 markdown 镜像:", sum(1 for r in rows if not r["mirror"]))
    print("无 JSON-LD:", sum(1 for r in rows if not r["has_ld"]))
    if missing:
        print("sitemap 里有但磁盘没有:", missing[:10])

    if a.check:
        return 1 if missing else 0

    out = os.path.join(WS, "08-execution", "tech",
                       f"url-inventory-{dt.date.today().isoformat()}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
               "site": BASE, "count": len(rows), "sitemap_count": len(urls),
               "by_lang": by_lang, "by_family": by_family,
               "missing_on_disk": missing, "pages": rows},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("→", out)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
