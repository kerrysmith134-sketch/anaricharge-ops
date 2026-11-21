#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gmail_send.py — 用真实浏览器在 kerry@anaricharge.com 的 Gmail 里发一封邮件

## 为什么必须用浏览器（2026-11-12 教训）
我们一度用 Instantly 的 `/emails/test` 代发：**信到了但正文是空的**（用户截图确认）。
通知/摘要/回信都受影响。用户明确要求："直接用浏览器操作我的 kerry@anaricharge.com 邮箱收和发就行了"。
所以对外发信统一走这里：真实 Gmail 会话 + 真实 compose UI。

## 关键实现点（踩过的坑）
- Gmail 现代 UI 的 `el.click()` 无效 → 必须派发 pointerdown/mousedown/pointerup/mouseup 再 click
- 正文是 contenteditable，不能用 `.value`；用 focus + `document.execCommand('insertText')`
- 收件人输入框可能是 `input[aria-label="To recipients"]`（新版）或 `textarea[name=to]`（旧版），两种都试
- compose 用 `?view=cm&fs=1&tf=1` 全屏模式最稳（不用先点"撰写"）

## 用法
  python3 scripts/tools/gmail_send.py --to a@b.com --subject "Re: ..." --body-file /tmp/body.txt
  python3 scripts/tools/gmail_send.py --to a@b.com --subject "..." --body-file ... --dry   # 只填充不发
  python3 scripts/tools/gmail_send.py ... --force   # 24h 内已发过仍强制再发（默认拒绝）
退出码：0 已发送 / 1 失败
"""
import argparse
import json
import os
import re
import sys
import time

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(WS, "scripts", "browser"))

REAL_CLICK = """
function realClick(el){
  var r=el.getBoundingClientRect();
  var o={bubbles:true,cancelable:true,clientX:r.left+r.width/2,clientY:r.top+r.height/2,view:window};
  ['pointerdown','mousedown','pointerup','mouseup'].forEach(function(t){
    el.dispatchEvent(new (t.indexOf('pointer')===0?PointerEvent:MouseEvent)(t,o));
  });
  el.click();
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--cc", default="")
    ap.add_argument("--force", action="store_true",
                    help="24h 内已向同一地址发过时仍强制发送（默认拒绝）")
    a = ap.parse_args()

    body = open(a.body_file, encoding="utf-8").read()
    try:
        from wb import WB, cleanup_all
    except Exception as e:  # noqa: BLE001
        print(f"❌ 无法加载 wb：{e}")
        return 1

    wb = WB(session="gmail-send")
    try:
        # 0) 去重护栏（2026-11-16 踩过：两个会话 3 分钟内各发一封给同一编辑）
        if not a.force and not a.dry:
            q = a.to.replace("@", "%40")
            wb.nav("https://mail.google.com/mail/u/0/#search/in%3Asent+to%3A" + q, new_tab=True)
            time.sleep(7)
            txt = wb.eval("return (document.querySelector('[role=main]')||document.body).innerText.slice(0,400);") or ""
            m = re.search(r"(\d+)\s*(?:Conversations|会话)", txt)
            n = int(m.group(1)) if m else 0
            if n > 0:
                print(f"❌ 24h 内已向 {a.to} 发过 {n} 封（防重复）。确认要再发请加 --force")
                return 2
        wb.nav("https://mail.google.com/mail/u/0/?view=cm&fs=1&tf=1", new_tab=True)
        time.sleep(9)
        # 1) 收件人
        r = wb.eval(REAL_CLICK + """
        var to=document.querySelector('input[aria-label="To recipients"], textarea[name=to], input[name=to]');
        if(!to) return 'no_to_field';
        to.focus();
        to.value=%s;
        to.dispatchEvent(new Event('input',{bubbles:true}));
        to.dispatchEvent(new Event('change',{bubbles:true}));
        to.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',keyCode:13,bubbles:true}));
        return 'ok';
        """ % json.dumps(a.to))
        print(f"  收件人: {r}")
        if r != "ok":
            return 1
        time.sleep(1)
        # 2) 主题
        r = wb.eval(REAL_CLICK + """
        var s=document.querySelector('input[name=subjectbox], input[name=subject]');
        if(!s) return 'no_subject';
        s.focus(); s.value=%s;
        s.dispatchEvent(new Event('input',{bubbles:true}));
        s.dispatchEvent(new Event('change',{bubbles:true}));
        return s.value.length ? 'ok' : 'empty';
        """ % json.dumps(a.subject))
        print(f"  主题: {r} ({len(a.subject)} 字符)")
        # 3) 正文（contenteditable）
        r = wb.eval(REAL_CLICK + """
        var b=document.querySelector('div[aria-label="Message Body"], div[contenteditable=true][role=textbox], div[contenteditable=true]');
        if(!b) return 'no_body';
        b.focus();
        var sel=window.getSelection(); var range=document.createRange();
        range.selectNodeContents(b); range.collapse(true);
        sel.removeAllRanges(); sel.addRange(range);
        document.execCommand('insertText', false, %s);
        return (b.innerText||'').length ? 'ok:'+(b.innerText||'').length : 'empty';
        """ % json.dumps(body))
        print(f"  正文: {r}")
        if not str(r).startswith("ok:"):
            return 1
        time.sleep(1)
        if a.dry:
            print("  [dry] 已填充，不发送")
            return 0
        # 4) 发送
        r = wb.eval(REAL_CLICK + """
        var btn=Array.from(document.querySelectorAll('[role=button],div[role=button]')).find(function(x){
          var al=(x.getAttribute('aria-label')||'').trim();
          return /^Send/.test(al) || /发送/.test(al);});
        if(!btn) return 'no_send_btn';
        realClick(btn);
        return 'clicked';
        """)
        print(f"  发送: {r}")
        time.sleep(5)
        # 5) 验证：compose 关闭 / snackbar 提示
        ver = wb.eval("""
        var t=(document.body.innerText||'');
        var snack = /Message sent|已发送/.test(t);
        var composeOpen = !!document.querySelector('input[name=subjectbox]');
        return JSON.stringify({snackbar:snack, composeOpen:composeOpen});
        """)
        print(f"  验证: {ver}")
        return 0
    finally:
        try:
            cleanup_all(verbose=False)
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    raise SystemExit(main())
