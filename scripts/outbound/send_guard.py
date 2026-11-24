#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""send_guard.py — 对外发信前的本地去重闸门（2026-11-24 新增）

## 为什么有这个
2026-11-24 我用 Gmail 网页给 contribute@renwaves.com 连发了两封同样的回信：
第一次脚本的"正文是否填入"检测用了精确的 aria-label 匹配，页面里是别的标签 → 判为 NO_EDITOR，
但正文其实已填入，Send 已发；随后重试又发了一次。**收件人收到两封一样的邮件。**

这条闸门只做一件事：**同一个收件人在 N 小时内已经发过，就直接拒绝**，
不再依赖"我这次是不是点成功了"这种主观判断。

## 用法
  python3 scripts/outbound/send_guard.py check  <email> [--hours 24]   # 0 可发 / 3 已发过
  python3 scripts/outbound/send_guard.py record <email> --subject "..."
"""
import json, os, sys, datetime as dt

WS = "/Users/kerrychu/anari-charge-website"
LEDGER = os.path.join(WS, "08-execution/outbound/replies/sent-ledger.jsonl")

def load():
    rows = []
    if os.path.exists(LEDGER):
        for line in open(LEDGER, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows

def main():
    if len(sys.argv) < 3:
        print("用法: send_guard.py check <email> [--hours N] | record <email> --subject ...")
        return 2
    cmd, email = sys.argv[1], sys.argv[2].strip().lower()
    hours = 24.0
    if "--hours" in sys.argv:
        hours = float(sys.argv[sys.argv.index("--hours") + 1])
    rows = load()
    if cmd == "check":
        now = dt.datetime.now(dt.timezone.utc)
        for r in rows:
            if str(r.get("to", "")).lower() != email:
                continue
            try:
                t = dt.datetime.fromisoformat(str(r.get("at")))
            except Exception:
                continue
            if (now - t).total_seconds() < hours * 3600:
                print(f"⛔ 拒绝发送：{email} 在 {hours:.0f}h 内已发过（{t.isoformat(timespec='minutes')}, subject={r.get('subject','')[:50]}）")
                return 3
        print(f"✅ 可发送：{email} 在 {hours:.0f}h 内无发送记录")
        return 0
    if cmd == "record":
        subj = ""
        if "--subject" in sys.argv:
            subj = sys.argv[sys.argv.index("--subject") + 1]
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        rec = {"at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               "to": email, "subject": subj}
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"已记录发送: {email}")
        return 0
    print("未知命令:", cmd)
    return 2

if __name__ == "__main__":
    sys.exit(main())
