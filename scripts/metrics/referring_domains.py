#!/usr/bin/env python3
"""referring_domains.py — 引用域台账（Pod C 的核心结果指标）。

## 为什么需要
Pod C 的 KPI `C.referring_domains` 之前完全空着：没有 Ahrefs/Moz 之类的工具，
"有多少外链"只能靠感觉。但**外链是否真的存在是可以验证的事实**——
一个页面要么链到 anaricharge.com，要么没链。

## 做法
1. 发现（人/agent 用搜索或外联回复找候选页）→ `add <url>`
2. 复核（脚本抓页面，确认真的有指向我们的链接）→ 记录锚文本与日期
3. 去重按**域名**计数（一个站在多个页面链接只算 1 个引用域）
4. 定期 `verify` 全量复核（外链会消失，台账必须能反映失效）

## 用法
  python3 scripts/metrics/referring_domains.py add <url> [--note "来源说明"]
  python3 scripts/metrics/referring_domains.py verify
  python3 scripts/metrics/referring_domains.py report
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from urllib.parse import urlparse

WS = "/Users/kerrychu/anari-charge-website"
LEDGER = os.path.join(WS, "08-execution", "backlink", "referring-domains.json")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}
OUR_HOSTS = ("anaricharge.com", "www.anaricharge.com")
SAME_ORG = ("anariev.com", "www.anariev.com", "anarienergy.com", "www.anarienergy.com")


def load():
    if not os.path.exists(LEDGER):
        return {"_comment": "引用域台账。由 scripts/metrics/referring_domains.py 维护。", "rows": []}
    return json.load(open(LEDGER, encoding="utf-8"))


def save(d):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    json.dump(d, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")


def find_link(html, page_url):
    """返回 [(href, anchor)]，只保留指向我们站的外链。"""
    out = []
    for m in re.finditer(r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S | re.I):
        href, inner = m.group(1), m.group(2)
        if not re.search(r"anaricharge\.com", href, re.I):
            continue
        anchor = re.sub(r"<[^>]+>", "", inner)
        anchor = re.sub(r"\s+", " ", anchor).strip()[:120]
        out.append((href, anchor))
    return out


def check(url):
    """抓页面并判定：external / same_org / internal / no_link / unreachable。"""
    host = (urlparse(url).hostname or "").lower()
    if host in OUR_HOSTS:
        return {"kind": "internal", "note": "本站页面，不算引用域"}
    if host in SAME_ORG:
        return {"kind": "same_org", "note": "同公司姊妹站，单独统计不计入引用域"}
    try:
        html = fetch(url)
    except Exception as e:  # noqa: BLE001
        # 2026-11-14 修复：反爬拦截 ≠ 链接失效。
        # 实测 zenodo 的 DOI 记录页对脚本返回 403（浏览器可正常访问），
        # 旧逻辑把它判成 unreachable → status 从 active 掉出 → C.referring_domains 3→2，
        # 等于「用抓取失败冒充链接消失」。现在 403/429/451 一律记为 blocked，保留 active。
        code = None
        try:
            code = getattr(e, "code", None) or int(str(e).split("HTTP Error ")[1].split(":")[0])
        except Exception:  # noqa: BLE001
            code = None
        if code in (403, 429, 451):
            return {"kind": "blocked", "http": code,
                    "note": "反爬/限流 %s：抓取被拒，不代表链接失效，保留 active（需人工或浏览器复核）" % code}
        return {"kind": "unreachable", "note": "%s: %s" % (type(e).__name__, str(e)[:120])}
    links = find_link(html, url)
    if not links:
        return {"kind": "no_link", "note": "页面可访问但未找到指向 anaricharge.com 的 <a>"}
    href, anchor = links[0]
    rel = ""
    m = re.search(r'<a\s[^>]*href=["\']' + re.escape(href) + r'["\'][^>]*>', html, re.I)
    if m and re.search(r'rel=["\'][^"\']*nofollow', m.group(0), re.I):
        rel = "nofollow"
    return {"kind": "external", "href": href, "anchor": anchor, "rel": rel}


SURFACES = ("directory", "registry", "marketplace", "dataset", "repo",
            "wikidata", "social", "editorial", "partner", "unknown")


def cmd_add(url, note="", surface="unknown"):
    d = load()
    host = (urlparse(url).hostname or "").lower().lstrip("www.").replace("www.", "")
    base_host = host[4:] if host.startswith("www.") else host
    res = check(url)
    today = dt.date.today().isoformat()
    if d["rows"]:
        for r in d["rows"]:
            if r.get("page_url") == url:
                r.update(result=res, last_checked=today)
                save(d)
                print("已更新已存在条目：", url, "→", res["kind"])
                return 0
    d.setdefault("rows", []).append({
        "domain": base_host, "page_url": url, "note": note,
        "surface": surface if surface in SURFACES else "unknown",
        "result": res, "first_seen": today, "last_checked": today,
        "status": "active" if res["kind"] in ("external", "blocked") else res["kind"],
    })
    save(d)
    print("已加入台账：", url, "→", res["kind"], res.get("note") or res.get("anchor", ""))
    return 0


def cmd_verify():
    d = load()
    today = dt.date.today().isoformat()
    ok = bad = blocked = 0
    for r in d.get("rows") or []:
        # 只复核已有验证页面的行；pitched/pending 行还没有 page_url，跳过（别拿 KeyError 当失效）
        if not r.get("page_url"):
            print("  ⏳", r.get("domain"), "→", r.get("status"), "（尚未投稿成功，跳过复核）")
            continue
        res = check(r["page_url"])
        r["result"] = res
        r["last_checked"] = today
        r["status"] = "active" if res["kind"] in ("external", "blocked") else res["kind"]
        if res["kind"] == "external":
            ok += 1
            print("  ✅", r["page_url"])
        elif res["kind"] == "blocked":
            blocked += 1
            print("  ⚠️ ", r["page_url"], "→ 反爬拦截（保留 active，需人工/浏览器复核）")
        else:
            bad += 1
            print("  ❌", r["page_url"], "→", res["kind"], res.get("note", ""))
    save(d)
    print(f"\n复核完成：有效 {ok} / 反爬拦截 {blocked}（仍计 active） / 失效或非外链 {bad}")
    return 0


def cmd_report():
    d = load()
    rows = d.get("rows") or []
    active = [r for r in rows if r.get("status") == "active"]
    domains = sorted({r["domain"] for r in active})
    print("=== 引用域台账 ===")
    print(f"  条目 {len(rows)} | 有效 {len(active)} | **唯一引用域 {len(domains)}**")
    if domains:
        print("  域名：" + ", ".join(domains))

    # 按渠道类型算产出率 —— 这是"根据数据优化"的依据：
    # 哪类渠道真的产出引用域，就把预算/时间往哪类倾斜
    attempts = d.get("attempts") or []
    by = {}
    seen_targets = set()
    for a in attempts:
        s = a.get("surface", "unknown")
        by.setdefault(s, {"tried": 0, "won": 0})
        by[s]["tried"] += 1
        seen_targets.add(a.get("target"))
    # 有效引用域计入 won；若没有对应的 attempt 记录，则同时计一次 tried
    for r in active:
        s = r.get("surface", "unknown")
        by.setdefault(s, {"tried": 0, "won": 0})
        by[s]["won"] += 1
        if r.get("page_url") not in seen_targets and r.get("domain") not in seen_targets:
            by[s]["tried"] += 1
    if by:
        print("\n  渠道类型产出（tried=尝试数 / won=拿到引用域）")
        for s, v in sorted(by.items(), key=lambda x: -x[1]["won"]):
            rate = (v["won"] / v["tried"] * 100) if v["tried"] else 0
            print(f"    {s:12s} tried {v['tried']:>2} | won {v['won']:>2} | 命中率 {rate:>5.1f}%")
    for r in rows:
        if r.get("status") != "active":
            print(f"  ⚠️ 非有效：{r.get('page_url') or r.get('url') or r.get('target') or r}（{r.get('status')}）")
    return 0


def cmd_attempt(surface, target, result, note=""):
    """记录一次外链尝试（无论成没成）。

    只有把"失败"也记下来，才能算出渠道命中率；
    只记成功会让所有渠道看起来都是 100%。
    """
    d = load()
    d.setdefault("attempts", []).append({
        "date": dt.date.today().isoformat(), "surface": surface,
        "target": target, "result": result, "note": note,
    })
    save(d)
    print(f"已记录尝试：{surface} / {target} → {result}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["add", "verify", "report", "attempt"])
    ap.add_argument("url", nargs="?")
    ap.add_argument("--note", default="")
    ap.add_argument("--surface", default="unknown",
                    help="渠道类型: " + "/".join(SURFACES))
    a = ap.parse_args()
    if a.cmd == "add":
        if not a.url:
            raise SystemExit("用法: add <url> [--note ...]")
        return cmd_add(a.url, a.note, a.surface)
    if a.cmd == "attempt":
        if not (a.url and a.note):
            raise SystemExit("用法: attempt <目标> --note '<result> | 说明'")
        return cmd_attempt(a.surface, a.url, a.note)
    if a.cmd == "verify":
        return cmd_verify()
    return cmd_report()


if __name__ == "__main__":
    sys.exit(main())
