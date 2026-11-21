#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gmail_cleanup.py — 自动清理 Gmail 收件箱里的 Instantly 预热邮件

## 背景
Instantly 的 warmup 会持续往我们 5 个发信账号里注入"假对话"邮件（主题带随机串：
`QHHXXYR SP3ESDN`、`DAVM9XE`、`H3F6MZ7` 之类），量很大，把真实询盘/客户回复**淹没**了。
2026-11-11 用户实测：收件箱里绝大多数是这种邮件。

## 判定
主题命中任一即视为预热邮件：
- 含 `QHHXXYR`（Instantly warmup 固定串）
- 含 `warmup`
- 含「大写+数字混合的 6–10 位随机 token」（如 `DAVM9XE`、`J3TE9YH`、`Y24`）
且**不**命中 `ops/gmail-protect.txt` 里的保护词（询盘摘要 / New inquiry / 客户回复关键词…）。

## 技术要点（踩过的坑）
- Gmail 现代 UI 的 `el.click()` **无效**，必须派发 pointerdown/mousedown/pointerup/mouseup 后 click
- 行文本用 `.bog` 的 **textContent**（`innerText` 因懒渲染返回空）
- 行元素 `tr.zA`；全选框 `[role=checkbox][0]`；删除按钮 aria-label=`Delete`
- 每页约 50 行、命中 30–40 封；单轮删完需重新导航（Gmail 不会自动补页）

## 用法
  python3 scripts/tools/gmail_cleanup.py              # 默认最多 20 页
  python3 scripts/tools/gmail_cleanup.py --dry        # 只统计不删
  python3 scripts/tools/gmail_cleanup.py --pages 5    # 限制轮数
退出码：0 成功 / 1 桥不可用或出错
"""
import argparse
import json
import os
import sys
import time

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(WS, "scripts", "browser"))
PROTECT_FILE = os.path.join(WS, "ops", "gmail-protect.txt")

PICK_JS = """
function realClick(el){var r=el.getBoundingClientRect();
 var o={bubbles:true,cancelable:true,clientX:r.left+r.width/2,clientY:r.top+r.height/2,view:window};
 ['pointerdown','mousedown','pointerup','mouseup'].forEach(function(t){el.dispatchEvent(new (t.indexOf('pointer')===0?PointerEvent:MouseEvent)(t,o));});
 el.click();}
var PROTECT = %s;
function protected_(s){ for (var i=0;i<PROTECT.length;i++){ if (PROTECT[i] && s.indexOf(PROTECT[i])>=0) return true; } return false; }
function isWarmup(s){
  if (protected_(s)) return false;
  if (/QHHXXYR/i.test(s)) return true;
  if (/warmup/i.test(s)) return true;
  return !!s.match(/\\b(?=[A-Z0-9]{6,10}\\b)(?=[A-Z0-9]*[A-Z])(?=[A-Z0-9]*[0-9])[A-Z0-9]{6,10}\\b/);
}
var rows=Array.from(document.querySelectorAll('tr.zA'));
var picked=[];
rows.forEach(function(tr){
  var b=tr.querySelector('.bog'); var s=((b&&b.textContent)||'').trim();
  if(isWarmup(s)) picked.push({tr:tr, subj:s});
});
picked.forEach(function(p){ var cb=p.tr.querySelector('[role=checkbox]'); if(cb) realClick(cb); });
return JSON.stringify({scanned:rows.length, picked:picked.length,
  samples:picked.slice(0,3).map(function(p){return p.subj.slice(0,40);})});
"""

DEL_JS = """
function realClick(el){var r=el.getBoundingClientRect();
 var o={bubbles:true,cancelable:true,clientX:r.left+r.width/2,clientY:r.top+r.height/2,view:window};
 ['pointerdown','mousedown','pointerup','mouseup'].forEach(function(t){el.dispatchEvent(new (t.indexOf('pointer')===0?PointerEvent:MouseEvent)(t,o));});
 el.click();}
var b=Array.from(document.querySelectorAll('[role=button],button')).find(function(x){
  return ((x.getAttribute('aria-label')||x.getAttribute('data-tooltip')||x.innerText||'').trim()==='Delete');});
if(b){realClick(b); return 'deleted';} return 'no_delete_button';
"""


def protect_words():
    words = []
    if os.path.exists(PROTECT_FILE):
        for line in open(PROTECT_FILE, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                words.append(line)
    return words or ["询盘摘要", "New inquiry"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=20)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--query", default="QHHXXYR",
                    help="Gmail 搜索式；默认 QHHXXYR（Instantly warmup 固定串，实测可命中全部预热邮件；"
                         "会扫 in:anywhere 含归档/各类标签，保护词仍生效）")
    a = ap.parse_args()
    try:
        from wb import WB, cleanup_all
    except Exception as e:  # noqa: BLE001
        print(f"❌ 无法加载 wb：{e}")
        return 1
    pick_js = PICK_JS % json.dumps(protect_words(), ensure_ascii=False)
    wb = WB(session="gmail-cleanup")
    total = 0
    try:
        for i in range(a.pages):
            try:
                import urllib.parse as _up
                wb.nav("https://mail.google.com/mail/u/0/#search/" + _up.quote(a.query),
                       new_tab=(i == 0))
            except Exception as e:  # noqa: BLE001
                print(f"  ⚠️ 第 {i+1} 轮导航失败：{str(e)[:80]}")
                time.sleep(8)
                continue
            # 等列表真正渲染（Gmail/Edge 实测 7s 不够，曾把"未渲染"误判为"已清空"）
            rows = 0
            for _ in range(10):
                time.sleep(3)
                try:
                    rows = int(wb.eval("return document.querySelectorAll('tr.zA').length;") or 0)
                except Exception:  # noqa: BLE001
                    rows = 0
                if rows > 0:
                    break
            try:
                d = json.loads(wb.eval(pick_js) or "{}")
            except Exception as e:  # noqa: BLE001
                print(f"  ⚠️ 第 {i+1} 轮读取失败：{str(e)[:80]}")
                continue
            n = d.get("picked", 0)
            if not n:
                empty = False
                try:
                    txt = wb.eval("return (document.body.innerText||'').slice(0,800);") or ""
                    empty = ("没有" in txt and "结果" in txt) or ("No messages" in txt) or ("No conversations" in txt)
                except Exception:  # noqa: BLE001
                    pass
                if d.get("scanned", 0) == 0 and not empty:
                    print(f"  ⚠️ 第 {i+1} 轮：列表未渲染，重试")
                    continue
                print(f"  ✅ 第 {i+1} 轮：该范围已无预热邮件（扫描 {d.get('scanned')} 行）")
                break
            if a.dry:
                print(f"  [dry] 第 {i+1} 轮：命中 {n} 封 {d.get('samples')}")
                total += n
                # dry 模式下只看一页，避免重复统计
                break
            time.sleep(1.5)
            wb.eval(DEL_JS)
            total += n
            time.sleep(3.5)
            print(f"  第 {i+1} 轮：删除 {n} 封 {('' if not d.get('samples') else '· ' + str(d['samples'][:1]))}")
    finally:
        try:
            cleanup_all(verbose=False)
        except Exception:  # noqa: BLE001
            pass
    print(f"  合计{'（dry 统计）' if a.dry else '删除'} {total} 封")
    # 2026-11-21：把结果落盘，让 watchdog/播报能看见（此前跑没跑、删多少都不可见）
    try:
        import datetime as _dt
        import json as _json
        out_dir = os.path.join(WS, "08-execution", "tech")
        os.makedirs(out_dir, exist_ok=True)
        rec = {"date": _dt.date.today().isoformat(),
               "at": _dt.datetime.now().isoformat(timespec="seconds"),
               "query": a.query, "deleted": total, "dry": bool(a.dry)}
        with open(os.path.join(out_dir, "gmail-cleanup-%s.json" % rec["date"]), "w", encoding="utf-8") as f:
            _json.dump(rec, f, ensure_ascii=False, indent=1)
    except Exception as e:  # noqa: BLE001
        print(f"  （补记清理结果失败：{e}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
