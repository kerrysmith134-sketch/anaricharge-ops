#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""browser-audit-local.py — 本地复现 .github/workflows/browser-audit.yml 的三项真实浏览器验收

## 为什么需要
审计 8.3 要求 Playwright / axe-core / Lighthouse 进 CI。CI 在 GitHub runner 上跑，
本地如果只能在线上看数字，失败就没法复盘。这个脚本用**仓库自带的 dev-server +
本机已有 headless Chrome** 在本地跑同样的三项，输出可对比的 JSON：
  08-execution/tech/browser-audit-<date>.json

## 三项（与 workflow 一一对应）
  ① Playwright 可用性：`npx --yes @playwright/test --version`
  ② axe-core 可访问性：playwright + axe-core（**同一份仓库脚本**
     `06-site/anari-new-site/scripts/tools/browser-audit.js`，避免"本地和 CI 两套逻辑"）
     本机装不了 playwright 时回退：headless Chrome + 简单 DOM 检查（报告 method 会写明）
  ③ Lighthouse：`npx --yes lighthouse`，对本地起服务的 /、/inquiry、/markets/ 打分
     本机跑不了 lighthouse 时回退：headless Chrome 的 performance 代理指标（明确标注）

阈值（与 CI 一致；低于阈值只警示，脚本退出码仍为 0）：
  a11y Critical = 0；Lighthouse performance ≥60 / accessibility ≥90 / SEO ≥90

## 用法
  cd /Users/kerrychu/anari-charge-website
  python3 scripts/tools/browser-audit-local.py
  python3 scripts/tools/browser-audit-local.py --base http://127.0.0.1:7188   # 用已在跑的服务
  python3 scripts/tools/browser-audit-local.py --date 2026-11-12 --keep-server # 调试用

浏览器卫生（R10）：headless Chrome 用独立 --user-data-dir，不碰用户 Chrome 配置、不开标签。
"""
import argparse
import html as htmllib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = os.path.join(WS, "06-site", "anari-new-site")
SITE = os.path.join(REPO, "site")
TECH = os.path.join(WS, "08-execution", "tech")
DEPS = "/tmp/audit-deps"          # 与 CI 的 /tmp/audit-deps 同构（npm --prefix 安装）
NPM_CACHE = "/tmp/anari-npm-cache"
CHROME = os.environ.get("CHROME_PATH") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEFAULT_PAGES = "/,/inquiry,/markets/"
THRESHOLDS = {"axe_critical": 0, "performance": 60, "accessibility": 90, "seo": 90}


def log(msg):
    print(f"[browser-audit-local] {msg}")


def warn(msg):
    print(f"[browser-audit-local] ⚠ {msg}")


def run(cmd, timeout=300, cwd=None, env=None):
    e = dict(os.environ)
    e["npm_config_cache"] = NPM_CACHE
    e.setdefault("PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD", "1")
    if env:
        e.update(env)
    try:
        return subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, "", f"timeout {timeout}s")


def chrome_version():
    if not os.path.exists(CHROME):
        return None
    r = run([CHROME, "--version"], timeout=20)
    return (r.stdout or r.stderr).strip() or None


def free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def wait_http(url, timeout=25):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def start_server(port):
    proc = subprocess.Popen(
        ["node", "scripts/dev-server.js", "--port", str(port), "--host", "127.0.0.1"],
        cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    base = f"http://127.0.0.1:{port}"
    if not wait_http(base + "/"):
        err = ""
        try:
            proc.terminate()
            err = (proc.stderr.read() or "")[-300:]
        except Exception:
            pass
        raise RuntimeError(f"dev-server 未就绪（{base}）：{err}")
    return proc, base


# ---------------------------------------------------------------- ① Playwright
def playwright_availability():
    r = run(["npx", "--yes", "@playwright/test", "--version"], timeout=300)
    text = (r.stdout or r.stderr).strip().splitlines()
    version = text[-1].strip() if text else ""
    ok = r.returncode == 0 and bool(re.search(r"\d+\.\d+", version))
    return {"ok": ok, "version": version if ok else None, "raw": (r.stdout or r.stderr).strip()[-300:]}


# ---------------------------------------------------------------- ② axe-core
def ensure_audit_deps():
    """npm --prefix /tmp/audit-deps 装 playwright + axe-core（不下载 playwright 浏览器）。"""
    need = os.path.join(DEPS, "node_modules", "playwright")
    axe = os.path.join(DEPS, "node_modules", "axe-core", "axe.min.js")
    if os.path.exists(need) and os.path.exists(axe):
        return True, "already installed"
    os.makedirs(DEPS, exist_ok=True)
    r = run(["npm", "install", "--prefix", DEPS, "--no-audit", "--no-fund", "playwright", "axe-core"], timeout=300)
    ok = r.returncode == 0 and os.path.exists(need) and os.path.exists(axe)
    detail = (r.stdout or "").strip().splitlines()[-1:] or [(r.stderr or "").strip()[-200:]]
    return ok, str(detail)


def run_axe(base, pages):
    """调用仓库里的同一份 CI 脚本（scripts/tools/browser-audit.js）。"""
    out = os.path.join(tempfile.mkdtemp(prefix="anari-axe-"), "axe.json")
    script = os.path.join(REPO, "scripts", "tools", "browser-audit.js")
    axe_src = os.path.join(DEPS, "node_modules", "axe-core", "axe.min.js")
    r = run(
        ["node", script, "--base", base, "--pages", pages, "--axe", axe_src, "--out", out],
        timeout=240,
        env={"NODE_PATH": os.path.join(DEPS, "node_modules")},
    )
    print((r.stdout or "").strip()[-1500:])
    if r.returncode not in (0,) or not os.path.exists(out):
        raise RuntimeError(f"browser-audit.js 失败 rc={r.returncode}: {(r.stderr or r.stdout).strip()[-400:]}")
    return json.load(open(out, encoding="utf-8"))


# ---------------------------------------------------------------- headless Chrome 兜底
HARNESS = r"""<!doctype html><meta charset="utf-8"><title>browser-audit harness</title>
<body><pre id="result">pending</pre>
<script>
(function () {
  var target = new URLSearchParams(location.search).get('target') || '/';
  var f = document.createElement('iframe');
  f.style.cssText = 'width:1280px;height:900px;border:0';
  f.src = target;
  var finished = false;
  function finish(obj) {
    if (finished) return; finished = true;
    document.getElementById('result').textContent = JSON.stringify(obj);
  }
  function run() {
    var d, w;
    try { d = f.contentDocument; w = f.contentWindow; } catch (e) { finish({ error: 'cross-origin: ' + e }); return; }
    if (!d || !d.documentElement) { finish({ error: 'no iframe document' }); return; }
    function txt(el) { return ((el && el.textContent) || '').replace(/\s+/g, ' ').trim(); }
    function meta(name) {
      var m = d.querySelector('meta[name="' + name + '"]');
      return m && m.content ? m.content : '';
    }
    function accName(el) {
      var a = el.getAttribute('aria-label'); if (a) return a.trim();
      var lb = el.getAttribute('aria-labelledby');
      if (lb) {
        return lb.split(/\s+/).map(function (id) { var e = d.getElementById(id); return e ? txt(e) : ''; }).join(' ').trim();
      }
      if (el.tagName === 'IMG') return (el.getAttribute('alt') || '').trim();
      if (el.id) { var l = d.querySelector('label[for="' + el.id.replace(/"/g, '\\"') + '"]'); if (l) return txt(l); }
      var pl = el.closest && el.closest('label'); if (pl) return txt(pl);
      var t = el.getAttribute('title'); if (t) return t.trim();
      if (el.tagName === 'A' || el.tagName === 'BUTTON') return txt(el);
      var ph = el.getAttribute('placeholder'); if (ph) return ph.trim();
      return '';
    }
    var hs = [].slice.call(d.querySelectorAll('h1,h2,h3,h4,h5,h6')).map(function (h) { return +h.tagName[1]; });
    var skips = [];
    for (var i = 1; i < hs.length; i++) if (hs[i] - hs[i - 1] > 1) skips.push(hs[i - 1] + '→' + hs[i]);
    var seen = {}, dups = [];
    [].forEach.call(d.querySelectorAll('[id]'), function (e) { if (seen[e.id]) dups.push(e.id); seen[e.id] = 1; });
    var imgs = [].slice.call(d.querySelectorAll('img'));
    var links = [].slice.call(d.querySelectorAll('a[href]'));
    var inputs = [].slice.call(d.querySelectorAll('input:not([type=hidden]),select,textarea'));
    var btns = [].slice.call(d.querySelectorAll('button,[role=button]'));
    var perf = w.performance || {};
    var nav = perf.getEntriesByType ? (perf.getEntriesByType('navigation')[0] || null) : null;
    var res = perf.getEntriesByType ? perf.getEntriesByType('resource') : [];
    var bytes = res.reduce(function (s, r) { return s + (r.transferSize || 0); }, 0);
    finish({
      target: target,
      title: d.title || '',
      titleLen: (d.title || '').length,
      metaDescLen: meta('description').length,
      lang: d.documentElement.lang || '',
      viewport: meta('viewport'),
      h1Count: d.querySelectorAll('h1').length,
      headingOrderSkips: skips.slice(0, 10),
      imgTotal: imgs.length,
      imgNoAlt: imgs.filter(function (i) { return !i.hasAttribute('alt'); }).length,
      linksTotal: links.length,
      linksNoName: links.filter(function (a) { return !accName(a); }).length,
      inputsTotal: inputs.length,
      inputsNoName: inputs.filter(function (i) { return !accName(i); }).length,
      buttonsTotal: btns.length,
      buttonsNoName: btns.filter(function (b) { return !accName(b); }).length,
      mainCount: d.querySelectorAll('main').length,
      navCount: d.querySelectorAll('nav').length,
      footerCount: d.querySelectorAll('footer').length,
      dupIds: dups.slice(0, 10),
      domNodes: d.querySelectorAll('*').length,
      perfProxy: {
        ttfbMs: nav ? Math.round(nav.responseStart) : null,
        loadMs: nav ? Math.round(nav.loadEventEnd) : null,
        resourceCount: res.length,
        transferBytes: bytes
      }
    });
  }
  f.onload = function () { setTimeout(function () { try { run(); } catch (e) { finish({ error: String(e) }); } }, 1200); };
  document.body.appendChild(f);
  setTimeout(function () { try { run(); } catch (e) { finish({ error: String(e) }); } }, 9000);
})();
</script>
"""


def dom_checks(base, pages):
    """headless Chrome + 同源 iframe harness：简单 DOM / a11y 检查 + perf 代理指标。"""
    harness_name = ".browser-audit-harness.html"
    harness_path = os.path.join(SITE, harness_name)
    profile = tempfile.mkdtemp(prefix="anari-audit-chrome-")
    results = []
    try:
        with open(harness_path, "w", encoding="utf-8") as fh:
            fh.write(HARNESS)
        for page in pages:
            url = f"{base}/{harness_name}?target={urllib.parse.quote(page)}"
            cmd = [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
                   "--disable-dev-shm-usage", "--disable-crash-reporter", "--hide-scrollbars",
                   "--no-first-run", "--no-default-browser-check",
                   "--user-data-dir=" + profile, "--virtual-time-budget=12000",
                   "--dump-dom", url]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            m = re.search(r'<pre id="result">([\s\S]*?)</pre>', r.stdout or "")
            rec = {"path": page}
            if not m:
                rec["error"] = f"harness 无输出（rc={r.returncode}）"
            else:
                try:
                    rec.update(json.loads(htmllib.unescape(m.group(1))))
                except Exception as e:  # noqa: BLE001
                    rec["error"] = f"结果解析失败: {e}"
            results.append(rec)
            log(f"DOM checks {page}: " + ("OK" if "error" not in rec else rec["error"]))
    finally:
        try:
            os.remove(harness_path)
        except OSError:
            pass
        shutil.rmtree(profile, ignore_errors=True)
    return results


# ---------------------------------------------------------------- ③ Lighthouse
def run_lighthouse(base, pages):
    outdir = tempfile.mkdtemp(prefix="anari-lh-")
    results, warnings = {}, []
    for page in pages:
        name = "home" if page == "/" else re.sub(r"[^a-z0-9]+", "-", page.strip("/").lower())
        out = os.path.join(outdir, name + ".json")
        log(f"Lighthouse {page} …（首次会 npx 下载，约 10–40s）")
        r = run(
            ["npx", "--yes", "lighthouse", base + page,
             "--output=json", "--output-path=" + out,
             "--only-categories=performance,accessibility,seo",
             "--chrome-flags=--headless=new --no-sandbox --disable-dev-shm-usage",
             "--quiet"],
            timeout=360,
            env={"CHROME_PATH": CHROME, "npm_config_cache": NPM_CACHE},
        )
        if r.returncode != 0 or not os.path.exists(out):
            warnings.append(f"Lighthouse {page} 失败 rc={r.returncode}: {(r.stderr or r.stdout).strip()[-200:]}")
            results[page] = {"error": (r.stderr or r.stdout).strip()[-300:]}
            continue
        d = json.load(open(out, encoding="utf-8"))
        cats = d.get("categories", {})
        def sc(k):
            v = cats.get(k, {}).get("score")
            return None if v is None else round(v * 100)
        results[page] = {"performance": sc("performance"), "accessibility": sc("accessibility"),
                         "seo": sc("seo"), "lighthouseVersion": d.get("lighthouseVersion"),
                         "finalUrl": d.get("finalUrl")}
        log(f"  → perf {results[page]['performance']} · a11y {results[page]['accessibility']} · seo {results[page]['seo']}")
    shutil.rmtree(outdir, ignore_errors=True)
    return results, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="", help="已在跑的服务 URL（默认自动起 dev-server）")
    ap.add_argument("--port", type=int, default=0, help="自动起服务时用这个端口（默认随机）")
    ap.add_argument("--pages", default=DEFAULT_PAGES)
    ap.add_argument("--date", default=time.strftime("%Y-%m-%d"))
    ap.add_argument("--out", default="")
    ap.add_argument("--keep-server", action="store_true")
    a = ap.parse_args()

    pages = [p.strip() for p in a.pages.split(",") if p.strip()]
    out_path = a.out or os.path.join(TECH, f"browser-audit-{a.date}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    result = {
        "date": a.date,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "pages": pages,
        "method": {},
        "thresholds": THRESHOLDS,
        "errors": [],
    }

    result["method"]["chrome"] = chrome_version() or f"未找到 Chrome（{CHROME}）"
    result["method"]["node"] = (run(["node", "--version"]).stdout or "").strip()

    # ① Playwright 可用性
    pw = playwright_availability()
    result["playwright"] = pw
    result["method"]["playwright_check"] = "npx --yes @playwright/test --version"
    log(f"① Playwright: {pw['version'] if pw['ok'] else '不可用'}")

    server = None
    try:
        if a.base:
            base = a.base.rstrip("/")
            if not wait_http(base + "/"):
                raise RuntimeError(f"指定 base 不可达：{base}")
        else:
            port = a.port or free_port()
            server, base = start_server(port)
        result["base"] = base
        result["method"]["server"] = f"node scripts/dev-server.js（{base}）"
        log(f"本地服务：{base}")

        # ② axe（playwright+axe）→ 失败则 headless Chrome DOM 检查兜底
        a11y = {"engine": None, "pages": [], "critical": None, "serious": None, "fallback": False}
        try:
            if not pw["ok"]:
                raise RuntimeError("playwright 不可用")
            ok, detail = ensure_audit_deps()
            if not ok:
                raise RuntimeError(f"playwright/axe-core 依赖装不上：{detail}")
            axe = run_axe(base, ",".join(pages))
            a11y = {
                "engine": "playwright+axe-core（" + str(axe.get("engine")) + "）",
                "axeVersion": axe.get("axeVersion"),
                "pages": axe.get("pages", []),
                "critical": sum(p.get("counts", {}).get("critical", 0) for p in axe.get("pages", [])),
                "serious": sum(p.get("counts", {}).get("serious", 0) for p in axe.get("pages", [])),
                "fallback": False,
            }
            result["method"]["a11y"] = "playwright + axe-core " + str(axe.get("axeVersion"))
        except Exception as e:  # noqa: BLE001
            warn(f"playwright 路径失败，回退 headless Chrome DOM 检查：{e}")
            result["method"]["a11y"] = "fallback: headless Chrome + 简单 DOM 检查（playwright 不可用）"
            checks = dom_checks(base, pages)
            a11y = {"engine": "headless Chrome DOM checks（fallback）", "pages": checks,
                    "critical": None, "fallback": True}
        result["a11y"] = a11y
        log(f"② a11y：engine={a11y['engine']} critical={a11y.get('critical')}")

        # ③ Lighthouse → 失败则 DOM 代理指标兜底
        try:
            lh, lh_warn = run_lighthouse(base, pages)
            result["method"]["lighthouse"] = "npx --yes lighthouse（仅 performance/accessibility/seo）"
        except Exception as e:  # noqa: BLE001
            warn(f"Lighthouse 不可用，回退 headless Chrome 代理指标：{e}")
            lh, lh_warn = {}, [str(e)]
            result["method"]["lighthouse"] = "fallback: headless Chrome performance 代理指标"
            proxy = {p["path"]: p.get("perfProxy") for p in a11y.get("pages", [])} if a11y.get("fallback") else {}
            lh = {"_proxy": proxy}
        result["lighthouse"] = lh
        result["lighthouseWarnings"] = lh_warn

        # 阈值判定（只记录，不 exit 非零）
        verdict = []
        crit = a11y.get("critical")
        if crit is not None:
            verdict.append({"check": "axe Critical", "value": crit, "max": THRESHOLDS["axe_critical"], "pass": crit <= THRESHOLDS["axe_critical"]})
        for page, row in lh.items():
            if page == "_proxy" or not isinstance(row, dict) or "error" in row:
                continue
            for k, label in (("performance", "Lighthouse performance"), ("accessibility", "Lighthouse accessibility"), ("seo", "Lighthouse SEO")):
                v = row.get(k)
                if v is None:
                    continue
                verdict.append({"check": f"{label} {page}", "value": v, "min": THRESHOLDS[k], "pass": v >= THRESHOLDS[k]})
        result["verdict"] = verdict
        result["pass"] = all(v["pass"] for v in verdict) if verdict else None
    except Exception as e:  # noqa: BLE001
        result["errors"].append(str(e))
        warn(f"运行失败：{e}")
    finally:
        if server and not a.keep_server:
            try:
                server.terminate()
                server.wait(timeout=5)
            except Exception:
                pass

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    log(f"报告 → {os.path.relpath(out_path, WS)}")

    if result.get("verdict"):
        print("\n阈值判定（低于阈值只警示，不阻塞）：")
        for v in result["verdict"]:
            limit = f"max {v['max']}" if "max" in v else f"min {v['min']}"
            print(f"  {'PASS' if v['pass'] else 'WARN'}  {v['check']}: {v['value']}（{limit}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
