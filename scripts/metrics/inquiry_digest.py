#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""inquiry_digest.py — 每日询盘摘要邮件（北京时间口径）

## 为什么有这个
2026-11-11 用户实测：即时通知能发出（Brevo 显示 delivered）但人看不到，
而询盘数据真正的主记录在 D1。与其依赖"即时推送被看见"，不如每天固定一封摘要：
昨天有哪些询盘、完整字段是什么、账本状态是什么。

## 口径
- **按北京时间日界**切分（用户在中国），查询用对应 UTC 区间
- 只统计 D1 `submissions`（主记录），不从邮件/CRM 反推
- 0 条时默认**不发信**（避免每天一封空邮件），只在终端输出；`--force` 可强制发一封空摘要做测试

## 发送通道
走 Instantly 的 `/emails/test`（经我们自己的 Google 账号中继）：
SPF `_spf.google.com` + DKIM `s=google` 都是 anaricharge.com，实测可正常进收件箱。
Brevo 通道因 SPF 未 include Brevo 易进垃圾箱，故不用于此摘要。

## 用法
  python3 scripts/metrics/inquiry_digest.py                 # 昨天（北京）
  python3 scripts/metrics/inquiry_digest.py --date 2026-11-11
  python3 scripts/metrics/inquiry_digest.py --dry           # 只打印不发
  python3 scripts/metrics/inquiry_digest.py --force         # 0 条也发
退出码：0 成功（含 0 条跳过）/ 1 发送失败
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(WS, "scripts", "outbound"))
sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))

BJ = dt.timezone(dt.timedelta(hours=8))
OUT_DIR = os.path.join(WS, "08-execution", "inquiry", "digests")


def d1(sql):
    r = subprocess.run([sys.executable, os.path.join(WS, "scripts/metrics/d1_query.py"), "sql", sql],
                       capture_output=True, text=True, timeout=180)
    rows = []
    for line in (r.stdout or "").split("\n"):
        line = line.strip()
        if line.startswith("{"):
            try:
                rows.append(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    return rows


def ledger():
    p = os.path.join(WS, "08-execution", "inquiry", "lifecycle.jsonl")
    out = {}
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                out[rec["submission_id"]] = rec
            except Exception:  # noqa: BLE001
                pass
    return out


def window(day):
    start_bj = dt.datetime.combine(day, dt.time(0, 0), tzinfo=BJ)
    end_bj = start_bj + dt.timedelta(days=1)
    fmt = lambda x: x.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return fmt(start_bj), fmt(end_bj)


def rows_for(day):
    a, b = window(day)
    return d1("SELECT submission_id, email, form_type, consent, status, payload, created_at, "
              f"attr_first, user_agent FROM submissions WHERE created_at >= '{a}' AND created_at < '{b}' "
              "ORDER BY created_at")


def compose(day, rows):
    led = ledger()
    lines = [f"<b>询盘摘要 · {day.isoformat()}（北京时间当天）</b>", "",
             f"共 <b>{len(rows)}</b> 条。" if rows else "当天 0 条询盘。", ""]
    for i, r in enumerate(rows, 1):
        p = json.loads(r["payload"]) if isinstance(r["payload"], str) else (r.get("payload") or {})
        rec = led.get(r["submission_id"], {})
        when = (dt.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                .astimezone(BJ).strftime("%H:%M"))
        lines += [
            f"<b>{i}. {p.get('FIRSTNAME') or '(no name)'} — {p.get('COMPANY') or '(no company)'}</b>",
            f"　邮箱：{r['email']}",
            f"　国家：{p.get('COUNTRY') or '-'}　项目类型：{p.get('PRODUCT') or '-'}",
            f"　项目描述：{p.get('PROJECT') or '（空）'}",
            f"　时间：{when}（北京）　营销同意：{'是' if str(r.get('consent')) == '1' else '否'}",
            f"　账本状态：{rec.get('status', '未入账')}　submission_id：{r['submission_id']}",
            "",
        ]
    if not rows:
        lines += ["（没有新询盘。若你希望空摘要也发，加 --force）", ""]
    lines += ["—— 主记录在 D1 `anari-leads.submissions`；销售跟进看 Brevo CRM → Deals。"]
    html = "<br>".join(lines)
    text = "\n".join(l.replace("<b>", "").replace("</b>", "") for l in lines)
    return html, text


def send(subject, html, text):
    """改成走真实 Gmail 浏览器通道（2026-11-12）。
    原因：Instantly `/emails/test` 发出的信**正文为空**（用户实测），摘要也会变成空信。
    现在统一调用 scripts/tools/gmail_send.py（真实 compose），并把纯文本正文写成临时文件。"""
    import subprocess
    to = (os.environ.get("NOTIFY_TO") or "kerry@anaricharge.com").split(",")
    to = [e.strip() for e in to if e.strip()]
    body_file = "/tmp/inquiry-digest-body.txt"
    with open(body_file, "w", encoding="utf-8") as f:
        f.write(text)
    for addr in to:
        rc = subprocess.run(
            [sys.executable, os.path.join(WS, "scripts", "tools", "gmail_send.py"),
             "--to", addr, "--subject", subject, "--body-file", body_file],
            capture_output=True, text=True, timeout=900).returncode
        if rc != 0:
            raise SystemExit(f"gmail_send failed for {addr}")
    return {"status": "sent_via_gmail"}, to


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    day = (dt.date.fromisoformat(a.date) if a.date
           else (dt.datetime.now(BJ).date() - dt.timedelta(days=1)))
    rows = rows_for(day)
    html, text = compose(day, rows)
    print(f"  {day.isoformat()}（北京）询盘 {len(rows)} 条")
    for r in rows:
        p = json.loads(r["payload"]) if isinstance(r["payload"], str) else {}
        print(f"   - {p.get('FIRSTNAME','?')} / {p.get('COMPANY','?')} / {p.get('COUNTRY','?')} / {r['email']}")
    os.makedirs(OUT_DIR, exist_ok=True)
    art = os.path.join(OUT_DIR, f"{day.isoformat()}.md")
    with open(art, "w", encoding="utf-8") as f:
        f.write(f"# 询盘摘要 {day.isoformat()}（北京）\n\n{text}\n")
    print(f"  产物：{art}")
    # 顺带刷新第一方台账页（本地 HTML，不依赖邮箱/Brevo）
    try:
        subprocess.run([sys.executable, os.path.join(WS, "scripts/metrics/inquiry_ledger_page.py")],
                       capture_output=True, text=True, timeout=120)
    except Exception:  # noqa: BLE001
        pass
    if not rows and not a.force:
        print("  0 条 → 按约定不发信（--force 可强制）")
        return 0
    subject = f"询盘摘要 · {day.isoformat()} · {len(rows)} 条新询盘"
    if a.dry:
        print(f"  [dry] 不发送。主题：{subject}")
        return 0
    try:
        r, to = send(subject, html, text)
        print(f"  已发送 → {', '.join(to)}：{json.dumps(r, ensure_ascii=False)[:120]}")
        return 0
    except SystemExit as e:
        print(f"  ❌ 发送失败：{str(e)[:200]}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
