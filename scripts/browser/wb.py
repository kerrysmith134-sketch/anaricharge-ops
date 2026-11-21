#!/usr/bin/env python3
"""wb.py — Kimi WebBridge 的 Python 客户端 + CLI。

把「操作浏览器」变成工作区里可复用、可校验、可审计的能力，而不是每次手写 curl。

桥守护进程：http://127.0.0.1:10086
健康检查：  python3 scripts/browser/wb.py health

CLI 用法:
  python3 scripts/browser/wb.py health
  python3 scripts/browser/wb.py tabs
  python3 scripts/browser/wb.py nav "https://www.quora.com/" --session quora
  python3 scripts/browser/wb.py snap --session quora
  python3 scripts/browser/wb.py eval "document.title" --session quora
  python3 scripts/browser/wb.py status              # 各平台登录态
  python3 scripts/browser/wb.py close --session quora

Python 用法:
  from wb import WB
  wb = WB(session="quora")
  wb.nav("https://www.quora.com/")
  print(wb.text()[:300])
"""
import argparse
import atexit
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

BRIDGE = os.environ.get("WB_BRIDGE", "http://127.0.0.1:10086")
BIN = os.path.expanduser("~/.kimi-webbridge/bin/kimi-webbridge")
DEFAULT_TIMEOUT = 90

# 各平台的登录态判据（只读，不产生任何写入）
PLATFORMS = {
    "quora": {
        "url": "https://www.quora.com/",
        "markers": ["Answer", "Spaces", "Notifications"],
        "anti": ["Log In", "Sign up"],
    },
    "reddit": {
        "url": "https://www.reddit.com/",
        "markers": ["创建帖子", "展开用户菜单", "Create Post", "Expand user menu"],
        "anti": ["Log In", "Sign Up"],
    },
    "brevo": {
        "url": "https://app.brevo.com/",
        "markers": ["Hello ", "Campaigns", "Contacts"],
        "anti": ["Log in", "Sign in"],
    },
    "gsc": {
        "url": "https://search.google.com/search-console?resource_id=sc-domain:anaricharge.com",
        "markers": ["Overview", "效果", "网页", "Performance"],
        "anti": ["about", "Sign in"],
    },
    "cloudflare": {
        "url": "https://dash.cloudflare.com/",
        "markers": ["Websites", "Account Home"],
        "anti": ["/login", "Sign in to Cloudflare"],
    },
}


class WBError(RuntimeError):
    pass


class WB:
    def __init__(self, session="default", timeout=DEFAULT_TIMEOUT):
        self.session = session
        self.timeout = timeout
        _register_exit_cleanup(self.session)

    # ---------- transport ----------
    def _post(self, action, args=None):
        body = json.dumps({"action": action, "args": args or {}, "session": self.session}).encode()
        req = urllib.request.Request(
            BRIDGE + "/command", data=body,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                payload = json.load(r)
        except urllib.error.URLError as e:
            raise WBError("bridge unreachable: %s (daemon 起了吗？%s start)" % (e, BIN))
        if not payload.get("ok"):
            err = payload.get("error") or {}
            raise WBError("%s: %s" % (err.get("code", "error"), err.get("message", "")[:300]))
        return payload.get("data")

    # ---------- tools ----------
    def nav(self, url, new_tab=True, group_title=None):
        a = {"url": url, "newTab": new_tab}
        if group_title:
            a["group_title"] = group_title
        return self._post("navigate", a)

    def find_tab(self, url, active=False):
        return self._post("find_tab", {"url": url, "active": active})

    def list_tabs(self):
        return self._post("list_tabs")

    def snapshot(self):
        return self._post("snapshot")

    def click(self, selector):
        return self._post("click", {"selector": selector})

    def fill(self, selector, value):
        return self._post("fill", {"selector": selector, "value": value})

    def screenshot(self, path=None, fmt="png", quality=None, selector=None):
        a = {"format": fmt}
        if path:
            a["path"] = path
        if quality is not None:
            a["quality"] = quality
        if selector:
            a["selector"] = selector
        return self._post("screenshot", a)

    def close_tab(self):
        return self._post("close_tab")

    def close_session(self):
        return self._post("close_session")

    # ---------- 便捷封装 ----------
    def eval(self, code):
        """在页面上下文里跑 JS；自动包 IIFE 避免重复声明冲突。"""
        d = self._post("evaluate", {"code": "(() => { %s })()" % code})
        return d.get("value")

    def js(self, expr):
        """求值单个表达式（不包 IIFE，适合 object literal 之外的表达式）。"""
        d = self._post("evaluate", {"code": "JSON.stringify(%s)" % expr})
        v = d.get("value")
        try:
            return json.loads(v) if isinstance(v, str) else v
        except Exception:  # noqa: BLE001
            return v

    def text(self):
        return self.eval("return document.body.innerText;") or ""

    def title(self):
        return self.eval("return document.title;")

    def url(self):
        return self.eval("return location.href;")

    def wait_text(self, needle, timeout=25, interval=1.0):
        """等页面上出现某段文字（用于等 SPA 渲染完）。"""
        end = time.time() + timeout
        while time.time() < end:
            try:
                if needle in self.text():
                    return True
            except WBError:
                pass
            time.sleep(interval)
        return False


# ---------------------------------------------------------------- 健康 / 登录态
def daemon_status():
    if not os.path.exists(BIN):
        return {"installed": False}
    try:
        out = subprocess.run([BIN, "status"], capture_output=True, text=True, timeout=20).stdout
        d = json.loads(out)
        d["installed"] = True
        return d
    except Exception as e:  # noqa: BLE001
        return {"installed": True, "error": str(e)[:200]}


def ensure_daemon():
    st = daemon_status()
    if not st.get("running"):
        subprocess.run([BIN, "start"], capture_output=True, text=True, timeout=60)
        time.sleep(3)
        st = daemon_status()
    return st


def check_platform(session, spec):
    wb = WB(session=session, timeout=60)
    res = {"session": session, "url": spec["url"]}
    try:
        wb.nav(spec["url"], new_tab=True, group_title="ANARI-接管")
        time.sleep(2)
        body = wb.text()[:4000]
        cur = wb.url() or ""
        hit = [m for m in spec["markers"] if m in body]
        bad = [a for a in spec["anti"] if a in body or a in cur]
        res["logged_in"] = bool(hit) and not bad
        res["markers_hit"] = hit
        res["anti_hit"] = bad
        res["landed_url"] = cur
        res["title"] = wb.title()
    except WBError as e:
        res["logged_in"] = False
        res["error"] = str(e)[:200]
    return res


# ---------------------------------------------------------------- 标签页卫生
KNOWN_SESSIONS = [
    "default", "anari", "quora", "reddit", "brevo", "gsc", "cf", "materials",
    "linkedin", "qa", "qa2", "qa3", "qa4", "gtm", "ga4", "gsc2", "cloudflare",
    "quora2", "reddit2", "brevo2", "inquiry", "verify", "instant", "instantly",
    "gtm2", "ga4-2", "gsc-inspect", "ads", "pages", "enrich", "enrichment", "enrich3", "wave3",
]


def cmd_hygiene():
    """标准收尾：关掉所有会话标签并复核为零。

    为什么要有这条命令：`cleanup` 只是动作，`hygiene` 是**动作 + 验证**。
    团队纪律要求"跑完必须验证 0 个自开标签"，这条命令就是那个验证。
    """
    before = tabs_summary()
    n = cleanup_all(verbose=True)
    after = tabs_summary()
    remaining = sum(s["count"] for s in after)
    print("复核：清理前 %d 个 → 清理后 %d 个" % (
        sum(s["count"] for s in before), remaining))
    if remaining:
        print("⚠️ 仍有 %d 个标签未清理，人工检查：" % remaining)
        for s in after:
            print("   %-14s %d 个 %s" % (s["session"], s["count"], s["titles"][:2]))
        return 1
    print("✅ 浏览器已清空")
    return 0



# --- 进程退出兜底清理（2026-11-10 加入）------------------------------------
# 为什么加：纪律写在 AGENTS.md 里，但脚本异常/提前 return 时没人记得调 cleanup_all，
# 结果标签越积越多（2026-11-07 一次 21 个）。改成机制：任何 import wb 并 new 过 WB 的进程，
# 退出时（正常结束或抛异常）自动关闭自己碰过的会话标签。
# 需要保留标签排查时：WB_KEEP_TABS=1 python3 ...
_PROCESS_SESSIONS = set()


def _register_exit_cleanup(session):
    _PROCESS_SESSIONS.add(session)


def _atexit_cleanup():
    import os as _os
    if _os.environ.get("WB_KEEP_TABS") == "1":
        return
    if not _PROCESS_SESSIONS:
        return
    for s in list(_PROCESS_SESSIONS):
        try:
            (WB(session=s).close_session() or {}).get("closed", 0)
        except Exception:  # noqa: BLE001
            pass


atexit.register(_atexit_cleanup)


def tabs_summary():
    """当前所有会话的标签汇总（供 hygiene 与审计用）。"""
    out = []
    for s in KNOWN_SESSIONS:
        try:
            tabs = (WB(session=s).list_tabs() or {}).get("tabs") or []
            if tabs:
                out.append({"session": s, "count": len(tabs),
                            "titles": [t.get("title", "") for t in tabs][:3]})
        except Exception:  # noqa: BLE001
            pass
    return out


def cleanup_all(verbose=True):
    """关闭所有已知会话的标签页。每次浏览器任务结束都应调用。"""
    total = 0
    for s in KNOWN_SESSIONS:
        try:
            n = (WB(session=s).close_session() or {}).get("closed", 0)
            if n:
                total += n
                if verbose:
                    print("  关闭 %-12s %d 个标签" % (s, n))
        except Exception:  # noqa: BLE001
            pass
    if verbose:
        print("合计关闭 %d 个标签" % total)
    return total


def tabs_all():
    """列出各会话剩余标签数（用于自查）。"""
    rows = []
    for s in KNOWN_SESSIONS:
        try:
            tabs = (WB(session=s).list_tabs() or {}).get("tabs") or []
            if tabs:
                rows.append({"session": s, "count": len(tabs),
                             "titles": [t.get("title", "")[:60] for t in tabs]})
        except Exception:  # noqa: BLE001
            pass
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=[
        "health", "tabs", "tabs-all", "cleanup", "hygiene", "nav", "snap", "eval", "status",
        "close", "screenshot"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--session", default="default")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.cmd == "health":
        st = ensure_daemon()
        ok = st.get("running") and st.get("extension_connected")
        print(json.dumps({
            "installed": st.get("installed"),
            "running": st.get("running"),
            "extension_connected": st.get("extension_connected"),
            "version": st.get("version"),
            "healthy": bool(ok),
        }, ensure_ascii=False, indent=2))
        return 0 if ok else 1

    if a.cmd == "status":
        ensure_daemon()
        out = [check_platform(k, v) for k, v in PLATFORMS.items()]
        if a.json:
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            for r in out:
                icon = "✅" if r.get("logged_in") else "❌"
                print(f"{icon} {r['session']:12s} {r.get('title', '')[:40]:42s} {r['landed_url'][:60]}")
        # 2026-11-07 修：status 会为每个平台各开一个标签，检查完从不关闭 ——
        # 这是标签堆积的真正主因（每次调用漏 5 个）。检查属只读动作，收尾即关。
        closed = cleanup_all(verbose=False)
        print("[hygiene] 登录态检查已关闭 %d 个标签" % closed)
        return 0

    if a.cmd == "hygiene":
        return cmd_hygiene()

    if a.cmd == "cleanup":
        cleanup_all()
        return 0
    if a.cmd == "tabs-all":
        rows = tabs_all()
        print(json.dumps(rows, ensure_ascii=False, indent=2) if rows else "（无残留标签）")
        return 0

    wb = WB(session=a.session)
    if a.cmd == "tabs":
        print(json.dumps(wb.list_tabs(), ensure_ascii=False, indent=2))
    elif a.cmd == "nav":
        print(json.dumps(wb.nav(a.arg, new_tab=True, group_title="ANARI-接管"),
                         ensure_ascii=False, indent=2))
    elif a.cmd == "snap":
        print(json.dumps(wb.snapshot(), ensure_ascii=False, indent=2))
    elif a.cmd == "eval":
        print(json.dumps(wb.js(a.arg), ensure_ascii=False, indent=2))
    elif a.cmd == "screenshot":
        print(json.dumps(wb.screenshot(path=a.arg), ensure_ascii=False, indent=2))
    elif a.cmd == "close":
        print(json.dumps(wb.close_session(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
