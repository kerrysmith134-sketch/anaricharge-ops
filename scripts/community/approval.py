#!/usr/bin/env python3
"""approval.py — 社媒草稿的「批量审批」队列。

## 为什么需要
R6 规定：发帖是不可逆外部动作，必须逐次人工确认或显式授权。
于是每日社媒档位（R5/P6）只能出草稿、等授权 —— **逐条等授权 = 实际不产出**。
2026-11-07 实测：两个社媒档位投递 0 次、上线以来只发了 1 条。

## 解决方式：把「逐条授权」换成「批量授权」
1. 档位跑完把草稿写进 `08-execution/community/pending/<id>.md`
   （文件头一行 JSON：platform / question_url / link / created）
2. 用户一句话「这批发吧」→ 一条命令全部发布
3. 发布成功写 `quora-log.jsonl`，文件移到 `published/`

**没有降低审查强度**：人还是要看内容，但从"每条一次"变成"一批一次"。

## 用法
  python3 scripts/community/approval.py list              # 看待发草稿（含重复标记）
  python3 scripts/community/approval.py preflight         # 发布前只读检查（能答吗/是否已答）
  python3 scripts/community/approval.py publish q-20261108-1 q-20261108-2
  python3 scripts/community/approval.py publish --all
  python3 scripts/community/approval.py status
"""
import json
import os
import re
import subprocess
import sys
import datetime as dt
import time

WS = "/Users/kerrychu/anari-charge-website"
PEND = os.path.join(WS, "08-execution", "community", "pending")
PUB = os.path.join(WS, "08-execution", "community", "published")
LOG = os.path.join(WS, "08-execution", "community", "quora-log.jsonl")
# 结果不确定（502/超时/异常可能发生在提交之后）的草稿放这里：不自动重发，等人工核。
UNCERT = os.path.join(WS, "08-execution", "community", "uncertain")
OPS = os.path.join(WS, "scripts", "browser", "ops.py")


def parse(path):
    """文件第 1 行是 JSON meta，空行之后是正文。"""
    raw = open(path, encoding="utf-8").read()
    # 第一行是 JSON meta；其后可能是空白行（含只有空格的行），再是正文
    lines = raw.splitlines()
    meta, body_start = {}, 1
    if lines:
        try:
            meta = json.loads(lines[0])
        except Exception:  # noqa: BLE001
            meta = {}
    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1
    body = "\n".join(lines[body_start:]).strip()
    return meta, body, raw


def answered_urls():
    """已发布过的问题 URL（去重依据）——从 quora-log.jsonl 读。"""
    out = set()
    if os.path.exists(LOG):
        for line in open(LOG, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            # 只有"确认已发布"的才计入去重；失败记录不能挡住重试
            # （2026-11-08 踩过：失败的 3 条被当成已答，dry-run 直接 0 条）
            if (r.get("status") or "") != "published":
                continue
            q = (r.get("question") or "").strip().rstrip("/")
            if q:
                out.add(q)
    return out


def items():
    out = []
    for fn in sorted(os.listdir(PEND)):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(PEND, fn)
        meta, body, _ = parse(p)
        out.append({"id": fn[:-3], "path": p, "meta": meta, "body": body})
    return out


def cmd_list():
    its = items()
    if not its:
        print("待发队列为空。")
        return 0
    done = answered_urls()
    print(f"待发草稿 {len(its)} 条：\n")
    for it in its:
        m = it["meta"]
        if (m.get("question_url") or "").rstrip("/") in done:
            print(f"  [{it['id']}] ⚠️ 该问题已经答过 → 会被跳过（重复）\n")
            continue
        print(f"  [{it['id']}] {m.get('platform','?')} · {m.get('created','?')}")
        print(f"     问题: {m.get('question_url','(无)')}")
        if m.get("link"):
            print(f"     回链: {m['link']}")
        print(f"     正文 {len(it['body'])} 字，开头：{it['body'][:70].replace(chr(10),' ')}")
        print()
    print("发布： python3 scripts/community/approval.py publish <id> [id...]  |  publish --all")
    return 0


def _walk(nodes):
    for n in nodes or []:
        yield n
        for c in (n.get("children") or []):
            yield from _walk([c])


def preflight(its):
    """发布前只读检查：能否看到「Answer」入口（= 登录有效且问题可答）。

    判据与 `ops.py quora_post_answer` 保持一致：找按钮文本匹配
    `/^(Answer|回答)(\s*·\s*\d+)?$/` 的入口（2026-11-09 起已答问题的题头按钮
    带答案数，文本为 `Answer · 10`；旧的精确 `=='Answer'` 让所有已答题误判不可发）。
    这里**只看不点**，避免留下未提交草稿。
    """
    sys.path.insert(0, os.path.join(WS, "scripts", "browser"))
    from wb import WB, cleanup_all
    import time as _t
    wb = WB(session="preflight")
    bad = 0
    try:
        for it in its:
            url = it["meta"].get("question_url") or ""
            if not url:
                print(f"  ❌ {it['id']} 缺 question_url")
                bad += 1
                continue
            try:
                wb.nav(url, new_tab=False)
                _t.sleep(5)
                title = wb.eval("return document.title.slice(0,70);") or ""
                entry = wb.eval(r"""
                  var norm=function(s){return (s||'').replace(/\s+/g,' ').trim();};
                  var re=/^(Answer|回答)(\s*·\s*\d+)?$/;
                  return Array.from(document.querySelectorAll('[role=button],button,a'))
                    .filter(function(e){return re.test(norm(e.innerText)) && e.getBoundingClientRect().height>0;})
                    .map(function(e){return norm(e.innerText);}).slice(0,5);
                """) or []
                has_answer = bool(entry)
                body_txt = wb.eval("return (document.body.innerText||'').slice(0,20000);") or ""
                gone = bool(re.search(r"Page Not Found|deleted|removed", body_txt[:400]))
                answered_mark = "you've written an answer" in body_txt.lower()
                in_log = (it["meta"].get("question_url") or "").rstrip("/") in answered_urls()
                if answered_mark or in_log:
                    print(f"  ⚠️ {it['id']} — 已答过（重复），发布时会跳过 · {title}")
                    bad += 1
                    continue
                ok = bool(has_answer) and not gone
                reason = "" if ok else (
                    "问题页不存在/已删除" if gone else
                    "看不到 Answer 入口（未登录，或该问题不允许回答）")
                print(("  ✅ " if ok else "  ❌ ") + it["id"] + " — " + title
                      + ("" if ok else " · " + reason))
                bad += 0 if ok else 1
            except Exception as e:  # noqa: BLE001
                print(f"  ❌ {it['id']} 打不开: {type(e).__name__}: {str(e)[:100]}")
                bad += 1
        print(f"\n预检 {len(its)} 条 | 有问题 {bad} 条")
        return 0 if bad == 0 else 1
    finally:
        try:
            cleanup_all(verbose=False)
        except Exception:  # noqa: BLE001
            pass

def cmd_status():
    its = items()
    pubs = [f for f in os.listdir(PUB)] if os.path.isdir(PUB) else []
    unc = ([f for f in os.listdir(UNCERT) if f.endswith(".md")]
           if os.path.isdir(UNCERT) else [])
    n_log = 0
    if os.path.exists(LOG):
        for line in open(LOG, encoding="utf-8"):
            if line.strip():
                n_log += 1
    print(f"待发 {len(its)} 条 | 已发布文件 {len(pubs)} 个 | 日志 {n_log} 条"
          + (f" | ⚠️ 待人工核 {len(unc)} 条（uncertain/，不会自动重发）" if unc else ""))
    return 0


def ensure_bridge():
    """发布前确认 WebBridge 守护进程可用。

    2026-11-08 实测：daemon 在连续会话后偶发 502 Bad Gateway，
    此时 ops.py 会失败，若不重试会被误判成"页面没有 Answer 入口"。
    """
    import subprocess as _sp
    BIN = os.path.expanduser("~/.kimi-webbridge/bin/kimi-webbridge")
    for attempt in range(3):
        try:
            r = _sp.run([sys.executable, os.path.join(WS, "scripts", "browser", "wb.py"), "health"],
                        capture_output=True, text=True, timeout=30)
            if '"healthy": true' in (r.stdout or ""):
                return True
        except Exception:  # noqa: BLE001
            pass
        try:
            _sp.run([BIN, "start"], capture_output=True, text=True, timeout=60)
        except Exception:  # noqa: BLE001
            pass
        time.sleep(6)
    return False


def _canonical(question_url):
    """问题页 canonical：`/unanswered/<slug>` 回答后会被重定向到 `<slug>`。"""
    return re.sub(r"/unanswered/", "/", question_url or "")


def _snippet(body, n=50):
    for ln in (body or "").split("\n"):
        s = ln.strip()
        if len(s) > 40:
            return s[:n]
    return (body or "").strip()[:n]


def verify_published(question_url, body):
    """独立复核「我们的答案是否已在线」——只看页面事实，不信 status / 退出码。

    为什么需要（2026-11-09 实测）：`approval.py publish` 报过 502 / 未确认，但答案
    其实已经在线；11-08 反向也出过"报成功实际没发"。两边都错在把结果托付给一次退出码。
    判据 = **三证**：①正文片段命中 ②「You've written an answer」横幅 或 /answer/ permalink。
    只读：打开 canonical 问题页、重试错误页（"Try again"/限流白页），不点任何按钮。
    返回 (ok, detail, answer_url)。
    """
    snippet = _snippet(body)
    if not snippet:
        return False, "正文为空，无法复核", ""
    url = _canonical(question_url)
    sys.path.insert(0, os.path.join(WS, "scripts", "browser"))
    from wb import WB, cleanup_all
    import time as _t

    wb = WB(session="verify")
    txt = ""
    try:
        last_err = ""
        for attempt in range(4):
            try:
                wb.nav(url, new_tab=False)
                _t.sleep(8)
                txt = wb.eval("return (document.body.innerText||'').slice(0,20000);") or ""
            except Exception as e:  # noqa: BLE001
                # WebBridge 偶发 502（已知问题）→ 重试，不把网络错误当成"没发布"
                last_err = type(e).__name__
                _t.sleep(5)
                continue
            bad_page = len(txt) < 1200 or "Try again" in txt[:400]
            if not bad_page:
                break
        if not txt:
            return False, "复核页面打不开: %s" % (last_err or "unknown"), ""
        low = txt.lower()
        banner = "you've written an answer" in low
        snippet_ok = snippet in txt
        answer_url = ""
        try:
            links = wb.eval(
                "return Array.from(document.querySelectorAll('a[href*=\"/answer/\"]'))"
                ".map(function(a){return a.href;}).slice(0,5);") or []
            if links:
                answer_url = links[0]
        except Exception:  # noqa: BLE001
            pass
        permalink = bool(answer_url) or "/answer/" in txt
        ok = snippet_ok and (banner or permalink)
        detail = "snippet=%s banner=%s permalink=%s" % (snippet_ok, banner, permalink)
        return ok, detail, answer_url
    finally:
        try:
            cleanup_all(verbose=False)
        except Exception:  # noqa: BLE001
            pass

def _archive_and_log(it, answer_url, note):
    """发布确认后：队列文件移到 published/ + 写台账。"""
    m = it["meta"]
    url = m.get("question_url") or ""
    os.makedirs(PUB, exist_ok=True)
    base, ext = os.path.splitext(os.path.basename(it["path"]))
    dst = os.path.join(PUB, base + ext)
    n = 2
    while os.path.exists(dst):  # 防同日并行会话同 id 覆盖（2026-11-14 实际踩到）
        dst = os.path.join(PUB, "%s-%d%s" % (base, n, ext))
        n += 1
    os.replace(it["path"], dst)
    rec = {"date": dt.date.today().isoformat(),
           "question": url,
           "answer": answer_url or "",
           "link": m.get("link", ""),
           "words": len(it["body"].split()),
           "status": "published",
           "note": note}
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _quarantine(it, why):
    """结果不确定的草稿移出 pending/：不自动重发（重发 = 真实重复发帖风险），留待人工核。"""
    os.makedirs(UNCERT, exist_ok=True)
    dst = os.path.join(UNCERT, os.path.basename(it["path"]))
    os.replace(it["path"], dst)
    try:
        note = os.path.join(UNCERT, os.path.basename(it["path"]) + ".why.txt")
        with open(note, "w", encoding="utf-8") as f:
            f.write(why + "\n")
    except Exception:  # noqa: BLE001
        pass
    return dst


def publish_one(it, dry=False):
    m = it["meta"]
    url = m.get("question_url") or ""
    if not url:
        return False, "缺 question_url"
    if dry:
        return True, "dry-run（未提交）"
    if not ensure_bridge():
        return False, "WebBridge 守护进程不可用（502/未起）——已重试 3 次，未能发布"
    cmd = [sys.executable, OPS, "quora-answer", url, "--text", it["body"],
           "--confirm", "--submit"]
    r = subprocess.run(cmd, cwd=WS, capture_output=True, text=True, timeout=300)
    out = r.stdout or ""
    # 坑（2026-11-08 实测）：ops.py 的 quora-answer 即使返回 status=blocked 也 exit 0，
    # 只看 returncode 会把"登录态失效、根本没发出去"报成"已发布"——我们真的这样誤报过一次。
    # 所以必须解析 JSON 的 status 字段，只有 published 才算成功。
    status = ""
    payload = {}
    try:
        start = out.find("{")
        payload = json.loads(out[start:]) if start >= 0 else {}
        status = (payload.get("status") or "").lower()
    except Exception:  # noqa: BLE001
        payload = {}
    hard_err = r.returncode != 0 or '"error"' in out
    if status != "published":
        verify = (payload or {}).get("verify") or {}
        why = ((payload or {}).get("reason")
               or json.dumps(verify, ensure_ascii=False)[:200]
               or status
               or (out or r.stderr or "")[-200:]
               or "无状态")
        # 2026-11-09：ops.py 报失败 ≠ 没发出去（实测：502/超时发生在**提交之后**，
        # 报"0 条发布"但 2/2 其实在线）。判失败之前先独立复核页面事实：
        #   · 确认在线 → 归档 + 记台账（避免下一次 --all 重复发）；
        #   · 结果不确定（error/timeout/未验证）→ 移入 uncertain/，绝不自动重发；
        #   · 明确没发（blocked / filled_not_submitted）→ 留在 pending/ 等重试。
        okv, whyv, ans_url = False, "未执行", ""
        try:
            okv, whyv, ans_url = verify_published(url, it["body"])
        except Exception as e:  # noqa: BLE001
            whyv = "复核异常 %s" % type(e).__name__
        if okv:
            _archive_and_log(it, ans_url,
                             f"ops.py 报 {status or 'error'}，独立复核三证确认已发布（{whyv}）")
            return True, "已发布（ops.py 报失败，页面复核确认在线）"
        if hard_err or status in ("", "error", "submitted_unverified"):
            _quarantine(it, f"status={status or 'error'} why={why} verify={whyv}")
            return False, (f"结果不确定（status={status or 'error'}）：{why}；复核：{whyv}；"
                           "已移入 uncertain/ 待人工核一次，不会自动重发")
        return False, f"未确认发布（status={status or '?'}）：{why}；复核：{whyv}"
    # 尽量从 ops.py 的输出里取回 permalink / 回答 URL，取不到就留空（不编造）
    answer_url = ""
    try:
        start = out.find("{")
        payload = json.loads(out[start:]) if start >= 0 else {}
        for k in ("answer_url", "permalink", "url", "answer"):
            v = payload.get(k)
            if isinstance(v, str) and v.startswith("http"):
                answer_url = v
                break
    except Exception:  # noqa: BLE001
        pass
    _archive_and_log(it, answer_url, "batch-approval via approval.py")
    return True, "已发布"


def cmd_publish(ids, dry=False):
    its = items()
    if not its:
        print("没有待发草稿。")
        return 0
    if "--all" in sys.argv:
        target = its
    else:
        want = set(ids)
        target = [i for i in its if i["id"] in want]
        if not target:
            print("没有匹配的 id。用 list 查看可用 id。")
            return 2
    done = answered_urls()
    target = [it for it in target
              if (it["meta"].get("question_url") or "").rstrip("/") not in done]
    ok = bad = 0
    for it in target:
        good, msg = publish_one(it, dry)
        print(("  ✅ " if good else "  ❌ ") + it["id"] + " — " + msg)
        ok += 1 if good else 0
        bad += 0 if good else 1
    print(f"\n发布 {ok} 条 | 失败 {bad} 条")
    return 0 if bad == 0 else 1


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else "list"
    if a == "list":
        return cmd_list()
    if a == "status":
        return cmd_status()
    if a == "preflight":
        its = items()
        if not its:
            print("队列为空。"); return 0
        return preflight(its)
    if a == "publish":
        dry = "--dry" in sys.argv
        ids = [x for x in sys.argv[2:] if not x.startswith("--")]
        return cmd_publish(ids, dry)
    raise SystemExit("用法: list | status | preflight | publish <id...|--all> [--dry]")


if __name__ == "__main__":
    sys.exit(main())
