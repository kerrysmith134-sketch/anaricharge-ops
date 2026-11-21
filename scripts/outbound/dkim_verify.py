#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dkim_verify.py — 用真实发出的一封信验证 DKIM 是否生效（不靠猜测）

## 为什么需要
Google Admin 显示 "Authenticating email with DKIM" **只是 Google 认为已开启**，
不等于我们的信真的带了签名。唯一硬证据是：**从 kerry@anaricharge.com 真发一封信，
在收信端读原始头**，看有没有 `DKIM-Signature: d=anaricharge.com` 以及接收方是否 dkim=pass。

## 怎么做到（三次踩坑后的可行路径）
1. 用 mail.tm 公开 API 建一个**一次性收件箱**（无需注册、不留我们自己的邮箱）
2. 用 Instantly 的 `/emails/test` 端点从我们的真实发信账号发一封测试信
   （payload 必须是 `{eaccount, to_address_email_list, subject, body:{text,html}}`）
3. 轮询收件箱 → 取 `sourceUrl` 拿原始 EML → 解析 `DKIM-Signature` 与 `Authentication-Results`
4. 删除临时账号（不留下残留）

## 用法
  python3 scripts/outbound/dkim_verify.py            # 完整验证
  python3 scripts/outbound/dkim_verify.py --raw       # 同时打印头
退出码：0 = DKIM 签名存在且域名正确；1 = 缺失或域名不对
"""
import argparse
import json
import random
import re
import string
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)) if (os := __import__("os")) else "."
sys.path.insert(0, HERE)
import instantly_client as ic  # noqa: E402

MAIL = "https://api.mail.tm"
SENDER = "kerry@anaricharge.com"
TIMEOUT_S = 180


def api(path, method="GET", body=None, token=None, raw=False):
    req = urllib.request.Request(
        MAIL + path, method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"Content-Type": "application/json", "Accept": "*/*",
                 **({"Authorization": "Bearer " + token} if token else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read().decode("utf-8", "ignore")
    return data if raw else json.loads(data)


def make_inbox():
    doms = api("/domains")
    items = doms.get("hydra:member") if isinstance(doms, dict) else doms
    dom = items[0]["domain"]
    addr = "dkim-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8)) + "@" + dom
    pw = "AnariDkim" + str(int(time.time())) + "!"
    api("/accounts", "POST", {"address": addr, "password": pw})
    tok = api("/token", "POST", {"address": addr, "password": pw})["token"]
    return addr, pw, tok


def send_test(to_addr):
    body = {"eaccount": SENDER, "to_address_email_list": [to_addr],
            "subject": "DKIM header verification",
            "body": {"text": "DKIM header check", "html": "<p>DKIM header check</p>"}}
    return ic.call("/emails/test", "POST", body)


def parse_headers(eml_wrapped):
    """mail.tm 的 source 接口返回 JSON，真正 EML 在 data 字段里。"""
    text = eml_wrapped.strip()
    if text.startswith("{"):
        try:
            text = json.loads(text)["data"]
        except (ValueError, KeyError):
            pass
    text = text.replace("\r", "")
    hdr = text.partition("\n\n")[0]
    merged = []
    for line in hdr.split("\n"):
        if line[:1] in (" ", "\t") and merged:
            merged[-1] += " " + line.strip()
        else:
            merged.append(line)
    return text, merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", action="store_true")
    ap.add_argument("--keep", action="store_true", help="保留临时邮箱（排查用）")
    a = ap.parse_args()

    addr, pw, tok = make_inbox()
    print(f"一次性收件箱：{addr}")
    try:
        r = send_test(addr)
        print(f"Instantly /emails/test → {json.dumps(r, ensure_ascii=False)[:80]}")
    except SystemExit as e:
        print(f"❌ 发送失败：{str(e)[:200]}")
        return 1

    msg = None
    deadline = time.time() + TIMEOUT_S
    while time.time() < deadline:
        time.sleep(12)
        msgs = api("/messages", token=tok)
        items = msgs.get("hydra:member") if isinstance(msgs, dict) else msgs
        if items:
            msg = items[0]
            break
        print("  等待收信…")
    if not msg:
        print(f"❌ {TIMEOUT_S}s 内没收到信（可能被拒或延迟）")
        return 1

    print(f"收到：{msg.get('subject')} · from {(msg.get('from') or {}).get('address')}")
    eml = api(msg["sourceUrl"], token=tok, raw=True)
    text, hdrs = parse_headers(eml)
    dkim = next((h for h in hdrs if h.lower().startswith("dkim-signature")), "")
    auth = next((h for h in hdrs if h.lower().startswith("authentication-results")), "")
    d = (re.search(r"d=([A-Za-z0-9.\-]+)", dkim) or [None, ""])[1]
    s = (re.search(r"s=([A-Za-z0-9.\-]+)", dkim) or [None, ""])[1]
    status = (re.search(r"dkim=(\w+)", auth, re.I) or [None, "接收方未返回"])[1]

    print(f"\nDKIM-Signature: {'存在' if dkim else '缺失'} · d={d or '?'} · s={s or '?'}")
    print(f"Authentication-Results dkim=: {status}")
    if a.raw:
        print("\n--- 头（前 1200 字符）---")
        print("\n".join(hdrs)[:1200])

    ok = bool(dkim) and d == "anaricharge.com"
    print(f"\n{'✅ DKIM 生效（我们的域名在被签名）' if ok else '❌ DKIM 未生效'}")
    if not a.keep:
        try:
            api("/accounts/" + msg["accountId"], "DELETE", token=tok)
            print("临时邮箱已删除")
        except Exception:  # noqa: BLE001
            pass
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
