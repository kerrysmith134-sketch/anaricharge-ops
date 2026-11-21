#!/usr/bin/env python3
"""email_enrichment.py — 外联目标邮箱挖掘：公开优先，付费兜底。

配套 skill: .agents/skills/email-enrichment/SKILL.md

用法:
  python3 scripts/outbound/email_enrichment.py public <domain>       # 只跑公开层
  python3 scripts/outbound/email_enrichment.py get <domain>          # 公开→付费兜底
  python3 scripts/outbound/email_enrichment.py batch                # 对台账全部目标跑公开层
  python3 scripts/outbound/email_enrichment.py report               # 台账邮箱覆盖率

凭证（付费层，可选）：.secrets/enrichment.json {"hunter":"…","apollo":"…","snovio":"…"}
省着用：命中缓存不调用；公开层拿到就不调用付费；每次调用计入 credits_used。
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

WS = "/Users/kerrychu/anari-charge-website"
OUT = os.path.join(WS, "08-execution", "marketing-outbound")
LEDGER = os.path.join(OUT, "media-targets-20261107.json")
CACHE = os.path.join(OUT, "enrichment-cache.json")
SECRETS = os.path.join(WS, ".secrets", "enrichment.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# 按命中概率排序；找到 ≥1 个优先角色箱就提前结束该域名
PATHS = ["", "/contact", "/contact-us", "/about", "/write-for-us", "/contribute",
         "/submit", "/advertise", "/press", "/media", "/team", "/about-us", "/newsroom"]

PRIORITY = ["editorial", "editor", "news", "tips", "tip", "press", "media",
            "advertise", "submit", "contribute", "partners", "contact", "info", "hello", "team"]
BLOCK = ["noreply", "no-reply", "donotreply", "unsubscribe", "abuse", "privacy",
         "jobs", "careers", "support", "webmaster", "postmaster", "bounce"]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def load_json(p, default):
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return default
    return default


def fetch(url, timeout=6):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "text/html,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return ""


def public_scan(domain):
    """第 1 层：并发抓官网常见联系/投稿页，抽 mailto 与可见邮箱。"""
    from concurrent.futures import ThreadPoolExecutor
    base = "https://" + domain
    found = {}

    def grab(path):
        return path, fetch(base + path)

    with ThreadPoolExecutor(max_workers=6) as ex:
        for path, html in ex.map(grab, PATHS):
            if not html:
                continue
            for m in re.finditer(r'mailto:([^"\'>\s?&]+)', html):
                addr = urllib.parse.unquote(m.group(1)).strip().lower()
                if domain in addr and addr not in found:
                    found[addr] = {"page": path or "/", "how": "mailto"}
            for m in EMAIL_RE.finditer(html):
                addr = m.group(0).lower().rstrip(".")
                if domain in addr and addr not in found:
                    found[addr] = {"page": path or "/", "how": "text"}

    def score(a):
        local = a.split("@")[0]
        if any(b in local for b in BLOCK):
            return 999
        for i, p in enumerate(PRIORITY):
            if local.startswith(p):
                return i
        return 100

    out = []
    for addr, meta in sorted(found.items(), key=lambda kv: score(kv[0])):
        s = score(addr)
        if s == 999:
            continue
        out.append({"email": addr, "source": "public_" + meta["how"],
                    "page": meta["page"],
                    "confidence": "high" if s < 10 else "medium"})
    return out


def _get(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/json"} | (headers or {}))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return {"_http_error": e.code, "_body": e.read()[:300].decode("utf-8", "replace")}
    except Exception as e:  # noqa: BLE001
        return {"_error": str(e)[:200]}


def provider_budget():
    """查询三家余额。省着用的第一步：没额度就别调用。"""
    creds = load_json(SECRETS, {})
    out = {}
    if creds.get("hunter"):
        d = _get("https://api.hunter.io/v2/account?api_key=" + creds["hunter"])
        c = ((d.get("data") or {}).get("requests") or {}).get("credits") or {}
        out["hunter"] = {"remaining": c.get("remaining"), "plan": (d.get("data") or {}).get("plan_name"),
                         "reset": (d.get("data") or {}).get("reset_date")}
    if creds.get("snovio"):
        sn = creds["snovio"]
        tok = urllib.request.Request(
            "https://api.snov.io/v1/oauth/access_token",
            data=urllib.parse.urlencode({"grant_type": "client_credentials",
                                         "client_id": sn["a"],
                                         "client_secret": sn["b"]}).encode(),
            headers={"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(tok, timeout=25) as r:
                at = json.loads(r.read().decode()).get("access_token")
            b = _get("https://api.snov.io/v1/get-balance?access_token=" + str(at))
            out["snovio"] = {"remaining": (b.get("data") or {}).get("balance")}
        except Exception as e:  # noqa: BLE001
            out["snovio"] = {"error": str(e)[:120]}
    if creds.get("apollo"):
        out["apollo"] = {"note": "无公开余额接口；调用失败会返回 insufficient credits"}
    return out


def browser_scan(domain, paths=None, settle=3.5):
    """第 1.5 层：用真实浏览器抓（能过 Cloudflare 与 JS 渲染，免费）。

    与 public_scan 的区别：走用户真实 Chrome（带登录态/真实指纹），
    能打开被 403 挡住的站点。代价是慢（每页 ~4s），所以只对公开层失败的域名用。

    ⚠️ 增量落盘：每处理完一个域名就写回缓存，避免某个域名卡住丢掉全部结果。
    """
    import subprocess
    import time
    sys.path.insert(0, os.path.join(WS, "scripts", "browser"))
    from wb import WB  # noqa: E402

    # 实测：只跑 /contact /about /advertise /press 会漏掉不少站点。
    # 加上 /contact-us /about-us /team /staff /write-for-us /contribute /editorial 后，
    # eepower.com 这类站点的 editorial@ 才被抓到。默认就用扩展后的列表。
    # 2026-11-07：实测不少站点 /contact 是 301（带尾斜杠或跳 www），
    # 直接抓会空手而归。所以路径同时覆盖尾斜杠写法，并对 www/裸域各试一次。
    base = ["/contact", "/about", "/write-for-us", "/contribute"]
    paths = paths or []
    if not paths:
        for b in base:
            paths += [b, b + "/"]
        paths += ["/contact-us", "/about-us", "/team", "/staff", "/editorial",
                  "/advertise", "/press", "/advertise/"]
    subprocess.run(["osascript", "-e", 'tell application "Google Chrome" to activate'],
                   capture_output=True)
    time.sleep(1)
    wb = WB(session="enrich")
    found = []
    try:
        for path in paths:
            try:
                wb.nav("https://" + domain + path, new_tab=False)
                time.sleep(settle)
            except Exception:  # noqa: BLE001
                continue
            try:
                raw = wb.eval(
                "const ms=Array.from(document.querySelectorAll('a[href^=\"mailto:\"]'))"
                ".map(a=>a.getAttribute('href').replace('mailto:','').split('?')[0].trim().toLowerCase());"
                "const txt=(document.body&&document.body.textContent)||'';"
                "const re=/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}/g;"
                "const m=(txt.match(re)||[]).map(s=>s.toLowerCase());"
                "return JSON.stringify({mailto:ms,text:m.slice(0,50)});")
            except Exception:  # noqa: BLE001
                continue
            try:
                d = json.loads(raw)
            except Exception:  # noqa: BLE001
                continue
            cand = [e for e in (d.get("mailto") or []) + (d.get("text") or [])
                    if domain.replace("www.", "") in e]
            cand = [e for e in cand
                    if not e.endswith((".png", ".jpg", ".gif", ".webp", ".svg"))
                    and e.count("@") == 1 and not e.endswith(".")]
            if cand:
                opts = list(dict.fromkeys(cand))
                found = [{"email": e, "source": "browser_" + path.strip("/"),
                          "page": path, "confidence": "high"} for e in opts[:4]]
                break
    finally:
        try:
            wb.close_session()
        except Exception:  # noqa: BLE001
            pass

    cache = load_json(CACHE, {})
    prev = cache.get(domain) or {}
    entry = {"domain": domain,
             "results": found or prev.get("results") or [],
             "credits_used": 0, "provider_calls": ["browser"],
             "checked_at": time.strftime("%Y-%m-%d")}
    cache[domain] = entry
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return entry


def browser_batch(domains):
    """逐个域名跑浏览器层，每个域名立刻落盘。"""
    out = {}
    for i, dom in enumerate(domains, 1):
        e = browser_scan(dom)
        out[dom] = e["results"]
        top = (e["results"] or [{}])[0]
        print(f"  [{i}/{len(domains)}] {dom:34s} {top.get('email') or '（未找到）'}", flush=True)
    return out


def paid_lookup(domain):
    """第 3 层：付费 API 兜底。调用前先看余额，没额度直接返回原因，不浪费请求。"""
    creds = load_json(SECRETS, {})
    budget = provider_budget()
    used, notes = [], []

    h = budget.get("hunter") or {}
    if creds.get("hunter") and (h.get("remaining") or 0) > 0:
        d = _get("https://api.hunter.io/v2/domain-search?domain=%s&api_key=%s&limit=10"
                 % (domain, creds["hunter"]))
        used.append("hunter")
        emails = (d.get("data") or {}).get("emails") or []
        good = [e for e in emails if (e.get("confidence") or 0) >= 70]
        if good:
            best = max(good, key=lambda e: e.get("confidence") or 0)
            return [{"email": best.get("value"), "source": "hunter",
                     "confidence": "high" if (best.get("confidence") or 0) >= 90 else "medium",
                     "position": (best.get("position") or "")[:40]}], used
    else:
        notes.append("hunter: 无剩余额度 %s" % (h or "未配置"))

    sn = budget.get("snovio") or {}
    try:
        if creds.get("snovio") and float(sn.get("remaining") or 0) > 0:
            notes.append("snovio: 有余额但接口待实现")
        else:
            notes.append("snovio: 余额 %s" % (sn.get("remaining") or 0))
    except (TypeError, ValueError):
        notes.append("snovio: 余额未知")

    notes.append("apollo: 见 paid_lookup 备注（当前 masterkey 报 insufficient credits）")
    return [], used + notes


def enrich(domain, allow_paid=True):
    cache = load_json(CACHE, {})
    if domain in cache and cache[domain].get("results"):
        return dict(cache[domain], cached=True)
    res = public_scan(domain)
    used = []
    if not res and allow_paid:
        res, used = paid_lookup(domain)
    entry = {"domain": domain, "results": res,
             "credits_used": len([u for u in used if "error" not in u and "skipped" not in u]),
             "provider_calls": used,
             "checked_at": time.strftime("%Y-%m-%d")}
    cache[domain] = entry
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return entry


def batch_public():
    from concurrent.futures import ThreadPoolExecutor
    tg = load_json(LEDGER, [])
    results = []

    def one(t):
        d = t.get("domain")
        if not d:
            return None
        return (t, enrich(d, allow_paid=False))

    with ThreadPoolExecutor(max_workers=5) as ex:
        pairs = [x for x in ex.map(one, tg) if x]
    for t, e in pairs:
        d = t.get("domain")
        top = e["results"][0] if e["results"] else None
        results.append({"name": t.get("name"), "domain": d,
                        "email": (top or {}).get("email", ""),
                        "source": (top or {}).get("source", ""),
                        "page": (top or {}).get("page", ""),
                        "confidence": (top or {}).get("confidence", ""),
                        "all_found": [r["email"] for r in e["results"][:5]]})
        print(f"  {t.get('name','')[:26]:28s} {results[-1]['email'] or '（未找到）':32s} {results[-1]['source']}")
    json.dump(results, open(os.path.join(OUT, "enrichment-public-20261107.json"),
                            "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    found = sum(1 for r in results if r["email"])
    print(f"\n公开层命中 {found}/{len(results)}")
    return results


def report():
    tg = load_json(LEDGER, [])
    cache = load_json(CACHE, {})
    rows = []
    for t in tg:
        c = cache.get(t.get("domain") or "", {})
        top = (c.get("results") or [{}])[0] if c.get("results") else {}
        rows.append({"name": t.get("name"), "domain": t.get("domain"),
                     "ledger_email": t.get("email", ""),
                     "found_email": top.get("email", ""),
                     "source": top.get("source", ""),
                     "channel": t.get("channel", "")})
    have = sum(1 for r in rows if r["ledger_email"] or r["found_email"])
    print(json.dumps({"total": len(rows), "with_email": have,
                      "form_only": len(rows) - have, "rows": rows},
                     ensure_ascii=False, indent=1))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["public", "get", "batch", "browser", "report"])
    ap.add_argument("domain", nargs="?", help="单域名，或 browser 命令用逗号分隔的域名列表")
    ap.add_argument("--no-paid", action="store_true")
    a = ap.parse_args()
    if a.cmd == "public":
        print(json.dumps(enrich(a.domain, allow_paid=False), ensure_ascii=False, indent=1))
    elif a.cmd == "get":
        print(json.dumps(enrich(a.domain, allow_paid=not a.no_paid), ensure_ascii=False, indent=1))
    elif a.cmd == "batch":
        batch_public()
    elif a.cmd == "browser":
        doms = a.domain.split(",") if a.domain else []
        if not doms:
            raise SystemExit("用法: browser <domain1,domain2,...>")
        browser_batch(doms)
    else:
        report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
