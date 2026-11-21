#!/usr/bin/env python3
"""GSC URL Inspection → 请求编入索引（浏览器自动化，WebBridge）

2026-11-10 实测跑通版（E1 补跑 5 个 URL 全部 "Indexing requested"）。
背景与坑（同时更正 00-takeover/BROWSER-CAPABILITY.md 坑 3）：
  - GSC 是登录态；resource_id 必须 URL 编码：sc-domain%3Aanaricharge.com，
    否则控制台会回落 /about，看起来像"未登录"。
  - /inspect?...&id=<url> 直链不存在；正确流程 = 控制台顶部
    `input[aria-label*="Inspect any URL"]` 填 URL → 回车。
  - 回车用**合成 KeyboardEvent**（keydown/keypress/keyup, key=Enter, keyCode=13）：
    2026-11-10 实测 CDP Input.dispatchKeyEvent 在后台标签页不生效，合成事件可以。
  - REQUEST INDEXING 按文本定位到最内层 span，再取最近的
    [role=button]/button/[jsaction] 原生 .click()；实测有效（会先跑 live test）。
  - wb.py 的 `eval` 会把代码包成 `(() => { <code> })()`，所以传入的代码要写成
    **语句 + 显式 return**；不要再套一层 IIFE，否则返回值恒为 None。

用法:
  python3 scripts/tools/gsc_request_indexing.py <url> [<url> ...]
  python3 scripts/tools/gsc_request_indexing.py --skip-indexed <url> ...
输出:
  08-execution/gsc/index-requests-<date>.jsonl（追加）
  08-execution/gsc/<slug>-<date>-<hhmmss>.jpg（截图证据）
退出码: 0 = 全部 requested / already_indexed；1 = 有失败
"""
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

BRIDGE = "http://127.0.0.1:10086"
SESSION = "gsc-idx"
HOME = "https://search.google.com/search-console?hl=en&resource_id=sc-domain%3Aanaricharge.com"
OUT_DIR = "08-execution/gsc"
TODAY = datetime.date.today().isoformat()


def call(action, args=None, timeout=45, retries=4):
    """调用 bridge；对 502/连接错误做指数退避重试。

    2026-11-13 踩坑：GSC 页面较重时 snapshot/evaluate 会超时，daemon 直接回 **502 Bad Gateway**。
    同一时刻 example.com 上的 evaluate 正常 → 不是 daemon 死了，是**页面级超时**。
    当时的真实代价：当天 5 个 URL 全部记成 `no_input`（看起来像选择器坏了，其实是 502 被吞）。
    另一个可疑根因：扩展 2.0.32 vs daemon 2.0.35 版本不一致（daemon 提示可升 2.0.36）。
    所以：① 重试；② 每次开跑前 `nav` 一个轻页面确认通道，再进 GSC；③ 失败必须如实记 502，
    不许把 502 写成 no_input。
    """
    body = json.dumps({"action": action, "args": args or {}, "session": SESSION}).encode()
    last = None
    for i in range(retries):
        req = urllib.request.Request(BRIDGE + "/command", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())
        except urllib.error.HTTPError as e:
            last = "HTTP %s" % e.code
            if e.code == 502:
                time.sleep(1.5 * (i + 1))
                continue
            raise
        except Exception as e:  # noqa: BLE001
            last = "%s: %s" % (type(e).__name__, str(e)[:80])
            time.sleep(1.5 * (i + 1))
    raise RuntimeError("bridge unavailable after %d retries (%s)" % (retries, last))


def ev(code):
    """code 是函数体语句，必须显式 return（调用方不要自带 IIFE）。

    2026-11-12 修复：daemon v2.0.35 起 `evaluate` 只按**表达式**求值，不再把 code
    包成 `(()=>{...})()`；旧脚本直接传 `return ...` 会得到
    `SyntaxError: Illegal return statement`，被 ev() 的 except 吞成 None，
    表现就是一路 `no_input`（当天排查了半天 502，真因在此）。
    这里显式包一层 IIFE，兼容新旧 daemon。
    """
    wrapped = "(() => { %s })()" % code
    try:
        return (call("evaluate", {"code": wrapped}).get("data") or {}).get("value")
    except Exception:
        return None


def js(expr):
    try:
        v = ev("return JSON.stringify(%s);" % expr)
        return json.loads(v) if isinstance(v, str) else v
    except Exception:
        return None


def ensure_input(timeout=60):
    """确保在控制台页且顶部检查框存在；返回 data 选择器。"""
    end = time.time() + timeout
    while time.time() < end:
        sel = ev("""const i=document.querySelector('input[aria-label*="Inspect any URL"], input[aria-label*="检查"][type=text], input[aria-label*="URL"][type=text]');
if(!i) return null; i.setAttribute('data-gsc-nav','gscnav'); return '[data-gsc-nav=gscnav]';""")
        if sel:
            return sel
        ev('location.href=%s; return "nav";' % json.dumps(HOME))
        time.sleep(4)
    return None


def submit(sel, url):
    call("click", {"selector": sel})
    time.sleep(0.6)
    call("fill", {"selector": sel, "value": url})
    time.sleep(0.6)
    return ev("""const i=document.querySelector('[data-gsc-nav=gscnav]')||document.querySelector('input[aria-label*="Inspect any URL"], input[aria-label*="检查"][type=text], input[aria-label*="URL"][type=text]');
if(!i) return 0; i.focus();
const o={key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true,cancelable:true,composed:true};
i.dispatchEvent(new KeyboardEvent('keydown',o));
i.dispatchEvent(new KeyboardEvent('keypress',o));
i.dispatchEvent(new KeyboardEvent('keyup',o));
return 1;""")


def wait_inspect(url, timeout=70):
    end = time.time() + timeout
    while time.time() < end:
        time.sleep(3)
        st = js("""({u:location.href,
 has: location.href.includes('/inspect?'),
 urlIn: document.body.innerText.includes(%s),
 retr:/Retrieving data from Google Index/i.test(document.body.innerText)})""" % json.dumps(url))
        if st and st.get("has") and st.get("urlIn") and not st.get("retr"):
            return True
    return False


def click_request():
    return ev(r"""const els=[...document.querySelectorAll('button,[role=button],span')]
  .filter(x=>/^\s*request indexing\s*$/i.test((x.innerText||'').trim()) && x.offsetParent!==null);
const inner=els[els.length-1]; if(!inner) return 'nf';
const btn=inner.closest('[role=button],button,[jsaction]')||inner; btn.click(); return 'clicked';""")


def wait_result(timeout=150):
    end = time.time() + timeout
    while time.time() < end:
        time.sleep(6)
        t = js("""({ok:/Indexing requested|priority crawl queue/i.test(document.body.innerText),
 q:/quota|exceeded|hit the daily/i.test(document.body.innerText)})""") or {}
        if t.get("ok"):
            return "requested"
        if t.get("q"):
            return "quota"
    return "timeout"


def fresh_tab():
    """每个 URL 开一个**新标签**再进控制台。

    2026-11-13 实测根因（这条坑值得记）：
    - 复用旧标签时，GSC 控制台页在后台/被遮挡窗口里会被 Chrome 节流 → 页面不渲染，
      表现是 `snapshot/evaluate` 超时 → daemon 回 **502**，旧代码吞掉后记成 `no_input`。
    - 每 URL 用 `nav(newTab=True)` 建新标签后：sitemap 重提 1 次成功、requestIndexing
      **9/10 成功**（第 10 个本就已收录）。所以修法不是"重试选择器"，是**每次开新标签**。
    - 与 `00-takeover/BROWSER-CAPABILITY.md` 坑 1 的处置 ③ 一致：操作完关标签，下次重建。
    """
    try:
        call("navigate", {"url": HOME, "newTab": True}, timeout=60)
    except Exception:  # noqa: BLE001
        pass
    sel = ensure_input(timeout=40)
    return sel


def request_one(url, skip_indexed=False):
    print("=== %s" % url, flush=True)
    sel = fresh_tab()
    if not sel:
        # 新标签也没拿到输入框 → 再试一次（偶发 502）
        time.sleep(3)
        sel = fresh_tab()
    if not sel:
        return "no_input"
    submit(sel, url)
    if not wait_inspect(url):
        return "no_result"
    body = js("""({txt: document.body.innerText})""") or {}
    txt = body.get("txt", "")
    on_google = "URL is on Google" in txt
    if on_google and skip_indexed:
        return "already_indexed"
    r = click_request()
    if r != "clicked":
        return "no_button"
    res = wait_result()
    if on_google and res == "requested":
        res = "already_indexed_recrawl_requested"
    return res


def main():
    args = [a for a in sys.argv[1:] if a != "--skip-indexed"]
    skip = "--skip-indexed" in sys.argv
    if not args:
        print(__doc__)
        return 2
    os.makedirs(OUT_DIR, exist_ok=True)
    log = os.path.join(OUT_DIR, "index-requests-%s.jsonl" % TODAY)
    results = {}
    for i, url in enumerate(args):
        res = "fail"
        try:
            res = request_one(url, skip_indexed=skip)
        except Exception as e:  # noqa: BLE001
            print("   EXC:", e, flush=True)
        results[url] = res
        try:
            call("close_tab", {}, timeout=20)   # R10：用完即关，避免标签堆积
        except Exception:  # noqa: BLE001
            pass
        slug = url.rstrip("/").split("/")[-1] or "home"
        shot = os.path.abspath("%s/%s-%s-%s.jpg" % (
            OUT_DIR, slug, TODAY, datetime.datetime.now().strftime("%H%M%S")))
        try:
            call("screenshot", {"format": "jpeg", "quality": 70, "path": shot})
        except Exception as e:  # noqa: BLE001
            print("   screenshot err:", e)
            shot = None
        rec = {"date": TODAY, "url": url, "result": res, "screenshot": shot,
               "ts": datetime.datetime.now().isoformat(timespec="seconds")}
        with open(log, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("   RESULT:", res, "| shot:", shot, flush=True)
    print("\n== SUMMARY ==")
    for u, r in results.items():
        print(" ", r, u)
    print("log:", log)
    ok = all(r in ("requested", "already_indexed", "already_indexed_recrawl_requested")
             for r in results.values())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
