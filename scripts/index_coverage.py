#!/usr/bin/env python3
"""全站索引覆盖审计（GSC URL Inspection API）。

用法:
  curl -sL https://anaricharge.com/sitemap.xml -o /tmp/sitemap.xml
  python3 scripts/index_coverage.py --sitemap /tmp/sitemap.xml --out 08-execution/index-coverage-YYYYMMDD.json

配额：URL Inspection API 2000/天，站点 119 URL，安全。
只读凭证；不回写。
"""
import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from gsc_pull import access_token  # noqa: E402

SITE = "sc-domain:anaricharge.com"
ENDPOINT = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"


def inspect(url, at):
    body = json.dumps({"inspectionUrl": url, "siteUrl": SITE}).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Authorization": "Bearer " + at, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.load(r).get("inspectionResult", {})
    idx = res.get("indexStatusResult", {}) or {}
    return {
        "url": url,
        "verdict": idx.get("verdict"),
        "coverage": idx.get("coverageState"),
        "indexingState": idx.get("indexingState"),
        "pageFetch": idx.get("pageFetchState"),
        "robots": idx.get("robotsTxtState"),
        "lastCrawl": idx.get("lastCrawlTime"),
        "canonical": idx.get("googleCanonical"),
        "userCanonical": idx.get("userCanonical"),
        "sitemaps": idx.get("sitemap"),
        "referringUrls": len(idx.get("referringUrls") or []),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sitemap", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--scope", default="partial", choices=["full", "partial", "sample"], help="本次检查的范围；飞轮只信 full")
    ap.add_argument("--workers", type=int, default=8, help="并发数（默认 8）")
    a = ap.parse_args()

    xml = open(a.sitemap, encoding="utf-8", errors="replace").read()
    urls = re.findall(r"<loc>([^<]+)</loc>", xml)
    urls = [u.strip().replace("http://", "https://") for u in urls]
    seen, ordered = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    if a.limit:
        ordered = ordered[:a.limit]

    at = access_token()
    rows, errors = [], []
    t0 = time.time()

    def one(u):
        """单 URL 检查（带 429 退避）。返回 (row|None, error|None)。"""
        for attempt in range(3):
            try:
                return inspect(u, at), None
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(8)
                    continue
                return None, {"url": u, "error": "HTTP %s" % e.code}
            except Exception as e:  # noqa: BLE001
                if attempt == 2:
                    return None, {"url": u, "error": "%s: %s" % (type(e).__name__, str(e)[:160])}
                time.sleep(2)
        return None, {"url": u, "error": "retries exhausted"}

    # 2026-11-07：串行版每个 URL 约 7.5s（API 延迟 + 礼貌限速），151 URL 要 19 分钟，
    # 导致这个最有价值的收录 KPI 根本没法每日跑。改为并发（默认 8），保持退避逻辑不变。
    from concurrent.futures import ThreadPoolExecutor, as_completed
    done = 0
    with ThreadPoolExecutor(max_workers=max(1, a.workers)) as ex:
        futs = {ex.submit(one, u): u for u in ordered}
        for fut in as_completed(futs):
            row, err = fut.result()
            if row:
                rows.append(row)
            if err:
                errors.append(err)
            done += 1
            if done % 20 == 0:
                print("  ...%d/%d  (%.0fs)" % (done, len(ordered), time.time() - t0), flush=True)

    def count(key):
        c = {}
        for r in rows:
            c[r.get(key)] = c.get(r.get(key), 0) + 1
        return c

    out = {
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "site": SITE,
        "sitemap_urls": len(ordered),
        "inspected": len(rows),
        "scope": a.scope,
        "errors": errors,
        "verdict_dist": count("verdict"),
        "indexing_state_dist": count("indexingState"),
        "page_fetch_dist": count("pageFetch"),
        "coverage_dist": count("coverage"),
        "not_indexed": [r for r in rows if r.get("verdict") != "PASS"],
        "rows": rows,
    }
    json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=2)
    print("\nWROTE", a.out)
    print("inspected:", len(rows), "errors:", len(errors))
    print("verdict:", out["verdict_dist"])
    print("coverage:", out["coverage_dist"])
    ni = out["not_indexed"]
    if ni:
        print("\nNOT INDEXED (%d):" % len(ni))
        for r in ni[:40]:
            print("  %-8s %-32s %s" % (r.get("verdict"), r.get("coverage"), r["url"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
