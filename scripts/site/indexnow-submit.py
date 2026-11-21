#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""indexnow-submit.py — 把 sitemap 里的 URL 提交给 IndexNow（Bing/Yandex 等）

为什么要有这个脚本：
  之前每次发版都是手敲 curl，容易漏、也不可复核。索引收录是流水线的一环
  （飞轮 A.index_coverage_pct 的前提），必须可重复执行。

用法：
  python3 scripts/site/indexnow-submit.py                    # 提交 sitemap 全部 URL
  python3 scripts/site/indexnow-submit.py --filter /ru/cases # 只提交包含该子串的
  python3 scripts/site/indexnow-submit.py --limit 50         # 只提交前 N 条
  python3 scripts/site/indexnow-submit.py --dry              # 只打印，不发送

说明：
  - IndexNow 单次最多 10000 URL；本脚本按 10000 分批
  - key 文件名即 key 值，必须在站点根可访问（站点已有两个 key 文件）
  - 返回 200/202 视为接受；4xx 打印响应体便于排查
"""
import argparse
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, "..", "..", "06-site/anari-new-site/site"))
SITEMAP = os.path.join(SITE, "sitemap.xml")
ENDPOINT = "https://api.indexnow.org/indexnow"
HOST = "www.anaricharge.com"


def find_key():
    for name in sorted(os.listdir(SITE)):
        if re.fullmatch(r"[0-9a-f]{32}\.txt", name):
            return name[:-4]
    raise SystemExit("站点根找不到 IndexNow key 文件（32 位 hex .txt）")


def sitemap_urls():
    xml = open(SITEMAP, encoding="utf-8").read()
    return re.findall(r"<loc>(.*?)</loc>", xml)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter", default=None, help="只提交路径包含该子串的 URL")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    key = find_key()
    urls = sitemap_urls()
    if a.filter:
        urls = [u for u in urls if a.filter in u]
    if a.limit:
        urls = urls[: a.limit]

    print(f"key={key}  待提交 {len(urls)} 个 URL（sitemap 共 {len(sitemap_urls())}）")
    if a.dry:
        for u in urls[:20]:
            print("  ", u)
        if len(urls) > 20:
            print(f"   …还有 {len(urls) - 20} 条")
        return

    ok = 0
    for i in range(0, len(urls), 10000):
        batch = urls[i : i + 10000]
        body = json.dumps({
            "host": HOST,
            "key": key,
            "keyLocation": f"https://{HOST}/{key}.txt",
            "urlList": batch,
        }).encode()
        req = urllib.request.Request(
            ENDPOINT, data=body,
            headers={"Content-Type": "application/json; charset=utf-8",
                     "User-Agent": "anari-ops-indexnow/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                code = r.status
                detail = r.read(200).decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            code = e.code
            detail = e.read(300).decode("utf-8", "ignore")
        except Exception as e:  # 网络问题
            code, detail = 0, str(e)[:200]
        print(f"  批次 {i // 10000 + 1}: HTTP {code} {detail[:120]}")
        if code in (200, 202):
            ok += len(batch)

    print(f"\n提交完成：{ok}/{len(urls)} 个 URL 被接受")
    if ok < len(urls):
        sys.exit(1)


if __name__ == "__main__":
    main()
