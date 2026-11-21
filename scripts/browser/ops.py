#!/usr/bin/env python3
"""ops.py — 平台级浏览器操作（Quora / Reddit / Brevo / GSC）。

在 wb.py 之上封装「运营真正要做的事」，让 03-workflows/ 里的 SOP 能直接调用。

设计原则：
1. **读操作随时可跑**；写操作（发帖/回复/改后台）必须显式传 `confirm=True`，否则只返回预览。
2. 所有写操作返回结构里带 `preview`（将要提交的文本），便于留痕与人工复核。
3. 不代注册、不代登录、不绕过验证码。

CLI:
  python3 scripts/browser/ops.py quora-search "ev charging station franchise"
  python3 scripts/browser/ops.py quora-question <url>
  python3 scripts/browser/ops.py reddit-new "ElectricVehicles" --limit 10
  python3 scripts/browser/ops.py brevo-contacts
  python3 scripts/browser/ops.py brevo-find someone@example.com
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wb import WB, WBError, ensure_daemon  # noqa: E402


# ============================================================ Quora
def quora_search(keyword, limit=15):
    """Quora 站内搜索问题，返回 [{url, title}]。只读。"""
    wb = WB(session="quora")
    wb.nav("https://www.quora.com/search?q=" + keyword.replace(" ", "%20"),
           new_tab=True, group_title="ANARI-接管")
    time.sleep(4)
    data = wb.js(
        "Array.from(document.querySelectorAll('a[href*=\"/\"]'))"
        ".filter(a=>/\\/\\w[\\w-]*-\\d+$|\\/\\w[\\w-]*$/.test(a.pathname) && a.innerText.trim().length>18)"
        ".map(a=>({url:a.href,title:a.innerText.trim()}))"
        ".filter((v,i,arr)=>arr.findIndex(x=>x.url===v.url)===i)"
        ".slice(0,%d)" % limit)
    return data or []


def quora_question(url):
    """读一个问题页：标题、问题描述、已有答案摘要。只读。"""
    wb = WB(session="quora")
    wb.nav(url, new_tab=True, group_title="ANARI-接管")
    time.sleep(4)
    return wb.js(
        "{url:location.href,title:document.title,"
        " answerCount:(document.body.innerText.match(/(\\d+)\\s*(Answer|答案)/)||[])[0]||'',"
        " body:document.body.innerText.slice(0,3000)}")


def quora_post_answer(question_url, text, confirm=False, submit=False):
    """在指定问题下写回答。

    ## 2026-11-08 实测的正确路径（两次踩坑后）
    1) 点**页面顶部**的 `Answer` 按钮 → 弹出 `[role=dialog]` 模态 + 一个 `[contenteditable=true]` 编辑器。
       **2026-11-09 修正**：按钮无障碍文本在已答问题上是 `"Answer · 10"`（带答案数），
       精确匹配 `"Answer"` 只对 `/unanswered/` 页面成立 → 改为
       `/^(Answer|回答)(\s*·\s*\d+)?$/`，并按屏幕位置取最靠上的那个（题头按钮在相关题之前）。
    2) 编辑器里的正文用 `execCommand('insertText')` 写入（Quora 用 draft-style 编辑器，
       直接改 innerHTML 不触发它的状态）
    3) 点模态里（或页面上）文字为 `Post` / `发布` 的按钮提交
    4) 验证：重新加载问题页，正文片段出现 **或** "does not have any answers yet" 消失

    踩过的坑：
    - `/unanswered/<slug>` 就是问题页本身（h1 即问题），不是"列表页"；
    - 但页面上还有 4 个同类 Answer 按钮属于"相关问题"，点它们会跳到别的问题；
    - 旧实现走 snapshot ref，会命中相关问题的按钮 → 填不到编辑器 → 却仍点 Post，
      返回 submitted_unverified 被上游误当成功。
    """
    result = {"action": "quora_post_answer", "question": question_url,
              "chars": len(text), "preview": text[:300]}
    if not confirm:
        result["status"] = "dry_run"
        result["hint"] = "加 --confirm 才会真的发布"
        return result

    wb = WB(session="quora")
    wb.nav(question_url, new_tab=True, group_title="ANARI-接管")
    time.sleep(6)

    # 1) 页面可用性：轮询等 Answer 入口。
    # 2026-11-08 实测第三种失败形态：Quora 被限流时返回"Try again"错误页
    # （有 h1 但没有 Answer 入口、也没有"does not have any answers yet"）——
    # 这时需要点 Try again / 重载，而不是判定"未登录"。
    has_entry = False
    for i in range(6):
        has_entry = wb.eval(r"""
          var norm=function(s){return (s||'').replace(/\s+/g,' ').trim();};
          var re=/^(Answer|回答)(\s*·\s*\d+)?$/;
          return Array.from(document.querySelectorAll('[role=button],button,a,span,div'))
            .some(function(e){return re.test(norm(e.innerText));});
        """)
        if has_entry:
            break
        # 错误页：点 Try again，否则重载
        clicked = wb.eval("""
          var b=Array.from(document.querySelectorAll('[role=button],button'))
            .filter(function(e){return (e.innerText||'').trim()==='Try again';});
          if(!b.length) return false;
          b[0].click(); return true;
        """)
        time.sleep(8 if clicked else 0)
        if not clicked:
            wb.nav(question_url, new_tab=False)
            time.sleep(10)
    if not has_entry:
        result["status"] = "blocked"
        result["reason"] = ("页面上没有 Answer 入口（试了 Try again / 重载 6 轮）——"
                            "多为 Quora 限流错误页、问题已关闭或未登录")
        return result

    # 2) 点顶部 Answer，等模态。
    # 关键：必须点**可点击的祖先**（[role=button]/button），点内层 span 不会触发；
    # 且候选里可能有 sidebar 相关问题，取**屏幕上最靠上**的那个（题本体的按钮在最上方），
    # 同位置优先真 BUTTON（题头 div 与内部 button 文本相同）。
    path_before = wb.eval("return location.pathname;") or ""
    clicked_btn = wb.eval(r"""
      var norm=function(s){return (s||'').replace(/\s+/g,' ').trim();};
      var re=/^(Answer|回答)(\s*·\s*\d+)?$/;
      var cand=Array.from(document.querySelectorAll('[role=button],button,a'))
        .filter(function(e){
          if(!re.test(norm(e.innerText))) return false;
          return e.getBoundingClientRect().height>0;
        });
      if(!cand.length) return 'no-candidate';
      cand.sort(function(a,b){
        var ta=a.getBoundingClientRect().top, tb=b.getBoundingClientRect().top;
        if(Math.abs(ta-tb)>2) return ta-tb;
        if(a.tagName==='BUTTON'&&b.tagName!=='BUTTON') return -1;
        if(b.tagName==='BUTTON'&&a.tagName!=='BUTTON') return 1;
        return 0;
      });
      var el=cand[0];
      var clickable=el.closest('[role=button],button')||el;
      clickable.click();
      return 'clicked:'+(clickable.tagName||'')+':'+norm(el.innerText);
    """)
    editors = 0
    for _ in range(6):
        time.sleep(3)
        editors = wb.eval("return document.querySelectorAll('[contenteditable=true]').length;")
        if editors:
            break
    if not editors:
        result["click_info"] = clicked_btn
    if not editors:
        result["status"] = "blocked"
        result["reason"] = "点了 Answer 但没有出现编辑器（模态未打开）"
        return result
    # 防误点：若点击后页面跳到了别的问题（sidebar 相关题的 Answer），立刻中止，
    # 不往编辑器写任何东西、更不会提交（2026-11-08 踩过误点相关题）。
    path_after = wb.eval("return location.pathname;") or ""
    if path_before and path_after and path_before != path_after:
        result["status"] = "blocked"
        result["reason"] = ("点了 Answer 后页面跳到了别的问题（%s → %s）——"
                            "疑似命中相关题的按钮，已中止，未写入未提交"
                            % (path_before[:60], path_after[:60]))
        return result

    # 3) 写正文（insertText 让编辑器状态同步）
    wb.eval("""
      var ed=document.querySelector('[contenteditable=true]');
      ed.focus();
      var sel=window.getSelection(); var r=document.createRange();
      r.selectNodeContents(ed); r.collapse(false); sel.removeAllRanges(); sel.addRange(r);
      document.execCommand('insertText', false, %s);
    """ % json.dumps(text))
    time.sleep(2)
    written = wb.eval("""
      var ed=document.querySelector('[contenteditable=true]');
      return ed ? (ed.innerText||'').length : 0;
    """)
    result["editor_chars"] = written
    if not written:
        result["status"] = "blocked"
        result["reason"] = "正文没写进编辑器（0 字）"
        return result

    if not submit:
        result["status"] = "filled_not_submitted"
        result["hint"] = "已填入编辑器但未点 Post；加 --submit 才提交"
        return result

    # 4) 提交：模态内优先
    clicked = wb.eval("""
      var dlg=document.querySelector('[role=dialog]');
      var scope=dlg||document;
      var b=Array.from(scope.querySelectorAll('[role=button],button'))
        .filter(function(e){var s=(e.innerText||'').trim();return s==='Post'||s==='发布'||s==='Submit';});
      if(!b.length) return 'no-post-btn';
      b[b.length-1].click(); return 'clicked';
    """)
    result["submit_click"] = clicked
    time.sleep(10)

    # 5) 验证：重载**canonical** 问题页（`/unanswered/` 回答后会重定向到正式 URL）。
    # 2026-11-09 修正两处 fail-open / fail-quiet：
    #   - 原来只看 `no_answer_placeholder_gone` → "Try again" 错误页也满足 → 会把
    #     "没发出去" 误报成 published（11-08 就是这样誤报的）；
    #   - 原来只等 10s，答案尚未传播时只拿得到错误页 → 误报 submitted_unverified。
    # 现在：错误页重试 4 轮 + 三证判据（正文片段 + (答案横幅 或 /answer/ permalink)）。
    canon = question_url.replace("/unanswered/", "/")
    body = ""
    for _ in range(4):
        wb.nav(canon, new_tab=False)
        time.sleep(10)
        body = wb.text() or ""
        if len(body) > 1500 and "Try again" not in body[:400]:
            break
    first_line = [ln.strip() for ln in text.split("\n") if len(ln.strip()) > 40][:1]
    snippet = first_line[0][:50] if first_line else text.strip()[:50]
    banner = "you've written an answer" in body.lower()
    result["verify"] = {
        "body_has_snippet": snippet in body,
        "answered_banner": banner,
        "permalink_found": "/answer/" in body,
        "body_len": len(body),
        "url": wb.url(),
    }
    ok = result["verify"]["body_has_snippet"] and (
        banner or result["verify"]["permalink_found"])
    result["status"] = "published" if ok else "submitted_unverified"
    return result


# ============================================================ Reddit
def reddit_new(subreddit, limit=10, sort="new"):
    """读子版块帖子列表。只读。

    优先 old.reddit.com（DOM 稳定、无需等 SPA），失败再回退 www。
    """
    wb = WB(session="reddit")
    for base in ("https://old.reddit.com/r/%s/%s/", "https://www.reddit.com/r/%s/%s/"):
        url = base % (subreddit, sort)
        try:
            wb.nav(url, new_tab=True, group_title="ANARI-接管")
            time.sleep(6)
            if wb.js("document.querySelectorAll('a').length") < 20:
                continue
            rows = wb.js(
                "Array.from(document.querySelectorAll('a.title[href*=\"/comments/\"], a[href*=\"/comments/\"]'))"
                ".map(a=>({url:a.href.split('?')[0],title:(a.innerText||'').trim(),"
                "score:(a.closest('div.thing')||{}).getAttribute"
                "?(function(){const s=a.closest('div.thing').getAttribute('data-score');"
                "return s?parseInt(s,10):null})():null}))"
                ".filter(v=>v.title.length>8 && !/^\\d+\\s+(comment|comments|条评论)$/.test(v.title))"
                ".filter((v,i,arr)=>arr.findIndex(x=>x.url===v.url)===i)"
                ".slice(0,%d)" % limit)
            if rows:
                return rows
        except WBError:
            continue
    return []


def reddit_thread(url):
    """读帖子 + 前几条评论。只读。"""
    wb = WB(session="reddit")
    wb.nav(url, new_tab=True, group_title="ANARI-接管")
    time.sleep(4)
    return wb.js("({url:location.href,title:document.title,"
                 "body:document.body.innerText.slice(0,3000)})")


def reddit_reply_post(url, text, confirm=False):
    """在帖子里发评论。confirm=False 只预览。"""
    result = {"action": "reddit_reply", "thread": url, "chars": len(text), "preview": text[:500]}
    if not confirm:
        result["status"] = "dry_run"
        return result
    wb = WB(session="reddit")
    wb.nav(url, new_tab=True, group_title="ANARI-接管")
    time.sleep(4)
    snap = wb.snapshot()
    target = None
    for node in _walk(snap.get("tree") or []):
        name = (node.get("name") or "").lower()
        if node.get("role") == "textbox" and ("comment" in name or "join" in name or name == ""):
            target = node.get("ref")
            break
    if not target:
        result["status"] = "blocked"
        result["reason"] = "找不到评论输入框（可能未登录 / 该帖禁评）"
        return result
    wb.fill(target, text)
    result["status"] = "filled_not_submitted"
    result["hint"] = "已填入评论框但未提交；发帖不可逆，请人工点提交或显式授权。"
    return result


# ============================================================ Brevo
def brevo_contacts(count_only=False):
    """从 Brevo 后台读联系人概览。只读。"""
    wb = WB(session="brevo")
    wb.nav("https://app.brevo.com/contact/list", new_tab=True, group_title="ANARI-接管")
    time.sleep(6)
    body = wb.text()
    if count_only:
        return {"url": wb.url(), "snippet": body[:1500]}
    return {"url": wb.url(), "title": wb.title(), "body": body[:3000]}


def brevo_find(email):
    """在 Brevo 里查一个联系人（用于核对真实询盘）。只读。"""
    wb = WB(session="brevo")
    wb.nav("https://app.brevo.com/contact/list", new_tab=True, group_title="ANARI-接管")
    time.sleep(6)
    # 用后台搜索框
    snap = wb.snapshot()
    box = None
    for node in _walk(snap.get("tree") or []):
        name = (node.get("name") or "").lower()
        if node.get("role") == "textbox" and ("search" in name or "搜索" in name):
            box = node.get("ref")
            break
    if box:
        wb.fill(box, email)
        time.sleep(1)
        wb.eval("const e=new KeyboardEvent('keydown',{key:'Enter',bubbles:true});"
                "document.activeElement.dispatchEvent(e); return true;")
        time.sleep(5)
    return {"query": email, "url": wb.url(), "body": wb.text()[:3000]}


# ============================================================ helpers
def _walk(nodes):
    for n in nodes:
        yield n
        for c in n.get("children") or []:
            yield from _walk([c])


def _finish(status=0):
    """每个浏览器命令的统一收尾：关掉本次会话的标签。

    2026-11-07 教训：纪律写在文档里没用 —— 21 个标签堆着没人关。
    所以把 cleanup 绑到命令出口，而不是指望调用方记得。
    """
    try:
        import wb as _wb
        total = _wb.cleanup_all(verbose=False)
        print("  [hygiene] 已关闭 %d 个标签" % total)
    except Exception as e:  # noqa: BLE001
        print("  [hygiene] cleanup 失败: %s" % e)
    return status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=[
        "quora-search", "quora-question", "quora-answer",
        "reddit-new", "reddit-thread", "reddit-reply",
        "brevo-contacts", "brevo-find"])
    ap.add_argument("arg", nargs="?", default="")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--text", default="")
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--submit", action="store_true")
    a = ap.parse_args()

    ensure_daemon()

    if a.cmd == "quora-search":
        out = quora_search(a.arg, a.limit)
    elif a.cmd == "quora-question":
        out = quora_question(a.arg)
    elif a.cmd == "quora-answer":
        out = quora_post_answer(a.arg, a.text, confirm=a.confirm, submit=a.submit)
    elif a.cmd == "reddit-new":
        out = reddit_new(a.arg, a.limit)
    elif a.cmd == "reddit-thread":
        out = reddit_thread(a.arg)
    elif a.cmd == "reddit-reply":
        out = reddit_reply_post(a.arg, a.text, confirm=a.confirm)
    elif a.cmd == "brevo-contacts":
        out = brevo_contacts()
    elif a.cmd == "brevo-find":
        out = brevo_find(a.arg)
    else:
        out = {"error": "unknown"}

    print(json.dumps(out, ensure_ascii=False, indent=2))
    # 不可逆动作的"未确认"必须是非零退出，否则上游会当成功（2026-11-08 踩过）
    bad_status = out.get("status") in ("blocked", "submitted_unverified", "filled_not_submitted")
    return _finish(1 if bad_status else 0)


if __name__ == "__main__":
    # 即使中途抛异常也要收尾（标签不能留）
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        print("  [error] %s" % e)
        sys.exit(_finish(1))
