#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reg_watch.py — 法规/监管源变化监测（A04 Country & Regulatory Watch）

## 为什么用「抓页面 + 哈希比对」而不是解析
监管站点结构各异、还常改版；解析会天天坏。真正要回答的问题只有一个：
**"这个页面和上次比，变了没有？"** 变了就人工看，没变就不看。
所以只存正文哈希 + 长度，变化时打印前后摘录供判断。

## 状态文件
`08-execution/tech/regwatch-state.json`：id → {hash, len, checked_at, changed_at}

## 用法
  python3 scripts/metrics/reg_watch.py                # 检查全部源
  python3 scripts/metrics/reg_watch.py --only eu-afir
  python3 scripts/metrics/reg_watch.py --json
退出码：0 无变化或首次建立基线；2 有源发生变化（需人工看）
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(WS, "ops", "regwatch-sources.json")
STATE = os.path.join(WS, "08-execution", "tech", "regwatch-state.json")
UA = "AnariOps-RegWatch/1.0 (+https://www.anaricharge.com; monitoring public regulator pages)"



# 反爬/JS 挑战页特征：命中说明拿到的是"请启用 JavaScript"页，不是正文。
# 2026-11-11 踩过：EUR-Lex 对 urllib 返回 157 字符挑战页，被当成"变化"写进基线，
# 第二天拿到真页面（185k）反而误报"原文变了"。这类响应必须视为 blocked，不得更新基线。
BOT_CHALLENGE = (
    "verify that you're not a robot",
    "JavaScript is disabled",
    "Enable JavaScript and then reload",
    "Attention Required",
    "Just a moment...",
)


def is_bot_challenge(body):
    head = (body or "")[:2000]
    return len(head) < 4000 and any(k.lower() in head.lower() for k in BOT_CHALLENGE)

def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(s, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def fetch_text(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    try:
        txt = raw.decode("utf-8", "ignore")
    except Exception:  # noqa: BLE001
        txt = raw.decode("latin-1", "ignore")
    txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", txt, flags=re.S | re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def digest(txt):
    return hashlib.sha256(txt.encode("utf-8", "ignore")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    cfg = json.load(open(SRC, encoding="utf-8"))
    state = load_state()
    changed, failed, first, blocked = [], [], [], []
    checked = 0
    for s in cfg.get("sources") or []:
        if a.only and a.only != s.get("id"):
            continue
        checked += 1
        sid, url = s.get("id"), s.get("url")
        try:
            txt = fetch_text(url)
            h = digest(txt)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            failed.append({"id": sid, "url": url, "error": f"{type(e).__name__}: {str(e)[:80]}"})
            continue
        # 反爬挑战页：不写基线、不算变化，如实计入 blocked（2026-11-11 修）
        if is_bot_challenge(txt):
            blocked.append({"id": sid, "url": url, "reason": "bot_challenge",
                            "note": "拿到的是 JS 挑战页，不是正文；基线未更新"})
            continue
        prev = state.get(sid) or {}
        now = dt.date.today().isoformat()
        if not prev.get("hash"):
            first.append({"id": sid, "market": s.get("market"), "len": len(txt)})
            state[sid] = {"hash": h, "len": len(txt), "checked_at": now, "changed_at": None}
        elif prev["hash"] != h:
            changed.append({
                "id": sid, "market": s.get("market"), "label": s.get("label"),
                "url": url, "why": s.get("why"),
                "len_before": prev.get("len"), "len_after": len(txt),
                "changed_at": now, "excerpt": txt[:400],
            })
            state[sid] = {"hash": h, "len": len(txt), "checked_at": now, "changed_at": now}
        else:
            state[sid] = {**prev, "checked_at": now}
        save_state(state)

    result = {"checked": checked, "first_baseline": first, "changed": changed, "failed": failed, "blocked": blocked}
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        print(f"法规监测：检查 {checked} 个源")
        if first:
            print(f"\n🆕 首次建立基线 {len(first)} 个：")
            for x in first: print(f"    {x['id']} ({x['market']}) 正文 {x['len']} 字符")
        if changed:
            print(f"\n🔔 有变化 {len(changed)} 个（需人工看）：")
            for x in changed:
                print(f"    {x['id']} ({x['market']}) {x['len_before']}→{x['len_after']} 字符")
                print(f"      {x['url']}")
                print(f"      为什么要看：{x['why']}")
                print(f"      摘录：{x['excerpt'][:160]}…")
        if blocked:
            print(f"\n🚫 被反爬挡住 {len(blocked)} 个（不是变化，基线未更新，需人工/浏览器看）：")
            for b in blocked:
                print(f"    {b['id']}  {b.get('note', '')}")
        if failed:
            print(f"\n⚠️ 抓取失败 {len(failed)} 个（不算变化，如实记录）：")
            for x in failed:
                print(f"    {x['id']}: {x['error']}")
        if not (changed or failed or blocked):
            print("\n✅ 全部无变化")
    return 2 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
